import json
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    """Model representing a bank transaction extracted from an email."""

    cost: float
    currency_code: str
    date: datetime
    description: str  # the merchant name
    card_number: str
    details: str  # the note in the app
    category_id: Optional[str] = None

    __HASH_FIELDS = [
        "cost",
        "description",
        "date",
        "card_number",
    ]

    @property
    def cost_str(self) -> str:
        """Return the cost as a string with two decimal places."""
        return f"{self.cost:.2f}"

    @property
    def date_str(self) -> str:
        """Return the date as a string in YYYY-MM-DD format."""
        return self.date.isoformat()

    def to_dict(self) -> dict[str, str]:
        """Convert transaction to dictionary format."""
        ans = asdict(self)
        ans["date"] = self.date_str
        ans["hash"] = self.hash
        return ans

    @property
    def hash_str(self) -> str:
        """Return a hash of the transaction for uniqueness."""
        return "_".join(str(getattr(self, field)) for field in self.__HASH_FIELDS)

    @property
    def hash(self) -> str:
        """Return a hash of the transaction for uniqueness."""
        return sha256(self.hash_str.encode()).hexdigest()

    @property
    def details_with_metadata(self) -> str:
        """Return a footer for the transaction."""
        metadata = json.dumps(
            {
                "card_number": self.card_number,
                "hash": self.hash,
                "date": self.date_str,
            }
        )
        return f"{self.details}\n\n{metadata}"


@dataclass(frozen=True)
class EmailMessage:
    """Model for an email message."""

    uid: str
    subject: str
    sender: str
    to: tuple[str, ...]
    date: datetime
    body: str

    def to_dict(self) -> dict[str, str]:
        """Convert the email message to a dictionary."""
        ans = asdict(self)
        ans["date"] = self.date.isoformat()
        return ans
