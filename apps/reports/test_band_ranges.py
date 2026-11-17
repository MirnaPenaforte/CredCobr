from datetime import date, timedelta
from decimal import Decimal

import pytest
from openpyxl import load_workbook

from apps.companies.models import Company, State
from apps.customers.models import Customer
from apps.receivables.models import Receivable
from apps.reports.generators.excel import generate_state_excel


@pytest.mark.django_db
def test_report_ranges_keep_every_title_in_all_duplicates(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    reference = date(2026, 11, 17)
    state = State.objects.create(code="CE", name="Ceará")
    company = Company.objects.create(name="Empresa CE", state=state)
    customer = Customer.objects.create(identifier="C-1", name="Cliente")
    days_by_sheet = {
        "3_10": (3, 10),
        "11_30": (11, 30),
        "31_59": (31, 59),
        "60_plus": (60, 361),
    }
    all_days = (0, 1, 2, *(day for days in days_by_sheet.values() for day in days))
    for days in all_days:
        Receivable.objects.create(
            company=company,
            customer=customer,
            title_number=f"T-{days}",
            installment="1",
            outstanding_amount=Decimal("10"),
            due_date=reference - timedelta(days=days),
        )

    execution = generate_state_excel("CE", reference)
    workbook = load_workbook(execution.file_path, read_only=True)
    assert workbook.sheetnames == ["Resumo", "Todas as duplicatas", *days_by_sheet]
    all_titles = workbook["Todas as duplicatas"]
    assert all_titles.max_row == len(all_days) + 1
    assert {row[0] for row in list(all_titles.values)[1:]} == {f"T-{days}" for days in all_days}
    for sheet_name, days in days_by_sheet.items():
        assert {row[0] for row in list(workbook[sheet_name].values)[1:]} == {
            f"T-{day}" for day in days
        }
    workbook.close()
