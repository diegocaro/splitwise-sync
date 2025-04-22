"""Receipt parser for extracting transaction data from bank emails."""

import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .models import EmailMessage, Transaction

logger = logging.getLogger(__name__)


class ReceiptParser:
    """Parser for extracting transaction data from Banco de Chile emails."""

    def __init__(self):
        self.default_timezone = ZoneInfo("America/Santiago")

    def parse_email(self, message: EmailMessage) -> Transaction:
        """Parse a Banco de Chile email to extract transaction data."""
        # Clean and prepare the email body
        body = self._clean_body(message.body)

        # Extract all required transaction components
        text = self._extract_transaction_text(body)
        amount, currency = self._extract_amount_and_currency(body)
        bank_reference = self._extract_bank_reference(body)
        merchant = self._extract_merchant(body)
        parsed_date = self._extract_transaction_date(body)

        # Create and return the transaction
        return Transaction(
            amount=amount,
            currency=currency,
            date=parsed_date,
            merchant=merchant,
            bank_reference=bank_reference,
            text=text,
        )

    def _clean_body(self, body: str) -> str:
        """Clean HTML content if present."""
        if "<html" in body:
            soup = BeautifulSoup(body, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        return body

    def _extract_transaction_text(self, body: str) -> str:
        """Extract transaction description text."""
        text_match = re.search(r"(una compra por .+)\. Revisa", body)
        return text_match.group(1).strip() if text_match else ""

    def _extract_amount_and_currency(self, body: str) -> tuple[float, str]:
        """Extract amount and currency from the email body."""
        amount_match = re.search(r"([A-Z]{2,3})?\$\s*([.\d]+)(,\d{2})?", body)
        currency = "CLP"  # Default currency

        if not amount_match:
            logger.error("No amount found in the email")
            raise ValueError("No amount found in the email")

        amount = amount_match.group(2)
        if amount_match.group(3):  # If decimal part exists
            amount += amount_match.group(3)  # Append the decimal part
        if amount_match.group(1):
            currency = amount_match.group(1)

        # Process amount to standard format
        amount = amount.replace(".", "")  # Remove thousands separators
        amount = float(
            amount.replace(",", ".")
        )  # Convert comma to decimal point and to float

        return amount, currency

    def _extract_bank_reference(self, body: str) -> str:
        """Extract card number to use as bank reference."""
        card_number_match = re.search(r"\*{4}(\d{4})", body)
        if not card_number_match:
            logger.error("No card number found in the email")
            raise ValueError("No card number found in the email")

        return card_number_match.group(1)  # Extract last 4 digits

    def _extract_merchant(self, body: str) -> str:
        """Extract merchant name from the email body."""
        merchant_match = re.search(r"en ([^e]+?) el", body)
        if not merchant_match:
            merchant_match = re.search(r"en (.+?) el", body)

        if not merchant_match:
            logger.error("No merchant found in the email")
            raise ValueError("No merchant found in the email")

        return merchant_match.group(1).strip()

    def _extract_transaction_date(self, body: str) -> datetime:
        """Extract transaction date from the email body."""
        transaction_date_match = re.search(r"el (\d{2}/\d{2}/\d{4} \d{2}:\d{2})", body)

        if not transaction_date_match:
            logger.error("No transaction date found in the email")
            raise ValueError("No transaction date found in the email")

        transaction_date_str = transaction_date_match.group(1)
        return datetime.strptime(transaction_date_str, "%d/%m/%Y %H:%M").replace(
            tzinfo=self.default_timezone
        )
