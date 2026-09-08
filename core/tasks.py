from __future__ import annotations

import logging
import os
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from celery import shared_task
from celery.signals import task_failure
from django.conf import settings
from django.utils import timezone

from apps.audit.services import record_audit
from apps.collections.models import AgreementInstallment, CollectionStatus, PaymentAgreement, PaymentPromise
from apps.notifications.email import send_commitment_default_alert
from shared.dates import format_date

from .locking import task_lock

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="core.tasks.run_full_collection_pipeline")
def run_full_collection_pipeline(self: Any) -> dict[str, object]:
    logger.info("full_pipeline_started task_id=%s", self.request.id)

    with task_lock("full_collection_pipeline") as acquired:
        if not acquired:
            logger.warning("full_pipeline_skipped task_id=%s reason=lock_conflict", self.request.id)
            return {"status": "skipped", "reason": "lock_conflict"}

        result: dict[str, object] = {"status": "started", "phases": {}}

        try:
            from apps.imports.tasks import collect_all_sources
            result["phases"]["collection"] = collect_all_sources()
        except Exception:
            result["phases"]["collection"] = {"status": "failed"}
            logger.exception("full_pipeline_collection_failed task_id=%s", self.request.id)

        try:
            from apps.reports.tasks import generate_reports
            result["phases"]["reports"] = generate_reports(reference_date=format_date(date.today()))
        except Exception:
            result["phases"]["reports"] = {"status": "failed"}
            logger.exception("full_pipeline_reports_failed task_id=%s", self.request.id)

        try:
            from apps.notifications.tasks import send_all_reports
            result["phases"]["notification"] = send_all_reports()
        except Exception:
            result["phases"]["notification"] = {"status": "failed"}
            logger.exception("full_pipeline_notification_failed task_id=%s", self.request.id)

        result["status"] = "completed"
        result["completed_at"] = timezone.now().isoformat()
        logger.info("full_pipeline_completed task_id=%s", self.request.id)
        return result


@shared_task(bind=True, name="core.tasks.run_supplementary_collection")
def run_supplementary_collection(self: Any) -> dict[str, object]:
    logger.info("supplementary_collection_started task_id=%s", self.request.id)

    with task_lock("supplementary_collection") as acquired:
        if not acquired:
            logger.warning("supplementary_collection_skipped task_id=%s reason=lock_conflict", self.request.id)
            return {"status": "skipped", "reason": "lock_conflict"}

        try:
            from apps.imports.tasks import collect_all_sources
            result = collect_all_sources()
            logger.info("supplementary_collection_completed task_id=%s", self.request.id)
            return {"status": "completed", "collection": result}
        except Exception:
            logger.exception("supplementary_collection_failed task_id=%s", self.request.id)
            raise


@shared_task(bind=True, name="core.tasks.verify_expired_promises")
def verify_expired_promises(self: Any) -> dict[str, object]:
    logger.info("verify_expired_promises_started task_id=%s", self.request.id)

    with task_lock("verify_expired_promises") as acquired:
        if not acquired:
            logger.warning("verify_expired_promises_skipped task_id=%s reason=lock_conflict", self.request.id)
            return {"status": "skipped", "reason": "lock_conflict"}

        today = date.today()
        expired = PaymentPromise.objects.select_related("receivable").filter(
            promised_date__lt=today,
            status=PaymentPromise.Status.PENDING,
        )
        count = expired.count()

        for promise in expired:
            if promise.receivable.financial_status == promise.receivable.FinancialStatus.PAID:
                promise.status = PaymentPromise.Status.KEPT
                promise.save(update_fields=["status", "updated_at"])
                continue
            promise.status = PaymentPromise.Status.BROKEN
            promise.save(update_fields=["status", "updated_at"])
            collection, _ = CollectionStatus.objects.get_or_create(receivable=promise.receivable)
            collection.status = CollectionStatus.Status.BROKEN_PROMISE
            collection.notes = "Promessa de pagamento não cumprida."
            collection.save(update_fields=["status", "notes", "updated_at"])
            send_commitment_default_alert(
                operator=promise.receivable.operator or promise.created_by,
                receivable=promise.receivable,
                commitment_type="Promessa de pagamento",
                commitment_id=promise.pk,
            )

        overdue_installments = AgreementInstallment.objects.select_related(
            "agreement__receivable__customer", "agreement__receivable__operator", "agreement__created_by"
        ).filter(
            agreement__status=PaymentAgreement.Status.ACTIVE,
            due_date__lt=today,
            paid_at__isnull=True,
        ).order_by("agreement_id", "due_date")
        broken_agreement_ids: set[int] = set()
        for installment in overdue_installments:
            agreement = installment.agreement
            if agreement.pk in broken_agreement_ids:
                continue
            broken_agreement_ids.add(agreement.pk)
            collection, _ = CollectionStatus.objects.get_or_create(receivable=agreement.receivable)
            collection.status = CollectionStatus.Status.BROKEN_AGREEMENT
            collection.notes = "Acordo não cumprido: existe parcela vencida sem pagamento."
            collection.save(update_fields=["status", "notes", "updated_at"])
            send_commitment_default_alert(
                operator=agreement.receivable.operator or agreement.created_by,
                receivable=agreement.receivable,
                commitment_type="Acordo",
                commitment_id=agreement.pk,
            )

        logger.info(
            "verify_expired_promises_completed task_id=%s promises=%s agreements=%s",
            self.request.id, count, len(broken_agreement_ids),
        )
        return {"status": "completed", "expired_count": count, "broken_agreement_count": len(broken_agreement_ids)}


@shared_task(bind=True, name="core.tasks.run_daily_backup")
def run_daily_backup(self: Any) -> dict[str, object]:
    logger.info("daily_backup_started task_id=%s", self.request.id)

    with task_lock("daily_backup") as acquired:
        if not acquired:
            logger.warning("daily_backup_skipped task_id=%s reason=lock_conflict", self.request.id)
            return {"status": "skipped", "reason": "lock_conflict"}

        backup_dir = Path(os.getenv("BACKUPS_DIR", str(settings.BASE_DIR / "backups")))
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        try:
            db_settings = settings.DATABASES["default"]
            if db_settings["ENGINE"] == "django.db.backends.sqlite3":
                db_path = Path(db_settings["NAME"])
                if db_path.is_file():
                    backup_path = backup_dir / f"db_backup_{timestamp}.sqlite3"
                    shutil.copy2(db_path, backup_path)
                    logger.info("sqlite_backup_created path=%s", backup_path)
                    return {"status": "completed", "path": str(backup_path), "engine": "sqlite3"}
            else:
                media_dir = Path(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else None
                if media_dir and media_dir.exists():
                    media_backup = backup_dir / f"media_backup_{timestamp}.zip"
                    shutil.make_archive(str(media_backup.with_suffix("")), "zip", media_dir)
                    logger.info("media_backup_created path=%s", media_backup)
                    return {"status": "completed", "path": str(media_backup), "engine": "postgresql_media_only"}

            logger.warning("daily_backup_nothing_to_do task_id=%s", self.request.id)
            return {"status": "completed", "note": "nothing_to_backup"}
        except Exception:
            logger.exception("daily_backup_failed task_id=%s", self.request.id)
            raise


def _record_task_failure(task_id: str, task_name: str, exception: Exception) -> None:
    try:
        record_audit(
            user=None,
            action="TASK_FAILURE",
            model_name="celery_task",
            object_id=task_id,
            new_value={"task_name": task_name, "error": str(exception)},
            origin="celery",
            reason=f"Task {task_name} failed",
        )
    except Exception:
        logger.exception("failed_to_record_task_failure_audit")


@task_failure.connect
def handle_task_failure(sender: Any = None, task_id: str | None = None, exception: Exception | None = None, **kwargs: Any) -> None:  # noqa: ARG001
    task_name = getattr(sender, "name", str(sender)) if sender else "unknown"
    task_id_str = task_id or "unknown"
    logger.error("celery_task_failure task_name=%s task_id=%s error=%s", task_name, task_id_str, exception)
    _record_task_failure(task_id_str, task_name, exception or Exception("unknown"))
