from __future__ import annotations

from datetime import date
from typing import Iterable

from apps.companies.models import State

from .generators.excel import SHEETS, generate_band_excel, generate_state_excel
from .generators.pdf import generate_executive_pdf
from .models import ReportExecution


def generate_all_reports(
    *,
    reference_date: date | None = None,
    states: Iterable[str] | None = None,
    include_pdf: bool = False,
) -> list[ReportExecution]:
    target_date = reference_date or date.today()
    state_codes = list(states or State.objects.filter(code__in=["CE", "BA", "PE"]).values_list("code", flat=True))
    if not state_codes:
        state_codes = ["CE", "BA", "PE"]
    executions: list[ReportExecution] = []
    for code in state_codes:
        executions.append(generate_state_excel(code, target_date))
        executions.extend(generate_band_excel(code, band, target_date) for band in SHEETS)
    if include_pdf:
        executions.append(generate_executive_pdf(target_date))
    return executions
