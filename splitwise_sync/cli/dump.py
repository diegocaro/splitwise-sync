"""Main application for Splitwise transaction sync."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from splitwise_sync import config
from splitwise_sync.core.email_client import ImapEmailClient
from splitwise_sync.core.logging_utils import create_logger
from splitwise_sync.core.models import EmailMessage
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


def email_to_json(filename: Path) -> None:
    """Convert email to JSON format."""
    email_client = ImapEmailClient()
    receipt_parser = ReceiptParser()
    emails = email_client.fetch_unread_from_sender("enviodigital@bancoedwards.cl")

    def inner(email: EmailMessage) -> dict[str, Any]:
        ans = {"email": email.to_dict()}
        try:
            transaction = receipt_parser.parse_email(email)
            ans["transaction"] = transaction.to_dict()
        except Exception as exc:
            ans["error"] = str(exc)
        return ans

    transactions = [inner(email) for email in emails]

    with open(filename, "w") as f:
        json.dump(transactions, f, indent=4)


def main() -> None:
    """Main entry point for the application."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Dump transactions from emails to JSON or dump Splitwise expenses."
    )

    parser.add_argument(
        "--emails",
        type=Path,
        help="Output file for email parsed transactions in JSON format",
    )
    parser.add_argument(
        "--limit", type=int, default=1000, help="Limit the expenses to fetch"
    )

    parser.add_argument(
        "--expenses",
        type=Path,
        help="Output file for Splitwise expenses in JSON format",
    )

    args = parser.parse_args()

    if args.emails:
        email_to_json(args.emails)
        logger.info(f"Email transactions saved to {args.output}")
        return

    if args.expenses:
        splitwise_client = SplitwiseClient()
        expenses = splitwise_client.get_expenses(limit=args.limit)
        with open(args.expenses, "w") as f:
            json.dump(
                expenses,
                f,
                default=lambda o: o.__dict__,
                indent=4,
            )
        logger.info(f"Splitwise expenses saved to {args.expenses}")
        return


if __name__ == "__main__":
    main()
