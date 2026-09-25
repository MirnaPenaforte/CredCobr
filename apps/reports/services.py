from __future__ import annotations

from datetime import date
from typing import Iterable

from .generators.excel import generate_state_excel, generate_upcoming_excel
from .models import ReportExecution


def generate_all_reports(
    *,
    reference_date: date | None = None,
    states: Iterable[str] | None = None,
) -> list[ReportExecution]:
    target_date = reference_date or date.today()
    state_codes = list(states) if states is not None else ["CE", "BA", "PE"]
    executions: list[ReportExecution] = []
    for code in state_codes:
        executions.append(generate_state_excel(code, target_date))
        executions.append(generate_upcoming_excel(code, target_date))
    return executions
