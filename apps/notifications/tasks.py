from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from apps.reports.models import ReportExecution

from .email import send_report_email
from .models import Notification, Recipient

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.notifications.tasks.send_emails_for_state")
def send_emails_for_state(self: Any, report_execution_id: int) -> dict[str, object]:
    logger.info("email_send_started task_id=%s report_id=%s", self.request.id, report_execution_id)
    try:
        report = ReportExecution.objects.select_related("state").get(pk=report_execution_id)
        state_code = getattr(report.state, "code", None)
        filters: dict[str, Any] = {"active": True}
        if state_code:
            filters["state__code"] = state_code
        recipients = Recipient.objects.filter(**filters)
        notifications = send_report_email(report=report, recipients=recipients)
        result = {
            "report_id": report.pk,
            "state": state_code,
            "sent": len(notifications),
            "notification_ids": [n.pk for n in notifications],
        }
        logger.info("email_send_completed task_id=%s sent=%s", self.request.id, len(notifications))
        return result
    except Exception:
        logger.exception("email_send_failed task_id=%s report_id=%s", self.request.id, report_execution_id)
        raise


@shared_task(bind=True, name="apps.notifications.tasks.send_all_reports")
def send_all_reports(self: Any) -> dict[str, object]:
    logger.info("send_all_reports_started task_id=%s", self.request.id)
    reports = ReportExecution.objects.filter(status=ReportExecution.Status.COMPLETED, state__isnull=False)
    results: list[dict[str, object]] = []
    for report in reports:
        try:
            single_result = send_emails_for_state(report.pk)
            results.append(single_result)
        except Exception:
            results.append({"report_id": report.pk, "status": "failed"})
            logger.exception("email_send_failed_in_pipeline report_id=%s", report.pk)
    return {"results": results, "total_reports": len(results)}
