from __future__ import annotations

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, Max, Min, OuterRef, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import can_access_all_states, can_manage_collections, filter_by_state_scope
from apps.collections.models import CollectionStatus, PaymentAgreement, PaymentPromise
from apps.collections.services import create_agreement, register_payment_promise, update_status
from apps.companies.models import Company, EconomicGroup, State
from apps.customers.models import Customer
from apps.imports.models import ImportBatch
from apps.notifications.models import Notification
from apps.processing.services import calculate_indicators, calculate_overdue_days, calculate_receivable_overdue_days, calculate_overdue_bands, classify_overdue_days, consolidate_by_state, top_customers_by_group, top_groups
from apps.receivables.models import Receivable
from apps.reports.models import ReportExecution
from shared.dates import format_date, parse_date

from .forms import CollectionUpdateForm, PaymentAgreementForm, PaymentPromiseForm


def _visible_states(user):
    return State.objects.all()


@login_required
def home(request):
    receivables = filter_by_state_scope(Receivable.objects.select_related("company__state", "customer"), request.user)
    indicators = calculate_indicators(receivables, date.today())
    promises = filter_by_state_scope(PaymentPromise.objects.all(), request.user, field="receivable__company__state")
    by_state = consolidate_by_state(receivables, date.today())
    for state_code in ("CE", "BA", "PE"):
        by_state.setdefault(state_code, calculate_indicators([], date.today()))
    state_comparison = [{"state": code, "delinquency": str(by_state.get(code, {}).get("delinquency_percentage", 0))} for code in ("CE", "BA", "PE")]
    overdue_bands = calculate_overdue_bands(receivables, date.today())
    agreements = filter_by_state_scope(PaymentAgreement.objects.all(), request.user, field="receivable__company__state").filter(created_by__role="manager").count()
    return render(request, "dashboard/home.html", {
        "indicators": indicators,
        "by_state": by_state,
        "state_comparison": state_comparison,
        "states": _visible_states(request.user),
        "expired_promises": promises.filter(promised_date__lt=date.today(), status=PaymentPromise.Status.PENDING).count(),
        "overdue_bands": overdue_bands,
        "agreements_count": agreements,
        "last_update": receivables.aggregate(value=Max("updated_at"))["value"],
        "failed_imports": ImportBatch.objects.filter(status=ImportBatch.Status.FAILED).count(),
        "failed_notifications": Notification.objects.filter(status=Notification.Status.FAILED).count(),
    })


@login_required
def state_dashboard(request, code: str):
    state = get_object_or_404(State, code=code.upper())
    receivables = list(filter_by_state_scope(
        Receivable.objects.select_related("company__state", "customer__economic_group"), request.user
    ).filter(company__state=state))
    groups = top_groups(receivables)
    customers_by_group = {
        str(group["group_id"] if group["group_id"] is not None else "none"):
        top_customers_by_group(receivables, group["group_id"])
        for group in groups
    }
    selected_group = groups[0] if groups else {"group": "", "group_id": None}
    return render(request, "dashboard/state.html", {
        "state": state,
        "indicators": calculate_indicators(receivables, date.today()),
        "groups": groups,
        "customers_by_group": customers_by_group,
        "selected_group": selected_group,
    })


def _apply_maturity_filter(queryset, maturity: str):
    today = date.today()
    ranges = {
        "current": {"due_date__gte": today},
        "overdue": {"due_date__lt": today},
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
        overdue_titles=Count("id", filter=Q(due_date__lt=date.today())),
        oldest_due_date=Min("due_date"),
        interest_amount=Sum("interest_amount", filter=Q(due_date__lt=date.today())),
        balance_with_interest=Sum("balance_with_interest", filter=Q(due_date__lt=date.today())),
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
        if 0 < urgent_days <= 10:
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
    customer = get_object_or_404(Customer, pk=pk)
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
            item.overdue_color, item.overdue_label = "green", "Até 10 dias"
        elif 10 < overdue_days <= 30:
            item.overdue_color, item.overdue_label = "yellow", "11 a 30 dias"
        elif 30 < overdue_days <= 90:
            item.overdue_color, item.overdue_label = "orange", "31 a 90 dias"
        elif overdue_days > 90:
            item.overdue_color, item.overdue_label = "red", "91 a 360 dias"
        else:
            item.overdue_color, item.overdue_label = "", ""
        collection = getattr(item, "collection_status", None)
        if any(agreement.status == PaymentAgreement.Status.ACTIVE for agreement in item.agreements.all()):
            item.collection_label, item.collection_icon, item.collection_key = "Acordo", "🤝", "agreement"
        elif collection and collection.status == CollectionStatus.Status.PROMISE:
            item.collection_label, item.collection_icon, item.collection_key = "Promessa", "✓", "promise"
        elif collection and collection.status == CollectionStatus.Status.NEGOTIATING:
            item.collection_label, item.collection_icon, item.collection_key = "Negociado", "↔", "negotiating"
        elif collection and collection.status == CollectionStatus.Status.BROKEN_PROMISE:
            item.collection_label, item.collection_icon, item.collection_key = "Inadimplente", "!", "broken-promise"
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
    band_choices = ReportExecution.Band.choices
    valid_bands = {value for value, _ in band_choices}
    selected_band = request.GET.get("band", "")
    if selected_band and selected_band not in valid_bands:
        selected_band = ""

    selected_state = request.GET.get("state", "").upper()
    if selected_state not in {"CE", "BA", "PE"}:
        selected_state = ""
    selected_date = request.GET.get("report_date", "")
    try:
        report_date = parse_date(selected_date) if selected_date else None
        selected_date = format_date(report_date) if report_date else ""
    except ValueError:
        selected_date = ""
        report_date = None

    report_base = ReportExecution.objects.filter(
        report_type=ReportExecution.Type.BAND_EXCEL,
        status=ReportExecution.Status.COMPLETED,
    )
    band_queryset = report_base.select_related("state")
    if selected_band:
        band_queryset = band_queryset.filter(overdue_band=selected_band)
    if selected_state:
        band_queryset = band_queryset.filter(state__code=selected_state)
    if report_date:
        band_queryset = band_queryset.filter(report_date=report_date)

    bands_queryset = report_base
    if selected_state:
        bands_queryset = bands_queryset.filter(state__code=selected_state)
    if report_date:
        bands_queryset = bands_queryset.filter(report_date=report_date)
    available_bands = {value for value in bands_queryset.values_list("overdue_band", flat=True)}

    states_queryset = report_base
    if selected_band:
        states_queryset = states_queryset.filter(overdue_band=selected_band)
    if report_date:
        states_queryset = states_queryset.filter(report_date=report_date)
    available_states = set(states_queryset.values_list("state__code", flat=True))

    dates_queryset = report_base
    if selected_band:
        dates_queryset = dates_queryset.filter(overdue_band=selected_band)
    if selected_state:
        dates_queryset = dates_queryset.filter(state__code=selected_state)
    available_dates = [
        format_date(item)
        for item in sorted(set(dates_queryset.values_list("report_date", flat=True)))
    ]
    band_queryset = band_queryset.order_by("state__code", "-report_date")
    latest_by_state = {}
    for report in band_queryset:
        latest_by_state.setdefault((report.state.code, report.overdue_band), report)

    other_reports = ReportExecution.objects.exclude(
        report_type=ReportExecution.Type.BAND_EXCEL
    ).select_related("state")
    if selected_state:
        other_reports = other_reports.filter(Q(state__code=selected_state) | Q(state__isnull=True))
    if report_date:
        other_reports = other_reports.filter(report_date=report_date)
    other_reports = other_reports.order_by("-created_at")[:20]
    reports = list(latest_by_state.values())
    labels = dict(band_choices)
    return render(request, "reports/list.html", {
        "band_choices": band_choices,
        "available_bands": available_bands,
        "states": ("CE", "BA", "PE"),
        "available_states": available_states,
        "available_dates": available_dates,
        "selected_band": selected_band,
        "selected_band_label": labels.get(selected_band, "Todas as faixas"),
        "selected_state": selected_state,
        "selected_date": selected_date,
        "band_reports": reports,
        "band_report_count": len(reports),
        "other_reports": other_reports,
    })


@login_required
def report_download(request, pk: int):
    queryset = ReportExecution.objects.filter(pk=pk, status=ReportExecution.Status.COMPLETED)
    if not can_access_all_states(request.user):
        queryset = queryset.filter(Q(state__in=request.user.authorized_states.all()) | Q(state__isnull=True))
    report = get_object_or_404(queryset)
    if not report.file_path:
        raise Http404
    try:
        return FileResponse(open(report.file_path, "rb"), as_attachment=True)
    except OSError as exc:
        raise Http404 from exc


@login_required
def report_pdf(request, pk: int):
    queryset = ReportExecution.objects.filter(pk=pk, status=ReportExecution.Status.COMPLETED)
    if not can_access_all_states(request.user):
        queryset = queryset.filter(Q(state__in=request.user.authorized_states.all()) | Q(state__isnull=True))
    report = get_object_or_404(queryset)
    if not report.pdf_file_path:
        raise Http404
    try:
        return FileResponse(open(report.pdf_file_path, "rb"), content_type="application/pdf")
    except OSError as exc:
        raise Http404 from exc
