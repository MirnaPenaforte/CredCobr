from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO, Iterable

import pandas as pd
from django.db import transaction
from django.utils import timezone

from apps.companies.models import Company, EconomicGroup, State
from apps.customers.models import Customer
from apps.receivables.models import Receivable
from shared.dates import parse_date

from .models import ImportBatch, ImportRejection
from .records import NormalizedReceivableRecord

REQUIRED_HEADERS = {
    "id_titulo", "parcela", "id_cliente", "nome_cliente", "empresa",
    "estado", "valor_original", "saldo_em_aberto", "vencimento",
}


@dataclass(frozen=True, slots=True)
class ImportResult:
    batch_id: int
    total_rows: int
    imported_rows: int
    rejected_rows: int


def _decimal(value: Any) -> Decimal:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    normalized = str(value).strip().replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif normalized.count(".") > 1:
        normalized = normalized.replace(".", "")
    elif "." in normalized and len(normalized.rsplit(".", 1)[1]) == 3:
        normalized = normalized.replace(".", "")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetário inválido: {value}") from exc


def _date(value: Any) -> date:
    return parse_date(value)


def normalize_mapping(row: dict[str, Any]) -> NormalizedReceivableRecord:
    issued_at = row.get("emissao")
    return NormalizedReceivableRecord(
        title_number=str(row["id_titulo"]).strip(),
        installment=str(row.get("parcela", "1")).strip(),
        customer_identifier=str(row["id_cliente"]).strip(),
        customer_name=str(row["nome_cliente"]).strip(),
        company=str(row["empresa"]).strip(),
        state=str(row["estado"]).strip().upper(),
        original_amount=_decimal(row["valor_original"]),
        outstanding_amount=_decimal(row["saldo_em_aberto"]),
        due_date=_date(row["vencimento"]),
        issued_at=_date(issued_at) if issued_at not in (None, "") and not pd.isna(issued_at) else None,
        interest_amount=_decimal(row.get("juros", 0)),
        penalty_amount=_decimal(row.get("multa", 0)),
        economic_group=str(row.get("grupo", "") or "").strip(),
        source_reference=str(row.get("referencia_origem", "") or "").strip(),
    )


@transaction.atomic
def persist_records(records: Iterable[NormalizedReceivableRecord]) -> int:
    unique_records: dict[tuple[str, str, str, str], NormalizedReceivableRecord] = {}
    for record in records:
        if record.state not in {"CE", "BA", "PE"}:
            raise ValueError(f"Estado não autorizado: {record.state}")
        if not all((record.company, record.customer_identifier, record.title_number, record.installment)):
            raise ValueError("Empresa, cliente, documento e parcela são obrigatórios")
        unique_records[(record.state, record.company, record.title_number, record.installment)] = record

    normalized = list(unique_records.values())
    state_codes = {record.state for record in normalized}
    State.objects.bulk_create(
        [State(code=code, name=code) for code in state_codes],
        ignore_conflicts=True,
    )
    states = {item.code: item for item in State.objects.filter(code__in=state_codes)}

    group_records = {record.economic_group: record for record in normalized if record.economic_group}
    EconomicGroup.objects.bulk_create(
        [
            EconomicGroup(name=name, source_code=record.economic_group_code)
            for name, record in group_records.items()
        ],
        update_conflicts=True,
        unique_fields=["name"],
        update_fields=["source_code", "updated_at"],
    )
    groups = {
        item.name: item
        for item in EconomicGroup.objects.filter(name__in=group_records)
    }

    company_records = {(record.state, record.company): record for record in normalized}
    Company.objects.bulk_create(
        [
            Company(
                state=states[state_code],
                name=name,
                source_code=record.establishment_code,
                origin_code=record.origin_establishment_code,
            )
            for (state_code, name), record in company_records.items()
        ],
        update_conflicts=True,
        unique_fields=["state", "name"],
        update_fields=["source_code", "origin_code", "updated_at"],
    )
    companies = {
        (item.state.code, item.name): item
        for item in Company.objects.select_related("state").filter(state__code__in=state_codes)
    }

    customer_records = {record.customer_identifier: record for record in normalized}
    Customer.objects.bulk_create(
        [
            Customer(
                identifier=identifier,
                name=record.customer_name,
                document=record.customer_document or identifier,
                city=record.customer_city,
                economic_group=groups.get(record.economic_group),
            )
            for identifier, record in customer_records.items()
        ],
        update_conflicts=True,
        unique_fields=["identifier"],
        update_fields=["name", "document", "city", "economic_group", "updated_at"],
    )
    customers = {
        item.identifier: item
        for item in Customer.objects.filter(identifier__in=customer_records)
    }

    update_fields = [
        "customer", "original_amount", "term_days", "interest_rate", "daily_interest_amount",
        "balance_with_interest", "interest_amount", "penalty_amount", "outstanding_amount",
        "issued_at", "due_date", "source_overdue_days", "source_reference", "source_status",
        "seller", "agent_code", "origin_establishment_code", "establishment_code", "updated_at",
    ]
    for start in range(0, len(normalized), 1000):
        batch = normalized[start:start + 1000]
        Receivable.objects.bulk_create(
            [
                Receivable(
                    company=companies[(record.state, record.company)],
                    customer=customers[record.customer_identifier],
                    title_number=record.title_number,
                    installment=record.installment,
                    original_amount=record.original_amount,
                    term_days=record.term_days,
                    interest_rate=record.interest_rate,
                    daily_interest_amount=record.daily_interest_amount,
                    balance_with_interest=record.balance_with_interest,
                    interest_amount=record.interest_amount,
                    penalty_amount=record.penalty_amount,
                    outstanding_amount=record.outstanding_amount,
                    issued_at=record.issued_at,
                    due_date=record.due_date,
                    source_overdue_days=record.source_overdue_days,
                    source_reference=record.source_reference,
                    source_status=record.source_status,
                    seller=record.seller,
                    agent_code=record.agent_code,
                    origin_establishment_code=record.origin_establishment_code,
                    establishment_code=record.establishment_code,
                )
                for record in batch
            ],
            batch_size=500,
            update_conflicts=True,
            unique_fields=["company", "title_number", "installment"],
            update_fields=update_fields,
        )
    return len(normalized)


def import_excel(uploaded_file: BinaryIO, *, user: Any = None) -> ImportResult:
    file_name = Path(getattr(uploaded_file, "name", "upload.xlsx")).name
    if Path(file_name).suffix.lower() != ".xlsx":
        raise ValueError("Somente arquivos .xlsx são aceitos")
    frame = pd.read_excel(uploaded_file, engine="openpyxl")
    missing = REQUIRED_HEADERS.difference(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")

    batch = ImportBatch.objects.create(
        source=ImportBatch.Source.EXCEL,
        status=ImportBatch.Status.PROCESSING,
        file_name=file_name,
        total_rows=len(frame),
        created_by=user,
        started_at=timezone.now(),
    )
    valid: list[NormalizedReceivableRecord] = []
    for index, row in frame.iterrows():
        payload = row.where(pd.notna(row), None).to_dict()
        try:
            valid.append(normalize_mapping(payload))
        except (KeyError, ValueError, TypeError) as exc:
            ImportRejection.objects.create(
                batch=batch,
                row_number=int(index) + 2,
                reason=str(exc),
                payload={key: str(value) for key, value in payload.items()},
            )
    imported = persist_records(valid)
    batch.imported_rows = imported
    batch.rejected_rows = len(frame) - imported
    batch.status = ImportBatch.Status.COMPLETED
    batch.finished_at = timezone.now()
    batch.save(update_fields=["imported_rows", "rejected_rows", "status", "finished_at", "updated_at"])
    return ImportResult(batch.pk, len(frame), imported, batch.rejected_rows)


def import_legacy_collection_report(uploaded_file: BinaryIO, *, user: Any = None, default_state: str = "PE", default_company: str = "NOVA PE") -> ImportResult:
    """Importa o relatório legado de posição de cobrança (XLS).

    O arquivo não possui estado/empresa; esses campos devem ser fornecidos pelo contexto
    da origem para não serem inferidos a partir de dados inexistentes na planilha.
    """
    file_name = Path(getattr(uploaded_file, "name", "cobranca.xls")).name
    frame = pd.read_excel(uploaded_file, header=5, engine="xlrd")
    required = {"GRUPO", "Cod_Cliente", "Num_Documento", "Par_Documento", "EMISSÃO", "Dat_Vencimento", "Vlr_Documento", "Vlr_Saldo", "TOT JUROS", "ATR"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    state = str(default_state).strip().upper()
    if state not in {"CE", "BA", "PE"}:
        raise ValueError(f"Estado não autorizado: {state}")
    batch = ImportBatch.objects.create(source=ImportBatch.Source.EXCEL, status=ImportBatch.Status.PROCESSING, file_name=file_name, total_rows=len(frame), created_by=user, started_at=timezone.now())
    valid: list[NormalizedReceivableRecord] = []
    for index, row in frame.iterrows():
        payload = row.where(pd.notna(row), None).to_dict()
        try:
            code = str(payload["Cod_Cliente"]).strip()
            if not code or code.lower() == "nan": raise ValueError("código do cliente vazio")
            valid.append(NormalizedReceivableRecord(title_number=str(payload["Num_Documento"]).strip(), installment=str(payload["Par_Documento"]).strip(), customer_identifier=code, customer_name=f"Cliente {code}", company=default_company, state=state, original_amount=_decimal(payload["Vlr_Documento"]), outstanding_amount=_decimal(payload["Vlr_Saldo"]), due_date=_date(payload["Dat_Vencimento"]), source_overdue_days=max(int(payload["ATR"] or 0), 0), issued_at=_date(payload["EMISSÃO"]), interest_amount=_decimal(payload["TOT JUROS"]), term_days=int(payload["C_Prazo"] or 0), interest_rate=_decimal(payload["%JUR"]), balance_with_interest=_decimal(payload["SLD+JUR"]), economic_group=str(payload["GRUPO"] or "").strip(), source_reference=file_name))
        except (KeyError, ValueError, TypeError) as exc:
            ImportRejection.objects.create(batch=batch, row_number=int(index) + 7, reason=str(exc), payload={key: str(value) for key, value in payload.items()})
    imported = persist_records(valid)
    batch.imported_rows = imported; batch.rejected_rows = len(frame) - imported; batch.status = ImportBatch.Status.COMPLETED; batch.finished_at = timezone.now(); batch.save(update_fields=["imported_rows", "rejected_rows", "status", "finished_at", "updated_at"])
    return ImportResult(batch.pk, len(frame), imported, batch.rejected_rows)
