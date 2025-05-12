#!/usr/bin/env python
"""Script to summarize Splitwise expenses by category for a specific month."""

import argparse
import calendar
import datetime
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, TypedDict

import pandas as pd
from splitwise.category import Category  # type: ignore
from splitwise.expense import Expense  # type: ignore

from splitwise_sync.config import DEFAULT_FRIEND_ID
from splitwise_sync.core.splitwise_client import SplitwiseClient

logger = logging.getLogger(__name__)


class CurrencyFormatDict(TypedDict):
    symbol: str
    thousands_sep: str
    decimal_sep: str
    precision: int


# Define currency symbols and formatting
CURRENCY_FORMATS: Dict[str, CurrencyFormatDict] = {
    "CLP": {"symbol": "$", "thousands_sep": ".", "decimal_sep": ",", "precision": 0},
    "USD": {"symbol": "$", "thousands_sep": ",", "decimal_sep": ".", "precision": 2},
    "EUR": {"symbol": "€", "thousands_sep": ".", "decimal_sep": ",", "precision": 2},
    # Add more currencies as needed
}

# Default currency format to use if currency not found
DEFAULT_CURRENCY_FORMAT: CurrencyFormatDict = {
    "symbol": "$",
    "thousands_sep": ",",
    "decimal_sep": ".",
    "precision": 2,
}

LINE_SEPARATOR = "-" * 70


def format_currency_amount(amount: float, currency_code: str) -> str:
    """Format an amount according to the specified currency."""
    format_info = CURRENCY_FORMATS.get(currency_code, DEFAULT_CURRENCY_FORMAT)

    # Format with the appropriate precision
    precision = format_info["precision"]
    formatted_num = f"{amount:,.{precision}f}"

    # Replace separators according to currency code
    # Use a temporary unique marker for the decimal separator to avoid conflicts
    if format_info["decimal_sep"] != "." and precision > 0:
        formatted_num = formatted_num.replace(".", "<DECIMAL>")

    if format_info["thousands_sep"] != ",":
        formatted_num = formatted_num.replace(",", format_info["thousands_sep"])

    if format_info["decimal_sep"] != "." and precision > 0:
        formatted_num = formatted_num.replace("<DECIMAL>", format_info["decimal_sep"])

    # Add currency symbol
    return f"{formatted_num}"


def format_currency_symbol(currency_code: str) -> str:
    """Return a formatted string containing the currency code and its associated symbol."""
    format_info = CURRENCY_FORMATS.get(currency_code, DEFAULT_CURRENCY_FORMAT)

    return f"{currency_code} {format_info['symbol']}"


def parse_year_month(year_month: Optional[str] = None) -> Tuple[int, int]:
    """Parse year and month from string format 'YYYY-MM' or use current month."""
    if year_month:
        try:
            year, month = map(int, year_month.split("-")[:2])
            if not (1 <= month <= 12 and 1000 <= year <= 9999):
                raise ValueError("Invalid year or month range.")
            return month, year
        except (ValueError, IndexError) as e:
            raise ValueError(
                f"Invalid year-month format: {year_month}. Use YYYY-MM format."
            ) from e
    else:
        # Use current month and year
        today = datetime.date.today()
        return today.month, today.year


def get_date_range(month: int, year: int) -> Tuple[str, str]:
    """Get the start and end date for the given month and year."""
    start_date = datetime.date(year, month, 1)

    next_year = year + ((month) // 12)
    next_month = (month % 12) + 1
    end_date = datetime.date(next_year, next_month, 1)

    return start_date.isoformat(), end_date.isoformat()


def categorize_expenses(
    expenses: List[Expense], exclude_categories: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Categorize expenses by currency and sum up the amounts for each category.
    """
    if exclude_categories is None:
        exclude_categories = set()

    data = []
    for expense in expenses:
        category = expense.getCategory().getName().strip()
        if expense.getPayment():
            category = "Payment"
        row = {
            "id": expense.getId(),
            "cost": float(expense.getCost()),
            "currency_code": expense.getCurrencyCode(),
            "date": expense.getDate(),
            "category": category,
            "is_excluded": category in exclude_categories,
        }
        data.append(row)
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["month"] = df["date"].dt.strftime("%Y-%m")

    out = df.groupby(
        ["currency_code", "category", "is_excluded", "month"], as_index=False
    )["cost"].sum()

    return out


def _print_category_section(
    categories_data: pd.DataFrame,
    currency_symbol: str,
    currency_code: str,
    section_title: Optional[str] = None,
    is_excluded_section: bool = False,
    overall_total_for_percentage: Optional[float] = None,
) -> None:
    """Helper function to print a section of categories."""
    if categories_data.empty:
        return

    categories_data = categories_data.set_index("category")["cost"].to_dict()

    if section_title:
        print(LINE_SEPARATOR)
        print(f"{section_title:<30}")

    sorted_data = sorted(categories_data.items(), key=lambda x: x[1], reverse=True)

    for category, amount in sorted_data:
        formatted_amount = format_currency_amount(amount, currency_code)
        if (
            not is_excluded_section
            and overall_total_for_percentage is not None
            and overall_total_for_percentage > 0
        ):
            percentage = (amount / overall_total_for_percentage) * 100
            print(
                f"{category:<30} {currency_symbol} {formatted_amount:>10} {percentage:>9.1f}%"
            )
        else:
            note = " (excluded)" if is_excluded_section else " "
            print(
                f"{category:<30} {currency_symbol} {formatted_amount:>10} {'-':>9} {note:>10}"
            )


def display_summary(df: pd.DataFrame) -> None:
    """Display the summary of expenses by currency and category in a formatted table."""

    for currency_code, categories in df.groupby("currency_code"):
        total = categories["cost"].sum()
        currency_symbol = format_currency_symbol(currency_code)

        print(f"\nExpense Summary by Category [{currency_code}]:")
        print(LINE_SEPARATOR)
        print(
            f"{'Category':<30} {' '*len(currency_symbol)} {'Amount':>10} {'Percentage':>10} {'Note':<10}"
        )
        print(LINE_SEPARATOR)

        # Print included categories
        included_categories = categories[~categories["is_excluded"]]
        excluded_categories = categories[categories["is_excluded"]]
        total = included_categories["cost"].sum()
        excluded_total = excluded_categories["cost"].sum()

        _print_category_section(
            categories_data=included_categories,
            currency_symbol=currency_symbol,
            currency_code=currency_code,
            is_excluded_section=False,
            overall_total_for_percentage=total,
        )

        # Print excluded categories if any exist for this currency
        if not excluded_categories.empty:
            _print_category_section(
                categories_data=excluded_categories,
                currency_symbol=currency_symbol,
                currency_code=currency_code,
                section_title="EXCLUDED CATEGORIES:",
                is_excluded_section=True,
            )
            print(
                f"{'EXCLUDED TOTAL:':<30} {currency_symbol} {format_currency_amount(excluded_total, currency_code):>10}"
            )

        print(LINE_SEPARATOR)
        formatted_total = format_currency_amount(total, currency_code)
        half_total = format_currency_amount(total / 2, currency_code)
        print(
            f"{'TOTAL':<30} {currency_symbol} {formatted_total:>10} {100 if total > 0 else 0:>9.1f}% (half = {half_total})"
        )

        # Show grand total if there are excluded categories
        if excluded_total > 0:
            grand_total = total + excluded_total
            print(
                f"{'GRAND TOTAL (with excluded):':<30} {currency_symbol} {format_currency_amount(grand_total, currency_code):>10}"
            )


def main() -> None:
    """Run the main function to summarize expenses by category."""
    parser = argparse.ArgumentParser(
        description="Summarize Splitwise expenses by category for a specific month."
    )
    parser.add_argument(
        "--month", help="Year and month in YYYY-MM format (default: current month)"
    )
    parser.add_argument(
        "--friend-id",
        type=int,
        default=DEFAULT_FRIEND_ID,
        help="Splitwise friend ID (default: from config)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of expenses to retrieve (default: 1000)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        metavar="CATEGORY",
        default=["Payment", "Insurance"],
        help="Categories to exclude from the summary (e.g., --exclude Insurance 'Home Services'). Default: Payment and Insurance",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Parse month and year
    try:
        month, year = parse_year_month(args.month)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    month_name = calendar.month_name[month]
    logger.info(f"Analyzing expenses for {month_name} {year}")

    # Get date range for the month
    start_date, end_date = get_date_range(month, year)
    logger.debug(f"Date range: {start_date} to {end_date}")

    # Initialize Splitwise client
    client = SplitwiseClient(friend_id=args.friend_id)

    if not client.check_systems():
        logger.error("Failed to connect to Splitwise. Check your API credentials.")
        sys.exit(1)

    # Get expenses for the specified date range
    logger.info(f"Retrieving up to {args.limit} expenses from Splitwise...")
    expenses = client.get_expenses(
        limit=args.limit,
        dated_after=start_date,
        dated_before=end_date,
        friend_id=args.friend_id,
    )
    logger.info(f"Retrieved {len(expenses)} expenses")

    # Convert exclude categories to a set for faster lookups
    default_exclude_categories = {"Payment"}
    exclude_categories = (
        set(args.exclude).union(default_exclude_categories)
        if args.exclude
        else default_exclude_categories
    )
    if exclude_categories:
        logger.info(
            f"Excluding categories from totals: {', '.join(exclude_categories)}"
        )

    frame = categorize_expenses(expenses, exclude_categories)

    if frame.empty:
        logger.info("No expenses found for the specified period.")
        return

    # Display summary including excluded categories but not in totals
    display_summary(frame)


if __name__ == "__main__":
    main()
