from __future__ import annotations

from datetime import date

from celery import shared_task

from .services import generate_all_reports
from shared.dates import format_date, parse_date


@shared_task(name="apps.reports.tasks.generate_reports")
def generate_reports(*, reference_date: str | None = None) -> dict[str, object]:
    target_date = parse_date(reference_date) if reference_date else date.today()
    executions = generate_all_reports(reference_date=target_date)
    return {
        "reference_date": format_date(target_date),
        "count": len(executions),
        "executions": [
            {"id": item.pk, "state": item.state.code if item.state else None, "status": item.status}
            for item in executions
        ],
    }
