import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from splitwise_sync.core.models import Transaction
from splitwise_sync.core.transaction_store import TransactionStore


# Mock classes to simulate Splitwise objects
class FakeUser:
    """Mock for Splitwise User objects."""

    def __init__(self, id="1", email="test@example.com"):
        self.id = id
        self.email = email


class FakeExpense:
    def __init__(self, id="12345"):
        self.id = id
        self.created_by = FakeUser()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def store_path(temp_dir):
    """Create a path for the test transaction store."""
    return Path(temp_dir) / "test_transactions.json"


@pytest.fixture
def store(store_path: Path):
    """Create a transaction store instance."""
    return TransactionStore(store_path)


@pytest.fixture
def transaction():
    """Create a sample transaction."""
    return Transaction(
        cost=10.99,
        currency_code="USD",
        date=datetime.now(),
        description="Test Merchant",
        card_number="1234",
        details="Test purchase",
    )


def test_add_and_contains(
    store: TransactionStore, store_path: Path, transaction: Transaction
):
    """Test adding a transaction and checking if it exists."""
    assert not transaction.hash in store

    expense = FakeExpense(id="12345")
    store.add(transaction, expense)

    assert transaction.hash in store
    assert store_path.exists()

    with open(store_path, "r") as f:
        data = json.load(f)

    assert transaction.hash in data
    assert data[transaction.hash]["expense_id"] == "12345"
    assert data[transaction.hash]["transaction"]["description"] == "Test Merchant"
    assert "created_by_id" in data[transaction.hash]
    assert "created_by_email" in data[transaction.hash]


def test_persistence(
    store: TransactionStore, store_path: Path, transaction: Transaction
):
    """Test that transactions persist when a new store is created."""
    expense = FakeExpense(id="12345")
    store.add(transaction, expense)

    # Create a new store instance with the same path
    new_store = TransactionStore(store_path)

    # It should still contain the transaction
    assert transaction.hash in new_store
