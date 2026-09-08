from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.reports.generators.pdf import generate_executive_pdf
from apps.reports.services import generate_all_reports
from shared.dates import format_date, parse_date


class Command(BaseCommand):
    help = "Gera relatórios estaduais de cobrança e o resumo executivo opcional."

    def add_arguments(self, parser):
        parser.add_argument("--date")
        parser.add_argument("--state", choices=["CE", "BA", "PE"])
        parser.add_argument("--pdf", action="store_true")

    def handle(self, *args, **options):
        try:
            target_date = parse_date(options["date"]) if options.get("date") else date.today()
        except ValueError as exc:
            raise CommandError("Use a data no formato MM/DD/AAAA") from exc
        states = [options["state"]] if options.get("state") else ["CE", "BA", "PE"]
        executions = generate_all_reports(reference_date=target_date, states=states)
        self.stdout.write(f"Data de referência: {format_date(target_date)}")
        for execution in executions:
            self.stdout.write(f"{execution.state.code}: {execution.status} - {execution.file_path}")
        if options["pdf"]:
            execution = generate_executive_pdf(target_date)
            self.stdout.write(f"PDF executivo: {execution.status} - {execution.file_path}")
