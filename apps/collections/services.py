from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.audit.services import record_audit
from shared.dates import format_date

from .models import AgreementInstallment, CollectionInteraction, CollectionStatus, PaymentAgreement, PaymentPromise


@transaction.atomic
def update_status(
    collection: CollectionStatus,
    *,
    status: str,
    user: Any,
    notes: str = "",
    expected_payment_date: date | None = None,
    expected_amount: Decimal | None = None,
    next_action: str = "",
) -> CollectionStatus:
    previous = {
        "status": collection.status,
        "notes": collection.notes,
        "expected_payment_date": format_date(collection.expected_payment_date) if collection.expected_payment_date else None,
        "expected_amount": str(collection.expected_amount) if collection.expected_amount is not None else None,
        "next_action": collection.next_action,
    }
    collection.status = status
    collection.notes = notes
    collection.expected_payment_date = expected_payment_date
    collection.expected_amount = expected_amount
    collection.next_action = next_action
    collection.updated_by = user
    collection.save()
    record_audit(
        user=user,
        action="collection_status_updated",
        model_name=collection.__class__.__name__,
        object_id=str(collection.pk),
        previous_value=previous,
        new_value={"status": status, "notes": notes, "next_action": next_action},
        origin="application",
    )
    return collection


@transaction.atomic
def register_interaction(
    *, receivable: Any, user: Any, channel: str, notes: str, next_action: str = ""
) -> CollectionInteraction:
    interaction = CollectionInteraction.objects.create(
        receivable=receivable,
        user=user,
        channel=channel,
        notes=notes,
        next_action=next_action,
    )
    record_audit(
        user=user,
        action="collection_interaction_created",
        model_name=interaction.__class__.__name__,
        object_id=str(interaction.pk),
        new_value={"channel": channel, "next_action": next_action},
        origin="application",
    )
    return interaction


@transaction.atomic
def register_payment_promise(
    *, receivable: Any, user: Any, promised_date: date, promised_amount: Decimal, is_total_value: bool = False
) -> PaymentPromise:
    if not date.today() <= promised_date <= date.today() + timedelta(days=7):
        raise ValueError("A promessa deve ter data entre hoje e os próximos 7 dias.")
    promise = PaymentPromise.objects.create(
        receivable=receivable,
        created_by=user,
        promised_date=promised_date,
        promised_amount=promised_amount,
        is_total_value=is_total_value,
    )
    record_audit(
        user=user,
        action="payment_promise_created",
        model_name=promise.__class__.__name__,
        object_id=str(promise.pk),
        new_value={"promised_date": format_date(promised_date), "promised_amount": str(promised_amount)},
        origin="application",
    )
    return promise


@transaction.atomic
def create_agreement(
    *,
    receivable: Any,
    user: Any,
    negotiated_amount: Decimal,
    installment_count: int,
    first_due_date: date,
    periodicity_days: int = 30,
    is_total_value: bool = False,
) -> PaymentAgreement:
    agreement = PaymentAgreement.objects.create(
        receivable=receivable,
        created_by=user,
        negotiated_amount=negotiated_amount,
        installment_count=installment_count,
        periodicity_days=periodicity_days,
        is_total_value=is_total_value,
    )
    base_amount = (negotiated_amount / installment_count).quantize(Decimal("0.01"))
    for number in range(1, installment_count + 1):
        amount = base_amount if number < installment_count else negotiated_amount - base_amount * (installment_count - 1)
        AgreementInstallment.objects.create(
            agreement=agreement,
            number=number,
            due_date=first_due_date + timedelta(days=periodicity_days * (number - 1)),
            amount=amount,
        )
    record_audit(
        user=user,
        action="payment_agreement_created",
        model_name=agreement.__class__.__name__,
        object_id=str(agreement.pk),
        new_value={"negotiated_amount": str(negotiated_amount), "installment_count": installment_count},
        origin="application",
    )
    return agreement
