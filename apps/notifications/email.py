from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.reports.models import ReportExecution

from .models import Notification, Recipient

logger = logging.getLogger(__name__)


@transaction.atomic
def send_commitment_default_alert(*, operator, receivable, commitment_type: str, commitment_id: int) -> Notification | None:
    """Alert the assigned operator once when a promise or agreement is broken."""
    if operator is None or not operator.email:
        logger.warning("commitment_default_alert_skipped receivable_id=%s reason=operator_without_email", receivable.pk)
        return None

    profile = Recipient.Profile.ADMINISTRATOR if operator.role == "administrator" else Recipient.Profile.MANAGER
    recipient = Recipient.objects.filter(email__iexact=operator.email).first()
    if recipient is None:
        recipient = Recipient.objects.create(
            name=operator.get_full_name() or operator.username,
            email=operator.email,
            phone_number=operator.whatsapp_number,
            profile=profile,
        )

    key = f"commitment-default:{commitment_type}:{commitment_id}:operator:{operator.pk}"
    notification, _ = Notification.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "channel": Notification.Channel.EMAIL,
            "recipient": recipient,
            "template_name": "commitment_default_alert",
            "payload": {
                "commitment_type": commitment_type,
                "customer": receivable.customer.name,
                "receivable_id": receivable.pk,
                "title_number": receivable.title_number,
            },
        },
    )
    if notification.status in {Notification.Status.SENT, Notification.Status.DELIVERED, Notification.Status.READ}:
        return notification

    notification.attempts += 1
    try:
        subject = f"Atenção: {commitment_type} não cumprido — {receivable.customer.name}"
        body = (
            f"O cliente {receivable.customer.name} possui um(a) {commitment_type.lower()} não cumprido(a).\n\n"
            f"Título: {receivable.title_number}\n"
            f"Saldo devido: R$ {receivable.balance_with_interest:,.2f}\n"
            "O cliente voltou a compor os rankings de devedores."
        )
        EmailMultiAlternatives(subject=subject, body=body, from_email=None, to=[recipient.email]).send(fail_silently=False)
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.error_message = ""
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error_message = str(exc)
        logger.exception("commitment_default_alert_failed notification_id=%s", notification.pk)
    notification.save(update_fields=["attempts", "status", "sent_at", "error_message", "updated_at"])
    return notification


@transaction.atomic
def send_report_email(
    *,
    report: ReportExecution,
    recipients: Iterable[Recipient],
    attachments: Iterable[ReportExecution] | None = None,
    subject: str | None = None,
    force: bool = False,
) -> list[Notification]:
    sent: list[Notification] = []
    for recipient in recipients:
        if not recipient.active or not recipient.email:
            continue
        key = f"email:{report.pk}:{recipient.pk}"
        notification, created = Notification.objects.get_or_create(
            idempotency_key=key,
            defaults={
                "channel": Notification.Channel.EMAIL,
                "recipient": recipient,
                "report_execution": report,
                "payload": {"subject": subject or "Relatorio de cobranca"},
            },
        )
        if notification.status == Notification.Status.SENT and not force:
            sent.append(notification)
            continue
        notification.attempts += 1
        try:
            email = EmailMultiAlternatives(
                subject=subject or f"Relatorio de cobranca - {report.report_date:%m/%d/%Y}",
                body="Relatorio de cobranca em anexo.",
                from_email=None,
                to=[recipient.email],
            )
            email.attach_alternative(render_to_string("notifications/report_email.html", {"recipient": recipient, "report": report}), "text/html")
            for attachment_report in attachments or [report]:
                if not attachment_report.file_path:
                    continue
                path = Path(attachment_report.file_path)
                if path.is_file():
                    email.attach(path.name, path.read_bytes(), "application/octet-stream")
            email.send(fail_silently=False)
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.error_message = ""
            sent.append(notification)
        except Exception as exc:
            notification.status = Notification.Status.FAILED
            notification.error_message = str(exc)
            logger.exception("email_notification_failed notification_id=%s", notification.pk)
        notification.save(update_fields=["attempts", "status", "sent_at", "error_message", "updated_at"])
    return sent
