"""
NSE Securities and ETF List Parser.

Parses EQUITY_L.csv and eq_etfseclist.csv from NSE archives.
Handles validation and transforms data for database insertion.

References:
- .claude/file-formats.md Section 1.1 (EQUITY_L.csv)
- .claude/file-formats.md Section 1.2 (eq_etfseclist.csv)
"""
import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from io import StringIO


class SecurityParseError(Exception):
    """Raised when security data parsing fails."""
    pass


def parse_date(date_str: str, format_str: str) -> Optional[datetime.date]:
    """
    Parse date string with given format.

    Args:
        date_str: Date string (e.g., "29-NOV-1977" or "08-Jan-02")
        format_str: Format string (e.g., "%d-%b-%Y" or "%d-%b-%y")

    Returns:
        date object or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None

    try:
        return datetime.strptime(date_str.strip(), format_str).date()
    except ValueError:
        return None


def parse_decimal(value_str: str) -> Optional[Decimal]:
    """
    Parse decimal value from string.

    Args:
        value_str: Decimal string

    Returns:
        Decimal object or None if empty/invalid
    """
    if not value_str or value_str.strip() == "":
        return None

    try:
        return Decimal(value_str.strip())
    except (InvalidOperation, ValueError):
        return None


def validate_isin(isin: str) -> bool:
    """
    Validate ISIN format.

    ISIN must:
    - Be exactly 12 characters
    - Start with 'IN'
    - Contain only alphanumeric characters

    Args:
        isin: ISIN string to validate

    Returns:
        True if valid, False otherwise
    """
    if not isin or len(isin) != 12:
        return False

    if not isin.startswith('IN'):
        return False

    # Check if remaining 10 characters are alphanumeric
    return isin[2:].isalnum()


def validate_symbol(symbol: str) -> bool:
    """
    Validate symbol format.

    Symbol must contain only:
    - Uppercase letters (A-Z)
    - Numbers (0-9)
    - Ampersand (&)
    - Hyphen (-)

    Args:
        symbol: Symbol string to validate

    Returns:
        True if valid, False otherwise
    """
    if not symbol:
        return False

    pattern = r'^[A-Z0-9&-]+$'
    return bool(re.match(pattern, symbol))


def parse_equity_list(csv_content: str) -> Dict:
    """
    Parse NSE EQUITY_L.csv content.

    Expected columns (case-sensitive, spaces matter):
    - SYMBOL
    - NAME OF COMPANY (note the spaces)
    - SERIES
    - DATE OF LISTING
    - PAID UP VALUE
    - MARKET LOT
    - ISIN NUMBER (note the space)
    - FACE VALUE

    Args:
        csv_content: CSV file content as string

    Returns:
        Dict with:
        - success: bool
        - data: List of dicts with security data
        - errors: List of error messages
        - stats: Dict with parsing statistics
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "stats": {
            "total_rows": 0,
            "parsed_successfully": 0,
            "skipped": 0,
            "failed": 0
        }
    }

    try:
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Strip spaces from column names to handle CSV formatting variations
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            result["stats"]["total_rows"] += 1

            try:
                # Extract and validate required fields
                symbol = row.get('SYMBOL', '').strip()
                isin = row.get('ISIN NUMBER', '').strip()
                security_name = row.get('NAME OF COMPANY', '').strip()
                series = row.get('SERIES', '').strip()

                # Validation
                if not symbol:
                    result["errors"].append(f"Row {row_num}: Missing SYMBOL")
                    result["stats"]["failed"] += 1
                    continue

                if not validate_symbol(symbol):
                    result["errors"].append(f"Row {row_num}: Invalid SYMBOL format: {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                if not isin:
                    result["errors"].append(f"Row {row_num}: Missing ISIN NUMBER")
                    result["stats"]["failed"] += 1
                    continue

                if not validate_isin(isin):
                    result["errors"].append(f"Row {row_num}: Invalid ISIN format: {isin}")
                    result["stats"]["failed"] += 1
                    continue

                if not security_name:
                    result["errors"].append(f"Row {row_num}: Missing NAME OF COMPANY")
                    result["stats"]["failed"] += 1
                    continue

                # Parse optional fields
                listing_date = parse_date(row.get('DATE OF LISTING', ''), '%d-%b-%Y')
                paid_up_value = parse_decimal(row.get('PAID UP VALUE', ''))
                market_lot_str = row.get('MARKET LOT', '').strip()
                face_value = parse_decimal(row.get('FACE VALUE', ''))

                # Market lot is required and must be positive integer
                market_lot = None
                if market_lot_str:
                    try:
                        market_lot = int(market_lot_str)
                        if market_lot <= 0:
                            result["errors"].append(f"Row {row_num}: MARKET LOT must be positive: {market_lot}")
                            result["stats"]["failed"] += 1
                            continue
                    except ValueError:
                        result["errors"].append(f"Row {row_num}: Invalid MARKET LOT: {market_lot_str}")
                        result["stats"]["failed"] += 1
                        continue

                # Build security dict
                security = {
                    "symbol": symbol,
                    "isin": isin,
                    "security_name": security_name,
                    "series": series if series else None,
                    "listing_date": listing_date,
                    "paid_up_value": paid_up_value,
                    "market_lot": market_lot,
                    "face_value": face_value,
                    "security_type": "EQUITY",
                    "is_active": True
                }

                result["data"].append(security)
                result["stats"]["parsed_successfully"] += 1

            except Exception as e:
                result["errors"].append(f"Row {row_num}: Unexpected error: {str(e)}")
                result["stats"]["failed"] += 1

        result["success"] = result["stats"]["parsed_successfully"] > 0

    except Exception as e:
        result["errors"].append(f"CSV parsing failed: {str(e)}")
        result["success"] = False

    return result


def parse_etf_list(csv_content: str) -> Dict:
    """
    Parse NSE eq_etfseclist.csv content.

    Expected columns:
    - Symbol
    - Underlying
    - SecurityName
    - DateofListing
    - MarketLot
    - ISINNumber
    - FaceValue

    Args:
        csv_content: CSV file content as string

    Returns:
        Dict with:
        - success: bool
        - data: List of dicts with ETF data
        - errors: List of error messages
        - stats: Dict with parsing statistics
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "stats": {
            "total_rows": 0,
            "parsed_successfully": 0,
            "skipped": 0,
            "failed": 0
        }
    }

    try:
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Strip spaces from column names to handle CSV formatting variations
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            result["stats"]["total_rows"] += 1

            try:
                # Extract and validate required fields
                symbol = row.get('Symbol', '').strip()
                isin = row.get('ISINNumber', '').strip()
                security_name = row.get('SecurityName', '').strip()
                underlying = row.get('Underlying', '').strip()

                # Validation
                if not symbol:
                    result["errors"].append(f"Row {row_num}: Missing Symbol")
                    result["stats"]["failed"] += 1
                    continue

                if not validate_symbol(symbol):
                    result["errors"].append(f"Row {row_num}: Invalid Symbol format: {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                if not isin:
                    result["errors"].append(f"Row {row_num}: Missing ISINNumber")
                    result["stats"]["failed"] += 1
                    continue

                if not validate_isin(isin):
                    result["errors"].append(f"Row {row_num}: Invalid ISIN format: {isin}")
                    result["stats"]["failed"] += 1
                    continue

                if not security_name:
                    result["errors"].append(f"Row {row_num}: Missing SecurityName")
                    result["stats"]["failed"] += 1
                    continue

                # Parse optional fields (DateofListing uses different format: "08-Jan-02")
                listing_date = parse_date(row.get('DateofListing', ''), '%d-%b-%y')
                market_lot_str = row.get('MarketLot', '').strip()
                face_value = parse_decimal(row.get('FaceValue', ''))

                # Market lot is required and must be positive integer
                market_lot = None
                if market_lot_str:
                    try:
                        market_lot = int(market_lot_str)
                        if market_lot <= 0:
                            result["errors"].append(f"Row {row_num}: MarketLot must be positive: {market_lot}")
                            result["stats"]["failed"] += 1
                            continue
                    except ValueError:
                        result["errors"].append(f"Row {row_num}: Invalid MarketLot: {market_lot_str}")
                        result["stats"]["failed"] += 1
                        continue

                # Build ETF dict (combine SecurityName and Underlying for full name)
                etf_full_name = f"{security_name}"
                if underlying:
                    etf_full_name = f"{underlying} - {security_name}"

                security = {
                    "symbol": symbol,
                    "isin": isin,
                    "security_name": etf_full_name,
                    "series": "EQ",  # ETFs typically trade in EQ series
                    "listing_date": listing_date,
                    "paid_up_value": None,  # Not provided in ETF list
                    "market_lot": market_lot,
                    "face_value": face_value,
                    "security_type": "ETF",
                    "is_active": True
                }

                result["data"].append(security)
                result["stats"]["parsed_successfully"] += 1

            except Exception as e:
                result["errors"].append(f"Row {row_num}: Unexpected error: {str(e)}")
                result["stats"]["failed"] += 1

        result["success"] = result["stats"]["parsed_successfully"] > 0

    except Exception as e:
        result["errors"].append(f"CSV parsing failed: {str(e)}")
        result["success"] = False

    return result
