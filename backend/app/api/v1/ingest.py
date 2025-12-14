"""
Data Ingestion API Endpoints.

Provides endpoints for triggering data ingestion from various sources.
These endpoints are typically called by n8n workflows or manual triggers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.database.session import get_db
from app.services.nse.securities_service import ingest_securities_from_nse
from app.services.nse.market_cap_service import ingest_market_cap_from_nse
from app.services.nse.deals_service import ingest_deals_from_nse
from app.services.nse.surveillance_service import fetch_surveillance_data, ingest_surveillance
from app.services.nse.industry_service import scrape_all_securities
from app.schemas.industry import IndustryIngestionRequest, IndustryIngestionResponse
from app.services.upstox.instrument_service import ingest_instruments_from_upstox
from app.services.upstox.daily_quotes_service import DailyQuotesService
from app.services.upstox.historical_service import HistoricalDataService
from app.services.upstox.batch_historical_service import BatchHistoricalService
from app.schemas.upstox import InstrumentIngestionResponse
from app.utils.resource_monitor import monitor_resources

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


@router.post("/industry-classification", response_model=IndustryIngestionResponse)
async def ingest_industry_classification(
    limit: Optional[int] = Query(None, gt=0, le=5000, description="Limit number of symbols to scrape (for testing)"),
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to scrape (e.g., ['RELIANCE', 'TCS'])"),
    db: Session = Depends(get_db)
):
    """
    Scrape industry classification and index constituents from NSE Quote Equity API.

    This endpoint uses Playwright to authenticate with NSE and scrape the Quote Equity API
    for all active securities, extracting:
    1. **Industry Classification**: 4-level hierarchy (Macro > Sector > Industry > Basic Industry)
    2. **Index Constituents**: Which indices each security belongs to (from pdSectorIndAll)

    **Data Source:** https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}

    **Rate Limiting:** 1 request/second to respect NSE server limits
    """
    try:
        # Run async scraper
        result = await scrape_all_securities(
            db=db,
            limit=limit,
            symbols=symbols
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Industry classification scraping failed",
                    "errors": result.get("errors", []),
                    "symbols_processed": result.get("symbols_processed", 0),
                    "symbols_failed": result.get("symbols_failed", 0)
                }
            )

        return IndustryIngestionResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Industry classification scraping failed: {str(e)}",
                "errors": [str(e)]
            }
        )


@router.post("/upstox-instruments", response_model=InstrumentIngestionResponse)
async def ingest_upstox_instruments(db: Session = Depends(get_db)):
    """
    Ingest Upstox instrument master data from NSE.json.gz.

    This endpoint downloads the Upstox instruments file, decompresses it,
    and ingests all NSE instruments into the database. It also auto-creates
    mappings between our securities table and Upstox instruments.

    **Source:** https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz

    **Process:**
    1. Download gzipped JSON file from Upstox
    2. Decompress and parse JSON
    3. UPSERT instruments to upstox_instruments table (batch size: 500)
    4. Auto-create symbol mappings (match by ISIN first, then symbol)
    5. Return statistics

    **Matching Logic:**
    - Equities: exchange='NSE_EQ', match by ISIN (confidence=100) or symbol (confidence=90)
    - Indices: Manual mapping only (not automated)

    **Returns:**
    - success: Whether ingestion completed successfully
    - total_instruments: Total instruments in source file (~2000+ for NSE)
    - instruments_inserted: New instruments added
    - instruments_updated: Existing instruments updated
    - mappings_created: Auto-created symbol mappings
    - errors: List of errors encountered
    - duration_seconds: Total execution time

    **Note:** This endpoint should be run:
    - Initially after setting up the database
    - Daily via n8n workflow (instruments may change)
    """

    result = ingest_instruments_from_upstox(db=db)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Upstox instrument ingestion failed",
                "errors": result.get("errors", []),
                "total_instruments": result.get("total_instruments", 0),
                "mappings_created": result.get("mappings_created", 0)
            }
        )

    return InstrumentIngestionResponse(**result)


@router.post("/daily-ohlcv")
async def ingest_daily_ohlcv(
    symbols: Optional[List[str]] = Query(None, description="Optional list of symbols to fetch. If not provided, fetches all active securities"),
    db: Session = Depends(get_db)
):
    """
    Ingest daily OHLCV data from Upstox for all active securities.

    This endpoint fetches the latest market quotes (OHLCV) from Upstox API for all active
    securities or a specified list of symbols. It's designed to be called by the Daily EOD
    n8n workflow after market close.

    **Source:** Upstox API `/v2/market-quote/quotes`

    **Process:**
    1. Get all active securities from database (or filter by provided symbols)
    2. Get instrument_key mappings from symbol_instrument_mapping table
    3. Fetch market quotes from Upstox (batch request, 500 symbols per call)
    4. Extract OHLCV, VWAP, circuits, 52w high/low
    5. UPSERT to ohlcv_daily table (symbol + today's date)
    6. Return statistics and errors

    **Query Parameters:**
    - symbols: Optional list of symbols (e.g., ["RELIANCE", "TCS", "INFY"])

    **Returns:**
    - success: Whether the ingestion completed successfully
    - total_symbols: Total securities processed
    - successful: Number of securities with data fetched successfully
    - failed: Number of securities that failed
    - errors: List of errors (symbol + error message)
    - execution_time_ms: Total execution time

    **Note:** This endpoint requires:
    - Active Upstox token (check /api/v1/auth/upstox/token-status)
    - Symbol-to-instrument mappings (run /api/v1/ingest/upstox-instruments first)

    **Used By:** Daily EOD Master n8n workflow (Mon-Fri 9 PM IST)
    """
    service = DailyQuotesService(db)
    result = service.fetch_daily_ohlcv(symbols=symbols)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Daily OHLCV ingestion failed or partially completed",
                "total_symbols": result["total_symbols"],
                "successful": result["successful"],
                "failed": result["failed"],
                "errors": result["errors"][:10]  # Limit to first 10 errors
            }
        )

    return result


@router.post("/historical-ohlcv/{symbol}")
async def ingest_historical_ohlcv(
    symbol: str,
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD). Defaults to 5 years ago or listing_date"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD). Defaults to today"),
    db: Session = Depends(get_db)
):
    """
    Ingest historical OHLCV data from Upstox for a single security.

    This endpoint fetches up to 5 years of daily historical OHLCV data for a specific symbol
    from Upstox API. It's used for initial backfill or filling gaps in historical data.

    **Source:** Upstox API `/v2/historical-candle/{instrument_key}/day/{to_date}/{from_date}`

    **Process:**
    1. Validate security exists in database
    2. Calculate date range (defaults: from=5 years ago, to=today)
    3. Get instrument_key from symbol_instrument_mapping
    4. Fetch historical candles from Upstox
    5. UPSERT to ohlcv_daily table (symbol + date)
    6. Detect gaps (missing trading days)
    7. Return statistics

    **Path Parameters:**
    - symbol: Security symbol (e.g., "RELIANCE")

    **Query Parameters:**
    - from_date: Start date in YYYY-MM-DD format (optional)
    - to_date: End date in YYYY-MM-DD format (optional)

    **Returns:**
    - success: Whether the ingestion completed successfully
    - symbol: Security symbol processed
    - records_inserted: New OHLCV records added
    - records_updated: Existing records updated
    - date_range: Actual date range processed
    - gaps_detected: List of missing trading days (first 10 only)
    - errors: List of errors encountered
    - execution_time_ms: Total execution time

    **Example:**
    ```
    POST /api/v1/ingest/historical-ohlcv/RELIANCE?from_date=2020-01-01&to_date=2025-12-06
    ```

    **Note:** This endpoint requires:
    - Active Upstox token
    - Symbol exists in securities table
    - Instrument mapping exists for the symbol

    **Used By:** Historical OHLCV Backfill n8n workflow (manual trigger)
    """
    service = HistoricalDataService(db)
    result = service.fetch_historical_ohlcv(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Historical OHLCV ingestion failed for {symbol}",
                "symbol": symbol,
                "errors": result["errors"]
            }
        )

    return result


@router.post("/historical-ohlcv-batch")
@monitor_resources("Historical OHLCV Batch Ingestion")
async def ingest_historical_ohlcv_batch(
    symbols: Optional[List[str]] = Query(None, description="Optional list of symbols. If not provided, processes all active securities"),
    start_date: Optional[date] = Query(None, description="Start date (default: 5 years ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: yesterday)"),
    batch_size: int = Query(50, description="Number of symbols to process per batch"),
    db: Session = Depends(get_db)
):
    """
    Batch ingest historical OHLCV data from Upstox for multiple securities.

    This endpoint fetches 5 years of historical daily OHLCV data from Upstox API
    for all active securities (or specified symbols) and stores them in the database.

    **Features:**
    - Batch processing (default: 50 symbols per batch to respect rate limits)
    - Automatic retry logic for failed requests
    - Resource monitoring and logging
    - Results logged to `ingestion_logs` table

    **Source:** Upstox Historical Candle API

    **Process:**
    1. Query active securities from database (or use provided symbols)
    2. For each security, map to Upstox instrument key
    3. Fetch historical OHLCV data in date range
    4. Insert/update records in `ohlcv_daily` table
    5. Log results to `ingestion_logs` table

    **Query Parameters:**
    - symbols: Optional list of specific symbols to process (default: all active securities)
    - start_date: Start date for historical data (default: 5 years ago)
    - end_date: End date for historical data (default: yesterday)
    - batch_size: Number of symbols per batch (default: 50)

    **Returns:**
    - success: Whether the overall ingestion succeeded
    - symbols_processed: Number of symbols successfully processed
    - records_inserted: Total OHLCV records inserted
    - records_updated: Total OHLCV records updated
    - symbols_failed: Number of symbols that failed
    - errors: List of errors (capped at 50 for readability)
    - execution_time_ms: Total execution time in milliseconds

    **Example Usage:**
    ```bash
    # Process all active securities (5 years of data)
    curl -X POST http://localhost:8001/api/v1/ingest/historical-ohlcv-batch

    # Process specific symbols with custom date range
    curl -X POST "http://localhost:8001/api/v1/ingest/historical-ohlcv-batch?symbols=RELIANCE&symbols=TCS&start_date=2023-01-01&end_date=2024-12-31"

    # Process with smaller batch size (for testing)
    curl -X POST "http://localhost:8001/api/v1/ingest/historical-ohlcv-batch?batch_size=10"
    ```

    **Note:** This operation can take 10-30 minutes for 2000+ securities.
    Monitor progress in backend logs and Grafana dashboards.
    """
    service = BatchHistoricalService(db)
    result = service.fetch_batch_historical_ohlcv(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        batch_size=batch_size
    )

    if not result["success"] and result["symbols_processed"] == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Historical OHLCV batch ingestion completely failed",
                "errors": result["errors"]
            }
        )

    return {
        "message": "Historical OHLCV batch ingestion completed",
        "success": result["success"],
        "symbols_processed": result["symbols_processed"],
        "records_inserted": result["records_inserted"],
        "records_updated": result["records_updated"],
        "symbols_failed": result["symbols_failed"],
        "errors": result["errors"][:50],  # Limit errors in response
        "execution_time_ms": result["execution_time_ms"]
    }


@router.post("/daily-ohlcv")
@monitor_resources("Daily OHLCV Ingestion")
async def ingest_daily_ohlcv(
    symbols: Optional[List[str]] = Query(None, description="Optional list of symbols. If not provided, processes all active securities"),
    target_date: Optional[date] = Query(None, description="Target date (default: yesterday)"),
    batch_size: int = Query(50, description="Number of symbols to process per batch"),
    db: Session = Depends(get_db)
):
    """
    Ingest yesterday's OHLCV data from Upstox for active securities.

    This endpoint is designed for daily automated runs (typically via n8n workflow).
    It fetches OHLCV data for a single trading day (default: yesterday) for all
    active securities.

    **Features:**
    - Fast execution (single date only)
    - Batch processing to respect rate limits
    - Resource monitoring
    - Results logged to `ingestion_logs` table (source='upstox_daily')

    **Source:** Upstox Historical Candle API (1 day range)

    **Process:**
    1. Determine target date (default: yesterday)
    2. Query active securities from database
    3. Batch process: Fetch OHLCV for target date
    4. Upsert records in `ohlcv_daily` table
    5. Log results to `ingestion_logs`

    **Query Parameters:**
    - symbols: Optional list of specific symbols (default: all active securities)
    - target_date: The date to fetch OHLCV for (default: yesterday)
    - batch_size: Number of symbols per batch (default: 50)

    **Returns:**
    - success: Whether the ingestion succeeded
    - symbols_processed: Number of symbols processed
    - records_inserted: Total records inserted
    - records_updated: Total records updated
    - symbols_failed: Number of failed symbols
    - errors: List of errors encountered
    - execution_time_ms: Execution time in milliseconds

    **Example Usage:**
    ```bash
    # Fetch yesterday's data for all securities (typical daily run)
    curl -X POST http://localhost:8001/api/v1/ingest/daily-ohlcv

    # Fetch specific date
    curl -X POST "http://localhost:8001/api/v1/ingest/daily-ohlcv?target_date=2024-12-11"

    # Fetch for specific symbols only
    curl -X POST "http://localhost:8001/api/v1/ingest/daily-ohlcv?symbols=RELIANCE&symbols=TCS"
    ```

    **Note:** This endpoint typically completes in 2-5 minutes for 2000+ securities.
    """
    from datetime import timedelta

    # Default to yesterday if no date provided
    if not target_date:
        target_date = (date.today() - timedelta(days=1))

    service = BatchHistoricalService(db)
    result = service.fetch_batch_historical_ohlcv(
        symbols=symbols,
        start_date=target_date,
        end_date=target_date,
        batch_size=batch_size
    )

    # Override source to 'upstox_daily' for ingestion logs
    # (BatchHistoricalService logs as 'upstox_historical' by default)

    if not result["success"] and result["symbols_processed"] == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Daily OHLCV ingestion failed for date {target_date}",
                "date": str(target_date),
                "errors": result["errors"]
            }
        )

    return {
        "message": f"Daily OHLCV ingestion completed for {target_date}",
        "success": result["success"],
        "date": str(target_date),
        "symbols_processed": result["symbols_processed"],
        "records_inserted": result["records_inserted"],
        "records_updated": result["records_updated"],
        "symbols_failed": result["symbols_failed"],
        "errors": result["errors"][:50],
        "execution_time_ms": result["execution_time_ms"]
    }
