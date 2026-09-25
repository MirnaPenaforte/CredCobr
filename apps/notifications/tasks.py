from __future__ import annotations

import logging
from typing import Any
from pathlib import Path

from celery import shared_task
from django.utils import timezone
from openpyxl import load_workbook

from apps.accounts.models import User
from apps.reports.models import ReportExecution
from core.locking import task_lock

from .attachments import plan_report_attachments
from .email import send_report_email
from .models import Notification, Recipient

logger = logging.getLogger(__name__)

REPORT_TYPE_LABELS = {
    ReportExecution.Type.STATE_EXCEL: "Boletos vencidos",
    ReportExecution.Type.UPCOMING_EXCEL: "Boletos a vencer",
}
DELIVERY_REPORT_TYPES = (ReportExecution.Type.STATE_EXCEL, ReportExecution.Type.UPCOMING_EXCEL)
OVERDUE_BAND_SUBJECT = "5-10 dias, 11-30 dias, 31-90 dias, 91-360 dias"
OVERDUE_BANDS = {
    "5_10": "5-10 dias",
    "11_30": "11-30 dias",
    "31_90": "31-90 dias",
    "91_360": "91-360 dias",
}


def report_subject(*, state_code: str, report_type: str, overdue_bands: tuple[str, ...] | None = None) -> str:
    subject = f"Relatório de cobrança - {state_code} - {REPORT_TYPE_LABELS.get(report_type, report_type)}"
    if report_type == ReportExecution.Type.STATE_EXCEL:
        bands = ", ".join(overdue_bands or tuple(OVERDUE_BANDS.values()))
        subject += f" - {bands or OVERDUE_BAND_SUBJECT}"
    return subject


def _bands_in_attachment(path: Path) -> tuple[str, ...]:
    workbook = load_workbook(path, read_only=True)
    try:
        return tuple(OVERDUE_BANDS[name] for name in OVERDUE_BANDS if name in workbook.sheetnames)
    finally:
        workbook.close()


def reports_by_state(reference_date) -> dict[str, dict[str, ReportExecution]]:
    reports = ReportExecution.objects.filter(
        report_date=reference_date,
        status=ReportExecution.Status.COMPLETED,
        state__isnull=False,
        report_type__in=DELIVERY_REPORT_TYPES,
    ).select_related("state")
    return {
        state_code: {report.report_type: report for report in reports if report.state.code == state_code}
        for state_code in {report.state.code for report in reports}
    }


def _recipient_for(user: User) -> Recipient:
    recipient, _ = Recipient.objects.get_or_create(
        email=user.email,
        defaults={
            "name": user.get_full_name() or user.username,
            "phone_number": user.whatsapp_number,
            "profile": Recipient.Profile.ADMINISTRATOR if user.role == User.Role.ADMINISTRATOR else Recipient.Profile.MANAGER,
        },
    )
    return recipient


def deliver_reports_for_user(
    user: User,
    state_reports_map: dict[str, dict[str, ReportExecution]],
    reference_date,
    *,
    force: bool = False,
) -> list[dict[str, object]]:
    """Deliver one e-mail per report for each state the user is subscribed to."""
    recipient = _recipient_for(user)
    results: list[dict[str, object]] = []
    for state in user.report_states.all():
        state_reports = state_reports_map.get(state.code, {})
        for report_type in DELIVERY_REPORT_TYPES:
            report = state_reports.get(report_type)
            if not report:
                logger.warning(
                    "report_email_skipped user_id=%s state=%s report_type=%s reason=report_missing",
                    user.pk, state.code, report_type,
                )
                continue
            try:
                base_subject = report_subject(
                    state_code=state.code,
                    report_type=report_type,
                )
                parts = plan_report_attachments(report.file_path)
                notifications: list[Notification] = []
                if len(parts) <= 1:
                    notifications = send_report_email(
                        report=report,
                        recipients=[recipient],
                        subject=base_subject,
                        force=force,
                    )
                else:
                    for index, part in enumerate(parts, start=1):
                        part_bands = _bands_in_attachment(part)
                        notifications.extend(send_report_email(
                            report=report,
                            recipients=[recipient],
                            subject=(
                                f"{report_subject(state_code=state.code, report_type=report_type, overdue_bands=part_bands)} "
                                f"({index}/{len(parts)})"
                            ),
                            attach_report=False,
                            extra_paths=[part],
                            force=force,
                        ))
                results.append({
                    "user_id": user.pk,
                    "state": state.code,
                    "report_type": report_type,
                    "sent": len(notifications),
                    "status": "sent" if len(notifications) == max(1, len(parts)) else "failed",
                    "report_id": report.pk,
                    "messages": max(1, len(parts)),
                })
            except Exception:
                results.append({"user_id": user.pk, "state": state.code, "report_type": report_type, "status": "failed"})
                logger.exception(
                    "email_send_failed_in_pipeline user_id=%s state=%s report_type=%s",
                    user.pk, state.code, report_type,
                )
    return results


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
def send_all_reports(self: Any, force: bool = False) -> dict[str, object]:
    """Send one e-mail per report, for each state every active user is subscribed to.

    A user subscribed to more than one state receives more than one e-mail: one
    message for every state/report combination (vencidos and a vencer). When
    ``force`` is true, already-sent reports are delivered again.
    """
    logger.info("send_all_reports_started task_id=%s", self.request.id)
    reference_date = timezone.localdate()
    state_reports_map = reports_by_state(reference_date)
    users = User.objects.filter(is_active=True).exclude(email="").prefetch_related("report_states")
    results: list[dict[str, object]] = []
    for user in users:
        results.extend(deliver_reports_for_user(user, state_reports_map, reference_date, force=force))
    return {"results": results, "reference_date": reference_date.isoformat(), "total_deliveries": len(results), "failed_deliveries": sum(item.get("status") == "failed" for item in results)}


@shared_task(bind=True, name="apps.notifications.tasks.send_user_reports")
def send_user_reports(self: Any, user_id: int, force: bool = True) -> dict[str, object]:
    """Deliver the report e-mails for a single user (used by the user management screen)."""
    logger.info("send_user_reports_started task_id=%s user_id=%s", self.request.id, user_id)
    with task_lock(f"send_user_reports:{user_id}", timeout=7200) as acquired:
        if not acquired:
            logger.warning("send_user_reports_skipped user_id=%s reason=already_running", user_id)
            return {"user_id": user_id, "status": "skipped", "reason": "already_running"}
        reference_date = timezone.localdate()
        user = User.objects.get(pk=user_id)
        state_reports_map = reports_by_state(reference_date)
        results = deliver_reports_for_user(user, state_reports_map, reference_date, force=force)
        return {"user_id": user_id, "results": results, "reference_date": reference_date.isoformat(), "total_deliveries": len(results)}
