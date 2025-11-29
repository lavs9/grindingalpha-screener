"""
NSE Industry Classification & Index Constituent Service.

Handles fetching industry classification and index membership data from NSE Quote Equity API.
Requires Playwright for cookie-based authentication.

Data Source: https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}
"""
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import httpx

from app.models.metadata import IndustryClassification, IndexConstituent
from app.models.security import Security, Index


# NSE Quote Equity API
NSE_QUOTE_API = "https://www.nseindia.com/api/quote-equity"
NSE_HOMEPAGE = "https://www.nseindia.com"

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3


class IndustryServiceError(Exception):
    """Raised when industry service operations fail."""
    pass


class NSECookieManager:
    """
    Manages NSE cookie authentication using Playwright.

    NSE Quote API requires cookies (_abck, nsit, nseappid) that are set via JavaScript.
    This manager uses a headless browser to obtain and refresh cookies.
    """

    def __init__(self):
        self.cookies: Dict[str, str] = {}
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.cookie_expiry: Optional[float] = None

    async def initialize(self):
        """Initialize Playwright browser and fetch initial cookies."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        await self._refresh_cookies()

    async def _refresh_cookies(self):
        """Navigate to NSE homepage and extract cookies."""
        if not self.context:
            raise IndustryServiceError("Browser context not initialized")

        page = await self.context.new_page()
        try:
            # Navigate to NSE homepage and wait for cookies to be set
            await page.goto(NSE_HOMEPAGE, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait 3s for JavaScript to set cookies

            # Extract cookies
            cookies = await self.context.cookies()
            self.cookies = {
                cookie['name']: cookie['value']
                for cookie in cookies
                if cookie['name'] in ('_abck', 'nsit', 'nseappid', 'ak_bmsc', 'bm_sv')
            }

            # Set cookie expiry (refresh after 20 minutes)
            self.cookie_expiry = time.time() + (20 * 60)

        finally:
            await page.close()

    async def get_cookies(self) -> Dict[str, str]:
        """Get current cookies, refreshing if expired."""
        if not self.cookies or (self.cookie_expiry and time.time() > self.cookie_expiry):
            await self._refresh_cookies()
        return self.cookies

    async def close(self):
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


async def fetch_quote_data(symbol: str, cookie_manager: NSECookieManager) -> Dict:
    """
    Fetch NSE Quote Equity data for a single symbol.

    Args:
        symbol: NSE symbol (e.g., "RELIANCE")
        cookie_manager: Initialized NSECookieManager instance

    Returns:
        Dict with quote data or error info
    """
    result = {
        "success": False,
        "symbol": symbol,
        "data": None,
        "error": None
    }

    for attempt in range(MAX_RETRIES):
        try:
            cookies = await cookie_manager.get_cookies()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    NSE_QUOTE_API,
                    params={"symbol": symbol},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": NSE_HOMEPAGE
                    },
                    cookies=cookies
                )

                if response.status_code == 403:
                    # Cookie expired, refresh and retry
                    await cookie_manager._refresh_cookies()
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(2)
                        continue
                    result["error"] = "Authentication failed after retries"
                    return result

                response.raise_for_status()
                result["data"] = response.json()
                result["success"] = True
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                result["error"] = f"Symbol not found: {symbol}"
                return result
            result["error"] = f"HTTP error: {e}"
        except Exception as e:
            result["error"] = f"Request failed: {str(e)}"

        # Rate limiting between retries
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))

    return result


def parse_industry_classification(quote_data: Dict, symbol: str) -> Optional[Dict]:
    """
    Parse industry classification from NSE Quote data.

    Args:
        quote_data: NSE Quote API response
        symbol: NSE symbol

    Returns:
        Dict with industry classification fields or None if not available
    """
    industry_info = quote_data.get("industryInfo")
    if not industry_info:
        return None

    return {
        "symbol": symbol,
        "macro": industry_info.get("macro"),
        "sector": industry_info.get("sector"),
        "industry": industry_info.get("industry"),
        "basic_industry": industry_info.get("basicIndustry")
    }


def parse_index_constituents(quote_data: Dict, symbol: str, scrape_date: date) -> List[str]:
    """
    Parse index membership from NSE Quote data.

    Args:
        quote_data: NSE Quote API response
        symbol: NSE symbol
        scrape_date: Date of this scrape (for effective_from tracking)

    Returns:
        List of index names this symbol belongs to
    """
    metadata = quote_data.get("metadata", {})
    index_list = metadata.get("pdSectorIndAll", [])

    # Filter out empty strings and None values
    return [idx for idx in index_list if idx]


async def scrape_all_securities(
    db: Session,
    limit: Optional[int] = None,
    symbols: Optional[List[str]] = None
) -> Dict:
    """
    Scrape industry classification and index constituents for all securities.

    Args:
        db: SQLAlchemy database session
        limit: Optional limit for testing (scrape first N symbols)
        symbols: Optional list of specific symbols to scrape

    Returns:
        Dict with scraping statistics and results
    """
    result = {
        "success": False,
        "total_symbols": 0,
        "symbols_processed": 0,
        "symbols_failed": 0,
        "industry_records": 0,
        "index_constituent_records": 0,
        "errors": [],
        "duration_seconds": 0
    }

    start_time = time.time()
    cookie_manager = NSECookieManager()

    try:
        # Initialize Playwright browser
        await cookie_manager.initialize()

        # Get list of symbols to scrape
        if symbols:
            symbol_list = symbols
        else:
            query = db.query(Security.symbol).filter(Security.is_active == True)
            if limit:
                query = query.limit(limit)
            symbol_list = [row.symbol for row in query.all()]

        result["total_symbols"] = len(symbol_list)
        scrape_date = date.today()

        # Track all index names seen (for bulk insert into indices table)
        all_index_names = set()

        # Scrape each symbol
        for i, symbol in enumerate(symbol_list, 1):
            try:
                # Rate limiting
                if i > 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY)

                # Fetch quote data
                quote_result = await fetch_quote_data(symbol, cookie_manager)

                if not quote_result["success"]:
                    result["symbols_failed"] += 1
                    result["errors"].append(f"{symbol}: {quote_result['error']}")
                    continue

                quote_data = quote_result["data"]

                # Parse and store industry classification
                industry_data = parse_industry_classification(quote_data, symbol)
                if industry_data:
                    upsert_industry_classification(db, industry_data)
                    result["industry_records"] += 1

                # Parse index constituents
                index_names = parse_index_constituents(quote_data, symbol, scrape_date)
                all_index_names.update(index_names)

                result["symbols_processed"] += 1

                # Log progress every 50 symbols
                if i % 50 == 0:
                    print(f"Progress: {i}/{result['total_symbols']} symbols scraped")

            except Exception as e:
                result["symbols_failed"] += 1
                result["errors"].append(f"{symbol}: {str(e)}")

        # Ensure all indices exist in indices table
        ensure_indices_exist(db, list(all_index_names))

        # Now process index constituents for all symbols
        result["index_constituent_records"] = await process_index_constituents(
            db, symbol_list, cookie_manager, scrape_date
        )

        db.commit()
        result["success"] = True

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Fatal error: {str(e)}")
        result["success"] = False

    finally:
        await cookie_manager.close()
        result["duration_seconds"] = int(time.time() - start_time)

    return result


async def process_index_constituents(
    db: Session,
    symbol_list: List[str],
    cookie_manager: NSECookieManager,
    scrape_date: date
) -> int:
    """
    Process index constituents for all symbols and track entry/exit.

    This function:
    1. Fetches current index membership for each symbol
    2. Compares with existing database records
    3. Inserts new constituents (effective_from = scrape_date)
    4. Marks removed constituents (effective_to = scrape_date - 1)

    Args:
        db: Database session
        symbol_list: List of symbols to process
        cookie_manager: Initialized NSECookieManager
        scrape_date: Date of this scrape

    Returns:
        Number of index constituent records inserted/updated
    """
    records_affected = 0

    # Build map of symbol -> current index IDs from API
    symbol_current_indices: Dict[str, set] = {}

    for symbol in symbol_list:
        try:
            # Fetch quote data (may have been cached in previous step, but re-fetch for safety)
            quote_result = await fetch_quote_data(symbol, cookie_manager)
            if not quote_result["success"]:
                continue

            index_names = parse_index_constituents(quote_result["data"], symbol, scrape_date)

            # Resolve index names to index IDs
            if index_names:
                index_ids = db.query(Index.id).filter(Index.index_name.in_(index_names)).all()
                symbol_current_indices[symbol] = {idx.id for idx in index_ids}

            await asyncio.sleep(RATE_LIMIT_DELAY)

        except Exception:
            continue

    # For each symbol, compare current vs database state
    for symbol, current_index_ids in symbol_current_indices.items():
        # Get existing active constituents for this symbol
        existing_records = db.query(IndexConstituent).filter(
            and_(
                IndexConstituent.symbol == symbol,
                IndexConstituent.effective_to.is_(None)
            )
        ).all()

        existing_index_ids = {rec.index_id for rec in existing_records}

        # Find new indices (in current but not in existing)
        new_index_ids = current_index_ids - existing_index_ids

        # Find removed indices (in existing but not in current)
        removed_index_ids = existing_index_ids - current_index_ids

        # Insert new constituents
        for index_id in new_index_ids:
            new_constituent = IndexConstituent(
                index_id=index_id,
                symbol=symbol,
                effective_from=scrape_date,
                effective_to=None,
                weightage=None
            )
            db.add(new_constituent)
            records_affected += 1

        # Mark removed constituents
        for index_id in removed_index_ids:
            # Find the active record and set effective_to
            record = next((r for r in existing_records if r.index_id == index_id), None)
            if record:
                record.effective_to = scrape_date - timedelta(days=1)
                records_affected += 1

    return records_affected


def upsert_industry_classification(db: Session, industry_data: Dict):
    """
    Insert or update industry classification for a symbol.

    Uses UPSERT pattern (symbol is unique).

    Args:
        db: Database session
        industry_data: Dict with symbol, macro, sector, industry, basic_industry
    """
    existing = db.query(IndustryClassification).filter(
        IndustryClassification.symbol == industry_data["symbol"]
    ).first()

    if existing:
        # Update existing record
        existing.macro = industry_data.get("macro")
        existing.sector = industry_data.get("sector")
        existing.industry = industry_data.get("industry")
        existing.basic_industry = industry_data.get("basic_industry")
    else:
        # Insert new record
        new_record = IndustryClassification(**industry_data)
        db.add(new_record)


def ensure_indices_exist(db: Session, index_names: List[str]):
    """
    Ensure all index names exist in indices table.

    Inserts missing indices with minimal data (name only).

    Args:
        db: Database session
        index_names: List of index names from NSE Quote API
    """
    if not index_names:
        return

    # Get existing index names
    existing = db.query(Index.index_name).filter(Index.index_name.in_(index_names)).all()
    existing_names = {row.name for row in existing}

    # Insert missing indices
    missing_names = set(index_names) - existing_names
    for name in missing_names:
        new_index = Index(
            index_name=name,
            symbol=name,  # Use same as index_name for now
            is_active=True
        )
        db.add(new_index)

    db.flush()  # Flush to get index IDs


def get_industry_by_symbol(db: Session, symbol: str) -> Optional[Dict]:
    """
    Get industry classification for a single symbol.

    Args:
        db: Database session
        symbol: NSE symbol

    Returns:
        Dict with industry classification or None
    """
    record = db.query(IndustryClassification).filter(
        IndustryClassification.symbol == symbol
    ).first()

    if not record:
        return None

    return {
        "symbol": record.symbol,
        "macro": record.macro,
        "sector": record.sector,
        "industry": record.industry,
        "basic_industry": record.basic_industry
    }


def get_index_constituents(
    db: Session,
    index_name: str,
    as_of_date: Optional[date] = None
) -> List[str]:
    """
    Get all symbols that are constituents of an index.

    Args:
        db: Database session
        index_name: Index name (e.g., "NIFTY 50")
        as_of_date: Optional historical date (defaults to current)

    Returns:
        List of symbol strings
    """
    # Get index ID
    index = db.query(Index).filter(Index.index_name == index_name).first()
    if not index:
        return []

    query_date = as_of_date if as_of_date else date.today()

    # Query constituents active on query_date
    records = db.query(IndexConstituent).filter(
        and_(
            IndexConstituent.index_id == index.id,
            IndexConstituent.effective_from <= query_date,
            or_(
                IndexConstituent.effective_to.is_(None),
                IndexConstituent.effective_to >= query_date
            )
        )
    ).all()

    return [record.symbol for record in records]
