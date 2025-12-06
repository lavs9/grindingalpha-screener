# n8n Workflows Implementation Plan

**Phase:** 1.6 - n8n Workflow Automation
**Duration:** 5-7 days
**Goal:** Automate daily data ingestion, weekly scraping, and historical backfill using n8n

---

## Overview

This document outlines all n8n workflows to be implemented for the Stock Screener Platform. Each workflow will trigger FastAPI endpoints and use database-driven aggregation for status tracking.

**Key Design Principles:**
1. **Independent Parallel Execution:** Each branch has `Continue On Fail: TRUE`
2. **Database-Driven Aggregation:** Query `ingestion_logs` table, not n8n state
3. **No Data Passing Between Branches:** Each source fetches independently
4. **Critical Dependency Handling:** OHLCV branch checks if securities exist first
5. **Manual Retry Capability:** Failed sources can be re-run individually

---

## Workflow 1: Daily EOD Master Workflow

**Schedule:** Every weekday at 9:00 PM IST (after market close + settlement)
**Trigger:** Cron: `0 21 * * 1-5` (Mon-Fri at 9 PM IST)
**Duration:** ~10-15 minutes (parallel execution)

### Architecture

```
[Cron Trigger] → [Check Market Open?] → [Parallel Execution (6 branches)]
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
            [NSE Securities]          [NSE ETFs]              [NSE Market Cap]
                    ↓                         ↓                         ↓
            [Bulk Deals]              [Block Deals]           [Surveillance List]
                    ↓                         ↓                         ↓
                    └─────────────────────────┼─────────────────────────┘
                                              ↓
                                    [Check OHLCV Prerequisites]
                                              ↓
                                    [Upstox Daily OHLCV] (depends on securities)
                                              ↓
                                    [Aggregation Query]
                                              ↓
                                    [Send Summary Email/Slack]
```

### Nodes

#### 1. Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 21 * * 1-5`
- **Timezone:** Asia/Kolkata

#### 2. Check Market Open (HTTP Request)
- **URL:** `http://backend:8000/api/v1/health/market-status`
- **Method:** GET
- **Expected Response:** `{"is_market_open": false, "next_open": "..."}`
- **Branch Logic:** If market closed today (holiday), skip workflow

#### 3. Parallel Branch 1: NSE Securities
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/securities`
- **Method:** POST
- **Timeout:** 120 seconds
- **Continue On Fail:** TRUE
- **Expected Response:**
  ```json
  {
    "success": true,
    "total_records": 2200,
    "inserted": 50,
    "updated": 2150,
    "source": "EQUITY_L.csv"
  }
  ```

#### 4. Parallel Branch 2: NSE ETFs
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/etfs`
- **Method:** POST
- **Timeout:** 60 seconds
- **Continue On Fail:** TRUE

#### 5. Parallel Branch 3: NSE Market Cap
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/market-cap`
- **Method:** POST
- **Timeout:** 90 seconds
- **Continue On Fail:** TRUE

#### 6. Parallel Branch 4: Bulk Deals
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/bulk-deals`
- **Method:** POST
- **Timeout:** 60 seconds
- **Continue On Fail:** TRUE

#### 7. Parallel Branch 5: Block Deals
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/block-deals`
- **Method:** POST
- **Timeout:** 60 seconds
- **Continue On Fail:** TRUE

#### 8. Parallel Branch 6: Surveillance List
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/surveillance`
- **Method:** POST
- **Timeout:** 60 seconds
- **Continue On Fail:** TRUE

#### 9. Check OHLCV Prerequisites (PostgreSQL Query)
- **Type:** Postgres Node
- **Query:**
  ```sql
  SELECT COUNT(*) as active_securities
  FROM securities
  WHERE is_active = TRUE AND updated_at >= CURRENT_DATE;
  ```
- **Branch Logic:** If `active_securities > 2000`, proceed to OHLCV fetch

#### 10. Upstox Daily OHLCV (HTTP Request)
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/daily-ohlcv`
- **Method:** POST
- **Timeout:** 300 seconds (5 minutes for 2000+ symbols)
- **Continue On Fail:** TRUE
- **Dependencies:** Runs AFTER securities branch completes

#### 11. Aggregation Query (PostgreSQL)
- **Type:** Postgres Node
- **Query:**
  ```sql
  SELECT
    source,
    status,
    records_inserted,
    records_updated,
    errors,
    timestamp
  FROM ingestion_logs
  WHERE DATE(timestamp) = CURRENT_DATE
  ORDER BY timestamp DESC;
  ```
- **Output:** JSON array of today's ingestion results

#### 12. Format Summary (Function Node)
- **Type:** Function
- **Code:**
  ```javascript
  const logs = $input.all();
  const summary = {
    date: new Date().toISOString().split('T')[0],
    total_sources: logs.length,
    successful: logs.filter(l => l.json.status === 'success').length,
    failed: logs.filter(l => l.json.status === 'failed').length,
    details: logs.map(l => ({
      source: l.json.source,
      status: l.json.status,
      records: l.json.records_inserted + l.json.records_updated,
      errors: l.json.errors
    }))
  };
  return [{ json: summary }];
  ```

#### 13. Send Notification (Slack/Email)
- **Type:** Slack/Email Node
- **Message Template:**
  ```
  📊 Daily EOD Ingestion Summary - {{ $json.date }}

  ✅ Successful: {{ $json.successful }}/{{ $json.total_sources }}
  ❌ Failed: {{ $json.failed }}/{{ $json.total_sources }}

  Details:
  {{ $json.details }}
  ```

---

## Workflow 2: Upstox Token Refresh Workflow

**Schedule:** Every day at 8:00 AM IST (before market open)
**Trigger:** Cron: `0 8 * * *`
**Duration:** ~30 seconds

### Architecture

```
[Cron Trigger] → [Check Token Expiry] → [If Expired] → [Refresh Token]
                                              ↓
                                      [Log Token Status]
                                              ↓
                                      [Send Alert if Failed]
```

### Nodes

#### 1. Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 8 * * *`
- **Timezone:** Asia/Kolkata

#### 2. Check Token Expiry (HTTP Request)
- **URL:** `http://backend:8000/api/v1/auth/upstox/token-status`
- **Method:** GET
- **Expected Response:**
  ```json
  {
    "active": false,
    "message": "No active token found. Please login."
  }
  ```

#### 3. Refresh Token (HTTP Request)
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/auth/upstox/login`
- **Method:** POST
- **Headers:**
  ```json
  {
    "Content-Type": "application/json"
  }
  ```
- **Body:**
  ```json
  {
    "mobile": "{{ $env.UPSTOX_MOBILE }}",
    "pin": "{{ $env.UPSTOX_PIN }}",
    "totp_secret": "{{ $env.UPSTOX_TOTP_SECRET }}"
  }
  ```
- **Timeout:** 60 seconds
- **Retry:** 3 attempts with 10-second delay

#### 4. Log Token Status (PostgreSQL Insert)
- **Type:** Postgres Node
- **Operation:** Insert
- **Table:** `ingestion_logs`
- **Values:**
  ```json
  {
    "source": "upstox_token_refresh",
    "status": "{{ $json.success ? 'success' : 'failed' }}",
    "records_inserted": 1,
    "errors": "{{ $json.errors }}"
  }
  ```

#### 5. Send Alert if Failed (Slack/Email)
- **Type:** Slack Node
- **Condition:** Only if `$json.success === false`
- **Message:**
  ```
  🚨 Upstox Token Refresh Failed

  Time: {{ $now }}
  Errors: {{ $json.errors }}

  Manual intervention required:
  1. Generate token manually from Upstox dashboard
  2. Insert into database using SQL:
     INSERT INTO upstox_tokens (access_token, expires_at, is_active)
     VALUES ('YOUR_TOKEN', '2025-12-06 23:59:00+05:30', TRUE);
  ```

---

## Workflow 3: Weekly Industry Classification Scraper

**Schedule:** Every Sunday at 10:00 AM IST
**Trigger:** Cron: `0 10 * * 0`
**Duration:** ~5 minutes (Playwright scraping)

### Architecture

```
[Cron Trigger] → [Scrape NSE Industry Data] → [Log Results] → [Send Summary]
```

### Nodes

#### 1. Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 10 * * 0` (Every Sunday)
- **Timezone:** Asia/Kolkata

#### 2. Scrape NSE Industry Data (HTTP Request)
- **URL:** `http://backend:8000/api/v1/ingest/industry-classification`
- **Method:** POST
- **Timeout:** 300 seconds (Playwright automation takes time)
- **Retry:** 2 attempts with 30-second delay

#### 3. Log Results (PostgreSQL)
- **Type:** Postgres Node
- **Query:**
  ```sql
  SELECT
    COUNT(*) as total_classified,
    COUNT(DISTINCT industry) as unique_industries,
    COUNT(DISTINCT sector) as unique_sectors
  FROM industry_classification
  WHERE updated_at >= CURRENT_DATE;
  ```

#### 4. Send Summary (Slack)
- **Type:** Slack Node
- **Message:**
  ```
  📋 Weekly Industry Classification Update

  Total Securities Classified: {{ $json.total_classified }}
  Unique Industries: {{ $json.unique_industries }}
  Unique Sectors: {{ $json.unique_sectors }}
  ```

---

## Workflow 4: Historical OHLCV Backfill Workflow

**Schedule:** Manual trigger only (one-time or on-demand)
**Trigger:** Webhook or manual execution
**Duration:** ~2-3 hours (5 years data for 2000+ securities)

### Architecture

```
[Webhook/Manual Trigger] → [Get All Active Securities] → [Split Into Batches]
                                              ↓
                                    [For Each Batch (50 symbols)]
                                              ↓
                                    [POST /ingest/historical-ohlcv/{symbol}]
                                              ↓
                                    [Wait 2 seconds] (rate limiting)
                                              ↓
                                    [Aggregation Query]
                                              ↓
                                    [Generate Report]
```

### Nodes

#### 1. Webhook Trigger
- **Type:** Webhook
- **Path:** `/webhook/backfill-ohlcv`
- **Method:** POST
- **Authentication:** API Key

#### 2. Get Active Securities (PostgreSQL)
- **Type:** Postgres Node
- **Query:**
  ```sql
  SELECT
    symbol,
    isin,
    listing_date
  FROM securities
  WHERE is_active = TRUE
  ORDER BY symbol;
  ```

#### 3. Split Into Batches (Function Node)
- **Type:** Function
- **Code:**
  ```javascript
  const securities = $input.all().map(item => item.json);
  const batchSize = 50;
  const batches = [];

  for (let i = 0; i < securities.length; i += batchSize) {
    batches.push(securities.slice(i, i + batchSize));
  }

  return batches.map(batch => ({ json: { batch } }));
  ```

#### 4. For Each Batch (Loop Node)
- **Type:** Loop Over Items
- **Input:** Batches from previous node

#### 5. Historical OHLCV Ingestion (HTTP Request)
- **Type:** HTTP Request
- **URL:** `http://backend:8000/api/v1/ingest/historical-ohlcv/{{ $json.symbol }}`
- **Method:** POST
- **Query Parameters:**
  ```json
  {
    "from_date": "{{ $json.listing_date }}",
    "to_date": "{{ $now.format('YYYY-MM-DD') }}"
  }
  ```
- **Timeout:** 60 seconds
- **Continue On Fail:** TRUE

#### 6. Rate Limit Wait (Wait Node)
- **Type:** Wait
- **Duration:** 2 seconds
- **Reason:** Upstox API rate limiting

#### 7. Aggregation Query (PostgreSQL)
- **Type:** Postgres Node
- **Query:**
  ```sql
  SELECT
    COUNT(*) as total_ingested,
    SUM(records_inserted) as total_records,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
  FROM ingestion_logs
  WHERE source LIKE 'historical_ohlcv%'
    AND timestamp >= NOW() - INTERVAL '3 hours';
  ```

#### 8. Generate Report (Function Node)
- **Type:** Function
- **Code:**
  ```javascript
  const stats = $input.first().json;
  const report = {
    execution_date: new Date().toISOString(),
    total_symbols_processed: stats.total_ingested,
    total_records_inserted: stats.total_records,
    failed_symbols: stats.failed_count,
    success_rate: ((stats.total_ingested - stats.failed_count) / stats.total_ingested * 100).toFixed(2) + '%'
  };
  return [{ json: report }];
  ```

#### 9. Save Report (File Write)
- **Type:** Write Binary File
- **File Path:** `/app/logs/backfill_report_{{ $now.format('YYYYMMDD_HHmmss') }}.json`
- **Content:** `{{ $json }}`

---

## Workflow 5: Upstox Instrument Refresh Workflow

**Schedule:** Weekly on Saturday at 11:00 PM IST
**Trigger:** Cron: `0 23 * * 6`
**Duration:** ~3 minutes

### Architecture

```
[Cron Trigger] → [Ingest Instruments] → [Create Mappings] → [Log Stats]
```

### Nodes

#### 1. Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 23 * * 6` (Every Saturday)
- **Timezone:** Asia/Kolkata

#### 2. Ingest Upstox Instruments (HTTP Request)
- **URL:** `http://backend:8000/api/v1/ingest/upstox-instruments`
- **Method:** POST
- **Timeout:** 180 seconds

#### 3. Log Statistics (Slack)
- **Type:** Slack Node
- **Message:**
  ```
  🔄 Upstox Instrument Refresh Complete

  Total Instruments: {{ $json.total_instruments }}
  Inserted: {{ $json.instruments_inserted }}
  Updated: {{ $json.instruments_updated }}
  Mappings Created: {{ $json.mappings_created }}
  ```

---

## Implementation Checklist

### Phase 1.6.1: Setup n8n MCP Server
- [ ] Add n8n API key to environment variables
- [ ] Configure MCP server in Claude Code settings
- [ ] Test MCP connection
- [ ] Enable n8n API authentication

### Phase 1.6.2: Create Backend Endpoints (Missing)
- [ ] `GET /api/v1/health/market-status` - Check if market is open today
- [ ] `POST /api/v1/ingest/daily-ohlcv` - Fetch daily OHLCV for all symbols
- [ ] `POST /api/v1/ingest/historical-ohlcv/{symbol}` - Fetch 5-year historical data

### Phase 1.6.3: Build Workflows
- [ ] Workflow 1: Daily EOD Master (priority)
- [ ] Workflow 2: Upstox Token Refresh (priority)
- [ ] Workflow 3: Weekly Industry Scraper
- [ ] Workflow 4: Historical Backfill (manual)
- [ ] Workflow 5: Instrument Refresh (weekly)

### Phase 1.6.4: Testing
- [ ] Test each workflow manually
- [ ] Test parallel branch failures (simulate NSE downtime)
- [ ] Test OHLCV dependency check
- [ ] Test aggregation queries
- [ ] Test notification delivery

### Phase 1.6.5: Monitoring
- [ ] Set up Slack channel for workflow notifications
- [ ] Configure error alerts
- [ ] Create dashboard for ingestion_logs table
- [ ] Document manual retry procedures

---

## Environment Variables Needed

Add to `.env` and `docker-compose.yml`:

```bash
# n8n API Configuration
N8N_API_KEY=your_generated_api_key_here
N8N_API_URL=http://localhost:5678

# Notification Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url
NOTIFICATION_EMAIL=alerts@yourcompany.com
```

---

## Success Criteria

- ✅ All 5 workflows created and tested
- ✅ Daily EOD workflow runs successfully for 5 consecutive days
- ✅ Token refresh workflow handles expiry automatically
- ✅ Aggregation queries return accurate status
- ✅ Failed branches don't block other sources
- ✅ Notifications sent on success and failure
- ✅ Historical backfill completes for all 2000+ securities
- ✅ Documentation updated with workflow JSON exports

---

## Next Steps After Phase 1.6

1. **Phase 2.1:** Implement calculated metrics (30+ metrics)
2. **Phase 2.2:** Build screener logic (11 screeners)
3. **Phase 2.3:** Create API endpoints for screener results
4. **Phase 3:** Build frontend dashboard
