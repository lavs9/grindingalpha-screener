# Product Requirements Document (PRD)
## Indian Stock Market Screener Platform

**Version:** 1.0
**Date:** November 16, 2025
**Status:** Planning Phase

---

## 1. Executive Summary

### 1.1 Project Overview
A sophisticated stock market screening platform designed specifically for the Indian equity market (NSE). The system will aggregate data from multiple sources, calculate advanced technical metrics, and provide unique screeners to identify trading opportunities based on momentum, relative strength, and institutional activity patterns.

### 1.2 Project Vision
To build a comprehensive, automated stock screening platform that combines:
- Real-time and historical market data from NSE and Upstox
- Advanced technical analysis (VARS, ATR extensions, VCP patterns)
- Institutional activity tracking (bulk/block deals)
- Sector rotation analysis (RRG charts)
- Breadth metrics for market sentiment

### 1.3 Target Users
- **Primary**: Active traders focusing on momentum and swing trading strategies
- **Secondary**: Portfolio managers tracking sector rotations and relative strength
- **Tertiary**: Retail investors looking for high-probability setups

---

## 2. Project Objectives

### 2.1 Business Objectives
1. **Automated Data Pipeline**: Eliminate manual data collection with scheduled EOD updates (8-9 PM IST)
2. **Unique Screeners**: Implement 11 advanced screeners not commonly available for Indian markets
3. **Scalability**: Support universe of 2000+ listed securities with historical data
4. **Performance**: Sub-second query response for screener results
5. **Extensibility**: Easy addition of new metrics and screeners via modular architecture

### 2.2 Technical Objectives
1. Store 5+ years of historical OHLCV data for all NSE equities, ETFs, and indices
2. Calculate 30+ technical indicators daily for entire universe
3. Handle 10+ million time-series records efficiently
4. Provide RESTful API for data access
5. Enable workflow-based automation (n8n) for flexible pipeline management

---

## 3. Scope

### 3.1 In Scope - Phase 1 (Data Storage & Infrastructure)
- PostgreSQL database setup with comprehensive schema
- Integration with Upstox API for historical and daily OHLC data
- NSE data sources integration (listed securities, market cap, bulk/block deals, surveillance)
- Industry/sector classification via automated NSE scraping (Playwright)
- n8n workflow setup for scheduled data ingestion
- FastAPI endpoints for data ingestion and retrieval
- Docker containerization for local deployment
- Data validation and quality checks

### 3.2 In Scope - Phase 2 (Future)
- Daily calculation engine for 30+ technical metrics
- RRG chart implementation (first screener)
- Remaining 10 screeners
- Frontend dashboard
- Cloud deployment

### 3.3 Out of Scope
- Order placement/execution
- Portfolio management
- Real-time intraday data streaming
- Mobile applications
- Options chain analysis (postponed)
- User authentication (single-user system initially)

---

## 4. User Stories

### 4.1 Data Ingestion
**As a** system administrator
**I want** automated daily data fetch from NSE and Upstox
**So that** I have up-to-date market data without manual intervention

**Acceptance Criteria:**
- Data fetches trigger automatically at 8:30 PM IST on trading days
- Failed fetches retry with exponential backoff
- Email/webhook notifications on fetch failures
- Logs show fetch status and record counts

### 4.2 Historical Data Backfill
**As a** system administrator
**I want** to backfill 5 years of historical OHLCV data for all securities
**So that** screeners have sufficient data for calculations

**Acceptance Criteria:**
- Historical data fetched for all 2000+ securities from Upstox
- Handles securities with <5 years of data (recently listed)
- Validates data completeness and flags gaps
- Progress tracking for long-running backfills

### 4.3 Market Cap Tracking
**As a** trader
**I want** historical market cap data for all securities
**So that** I can filter by market cap and track cap changes over time

**Acceptance Criteria:**
- Market cap stored daily for all securities
- Historical backfill for 5 years (or 1 year minimum)
- Missing files handled gracefully (NSE archives may have gaps)
- Only store data for currently listed securities

### 4.4 Institutional Activity Monitoring
**As a** trader
**I want** bulk and block deal data
**So that** I can identify institutional interest as a trading catalyst

**Acceptance Criteria:**
- Daily bulk and block deals fetched from NSE
- Data linked to securities via symbol/ISIN
- Historical data imported separately (provided manually)
- Deals flagged in screener outputs

### 4.5 Industry/Sector Classification
**As a** trader
**I want** accurate industry and sector mappings for all securities
**So that** I can analyze sector rotation and leading industries

**Acceptance Criteria:**
- Weekly automated scrape from NSE (overcoming cookie challenges)
- Manual override capability for corrections
- Four-level classification: Macro > Sector > Industry > Basic Industry
- Missing classifications flagged for review

---

## 5. Functional Requirements

### 5.1 Data Sources & Frequency

#### 5.1.1 Listed Securities (Daily EOD)
**Source:** NSE Archives
**Endpoints:**
- Equities: `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv`
- ETFs: `https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv`

**Fields:**
- Symbol (primary identifier)
- ISIN (secondary identifier)
- Security Name
- Series (EQ, BE, etc.)
- Date of Listing
- Paid-up Value
- Market Lot
- Face Value

**Update Frequency:** Daily at 8:30 PM IST
**Historical Backfill:** Not required (current list only)

#### 5.1.2 Indices (One-time + Daily EOD)
**Source:** Upstox API (instrument type = INDEX)

**Fields:**
- Index Name
- Symbol
- Exchange (NSE_INDEX)

**Update Frequency:** Daily OHLCV updates; constituents monthly

#### 5.1.3 Market Cap Data (Daily EOD)
**Source:** NSE Archives (ZIP files)
**URL Pattern:** `https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip`
**Inner File Pattern:** `MCAP{DDMMYYYY}.csv`

**Fields to Store:**
- Trade Date (validation field)
- Symbol
- Series
- Security Name
- Category
- Last Trade Date
- Face Value (Rs.)
- Issue Size
- Close Price/Paid-up Value (Rs.)
- Market Cap (Rs.) **[PRIMARY METRIC]**

**Update Frequency:** Daily at 8:30 PM IST
**Historical Backfill:** 5 years (or 1 year minimum); stop on first missing file
**Data Filtering:** Only store for securities in Listed Securities table

#### 5.1.4 Bulk & Block Deals (Daily EOD)
**Sources:**
- Block Deals: `https://nsearchives.nseindia.com/content/equities/block.csv`
- Bulk Deals: `https://nsearchives.nseindia.com/content/equities/bulk.csv`

**Fields:**
- Date
- Symbol
- Security Name
- Client Name
- Deal Type (Buy/Sell)
- Quantity
- Trade Price
- Remarks

**Update Frequency:** Daily at 8:30 PM IST
**Historical Backfill:** Provided separately (manual import)

#### 5.1.5 Historical OHLCV Data (One-time Backfill)
**Source:** Upstox API
**Endpoint:** `/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}`
**Documentation:** https://upstox.com/developer/api-documentation/v3/get-historical-candle-data

**Coverage:**
- All listed securities from 5.1.1
- All ETFs from 5.1.1
- All indices from 5.1.2

**Fields:**
- Date
- Open
- High
- Low
- Close
- Volume (equities/ETFs only; N/A for indices)

**Historical Range:** 5 years from current date
**Handling Recent Listings:** Fetch from listing date if <5 years old
**API Behavior:** Upstox auto-handles listing date validation

#### 5.1.6 Daily OHLCV + Market Quote (Daily EOD)
**Source:** Upstox API
**Endpoint:** `/market-quote/quotes` (Full Market Quote)
**Documentation:** https://upstox.com/developer/api-documentation/get-full-market-quote

**Fields to Store:**
- Last Price
- Open, High, Low, Close (OHLC)
- Volume
- Previous Close
- Change (absolute and %)
- Last Trade Time
- OI (Open Interest, for derivatives - skip for equities)
- VWAP (Volume Weighted Average Price)
- Upper Circuit / Lower Circuit
- 52-week High/Low
- **Exclude:** Depth data (bids/asks)

**Update Frequency:** Daily at 8:45 PM IST (after OHLCV data is finalized)

#### 5.1.7 Industry & Sector Classification (Weekly)
**Source:** NSE Website (requires cookie-based authentication)
**Endpoint:** `https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}`

**Fields:**
- Symbol
- Macro (highest level)
- Sector
- Industry
- Basic Industry (most granular)

**Update Frequency:** Weekly (Sundays at 10 PM IST)
**Historical Backfill:** Not required
**Challenge:** NSE requires session cookies; solution via Playwright browser automation

#### 5.1.8 Surveillance Measures (Daily EOD)
**Source:** NSE Archives
**URL Pattern:** `https://nsearchives.nseindia.com/content/cm/REG1_IND{DDMMYY}.csv`

**Fields:**
- Date
- Symbol
- Security Name
- Surveillance Action (ASM, GSM, etc.)
- Reason

**Update Frequency:** Daily at 8:30 PM IST
**Historical Backfill:** Not required
**Usage:** Filter out flagged securities from screeners

#### 5.1.9 Index Constituents (Monthly Manual)
**Source:** Niftyindices.com
**Format:** CSV (manually downloaded)

**Fields:**
- Index Name (e.g., "Nifty 50", "Nifty Bank")
- Symbol
- Company Name
- Industry
- Weightage (%)

**Update Frequency:** Monthly (manual upload)
**Historical Backfill:** Not required

#### 5.1.10 Market Holidays (One-time + Annual Update)
**Source:** Upstox API
**Endpoint:** `/market-holidays`
**Documentation:** https://upstox.com/developer/api-documentation/get-market-holidays

**Fields:**
- Date
- Holiday Name
- Exchange (NSE/BSE)

**Update Frequency:** Annual (or on-demand)

---

### 5.2 Database Schema Requirements

#### 5.2.1 Primary Identifiers
- **Securities & ETFs:** Symbol (primary), ISIN (secondary, unique)
- **Indices:** Index Name + Symbol
- **Time-series Data:** Composite key (Symbol/ISIN + Date)

#### 5.2.2 Data Relationships
```
Securities (1) ──< (N) OHLCV Daily
Securities (1) ──< (N) Market Cap History
Securities (1) ──< (N) Bulk Deals
Securities (1) ──< (N) Block Deals
Securities (N) ──> (1) Industry Classification
Securities (N) ──> (N) Index Constituents (M:N join table)
Securities (1) ──< (1) Surveillance Status
```

#### 5.2.3 Tables Required (Phase 1)
1. **securities** (equities + ETFs master table)
2. **indices** (index master table)
3. **ohlcv_daily** (time-series: daily OHLC + volume)
4. **market_cap_history** (time-series: daily market cap)
5. **bulk_deals** (transaction records)
6. **block_deals** (transaction records)
7. **industry_classification** (lookup table)
8. **surveillance_measures** (current status + history)
9. **index_constituents** (M:N join table)
10. **market_holidays** (calendar table)

See [Architecture.md](./Architecture.md) for detailed schema definitions.

---

### 5.3 API Requirements (Phase 1)

#### 5.3.1 Data Ingestion Endpoints
- `POST /ingest/securities` - Ingest listed securities from NSE
- `POST /ingest/etfs` - Ingest ETF list from NSE
- `POST /ingest/indices` - Sync indices from Upstox
- `POST /ingest/market-cap` - Ingest daily market cap
- `POST /ingest/bulk-deals` - Ingest bulk deals
- `POST /ingest/block-deals` - Ingest block deals
- `POST /ingest/surveillance` - Ingest surveillance measures
- `POST /ingest/industry-classification` - Ingest industry data (weekly)
- `POST /ingest/historical-ohlcv/{symbol}` - Backfill historical OHLCV
- `POST /ingest/daily-ohlcv` - Ingest daily OHLCV for all securities

#### 5.3.2 Data Retrieval Endpoints
- `GET /securities` - List all securities with filters
- `GET /securities/{symbol}` - Get security details
- `GET /securities/{symbol}/ohlcv?from={date}&to={date}` - OHLCV history
- `GET /securities/{symbol}/market-cap?from={date}&to={date}` - Market cap history
- `GET /indices` - List all indices
- `GET /indices/{index_name}/constituents` - Index constituents
- `GET /bulk-deals?symbol={symbol}&from={date}&to={date}` - Bulk deals
- `GET /block-deals?symbol={symbol}&from={date}&to={date}` - Block deals

#### 5.3.3 Health & Monitoring
- `GET /health` - System health check
- `GET /status/ingestion` - Last ingestion status for all sources
- `GET /status/data-quality` - Data completeness metrics

---

### 5.4 Automation Requirements (n8n Workflows)

#### 5.4.1 Daily EOD Workflow (8:30-9:00 PM IST)
**Trigger:** Cron schedule (weekdays only, check holiday calendar)
**Steps:**
1. Check if today is a trading day (query market_holidays)
2. **Parallel Execution:**
   - Fetch NSE listed securities → POST /ingest/securities
   - Fetch NSE ETF list → POST /ingest/etfs
   - Fetch market cap ZIP → Extract → POST /ingest/market-cap
   - Fetch bulk deals → POST /ingest/bulk-deals
   - Fetch block deals → POST /ingest/block-deals
   - Fetch surveillance measures → POST /ingest/surveillance
3. Wait for all to complete
4. Fetch Upstox daily OHLCV for all symbols → POST /ingest/daily-ohlcv
5. Send success/failure notification (email/Slack/webhook)

**Error Handling:**
- Retry failed steps 3x with exponential backoff
- Log errors to database
- Send alert if critical step fails (OHLCV fetch)

#### 5.4.2 Weekly Industry Classification Workflow (Sundays 10 PM IST)
**Trigger:** Cron schedule (Sundays)
**Steps:**
1. Launch Playwright browser
2. Visit NSE homepage to get session cookies
3. For each symbol in securities table:
   - GET `https://www.nseindia.com/api/quote-equity?symbol={symbol}` with cookies
   - Extract industryInfo object
   - POST /ingest/industry-classification with data
   - Sleep 1 second (rate limiting)
4. Close browser
5. Send summary notification (symbols updated, failures)

**Cookie Refresh Strategy:**
- If 403 error, refresh browser session and retry
- Max 3 cookie refresh attempts
- Fallback to manual cookie input if automation fails

#### 5.4.3 Historical Data Backfill Workflow (One-time, Manual Trigger)
**Trigger:** Manual start from n8n UI
**Steps:**
1. Get all symbols from securities table
2. For each symbol:
   - Calculate from_date (5 years ago or listing date)
   - GET Upstox historical candle data
   - POST /ingest/historical-ohlcv/{symbol}
   - Update progress counter
3. Repeat for all indices and ETFs
4. Send completion report (total records, failures)

**Rate Limiting:** Upstox API limits apply (TBD from SDK docs)

#### 5.4.4 Market Cap Historical Backfill Workflow (One-time, Manual Trigger)
**Trigger:** Manual start from n8n UI
**Steps:**
1. Loop from 5 years ago to yesterday
2. For each date:
   - Skip weekends/holidays
   - Fetch PR{DDMMYY}.zip from NSE
   - Extract MCAP{DDMMYYYY}.csv
   - POST /ingest/market-cap with date parameter
   - If 404 (missing file), log and stop backfill for earlier dates
3. Send completion report

---

### 5.5 Data Validation Requirements

#### 5.5.1 Ingestion-time Validations
- **Symbol/ISIN Format:** Regex validation for NSE symbol patterns
- **Date Validation:** Reject future dates; validate format consistency
- **Numeric Ranges:** OHLC values must be positive; Volume ≥ 0
- **OHLC Consistency:** High ≥ Low, Open/Close between High/Low
- **Duplicate Detection:** Composite key (Symbol + Date) uniqueness
- **Foreign Key Integrity:** Symbol must exist in securities table before OHLCV insertion

#### 5.5.2 Post-ingestion Quality Checks
- **Completeness:** % of securities with OHLCV data for date
- **Gap Detection:** Missing dates in time-series (excluding holidays)
- **Outlier Detection:** Flag >20% daily price moves for review
- **Volume Anomalies:** Flag 0 volume on trading days

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **Query Response Time:** <1 second for screener results (up to 2000 securities)
- **Data Ingestion:** Complete daily EOD fetch within 30 minutes
- **Historical Backfill:** Process 2000 securities × 5 years within 24 hours (with API rate limits)
- **Database:** Support 10M+ time-series records without degradation

### 6.2 Scalability
- **Horizontal Scaling:** n8n workflows can run on multiple workers
- **Database:** PostgreSQL initially; migrate to ClickHouse if query performance degrades
- **API:** FastAPI can scale with multiple uvicorn workers

### 6.3 Reliability
- **Uptime Target:** 99% availability (excluding maintenance windows)
- **Data Integrity:** ACID compliance for all database transactions
- **Backup:** Daily automated PostgreSQL backups (Docker volume snapshots)
- **Disaster Recovery:** Database restore from backup within 1 hour

### 6.4 Security
- **API Credentials:** Store Upstox API keys in environment variables (never hardcode)
- **Database:** Remove hardcoded credentials; use .env files
- **Network:** Localhost-only access initially; add authentication for cloud deployment
- **Secrets Management:** Docker secrets for production

### 6.5 Maintainability
- **Code Quality:** Pylint/Black for Python; type hints for all functions
- **Documentation:** Inline docstrings; API docs via FastAPI auto-generation
- **Logging:** Structured logs (JSON) with severity levels
- **Monitoring:** n8n execution logs; database query performance metrics

### 6.6 Usability (n8n)
- **Workflow Templates:** Pre-built templates for common data sources
- **Visual Debugging:** n8n UI shows execution flow and intermediate data
- **Error Notifications:** Clear error messages with remediation steps

---

## 7. Screener Specifications (Phase 2)

### 7.1 Universal Filters (Apply to All Screeners)
- **Security Type:** Listed equities + ETFs only (exclude indices unless specified)
- **Market Cap:** ≥ ₹100 crore
- **Volume:** Average daily volume ≥ 100,000 shares (20-day average)
- **Surveillance:** Exclude securities in ASM/GSM frameworks
- **Liquidity:** Traded on ≥80% of last 20 trading days

### 7.2 Screener 1: 4% Daily Breakouts/Gainers
**Inspiration:** @PradeepBonde (Stockbee)
**Purpose:** Identify momentum stocks with ≥4% daily moves and volume surge

**Criteria:**
- Daily % Change ≥ 4% (or ≤ -4% for decliners)
- RVOL (Relative Volume) ≥ 1.25
- Optional: M30 Re-ORH confirmation (if intraday data available)

**Output Columns:**
- Ticker, % Change, Close Price, Volume, RVOL, M30 Re-ORH (Yes/No), Market Cap, Sector

**Sorting:** Descending by % Change
**Separate Lists:** +4% Gainers, -4% Decliners

### 7.3 Screener 2: 20% Weekly Moves
**Inspiration:** @PradeepBonde (Stockbee)
**Purpose:** Extreme swings for pattern study and volatility context

**Criteria:**
- Weekly % Change ≥ 20% (or ≤ -20%)
- ADR% > 2% (volatility filter)

**Output Columns:**
- Ticker, Weekly % Change, Volume Avg (20D), ADR%, Market Cap, Industry, Sector

**Sorting:** Descending by absolute % change
**Separate Lists:** +20% Gainers, -20% Decliners

### 7.4 Screener 3: High-Volume Movers
**Inspiration:** @PradeepBonde (Stockbee 9M screener, adapted to NSE)
**Purpose:** Volume surge detection for institutional interest

**Criteria:**
- Volume ≥ 5M shares (single day)
- RVOL ≥ 1.25
- Optional: Float % tracking (if data available)

**Output Columns:**
- Ticker, Volume, RVOL, % Change, Float %, Market Cap, Industry, Sector

**Sorting:** Descending by volume

### 7.5 Screener 4: Relative Strength Leaders ("97 Club")
**Inspiration:** @SteveDJacobs (Qullamaggie)
**Purpose:** Top 3% relative strength across multiple timeframes

**Criteria:**
- VARS (Volatility-Adjusted RS) ≥ 97th percentile in at least 2 of:
  - 1-week RS
  - 1-month RS
  - 3-month RS
- Price > SMA50

**Output Columns:**
- Ticker, VARS Day, VARS Week, VARS Month, % Change (1M), Market Cap, Industry, Sector

**Sorting:** Descending by average VARS

**VARS Calculation:** RS Percentile / (ATR% / 100) - normalizes for volatility

### 7.6 Screener 5: MA Stacked Breakouts
**Inspiration:** @SteveDJacobs (Qullamaggie) + @FranVezz
**Purpose:** Uptrend breakouts with VCP contraction patterns

**Criteria:**
- MA Stack: Close > EMA10 > SMA20 > SMA50
- 20-day range breakout ≥ 50%
- VARS (1W or 1M or 3M) ≥ 97
- VCP Score ≥ 3 (narrowing ranges over 3-5 bars)
- ATR% from SMA50 < 7x (not overly extended)

**Output Columns:**
- Ticker, RS (max timeframe), ATR% from 50-MA, VCP Score, Price-to-Range %, Market Cap, Industry, Sector

**Sorting:** Ascending by ATR% extension (least extended first)
**Highlight:** Bold if ≥7x extension (risky)

### 7.7 Screener 6: ATR Extension Matrix for Sectors
**Inspiration:** @SteveDJacobs
**Purpose:** Sector rotation by extension levels

**Criteria:**
- Calculate ATR Extension for each sectoral index
- ATR Extension = ((Close / SMA50) - 1) / (ATR / Close)

**Output Columns:**
- Sector, ATR Extension, ADR%, Weekly % Change, Monthly % Change

**Sorting:** Descending by ATR Extension
**Color Coding:** Green (<3x), Yellow (3-5x), Red (>5x)

### 7.8 Screener 7: Leading Industries/Groups
**Inspiration:** @SteveDJacobs + @FranVezz
**Purpose:** Top 20% industry strength with laggard identification

**Criteria:**
- Calculate equal-weighted VARS for each industry
- Top 20% VARS (weekly/monthly)
- Show VARW (Volatility-Adjusted Relative Weakness) for laggards

**Output Columns:**
- Industry Group, Weekly Strength (VARS %), Monthly Strength, VARW (laggards), Top 4 Performers (Ticker, % Change)

**Sorting:** Descending by weekly strength
**Highlight:** Top 20% in green

### 7.9 Screener 8: Stage Analysis Breakdown
**Inspiration:** @SteveDJacobs (Stan Weinstein Stage Analysis)
**Purpose:** Stage classification with tight entry identification

**Stages:**
- **Stage 1 (Basing):** Price below SMA50, SMA50 flattening
- **Stage 2 (Advancing):** Price > SMA50, SMA50 rising, EMA10 > SMA20
- **Stage 3 (Topping):** Price > SMA50, SMA50 flattening
- **Stage 4 (Declining):** Price < SMA50, SMA50 falling

**Criteria:**
- LoD ATR % < 60% (for tight Stage 2 entries)

**Output Columns:**
- Stage Breakdown (% in each stage)
- Count by Stage
- Average LoD ATR % for Stage 2 stocks
- Bar chart + table

**Sorting:** By stage priority (Stage 2 first)

### 7.10 Screener 9: Momentum Watchlist
**Inspiration:** @FranVezz + @PradeepBonde
**Purpose:** RS leaders holding key MAs with catalysts

**Criteria:**
- VARS (1M) ≥ 90
- Price holding SMA50 (within 5%)
- Green candles (Close > Open) in last 3 days
- LoD ATR % < 60%
- Optional: Recent bulk/block deal (last 5 days) as PEAD proxy

**Output Columns:**
- Ticker, RS (1M), Candle Type, LoD ATR %, Recent Deal (Yes/No), Industry, Sector

**Sorting:** Ascending by LoD ATR % (tightest first)

### 7.11 Screener 10: Breadth Metrics Dashboard
**Inspiration:** @SteveDJacobs + @PradeepBonde + TradersLab.io
**Purpose:** Market sentiment via advance/decline and McClellan metrics

**Universes:**
- Nifty 50 (equal-weighted)
- Nifty 500 (equal-weighted)
- NSE Composite (all listed)

**Metrics:**
- Up/Down Ratio (1D, 1W, 1M)
- % Above SMA20, SMA50, SMA200
- New 20-Day Highs / Lows
- McClellan Oscillator (19-EMA advances - 39-EMA declines)
- McClellan Summation Index (cumulative oscillator)

**Output Format:**
- Table with universes as rows
- Stacked bar charts for % above MAs
- Line chart for McClellan Oscillator over time

### 7.12 Screener 11: RRG Charts for Sectoral Indices (PRIORITY)
**Purpose:** Sector rotation visualization via Relative Rotation Graphs

**Methodology:**
1. Calculate RS-Ratio for each sector vs. Nifty 50 benchmark
   - RS-Ratio = (Sector Index / Nifty 50) / SMA(Sector Index / Nifty 50, 10 weeks)
2. Calculate RS-Momentum = ROC(RS-Ratio, 10 weeks)
3. Plot on quadrant chart:
   - **Leading (top-right):** RS-Ratio > 100, RS-Momentum > 100
   - **Weakening (top-left):** RS-Ratio < 100, RS-Momentum > 100
   - **Lagging (bottom-left):** RS-Ratio < 100, RS-Momentum < 100
   - **Improving (bottom-right):** RS-Ratio > 100, RS-Momentum < 100
4. Show tails (10-week history)
5. Color points by ADR% (high volatility = red tails for risk)

**Sectors to Include:**
- Nifty Auto
- Nifty Bank
- Nifty Financial Services
- Nifty FMCG
- Nifty IT
- Nifty Media
- Nifty Metal
- Nifty Pharma
- Nifty PSU Bank
- Nifty Realty
- Nifty Private Bank
- (Add more as needed)

**Output:**
- Interactive scatter plot (X: RS-Ratio, Y: RS-Momentum)
- Hover tooltip: Sector name, RS values, % change
- Update frequency: Weekly

---

## 8. Daily Calculated Metrics (Phase 2)

Post-EOD (8-9 PM IST), calculate and store the following for all securities:

1. **Price Changes:** 1D, 1W, 1M, 3M, 6M % changes
2. **Relative Strength (RS):** Percentile ranking (0-100) across universe for each timeframe
3. **VARS:** Volatility-Adjusted RS = RS / (ATR% / 100)
4. **VARW:** Volatility-Adjusted Relative Weakness (inverse VARS for laggards)
5. **Moving Averages:** EMA10, SMA20, SMA50, SMA100, SMA200
6. **ATR (14-day):** Wilder's Average True Range
7. **ATR%:** (ATR / Close) × 100
8. **ATR% from 50-MA:** Multiples (e.g., 3x, 5x, 7x)
9. **ADR%:** Average Daily Range % = Avg((High - Low) / Close × 100, 20 days)
10. **ATR Extension:** ((Close / SMA50) - 1) / (ATR / Close)
11. **20-Day Darvas Box:** Highest high, lowest low, price-to-range %
12. **RVOL:** Today's volume / 50-day average volume
13. **ORH/M30 Re-ORH:** Opening range high; 30-min reclaim flag (if intraday data available)
14. **LoD ATR%:** (Low of Day - Close) / ATR × 100 (<60% flag for tight entries)
15. **New 20-Day Highs/Lows:** Count of securities at highs/lows
16. **Industry/Sector Strength:** Equal-weighted VARS % for each industry
17. **RRG Metrics:** RS-Ratio, RS-Momentum, ADR% color scale
18. **Candle Type:** Green (Close > Open) / Red flag
19. **Up/Down Counts:** 1D, 1W, 1M (for breadth metrics)
20. **McClellan Oscillator:** 19-EMA advances - 39-EMA declines
21. **McClellan Summation Index:** Cumulative McClellan Oscillator
22. **VCP Score:** Volatility Contraction Pattern (1-5 based on narrowing ranges over 3-5 bars)
23. **Stage Classification:** Stage 1-4 with LoD flag

---

## 9. Success Metrics

### 9.1 Phase 1 (Data Storage) Success Criteria
- ✅ 100% of listed securities (2000+) in database
- ✅ 5 years historical OHLCV data for ≥95% of universe
- ✅ Daily EOD fetch success rate ≥98%
- ✅ Market cap historical data for ≥80% of securities (5Y or 1Y)
- ✅ Industry classification coverage ≥95%
- ✅ n8n workflows running without manual intervention for 30 days
- ✅ Data quality score ≥95% (completeness + accuracy)

### 9.2 Phase 2 (Screeners) Success Criteria
- ✅ RRG charts generate within 5 seconds
- ✅ Daily metrics calculated for entire universe within 1 hour post-EOD
- ✅ Screener results match manual calculations (spot-check 10 securities)
- ✅ All 11 screeners operational and accessible via API

### 9.3 Performance Benchmarks
- Database query response time: <500ms for 5Y OHLCV data (single security)
- API endpoint latency: <200ms for screener results
- n8n workflow execution time: <30 minutes for complete daily fetch

---

## 10. Assumptions & Dependencies

### 10.1 Assumptions
- Upstox API rate limits allow backfilling 2000+ securities within 24 hours
- NSE archives remain publicly accessible without authentication (except industry data)
- Market cap data files (PR*.zip) continue to be published daily by NSE
- PostgreSQL can handle 10M+ records without significant performance degradation (ClickHouse migration if needed)
- n8n community edition supports required workflow complexity

### 10.2 External Dependencies
- **Upstox API:** Availability, rate limits, data accuracy
- **NSE Website:** Uptime, URL stability, cookie-based authentication
- **Docker:** Local environment stability
- **Playwright:** Browser automation for NSE scraping

### 10.3 Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Upstox API downtime | High | Cache last successful fetch; retry mechanism |
| NSE changes cookie auth | Medium | Playwright auto-refresh; manual override capability |
| NSE archive gaps (market cap) | Low | Graceful handling; flag missing dates |
| PostgreSQL performance | Medium | Index optimization; ClickHouse migration plan |
| n8n workflow failures | High | Comprehensive error handling; alerting |

---

## 11. Future Enhancements (Post-Phase 2)

### 11.1 Data Enhancements
- Intraday tick data for ORH/M30 Re-ORH calculations
- Earnings dates for PEAD (Post-Earnings Announcement Drift)
- Corporate actions (splits, bonuses, dividends)
- Futures/Options data for derivatives screeners

### 11.2 Screener Enhancements
- Custom screener builder (user-defined filters)
- Backtesting framework for screener performance
- Alerts (email/SMS/webhook) when securities meet screener criteria
- Portfolio integration (track screener picks)

### 11.3 Infrastructure
- ClickHouse migration for time-series data
- Cloud deployment (AWS/GCP)
- Frontend dashboard (React/Vue.js)
- User authentication and multi-tenancy

---

## 12. Glossary

- **ADR%:** Average Daily Range % - Avg((High - Low) / Close × 100, 20 days)
- **ATR:** Average True Range (14-day Wilder's method)
- **ATR%:** (ATR / Close) × 100
- **ATR Extension:** ((Close / SMA50) - 1) / (ATR / Close)
- **EOD:** End of Day
- **ISIN:** International Securities Identification Number
- **LoD:** Low of Day
- **M30 Re-ORH:** 30-minute reclaim of Opening Range High
- **McClellan Oscillator:** 19-EMA(Advances - Declines) - 39-EMA(Advances - Declines)
- **NSE:** National Stock Exchange of India
- **ORH:** Opening Range High (first 30 minutes)
- **PEAD:** Post-Earnings Announcement Drift
- **RRG:** Relative Rotation Graph
- **RS:** Relative Strength (percentile ranking)
- **RVOL:** Relative Volume = Today's Volume / 50-day Avg Volume
- **VARS:** Volatility-Adjusted Relative Strength = RS / (ATR% / 100)
- **VARW:** Volatility-Adjusted Relative Weakness (inverse VARS)
- **VCP:** Volatility Contraction Pattern (narrowing ranges pre-breakout)
- **VWAP:** Volume Weighted Average Price

---

## 13. References

### 13.1 External Documentation
- Upstox Python SDK: https://upstox.com/developer/api-documentation/upstox-generated-sdk
- NSE Archives: https://nsearchives.nseindia.com/
- n8n Documentation: https://docs.n8n.io/
- Playwright: https://playwright.dev/

### 13.2 Trading Strategy References
- @PradeepBonde (Stockbee): Momentum breakout strategies
- @SteveDJacobs (Qullamaggie): MA stacked breakouts, ATR extensions, RS leaders
- @FranVezz: VCP patterns, momentum watchlists
- Jeff Sun's Substack: VARS/VARW, ADR%, LoD ATR distance
- TradersLab.io: Equal-weighted breadth, McClellan metrics

---

**Document Owner:** Development Team
**Last Updated:** November 16, 2025
**Next Review:** After Phase 1 Completion
