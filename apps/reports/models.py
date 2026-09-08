from django.db import models

from shared.models import TimestampedModel


class ReportExecution(TimestampedModel):
    class Type(models.TextChoices):
        STATE_EXCEL = "state_excel", "Excel estadual consolidado"
        BAND_EXCEL = "band_excel", "Excel por faixa"
        EXECUTIVE_PDF = "executive_pdf", "PDF executivo"

    class Band(models.TextChoices):
        DAYS_1_10 = "1_10", "Até 10 dias"
        DAYS_11_30 = "11_30", "De 11 a 30 dias"
        DAYS_31_90 = "31_90", "De 31 a 90 dias"
        DAYS_91_360 = "91_360", "De 91 a 360 dias"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        COMPLETED = "completed", "Concluído"
        FAILED = "failed", "Falhou"

    state = models.ForeignKey("companies.State", on_delete=models.PROTECT, null=True, blank=True)
    report_type = models.CharField(max_length=30, choices=Type.choices, default=Type.STATE_EXCEL)
    overdue_band = models.CharField(max_length=20, choices=Band.choices, blank=True)
    report_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file_path = models.CharField(max_length=500, blank=True)
    pdf_file_path = models.CharField(max_length=500, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    rows_processed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["report_date", "status", "report_type"], name="reports_rep_report__801238_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["state", "report_type", "overdue_band", "report_date"],
                name="unique_state_band_report_per_date",
            )
        ]

    def __str__(self) -> str:
        state = self.state.code if self.state else "GERAL"
        band = f" - {self.get_overdue_band_display()}" if self.overdue_band else ""
        return f"{self.get_report_type_display()} - {state}{band} - {self.report_date}"
