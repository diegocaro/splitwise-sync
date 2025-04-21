from dataclasses import asdict, dataclass
from datetime import datetime
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


@dataclass
class Transaction:
    """Model representing a bank transaction extracted from an email."""

    amount: float
    currency: str
    date: datetime
    merchant: str
    bank_reference: str
    text: Optional[str] = None
    category: Optional[str] = None

    def to_splitwise_expense(self) -> CustomExpense:
        """Convert transaction to Splitwise expense format."""
        return CustomExpense(
            cost=str(self.amount),
            description=self.merchant,
            date=self.date.isoformat(),
            category_id=None,  # Will be implemented in phase 2
            details=(
                self.text if self.text else f"Bank reference: {self.bank_reference}"
            ),
            currency_code=self.currency,
        )

    def to_dict(self) -> dict[str, str]:
        """Convert transaction to dictionary format."""
        ans = asdict(self)
        ans["date"] = self.date.isoformat()
        return ans


@dataclass
class EmailMessage:
    """Model for an email message."""

    id: str
    subject: str
    sender: str
    date: datetime
    body: str

    def to_dict(self) -> dict[str, str]:
        """Convert the email message to a dictionary."""
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "date": self.date.isoformat(),
            "body": self.body,
        }
