from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError

from apps.imports.adapters.sql import LegacySqlAdapter
from apps.imports.models import ImportBatch
from apps.imports.tasks import LEGACY_DATABASE_VIEW, _run_adapter, build_legacy_query
from apps.reports.services import generate_all_reports


class Command(BaseCommand):
    help = "Executa coleta, processamento e geração de relatórios de cobrança."

    def add_arguments(self, parser):
        parser.add_argument("--state", choices=["CE", "BA", "PE"])
        parser.add_argument("--source", choices=["all", "legacy"], default="all")
        parser.add_argument("--skip-collection", action="store_true")
        parser.add_argument("--send", action="store_true")

    def handle(self, *args, **options):
        state = options.get("state")
        if not options["skip_collection"]:
            if options["source"] in {"all", "legacy"}:
                try:
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
                    result = _run_adapter(ImportBatch.Source.LEGACY, adapter)
                    self.stdout.write(f"Coleta legada: batch {result['batch_id']} - {result['status']} ({result['imported_rows']} títulos)")
                    if result["status"] != "completed" or result["imported_rows"] <= 0:
                        raise CommandError("Coleta legada não trouxe títulos; relatórios não foram gerados")
                except CommandError:
                    raise
                except Exception as exc:
                    raise CommandError(f"Falha no banco legado: {exc}") from exc
        states = [state] if state else ["CE", "BA", "PE"]
        generate_all_reports(states=states)
        self.stdout.write(self.style.SUCCESS(f"Pipeline concluido para {', '.join(states)}"))
