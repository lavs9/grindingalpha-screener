"""
Data Ingestion API Endpoints.

Provides endpoints for triggering data ingestion from various sources.
These endpoints are typically called by n8n workflows or manual triggers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.services.nse.securities_service import ingest_securities_from_nse
from app.services.nse.market_cap_service import ingest_market_cap_from_nse
from app.services.nse.deals_service import ingest_deals_from_nse
from app.services.nse.surveillance_service import fetch_surveillance_data, ingest_surveillance
from datetime import date

router = APIRouter()


@router.post("/securities")
async def ingest_securities(
    file_path: Optional[str] = Query(None, description="Optional local file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE equity securities list (EQUITY_L.csv).

    This endpoint fetches the latest equity securities list from NSE archives,
    parses the CSV, validates the data, and inserts/updates records in the database.

    **Source:** https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv

    **Process:**
    1. Fetch CSV from NSE or read from local file (if file_path provided)
    2. Parse and validate each security record
    3. Insert new securities or update existing ones (upsert on symbol)
    4. Return statistics and any errors encountered

    **Query Parameters:**
    - file_path: Optional local file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - source: URL or file path that was processed
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_successfully, failed)
    - ingestion_result: Database insertion results (records_inserted, records_failed)
    - total_errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE (production)
    curl -X POST http://localhost:8000/api/v1/ingest/securities

    # Test with sample file
    curl -X POST "http://localhost:8000/api/v1/ingest/securities?file_path=/path/to/EQUITY_L_sample.csv"
    ```
    """
    result = ingest_securities_from_nse(db=db, use_equity=True, file_path=file_path)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Securities ingestion failed",
                "errors": result.get("total_errors", []),
                "parse_stats": result.get("parse_stats", {}),
                "ingestion_result": result.get("ingestion_result")
            }
        )

    return {
        "message": "Securities ingestion completed",
        "success": True,
        "source": result["source"],
        "parse_stats": result["parse_stats"],
        "ingestion_result": result["ingestion_result"],
        "errors": result.get("total_errors", [])
    }


@router.post("/etf")
async def ingest_etf(
    file_path: Optional[str] = Query(None, description="Optional local file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE ETF list (eq_etfseclist.csv).

    This endpoint fetches the latest ETF list from NSE archives,
    parses the CSV, validates the data, and inserts/updates records in the database.

    **Source:** https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv

    **Process:**
    1. Fetch CSV from NSE or read from local file (if file_path provided)
    2. Parse and validate each ETF record
    3. Insert new ETFs or update existing ones (upsert on symbol)
    4. Mark security_type as 'ETF' for all records
    5. Return statistics and any errors encountered

    **Query Parameters:**
    - file_path: Optional local file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - source: URL or file path that was processed
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_successfully, failed)
    - ingestion_result: Database insertion results (records_inserted, records_failed)
    - total_errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE (production)
    curl -X POST http://localhost:8000/api/v1/ingest/etf

    # Test with sample file
    curl -X POST "http://localhost:8000/api/v1/ingest/etf?file_path=/path/to/eq_etfseclist_sample.csv"
    ```
    """
    result = ingest_securities_from_nse(db=db, use_equity=False, file_path=file_path)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "ETF ingestion failed",
                "errors": result.get("total_errors", []),
                "parse_stats": result.get("parse_stats", {}),
                "ingestion_result": result.get("ingestion_result")
            }
        )

    return {
        "message": "ETF ingestion completed",
        "success": True,
        "source": result["source"],
        "parse_stats": result["parse_stats"],
        "ingestion_result": result["ingestion_result"],
        "errors": result.get("total_errors", [])
    }


@router.post("/market-cap")
async def ingest_market_cap(
    target_date: Optional[str] = Query(None, description="Date to fetch market cap for (YYYY-MM-DD format)"),
    file_path: Optional[str] = Query(None, description="Optional local ZIP file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE market cap data from PR{DDMMYY}.zip archives.

    This endpoint fetches market cap data from NSE archives for a specific date,
    extracts the MCAP{DDMMYYYY}.csv file from the ZIP archive, parses the data,
    and inserts/updates records in the market_cap_history table.

    **Source:** https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip

    **Process:**
    1. Download ZIP archive from NSE or read from local file (if file_path provided)
    2. Extract MCAP{DDMMYYYY}.csv from ZIP (handles subdirectories)
    3. Parse and validate each market cap record
    4. Skip symbols that don't exist in securities table (configurable)
    5. Insert new records or update existing ones (upsert on symbol+date)
    6. Return statistics and any errors encountered

    **Query Parameters:**
    - target_date: Date to fetch data for (YYYY-MM-DD format). Defaults to today.
    - file_path: Optional local ZIP file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - source: URL or file path that was processed
    - trade_date: Actual trade date from the CSV file
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_successfully, failed)
    - ingestion_result: Database insertion results (records_inserted, records_skipped)
    - total_errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE for today
    curl -X POST http://localhost:8000/api/v1/ingest/market-cap

    # Fetch from NSE for specific date
    curl -X POST "http://localhost:8000/api/v1/ingest/market-cap?target_date=2025-01-16"

    # Test with sample ZIP file
    curl -X POST "http://localhost:8000/api/v1/ingest/market-cap?file_path=/app/.claude/samples/PR160125_sample.zip"
    ```
    """
    # Parse target_date or use today
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Invalid date format: {target_date}. Use YYYY-MM-DD format."}
            )
    else:
        parsed_date = date.today()

    # Ingest market cap data
    try:
        result = ingest_market_cap_from_nse(
            db=db,
            target_date=parsed_date,
            file_path=file_path,
            skip_missing_symbols=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Unexpected error during market cap ingestion: {str(e)}",
                "error_type": type(e).__name__
            }
        )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Market cap ingestion failed",
                "errors": result.get("total_errors", result.get("fetch_errors", [])),
                "trade_date": result.get("trade_date"),
                "parse_stats": result.get("parse_stats", {}),
                "ingestion_result": result.get("ingestion_result")
            }
        )

    return {
        "message": "Market cap ingestion completed",
        "success": True,
        "source": result.get("source", ""),
        "trade_date": result.get("trade_date"),
        "parse_stats": result.get("parse_stats", {}),
        "ingestion_result": result.get("ingestion_result", {}),
        "errors": result.get("total_errors", [])
    }


@router.post("/bulk-deals")
async def ingest_bulk_deals(
    file_path: Optional[str] = Query(None, description="Optional local CSV file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE bulk deals data.

    This endpoint fetches bulk deals data from NSE archives, parses the CSV,
    validates the data, and inserts records into the bulk_deals table.

    **Source:** https://nsearchives.nseindia.com/content/equities/bulk.csv

    **Process:**
    1. Fetch CSV from NSE or read from local file (if file_path provided)
    2. Parse and validate each bulk deal record
    3. Skip symbols that don't exist in securities table (optional)
    4. Insert records (no upsert - each deal is a unique event)
    5. Return statistics and any errors encountered

    **Query Parameters:**
    - file_path: Optional local CSV file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - source: URL or file path that was processed
    - deal_date: The date from the CSV file
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_successfully, failed)
    - ingestion_result: Database insertion results (records_inserted, records_skipped)
    - total_errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE (production)
    curl -X POST http://localhost:8000/api/v1/ingest/bulk-deals

    # Test with sample CSV file
    curl -X POST "http://localhost:8000/api/v1/ingest/bulk-deals?file_path=/app/.claude/samples/bulk_sample.csv"
    ```
    """
    try:
        result = ingest_deals_from_nse(
            db=db,
            deal_type="BULK",
            file_path=file_path,
            skip_missing_symbols=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Unexpected error during bulk deals ingestion: {str(e)}",
                "error_type": type(e).__name__
            }
        )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Bulk deals ingestion failed",
                "errors": result.get("total_errors", result.get("fetch_errors", [])),
                "deal_date": result.get("deal_date"),
                "parse_stats": result.get("parse_stats", {}),
                "ingestion_result": result.get("ingestion_result")
            }
        )

    return {
        "message": "Bulk deals ingestion completed",
        "success": True,
        "source": result.get("source", ""),
        "deal_date": result.get("deal_date"),
        "parse_stats": result.get("parse_stats", {}),
        "ingestion_result": result.get("ingestion_result", {}),
        "errors": result.get("total_errors", [])
    }


@router.post("/block-deals")
async def ingest_block_deals(
    file_path: Optional[str] = Query(None, description="Optional local CSV file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE block deals data.

    This endpoint fetches block deals data from NSE archives, parses the CSV,
    validates the data, and inserts records into the block_deals table.

    **Source:** https://nsearchives.nseindia.com/content/equities/block.csv

    **Process:**
    1. Fetch CSV from NSE or read from local file (if file_path provided)
    2. Parse and validate each block deal record
    3. Skip symbols that don't exist in securities table (optional)
    4. Insert records (no upsert - each deal is a unique event)
    5. Return statistics and any errors encountered

    **Query Parameters:**
    - file_path: Optional local CSV file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - source: URL or file path that was processed
    - deal_date: The date from the CSV file
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_successfully, failed)
    - ingestion_result: Database insertion results (records_inserted, records_skipped)
    - total_errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE (production)
    curl -X POST http://localhost:8000/api/v1/ingest/block-deals

    # Test with sample CSV file
    curl -X POST "http://localhost:8000/api/v1/ingest/block-deals?file_path=/app/.claude/samples/block_sample.csv"
    ```
    """
    try:
        result = ingest_deals_from_nse(
            db=db,
            deal_type="BLOCK",
            file_path=file_path,
            skip_missing_symbols=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Unexpected error during block deals ingestion: {str(e)}",
                "error_type": type(e).__name__
            }
        )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Block deals ingestion failed",
                "errors": result.get("total_errors", result.get("fetch_errors", [])),
                "deal_date": result.get("deal_date"),
                "parse_stats": result.get("parse_stats", {}),
                "ingestion_result": result.get("ingestion_result")
            }
        )

    return {
        "message": "Block deals ingestion completed",
        "success": True,
        "source": result.get("source", ""),
        "deal_date": result.get("deal_date"),
        "parse_stats": result.get("parse_stats", {}),
        "ingestion_result": result.get("ingestion_result", {}),
        "errors": result.get("total_errors", [])
    }


@router.post("/surveillance")
async def ingest_surveillance_data(
    filename: Optional[str] = Query(None, description="NSE filename (e.g., 'REG1_IND160125.csv')"),
    ingestion_date: Optional[str] = Query(None, description="Date override (YYYY-MM-DD format)"),
    file_path: Optional[str] = Query(None, description="Optional local file path for testing"),
    db: Session = Depends(get_db)
):
    """
    Ingest NSE Surveillance Measures data (REG1_IND format).

    This endpoint fetches surveillance data from NSE archives, parses the 63-column CSV,
    and stores it across 4 normalized database tables for efficient querying.

    **Source:** https://nsearchives.nseindia.com/surveillance/REG1_IND{DDMMYY}.csv

    **Data Structure:**
    - 63 total columns with surveillance measures and risk indicators
    - Stored in 4 normalized tables:
        1. surveillance_list (16 columns) - Core staged measures + binary flags
        2. surveillance_fundamental_flags (10 columns) - Financial/compliance risks
        3. surveillance_price_movement (11 columns) - Close-to-close price movements
        4. surveillance_price_variation (7 columns) - High-low volatility indicators

    **Surveillance Measures:**
    - **Staged Measures:** GSM (0-6), Long/Short Term ASM (1-4, 1-2), ESM (1-2),
                          IRP (0-2), Default (0-1), ICA (0-1), SMS (0-1)
    - **Binary Flags:** High promoter pledge, Add-on price band, Total pledge, Social media
    - **Financial Flags:** Loss-making, High encumbrance (>50%), Zero EPS, BZ/SZ series, etc.
    - **Price Momentum:** 11 close-to-close thresholds (25%-200% over 5d-365d)
    - **Volatility:** 7 high-low variation thresholds (75%-300% over 1m-12m)

    **Process:**
    1. Fetch CSV from NSE or read from local file (if file_path provided)
    2. Parse all 63 columns and split into 4 tables (18 filler columns ignored)
    3. Convert NSE encoding: "100" → NULL, "0"/"1"/"2" → stage level/flagged
    4. Validate data consistency across all 4 tables
    5. UPSERT records (replace existing data for same date)
    6. Return statistics per table and any errors

    **Query Parameters:**
    - filename: NSE filename (e.g., "REG1_IND160125.csv") - date extracted from filename
    - ingestion_date: Optional date override (YYYY-MM-DD format) - overrides filename date
    - file_path: Optional local file path (for testing with sample files)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - ingestion_date: Date of the surveillance snapshot
    - source: URL or file path that was processed
    - parse_stats: Statistics from CSV parsing (total_rows, parsed_rows, error_rows)
    - records_inserted: Per-table insertion counts
    - errors: List of all errors encountered

    **Example Usage:**
    ```bash
    # Fetch from NSE (production) with filename
    curl -X POST "http://localhost:8000/api/v1/ingest/surveillance?filename=REG1_IND160125.csv"

    # With explicit date override
    curl -X POST "http://localhost:8000/api/v1/ingest/surveillance?filename=REG1_IND160125.csv&ingestion_date=2025-01-16"

    # Test with local sample file
    curl -X POST "http://localhost:8000/api/v1/ingest/surveillance?file_path=.claude/samples/REG1_IND160125.csv"
    ```

    **References:**
    - Specification: .claude/file-formats-surveillance.md
    - NSE Circular: NSE/SURV/65097 dated November 14, 2024
    - Database Models: app/models/surveillance.py
    """
    # Convert date string to date object if provided
    date_override = None
    if ingestion_date:
        try:
            date_override = date.fromisoformat(ingestion_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Invalid date format: {ingestion_date}. Use YYYY-MM-DD."}
            )

    # Fetch and parse surveillance data
    fetch_result = fetch_surveillance_data(
        filename=filename,
        ingestion_date=date_override,
        file_path=file_path
    )

    if not fetch_result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Surveillance data fetch/parse failed",
                "errors": fetch_result.get("errors", []),
                "parse_stats": fetch_result.get("stats", {}),
                "source": fetch_result.get("source", "")
            }
        )

    # Ingest into database
    ingest_result = ingest_surveillance(
        db=db,
        surveillance_data=fetch_result["data"],
        skip_missing_symbols=True
    )

    if not ingest_result["success"]:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Surveillance data ingestion failed",
                "errors": ingest_result.get("errors", []),
                "parse_stats": fetch_result.get("stats", {}),
                "records_inserted": ingest_result.get("records_inserted", {})
            }
        )

    # Calculate total records inserted across all tables
    total_inserted = sum(ingest_result["records_inserted"].values())

    return {
        "message": f"Surveillance data ingestion completed for {fetch_result['ingestion_date']}",
        "success": True,
        "ingestion_date": fetch_result["ingestion_date"],
        "source": fetch_result.get("source", ""),
        "parse_stats": fetch_result.get("stats", {}),
        "records_inserted": ingest_result.get("records_inserted", {}),
        "records_updated": ingest_result.get("records_updated", {}),
        "total_records": total_inserted,
        "errors": fetch_result.get("errors", []) + ingest_result.get("errors", [])
    }
