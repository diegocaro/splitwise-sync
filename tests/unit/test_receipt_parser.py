"""Unit tests for the receipt parser."""

from datetime import datetime
from pathlib import Path

import pytest

from splitwise_sync.core.email_client import EmailMessage
from splitwise_sync.core.receipt_parser import ReceiptParser, Transaction


@pytest.fixture
def parser() -> ReceiptParser:
    """Fixture providing a ReceiptParser instance."""
    return ReceiptParser()


@pytest.fixture
def email_content() -> str:
    """Fixture providing test email content."""
    test_email_path = Path(__file__).parent / "email-body.txt"
    with open(test_email_path, "r", encoding="utf-8") as file:
        email_html = file.read()
    return email_html


def create_email(body: str) -> EmailMessage:
    """Fixture providing email metadata."""
    return EmailMessage(
        uid="123456789",
        subject="Compra con tu Tarjeta de Crédito Banco de Chile",
        sender="notificaciones@bancochile.cl",
        to="user@gmail.com",
        date=datetime.fromisoformat("2025-04-19T14:40:00Z"),
        body=body,
    )


def test_transaction_parsing() -> None:
    """Test that Transaction objects are properly created and populated."""
    # Create a transaction directly to test the model
    transaction = Transaction(
        cost=1190.0,
        details="Test transaction",
        date=datetime(2025, 4, 19, 14, 33),
        description="Test Merchant",
        card_number="7766",
        currency_code="CLP",
    )

    # Verify attributes
    assert transaction.cost == 1190.0
    assert transaction.details == "Test transaction"
    assert transaction.description == "Test Merchant"
    assert transaction.card_number == "7766"
    assert transaction.currency_code == "CLP"


def test_no_transaction_when_no_amount(parser: ReceiptParser) -> None:
    """Test that no transaction is returned when amount can't be extracted."""
    email_body = "This email does not contain any transaction amount details"

    # Email with no amount information
    message = create_email(email_body)

    with pytest.raises(ValueError, match="No amount found in the email"):
        parser.parse_email(message)


def test_parse_html_email(parser: ReceiptParser, email_content: str) -> None:
    """Test parsing an HTML email using BeautifulSoup."""

    # Create a mock email message with the HTML content
    message = create_email(email_content)

    # Parse the email
    transaction = parser.parse_email(message)

    # Verify transaction details
    assert transaction is not None
    assert transaction.cost == 1190.0
    assert transaction.card_number == "7766"
    assert (
        transaction.details
        == "una compra por $1.190 con Tarjeta de Crédito ****7766 en SPID MUT - O871        SANTIAGO      CHL el 19/04/2025 14:33"
    )
    assert "SPID MUT" in transaction.description
    assert "SANTIAGO" in transaction.description
    assert transaction.currency_code == "CLP"  # Verify currency is correctly set

    # Verify date format
    assert transaction.date is not None
    assert isinstance(transaction.date, datetime)
