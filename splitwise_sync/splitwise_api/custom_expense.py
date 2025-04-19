from dataclasses import dataclass
from typing import Optional


@dataclass
class CustomExpense:
    """Model representing a custom expense for Splitwise."""

    cost: str
    description: str
    date: str
    category_id: Optional[int] = None
    details: Optional[str] = None
    currency_code: str = "CLP"
