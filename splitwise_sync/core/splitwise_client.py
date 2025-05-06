"""Splitwise API client for managing expenses."""

import logging
from typing import Any

from splitwise import Splitwise  # type: ignore
from splitwise.expense import Expense  # type: ignore
from splitwise.user import ExpenseUser  # type: ignore

from ..config import (
    DEFAULT_FRIEND_ID,
    DEFAULT_SPLIT,
    SPLITWISE_API_KEY,
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
)
from .models import Transaction

logger = logging.getLogger(__name__)


class SplitwiseClient:
    """Client for interacting with the Splitwise API."""

    def __init__(
        self, split: float = DEFAULT_SPLIT, friend_id: int = DEFAULT_FRIEND_ID
    ) -> None:
        """Initialize the Splitwise client."""

        self.client = self._get_splitwise_client()
        self.friend_id = friend_id
        self.split = split

    def _get_splitwise_client(self) -> Splitwise:
        """Create and configure the Splitwise client."""
        return Splitwise(
            consumer_key=SPLITWISE_CONSUMER_KEY,
            consumer_secret=SPLITWISE_CONSUMER_SECRET,
            api_key=SPLITWISE_API_KEY,
        )

    def create_expense(self, transaction: Transaction) -> Expense:
        """Create a new expense in Splitwise from a Transaction."""
        logger.debug(
            "Creating expense with cost=%s, description=%s",
            transaction.cost,
            transaction.description,
        )

        new = Expense()  # type: ignore
        new.setCost(transaction.cost)  # type: ignore
        new.setDescription(transaction.description)  # type: ignore
        new.setDate(transaction.date_str)  # type: ignore
        new.setDetails(transaction.details_with_metadata)  # type: ignore
        new.setCurrencyCode(transaction.currency_code)  # type: ignore

        if transaction.category_id:
            new.setCategory(transaction.category_id)  # type: ignore

        # Set current user as the payer and owner of the expense
        user = self.client.getCurrentUser()

        # Add the user as the only person involved in the expense

        users = []

        user1_split = round(transaction.cost * self.split, 2)
        user2_split = transaction.cost - user1_split

        user1 = ExpenseUser()
        user1.setId(user.id)  # type: ignore
        user1.setPaidShare(transaction.cost)  # type: ignore
        user1.setOwedShare(user1_split)  # type: ignore

        user2 = ExpenseUser()
        user2.setId(self.friend_id)  # type: ignore
        user2.setPaidShare("0.0")  # type: ignore
        user2.setOwedShare(user2_split)  # type: ignore

        users.append(user1)  # type: ignore
        users.append(user2)  # type: ignore
        new.setUsers(users)  # type: ignore
        print(
            new.cost,
            user1.paid_share,
            user1.owed_share,
            user2.paid_share,
            user2.owed_share,
        )
        created_expense, errors = self.client.createExpense(new)  # type: ignore
        if errors or not created_expense:
            logger.error("Error creating expense: %s", errors.errors)  # type: ignore
            raise Exception(f"Error creating expense: {errors.errors}")  # type: ignore
        logger.debug("Expense created successfully id=%s", created_expense.id)
        return created_expense

    def delete_expense(self, expense_id: int) -> None:
        """Delete an expense in Splitwise by its ID."""
        logger.debug("Deleting expense with ID: %s", expense_id)

        success, errors = self.client.deleteExpense(expense_id)
        if errors or not success:
            logger.error("Error deleting expense: %s", errors.errors)
            raise Exception(f"Error deleting expense: {errors.errors}")
        logger.debug("Expense deleted successfully")

    def check_systems(self) -> bool:
        """Check if the Splitwise API is reachable."""
        try:
            self.client.getCurrentUser()
            logger.debug("Splitwise API is reachable")
            return True
        except Exception as e:
            logger.error("Error checking Splitwise API: %s", e)
            return False

    def get_expenses(
        self,
        limit: int = 20,
        return_deleted: bool = False,
        **kwargs: Any,
    ) -> list[Expense]:
        """Get expenses from Splitwise as a dictionary with expense IDs as keys.

        Args:
            limit: Maximum number of expenses to retrieve
            return_deleted: Whether to include deleted expenses
            **kwargs: Additional arguments to filter expenses from Splitwise API
                      (e.g., friend_id, group_id, etc.)

        Returns:
            List of Expense objects retrieved from the Splitwise API
        """
        api_kwargs = {
            "limit": limit,
        }

        if not return_deleted:
            api_kwargs["visible"] = False

        api_kwargs.update(kwargs)
        expenses = self.client.getExpenses(**api_kwargs)
        return expenses


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.DEBUG)
    # Example usage
    client = SplitwiseClient()
    if client.check_systems():
        print("Splitwise API is reachable.")
    else:
        print("Splitwise API is not reachable.")
    expenses = client.get_expenses(friend_id=DEFAULT_FRIEND_ID, limit=20)
    for expense in expenses:
        print(json.dumps(expense, default=lambda o: o.__dict__, indent=4))
