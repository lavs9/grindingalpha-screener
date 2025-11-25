"""
NSE Bulk & Block Deals Parser.

Parses bulk.csv and block.csv files from NSE archives.
Both files have identical format with different deal types.

References:
- .claude/file-formats.md Section 3.1 (Bulk Deals)
- .claude/file-formats.md Section 3.2 (Block Deals)
"""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from io import StringIO


class DealsParseError(Exception):
    """Raised when deals data parsing fails."""
    pass


def parse_deals_date(date_str: str) -> Optional[datetime.date]:
    """
    Parse deals date format: DD-MMM-YYYY (e.g., "24-NOV-2025").

    Args:
        date_str: Date string from CSV

    Returns:
        date object or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None

    try:
        # Format: "24-NOV-2025"
        return datetime.strptime(date_str.strip(), '%d-%b-%Y').date()
    except ValueError:
        # Try alternate format with spaces
        try:
            return datetime.strptime(date_str.strip(), '%d %b %Y').date()
        except ValueError:
            return None


def parse_deals_decimal(value_str: str) -> Optional[Decimal]:
    """
    Parse decimal value from deals CSV.

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


def parse_deals_csv(csv_content: str, deal_category: str = "BULK") -> Dict:
    """
    Parse NSE bulk.csv or block.csv content.

    Expected columns:
    - Date
    - Symbol
    - Security Name
    - Client Name
    - Buy/Sell
    - Quantity Traded
    - Trade Price / Wght. Avg. Price
    - Remarks

    Args:
        csv_content: CSV file content as string
        deal_category: "BULK" or "BLOCK" for logging purposes

    Returns:
        Dict with:
        - success: bool
        - data: List of dicts with deal data
        - errors: List of error messages
        - stats: Dict with parsing statistics
        - deal_date: The trade date from the file (if consistent)
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
            "no_records": False
        },
        "deal_date": None
    }

    try:
        # Check for "NO RECORDS" case
        if csv_content.strip().startswith("NO RECORDS"):
            result["stats"]["no_records"] = True
            result["success"] = True
            result["errors"].append("No deals recorded for this date")
            return result

        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Strip spaces from column names
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

        for row_num, row in enumerate(reader, start=2):
            result["stats"]["total_rows"] += 1

            try:
                # Extract required fields
                date_str = row.get('Date', '').strip()
                symbol = row.get('Symbol', '').strip()
                security_name = row.get('Security Name', '').strip()
                client_name = row.get('Client Name', '').strip()
                buy_sell = row.get('Buy/Sell', '').strip().upper()
                quantity_str = row.get('Quantity Traded', '').strip().replace(',', '')
                price = parse_deals_decimal(row.get('Trade Price / Wght. Avg. Price', ''))
                remarks = row.get('Remarks', '').strip()

                # Parse date
                deal_date = parse_deals_date(date_str)

                # Validation
                if not symbol:
                    result["errors"].append(f"Row {row_num}: Missing Symbol")
                    result["stats"]["failed"] += 1
                    continue

                if not deal_date:
                    result["errors"].append(f"Row {row_num}: Invalid Date: {date_str}")
                    result["stats"]["failed"] += 1
                    continue

                # Set deal_date from first valid row
                if result["deal_date"] is None:
                    result["deal_date"] = deal_date

                if not client_name:
                    result["errors"].append(f"Row {row_num}: Missing Client Name for {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                # Validate Buy/Sell
                if buy_sell not in ('BUY', 'SELL'):
                    result["errors"].append(f"Row {row_num}: Invalid Buy/Sell value '{buy_sell}' for {symbol} (must be BUY or SELL)")
                    result["stats"]["failed"] += 1
                    continue

                # Parse and validate quantity
                try:
                    quantity = int(quantity_str) if quantity_str else None
                    if quantity is None or quantity <= 0:
                        result["errors"].append(f"Row {row_num}: Invalid Quantity for {symbol}")
                        result["stats"]["failed"] += 1
                        continue
                except ValueError:
                    result["errors"].append(f"Row {row_num}: Invalid Quantity format for {symbol}: {quantity_str}")
                    result["stats"]["failed"] += 1
                    continue

                # Validate price
                if price is None or price <= 0:
                    result["errors"].append(f"Row {row_num}: Invalid Trade Price for {symbol}")
                    result["stats"]["failed"] += 1
                    continue

                # Build deal record
                deal_record = {
                    "date": deal_date,
                    "symbol": symbol,
                    "security_name": security_name if security_name else None,
                    "client_name": client_name,
                    "deal_type": buy_sell,
                    "quantity": quantity,
                    "price": price,
                }

                result["data"].append(deal_record)
                result["stats"]["parsed_successfully"] += 1

            except Exception as e:
                result["errors"].append(f"Row {row_num}: Unexpected error: {str(e)}")
                result["stats"]["failed"] += 1

        result["success"] = result["stats"]["parsed_successfully"] > 0 or result["stats"]["no_records"]

    except Exception as e:
        result["errors"].append(f"CSV parsing failed: {str(e)}")
        result["success"] = False

    return result
