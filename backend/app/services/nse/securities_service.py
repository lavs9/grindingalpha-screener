"""
NSE Securities Service.

Handles fetching, parsing, and storing NSE securities and ETF data.
Implements business logic for security ingestion with database transactions.
"""
import requests
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.models.security import Security
from app.services.nse.securities_parser import parse_equity_list, parse_etf_list


# NSE Archive URLs
EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
ETF_LIST_URL = "https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv"


def fetch_securities_list(use_equity: bool = True, file_path: str = None) -> Dict:
    """
    Fetch and parse NSE securities list.

    Args:
        use_equity: If True, fetch EQUITY_L.csv; if False, fetch eq_etfseclist.csv
        file_path: Optional local file path to read from (for testing with samples)

    Returns:
        Dict with:
        - success: bool
        - data: List of parsed securities
        - errors: List of error messages
        - source: str (url or file path)
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "source": ""
    }

    try:
        # Fetch CSV content
        if file_path:
            # Read from local file (for testing)
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            result["source"] = f"file://{file_path}"
        else:
            # Fetch from NSE archive
            url = EQUITY_LIST_URL if use_equity else ETF_LIST_URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            csv_content = response.text
            result["source"] = url

        # Parse CSV
        if use_equity:
            parse_result = parse_equity_list(csv_content)
        else:
            parse_result = parse_etf_list(csv_content)

        result["success"] = parse_result["success"]
        result["data"] = parse_result["data"]
        result["errors"] = parse_result["errors"]
        result["stats"] = parse_result["stats"]

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


def ingest_securities(db: Session, securities_data: list) -> Dict:
    """
    Insert or update securities in database.

    Uses PostgreSQL UPSERT (INSERT ... ON CONFLICT) to handle duplicates.
    Updates existing records if symbol already exists.

    Args:
        db: SQLAlchemy database session
        securities_data: List of security dicts from parser

    Returns:
        Dict with:
        - success: bool
        - records_inserted: int
        - records_updated: int
        - records_failed: int
        - errors: List of error messages
    """
    result = {
        "success": False,
        "records_inserted": 0,
        "records_updated": 0,
        "records_failed": 0,
        "errors": []
    }

    if not securities_data:
        result["errors"].append("No securities data provided")
        return result

    try:
        for security_dict in securities_data:
            try:
                # Use PostgreSQL INSERT ... ON CONFLICT for upsert
                stmt = insert(Security).values(**security_dict)

                # On conflict (symbol already exists), update the record
                stmt = stmt.on_conflict_do_update(
                    index_elements=['symbol'],
                    set_={
                        'isin': stmt.excluded.isin,
                        'security_name': stmt.excluded.security_name,
                        'series': stmt.excluded.series,
                        'listing_date': stmt.excluded.listing_date,
                        'paid_up_value': stmt.excluded.paid_up_value,
                        'market_lot': stmt.excluded.market_lot,
                        'face_value': stmt.excluded.face_value,
                        'security_type': stmt.excluded.security_type,
                        'is_active': stmt.excluded.is_active,
                        'updated_at': stmt.excluded.updated_at,
                    }
                )

                # Execute and check if it was insert or update
                result_proxy = db.execute(stmt)

                # Note: PostgreSQL doesn't easily tell us if it was insert or update
                # We'll count as inserted for now
                result["records_inserted"] += 1

            except IntegrityError as e:
                db.rollback()
                result["errors"].append(f"Integrity error for {security_dict.get('symbol')}: {str(e)}")
                result["records_failed"] += 1
            except Exception as e:
                db.rollback()
                result["errors"].append(f"Error inserting {security_dict.get('symbol')}: {str(e)}")
                result["records_failed"] += 1

        # Commit all changes
        db.commit()
        result["success"] = result["records_inserted"] > 0

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database transaction failed: {str(e)}")
        result["success"] = False

    return result


def ingest_securities_from_nse(db: Session, use_equity: bool = True, file_path: str = None) -> Dict:
    """
    Complete workflow: Fetch, parse, and ingest securities.

    Args:
        db: SQLAlchemy database session
        use_equity: If True, fetch equities; if False, fetch ETFs
        file_path: Optional local file path (for testing)

    Returns:
        Dict with complete ingestion results including fetch, parse, and insert stats
    """
    # Fetch and parse
    fetch_result = fetch_securities_list(use_equity=use_equity, file_path=file_path)

    if not fetch_result["success"]:
        return {
            "success": False,
            "source": fetch_result["source"],
            "fetch_errors": fetch_result["errors"],
            "parse_stats": fetch_result.get("stats", {}),
            "ingestion_result": None
        }

    # Ingest to database
    ingestion_result = ingest_securities(db, fetch_result["data"])

    return {
        "success": ingestion_result["success"],
        "source": fetch_result["source"],
        "parse_stats": fetch_result.get("stats", {}),
        "ingestion_result": ingestion_result,
        "total_errors": fetch_result["errors"] + ingestion_result["errors"]
    }
