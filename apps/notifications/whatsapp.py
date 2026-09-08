from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import httpx
from django.db import transaction
from django.utils import timezone

from .models import Notification, Recipient

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.version = os.getenv("META_GRAPH_API_VERSION", "v21.0")
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "")
        self.token = os.getenv("META_WHATSAPP_TOKEN", "")
        self.client = client or httpx.Client(timeout=float(os.getenv("META_TIMEOUT", "15")))

    @transaction.atomic
    def send_template(
        self,
        *,
        recipient: Recipient,
        template_name: str,
        parameters: list[str] | None = None,
        idempotency_key: str,
    ) -> Notification:
        notification, _ = Notification.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "channel": Notification.Channel.WHATSAPP,
                "recipient": recipient,
                "template_name": template_name,
                "payload": {"parameters": parameters or []},
            },
        )
        if notification.status in {Notification.Status.SENT, Notification.Status.DELIVERED, Notification.Status.READ}:
            return notification
        if not self.phone_number_id or not self.token or not recipient.phone_number:
            raise ValueError("Configuracao Meta ou telefone do destinatario ausente")
        notification.attempts += 1
        try:
            response = self.client.post(
                f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient.phone_number,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": "pt_BR"},
                        "components": [{"type": "body", "parameters": [{"type": "text", "text": value} for value in (parameters or [])]}],
                    },
                },
            )
            response.raise_for_status()
            body = response.json()
            notification.provider_message_id = str(body.get("messages", [{}])[0].get("id", ""))
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.error_message = ""
        except Exception as exc:
            notification.status = Notification.Status.FAILED
            notification.error_message = str(exc)
            logger.exception("whatsapp_notification_failed notification_id=%s", notification.pk)
        notification.save(update_fields=["attempts", "provider_message_id", "status", "sent_at", "error_message", "updated_at"])
        if notification.status == Notification.Status.FAILED:
            raise RuntimeError("Falha no envio WhatsApp")
        return notification

    def send_state_summary(self, *, recipient: Recipient, state_code: str, indicators: dict[str, object], report_date: str, idempotency_key: str) -> Notification:
        parameters = [
            state_code,
            report_date,
            str(indicators.get("portfolio_total", "0")),
            str(indicators.get("overdue_over_ten", "0")),
            str(indicators.get("delinquency_percentage", "0")),
        ]
        return self.send_template(
            recipient=recipient,
            template_name=os.getenv("META_SUMMARY_TEMPLATE", "collection_summary"),
            parameters=parameters,
            idempotency_key=idempotency_key,
        )


def validate_webhook_signature(body: bytes, signature: str, app_secret: str | None = None) -> bool:
    secret = app_secret or os.getenv("META_APP_SECRET", "")
    if not secret or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)
