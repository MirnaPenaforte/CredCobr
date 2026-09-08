from __future__ import annotations

from datetime import date
from decimal import Decimal
import re
from typing import Any, Callable

from apps.imports.records import NormalizedReceivableRecord
from shared.dates import parse_date


class LegacySqlAdapter:
    def __init__(
        self,
        *,
        driver: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        query: str = "",
        schema_view: str = "",
        query_builder: Callable[[set[str]], str] | None = None,
        connection_factory: Callable[..., Any] | None = None,
    ) -> None:
        if driver.lower() != "mssql":
            raise ValueError("O banco legado deve utilizar o driver mssql")
        clean_query = query.strip().rstrip(";")
        if clean_query:
            self._validate_query(clean_query)
        elif not schema_view or query_builder is None:
            raise ValueError("Informe uma consulta ou uma visão com construtor de consulta")
        elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema_view):
            raise ValueError("A visão deve conter somente um identificador SQL")
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.query = clean_query
        self.schema_view = schema_view
        self.query_builder = query_builder
        self.connection_factory = connection_factory

    @staticmethod
    def _validate_query(query: str) -> None:
        if ";" in query or not query.lower().startswith("select"):
            raise ValueError("A consulta legada deve conter um único SELECT somente leitura")

    @staticmethod
    def _text(value: Any) -> str:
        return "" if value is None else str(value).strip()

    @staticmethod
    def _to_date(value: Any) -> date:
        return parse_date(value)

    @staticmethod
    def _to_record(row: tuple[Any, ...]) -> NormalizedReceivableRecord:
        return NormalizedReceivableRecord(
            title_number=LegacySqlAdapter._text(row[0]),
            installment=LegacySqlAdapter._text(row[1]),
            customer_identifier=LegacySqlAdapter._text(row[2]),
            customer_name=LegacySqlAdapter._text(row[3]),
            company=LegacySqlAdapter._text(row[4]),
            state=LegacySqlAdapter._text(row[5]).upper(),
            original_amount=Decimal(str(row[6])), outstanding_amount=Decimal(str(row[7])),
            due_date=LegacySqlAdapter._to_date(row[8]),
            issued_at=LegacySqlAdapter._to_date(row[9]) if row[9] else None,
            interest_amount=Decimal(str(row[10] or 0)),
            penalty_amount=Decimal(str(row[11] or 0)),
            economic_group=LegacySqlAdapter._text(row[12]),
            # Algumas views representam títulos a vencer com Dias_Atraso negativo.
            # O campo local é estritamente "dias em atraso"; para títulos ainda
            # vigentes, o valor correto é zero. A classificação usa due_date.
            source_overdue_days=max(int(row[13] or 0), 0) if len(row) > 13 else 0,
            source_reference=LegacySqlAdapter._text(row[14]) if len(row) > 14 else "",
            interest_rate=Decimal(str(row[15] or 0)) if len(row) > 15 else Decimal("0"),
            balance_with_interest=Decimal(str(row[16] or 0)) if len(row) > 16 else Decimal("0"),
            daily_interest_amount=Decimal(str(row[17] or 0)) if len(row) > 17 else Decimal("0"),
            source_status=LegacySqlAdapter._text(row[18]) if len(row) > 18 else "",
            customer_document=LegacySqlAdapter._text(row[19]) if len(row) > 19 else "",
            customer_city=LegacySqlAdapter._text(row[20]) if len(row) > 20 else "",
            seller=LegacySqlAdapter._text(row[21]) if len(row) > 21 else "",
            economic_group_code=LegacySqlAdapter._text(row[22]) if len(row) > 22 else "",
            agent_code=LegacySqlAdapter._text(row[23]) if len(row) > 23 else "",
            origin_establishment_code=LegacySqlAdapter._text(row[24]) if len(row) > 24 else "",
            establishment_code=LegacySqlAdapter._text(row[25]) if len(row) > 25 else "",
        )

    def fetch(self) -> list[NormalizedReceivableRecord]:
        if not all((self.host, self.database, self.user)):
            return []
        if self.connection_factory is None:
            import pymssql

            connection = pymssql.connect(
                server=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
        else:
            connection = self.connection_factory(
                server=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
        with connection:
            with connection.cursor() as cursor:
                query = self.query
                if not query:
                    cursor.execute(f"SELECT TOP 0 * FROM {self.schema_view}")
                    columns = {str(item[0]) for item in cursor.description}
                    query = self.query_builder(columns)
                    self._validate_query(query)
                cursor.execute(query)
                return [self._to_record(row) for row in cursor.fetchall()]
