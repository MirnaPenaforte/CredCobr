from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, Exists, Max, Min, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.permissions import can_access_all_states, can_manage_collections, filter_by_state_scope
from apps.collections.models import AgreementInstallment, CollectionStatus, PaymentAgreement, PaymentPromise
from apps.collections.services import create_agreement, register_payment_promise, update_status
from apps.companies.models import Company, EconomicGroup, State
from apps.customers.models import Customer
from apps.imports.models import ImportBatch
from apps.notifications.models import Notification
from apps.processing.services import calculate_receivable_overdue_days
from apps.receivables.models import Receivable
from apps.reports.models import ReportExecution
from shared.dates import format_date, parse_date

from .forms import CollectionUpdateForm, PaymentAgreementForm, PaymentPromiseForm


def _visible_states(user):
    return State.objects.all()


MONEY_FIELD = DecimalField(max_digits=18, decimal_places=2)


def _money_sum(field: str, condition: Q | None = None):
    return Coalesce(Sum(field, filter=condition), Value(Decimal("0")), output_field=MONEY_FIELD)


def _indicator_row(row: dict[str, object] | None = None) -> dict[str, object]:
    row = row or {}
    portfolio_total = row.get("portfolio_total") or Decimal("0")
    overdue_total = row.get("overdue_total") or Decimal("0")
    delinquency = (overdue_total / portfolio_total * Decimal("100")) if portfolio_total else Decimal("0")
    return {
        "portfolio_total": portfolio_total,
        "overdue_total": overdue_total,
        "overdue_over_five": overdue_total,
        "delinquency_percentage": delinquency.quantize(Decimal("0.01")),
        "title_count": row.get("title_count") or 0,
    }


def _dashboard_totals(queryset, reference_date: date) -> tuple[dict[str, object], dict[str, dict[str, object]], dict[str, Decimal]]:
    cutoff_5 = reference_date - timedelta(days=5)
    rows = list(queryset.values("company__state__code").annotate(
        portfolio_total=_money_sum("outstanding_amount"),
        overdue_total=_money_sum("outstanding_amount", Q(due_date__lte=cutoff_5)),
        days_5_10=_money_sum("outstanding_amount", Q(
            due_date__range=(reference_date - timedelta(days=10), cutoff_5),
        )),
        days_11_30=_money_sum("outstanding_amount", Q(
            due_date__range=(reference_date - timedelta(days=30), reference_date - timedelta(days=11)),
        )),
        days_31_90=_money_sum("outstanding_amount", Q(
            due_date__range=(reference_date - timedelta(days=90), reference_date - timedelta(days=31)),
        )),
        days_91_360=_money_sum("outstanding_amount", Q(
            due_date__range=(reference_date - timedelta(days=360), reference_date - timedelta(days=91)),
        )),
        title_count=Count("id"),
    ))
    rows_by_code = {row["company__state__code"]: row for row in rows}
    by_state = {code: _indicator_row(rows_by_code.get(code)) for code in ("CE", "BA", "PE")}
    indicators = _indicator_row({
        "portfolio_total": sum((item["portfolio_total"] for item in by_state.values()), Decimal("0")),
        "overdue_total": sum((item["overdue_total"] for item in by_state.values()), Decimal("0")),
        "title_count": sum(item["title_count"] for item in by_state.values()),
    })
    overdue_bands = {
        name: sum((row.get(name) or Decimal("0") for row in rows), Decimal("0"))
        for name in ("overdue_total", "days_5_10", "days_11_30", "days_31_90", "days_91_360")
    }
    return indicators, by_state, overdue_bands


def _state_rankings(queryset, reference_date: date) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    current_promises = PaymentPromise.objects.filter(
        status=PaymentPromise.Status.PENDING,
        promised_date__gte=reference_date,
    ).values("receivable__customer_id")
    overdue_installments = AgreementInstallment.objects.filter(
        agreement_id=OuterRef("pk"), due_date__lt=reference_date, paid_at__isnull=True,
    )
    current_agreements = PaymentAgreement.objects.filter(
        status=PaymentAgreement.Status.ACTIVE,
    ).annotate(has_overdue=Exists(overdue_installments)).filter(
        has_overdue=False,
    ).values("receivable__customer_id")
    eligible = queryset.filter(
        due_date__lt=reference_date - timedelta(days=30),
        financial_status__in=(Receivable.FinancialStatus.OPEN, Receivable.FinancialStatus.PARTIALLY_PAID),
        balance_with_interest__gt=0,
    ).exclude(
        customer_id__in=Subquery(current_promises),
    ).exclude(
        customer_id__in=Subquery(current_agreements),
    )
    groups = list(eligible.values(
        "customer__economic_group_id", "customer__economic_group__name",
    ).annotate(amount=_money_sum("balance_with_interest")).order_by("-amount", "customer__economic_group__name")[:10])
    group_ranking = [{
        "group_id": item["customer__economic_group_id"],
        "group": item["customer__economic_group__name"] or "SEM GRUPO",
        "amount": item["amount"],
    } for item in groups]
    customers = list(eligible.filter(
        customer__economic_group__name__iexact="clientes geral",
    ).values("customer_id", "customer__name").annotate(
        amount=_money_sum("balance_with_interest"),
    ).order_by("-amount", "customer__name")[:10])
    customer_ranking = [{
        "customer_id": item["customer_id"], "customer": item["customer__name"], "amount": item["amount"],
    } for item in customers]
    return group_ranking, customer_ranking


def _parse_report_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("Data inválida")


@login_required
def home(request):
    reference_date = timezone.localdate()
    receivables = filter_by_state_scope(Receivable.objects.all(), request.user)
    indicators, by_state, overdue_bands = _dashboard_totals(receivables, reference_date)
    promises = filter_by_state_scope(PaymentPromise.objects.all(), request.user, field="receivable__company__state")
    state_comparison = [{"state": code, "delinquency": str(by_state.get(code, {}).get("delinquency_percentage", 0))} for code in ("CE", "BA", "PE")]
    agreements = filter_by_state_scope(PaymentAgreement.objects.all(), request.user, field="receivable__company__state").filter(created_by__role="manager").count()
    latest_import = ImportBatch.objects.filter(
        source=ImportBatch.Source.LEGACY,
        status=ImportBatch.Status.COMPLETED,
        finished_at__isnull=False,
    ).order_by("-finished_at").first()
    return render(request, "dashboard/home.html", {
        "indicators": indicators,
        "by_state": by_state,
        "state_comparison": state_comparison,
        "states": _visible_states(request.user),
        "expired_promises": promises.filter(promised_date__lt=reference_date, status=PaymentPromise.Status.PENDING).count(),
        "overdue_bands": overdue_bands,
        "agreements_count": agreements,
        "last_update": latest_import.finished_at if latest_import else receivables.aggregate(last_update=Max("updated_at"))["last_update"],
        "failed_imports": ImportBatch.objects.filter(status=ImportBatch.Status.FAILED).count(),
        "failed_notifications": Notification.objects.filter(status=Notification.Status.FAILED).count(),
    })


@login_required
def state_dashboard(request, code: str):
    reference_date = timezone.localdate()
    state = get_object_or_404(State, code=code.upper())
    receivables = filter_by_state_scope(Receivable.objects.all(), request.user).filter(company__state=state)
    indicators, _, _ = _dashboard_totals(receivables, reference_date)
    groups, general_customers = _state_rankings(receivables, reference_date)
    return render(request, "dashboard/state.html", {
        "state": state,
        "indicators": indicators,
        "groups": groups,
        "general_customers": general_customers,
    })


def _apply_maturity_filter(queryset, maturity: str):
    today = date.today()
    ranges = {
        "current": {"due_date__gte": today},
        "overdue": {"due_date__lt": today - timedelta(days=4)},
        "5_10": {"due_date__range": (today - timedelta(days=10), today - timedelta(days=5))},
        "11_30": {"due_date__range": (today - timedelta(days=30), today - timedelta(days=11))},
        "31_90": {"due_date__range": (today - timedelta(days=90), today - timedelta(days=31))},
        "91_360": {"due_date__range": (today - timedelta(days=360), today - timedelta(days=91))},
    }
    return queryset.filter(**ranges[maturity]) if maturity in ranges else queryset


@login_required
def receivable_list(request):
    queryset = filter_by_state_scope(
        Receivable.objects.select_related("company__state", "customer__economic_group", "operator", "collection_status").prefetch_related("interactions", "payment_promises"),
        request.user,
    )
    query = request.GET.get("q", "").strip()
    filters = {name: request.GET.get(name, "") for name in (
        "state", "maturity", "company", "group", "operator", "status", "promised_date"
    )}
    if not filters["maturity"]:
        filters["maturity"] = "overdue"
    filters["state"] = filters["state"].upper()
    promised_date = None
    if filters["promised_date"]:
        try:
            promised_date = parse_date(filters["promised_date"])
            filters["promised_date"] = format_date(promised_date)
        except ValueError:
            filters["promised_date"] = ""
    if query:
        queryset = queryset.filter(
            Q(title_number__icontains=query) | Q(customer__name__icontains=query)
            | Q(customer__identifier__icontains=query) | Q(customer__document__icontains=query)
        )
    lookups = {
        "state": "company__state__code", "company": "company_id", "group": "customer__economic_group_id",
        "operator": "operator_id", "status": "collection_status__status",
    }
    for name, lookup in lookups.items():
        if filters[name]:
            queryset = queryset.filter(**{lookup: filters[name]})
    if promised_date:
        queryset = queryset.filter(payment_promises__promised_date=promised_date)
    queryset = _apply_maturity_filter(queryset, filters["maturity"]).distinct()
    customers = queryset.values(
        "customer_id", "customer__identifier", "customer__name", "customer__economic_group__name"
    ).annotate(
        overdue_titles=Count("id", filter=Q(due_date__lt=date.today() - timedelta(days=4))),
        oldest_due_date=Min("due_date"),
        interest_amount=Sum("interest_amount", filter=Q(due_date__lt=date.today() - timedelta(days=4))),
        balance_with_interest=Sum("balance_with_interest", filter=Q(due_date__lt=date.today() - timedelta(days=4))),
        has_agreement=Exists(PaymentAgreement.objects.filter(
            receivable__customer_id=OuterRef("customer_id"), status=PaymentAgreement.Status.ACTIVE,
        )),
        has_promise=Exists(CollectionStatus.objects.filter(
            receivable__customer_id=OuterRef("customer_id"),
            status=CollectionStatus.Status.PROMISE,
        )),
        has_negotiation=Exists(CollectionStatus.objects.filter(
            receivable__customer_id=OuterRef("customer_id"),
            status=CollectionStatus.Status.NEGOTIATING,
        )),
    ).order_by("oldest_due_date", "customer__name")
    page = Paginator(customers, 25).get_page(request.GET.get("page"))
    for item in page.object_list:
        due_days = (date.today() - item["oldest_due_date"]).days if item["oldest_due_date"] < date.today() else 0
        urgent_days = due_days
        if 5 <= urgent_days <= 10:
            item["urgent_color"] = "green"
        elif 10 < urgent_days <= 30:
            item["urgent_color"] = "yellow"
        elif 30 < urgent_days <= 90:
            item["urgent_color"] = "orange"
        elif urgent_days > 90:
            item["urgent_color"] = "red"
        else:
            item["urgent_color"] = ""
    scoped_companies = Company.objects.filter(state__in=_visible_states(request.user))
    return render(request, "receivables/list.html", {
        "page": page, "states": _visible_states(request.user), "query": query, "filters": filters,
        "companies": scoped_companies,
        "groups": EconomicGroup.objects.filter(customers__receivables__company__in=scoped_companies).distinct(),
        "operators": request.user.__class__.objects.filter(assigned_receivables__company__in=scoped_companies).distinct(),
        "collection_statuses": CollectionStatus.Status.choices,
    })


@login_required
def customer_receivables_detail(request, pk: int):
    customer = get_object_or_404(exclude_hidden_customers(Customer.objects.all(), relation=None), pk=pk)
    receivables = filter_by_state_scope(
        Receivable.objects.select_related("company__state", "collection_status").prefetch_related("payment_promises", "agreements").filter(customer=customer),
        request.user,
    ).order_by("due_date", "id")
    promise_operations = filter_by_state_scope(
        PaymentPromise.objects.select_related("receivable", "created_by").filter(receivable__customer=customer),
        request.user,
        field="receivable__company__state",
    ).order_by("-created_at")
    agreement_operations = filter_by_state_scope(
        PaymentAgreement.objects.select_related("receivable", "created_by").filter(receivable__customer=customer),
        request.user,
        field="receivable__company__state",
    ).order_by("-created_at")
    editable = can_manage_collections(request.user)
    if request.method == "POST" and not editable:
        raise PermissionDenied

    raw_selected_ids = request.POST.getlist("receivable_ids")
    selected_ids = [value for value in raw_selected_ids if value.isdigit()]
    selected_receivables = list(receivables.filter(pk__in=selected_ids)) if selected_ids else []
    promise_form = PaymentPromiseForm()
    agreement_form = PaymentAgreementForm()
    form_alert = ""
    if request.method == "POST" and request.POST.get("action") in {"promise", "agreement"}:
        if not selected_receivables:
            form_alert = "Selecione ao menos um boleto."
        elif request.POST["action"] == "promise":
            promise_form = PaymentPromiseForm(request.POST)
            if promise_form.is_valid():
                promise_data = promise_form.cleaned_data.copy()
                notes = promise_data.pop("notes")
                is_total_value = request.POST.get("use_total_value") == "1"
                with transaction.atomic():
                    for item in selected_receivables:
                        item_promise_data = promise_data.copy()
                        if is_total_value:
                            item_promise_data["promised_amount"] = item.balance_with_interest
                        register_payment_promise(receivable=item, user=request.user, is_total_value=is_total_value, **item_promise_data)
                        collection, _ = CollectionStatus.objects.get_or_create(receivable=item)
                        update_status(collection, status=CollectionStatus.Status.PROMISE, user=request.user, notes=notes)
                messages.success(request, "Promessas de pagamento registradas.")
                return redirect("customer-receivables-detail", pk=customer.pk)
            form_alert = "A data máxima permitida para promessas é 7 dias." if "promised_date" in promise_form.errors else "Verifique os dados informados para a promessa."
        else:
            agreement_form = PaymentAgreementForm(request.POST)
            if agreement_form.is_valid():
                agreement_data = agreement_form.cleaned_data.copy()
                notes = agreement_data.pop("notes")
                is_total_value = request.POST.get("use_total_value") == "1"
                with transaction.atomic():
                    for item in selected_receivables:
                        item_agreement_data = agreement_data.copy()
                        if is_total_value:
                            item_agreement_data["negotiated_amount"] = item.balance_with_interest
                        create_agreement(receivable=item, user=request.user, is_total_value=is_total_value, **item_agreement_data)
                        collection, _ = CollectionStatus.objects.get_or_create(receivable=item)
                        update_status(collection, status=CollectionStatus.Status.NEGOTIATING, user=request.user, notes=notes)
                messages.success(request, "Acordos registrados com sucesso.")
                return redirect("customer-receivables-detail", pk=customer.pk)
            form_alert = "Verifique os dados informados para o acordo."

    for item in receivables:
        item.is_selected = str(item.pk) in selected_ids
        overdue_days = calculate_receivable_overdue_days(item, date.today())
        if 0 < overdue_days <= 10:
            item.overdue_color, item.overdue_label = "green", "5 a 10 dias"
        elif 10 < overdue_days <= 30:
            item.overdue_color, item.overdue_label = "yellow", "11 a 30 dias"
        elif 30 < overdue_days <= 90:
            item.overdue_color, item.overdue_label = "orange", "31 a 90 dias"
        elif overdue_days > 90:
            item.overdue_color, item.overdue_label = "red", "91 a 360 dias"
        else:
            item.overdue_color, item.overdue_label = "", ""
        collection = getattr(item, "collection_status", None)
        if collection and collection.status in {
            CollectionStatus.Status.BROKEN_PROMISE,
            CollectionStatus.Status.BROKEN_AGREEMENT,
        }:
            item.collection_label, item.collection_icon, item.collection_key = "Inadimplente", "!", "broken-promise"
        elif any(agreement.status == PaymentAgreement.Status.ACTIVE for agreement in item.agreements.all()):
            item.collection_label, item.collection_icon, item.collection_key = "Acordo", "🤝", "agreement"
        elif collection and collection.status == CollectionStatus.Status.PROMISE:
            item.collection_label, item.collection_icon, item.collection_key = "Promessa", "✓", "promise"
        elif collection and collection.status == CollectionStatus.Status.NEGOTIATING:
            item.collection_label, item.collection_icon, item.collection_key = "Negociado", "↔", "negotiating"
        else:
            item.collection_label, item.collection_icon, item.collection_key = "Em aberto", "○", "open"
    negotiation_operations = []
    for promise in promise_operations:
        negotiation_operations.append({
            "created_at": promise.created_at, "document": str(promise.receivable), "type": "Promessa",
            "value_type": "Valor total" if promise.is_total_value else "Valor informado",
            "amount": promise.receivable.balance_with_interest if promise.is_total_value else promise.promised_amount,
            "periodicity": "À vista", "date": promise.promised_date,
        })
    for agreement in agreement_operations:
        negotiation_operations.append({
            "created_at": agreement.created_at, "document": str(agreement.receivable), "type": "Acordo",
            "value_type": "Valor total" if agreement.is_total_value else ("Parcelado" if agreement.installment_count > 1 else "À vista"),
            "amount": agreement.receivable.balance_with_interest if agreement.is_total_value else agreement.negotiated_amount,
            "periodicity": f"{agreement.installment_count} parcela(s) · {agreement.periodicity_days} dias", "date": None,
        })
    negotiation_operations.sort(key=lambda item: item["created_at"], reverse=True)
    return render(request, "receivables/customer_detail.html", {
        "customer": customer,
        "receivables": receivables,
        "promise_form": promise_form,
        "agreement_form": agreement_form,
        "negotiation_operations": negotiation_operations,
        "form_alert": form_alert,
        "can_edit": editable,
    })


@login_required
def receivable_detail(request, pk: int):
    queryset = filter_by_state_scope(
        Receivable.objects.select_related("company__state", "customer").prefetch_related("interactions__user", "payment_promises", "agreements__installments"),
        request.user,
    )
    receivable = get_object_or_404(queryset, pk=pk)
    editable = can_manage_collections(request.user)
    if request.method == "POST" and not editable:
        raise PermissionDenied
    try:
        collection = receivable.collection_status
    except CollectionStatus.DoesNotExist:
        collection = CollectionStatus(receivable=receivable)
        if editable:
            collection.save()
    form = CollectionUpdateForm(request.POST or None, instance=collection)
    promise_form = PaymentPromiseForm(request.POST or None)
    agreement_form = PaymentAgreementForm(request.POST or None)
    if request.method == "POST" and request.POST.get("action") == "promise" and promise_form.is_valid():
        promise_data = promise_form.cleaned_data.copy()
        promise_data.pop("notes")
        register_payment_promise(receivable=receivable, user=request.user, **promise_data)
        messages.success(request, "Promessa de pagamento registrada.")
        return redirect("receivable-detail", pk=pk)
    if request.method == "POST" and request.POST.get("action") == "agreement" and agreement_form.is_valid():
        agreement_data = agreement_form.cleaned_data.copy()
        agreement_data.pop("notes")
        create_agreement(receivable=receivable, user=request.user, **agreement_data)
        messages.success(request, "Acordo registrado com sucesso.")
        return redirect("receivable-detail", pk=pk)
    if request.method == "POST" and not request.POST.get("action") and form.is_valid():
        update_status(collection, user=request.user, **form.cleaned_data)
        messages.success(request, "Atualização registrada com sucesso.")
        return redirect("receivable-detail", pk=pk)
    return render(request, "receivables/detail.html", {
        "receivable": receivable, "collection": collection, "form": form,
        "promise_form": promise_form, "agreement_form": agreement_form, "can_edit": editable,
    })


@login_required
def report_list(request):
    report_types = [ReportExecution.Type.STATE_EXCEL, ReportExecution.Type.UPCOMING_EXCEL]

    selected_state = request.GET.get("state", "").upper()
    if selected_state not in {"CE", "BA", "PE"}:
        selected_state = ""
    selected_date = request.GET.get("report_date", "")
    try:
        report_date = _parse_report_date(selected_date) if selected_date else None
        selected_date = report_date.strftime("%d/%m/%Y") if report_date else ""
    except ValueError:
        selected_date = ""
        report_date = None

    base = ReportExecution.objects.filter(
        report_type__in=report_types,
        status=ReportExecution.Status.COMPLETED,
    ).select_related("state")

    available_states = set(base.values_list("state__code", flat=True))
    available_dates = [item.strftime("%d/%m/%Y") for item in sorted(set(base.values_list("report_date", flat=True)))]

    queryset = base
    if selected_state:
        queryset = queryset.filter(state__code=selected_state)
    if report_date:
        queryset = queryset.filter(report_date=report_date)

    latest: dict[tuple[str, str], ReportExecution] = {}
    for report in queryset.order_by("state__code", "report_type", "-report_date"):
        latest.setdefault((report.state.code, report.report_type), report)

    reports = list(latest.values())
    for report in reports:
        report.type_label = (
            "Vencidos" if report.report_type == ReportExecution.Type.STATE_EXCEL else "A vencer"
        )
    return render(request, "reports/list.html", {
        "reports": reports,
        "states": ("CE", "BA", "PE"),
        "available_states": available_states,
        "available_dates": available_dates,
        "selected_state": selected_state,
        "selected_date": selected_date,
    })


@login_required
def report_download(request, pk: int):
    queryset = ReportExecution.objects.filter(pk=pk, status=ReportExecution.Status.COMPLETED)
    if not can_access_all_states(request.user):
        queryset = queryset.filter(Q(state__in=request.user.authorized_states.all()) | Q(state__isnull=True))
    report = get_object_or_404(queryset)
    if not report.file_path:
        raise Http404
    stored_path = Path(report.file_path)
    candidates = [stored_path]
    reports_dir = Path(os.getenv("REPORTS_DIR", "reports"))
    fallback_path = reports_dir / stored_path.name
    if fallback_path != stored_path:
        candidates.append(fallback_path)
    for candidate in candidates:
        try:
            return FileResponse(
                candidate.open("rb"),
                as_attachment=True,
                filename=stored_path.name,
            )
        except OSError:
            continue
    raise Http404
