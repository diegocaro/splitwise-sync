import json
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from typing import Optional

import pandas as pd

from splitwise_sync.config import DEFAULT_TIMEZONE


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
    hash: str = ""  # populated in __post_init__

    __HASH_FIELDS = [
        "cost",
        "description",
        "date",
        "card_number",
    ]

    def __post_init__(self):
        """Post-initialization to set the hash and date."""
        object.__setattr__(self, "hash", self._hash)

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
    def _hash_str(self) -> str:
        """Return a hash of the transaction for uniqueness."""
        return "_".join(str(getattr(self, field)) for field in self.__HASH_FIELDS)

    @property
    def _hash(self) -> str:
        """Return a hash of the transaction for uniqueness."""
        return sha256(self._hash_str.encode()).hexdigest()

    @property
    def details_with_metadata(self) -> str:
        """Return a footer for the transaction."""
        json_str = json.dumps(self.to_dict())
        return f"{self.details}\n\n{json_str}"

    def to_dataframe(
        self, timezone: str = DEFAULT_TIMEZONE, prefix: str = "transaction_"
    ) -> pd.DataFrame:
        """Convert a list of transactions to a dictionary for DataFrame."""

        df = pd.DataFrame([asdict(self)])
        df["date"] = pd.to_datetime(df["date"])
        if timezone:
            df["date"] = df["date"].dt.tz_convert(timezone)

        df = df.rename(columns={col: f"{prefix}{col}" for col in df.columns})

        return df

    def to_series(
        self, timezone: str = DEFAULT_TIMEZONE, prefix: str = "transaction_"
    ) -> pd.Series:
        """Convert a transaction to a Series for DataFrame."""
        return self.to_dataframe(timezone=timezone, prefix=prefix).iloc[0]


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
