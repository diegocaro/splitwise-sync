#!/usr/bin/env python
"""Script to summarize Splitwise expenses by category for a specific month."""

import argparse
import calendar
import datetime
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, TypedDict

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
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """
    Categorize expenses by currency and sum up the amounts for each category.
    Separates excluded categories but still collects their data.

    Returns a tuple of two nested dictionaries:
    (
        # Regular categories to include in totals
        {
            'currency_code': {
                'category_name': total_amount,
                ...
            },
            ...
        },
        # Excluded categories (shown but not included in totals)
        {
            'currency_code': {
                'excluded_category_name': total_amount,
                ...
            },
            ...
        }
    )
    )
    """
    # First level: Currency code
    # Second level: Category name -> total amount
    included: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    excluded: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    current_exclude_categories: Set[str] = (
        exclude_categories if exclude_categories is not None else set()
    )

    for expense in expenses:
        category_obj: Optional[Category] = getattr(expense, "category", None)
        category_name: str = (
            getattr(category_obj, "name", "Uncategorized")
            if category_obj
            else "Uncategorized"
        )

        is_payment: bool = getattr(expense, "payment", False)
        if is_payment:
            category_name = "Payment"

        currency_code: str = getattr(expense, "currency_code", "USD")
        cost_str: str = getattr(expense, "cost", "0")
        cost: float = float(cost_str)
        expense_date: str = getattr(expense, "date", "")  # Assuming date is a string

        logger.debug(
            f"Processing expense: {category_name} - {currency_code} - {cost} - {expense_date} - is_payment={is_payment}"
        )

        if category_name in current_exclude_categories:
            excluded[currency_code][category_name] += cost
        else:
            included[currency_code][category_name] += cost

    # Convert inner defaultdicts to regular dicts
    return (
        {currency: dict(categories) for currency, categories in included.items()},
        {currency: dict(categories) for currency, categories in excluded.items()},
    )


def _print_category_section(
    categories_data: Dict[str, float],
    currency_symbol: str,
    currency_code: str,
    section_title: Optional[str] = None,
    is_excluded_section: bool = False,
    overall_total_for_percentage: Optional[float] = None,
) -> None:
    """Helper function to print a section of categories."""
    if not categories_data:
        return

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
            note = "(excluded)" if is_excluded_section else ""
            print(
                f"{category:<30} {currency_symbol} {formatted_amount:>10} {'-':>9} {note:>10}"
            )


def display_summary(
    categorized_expenses: Dict[str, Dict[str, float]],
    excluded_expenses: Dict[str, Dict[str, float]],
) -> None:
    """Display the summary of expenses by currency and category in a formatted table."""
    # The line `excluded_expenses = excluded_expenses or {}` is removed as categorize_expenses ensures it's a dict.

    for currency_code, categories in categorized_expenses.items():
        total = sum(categories.values())
        current_currency_excluded_expenses = excluded_expenses.get(currency_code, {})
        excluded_total = sum(current_currency_excluded_expenses.values())

        print(f"\nExpense Summary by Category [{currency_code}]:")
        print(LINE_SEPARATOR)
        print(f"{'Category':<30} {'Amount':>15} {'Percentage':>10} {'Note':>10}")
        print(LINE_SEPARATOR)

        currency_symbol = format_currency_symbol(currency_code)

        # Print included categories
        _print_category_section(
            categories_data=categories,
            currency_symbol=currency_symbol,
            currency_code=currency_code,
            is_excluded_section=False,
            overall_total_for_percentage=total,
        )

        # Print excluded categories if any exist for this currency
        if current_currency_excluded_expenses:
            _print_category_section(
                categories_data=current_currency_excluded_expenses,
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
            f"{'TOTAL':<30} {currency_symbol} {formatted_total:>10} {100 if total > 0 else 0:>9.1f}%    half = {half_total}"
        )

        # Show grand total if there are excluded categories
        if excluded_total > 0:
            grand_total = total + excluded_total
            print(
                f"{'GRAND TOTAL (with excluded):':<30} {currency_symbol} {format_currency_amount(grand_total, currency_code):>10}"
            )

        print(LINE_SEPARATOR)


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
        help="Categories to exclude from the summary (e.g., --exclude Insurance 'Home Services')",
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

    # Categorize and sum expenses by currency - now returns both included and excluded expenses
    categorized_expenses, excluded_expenses = categorize_expenses(
        expenses, exclude_categories
    )

    if not categorized_expenses and not excluded_expenses:
        logger.info("No expenses found for the specified period.")
        return

    # Display summary including excluded categories but not in totals
    display_summary(categorized_expenses, excluded_expenses)


if __name__ == "__main__":
    main()
