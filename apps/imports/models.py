from django.conf import settings
from django.db import models

from shared.models import TimestampedModel


class ImportBatch(TimestampedModel):
    class Source(models.TextChoices):
        EXCEL = "excel", "Excel"
        LEGACY = "legacy", "Banco legado"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        COMPLETED = "completed", "Concluído"
        FAILED = "failed", "Falhou"

    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file_name = models.CharField(max_length=255, blank=True)
    total_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="import_batches",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["source", "status", "created_at"], name="imports_imp_source_7a540e_idx")]


class ImportRejection(TimestampedModel):
    batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name="rejections")
    row_number = models.PositiveIntegerField()
    reason = models.TextField()
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["row_number"]
