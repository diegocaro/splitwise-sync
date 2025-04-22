from datetime import datetime
from hashlib import sha256

import pytest

from splitwise_sync.core.models import Transaction


@pytest.fixture
def sample_date():
    return datetime(2025, 4, 21, 12, 30, 15)


@pytest.fixture
def sample_transaction(sample_date: datetime):
    return Transaction(
        cost=49.99,
        currency_code="USD",
        date=sample_date,
        description="Coffee Shop",
        card_number="1234",
        details="Morning coffee with colleagues",
        category_id="food",
    )


def test_cost_str(sample_transaction: Transaction, sample_date: datetime):
    """Test that cost_str returns properly formatted cost."""
    assert sample_transaction.cost_str == "49.99"

    # Test with zero decimal places
    transaction = Transaction(
        cost=50.0,
        currency_code="USD",
        date=sample_date,
        description="Coffee Shop",
        card_number="1234",
        details="Morning coffee",
    )
    assert transaction.cost_str == "50.00"

    # Test with more than two decimal places
    transaction = Transaction(
        cost=50.123,
        currency_code="USD",
        date=sample_date,
        description="Coffee Shop",
        card_number="1234",
        details="Morning coffee",
    )
    assert transaction.cost_str == "50.12"


def test_date_str(sample_transaction: Transaction, sample_date: datetime):
    """Test that date_str returns date in ISO format."""
    expected_date_str = sample_date.isoformat()
    assert sample_transaction.date_str == expected_date_str


def test_to_dict(sample_transaction: Transaction, sample_date: datetime):
    """Test that to_dict converts transaction to dict with proper formatting."""
    transaction_dict = sample_transaction.to_dict()

    assert isinstance(transaction_dict, dict)
    assert transaction_dict["cost"] == 49.99
    assert transaction_dict["currency_code"] == "USD"
    assert transaction_dict["date"] == sample_date.isoformat()
    assert transaction_dict["description"] == "Coffee Shop"
    assert transaction_dict["card_number"] == "1234"
    assert transaction_dict["details"] == "Morning coffee with colleagues"
    assert transaction_dict["category_id"] == "food"


def test_hash_str(sample_transaction: Transaction):
    """Test that hash_str returns the correct string for hashing."""
    s = sample_transaction
    expected_hash_str = f"{s.cost}_{s.description}_{s.date}_{s.card_number}"
    assert sample_transaction.hash_str == expected_hash_str


def test_hash(sample_transaction: Transaction):
    """Test that hash returns the correct SHA256 hash."""
    hash_str = sample_transaction.hash_str
    expected_hash = sha256(hash_str.encode()).hexdigest()
    assert sample_transaction.hash == expected_hash


def test_equality(sample_transaction: Transaction, sample_date: datetime):
    """Test that two transactions with identical fields are equal."""
    transaction2 = Transaction(
        cost=49.99,
        currency_code="USD",
        date=sample_date,
        description="Coffee Shop",
        card_number="1234",
        details="Morning coffee with colleagues",
        category_id="food",
    )
    assert sample_transaction == transaction2


def test_immutability(sample_transaction: Transaction):
    """Test that the transaction is immutable (frozen)."""
    with pytest.raises(Exception):
        sample_transaction.cost = 100.0
