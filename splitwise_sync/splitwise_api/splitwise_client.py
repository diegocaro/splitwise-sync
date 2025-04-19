"""Splitwise API client for managing expenses."""

import logging

from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser

from splitwise_sync.splitwise_api.custom_expense import CustomExpense
from splitwise_sync.utils.config import (
    DEFAULT_FRIEND_ID,
    DEFAULT_SPLIT,
    SPLITWISE_API_KEY,
    SPLITWISE_CONSUMER_KEY,
    SPLITWISE_CONSUMER_SECRET,
)

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

    def create_expense(self, expense: CustomExpense) -> Expense:
        """Create a new expense in Splitwise."""
        logger.debug(
            "Creating expense with cost=%s, description=%s",
            expense.cost,
            expense.description,
        )

        new = Expense()
        new.setCost(expense.cost)
        new.setDescription(expense.description)
        new.setDate(expense.date)

        if expense.category_id:
            new.setCategory(expense.category_id)

        if expense.details:
            new.setDetails(expense.details)

        if expense.currency_code:
            new.setCurrencyCode(expense.currency_code)

        # Set current user as the payer and owner of the expense
        user = self.client.getCurrentUser()

        # Add the user as the only person involved in the expense

        users = []

        user1_split = float(expense.cost) * self.split
        user2_split = float(expense.cost) - user1_split

        user1 = ExpenseUser()
        user1.setId(user.id)
        user1.setPaidShare(expense.cost)
        user1.setOwedShare(user1_split)

        user2 = ExpenseUser()
        user2.setId(self.friend_id)
        user2.setPaidShare("0.0")
        user2.setOwedShare(user2_split)

        users.append(user1)
        users.append(user2)
        new.setUsers(users)

        created_expense, errors = self.client.createExpense(new)
        if errors:
            logger.error("Error creating expense: %s", errors.errors)
            raise Exception(f"Error creating expense: {errors.errors}")
        logger.debug("Expense created successfully: %s", created_expense)
        return created_expense

    def check_systems(self) -> bool:
        """Check if the Splitwise API is reachable."""
        try:
            self.client.getCurrentUser()
            logger.debug("Splitwise API is reachable")
            return True
        except Exception as e:
            logger.error("Error checking Splitwise API: %s", e)
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Example usage
    client = SplitwiseClient()
    if client.check_systems():
        print("Splitwise API is reachable.")
    else:
        print("Splitwise API is not reachable.")
