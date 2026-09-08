from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class NormalizedReceivableRecord:
    title_number: str
    installment: str
    customer_identifier: str
    customer_name: str
    company: str
    state: str
    original_amount: Decimal
    outstanding_amount: Decimal
    due_date: date
    source_overdue_days: int = 0
    issued_at: date | None = None
    interest_amount: Decimal = Decimal("0")
    penalty_amount: Decimal = Decimal("0")
    economic_group: str = ""
    source_reference: str = ""
    term_days: int = 0
    interest_rate: Decimal = Decimal("0")
    balance_with_interest: Decimal = Decimal("0")
    daily_interest_amount: Decimal = Decimal("0")
    source_status: str = ""
    customer_document: str = ""
    customer_city: str = ""
    seller: str = ""
    economic_group_code: str = ""
    agent_code: str = ""
    origin_establishment_code: str = ""
    establishment_code: str = ""
