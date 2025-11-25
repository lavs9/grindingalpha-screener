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
