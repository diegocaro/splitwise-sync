"""Main application for Splitwise transaction sync."""

import argparse
import json
import logging
from pathlib import Path

from splitwise.expense import Expense  # type: ignore

from splitwise_sync import config as Config
from splitwise_sync.core.email_client import ImapEmailClient
from splitwise_sync.core.models import EmailMessage
from splitwise_sync.core.receipt_parser import ReceiptParser
from splitwise_sync.core.splitwise_client import SplitwiseClient

logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SplitwiseSync:
    """Main application class for Splitwise transaction sync."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize the Splitwise sync application."""
        self.email_client = ImapEmailClient()
        self.receipt_parser = ReceiptParser()
        self.splitwise_client = SplitwiseClient()
        self.dry_run = dry_run

    def _fetch_unprocessed_emails(self) -> list[EmailMessage]:
        # Fetch unprocessed emails
        logger.info("Fetching unprocessed emails...")
        emails = self.email_client.fetch_unread_from_sender(
            "enviodigital@bancoedwards.cl", mark_as_read=not self.dry_run
        )
        return emails

    def process_emails(self) -> list[Expense]:
        """Process all unprocessed emails and return created expenses."""
        emails = self._fetch_unprocessed_emails()
        logger.info(f"Found {len(emails)} unprocessed emails.")

        # Process each email
        created_expenses: list[Expense] = []
        for email in emails:
            logger.info(f"Processing email: {email.subject}")
            try:
                transaction = self.receipt_parser.parse_email(email)
                if self.dry_run:
                    logger.info(f"Dry run: {transaction}")
                    continue

                created = self.splitwise_client.create_expense(
                    transaction.to_splitwise_expense()
                )
                created_expenses.append(created)
            except:
                self.email_client.mark_unread(email.id)
                logger.exception(f"Failed to create expense for email: {email.id}")
                continue

        return created_expenses

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
        help="Output file for email transactions in JSON format",
    )
    args = parser.parse_args()

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
