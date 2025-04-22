import json
import logging
from datetime import datetime
from pathlib import Path

from splitwise.expense import Expense  # type: ignore

from splitwise_sync.core.models import Transaction

logger = logging.getLogger(__name__)


class TransactionStore:
    """Store for processed transactions to ensure idempotency."""

    def __init__(self, store_path: Path):
        """Initialize the transaction store.

        Args:
            store_path: Path to the JSON file that stores processed transactions
        """
        self.store_path = store_path
        self._transactions: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load the stored transactions from the JSON file."""
        transactions = {}
        if not self.store_path.exists():
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                "Transaction store file %s does not exist. Creating a new one.",
                self.store_path,
            )
            with open(self.store_path, "w") as f:
                json.dump(transactions, f, indent=4)
        try:
            with open(self.store_path, "r") as f:
                transactions = json.load(f)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode JSON file %s. Starting with an empty store.",
                self.store_path,
            )

        self._transactions = transactions

    def __del__(self):
        """Ensure the transactions are saved when the object is deleted."""
        self._save()

    def _save(self) -> None:
        """Save the transactions to the JSON file."""
        with open(self.store_path, "w") as f:
            json.dump(self._transactions, f, indent=4)

    def __contains__(self, transaction_hash: str) -> bool:
        return transaction_hash in self._transactions

    def add(self, transaction: Transaction, expense: Expense) -> None:
        """Add a transaction to the store.

        Args:
            transaction: The transaction that was processed
            expense_id: The ID of the created Splitwise expense
        """
        item = {
            "transaction": transaction.to_dict(),
            "expense_id": str(expense.id),
            "processed_at": datetime.now().isoformat(),
            "created_by_id": str(expense.created_by.id),
            "created_by_email": str(expense.created_by.email),
        }
        self._transactions[transaction.hash] = item
        self._save()
