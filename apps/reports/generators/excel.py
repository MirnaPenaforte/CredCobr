from __future__ import annotations

import hashlib
import os
from datetime import date, datetime
from pathlib import Path

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.companies.models import State
from apps.processing.services import calculate_indicators, calculate_receivable_overdue_days, classify_overdue_days
from apps.receivables.models import Receivable
from apps.reports.models import ReportExecution
from .pdf import generate_band_pdf_file

SHEETS = ("1_10", "11_30", "31_90", "91_360")
BAND_LABELS = {
    "1_10": "Até 10 dias",
    "11_30": "De 11 a 30 dias",
    "31_90": "De 31 a 90 dias",
    "91_360": "De 91 a 360 dias",
}
HEADERS = [
    "ID do título", "Parcela", "ID do cliente", "Nome do cliente", "Grupo",
    "Empresa", "Estado", "Valor original", "Juros", "Multa", "Saldo em aberto",
    "Emissão", "Vencimento", "Dias vencidos", "Faixa", "Status financeiro",
    "Juros ao dia", "Status na origem", "Vendedor", "Código do agente",
    "Estabelecimento de origem", "Código do estabelecimento",
    "Gestor responsável", "Status da cobrança", "Previsão de pagamento", "Última interação",
]


def _reports_dir() -> Path:
    target = Path(os.getenv("REPORTS_DIR", "reports"))
    target.mkdir(parents=True, exist_ok=True)
    return target


def _state_items(state: State) -> list[Receivable]:
    return list(
        Receivable.objects.filter(company__state=state)
        .select_related("company__state", "customer__economic_group", "operator", "collection_status")
        .prefetch_related("interactions")
        .order_by("due_date", "id")
    )


def _row(item: Receivable, reference_date: date, band: str) -> list[object]:
    collection = getattr(item, "collection_status", None)
    last_interaction = item.interactions.first()
    responsible = ""
    if item.operator:
        responsible = item.operator.get_full_name() or item.operator.username
    return [
        item.title_number, item.installment, item.customer.identifier, item.customer.name,
        item.customer.economic_group.name if item.customer.economic_group else "",
        item.company.name, item.company.state.code, item.original_amount, item.interest_amount,
        item.penalty_amount, item.outstanding_amount, item.issued_at, item.due_date,
        calculate_receivable_overdue_days(item, reference_date), BAND_LABELS[band],
        item.get_financial_status_display(), item.daily_interest_amount, item.source_status,
        item.seller, item.agent_code, item.origin_establishment_code, item.establishment_code, responsible,
        collection.get_status_display() if collection else "Pendente",
        collection.expected_payment_date if collection else None,
        last_interaction.created_at.replace(tzinfo=None) if last_interaction else None,
    ]


def _format_sheet(sheet) -> None:
    header_fill = PatternFill("solid", fgColor="6E4B2E")
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, datetime):
                cell.number_format = "mm/dd/yyyy hh:mm"
            elif isinstance(cell.value, date):
                cell.number_format = "mm/dd/yyyy"
    for index, column in enumerate(sheet.columns, 1):
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 36)
        sheet.column_dimensions[get_column_letter(index)].width = width


def _save_execution(execution: ReportExecution, workbook: Workbook, path: Path, rows: int, metadata: dict) -> None:
    workbook.save(path)
    execution.file_path = str(path.resolve())
    execution.checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    execution.rows_processed = rows
    execution.status = ReportExecution.Status.COMPLETED
    execution.metadata = metadata


def generate_state_excel(state_code: str, reference_date: date) -> ReportExecution:
    state, _ = State.objects.get_or_create(code=state_code.upper(), defaults={"name": state_code.upper()})
    execution, _ = ReportExecution.objects.get_or_create(
        state=state, report_type=ReportExecution.Type.STATE_EXCEL,
        overdue_band="", report_date=reference_date,
    )
    execution.status = ReportExecution.Status.PROCESSING
    execution.started_at = timezone.now()
    execution.error_message = ""
    execution.save()
    try:
        items = _state_items(state)
        indicators = calculate_indicators(items, reference_date)
        workbook = Workbook()
        summary = workbook.active
        summary.title = "Resumo"
        summary.append(["Indicador", "Valor"])
        summary.append(["Estado", state.code])
        summary.append(["Empresas", "Nova + Multi" if state.code == "PE" else "Todas do estado"])
        summary.append(["Data de referência", reference_date])
        summary.append(["Carteira total", indicators["portfolio_total"]])
        summary.append(["Vencido acima de 10 dias", indicators["overdue_over_ten"]])
        summary.append(["Inadimplência (%)", indicators["delinquency_percentage"]])
        summary.append(["Quantidade de títulos", indicators["title_count"]])
        _format_sheet(summary)
        sheets = {name: workbook.create_sheet(name) for name in SHEETS}
        for sheet in sheets.values():
            sheet.append(HEADERS)
        for item in items:
            band = classify_overdue_days(calculate_receivable_overdue_days(item, reference_date)).value
            if band in sheets:
                sheets[band].append(_row(item, reference_date, band))
        for sheet in sheets.values():
            _format_sheet(sheet)
        path = _reports_dir() / f"cobranca_{state.code}_{reference_date:%Y%m%d}.xlsx"
        _save_execution(execution, workbook, path, len(items), {"sheets": ["Resumo", *SHEETS]})
    except Exception as exc:
        execution.status = ReportExecution.Status.FAILED
        execution.error_message = str(exc)
        raise
    finally:
        execution.finished_at = timezone.now()
        execution.save()
    return execution


def generate_band_excel(state_code: str, band: str, reference_date: date) -> ReportExecution:
    if band not in SHEETS:
        raise ValueError(f"Faixa de vencimento inválida: {band}")
    state, _ = State.objects.get_or_create(code=state_code.upper(), defaults={"name": state_code.upper()})
    execution, _ = ReportExecution.objects.get_or_create(
        state=state, report_type=ReportExecution.Type.BAND_EXCEL,
        overdue_band=band, report_date=reference_date,
    )
    execution.status = ReportExecution.Status.PROCESSING
    execution.started_at = timezone.now()
    execution.error_message = ""
    execution.save()
    try:
        items = [
            item for item in _state_items(state)
            if classify_overdue_days(calculate_receivable_overdue_days(item, reference_date)).value == band
        ]
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = band
        sheet.append(HEADERS)
        for item in items:
            sheet.append(_row(item, reference_date, band))
        _format_sheet(sheet)
        path = _reports_dir() / f"cobranca_{state.code}_{band}_{reference_date:%Y%m%d}.xlsx"
        _save_execution(execution, workbook, path, len(items), {
            "band": band,
            "band_label": BAND_LABELS[band],
            "companies": "Nova + Multi" if state.code == "PE" else "Todas do estado",
        })
        pdf_path = generate_band_pdf_file(state.code, band, reference_date, items)
        execution.pdf_file_path = str(pdf_path.resolve())
    except Exception as exc:
        execution.status = ReportExecution.Status.FAILED
        execution.error_message = str(exc)
        raise
    finally:
        execution.finished_at = timezone.now()
        execution.save()
    return execution
