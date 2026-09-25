from __future__ import annotations

import logging
from pathlib import Path

from django.db import transaction

from .models import ReportExecution

logger = logging.getLogger(__name__)


def _managed_file(path_value: str, reports_dir: Path) -> Path | None:
    if not path_value:
        return None
    candidate = reports_dir / Path(path_value).name
    return candidate if candidate.resolve().parent == reports_dir.resolve() else None


def supersede_old_reports(current: ReportExecution, reports_dir: Path) -> int:
    """Keep one downloadable report per state and type, preserving notification history."""
    old_paths: list[str] = []
    with transaction.atomic():
        previous = list(
            ReportExecution.objects.select_for_update()
            .filter(
                state=current.state,
                report_type=current.report_type,
                status=ReportExecution.Status.COMPLETED,
            )
            .exclude(pk=current.pk)
        )
        for report in previous:
            old_paths.extend((report.file_path, report.pdf_file_path))
            report.status = ReportExecution.Status.SUPERSEDED
            report.file_path = ""
            report.pdf_file_path = ""
            report.save(update_fields=["status", "file_path", "pdf_file_path", "updated_at"])

    current_path = _managed_file(current.file_path, reports_dir)
    for path_value in old_paths:
        old_path = _managed_file(path_value, reports_dir)
        if old_path is None or old_path == current_path:
            continue
        if old_path.is_file():
            old_path.unlink()
            logger.info("old_report_removed path=%s", old_path)
        for part in reports_dir.glob(f"{old_path.stem}_*.xlsx"):
            if part.is_file():
                part.unlink()
    return len(previous)
