"""Main application for Splitwise transaction sync."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from splitwise.expense import Expense  # type: ignore

from splitwise_sync import config
from splitwise_sync.core.email_client import ImapEmailClient
from splitwise_sync.core.logging_utils import create_logger
from splitwise_sync.core.models import EmailMessage, Transaction
from splitwise_sync.core.receipt_parser import ReceiptParser
from splitwise_sync.core.splitwise_client import SplitwiseClient

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Set up a separate logger for processed transactions
processed_logger = create_logger(
    "splitwise_sync.processed",
    config.LOGS_DIR / "processed.log",
    level=logging.INFO,
)

errored_logger = create_logger(
    "splitwise_sync.errored",
    config.LOGS_DIR / "errored.log",
    level=logging.ERROR,
)


class SplitwiseSync:
    """Main application class for Splitwise transaction sync."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize the Splitwise sync application."""
        self.email_client = ImapEmailClient()
        self.receipt_parser = ReceiptParser()
        self.splitwise_client = SplitwiseClient()
        self.dry_run = dry_run

    def _fetch_unprocessed_emails(self) -> list[EmailMessage]:
        logger.info("Fetching unprocessed emails...")
        emails = self.email_client.fetch_unread_from_sender(
            "enviodigital@bancoedwards.cl", mark_as_read=not self.dry_run
        )
        return emails

    def process_emails(self) -> list[Expense]:
        """Process all unprocessed emails and return created expenses."""
        emails = self._fetch_unprocessed_emails()
        logger.info(f"Found {len(emails)} unprocessed emails.")

        created_expenses: list[Expense] = []

        for email in emails:
            logger.info(f"Processing email: {email.subject}")
            try:
                transaction = self.receipt_parser.parse_email(email)

                if self.dry_run:
                    logger.info(f"Dry run: {transaction}")
                    continue

                expense_created = self.splitwise_client.create_expense(transaction)
                logger.debug(f"Created expense: id={expense_created.id}")
                self._log_processed(email, transaction, expense_created)
                created_expenses.append(expense_created)
            except Exception as exc:
                self.email_client.mark_unread(email.uid)
                logger.exception(f"Failed to create expense for email: {email.uid}")
                errored_logger.error({"email": email.to_dict(), "error": str(exc)})
                continue

        return created_expenses

    def _log_processed(
        self, email: EmailMessage, transaction: Transaction, expense: Expense
    ) -> None:
        """Log the processed email, transaction and expense info"""

        info: dict[str, Any] = {
            "processed_at": datetime.now().isoformat(),
            "expense_id": str(expense.id),
            "expense_created_by_id": str(expense.created_by.id),
            "expense_created_by_email": expense.created_by.email,
            "transaction": transaction.to_dict(),
            "email_sender": email.sender,
        }

        processed_logger.info(info)

    def email_to_json(self, filename: Path) -> None:
        """Convert email to JSON format."""
        emails = self._fetch_unprocessed_emails()

        transactions = [
            {
                "email": email.to_dict(),
                "transaction": self.receipt_parser.parse_email(email).to_dict(),
            }
            for email in emails
        ]

        with open(filename, "w") as f:
            json.dump(transactions, f, indent=4)


def main() -> None:
    """Main entry point for the application."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Splitwise Sync - Process emails and create Splitwise expenses"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (parse emails but don't create expenses)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file for email transactions in JSON format. Implies --dry-run.",
    )

    args = parser.parse_args()
    if args.output:
        args.dry_run = True

    app = SplitwiseSync(dry_run=args.dry_run)

    if args.output:
        app.email_to_json(args.output)
        logger.info(f"Email transactions saved to {args.output}")
        return

    expenses = app.process_emails()

    if expenses:
        total_amount = sum(float(expense.cost) for expense in expenses)  # type: ignore
        logger.info(
            f"Successfully created {len(expenses)} expenses totaling ${total_amount:.2f}"
        )
    else:
        logger.info("No expenses were created.")


if __name__ == "__main__":
    main()
