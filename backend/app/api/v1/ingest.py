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
