import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from splitwise_sync.core.models import Transaction
from splitwise_sync.core.transaction_store import TransactionStore


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
    # Initially the store should be empty
    assert not transaction.hash in store

    # Add the transaction
    store.add(transaction, "12345")

    # Now it should contain the transaction
    assert transaction.hash in store

    # Check that the file was created with the correct content
    assert store_path.exists()

    with open(store_path, "r") as f:
        data = json.load(f)

    assert transaction.hash in data
    assert data[transaction.hash]["expense_id"] == "12345"
    assert data[transaction.hash]["transaction"]["description"] == "Test Merchant"


def test_persistence(
    store: TransactionStore, store_path: Path, transaction: Transaction
):
    """Test that transactions persist when a new store is created."""
    # Add a transaction
    store.add(transaction, "12345")

    # Create a new store instance with the same path
    new_store = TransactionStore(store_path)

    # It should still contain the transaction
    assert transaction.hash in new_store
