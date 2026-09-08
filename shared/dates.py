from __future__ import annotations

from datetime import date, datetime
from typing import Any


DISPLAY_DATE_FORMAT = "%m/%d/%Y"
DISPLAY_DATETIME_FORMAT = "%m/%d/%Y %H:%M"
DATE_INPUT_FORMATS = (DISPLAY_DATE_FORMAT, "%Y-%m-%d")


def parse_date(value: Any) -> date:
    """Parse dates using the system contract: MM/DD/YYYY or canonical ISO.

    Native ``date``/``datetime`` values are already unambiguous and are kept as
    dates. String values never use locale inference, preventing 09/01/2026 from
    being read as 9 January.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    value_str = str(value).strip()
    for date_format in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(value_str, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {value}. Use MM/DD/AAAA.")


def format_date(value: date) -> str:
    return value.strftime(DISPLAY_DATE_FORMAT)
