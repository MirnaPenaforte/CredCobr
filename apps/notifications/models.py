from django.db import models

from shared.models import TimestampedModel


class Recipient(TimestampedModel):
    class Profile(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrador"
        MANAGER = "manager", "Gestor"

    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    profile = models.CharField(max_length=20, choices=Profile.choices)
    state = models.ForeignKey("companies.State", on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["state", "profile", "active"])]


class Notification(TimestampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENT = "sent", "Enviada"
        FAILED = "failed", "Falhou"
        DELIVERED = "delivered", "Entregue"
        READ = "read", "Lida"

    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    recipient = models.ForeignKey(Recipient, on_delete=models.PROTECT, related_name="notifications")
    report_execution = models.ForeignKey("reports.ReportExecution", on_delete=models.PROTECT, null=True, blank=True)
    template_name = models.CharField(max_length=160, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["channel", "status"]), models.Index(fields=["provider_message_id"])]
