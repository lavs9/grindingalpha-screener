# n8n Workflows for Stock Screener Automation

This directory contains n8n workflow definitions for automating daily data ingestion and metrics calculation.

## Available Workflows

### 1. Daily EOD Data Ingestion (With Metrics) ⭐ **RECOMMENDED**
**File:** `Daily_EOD_Data_Ingestion_With_Metrics.json`

**Schedule:** Monday-Friday at 8:30 PM IST

**What it does:**
1. Checks if today is a trading day (not weekend/holiday)
2. Ingests data from 6 sources in parallel:
   - NSE Securities List (EQUITY_L.csv)
   - NSE ETF List (ETF_L.csv)
   - NSE Market Cap Data (MCAP_*.csv)
   - Bulk Deals
   - Block Deals
   - Surveillance Lists
3. Checks ingestion status
4. If securities data is successful, ingests daily OHLCV data from Upstox
5. **Automatically calculates 64 technical indicators** (RSI, MACD, Bollinger Bands, ADX, etc.)
6. Returns final status summary

**API Endpoints Called:**
- `GET /api/v1/status/is-trading-day`
- `POST /api/v1/ingest/securities`
- `POST /api/v1/ingest/etf`
- `POST /api/v1/ingest/market-cap`
- `POST /api/v1/ingest/bulk-deals`
- `POST /api/v1/ingest/block-deals`
- `POST /api/v1/ingest/surveillance`
- `POST /api/v1/ingest/daily-ohlcv`
- `POST /api/v1/metrics/calculate-daily` ⭐ **NEW**
- `GET /api/v1/status/ingestion`

**Timeouts:**
- Data ingestion: 2 minutes (120s)
- OHLCV ingestion: 5 minutes (300s)
- Metrics calculation: 10 minutes (600s)

---

### 2. Daily EOD Data Ingestion (Original)
**File:** `Daily_EOD_Data_Ingestion.json`

Same as above but **without automatic metrics calculation**. Use this only if you want to calculate metrics separately.

---

### 3. Upstox Token Refresh
**File:** `Upstox_Token_Refresh.json`

**Schedule:** Monday-Friday at 8:00 AM IST

**What it does:**
- Automatically refreshes Upstox API access token using Playwright automation
- Stores new token in database with 23:59 IST expiry

---

### 4. Weekly Industry Classification
**File:** `Weekly_Industry_Classification.json`

**Schedule:** Sundays at 10:00 PM IST

**What it does:**
- Scrapes NSE website for updated industry classifications
- Updates `industry_classification` table

---

### 5. Historical Backfill OHLCV
**File:** `Historical_Backfill_OHLCV.json`

**Trigger:** Manual

**What it does:**
- Backfills historical OHLCV data (5 years default)
- For new securities or data gaps

---

## How to Import Workflows into n8n

### Option 1: Via n8n Web UI
1. Open n8n at http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select the JSON file you want to import
4. Click "Open"
5. Activate the workflow (toggle in top-right corner)

### Option 2: Via Docker Volume
The workflows are already mounted in the n8n container via Docker Compose:
```yaml
volumes:
  - ./n8n/workflows:/home/node/.n8n/workflows
```

Just restart the n8n container:
```bash
docker-compose restart n8n
```

---

## Manual Workflow Execution

### Trigger Daily EOD Workflow Manually
```bash
# Option 1: Via n8n UI
# Open http://localhost:5678, find the workflow, click "Execute Workflow"

# Option 2: Call backend endpoints directly
curl -X POST "http://localhost:8001/api/v1/ingest/securities"
curl -X POST "http://localhost:8001/api/v1/ingest/daily-ohlcv"
curl -X POST "http://localhost:8001/api/v1/metrics/calculate-daily"
```

---

## Backfill Scripts

### Backfill Metrics for December 2025
**File:** `../scripts/backfill_metrics_december.sh`

**What it does:**
- Calculates all 64 technical indicators for each trading day from December 1-26, 2025
- Skips weekends and holidays automatically
- Provides progress output for each date

**Usage:**
```bash
cd /Users/mayanklavania/projects/screener

# Make executable
chmod +x scripts/backfill_metrics_december.sh

# Run backfill
./scripts/backfill_metrics_december.sh
```

**Sample Output:**
```
===== Backfilling Technical Metrics for December 2025 =====
Date Range: 2025-12-01 to 2025-12-26

------------------------------------------------------------
Processing: 2025-12-01
------------------------------------------------------------
✅ SUCCESS: 2025-12-01
   Inserted: 1818 records
   Updated: 0 records

------------------------------------------------------------
Processing: 2025-12-06
------------------------------------------------------------
❌ FAILED: 2025-12-06 (HTTP 400)
   Response: {"detail":{"message":"Metrics calculation failed", ...}}

[Weekend/holiday - expected failure]
```

**Verify Results:**
```bash
# Check database
docker exec screener_postgres psql -U screener_user -d screener_db -c \
  "SELECT date, COUNT(*) FROM calculated_metrics WHERE date >= '2025-12-01' GROUP BY date ORDER BY date;"

# Check data quality
curl http://localhost:8001/api/v1/status/data-quality
```

---

## Workflow Behavior

### Trading Day Detection
- Workflows check `/api/v1/status/is-trading-day` before running
- If not a trading day (weekend/holiday), workflow exits gracefully
- No unnecessary API calls or errors

### Error Handling
- All ingestion nodes have `continueOnFail: true`
- Failures in one source don't block others
- OHLCV ingestion only runs if securities list was successfully ingested
- Metrics calculation only runs if OHLCV ingestion succeeded

### Status Monitoring
- Each workflow logs to `ingestion_logs` table
- Check recent runs:
  ```bash
  curl http://localhost:8001/api/v1/status/ingestion
  ```

---

## Metrics Calculated (64 Indicators)

When you run the Daily EOD workflow or backfill script, the following metrics are calculated:

### Price Changes (5)
- 1D, 1W, 1M, 3M, 6M percentage changes

### Relative Strength (3)
- RS Percentile (97 Club eligibility)
- VARS (Volume Adjusted RS)
- VARW (Volume Adjusted RS Weekly)

### Volatility (3)
- ATR-14 (Average True Range)
- ATR% (ATR as % of price)
- ADR% (Average Daily Range)

### Volume (3)
- RVOL (Relative Volume)
- 50-day average volume
- Volume surge flag

### Moving Averages (5)
- EMA10, SMA20, SMA50, SMA100, SMA200

### ATR Extension (2)
- ATR% from SMA50
- Low-of-Day ATR%

### Darvas Box (3)
- 20-day high/low
- Position %

### Pattern Recognition (2)
- VCP Score (1-5)
- MA Stacked Flag

### Stage Classification (2)
- Weinstein Stage (1-4)
- Stage Detail

### Breadth Metrics (4)
- Universe stocks above SMA50/SMA200
- McClellan Oscillator

### RRG Metrics (2)
- RS-Ratio
- RS-Momentum

### **NEW: Technical Indicators (17)**
- **RSI (3):** rsi_14, rsi_oversold, rsi_overbought
- **MACD (5):** macd_line, macd_signal, macd_histogram, is_macd_bullish_cross, is_macd_bearish_cross
- **Bollinger Bands (5):** bb_upper, bb_middle, bb_lower, bb_bandwidth_percent, is_bb_squeeze
- **ADX (4):** adx_14, di_plus, di_minus, is_strong_trend

---

## Troubleshooting

### Workflow Not Running
```bash
# Check n8n logs
docker-compose logs -f n8n

# Check if workflow is activated
# Open http://localhost:5678, check toggle in workflow UI

# Check cron schedule (should be Asia/Kolkata timezone)
```

### Metrics Calculation Failing
```bash
# Check backend logs
docker-compose logs -f backend

# Ensure OHLCV data exists for the target date
docker exec screener_postgres psql -U screener_user -d screener_db -c \
  "SELECT COUNT(*) FROM ohlcv_daily WHERE date = '2025-12-27';"

# Check for calculation errors
curl http://localhost:8001/api/v1/status/data-quality
```

### Upstox Token Expired
```bash
# Manually refresh token
curl -X POST http://localhost:8001/api/v1/auth/upstox/login

# Or run token refresh workflow manually via n8n UI
```

### Backfill Script Failing
```bash
# Check backend is running
curl http://localhost:8001/api/v1/status/data-quality

# Verify backend port (8001, not 8000)
docker ps | grep screener_backend

# Check date format (YYYY-MM-DD)
# Ensure OHLCV data exists for the date range
```

---

## Recommended Setup

For daily automated updates, use this configuration:

1. **Import and activate these workflows:**
   - ✅ Daily EOD Data Ingestion (With Metrics) - 8:30 PM IST Mon-Fri
   - ✅ Upstox Token Refresh - 8:00 AM IST Mon-Fri
   - ✅ Weekly Industry Classification - 10:00 PM IST Sundays

2. **One-time setup:**
   ```bash
   # Backfill historical metrics (if needed)
   ./scripts/backfill_metrics_december.sh
   ```

3. **Daily verification:**
   ```bash
   # Check data quality
   curl http://localhost:8001/api/v1/status/data-quality

   # Check recent ingestion status
   curl http://localhost:8001/api/v1/status/ingestion
   ```

4. **Access screeners:**
   - Open frontend: http://localhost:3000
   - All 14 screeners will have fresh data every trading day

---

## Workflow Execution Timeline (Typical Trading Day)

```
08:00 AM IST - Upstox Token Refresh
              ↓
              Token valid for entire trading day
              ↓
08:30 PM IST - Daily EOD Data Ingestion starts
              ↓
              [Step 1] Check if trading day (5s)
              ↓
              [Step 2] Ingest 6 data sources in parallel (60-120s)
              ├── Securities List
              ├── ETF List
              ├── Market Cap
              ├── Bulk Deals
              ├── Block Deals
              └── Surveillance
              ↓
              [Step 3] Verify securities ingestion (2s)
              ↓
              [Step 4] Ingest Daily OHLCV (120-300s)
              ↓
              [Step 5] Calculate 64 Technical Indicators (300-600s)
              ↓
              [Step 6] Final status check (2s)
              ↓
08:40-08:50 PM IST - Workflow complete
              ↓
              Fresh data available for all screeners
```

**Total Duration:** ~10-15 minutes per trading day

---

## Notes

- All workflows use IST timezone (Asia/Kolkata)
- Backend URL in workflows: `http://backend:8000` (Docker internal network)
- External API URL: `http://localhost:8001` (from host machine)
- Metrics calculation can take 5-10 minutes for ~1,800 securities
- Backfill scripts should be run during non-trading hours to avoid API conflicts

---

## Future Enhancements

Potential improvements for workflows:

1. **Email/Slack Notifications:** Add notification nodes for daily summary
2. **Error Retry Logic:** Automatic retry on transient failures
3. **Incremental Metrics:** Calculate only for symbols with new OHLCV data
4. **Performance Monitoring:** Add execution time tracking and alerts
5. **Data Validation:** Pre-calculation checks for data completeness
6. **Conditional Execution:** Skip metrics if OHLCV coverage < 90%

---

For more details on the backend API endpoints, see:
- [CLAUDE.md](../CLAUDE.md) - Project overview and development guide
- [.claude/Architecture.md](../.claude/Architecture.md) - System architecture
- Backend API docs: http://localhost:8001/docs (Swagger UI)
