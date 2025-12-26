"""
NSE Market Cap Service.

Handles fetching, extracting, parsing, and storing NSE market cap data.
ZIP archives are downloaded, extracted, and the MCAP CSV file is parsed.
"""
import requests
import zipfile
import tempfile
import os
from datetime import datetime, date
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.models.timeseries import MarketCapHistory
from app.services.nse.market_cap_parser import parse_market_cap_csv


def get_market_cap_url(target_date: date) -> str:
    """
    Generate NSE market cap archive URL for a given date.

    URL format: https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip

    Args:
        target_date: Date to fetch market cap data for

    Returns:
        Full URL to the ZIP archive
    """
    # Format: DDMMYY (2-digit year)
    date_str = target_date.strftime('%d%m%y')
    return f"https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{date_str}.zip"


def extract_mcap_csv_from_zip(zip_path: str, target_date: date) -> Optional[str]:
    """
    Extract MCAP CSV file from ZIP archive.

    The ZIP contains a folder PR{DDMMYY}/ with multiple files.
    We need to find MCAP{DDMMYYYY}.csv (4-digit year).

    Args:
        zip_path: Path to ZIP file
        target_date: Date to locate correct CSV file

    Returns:
        CSV content as string, or None if not found
    """
    try:
        # Expected CSV filename: MCAP{DDMMYYYY}.csv (4-digit year)
        csv_filename = f"MCAP{target_date.strftime('%d%m%Y')}.csv"

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in ZIP
            zip_files = zip_ref.namelist()

            # Find the MCAP CSV file (may be in a subdirectory)
            mcap_file = None
            for file in zip_files:
                if csv_filename in file and not file.startswith('__MACOSX'):
                    mcap_file = file
                    break

            if not mcap_file:
                return None

            # Extract and read CSV content
            with zip_ref.open(mcap_file) as csv_file:
                return csv_file.read().decode('utf-8')

    except zipfile.BadZipFile as e:
        raise MarketCapParseError(f"Invalid ZIP file: {str(e)}")
    except Exception as e:
        raise MarketCapParseError(f"ZIP extraction failed: {str(e)}")


class MarketCapParseError(Exception):
    """Raised when market cap parsing fails."""
    pass


def fetch_market_cap_data(target_date: date, file_path: Optional[str] = None) -> Dict:
    """
    Fetch and parse NSE market cap data for a specific date.

    Args:
        target_date: Date to fetch market cap data for
        file_path: Optional local ZIP file path (for testing)

    Returns:
        Dict with:
        - success: bool
        - data: List of parsed market cap records
        - errors: List of error messages
        - source: URL or file path
        - trade_date: Actual trade date from CSV
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "source": "",
        "trade_date": None
    }

    temp_zip_path = None

    try:
        # Fetch ZIP file
        if file_path:
            # Use local file
            temp_zip_path = file_path
            result["source"] = f"file://{file_path}"
        else:
            # Download from NSE
            url = get_market_cap_url(target_date)
            result["source"] = url

            # Download to temporary file with browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()

            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False) as tmp:
                tmp.write(response.content)
                temp_zip_path = tmp.name

        # Extract and parse CSV
        csv_content = extract_mcap_csv_from_zip(temp_zip_path, target_date)

        if not csv_content:
            result["errors"].append(f"MCAP CSV file not found in archive for date {target_date}")
            return result

        # Parse CSV
        parse_result = parse_market_cap_csv(csv_content, expected_date=target_date)

        result["success"] = parse_result["success"]
        result["data"] = parse_result["data"]
        result["errors"] = parse_result["errors"]
        result["stats"] = parse_result["stats"]
        result["trade_date"] = parse_result["trade_date"]

    except requests.exceptions.RequestException as e:
        result["errors"].append(f"HTTP request failed: {str(e)}")
        result["success"] = False
    except MarketCapParseError as e:
        result["errors"].append(str(e))
        result["success"] = False
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        result["success"] = False
    finally:
        # Clean up temporary file if we downloaded it
        if temp_zip_path and not file_path and os.path.exists(temp_zip_path):
            try:
                os.unlink(temp_zip_path)
            except:
                pass

    return result


def ingest_market_cap(db: Session, market_cap_data: list, skip_missing_symbols: bool = True) -> Dict:
    """
    Insert or update market cap records in database.

    Uses PostgreSQL UPSERT (INSERT ... ON CONFLICT) to handle duplicates.

    Args:
        db: SQLAlchemy database session
        market_cap_data: List of market cap dicts from parser
        skip_missing_symbols: If True, skip symbols not in securities table

    Returns:
        Dict with ingestion statistics
    """
    result = {
        "success": False,
        "records_inserted": 0,
        "records_updated": 0,
        "records_failed": 0,
        "records_skipped": 0,
        "errors": []
    }

    if not market_cap_data:
        result["errors"].append("No market cap data provided")
        return result

    # Get list of valid symbols from securities table if skip_missing_symbols
    valid_symbols = set()
    if skip_missing_symbols:
        from app.models.security import Security
        symbols_query = db.query(Security.symbol).all()
        valid_symbols = {s[0] for s in symbols_query}

    try:
        for record in market_cap_data:
            try:
                symbol = record.get('symbol')

                # Skip if symbol not in securities table
                if skip_missing_symbols and symbol not in valid_symbols:
                    result["records_skipped"] += 1
                    continue

                # Use PostgreSQL INSERT ... ON CONFLICT for upsert
                stmt = insert(MarketCapHistory).values(**record)

                # On conflict (symbol + date), update the record
                stmt = stmt.on_conflict_do_update(
                    index_elements=['symbol', 'date'],
                    set_={
                        'market_cap': stmt.excluded.market_cap,
                        'close_price': stmt.excluded.close_price,
                        'issue_size': stmt.excluded.issue_size,
                        'face_value': stmt.excluded.face_value,
                        'category': stmt.excluded.category,
                        'series': stmt.excluded.series,
                    }
                )

                db.execute(stmt)
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
        result["success"] = result["records_inserted"] > 0

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database transaction failed: {str(e)}")
        result["success"] = False

    return result


def ingest_market_cap_from_nse(
    db: Session,
    target_date: date,
    file_path: Optional[str] = None,
    skip_missing_symbols: bool = True
) -> Dict:
    """
    Complete workflow: Fetch, extract, parse, and ingest market cap data.

    Args:
        db: SQLAlchemy database session
        target_date: Date to fetch market cap data for
        file_path: Optional local ZIP file path (for testing)
        skip_missing_symbols: If True, only insert symbols that exist in securities table

    Returns:
        Dict with complete ingestion results
    """
    # Fetch and parse
    fetch_result = fetch_market_cap_data(target_date=target_date, file_path=file_path)

    if not fetch_result["success"]:
        return {
            "success": False,
            "source": fetch_result["source"],
            "trade_date": fetch_result.get("trade_date"),
            "fetch_errors": fetch_result["errors"],
            "parse_stats": fetch_result.get("stats", {}),
            "ingestion_result": None
        }

    # Ingest to database
    ingestion_result = ingest_market_cap(
        db=db,
        market_cap_data=fetch_result["data"],
        skip_missing_symbols=skip_missing_symbols
    )

    return {
        "success": ingestion_result["success"],
        "source": fetch_result["source"],
        "trade_date": fetch_result["trade_date"],
        "parse_stats": fetch_result.get("stats", {}),
        "ingestion_result": ingestion_result,
        "total_errors": fetch_result["errors"] + ingestion_result["errors"]
    }
