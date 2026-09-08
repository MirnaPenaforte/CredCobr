from decimal import Decimal

from django.conf import settings
from django.db import models

from shared.models import TimestampedModel


class CollectionStatus(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        CONTACTED = "contacted", "Contactado"
        PROMISE = "promise", "Promessa registrada"
        NEGOTIATING = "negotiating", "Em negociacao"
        PAID = "paid", "Pago"
        UNREACHABLE = "unreachable", "Nao localizado"
        BROKEN_PROMISE = "broken_promise", "Promessa não cumprida"

    receivable = models.OneToOneField("receivables.Receivable", on_delete=models.PROTECT, related_name="collection_status")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    expected_payment_date = models.DateField(null=True, blank=True)
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    next_action = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)


class CollectionInteraction(TimestampedModel):
    class Channel(models.TextChoices):
        PHONE = "phone", "Telefone"
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        OTHER = "other", "Outro"

    receivable = models.ForeignKey("receivables.Receivable", on_delete=models.PROTECT, related_name="interactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="collection_interactions")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    notes = models.TextField()
    next_action = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]


class PaymentPromise(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        KEPT = "kept", "Cumprida"
        BROKEN = "broken", "Quebrada"
        CANCELLED = "cancelled", "Cancelada"

    receivable = models.ForeignKey("receivables.Receivable", on_delete=models.PROTECT, related_name="payment_promises")
    promised_date = models.DateField()
    promised_amount = models.DecimalField(max_digits=14, decimal_places=2)
    is_total_value = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["promised_date", "status"])]


class PaymentAgreement(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        COMPLETED = "completed", "Concluido"
        CANCELLED = "cancelled", "Cancelado"

    receivable = models.ForeignKey("receivables.Receivable", on_delete=models.PROTECT, related_name="agreements")
    negotiated_amount = models.DecimalField(max_digits=14, decimal_places=2)
    installment_count = models.PositiveIntegerField()
    periodicity_days = models.PositiveIntegerField(default=30)
    is_total_value = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(negotiated_amount__gte=0), name="agreement_amount_non_negative"),
            models.CheckConstraint(condition=models.Q(installment_count__gt=0), name="agreement_installments_positive"),
        ]


class AgreementInstallment(TimestampedModel):
    agreement = models.ForeignKey(PaymentAgreement, on_delete=models.PROTECT, related_name="installments")
    number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["agreement", "number"], name="unique_agreement_installment")]
