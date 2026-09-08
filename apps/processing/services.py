from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Iterable

from django.db.models import QuerySet

from apps.collections.models import PaymentAgreement, PaymentPromise
from apps.receivables.models import Receivable


class OverdueBand(StrEnum):
    CURRENT = "current"
    DAYS_1_10 = "1_10"
    DAYS_11_30 = "11_30"
    DAYS_31_90 = "31_90"
    DAYS_91_360 = "91_360"
    OVER_360 = "over_360"


@dataclass(frozen=True, slots=True)
class ReceivableClassification:
    receivable_id: int
    overdue_days: int
    band: OverdueBand


def calculate_overdue_days(due_date: date, reference_date: date) -> int:
    return max((reference_date - due_date).days, 0)


def calculate_receivable_overdue_days(receivable: Receivable, reference_date: date) -> int:
    """Calculate aging from the actual due date, never from a source snapshot."""
    return calculate_overdue_days(receivable.due_date, reference_date)


def classify_overdue_days(days: int) -> OverdueBand:
    if days <= 0:
        return OverdueBand.CURRENT
    if days <= 10:
        return OverdueBand.DAYS_1_10
    if days <= 30:
        return OverdueBand.DAYS_11_30
    if days <= 90:
        return OverdueBand.DAYS_31_90
    if days <= 360:
        return OverdueBand.DAYS_91_360
    return OverdueBand.OVER_360


def classify_receivables(receivables: Iterable[Receivable], reference_date: date) -> list[ReceivableClassification]:
    return [
        ReceivableClassification(
            receivable_id=receivable.pk,
            overdue_days=days,
            band=classify_overdue_days(days),
        )
        for receivable in receivables
        for days in [calculate_receivable_overdue_days(receivable, reference_date)]
    ]


def _items(receivables: Iterable[Receivable] | QuerySet[Receivable]) -> list[Receivable]:
    return list(receivables)


def calculate_indicators(receivables: Iterable[Receivable], reference_date: date) -> dict[str, object]:
    items = _items(receivables)
    portfolio_total = sum((item.outstanding_amount for item in items), Decimal("0"))
    classified = [
        (item, calculate_receivable_overdue_days(item, reference_date))
        for item in items
    ]
    overdue_over_ten = sum(
        (item.outstanding_amount for item, days in classified if days > 10),
        Decimal("0"),
    )
    overdue_total = sum(
        (item.outstanding_amount for item in items if item.due_date < reference_date),
        Decimal("0"),
    )
    delinquency = (overdue_total / portfolio_total * Decimal("100")) if portfolio_total else Decimal("0")
    return {
        "portfolio_total": portfolio_total,
        "overdue_total": overdue_total,
        "overdue_over_ten": overdue_over_ten,
        "delinquency_percentage": delinquency.quantize(Decimal("0.01")),
        "title_count": len(items),
        "delinquent_customer_count": len({item.customer_id for item, days in classified if days > 10}),
    }


def calculate_overdue_bands(receivables: Iterable[Receivable], reference_date: date) -> dict[str, Decimal]:
    totals = {f"days_{band.value}": Decimal("0") for band in OverdueBand if band is not OverdueBand.CURRENT}
    overdue_total = Decimal("0")
    for item in _items(receivables):
        days = calculate_receivable_overdue_days(item, reference_date)
        if item.due_date < reference_date:
            overdue_total += item.outstanding_amount
        band = classify_overdue_days(days)
        if band is not OverdueBand.CURRENT:
            totals[f"days_{band.value}"] += item.outstanding_amount
    totals["overdue_total"] = overdue_total
    return totals


def consolidate_by_state(receivables: Iterable[Receivable], reference_date: date) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Receivable]] = defaultdict(list)
    for receivable in receivables:
        grouped[receivable.company.state.code].append(receivable)
    return {state: calculate_indicators(items, reference_date) for state, items in grouped.items()}


def _commitment_is_current(receivable: Receivable, reference_date: date) -> bool:
    """Return whether a title is covered by a promise or agreement without delay."""
    promises = receivable.payment_promises.all() if hasattr(receivable, "payment_promises") else []
    if any(
        promise.status == PaymentPromise.Status.PENDING and promise.promised_date >= reference_date
        for promise in promises
    ):
        return True

    agreements = receivable.agreements.all() if hasattr(receivable, "agreements") else []
    for agreement in agreements:
        if agreement.status != PaymentAgreement.Status.ACTIVE:
            continue
        installments = agreement.installments.all() if hasattr(agreement, "installments") else []
        has_overdue_installment = any(
            installment.due_date < reference_date and installment.paid_at is None
            for installment in installments
        )
        if not has_overdue_installment:
            return True
    return False


def _eligible_debtor_receivables(receivables: Iterable[Receivable], reference_date: date) -> list[Receivable]:
    """Return overdue debt from customers not protected by a current commitment.

    A commitment is current when its payment date/next installment has not passed.
    The exclusion is customer-wide in the selected dashboard scope, so a customer
    with an agreement or promise being honored is not ranked as a debtor.
    """
    items = list(receivables)
    customers_with_current_commitment = {
        item.customer_id for item in items if _commitment_is_current(item, reference_date)
    }
    cutoff = reference_date - timedelta(days=30)
    return [
        item for item in items
        if item.customer_id not in customers_with_current_commitment
        and item.due_date < cutoff
        and item.financial_status in {item.FinancialStatus.OPEN, item.FinancialStatus.PARTIALLY_PAID}
        and item.balance_with_interest > 0
    ]


def top_groups(
    receivables: Iterable[Receivable], limit: int = 10, reference_date: date | None = None
) -> list[dict[str, object]]:
    reference_date = reference_date or date.today()
    totals: dict[int | None, Decimal] = defaultdict(lambda: Decimal("0"))
    names: dict[int | None, str] = {}
    for item in _eligible_debtor_receivables(receivables, reference_date):
        group_id = item.customer.economic_group_id
        totals[group_id] += item.balance_with_interest
        names[group_id] = item.customer.economic_group.name if item.customer.economic_group else "SEM GRUPO"
    return [
        {"group_id": group_id, "group": names[group_id], "amount": amount}
        for group_id, amount in sorted(totals.items(), key=lambda pair: (-pair[1], names[pair[0]]))[:limit]
    ]


def top_customers_by_group(
    receivables: Iterable[Receivable], group_id: int | None, limit: int = 10
) -> list[dict[str, object]]:
    totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    names: dict[int, str] = {}
    for item in receivables:
        if item.customer.economic_group_id == group_id:
            totals[item.customer_id] += item.outstanding_amount
            names[item.customer_id] = item.customer.name
    return [
        {"customer_id": customer_id, "customer": names[customer_id], "amount": amount}
        for customer_id, amount in sorted(totals.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    ]


def top_general_customers(
    receivables: Iterable[Receivable], limit: int = 10, reference_date: date | None = None
) -> list[dict[str, object]]:
    reference_date = reference_date or date.today()
    totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    names: dict[int, str] = {}
    for item in _eligible_debtor_receivables(receivables, reference_date):
        group = item.customer.economic_group.name.strip().casefold() if item.customer.economic_group else ""
        if group == "clientes geral":
            totals[item.customer_id] += item.balance_with_interest
            names[item.customer_id] = item.customer.name
    return [
        {"customer_id": customer_id, "customer": names[customer_id], "amount": amount}
        for customer_id, amount in sorted(totals.items(), key=lambda pair: (-pair[1], names[pair[0]]))[:limit]
    ]
