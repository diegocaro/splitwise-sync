"""Receipt parser for extracting transaction data from bank emails."""

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo  # Import ZoneInfo for timezone support

from bs4 import BeautifulSoup

from ..splitwise_api.splitwise_client import CustomExpense
from .email_client import EmailMessage


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


class ReceiptParser:
    """Parser for extracting transaction data from Banco de Chile emails."""

    def parse_email(self, message: EmailMessage) -> Transaction:
        """Parse a Banco de Chile email to extract transaction data."""
        # Extract information using regular expressions
        default_timezone = ZoneInfo("America/Santiago")
        body = message.body
        date = message.date

        # Clean HTML content if present
        if "<html" in body:
            soup = BeautifulSoup(body, "html.parser")
            body = soup.get_text(separator=" ", strip=True)

        text_match = re.search(r"(una compra por .+)\. Revisa", body)
        text = ""
        if text_match:
            text = text_match.group(1).strip()

        # Extract amount and currency
        amount_match = re.search(r"([A-Z]{2,3})?\$\s*([.\d]+)(,\d{2})?", body)
        amount = None
        currency = "CLP"  # Default currency

        if amount_match:
            amount = amount_match.group(2)
            if amount_match.group(3):  # If decimal part exists
                amount += amount_match.group(3)  # Append the decimal part
            if amount_match.group(1):
                currency = amount_match.group(1)

        if amount:
            amount = amount.replace(".", "")  # Remove thousands separators
            amount = float(
                amount.replace(",", ".")
            )  # Convert comma to decimal point and to float
        else:
            amount = 0.0  # Create a transaction without an amount

        # Extract card number (to use as bank reference)
        card_number_match = re.search(r"\*{4}(\d{4})", body)
        bank_reference = card_number_match.group(1) if card_number_match else ""

        # Extract merchant
        # Improved merchant pattern to better handle HTML-cleaned text
        merchant_match = re.search(r"en ([^e]+?) el", body)
        if not merchant_match:
            merchant_match = re.search(r"en (.+?) el", body)

        merchant = (
            merchant_match.group(1).strip() if merchant_match else "Unknown merchant"
        )

        # Extract transaction date
        transaction_date_match = re.search(r"el (\d{2}/\d{2}/\d{4} \d{2}:\d{2})", body)

        if transaction_date_match:
            transaction_date_str = transaction_date_match.group(1)
            parsed_date = datetime.strptime(
                transaction_date_str, "%d/%m/%Y %H:%M"
            ).replace(tzinfo=default_timezone)
        else:
            # Use the email date if transaction date is not found
            parsed_date = date

        return Transaction(
            amount=amount,
            currency=currency,
            date=parsed_date,
            merchant=merchant,
            bank_reference=bank_reference,
            text=text,
        )
