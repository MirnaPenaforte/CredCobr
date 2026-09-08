from __future__ import annotations

import logging
import os
import re
from typing import Any

from celery import shared_task
from django.utils import timezone

from .adapters.sql import LegacySqlAdapter
from .models import ImportBatch
from .services import persist_records

logger = logging.getLogger(__name__)

LEGACY_DATABASE_VIEW = os.getenv("LEGACY_DATABASE_VIEW", "VW_DASH_FIN_BOL_A_")
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", LEGACY_DATABASE_VIEW):
    raise ValueError("LEGACY_DATABASE_VIEW deve conter somente um identificador SQL")

LEGACY_COLLECTION_YEAR = os.getenv("LEGACY_COLLECTION_YEAR", "2026")
if not re.fullmatch(r"\d{4}", LEGACY_COLLECTION_YEAR):
    raise ValueError("LEGACY_COLLECTION_YEAR deve conter um ano de quatro dígitos")

NEXT_COLLECTION_YEAR = int(LEGACY_COLLECTION_YEAR) + 1


def _column(columns: set[str], *candidates: str, required: bool = True) -> str | None:
    available = {name.lower(): name for name in columns}
    for candidate in candidates:
        if candidate.lower() in available:
            return f"[{available[candidate.lower()]}]"
    if required:
        raise ValueError(f"Coluna obrigatória ausente: {' ou '.join(candidates)}")
    return None


def build_legacy_query(columns: set[str]) -> str:
    """Build a normalized SELECT for both the old and the new BI view layouts."""
    title = _column(columns, "Num_Documento", "Cod_Documento")
    installment = _column(columns, "boleto_pacela", "boleto_parcela", "Par_Documento")
    document = _column(columns, "CNPJ", "Cgc_Cpf")
    group_name = _column(columns, "Gp_Cliente", "Des_GrpCli")
    establishment = _column(columns, "Estabecimento", "Estabelecimento", "Cod_Estabe")
    source_reference = _column(columns, "Cod_Documento", "Num_Documento")
    due_date = _column(columns, "Dat_Vencimento")
    issued_at = _column(columns, "Dat_Emissao")

    def optional(*candidates: str, default: str = "''") -> str:
        return _column(columns, *candidates, required=False) or default

    return f"""SELECT
    CAST({title} AS varchar(100)) AS title_number,
    CAST({installment} AS varchar(30)) AS installment,
    CAST({document} AS varchar(80)) AS customer_identifier,
    CAST({_column(columns, 'Razao_Social')} AS varchar(180)) AS customer_name,
    CAST({establishment} AS varchar(160)) AS company,
    CAST({_column(columns, 'UF')} AS varchar(2)) AS state,
    {_column(columns, 'Vlr_Documento')} AS original_amount,
    {_column(columns, 'Vlr_Atual')} AS outstanding_amount,
    CONVERT(date, {due_date}, 101) AS due_date,
    CONVERT(date, {issued_at}, 101) AS issued_at,
    {_column(columns, 'Vlr_Jrs+Mult')} AS interest_amount,
    0 AS penalty_amount,
    CAST({group_name} AS varchar(160)) AS economic_group,
    {_column(columns, 'Dias_Atraso')} AS source_overdue_days,
    CAST({source_reference} AS varchar(120)) AS source_reference,
    {_column(columns, 'Per_Juros')} AS interest_rate,
    {_column(columns, 'Vlr_Atual')} AS balance_with_interest,
    {optional('Ao_Dia', default='0')} AS daily_interest_amount,
    CAST({optional('Status_Documento')} AS varchar(20)) AS source_status,
    CAST({document} AS varchar(18)) AS customer_document,
    CAST({optional('Cidade')} AS varchar(120)) AS customer_city,
    CAST({optional('Vendedor')} AS varchar(160)) AS seller,
    CAST({optional('Cod_GrpCli')} AS varchar(40)) AS economic_group_code,
    CAST({optional('Cod_Agente')} AS varchar(40)) AS agent_code,
    CAST({optional('Cod_EstOri')} AS varchar(40)) AS origin_establishment_code,
    CAST({optional('Cod_Estabe')} AS varchar(40)) AS establishment_code
FROM {LEGACY_DATABASE_VIEW}
WHERE CONVERT(date, {issued_at}, 101) >= DATEFROMPARTS({LEGACY_COLLECTION_YEAR}, 1, 1)
  AND CONVERT(date, {issued_at}, 101) < DATEFROMPARTS({NEXT_COLLECTION_YEAR}, 1, 1)"""


LEGACY_COLUMNS = {
    "Dias_Atraso", "Dat_Vencimento", "Dat_Emissao", "Vlr_Documento", "Per_Juros",
    "Ao_Dia", "Vlr_Jrs+Mult", "Vlr_Atual", "Status_Documento", "Num_Documento",
    "Cod_Documento", "Par_Documento", "Cgc_Cpf", "Razao_Social", "UF", "Vendedor",
    "Cod_GrpCli", "Des_GrpCli", "Cod_Agente", "Cod_EstOri", "Cod_Estabe",
}
DEFAULT_LEGACY_QUERY = build_legacy_query(LEGACY_COLUMNS)


def _run_adapter(source: str, adapter: Any) -> dict[str, object]:
    batch = ImportBatch.objects.create(
        source=source,
        status=ImportBatch.Status.PROCESSING,
        started_at=timezone.now(),
    )
    try:
        records = adapter.fetch()
        imported = persist_records(records)
        batch.total_rows = len(records)
        batch.imported_rows = imported
        batch.status = ImportBatch.Status.COMPLETED
    except Exception as exc:
        batch.status = ImportBatch.Status.FAILED
        batch.error_message = str(exc)
        raise
    finally:
        batch.finished_at = timezone.now()
        batch.save()
    return {"batch_id": batch.pk, "status": batch.status, "imported_rows": batch.imported_rows}


@shared_task(name="apps.imports.tasks.collect_from_legacy_database")
def collect_from_legacy_database() -> dict[str, object]:
    custom_query = os.getenv("LEGACY_DATABASE_QUERY", "").strip()
    adapter = LegacySqlAdapter(
        driver=os.getenv("DB_DRIVER", ""),
        host=os.getenv("DB_HOST", ""),
        port=int(os.getenv("DB_PORT", "1433")),
        database=os.getenv("DB_NAME", ""),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASS", ""),
        query=custom_query,
        schema_view=LEGACY_DATABASE_VIEW,
        query_builder=None if custom_query else build_legacy_query,
    )
    return _run_adapter(ImportBatch.Source.LEGACY, adapter)


@shared_task(name="apps.imports.tasks.collect_all_sources")
def collect_all_sources() -> dict[str, object]:
    results: dict[str, object] = {}
    for name, task in (("legacy", collect_from_legacy_database),):
        try:
            results[name] = task()
        except Exception as exc:
            logger.exception("source_collection_failed source=%s", name)
            results[name] = {"status": "failed", "error": str(exc)}
    return results
