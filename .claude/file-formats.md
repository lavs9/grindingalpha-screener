# Data Source File Formats Reference
## Indian Stock Market Screener Platform

**Version:** 1.0
**Date:** November 16, 2025
**Purpose:** Canonical reference for all external data source formats

---

## Important: Always Reference This Document

**RULE:** Before creating any data model, parser, or ingestion logic, **ALWAYS** check this document first for the exact file format specification.

**When to Update:**
- External data source changes format (NSE, Upstox)
- New data source added
- Field meanings clarified
- Sample files added

**Change Log Format:**
```
- YYYY-MM-DD: Description of change
```

---

## 1. NSE Listed Securities

### 1.1 NSE Equity List (EQUITY_L.csv)

**Source URL:** https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv

**Sample File Location:** `.claude/samples/EQUITY_L_sample.csv`

**Format:** CSV (comma-separated), UTF-8 encoding

**Header Row:** YES (first row contains column names)

**Update Frequency:** Daily (available after market close)

**Columns:**

| Column Name | Data Type | Required | Constraints | Description | Example Value |
|------------|-----------|----------|-------------|-------------|---------------|
| SYMBOL | String(50) | Yes | Alphanumeric, `&`, `-` allowed | NSE trading symbol | RELIANCE |
| NAME OF COMPANY | String(255) | Yes | - | Full registered company name | Reliance Industries Limited |
| SERIES | String(10) | Yes | - | Trading series (EQ, BE, etc.) | EQ |
| DATE OF LISTING | Date | Yes | Format: DD-MMM-YYYY | Date when security was first listed | 29-NOV-1977 |
| PAID UP VALUE | Decimal(15,2) | No | Can be empty | Total paid-up capital in INR | 6339299200.00 |
| MARKET LOT | Integer | Yes | Must be > 0 | Minimum lot size for trading | 1 |
| ISIN NUMBER | String(12) | Yes | Must start with 'IN', exactly 12 chars | International Securities ID | INE002A01018 |
| FACE VALUE | Decimal(10,2) | Yes | Must be > 0 | Face value per share in INR | 10.00 |

**Validation Rules:**
- SYMBOL: Regex `^[A-Z0-9&-]+$` (uppercase alphanumeric with `&` or `-`)
- ISIN: Regex `^IN[A-Z0-9]{10}$` (starts with IN, 12 characters total)
- DATE OF LISTING: Cannot be future date
- MARKET LOT: Cannot be 0 or negative
- PAID UP VALUE: May be empty for some securities (treat as NULL)

**Parsing Notes:**
- Some fields may have leading/trailing whitespace → **ALWAYS TRIM**
- PAID UP VALUE may be completely empty (not "0.00") for certain securities
- DATE OF LISTING format is consistent but parse with `strptime('%d-%b-%Y')` to handle month names

**Known Issues:**
- Some company names contain commas → Parser must handle quoted CSV fields correctly
- Special characters in company names (Ltd., &, -, etc.) → Store as-is, don't sanitize

**Last Verified:** 2025-01-16
**Last Format Change:** None (stable format for 5+ years)

**Change Log:**
- 2025-01-16: Initial documentation

---

### 1.2 NSE ETF List (eq_etfseclist.csv)

**Source URL:** https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv

**Sample File Location:** `.claude/samples/eq_etfseclist_sample.csv`

**Format:** CSV (comma-separated), UTF-8 encoding

**Header Row:** YES

**Update Frequency:** Daily

**Columns:**

| Column Name | Data Type | Required | Description | Example Value |
|------------|-----------|----------|-------------|---------------|
| SYMBOL | String(50) | Yes | ETF trading symbol | GOLDBEES |
| Underlying | String(255) | Yes | ETF name | Nifty50 |
| SecurityName | String(30) | Yes |  | NIPINDETFNIFTYBEES |
| DateofListing | Date | Yes | Listing date (DD-MMM-YY) | 08-Jan-02 |
| MarketLot | Integer | Yes | Lot size | 1 |
| ISINNumber | String(12) | Yes | ISIN code | INF204KA1Q27 |
| FaceValue | Decimal(10,2) | Yes | Face value per unit | 10.00 |

**Validation Rules:** Same as EQUITY_L.csv

**Parsing Notes:**
- ETF ISINs may start with "INF" (funds) instead of "IN" (equities), just store ISIN
- Otherwise identical format to EQUITY_L.csv

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 2. NSE Market Cap Data

### 2.1 Market Cap Archive (PR{DDMMYY}.zip)

**Source URL Pattern:** `https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip`

**Date Format in URL:** DDMMYY (day, month, year - 2 digits each)

**Example URL:** https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR160125.zip (for 16-Jan-2025)

**Sample File Location:** `.claude/samples/PR160125_sample.zip` (contains MCAP16012025.csv)

**Format:** ZIP archive containing a single CSV file

**Inner File Naming:** `MCAP{DDMMYYYY}.csv` (note: 4-digit year inside, 2-digit in ZIP name)

**Update Frequency:** Daily (available next day after market close)

**Availability:** May have gaps; files missing for some dates (weekends, holidays, technical issues)

**CSV Format:** Comma-separated, UTF-8 encoding

**Header Row:** YES

**Columns:**

| Column Name | Data Type | Required | Description | Example Value |
|------------|-----------|----------|-------------|---------------|
| Trade Date | Date | Yes | Trading date (DD-MMM-YYYY) | 16-JAN-2025 |
| Symbol | String(50) | Yes | Security symbol | RELIANCE |
| Series | String(10) | Yes | Trading series | EQ |
| Security Name | String(255) | Yes | Company name | Reliance Industries Limited |
| Category | String(50) | No | Security category | X (large cap) / Y (mid cap) / etc. |
| Last Trade Date | Date | No | Last trading date if suspended | 16-JAN-2025 |
| Face Value(Rs.) | Decimal(10,2) | Yes | Face value per share | 10.00 |
| Issue Size | BigInt | Yes | Total issued shares | 6339299200 |
| Close Price/Paid up value(Rs.) | Decimal(15,2) | Yes | Closing price for the date | 1285.50 |
| Market Cap(Rs.) | Decimal(20,2) | **Yes** | **PRIMARY METRIC** Market capitalization in INR | 8150539475520.00 |

**Validation Rules:**
- Trade Date: Must match the date in file name
- Symbol: Must exist in `securities` table (warn if not, but still store)
- Market Cap: Must be > 0
- Issue Size: Must be > 0

**Parsing Workflow:**
1. Download ZIP file from NSE archives
2. Extract to temporary directory
3. Locate `MCAP{DDMMYYYY}.csv` file inside
4. Parse CSV
5. Validate Trade Date matches expected date
6. Filter: Only insert symbols that exist in `securities` table
7. Clean up temporary files

**Error Handling:**
- 404 Not Found → File doesn't exist for this date (gap in NSE data)
  - Action: Log warning, skip date, continue
  - Do NOT retry indefinitely
- Corrupted ZIP → Log error, alert admin
- Missing CSV inside ZIP → Log error, alert admin

**Historical Backfill Notes:**
- Start from 5 years ago (or 1 year minimum)
- Stop on first 404 (don't keep going backwards indefinitely)
- Respect weekends/holidays (use `market_holidays` table to skip)

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 3. NSE Bulk & Block Deals

### 3.1 Bulk Deals (bulk.csv)

**Source URL:** https://nsearchives.nseindia.com/content/equities/bulk.csv

**Sample File Location:** `.claude/samples/bulk_sample.csv`

**Format:** CSV (comma-separated), UTF-8 encoding

**Header Row:** YES

**Update Frequency:** Daily (contains deals from previous trading day)

**Columns:**

| Column Name | Data Type | Required | Description | Example Value |
|------------|-----------|----------|-------------|---------------|
| Date | Date | Yes | Deal date (DD-MMM-YYYY) | 16-JAN-2025 |
| Symbol | String(50) | Yes | Security symbol | RELIANCE |
| Security Name | String(255) | Yes | Company name | Reliance Industries Limited |
| Client Name | String(255) | Yes | Name of entity executing deal | XYZ MUTUAL FUND |
| Buy/Sell | String(10) | Yes | BUY or SELL | BUY |
| Quantity Traded | BigInt | Yes | Number of shares | 5000000 |
| Trade Price/Wght. Avg. Price | Decimal(15,2) | Yes | Average price per share | 1285.50 |
| Remarks | Text | No | Additional notes (if any) | - |

**Validation Rules:**
- Symbol: Should exist in `securities` table (warn if not, but still store)
- Deal Type: Must be exactly "BUY" or "SELL"
- Quantity: Must be > 0
- Trade Price: Must be > 0
- If empty file, record will be of format ```NO RECORDS,,,,,,```, ignore and send message as no records found

**Parsing Notes:**
- Client Name may contain commas (e.g., "MUTUAL FUND, LIMITED") → Handle quoted CSV
- Multiple deals for same symbol/date are common → Each is separate row

**Business Logic:**
- Bulk deals = significant volume (>0.5% of equity) traded by single client
- Used as institutional interest signal in screeners

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

### 3.2 Block Deals (block.csv)

**Source URL:** https://nsearchives.nseindia.com/content/equities/block.csv

**Sample File Location:** `.claude/samples/block_sample.csv`

**Format:** Identical to bulk.csv (same columns, same structure)

**Difference from Bulk Deals:**
- Block deals = large pre-negotiated trades executed outside normal market
- Typically larger size than bulk deals
- Different regulatory implications

**Columns:** Same as bulk deals (see 3.1)

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 4. NSE Surveillance Measures

### 4.1 Surveillance Actions (REG1_IND{DDMMYY}.csv)

**Source URL Pattern:** `https://nsearchives.nseindia.com/content/cm/REG1_IND{DDMMYY}.csv`

**Date Format in URL:** DDMMYY (2-digit day, month, year)

**Example URL:** https://nsearchives.nseindia.com/content/cm/REG1_IND160125.csv (for 16-Jan-2025)

**Sample File Location:** `.claude/samples/REG1_IND160125_sample.csv`

**Format:** CSV (comma-separated), UTF-8 encoding

**Header Row:** YES

**Update Frequency:** Daily

**Columns:**

| Column Name | Data Type | Required | Description | Example Value |
|------------|-----------|----------|-------------|---------------|
| Symbol | String(50) | Yes | Security symbol | XYZ |
| Security Name | String(255) | Yes | Company name | XYZ Limited |
| Surveillance Action | String(50) | Yes | Type of action (ASM, GSM, etc.) | ASM |
| Date | Date | Yes | Action effective date | 16-JAN-2025 |
| Reason | Text | No | Reason for surveillance | Price volatility |

**Surveillance Action Codes:**
- **ASM** (Additional Surveillance Measure): Price/volume abnormalities
- **GSM** (Graded Surveillance Measure): More severe restrictions
- Others: To be documented as encountered

**Validation Rules:**
- Symbol: Should exist in `securities` table
- Surveillance Action: Non-empty string

**Business Logic:**
- Securities under surveillance are **EXCLUDED** from all screeners
- Store is_active flag (toggle when surveillance lifted)

**Parsing Notes:**
- Some securities may have multiple surveillance actions simultaneously
- Action may be lifted in later CSV (not present = lifted)

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 5. Upstox API Responses

### 5.1 Historical Candle Data

**API Endpoint:** `/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}`

**Documentation:** https://upstox.com/developer/api-documentation/v3/get-historical-candle-data

**Sample Response Location:** `.claude/samples/upstox_historical_candle_sample.json`

**Authentication:** Bearer token in header

**Request Parameters:**
- `instrument_key`: Format `NSE_EQ|{ISIN}` (equities/ETFs) or `NSE_INDEX|{symbol}` (indices)
- `interval`: `1day` (we use daily candles)
- `to_date`: YYYY-MM-DD
- `from_date`: YYYY-MM-DD

**Response Format:** JSON

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "candles": [
      [
        "2025-01-16T09:15:00+05:30",  // [0] timestamp (ISO 8601 with timezone)
        1280.00,                       // [1] open
        1290.00,                       // [2] high
        1275.00,                       // [3] low
        1285.50,                       // [4] close
        5000000,                       // [5] volume (null for indices)
        0                              // [6] open interest (always 0 for equities)
      ],
      ...
    ]
  }
}
```

**Field Mapping to Database:**
| Array Index | Field | DB Column | Data Type | Notes |
|------------|-------|-----------|-----------|-------|
| [0] | timestamp | date | Date | Extract date part only, ignore time |
| [1] | open | open | Decimal(15,2) | Opening price |
| [2] | high | high | Decimal(15,2) | High price |
| [3] | low | low | Decimal(15,2) | Low price |
| [4] | close | close | Decimal(15,2) | Closing price |
| [5] | volume | volume | BigInt | NULL for indices |
| [6] | OI | - | - | Ignore (not relevant for equities) |

**Error Handling:**
- 404: Symbol not found in Upstox → Log error, skip symbol
- 429: Rate limit exceeded → Implement exponential backoff, retry
- 503: Service unavailable → Retry after 60 seconds, max 3 attempts

**Rate Limiting:**
- Upstox API limits: **TBD** (check SDK documentation)
- Implement throttling: Recommended 10 requests/second max
- Use batch requests where possible

**Data Quality Checks:**
- Verify: high >= low
- Verify: open and close between high and low
- Verify: volume >= 0 (or NULL for indices)
- Flag: >20% daily moves for review (possible data error or split/bonus)

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation
- TODO: Verify exact rate limits from Upstox support

---

### 5.2 Full Market Quote

**API Endpoint:** `/market-quote/quotes`

**Documentation:** https://upstox.com/developer/api-documentation/get-full-market-quote

**Sample Response Location:** `.claude/samples/upstox_full_market_quote_sample.json`

**Request Method:** GET with instrument_keys as query param

**Request Parameters:**
- `instrument_key`: Comma-separated list (max 500 symbols per request)
- Example: `NSE_EQ|INE002A01018,NSE_EQ|INE009A01021`

**Response Format:** JSON (nested structure)

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "NSE_EQ|INE002A01018": {
      "ohlc": {
        "open": 1280.00,
        "high": 1290.00,
        "low": 1275.00,
        "close": 1285.50
      },
      "volume": 5000000,
      "last_price": 1285.50,
      "prev_close": 1275.00,
      "change": 10.50,
      "change_percent": 0.82,
      "vwap": 1283.25,
      "upper_circuit_limit": 1402.50,
      "lower_circuit_limit": 1147.50,
      "52_week_high": 1500.00,
      "52_week_low": 1100.00,
      "depth": { ... }  // IGNORE - not storing depth data
    },
    ...
  }
}
```

**Field Mapping to Database:**
| JSON Path | DB Column | Data Type | Notes |
|-----------|-----------|-----------|-------|
| ohlc.open | open | Decimal(15,2) | Opening price |
| ohlc.high | high | Decimal(15,2) | High price |
| ohlc.low | low | Decimal(15,2) | Low price |
| ohlc.close | close | Decimal(15,2) | Closing price |
| volume | volume | BigInt | Trading volume |
| vwap | vwap | Decimal(15,2) | Volume-weighted avg price |
| prev_close | prev_close | Decimal(15,2) | Previous close |
| change_percent | change_pct | Decimal(8,4) | % change |
| upper_circuit_limit | upper_circuit | Decimal(15,2) | Upper circuit |
| lower_circuit_limit | lower_circuit | Decimal(15,2) | Lower circuit |
| 52_week_high | week_52_high | Decimal(15,2) | 52-week high |
| 52_week_low | week_52_low | Decimal(15,2) | 52-week low |
| depth | - | - | **IGNORE** (not storing) |

**Batching Strategy:**
- Fetch in batches of 500 symbols (Upstox max per request)
- Wait 100ms between batches to respect rate limits

**Error Handling:**
- Missing symbols in response → Log warning, continue
- Null values → Store as NULL in database

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

### 5.3 Market Holidays

**API Endpoint:** `/market-holidays`

**Documentation:** https://upstox.com/developer/api-documentation/get-market-holidays

**Sample Response Location:** `.claude/samples/upstox_market_holidays_sample.json`

**Request Parameters:** None (returns full year)

**Response Format:** JSON

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "NSE": [
      {
        "date": "2025-01-26",
        "description": "Republic Day",
        "type": "trading_holiday"
      },
      ...
    ]
  }
}
```

**Field Mapping to Database:**
| JSON Path | DB Column | Data Type |
|-----------|-----------|-----------|
| date | holiday_date | Date |
| description | holiday_name | String(255) |
| - | exchange | String(20) = 'NSE' |

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 6. Manual Upload Formats

### 6.1 Index Constituents CSV

**Source:** Manual download from Niftyindices.com

**Sample File Location:** `.claude/samples/nifty50_constituents_sample.csv`

**Format:** CSV (comma-separated), UTF-8 encoding

**Header Row:** YES (custom header, not from source)

**Update Frequency:** Monthly (manual update)

**Required Columns:**

| Column Name | Data Type | Required | Description | Example Value |
|------------|-----------|----------|-------------|---------------|
| symbol | String(50) | Yes | Security symbol | RELIANCE |
| company_name | String(255) | Yes | Company name | Reliance Industries Limited |
| industry | String(100) | No | Industry classification | Refineries |
| weightage | Decimal(6,4) | Yes | Weightage in index (%) | 10.2500 |

**Upload Process:**
1. Download constituents from Niftyindices.com
2. Convert to CSV with required columns (may require manual formatting)
3. Run `scripts/upload_index_constituents.py`:
   - Provide CSV file path
   - Provide index_name (e.g., "Nifty 50")
   - Provide effective_from date (usually month start)
4. Script POSTs to `/api/v1/ingest/index-constituents`

**Validation:**
- symbol: Must exist in `securities` table
- weightage: Sum across all constituents should be ~100% (allow ±1% tolerance)

**Historical Tracking:**
- When constituents change, set effective_to = (new effective_from - 1 day) for old records
- Insert new records with new effective_from

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 7. NSE Industry Classification (Scraped)

### 7.1 NSE Quote Equity API

**API Endpoint:** `https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}`

**Sample Response Location:** `.claude/samples/nse_quote_equity_sample.json`

**Authentication:** Requires session cookies (obtained via Playwright)

**Request Headers:**
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: application/json
Referer: https://www.nseindia.com/get-quotes/equity?symbol={SYMBOL}
Cookie: {session_cookies}
```

**Response Format:** JSON

**Response Structure:**
```json
{
  "info": {
    "symbol": "RELIANCE",
    "companyName": "Reliance Industries Limited",
    ...
  },
  "industryInfo": {
    "macro": "Energy",
    "sector": "Energy",
    "industry": "Refineries & Marketing",
    "basicIndustry": "Refineries"
  },
  ...
}
```

**Field Mapping to Database:**
| JSON Path | DB Column | Data Type |
|-----------|-----------|-----------|
| industryInfo.macro | macro | String(100) |
| industryInfo.sector | sector | String(100) |
| industryInfo.industry | industry | String(100) |
| industryInfo.basicIndustry | basic_industry | String(100) |

**Cookie Management:**
- Cookies expire after ~30 minutes
- On 403 error: Refresh browser session, extract new cookies, retry
- Max 3 cookie refresh attempts per scraping session

**Rate Limiting:**
- Sleep 1 second between requests to avoid blocking
- Process ~2000 symbols = ~35 minutes total

**Error Handling:**
- 403 Forbidden → Refresh cookies
- 404 Not Found → Symbol may be delisted, log and skip
- JSON parse error → Log and skip

**Last Verified:** 2025-01-16

**Change Log:**
- 2025-01-16: Initial documentation

---

## 8. Adding New Data Sources

**Process to Add New Format:**

1. **Research:**
   - Document source URL
   - Analyze format (CSV, JSON, XML, ZIP)
   - Identify all fields and their meanings
   - Determine update frequency

2. **Create Sample:**
   - Download sample file (5-10 rows for CSV, 2-3 records for JSON)
   - Anonymize if contains sensitive data
   - Save to `.claude/samples/`

3. **Document Format:**
   - Add new section to this file (file-formats.md)
   - Include: URL, format, columns/fields, validation rules, parsing notes
   - Add change log entry

4. **Update Code:**
   - Create parser in `services/`
   - Reference this documentation in code comments
   - Add validation checks based on documented rules

5. **Test:**
   - Test with sample file first
   - Test with live data
   - Verify validation rules work

6. **Review:**
   - PR review should verify code matches this documentation
   - Any discrepancies → Update documentation first, then code

---

## 9. Change Log Summary

**2025-01-16:**
- Initial documentation created
- All 10 data sources documented
- Sample file structure defined

**Future Updates:**
- Add Upstox rate limit specifics (pending confirmation)
- Add actual sample files as we collect them
- Document any format changes from NSE/Upstox

---

**Document Owner:** Development Team
**Last Updated:** 2025-01-16
**Next Review:** After first data ingestion test
