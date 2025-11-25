"""
NSE Market Cap Data Parser.

Parses MCAP{DDMMYYYY}.csv files extracted from PR{DDMMYY}.zip archives.
Handles validation and transforms data for market_cap_history table.

References:
- .claude/file-formats.md Section 2.1 (Market Cap Archive)
"""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from io import StringIO


class MarketCapParseError(Exception):
    """Raised when market cap data parsing fails."""
    pass


def parse_market_cap_date(date_str: str) -> Optional[datetime.date]:
    """
    Parse market cap date format: DD MMM YYYY (e.g., "16 JAN 2025").

    Note: Format has spaces between day, month, year.

    Args:
        date_str: Date string from MCAP CSV

    Returns:
        date object or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None

    try:
        # Format: "16 JAN 2025" with spaces
        return datetime.strptime(date_str.strip(), '%d %b %Y').date()
    except ValueError:
        # Try alternate format without spaces
        try:
            return datetime.strptime(date_str.strip(), '%d-%b-%Y').date()
        except ValueError:
            return None


def parse_market_cap_decimal(value_str: str) -> Optional[Decimal]:
    """
    Parse decimal value from market cap CSV.

    Values may have:
    - Leading/trailing spaces
    - Commas as thousand separators (need to be removed)
    - Empty values

    Args:
        value_str: Decimal string

    Returns:
        Decimal object or None if empty/invalid
    """
    if not value_str or value_str.strip() == "":
        return None

    try:
        # Remove spaces and commas
        cleaned = value_str.strip().replace(',', '')
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def parse_market_cap_csv(csv_content: str, expected_date: Optional[datetime.date] = None) -> Dict:
    """
    Parse NSE MCAP{DDMMYYYY}.csv content.

    Expected columns:
    - Trade Date
    - Symbol
    - Series
    - Security Name
    - Category
    - Last Trade Date
    - Face Value(Rs.)
    - Issue Size
    - Close Price/Paid up value(Rs.)
    - Market Cap(Rs.)

    Args:
        csv_content: CSV file content as string
        expected_date: Optional date to validate against Trade Date column

    Returns:
        Dict with:
        - success: bool
        - data: List of dicts with market cap data
        - errors: List of error messages
        - stats: Dict with parsing statistics
        - trade_date: The trade date from the file
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "stats": {
            "total_rows": 0,
            "parsed_successfully": 0,
            "skipped": 0,
            "failed": 0,
            "symbols_not_in_db": 0
        },
        "trade_date": None
    }

    try:
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Strip spaces from column names
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

        for row_num, row in enumerate(reader, start=2):
            result["stats"]["total_rows"] += 1

            try:
                # Extract required fields
                trade_date_str = row.get('Trade Date', '').strip()
                symbol = row.get('Symbol', '').strip()
                series = row.get('Series', '').strip()
                security_name = row.get('Security Name', '').strip()
                category = row.get('Category', '').strip()

                # Parse numeric fields
                face_value = parse_market_cap_decimal(row.get('Face Value(Rs.)', ''))
                issue_size_str = row.get('Issue Size', '').strip().replace(',', '')
                close_price = parse_market_cap_decimal(row.get('Close Price/Paid up value(Rs.)', ''))
                market_cap = parse_market_cap_decimal(row.get('Market Cap(Rs.)', ''))

                # Parse dates
                trade_date = parse_market_cap_date(trade_date_str)

                # Validation
                if not symbol:
                    result["errors"].append(f"Row {row_num}: Missing Symbol")
                    result["stats"]["failed"] += 1
                    continue

                if not trade_date:
                    result["errors"].append(f"Row {row_num}: Invalid Trade Date: {trade_date_str}")
                    result["stats"]["failed"] += 1
                    continue

                # Set trade_date from first valid row
                if result["trade_date"] is None:
                    result["trade_date"] = trade_date

                # Validate all rows have same trade date
                if trade_date != result["trade_date"]:
                    result["errors"].append(
                        f"Row {row_num}: Inconsistent trade date {trade_date} (expected {result['trade_date']})"
                    )
                    result["stats"]["failed"] += 1
                    continue

                # Validate expected_date if provided
                if expected_date and trade_date != expected_date:
                    result["errors"].append(
                        f"Row {row_num}: Trade date {trade_date} doesn't match expected {expected_date}"
                    )
                    result["stats"]["failed"] += 1
                    continue

                # Market cap is required and must be positive
                if market_cap is None or market_cap <= 0:
                    result["errors"].append(f"Row {row_num}: Invalid Market Cap for {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                # Close price is required and must be positive
                if close_price is None or close_price <= 0:
                    result["errors"].append(f"Row {row_num}: Invalid Close Price for {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                # Parse issue size (total shares)
                issue_size = None
                if issue_size_str:
                    try:
                        issue_size = int(issue_size_str)
                        if issue_size <= 0:
                            result["errors"].append(f"Row {row_num}: Issue Size must be positive for {symbol}")
                            result["stats"]["failed"] += 1
                            continue
                    except ValueError:
                        result["errors"].append(f"Row {row_num}: Invalid Issue Size for {symbol}: {issue_size_str}")
                        result["stats"]["failed"] += 1
                        continue

                # Build market cap record
                market_cap_record = {
                    "symbol": symbol,
                    "date": trade_date,
                    "market_cap": market_cap,
                    "close_price": close_price,
                    "issue_size": issue_size,
                    "face_value": face_value,
                    "category": category if category else None,
                    "series": series if series else None
                }

                result["data"].append(market_cap_record)
                result["stats"]["parsed_successfully"] += 1

            except Exception as e:
                result["errors"].append(f"Row {row_num}: Unexpected error: {str(e)}")
                result["stats"]["failed"] += 1

        result["success"] = result["stats"]["parsed_successfully"] > 0

    except Exception as e:
        result["errors"].append(f"CSV parsing failed: {str(e)}")
        result["success"] = False

    return result
