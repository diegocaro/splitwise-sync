#!/usr/bin/env python
"""Unit tests for the category_summary.py module."""

import datetime
import io
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from splitwise_sync.cli.category_summary import (
    _print_category_section,
    categorize_expenses,
    display_summary,
    format_amount_list,
    format_currency_amount,
    format_currency_symbol,
    get_date_range,
    parse_year_month,
)


@pytest.fixture
def sample_month_date():
    return datetime.date(2025, 4, 21)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = [
        # currency_code, category, is_excluded, month, cost
        ["USD", "Food", False, "2025-04", 100.0],
        ["USD", "Transportation", False, "2025-04", 75.5],
        ["USD", "Payment", True, "2025-04", 50.0],
        ["USD", "Food", False, "2025-03", 90.0],
        ["USD", "Transportation", False, "2025-03", 65.5],
        ["USD", "Payment", True, "2025-03", 40.0],
        ["CLP", "Food", False, "2025-04", 50000.0],
        ["CLP", "Entertainment", False, "2025-04", 25000.0],
    ]
    return pd.DataFrame(
        data, columns=["currency_code", "category", "is_excluded", "month", "cost"]
    )


@pytest.fixture
def sample_pivot():
    """Create a sample pivot table for testing."""
    # Create sample data for the pivot table
    index = ["Food", "Transportation"]
    columns = ["2025-03", "2025-04"]
    data = [
        [90.0, 100.0],  # Food
        [65.5, 75.5],  # Transportation
    ]

    return pd.DataFrame(data, index=index, columns=columns)


@pytest.fixture
def mock_expenses():
    expenses = []

    # Create mock expense 1
    expense1 = MagicMock()
    expense1.getId.return_value = "1"
    expense1.getCost.return_value = "100.00"
    expense1.getCurrencyCode.return_value = "USD"
    expense1.getDate.return_value = "2025-04-10"
    category1 = MagicMock()
    category1.getName.return_value = "Food"
    expense1.getCategory.return_value = category1
    expense1.getPayment.return_value = False
    expenses.append(expense1)

    # Create mock expense 2
    expense2 = MagicMock()
    expense2.getId.return_value = "2"
    expense2.getCost.return_value = "75.50"
    expense2.getCurrencyCode.return_value = "USD"
    expense2.getDate.return_value = "2025-04-15"
    category2 = MagicMock()
    category2.getName.return_value = "Transportation"
    expense2.getCategory.return_value = category2
    expense2.getPayment.return_value = False
    expenses.append(expense2)

    # Create mock expense 3 (payment)
    expense3 = MagicMock()
    expense3.getId.return_value = "3"
    expense3.getCost.return_value = "50.00"
    expense3.getCurrencyCode.return_value = "USD"
    expense3.getDate.return_value = "2025-04-20"
    category3 = MagicMock()
    category3.getName.return_value = "Other"
    expense3.getCategory.return_value = category3
    expense3.getPayment.return_value = True  # This is a payment
    expenses.append(expense3)

    return expenses


def test_parse_year_month_with_valid_input():
    """Test parse_year_month with valid input."""
    result = parse_year_month("2025-04")
    assert result == datetime.date(2025, 4, 1)


def test_parse_year_month_with_none():
    """Test parse_year_month with None input (should return current month)."""
    with patch("splitwise_sync.cli.category_summary.datetime.date") as mock_date_class:
        # Create a mock date instance
        mock_date = MagicMock()
        mock_date.replace.return_value = datetime.date(2025, 4, 21)

        # Set up the today method to return our mock date
        mock_today = MagicMock(return_value=mock_date)
        mock_date_class.today = mock_today

        result = parse_year_month(None)
        assert mock_date.replace.called
        assert mock_date.replace.call_args == [(), {"day": 1}]


def test_get_date_range_single_period(sample_month_date):
    """Test get_date_range with a single period."""
    start_date, end_date = get_date_range(sample_month_date, periods=1)

    assert start_date == "2025-04-01"
    assert end_date == "2025-05-01"


def test_get_date_range_multiple_periods(sample_month_date):
    """Test get_date_range with multiple periods."""
    start_date, end_date = get_date_range(sample_month_date, periods=3)

    assert start_date == "2025-02-01"
    assert end_date == "2025-05-01"


def test_format_currency_amount_usd():
    """Test format_currency_amount with USD."""
    result = format_currency_amount(1234.56, "USD")
    assert result == "1,234.56"


def test_format_currency_amount_clp():
    """Test format_currency_amount with CLP."""
    result = format_currency_amount(1234567, "CLP")
    assert result == "1.234.567"


def test_format_currency_amount_unknown():
    """Test format_currency_amount with unknown currency code."""
    result = format_currency_amount(1234.56, "XYZ")
    assert result == "1,234.56"  # Should use default format


def test_format_currency_symbol_usd():
    """Test format_currency_symbol with USD."""
    result = format_currency_symbol("USD")
    assert result == "USD $"


def test_format_currency_symbol_clp():
    """Test format_currency_symbol with CLP."""
    result = format_currency_symbol("CLP")
    assert result == "CLP $"


def test_format_currency_symbol_unknown():
    """Test format_currency_symbol with unknown currency code."""
    result = format_currency_symbol("XYZ")
    assert result == "XYZ $"  # Should use default format


def test_categorize_expenses(mock_expenses):
    """Test categorize_expenses function."""
    # Test with no exclusions
    df = categorize_expenses(mock_expenses)

    # Check that we have 3 rows (Food, Transportation, Payment)
    assert len(df) == 3

    # Check that the costs are correct
    food_row = df[df["category"] == "Food"].iloc[0]
    transport_row = df[df["category"] == "Transportation"].iloc[0]
    payment_row = df[df["category"] == "Payment"].iloc[0]

    assert food_row["cost"] == 100.0
    assert transport_row["cost"] == 75.5
    assert payment_row["cost"] == 50.0

    # All rows should have is_excluded=False
    assert not df["is_excluded"].any()


def test_categorize_expenses_with_exclusions(mock_expenses):
    """Test categorize_expenses function with category exclusions."""
    # Test with Payment excluded
    df = categorize_expenses(mock_expenses, {"Payment"})

    # Check that we have 3 rows still
    assert len(df) == 3

    # Check that Payment is marked as excluded
    payment_row = df[df["category"] == "Payment"].iloc[0]
    assert payment_row["is_excluded"]

    # Check that other categories are not marked as excluded
    other_rows = df[df["category"] != "Payment"]
    assert not other_rows["is_excluded"].any()


def test_format_amount_list():
    """Test format_amount_list function."""
    amounts = [100.0, 200.0, 300.0]

    # Test with USD
    formatted_usd = format_amount_list(amounts, "USD")
    assert formatted_usd == "    100.00    200.00    300.00"

    # Test with CLP
    formatted_clp = format_amount_list(amounts, "CLP")
    assert formatted_clp == "       100       200       300"


def test_print_category_section(sample_pivot):
    """Test _print_category_section function."""
    with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        _print_category_section(
            pivot=sample_pivot,
            currency_symbol="USD $",
            currency_code="USD",
            section_title="TEST SECTION",
            is_excluded_section=False,
        )

        output = fake_stdout.getvalue()

        # Check that the section title is printed
        assert "TEST SECTION" in output

        # Check that all categories are included
        assert "Food" in output
        assert "Transportation" in output

        # Check that percentages are included (not excluded section)
        assert "%" in output


def test_print_category_section_excluded(sample_pivot):
    """Test _print_category_section function with excluded section."""
    with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        _print_category_section(
            pivot=sample_pivot,
            currency_symbol="USD $",
            currency_code="USD",
            section_title="EXCLUDED SECTION",
            is_excluded_section=True,
        )

        output = fake_stdout.getvalue()

        # Check that the section title is printed
        assert "EXCLUDED SECTION" in output

        # Check that all categories are included
        assert "Food" in output
        assert "Transportation" in output

        # Check that "excluded" note is included
        assert "(excluded)" in output

        # Check that percentages are NOT included (excluded section)
        assert "%" not in output


def test_display_summary(sample_dataframe):
    """Test display_summary function."""
    # Call display_summary with our sample dataframe
    with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        display_summary(sample_dataframe)

        output = fake_stdout.getvalue()

        # Check that currency headers are included
        assert "Expense Summary by Category [USD]:" in output
        assert "Expense Summary by Category [CLP]:" in output

        # Check that categories are included
        assert "Food" in output
        assert "Transportation" in output
        assert "Entertainment" in output

        # Check that excluded section is included
        assert "EXCLUDED CATEGORIES:" in output
        assert "Payment" in output

        # Check that totals are included
        assert "TOTAL" in output
        assert "half =" in output

        # Check that grand total is included (since we have excluded categories)
        assert "GRAND TOTAL (with excluded):" in output
