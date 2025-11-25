"""
NSE Bulk & Block Deals Service.

Handles fetching, parsing, and storing NSE bulk and block deals data.
Both endpoints use the same CSV format with different URLs.
"""
import requests
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.models.events import BulkDeal, BlockDeal
from app.services.nse.deals_parser import parse_deals_csv


# NSE Archive URLs
BULK_DEALS_URL = "https://nsearchives.nseindia.com/content/equities/bulk.csv"
BLOCK_DEALS_URL = "https://nsearchives.nseindia.com/content/equities/block.csv"


class DealsServiceError(Exception):
    """Raised when deals service operations fail."""
    pass


def fetch_deals_data(deal_type: str = "BULK", file_path: Optional[str] = None) -> Dict:
    """
    Fetch and parse NSE deals data (bulk or block).

    Args:
        deal_type: "BULK" or "BLOCK"
        file_path: Optional local file path (for testing)

    Returns:
        Dict with:
        - success: bool
        - data: List of parsed deal records
        - errors: List of error messages
        - source: URL or file path
        - deal_date: The date from the CSV file
        - stats: Parsing statistics
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "source": "",
        "deal_date": None,
        "stats": {}
    }

    deal_type = deal_type.upper()
    if deal_type not in ("BULK", "BLOCK"):
        result["errors"].append(f"Invalid deal_type: {deal_type}. Must be BULK or BLOCK.")
        return result

    try:
        # Fetch CSV content
        if file_path:
            # Read from local file (for testing)
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            result["source"] = f"file://{file_path}"
        else:
            # Fetch from NSE archive
            url = BULK_DEALS_URL if deal_type == "BULK" else BLOCK_DEALS_URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            csv_content = response.text
            result["source"] = url

        # Parse CSV
        parse_result = parse_deals_csv(csv_content, deal_category=deal_type)

        result["success"] = parse_result["success"]
        result["data"] = parse_result["data"]
        result["errors"] = parse_result["errors"]
        result["stats"] = parse_result["stats"]
        result["deal_date"] = parse_result.get("deal_date")

    except requests.exceptions.RequestException as e:
        result["errors"].append(f"HTTP request failed: {str(e)}")
        result["success"] = False
    except FileNotFoundError as e:
        result["errors"].append(f"File not found: {str(e)}")
        result["success"] = False
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        result["success"] = False

    return result


def ingest_deals(
    db: Session,
    deals_data: list,
    deal_type: str = "BULK",
    skip_missing_symbols: bool = False
) -> Dict:
    """
    Insert deal records into database.

    Note: Unlike market cap, we don't use UPSERT here. Each deal is a unique event,
    even if same client/symbol/date. We allow duplicates intentionally.

    Args:
        db: SQLAlchemy database session
        deals_data: List of deal dicts from parser
        deal_type: "BULK" or "BLOCK"
        skip_missing_symbols: If True, skip symbols not in securities table

    Returns:
        Dict with ingestion statistics
    """
    result = {
        "success": False,
        "records_inserted": 0,
        "records_failed": 0,
        "records_skipped": 0,
        "errors": []
    }

    if not deals_data:
        result["success"] = True  # No data is not an error
        return result

    deal_type = deal_type.upper()
    Model = BulkDeal if deal_type == "BULK" else BlockDeal

    # Get list of valid symbols if skip_missing_symbols
    valid_symbols = set()
    if skip_missing_symbols:
        from app.models.security import Security
        symbols_query = db.query(Security.symbol).all()
        valid_symbols = {s[0] for s in symbols_query}

    try:
        for record in deals_data:
            try:
                symbol = record.get('symbol')

                # Skip if symbol not in securities table
                if skip_missing_symbols and symbol not in valid_symbols:
                    result["records_skipped"] += 1
                    continue

                # Insert new record (no upsert - each deal is unique)
                deal = Model(**record)
                db.add(deal)
                result["records_inserted"] += 1

            except IntegrityError as e:
                db.rollback()
                result["errors"].append(f"Integrity error for {record.get('symbol')}: {str(e)}")
                result["records_failed"] += 1
            except Exception as e:
                db.rollback()
                result["errors"].append(f"Error inserting {record.get('symbol')}: {str(e)}")
                result["records_failed"] += 1

        # Commit all changes
        db.commit()
        result["success"] = True  # Success even if some failed, as long as we didn't crash

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database transaction failed: {str(e)}")
        result["success"] = False

    return result


def ingest_deals_from_nse(
    db: Session,
    deal_type: str = "BULK",
    file_path: Optional[str] = None,
    skip_missing_symbols: bool = False
) -> Dict:
    """
    Complete workflow: Fetch, parse, and ingest deals data.

    Args:
        db: SQLAlchemy database session
        deal_type: "BULK" or "BLOCK"
        file_path: Optional local file path (for testing)
        skip_missing_symbols: If True, only insert symbols that exist in securities table

    Returns:
        Dict with complete ingestion results
    """
    # Fetch and parse
    fetch_result = fetch_deals_data(deal_type=deal_type, file_path=file_path)

    if not fetch_result["success"]:
        return {
            "success": False,
            "source": fetch_result["source"],
            "deal_date": fetch_result.get("deal_date"),
            "fetch_errors": fetch_result["errors"],
            "parse_stats": fetch_result.get("stats", {}),
            "ingestion_result": None
        }

    # Handle "no records" case
    if fetch_result["stats"].get("no_records", False):
        return {
            "success": True,
            "source": fetch_result["source"],
            "deal_date": fetch_result.get("deal_date"),
            "parse_stats": fetch_result["stats"],
            "ingestion_result": {
                "success": True,
                "records_inserted": 0,
                "records_failed": 0,
                "records_skipped": 0,
                "errors": []
            },
            "total_errors": fetch_result["errors"]
        }

    # Ingest to database
    ingestion_result = ingest_deals(
        db=db,
        deals_data=fetch_result["data"],
        deal_type=deal_type,
        skip_missing_symbols=skip_missing_symbols
    )

    return {
        "success": ingestion_result["success"],
        "source": fetch_result["source"],
        "deal_date": fetch_result["deal_date"],
        "parse_stats": fetch_result.get("stats", {}),
        "ingestion_result": ingestion_result,
        "total_errors": fetch_result["errors"] + ingestion_result["errors"]
    }
