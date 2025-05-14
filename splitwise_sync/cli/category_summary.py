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


def parse_year_month(year_month: Optional[str] = None) -> datetime.date:
    """Parse year and month from string format 'YYYY-MM' or use current month."""
    if not year_month:
        return datetime.date.today().replace(day=1)

    return pd.to_datetime(year_month, format="%Y-%m").date()


def get_date_range(month: datetime.date, periods: int = 1) -> Tuple[str, str]:
    """Get the start and end date for the given month and year."""
    next_month = (month + pd.DateOffset(months=1)).replace(day=1).date()

    date_range = pd.date_range(end=next_month, periods=periods, freq="ME")
    start_date = date_range[0].replace(day=1).date()
    end_date = next_month
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


def format_amount_list(amount_list: List[float], currency_code: str) -> str:
    """Format a list of amounts according to the specified currency."""
    formatted_amounts = [
        f"{format_currency_amount(amount, currency_code):>10}" for amount in amount_list
    ]
    return "".join(formatted_amounts)
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
    return out


def _print_category_section(
    pivot: pd.DataFrame,
    categories_data: Dict[str, float],
    categories_data: pd.DataFrame,
    currency_symbol: str,
    currency_code: str,
    section_title: Optional[str] = None,
    is_excluded_section: bool = False,
) -> None:
    """Helper function to print a section of categories."""
    if pivot.empty:
    if not categories_data:
    if categories_data.empty:
        return

    categories_data = categories_data.set_index("category")["cost"].to_dict()

    if section_title:
        print(LINE_SEPARATOR)
        print(f"{section_title:<30}")

    last_column = pivot.columns[-1]

    overall_total_for_percentage = pivot[last_column].sum()
    sorted_data = pivot.sort_values(by=last_column, ascending=False)

    for category, amount in sorted_data.iterrows():
        amount = amount.to_list()
        formatted_amount = format_amount_list(amount, currency_code)
        last_column_amount = amount[-1]

        if not is_excluded_section:
            percentage = (last_column_amount / overall_total_for_percentage) * 100
            print(
                f"{category:<30} {currency_symbol} {formatted_amount} {percentage:>9.1f}%"
            )
        else:
            note = " (excluded)" if is_excluded_section else " "
            print(
                f"{category:<30} {currency_symbol} {formatted_amount} {'-':>9} {note:>10}"
            )


def display_summary(df: pd.DataFrame) -> None:
    """Display the summary of expenses by currency and category in a formatted table."""

    for currency_code, categories in df.groupby("currency_code"):
        pivot = categories.pivot_table(
            index=["category", "is_excluded"],
            columns="month",
            values="cost",
            aggfunc="sum",
            fill_value=0,
        )
        is_excluded = pivot.index.get_level_values("is_excluded")
        pivot = pivot.droplevel("is_excluded")

        currency_symbol = format_currency_symbol(currency_code)
        get_label = lambda year, month: f"{calendar.month_abbr[int(month)]} {year}"
        labels = [f"{get_label(*col.split("-")):>10}" for col in pivot.columns]
        labels = "".join(labels)
    for currency_code, categories in categorized_expenses.items():
        total = sum(categories.values())
        current_currency_excluded_expenses = excluded_expenses.get(currency_code, {})
        excluded_total = sum(current_currency_excluded_expenses.values())
    for currency_code, categories in df.groupby("currency_code"):
        total = categories["cost"].sum()
        currency_symbol = format_currency_symbol(currency_code)

        print(f"\nExpense Summary by Category [{currency_code}]:")
        print(LINE_SEPARATOR)
        print(
            f"{'Category':<30} {' '*len(currency_symbol)} {labels} {'Percentage':>10} {'Note':<10}"
        )
        print(f"{'Category':<30} {'Amount':>15} {'Percentage':>10} {'Note':>10}")
        print(
            f"{'Category':<30} {' '*len(currency_symbol)} {'Amount':>10} {'Percentage':>10} {'Note':<10}"
        )
        print(LINE_SEPARATOR)

        included = pivot[~is_excluded]
        excluded = pivot[is_excluded]

        total = included[included.columns].sum()
        excluded_total = excluded[included.columns].sum()

        currency_symbol = format_currency_symbol(currency_code)

        # Print included categories
        # Print included categories
        included_categories = categories[~categories["is_excluded"]]
        excluded_categories = categories[categories["is_excluded"]]
        total = included_categories["cost"].sum()
        excluded_total = excluded_categories["cost"].sum()

        _print_category_section(
            pivot=included,
            categories_data=categories,
            categories_data=included_categories,
            currency_symbol=currency_symbol,
            currency_code=currency_code,
            is_excluded_section=False,
        )

        # Print excluded categories if any exist for this currency
        if not excluded.empty:
        if current_currency_excluded_expenses:
        if not excluded_categories.empty:
            _print_category_section(
                pivot=excluded,
                categories_data=current_currency_excluded_expenses,
                categories_data=excluded_categories,
                currency_symbol=currency_symbol,
                currency_code=currency_code,
                section_title="EXCLUDED CATEGORIES:",
                is_excluded_section=True,
            )
            formatted_amount = format_amount_list(
                excluded_total.to_list(), currency_code
            )
            print(f"{'EXCLUDED TOTAL:':<30} {currency_symbol} {formatted_amount}")

        print(LINE_SEPARATOR)
        total_list = total.to_list()
        formatted_total = format_amount_list(total_list, currency_code)
        half_total = format_currency_amount(total_list[-1] / 2, currency_code)
        print(
            f"{'TOTAL':<30} {currency_symbol} {formatted_total} {100 if total_list[-1] > 0 else 0:>9.1f}% (half = {half_total})"
            f"{'TOTAL':<30} {currency_symbol} {formatted_total:>10} {100 if total > 0 else 0:>9.1f}%    half = {half_total}"
            f"{'TOTAL':<30} {currency_symbol} {formatted_total:>10} {100 if total > 0 else 0:>9.1f}% (half = {half_total})"
        )

        # Show grand total if there are excluded categories
        if excluded_total.sum() > 0:
            grand_total = total + excluded_total
            formatted_grand_total = format_amount_list(
                grand_total.to_list(), currency_code
            )
            print(
                f"{'GRAND TOTAL (with excluded):':<30} {currency_symbol} {formatted_grand_total}"
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
    # TODO: handle pagination
    parser.add_argument(
        "--limit",
        type=int,
        default=3000,
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
    parser.add_argument(
        "--periods",
        type=int,
        default=3,
        help="Number of previous periods to retrieve (default: 2)",
        help="Categories to exclude from the summary (e.g., --exclude Insurance 'Home Services')",
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
    month = parse_year_month(args.month)

    month_name = calendar.month_name[month.month]
    logger.debug(f"Analyzing expenses for {month_name} {month.year}")
    month_name = calendar.month_name[month]
    logger.info(f"Analyzing expenses for {month_name} {year}")
    month_name = calendar.month_name[month]
    logger.debug(f"Analyzing expenses for {month_name} {year}")

    # Get date range for the month
    start_date, end_date = get_date_range(month, periods=args.periods)
    logger.debug(f"Date range: {start_date} to {end_date}")

    # Initialize Splitwise client
    client = SplitwiseClient(friend_id=args.friend_id)

    if not client.check_systems():
        logger.error("Failed to connect to Splitwise. Check your API credentials.")
        sys.exit(1)

    logger.debug(f"Retrieving up to {args.limit} expenses from Splitwise...")
    expenses = client.get_expenses(
        limit=args.limit,
        dated_after=start_date,
        dated_before=end_date,
        friend_id=args.friend_id,
    )
    logger.debug(f"Retrieved {len(expenses)} expenses")

    if args.exclude:
        logger.info(f"Excluding categories from totals: {', '.join(args.exclude)}")

    frame = categorize_expenses(expenses, args.exclude)

    if frame.empty:
        logger.info("No expenses found for the specified period.")
        return

    display_summary(frame)


if __name__ == "__main__":
    main()
