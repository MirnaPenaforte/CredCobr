from decimal import Decimal

from django.conf import settings
from django.db import models

from shared.models import TimestampedModel


class Receivable(TimestampedModel):
    class FinancialStatus(models.TextChoices):
        OPEN = "open", "Em aberto"
        PARTIALLY_PAID = "partially_paid", "Parcialmente pago"
        PAID = "paid", "Pago"
        CANCELLED = "cancelled", "Cancelado"

    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="receivables")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="receivables")
    title_number = models.CharField(max_length=100)
    installment = models.CharField(max_length=30, default="1")
    original_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    interest_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    penalty_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    outstanding_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    issued_at = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    source_overdue_days = models.PositiveIntegerField(default=0, help_text="Dias de atraso informados pela fonte (ATR)")
    term_days = models.PositiveIntegerField(default=0)
    interest_rate = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal("0"))
    daily_interest_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    balance_with_interest = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    source_status = models.CharField(max_length=20, blank=True)
    seller = models.CharField(max_length=160, blank=True)
    agent_code = models.CharField(max_length=40, blank=True)
    origin_establishment_code = models.CharField(max_length=40, blank=True)
    establishment_code = models.CharField(max_length=40, blank=True)
    financial_status = models.CharField(max_length=20, choices=FinancialStatus.choices, default=FinancialStatus.OPEN)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_receivables",
        null=True,
        blank=True,
    )
    source_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "title_number", "installment"],
                name="unique_receivable_identity",
            ),
            models.CheckConstraint(
                condition=models.Q(outstanding_amount__gte=0),
                name="receivable_outstanding_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["due_date", "financial_status"]),
            models.Index(fields=["company", "due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title_number}/{self.installment}"
