from __future__ import annotations

import hashlib
import os
from datetime import date
from pathlib import Path

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.processing.services import calculate_indicators, consolidate_by_state
from apps.receivables.models import Receivable
from apps.reports.models import ReportExecution


def generate_band_pdf_file(state_code: str, band: str, reference_date: date, items: list[Receivable]) -> Path:
    reports_dir = Path(os.getenv("REPORTS_DIR", "reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"cobranca_{state_code}_{band}_{reference_date:%Y%m%d}.pdf"
    document = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    document.setTitle(f"Relatório de cobrança {state_code} - {band}")
    document.setFont("Helvetica-Bold", 16)
    document.drawString(50, height - 55, f"Relatório de boletos vencidos - {state_code}")
    document.setFont("Helvetica", 10)
    document.drawString(50, height - 75, f"Faixa: {band} | Data de referência: {reference_date:%m/%d/%Y}")
    document.drawString(50, height - 90, f"Empresas: {'Nova + Multi' if state_code == 'PE' else 'Todas do estado'}")
    y = height - 120
    document.setFont("Helvetica-Bold", 9)
    document.drawString(50, y, "Título")
    document.drawString(150, y, "Cliente")
    document.drawString(350, y, "Empresa")
    document.drawString(455, y, "Saldo")
    y -= 14
    document.setFont("Helvetica", 8)
    for item in items:
        if y < 45:
            document.showPage()
            y = height - 50
        document.drawString(50, y, str(item.title_number)[:16])
        document.drawString(150, y, str(item.customer.name)[:32])
        document.drawString(350, y, str(item.company.name)[:16])
        document.drawRightString(535, y, f"R$ {item.outstanding_amount:,.2f}")
        y -= 12
    document.save()
    return path


def generate_executive_pdf(reference_date: date) -> ReportExecution:
    execution = ReportExecution.objects.create(
        report_type=ReportExecution.Type.EXECUTIVE_PDF,
        report_date=reference_date,
        status=ReportExecution.Status.PROCESSING,
        started_at=timezone.now(),
    )
    reports_dir = Path(os.getenv("REPORTS_DIR", "reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"resumo_executivo_{reference_date:%Y%m%d}.pdf"
    try:
        items = list(Receivable.objects.select_related("company__state", "customer"))
        indicators = calculate_indicators(items, reference_date)
        states = consolidate_by_state(items, reference_date)
        document = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        document.setTitle("Resumo executivo de cobrança")
        document.setFont("Helvetica-Bold", 18)
        document.drawString(50, height - 60, "Resumo executivo de cobrança")
        document.setFont("Helvetica", 11)
        document.drawString(50, height - 84, f"Data de referência: {reference_date:%m/%d/%Y}")
        y = height - 120
        rows = [
            ("Carteira total", indicators["portfolio_total"]),
            ("Vencido acima de 10 dias", indicators["overdue_over_ten"]),
            ("Inadimplência", f'{indicators["delinquency_percentage"]}%'),
        ]
        for label, value in rows:
            document.drawString(50, y, f"{label}: {value}")
            y -= 22
        for code, values in sorted(states.items()):
            y -= 12
            document.setFont("Helvetica-Bold", 12)
            document.drawString(50, y, code)
            document.setFont("Helvetica", 10)
            document.drawString(95, y, f'Carteira: {values["portfolio_total"]} | Inadimplência: {values["delinquency_percentage"]}%')
        document.save()
        execution.file_path = str(path.resolve())
        execution.checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        execution.rows_processed = len(items)
        execution.status = ReportExecution.Status.COMPLETED
    except Exception as exc:
        execution.status = ReportExecution.Status.FAILED
        execution.error_message = str(exc)
        raise
    finally:
        execution.finished_at = timezone.now()
        execution.save()
    return execution
