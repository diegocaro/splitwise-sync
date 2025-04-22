"""Main application for Splitwise transaction sync."""

import argparse
import json
import logging
from pathlib import Path

from splitwise.expense import Expense  # type: ignore

from splitwise_sync import config
from splitwise_sync.core.email_client import ImapEmailClient
from splitwise_sync.core.models import EmailMessage
from splitwise_sync.core.receipt_parser import ReceiptParser
from splitwise_sync.core.splitwise_client import SplitwiseClient
from splitwise_sync.core.transaction_store import TransactionStore

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SplitwiseSync:
    """Main application class for Splitwise transaction sync."""

    def __init__(
        self, dry_run: bool = False, store_path: Path = config.STORE_PATH
    ) -> None:
        """Initialize the Splitwise sync application."""
        self.email_client = ImapEmailClient()
        self.receipt_parser = ReceiptParser()
        self.splitwise_client = SplitwiseClient()
        self.dry_run = dry_run
        self.transaction_store = TransactionStore(store_path)

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
        skipped_count = 0

        for email in emails:
            logger.info(f"Processing email: {email.subject}")
            try:
                transaction = self.receipt_parser.parse_email(email)

                if transaction.hash in self.transaction_store:
                    logger.info(f"Transaction already processed: {transaction.hash}")
                    skipped_count += 1
                    continue

                if self.dry_run:
                    logger.info(f"Dry run: {transaction}")
                    continue

                created = self.splitwise_client.create_expense(transaction)
                logger.debug(f"Created expense: id={created.id}")

                # Store the processed transaction
                self.transaction_store.add(transaction, created)

                created_expenses.append(created)
            except Exception as e:
                self.email_client.mark_unread(email.uid)
                logger.exception(f"Failed to create expense for email: {email.uid}")
                continue

        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} already processed transactions.")

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
    parser.add_argument(
        "--store",
        type=Path,
        default=config.STORE_PATH,
        help=f"Path to the transaction store file (default: {config.STORE_PATH})",
    )

    args = parser.parse_args()

    app = SplitwiseSync(dry_run=args.dry_run, store_path=args.store)

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
