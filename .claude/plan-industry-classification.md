# Implementation Plan: NSE Industry Classification & Index Constituents
## Phase 1.5: NSE Quote API Integration

**Date:** 2025-11-29
**Status:** Approved - Ready for Implementation
**Priority:** High (Prerequisite for screeners)
**Decision:** Option A (index_constituents table) confirmed

---

## Overview

Implement scraping of NSE Quote Equity API to extract:
1. **Industry Classification** (4-level hierarchy: Macro > Sector > Industry > Basic Industry)
2. **Index Constituents** (via `pdSectorIndAll` array - which indices a stock belongs to)

This replaces manual CSV uploads for index constituents and provides automated industry data updates.

---

## Data Source Analysis

### NSE Quote Equity API

**Endpoint:** `https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}`

**Authentication:** Cookie-based (requires Playwright browser automation)

**Key Data Extracted:**

1. **Industry Classification** (from `industryInfo` object):
   ```json
   "industryInfo": {
     "macro": "Energy",
     "sector": "Oil Gas & Consumable Fuels",
     "industry": "Petroleum Products",
     "basicIndustry": "Refineries & Marketing"
   }
   ```

2. **Index Membership** (from `metadata.pdSectorIndAll` array):
   ```json
   "metadata": {
     "pdSectorIndAll": [
       "NIFTY 50",
       "NIFTY 100",
       "NIFTY 200",
       "NIFTY 500",
       "NIFTY ENERGY",
       ...
     ]
   }
   ```

3. **Additional Metadata** (useful for future):
   - `info.isFNOSec` - F&O availability
   - `info.isSuspended` - Suspension status
   - `metadata.pdSectorPe` - Sector PE
   - `metadata.pdSymbolPe` - Stock PE

---

## Design Decisions

### 1. Database Schema

#### Option A: Create `index_constituents` Table (from Implementation-Plan.md)
```sql
CREATE TABLE index_constituents (
    id BIGSERIAL PRIMARY KEY,
    index_id INTEGER REFERENCES indices(id),
    symbol VARCHAR(50) REFERENCES securities(symbol),
    effective_from DATE NOT NULL,
    effective_to DATE,
    weightage DECIMAL(6,4),  -- NULL until we find source for weightage
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Pros:**
- Historical tracking of index changes
- Supports weightage when data becomes available
- Normalized design

**Cons:**
- More complex to maintain
- Need to track effective dates

#### Option B: Store Index List in JSON Column on `industry_classification`
```sql
ALTER TABLE industry_classification
ADD COLUMN indices_list JSON;
-- Example: ["NIFTY 50", "NIFTY 100", "NIFTY ENERGY"]
```

**Pros:**
- Simpler implementation
- No need for effective dates (current snapshot only)
- Easy to query "is this stock in NIFTY 50?"

**Cons:**
- No historical tracking
- Can't track when stock entered/exited index
- No weightage support

**DECISION:** Option A (index_constituents table) - **APPROVED**
- Even without weightage, table structure is better for queries
- Can easily add weightage column later when source is found
- Historical tracking is valuable for backtesting screeners
- Confirmed by user on 2025-11-29

### 2. Ingestion Strategy

**Weekly Full Scrape:**
- Scrape ALL securities (~2500 symbols)
- Update industry classification
- Update index constituents (mark as current snapshot)
- Duration: ~35-40 minutes (1 second delay between requests)

**Rationale:**
- Industry classifications change infrequently (quarterly at most)
- Index constituents change quarterly (rebalancing dates)
- Weekly scrape ensures we catch changes within reasonable time
- Avoid daily scraping to minimize NSE server load

**Error Handling:**
- Cookie refresh: Max 3 attempts per session
- 403 Forbidden: Refresh cookies and retry
- 404 Not Found: Symbol may be delisted, log and skip
- Rate limiting: 1 second delay between requests (enforced)

### 3. Cookie Management with Playwright

**Implementation:**
```python
async def get_nse_cookies():
    """
    Launch headless browser
    Navigate to NSE homepage
    Wait for cookies to be set (detect _abck, nsit, nseappid cookies)
    Extract all cookies
    Return as dict for requests library
    """
```

**Cookie Lifecycle:**
- Cookies valid for ~30 minutes
- Refresh on 403 errors
- Browser session can be reused for entire scraping session
- Close browser after scraping complete

---

## Implementation Tasks

### Task 1: Create `index_constituents` Database Model

**File:** `backend/app/models/metadata.py`

Add `IndexConstituent` model:
```python
class IndexConstituent(Base):
    """
    Tracks which securities belong to which indices over time.

    Data Source: NSE Quote Equity API (metadata.pdSectorIndAll)

    Note: Weightage is NULL until source is identified.
    Historical tracking via effective_from/effective_to dates.
    """
    __tablename__ = 'index_constituents'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    index_id = Column(Integer, ForeignKey('indices.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True)
    effective_from = Column(Date, nullable=False, index=True,
                           comment="Date this constituent relationship became effective")
    effective_to = Column(Date, nullable=True, index=True,
                         comment="Date this constituent relationship ended (NULL = current)")
    weightage = Column(Decimal(6, 4), nullable=True,
                      comment="Index weightage in % (NULL until source identified)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Composite unique constraint: symbol can't be in same index twice for overlapping dates
    __table_args__ = (
        Index('idx_index_constituents_active', 'index_id', 'symbol', 'effective_from',
              postgresql_where=(effective_to == None)),
        Index('idx_index_constituents_symbol_date', 'symbol', 'effective_from'),
    )
```

**Alembic Migration:** Create migration to add `index_constituents` table

### Task 2: Update `industry_classification` Model

**File:** `backend/app/models/metadata.py`

Add optional fields for enrichment (can be added later):
- No changes needed initially
- Keep current 4-level classification fields

### Task 3: Create NSE Industry Scraper Service

**File:** `backend/app/services/nse/industry_scraper.py`

```python
import asyncio
from playwright.async_api import async_playwright
import requests
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

async def get_nse_cookies() -> Dict[str, str]:
    """
    Launch Playwright browser and extract NSE cookies.

    Returns:
        Dict of cookie name -> value for requests library
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Navigate to NSE homepage to get cookies
        await page.goto('https://www.nseindia.com', wait_until='networkidle')

        # Wait for essential cookies to be set
        cookies = await context.cookies()
        await browser.close()

        # Convert to requests library format
        return {cookie['name']: cookie['value'] for cookie in cookies}


def fetch_industry_and_indices(symbol: str, cookies: Dict[str, str]) -> Optional[Dict]:
    """
    Fetch industry classification and index memberships for a symbol.

    Args:
        symbol: Security symbol (e.g., "RELIANCE")
        cookies: NSE session cookies

    Returns:
        Dict with:
        - industry_info: {macro, sector, industry, basic_industry}
        - indices: List of index names
        - metadata: Additional fields for future use

    Raises:
        CookieExpiredError: If 403 response (need to refresh cookies)
    """
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}'
    }

    response = requests.get(url, headers=headers, cookies=cookies, timeout=30)

    if response.status_code == 403:
        raise CookieExpiredError("NSE cookies expired, refresh needed")

    if response.status_code == 404:
        return None  # Symbol not found or delisted

    response.raise_for_status()
    data = response.json()

    return {
        'symbol': symbol,
        'industry_info': data.get('industryInfo', {}),
        'indices': data.get('metadata', {}).get('pdSectorIndAll', []),
        'is_fno': data.get('info', {}).get('isFNOSec', False),
        'is_suspended': data.get('info', {}).get('isSuspended', False)
    }


async def scrape_all_industries(db: Session) -> Dict:
    """
    Main orchestrator: Scrape industry and index data for all securities.

    Returns:
        Summary dict with statistics
    """
    # Implementation details...
```

**Error Handling:**
- Custom exception: `CookieExpiredError` for 403 responses
- Retry logic: Max 3 cookie refreshes per session
- Rate limiting: 1 second delay enforced between requests

### Task 4: Create Pydantic Schemas

**File:** `backend/app/schemas/industry.py` (new file)

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class IndustryClassificationBase(BaseModel):
    symbol: str
    macro: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    basic_industry: Optional[str] = None

class IndustryClassificationResponse(IndustryClassificationBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class IndexConstituentCreate(BaseModel):
    symbol: str
    index_name: str  # Will be resolved to index_id
    effective_from: date
    weightage: Optional[Decimal] = None

class IndexConstituentResponse(BaseModel):
    id: int
    index_id: int
    symbol: str
    effective_from: date
    effective_to: Optional[date]
    weightage: Optional[Decimal]

    class Config:
        from_attributes = True


class IndustryScrapingResponse(BaseModel):
    success: bool
    symbols_processed: int
    industries_updated: int
    index_constituents_updated: int
    failed_symbols: List[str]
    cookie_refreshes: int
    execution_time_seconds: float
```

### Task 5: Create FastAPI Endpoints

**File:** `backend/app/api/v1/ingest.py`

Add endpoint:
```python
@router.post("/industry-classification")
async def ingest_industry_classification(
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to scrape (defaults to all)"),
    db: Session = Depends(get_db)
):
    """
    Scrape industry classification and index memberships from NSE Quote API.

    This endpoint:
    1. Scrapes NSE Quote Equity API for industry data
    2. Updates industry_classification table
    3. Updates index_constituents table based on pdSectorIndAll
    4. Handles cookie management automatically (Playwright)

    **Process:**
    - Uses Playwright to obtain NSE session cookies
    - Scrapes ~2500 symbols (if symbols not specified)
    - Rate limited to 1 request/second
    - Auto-refreshes cookies on 403 errors
    - Duration: ~35-40 minutes for full scrape

    **Query Parameters:**
    - symbols: Optional list of symbols (defaults to all active securities)

    **Returns:**
    - Statistics: symbols_processed, industries_updated, index_constituents_updated
    - Errors: List of failed symbols
    - Metadata: cookie_refreshes, execution_time
    """
    result = await scrape_all_industries(db=db, symbols=symbols)

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Industry classification scraping failed",
                "errors": result.get("errors", []),
                "stats": result.get("stats", {})
            }
        )

    return {
        "message": "Industry classification scraping completed",
        "success": True,
        "symbols_processed": result["symbols_processed"],
        "industries_updated": result["industries_updated"],
        "index_constituents_updated": result["index_constituents_updated"],
        "failed_symbols": result["failed_symbols"],
        "cookie_refreshes": result["cookie_refreshes"],
        "execution_time_seconds": result["execution_time_seconds"]
    }
```

### Task 6: Implement Index Constituent Logic

**Algorithm:**
1. For each symbol, extract `pdSectorIndAll` array
2. For each index name in array:
   - Look up `index_id` from `indices` table (create if doesn't exist)
   - Check if constituent relationship already exists with `effective_to = NULL`
   - If not exists: INSERT new record with `effective_from = scrape_date`
   - If exists: No action (relationship is current)
3. For constituents NOT in current scrape but exist in DB with `effective_to = NULL`:
   - Set `effective_to = scrape_date - 1` (symbol exited index)

**Edge Cases:**
- Index name not in `indices` table: Auto-create with default values
- Symbol in index, then removed, then re-added: Create new record (don't reuse old one)
- Duplicate entries: Prevented by unique constraint on (index_id, symbol, effective_from) where effective_to IS NULL

### Task 7: Update Documentation

**File:** `.claude/file-formats.md`

Update Section 6 (Index Constituents) and Section 7 (Industry Classification):
- Remove manual CSV upload approach
- Document NSE Quote API as primary source
- Note: weightage field is NULL (awaiting source identification)
- Add `pdSectorIndAll` JSON structure
- Add example API response

**File:** `.claude/Implementation-Plan.md`

Update Phase 1.5 tasks to reflect new approach

---

## Testing Strategy

### Unit Tests

1. **Cookie Extraction Test:**
   - Launch Playwright
   - Verify cookies contain `_abck`, `nsit`, `nseappid`
   - Verify cookies are valid for API requests

2. **Single Symbol Fetch Test:**
   - Fetch "RELIANCE" data
   - Verify industry_info structure
   - Verify pdSectorIndAll array present
   - Verify at least "NIFTY 50" in indices

3. **403 Handling Test:**
   - Mock expired cookies
   - Verify cookie refresh triggered
   - Verify retry succeeds

4. **Index Constituent Logic Test:**
   - Scrape 5 symbols
   - Verify index_constituents records created
   - Re-scrape same symbols
   - Verify no duplicate records
   - Manually remove symbol from pdSectorIndAll
   - Re-scrape
   - Verify effective_to set correctly

### Integration Tests

1. **Full Scrape Test (100 symbols):**
   - Scrape 100 random symbols
   - Verify industry_classification updated
   - Verify index_constituents updated
   - Verify statistics are accurate

2. **Error Recovery Test:**
   - Simulate network errors mid-scrape
   - Verify scraper continues with remaining symbols
   - Verify failed symbols are logged

---

## Success Criteria

- [ ] `index_constituents` table created with proper constraints
- [ ] NSE cookie extraction working reliably
- [ ] Industry classification scraper fetches and parses NSE Quote API
- [ ] Index constituents logic correctly handles entry/exit from indices
- [ ] FastAPI endpoint `/api/v1/ingest/industry-classification` functional
- [ ] Rate limiting (1 req/sec) enforced
- [ ] Cookie refresh mechanism working
- [ ] Full scrape of ~2500 symbols completes without major errors
- [ ] Documentation updated in file-formats.md

---

## Timeline Estimate

- **Task 1 (Model + Migration):** 1 hour
- **Task 2 (Scraper Service):** 4 hours
- **Task 3 (Schemas):** 1 hour
- **Task 4 (API Endpoint):** 2 hours
- **Task 5 (Index Logic):** 3 hours
- **Task 6 (Documentation):** 1 hour
- **Task 7 (Testing):** 3 hours

**Total:** ~15 hours (2 working days)

---

## Questions for User

1. **Weightage Source:** Do you have any leads on where to get index weightage data? NSE website doesn't provide this in Quote API.
   - Possible sources: NSE Indices website downloads, Bloomberg, third-party data providers
   - For now: Keep weightage column NULL

2. **Scraping Frequency:** Confirm weekly scraping is acceptable?
   - Quarterly might be sufficient for index rebalancing
   - But industry classifications can change anytime

3. **Historical Backfill:** Should we backfill historical index constituents?
   - Would require manual CSVs for historical Nifty 50 constituents
   - Or accept that we only have data going forward from implementation date

---

## Dependencies

- **Python Packages:**
  - `playwright` - Already in requirements.txt for NSE scraping
  - `requests` - Already available
  - `asyncio` - Built-in

- **Database:**
  - `indices` table must exist (already exists)
  - `securities` table must exist (already exists)
  - Foreign key relationships will be enforced

---

## Next Steps After Approval

1. Create `index_constituents` model and migration
2. Implement cookie extraction with Playwright
3. Implement NSE Quote API parser
4. Implement index constituent logic
5. Create API endpoint
6. Test with sample symbols (RELIANCE, TCS, INFY, HDFC, ICICIBANK)
7. Run full scrape on all securities
8. Update documentation
