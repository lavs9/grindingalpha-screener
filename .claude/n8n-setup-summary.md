# n8n Setup Summary

**Date:** December 6, 2025
**Phase:** 1.6 - n8n Workflow Automation (Setup Complete)

---

## ✅ Completed Setup

### 1. Docker Compose Configuration
- **n8n container** configured with PostgreSQL storage
- **Database persistence** enabled (workflows survive container restarts)
- **n8n schema** will be auto-created in existing PostgreSQL instance
- **Health check dependencies** configured (postgres → backend → n8n)

### 2. Authentication & Security
- **UI Authentication:** Basic Auth enabled
  - Username: Set via `N8N_BASIC_AUTH_USER` in `.env`
  - Password: Set via `N8N_BASIC_AUTH_PASSWORD` in `.env`

- **API Authentication:** API key generated for programmatic access
  - API Key: Set via `N8N_API_KEY` in `.env`
  - Header: `X-N8N-API-KEY`

### 3. Environment Variables Required
```bash
# In .env (NOT committed to git)
# Generate secure values using:
# API Key: openssl rand -hex 32
# Password: openssl rand -base64 24

N8N_API_KEY=<generate-with-openssl-rand-hex-32>
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<generate-with-openssl-rand-base64-24>

# Optional (configure later)
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# NOTIFICATION_EMAIL=alerts@yourcompany.com
```

### 4. Documentation Created
- ✅ **[.claude/n8n-workflows-plan.md](.claude/n8n-workflows-plan.md)** - Complete workflow specifications (5 workflows)
- ✅ **[n8n/README.md](../n8n/README.md)** - Setup guide, troubleshooting, best practices
- ✅ **[.claude/mcp-config.json](.claude/mcp-config.json)** - MCP server configuration for Claude Code
- ✅ **[.env.example](../.env.example)** - Updated with n8n configuration template

### 5. MCP Server Configuration
Pre-configured for Claude Code integration:
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "<copy-from-your-.env-file>"
      }
    }
  }
}
```

**Note:** Replace `<copy-from-your-.env-file>` with the actual `N8N_API_KEY` value from your `.env` file.

---

## 📋 Workflow Implementation Plan

### 5 Workflows to Implement

| Priority | Workflow | Schedule | Description |
|----------|----------|----------|-------------|
| 🔥 1 | **Upstox Token Refresh** | Daily 8:00 AM IST | Check token expiry, refresh if needed |
| 🔥 2 | **Daily EOD Master** | Mon-Fri 9:00 PM IST | 6 parallel branches + OHLCV dependent branch |
| 3 | **Weekly Industry Scraper** | Sunday 10:00 AM IST | Playwright-based NSE industry classification |
| 4 | **Upstox Instrument Refresh** | Saturday 11:00 PM IST | Update 64,699+ instruments from NSE.json.gz |
| 5 | **Historical OHLCV Backfill** | Manual trigger | 5-year data for 2000+ securities |

### Daily EOD Master Workflow (Most Complex)
```
[Cron Trigger: Mon-Fri 9 PM] → [Check Market Open?] → [6 Parallel Branches]
    ├─ NSE Securities
    ├─ NSE ETFs
    ├─ NSE Market Cap
    ├─ Bulk Deals
    ├─ Block Deals
    └─ Surveillance List
        ↓
[Check Securities Updated?] → [Upstox Daily OHLCV] (depends on securities)
        ↓
[Aggregation Query from ingestion_logs] → [Send Summary Notification]
```

**Key Design:**
- **Continue On Fail: TRUE** on all parallel branches (failures don't block others)
- **Database-driven aggregation** (query `ingestion_logs`, not n8n state)
- **Critical dependency check** (OHLCV only runs if securities updated successfully)

---

## ⚠️ Missing Backend Endpoints

Before building workflows, implement these 3 endpoints:

### 1. Market Status Check
```
GET /api/v1/health/market-status

Purpose: Check if today is a trading day (skip workflow on holidays)

Response:
{
  "is_market_open": false,
  "is_trading_day": true,
  "current_time": "2025-12-06T21:00:00+05:30",
  "next_open": "2025-12-09T09:15:00+05:30",
  "message": "Market closed for the day"
}
```

**Implementation:**
- Query `market_holidays` table
- Check if CURRENT_DATE is a weekend (Sat/Sun)
- Return market status with IST timezone

**CRITICAL for n8n workflows:**
- Daily EOD workflow runs at **9 PM IST** (AFTER market close)
- **Always check `is_trading_day` field, NOT `is_market_open`**
- `is_trading_day === false` → Skip workflow (holiday/weekend)
- `is_trading_day === true` → Run workflow (market was open today)

**Why this matters:**
- At 9 PM, `is_market_open` will ALWAYS be `false` (market closes at 3:30 PM)
- But `is_trading_day` will be `true` if market was open earlier today
- Using `is_market_open` would incorrectly skip ALL workflows!

---

### 2. Daily OHLCV Ingestion
```
POST /api/v1/ingest/daily-ohlcv

Purpose: Fetch daily OHLCV for all active securities from Upstox

Request Body (optional):
{
  "symbols": ["RELIANCE", "TCS"]  // If empty, fetch all active securities
}

Response:
{
  "success": true,
  "total_symbols": 2200,
  "successful": 2150,
  "failed": 50,
  "errors": [
    {"symbol": "XYZ", "error": "No instrument mapping found"}
  ]
}
```

**Implementation:**
1. Get all active securities from `securities` table (or filter by `symbols` param)
2. For each security:
   - Get `instrument_key` from `symbol_instrument_mapping`
   - Call Upstox `/v2/market-quote/quotes?instrument_key={key}`
   - Parse OHLC, volume, VWAP, 52w high/low
3. Batch insert to `ohlcv_daily` (UPSERT on `symbol` + `date`)
4. Log to `ingestion_logs` table
5. Return summary with success/failure counts

**Reference:**
- Test endpoint exists: `GET /api/v1/auth/upstox/test-market-quotes?symbol=RELIANCE`
- Use same logic but batch all symbols

---

### 3. Historical OHLCV Backfill
```
POST /api/v1/ingest/historical-ohlcv/{symbol}

Purpose: Fetch 5 years of historical OHLCV for a single symbol

Query Parameters:
- from_date: YYYY-MM-DD (optional, defaults to max(listing_date, 5 years ago))
- to_date: YYYY-MM-DD (optional, defaults to today)

Response:
{
  "success": true,
  "symbol": "RELIANCE",
  "records_inserted": 1250,
  "date_range": {
    "from": "2020-12-06",
    "to": "2025-12-06"
  },
  "gaps_detected": []
}
```

**Implementation:**
1. Get security details from `securities` table (validate symbol exists)
2. Calculate `from_date`:
   - If not provided: `max(listing_date, CURRENT_DATE - 5 years)`
3. Get `instrument_key` from `symbol_instrument_mapping`
4. Call Upstox `/v2/historical-candle/{instrument_key}/day/{to_date}/{from_date}`
5. Parse candles (format: `[timestamp, open, high, low, close, volume]`)
6. Bulk insert to `ohlcv_daily` (UPSERT)
7. Detect gaps (missing trading days excluding weekends/holidays)
8. Log to `ingestion_logs`

**Reference:**
- Test endpoint exists: `GET /api/v1/auth/upstox/test-historical-data?symbol=RELIANCE`
- Use same logic with configurable date range

---

## 🚀 Next Steps

### Step 1: Restart n8n (Required)
```bash
cd /Users/mayanklavania/projects/screener

# Stop all containers
docker-compose down

# Start n8n (will create PostgreSQL schema on first run)
docker-compose up -d n8n

# Verify n8n is using PostgreSQL
docker-compose logs n8n | grep -i database
# Expected output: "Database type: postgresdb"
```

### Step 2: Verify n8n Setup
```bash
# Access n8n UI
open http://localhost:5678

# Login credentials:
# Username: Check N8N_BASIC_AUTH_USER in .env
# Password: Check N8N_BASIC_AUTH_PASSWORD in .env

# Test API access (using API key from .env)
curl -H "X-N8N-API-KEY: $(grep N8N_API_KEY .env | cut -d= -f2)" \
  http://localhost:5678/api/v1/workflows
```

### Step 3: Configure MCP Server (Optional but Recommended)
```bash
# Copy pre-configured MCP settings
cp .claude/mcp-config.json \
  ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

# Restart Claude Code extension in VSCode
# Verify MCP connection in Claude Code settings
```

### Step 4: Implement Missing Backend Endpoints
**Priority order:**
1. ✅ Market Status (`GET /api/v1/health/market-status`)
2. ✅ Daily OHLCV (`POST /api/v1/ingest/daily-ohlcv`)
3. ✅ Historical OHLCV (`POST /api/v1/ingest/historical-ohlcv/{symbol}`)

**Implementation files:**
- **Market Status:** Add to `backend/app/api/v1/health.py`
- **OHLCV Endpoints:** Add to `backend/app/api/v1/ingest.py`
- **Services:** Create `backend/app/services/upstox/daily_quotes_service.py` and `historical_service.py`
- **Schemas:** Add to `backend/app/schemas/upstox.py`

### Step 5: Build First Workflow (Upstox Token Refresh)
**Why start with this workflow:**
- Simplest workflow (only 5 nodes)
- Critical for daily operations (token expires at 23:59 IST)
- Tests n8n → backend → database connectivity

**Steps:**
1. Open n8n UI at http://localhost:5678
2. Create new workflow: "Upstox Token Refresh"
3. Add nodes:
   - Cron Trigger (daily 8 AM IST)
   - HTTP Request (token status check)
   - IF node (check if expired)
   - HTTP Request (refresh token)
   - Slack notification (if failed)
4. Test manually
5. Export workflow to `n8n/workflows/token-refresh.json`
6. Commit to git

### Step 6: Build Daily EOD Workflow
**Most complex workflow (13 nodes):**
1. Cron Trigger (Mon-Fri 9 PM IST)
2. Market Status Check (skip if holiday)
3. 6 Parallel HTTP Request nodes (securities, ETFs, market cap, deals, surveillance)
4. PostgreSQL Query (check if securities updated)
5. HTTP Request (Upstox daily OHLCV - dependent on securities)
6. PostgreSQL Aggregation Query (from `ingestion_logs`)
7. Function Node (format summary)
8. Slack Notification (send summary)

### Step 7: Test Workflows
```bash
# Test market status endpoint
curl http://localhost:8001/api/v1/health/market-status

# Test daily OHLCV endpoint
curl -X POST http://localhost:8001/api/v1/ingest/daily-ohlcv

# Test historical OHLCV endpoint
curl -X POST "http://localhost:8001/api/v1/ingest/historical-ohlcv/RELIANCE?from_date=2024-12-01&to_date=2025-12-06"

# Query ingestion logs
docker exec screener_postgres psql -U screener_user -d screener_db \
  -c "SELECT * FROM ingestion_logs ORDER BY timestamp DESC LIMIT 20;"
```

### Step 8: Enable Workflow Scheduling
Once manual tests pass:
1. Activate workflows in n8n UI
2. Monitor execution history
3. Set up Slack notifications (optional)
4. Document any failures in `ingestion_logs` table

---

## 📊 Monitoring & Observability

### Database Monitoring
```sql
-- Today's ingestion summary
SELECT
  source,
  status,
  COUNT(*) as executions,
  SUM(records_inserted) as total_records,
  MAX(timestamp) as last_run
FROM ingestion_logs
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY source, status
ORDER BY source;

-- Failed ingestions (last 7 days)
SELECT *
FROM ingestion_logs
WHERE status = 'failed'
  AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Slack Notifications (Optional)
1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Add to `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
3. Add Slack node to workflows
4. Test with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test from n8n"}' \
     $SLACK_WEBHOOK_URL
   ```

---

## 🔧 Troubleshooting

### Issue: n8n container won't start
**Solution:**
```bash
# Check logs
docker-compose logs n8n

# If PostgreSQL schema error, create manually:
docker exec screener_postgres psql -U screener_user -d screener_db \
  -c "CREATE SCHEMA IF NOT EXISTS n8n; GRANT ALL PRIVILEGES ON SCHEMA n8n TO screener_user;"

# Restart n8n
docker-compose restart n8n
```

### Issue: API key not working
**Solution:**
```bash
# Verify API key in .env
grep N8N_API_KEY .env

# Restart n8n to apply changes
docker-compose restart n8n

# Wait 10 seconds for startup
sleep 10

# Test again
curl -H "X-N8N-API-KEY: $(grep N8N_API_KEY .env | cut -d= -f2)" \
  http://localhost:5678/api/v1/workflows
```

### Issue: Workflow execution fails
**Checklist:**
1. Backend running? `curl http://localhost:8001/api/v1/health`
2. Database accessible? `docker exec screener_n8n nc -zv postgres 5432`
3. Upstox token valid? `curl http://localhost:8001/api/v1/auth/upstox/token-status`
4. Endpoint exists? Check FastAPI docs at http://localhost:8001/docs

---

## 📚 Documentation References

- **Workflow Specifications:** [.claude/n8n-workflows-plan.md](.claude/n8n-workflows-plan.md)
- **n8n Setup Guide:** [n8n/README.md](../n8n/README.md)
- **Architecture Details:** [.claude/Architecture.md](.claude/Architecture.md) Section 5
- **Implementation Plan:** [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md) Phase 1.6
- **MCP Configuration:** [.claude/mcp-config.json](.claude/mcp-config.json)

---

## ✅ Success Criteria (Phase 1.6)

- [ ] n8n running with PostgreSQL storage
- [ ] n8n UI accessible with Basic Auth
- [ ] n8n API accessible with API key
- [ ] 3 missing backend endpoints implemented
- [ ] Upstox Token Refresh workflow created and tested
- [ ] Daily EOD Master workflow created and tested
- [ ] Workflows run manually without errors
- [ ] `ingestion_logs` table populates correctly
- [ ] Parallel branch failures don't block other branches
- [ ] Workflows exported to `n8n/workflows/` directory
- [ ] Workflows scheduled and running automatically
- [ ] Notifications configured (Slack/Email)

---

## 🎯 Estimated Timeline

| Task | Duration | Status |
|------|----------|--------|
| n8n setup & configuration | 1 hour | ✅ Complete |
| Implement missing backend endpoints | 2-3 hours | ⏳ Pending |
| Build Upstox Token Refresh workflow | 1 hour | ⏳ Pending |
| Build Daily EOD Master workflow | 3-4 hours | ⏳ Pending |
| Build remaining 3 workflows | 2-3 hours | ⏳ Pending |
| Testing & debugging | 2-3 hours | ⏳ Pending |
| **Total** | **12-15 hours** | **10% Complete** |

---

## 🚀 Ready to Start!

You're now ready to proceed with Phase 1.6 implementation. Start by:

1. **Restart n8n** with new configuration
2. **Implement 3 missing endpoints** (market-status, daily-ohlcv, historical-ohlcv)
3. **Build first workflow** (Upstox Token Refresh - simplest)
4. **Test thoroughly** before scheduling

All documentation is in place, environment is configured, and the path forward is clear! 🎉
