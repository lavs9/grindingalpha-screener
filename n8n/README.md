# n8n Workflows

This directory contains all n8n workflows for automated data ingestion in the Stock Screener Platform.

## Setup Instructions

### 1. Configure n8n with Database Storage

n8n is configured to use PostgreSQL for workflow storage (persistent across container restarts).

**Access n8n UI:**
```bash
# URL: http://localhost:5678
# Username: admin
# Password: ZEwTRrfdQ+rG8A01/cBqyQ==  (from .env: N8N_BASIC_AUTH_PASSWORD)
```

### 2. Enable API Authentication

n8n API is secured with an API key for webhook and programmatic access.

**API Configuration:**
- **API URL:** http://localhost:5678
- **API Key:** `14bae9852790a601bf822e8eb7146740af7a5f374a824d764215bedbe8846639` (from .env: N8N_API_KEY)

**Test API Access:**
```bash
curl -H "X-N8N-API-KEY: 14bae9852790a601bf822e8eb7146740af7a5f374a824d764215bedbe8846639" \
  http://localhost:5678/api/v1/workflows
```

### 3. MCP Server Configuration

Add to your Claude Code settings (`~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "14bae9852790a601bf822e8eb7146740af7a5f374a824d764215bedbe8846639"
      }
    }
  }
}
```

**Or use the pre-configured file:**
```bash
cp .claude/mcp-config.json ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

### 4. Restart n8n Container

After updating docker-compose.yml and .env:

```bash
docker-compose down
docker-compose up -d n8n
docker-compose logs -f n8n
```

**Verify n8n is using PostgreSQL:**
```bash
# Check logs for "Database type: postgresdb"
docker-compose logs n8n | grep -i database
```

---

## Workflow Implementation Plan

See [.claude/n8n-workflows-plan.md](../.claude/n8n-workflows-plan.md) for detailed specifications.

### Workflows to Implement

1. **Daily EOD Master Workflow** (Priority 1)
   - Schedule: Every weekday at 9:00 PM IST
   - 6 parallel branches: Securities, ETFs, Market Cap, Bulk Deals, Block Deals, Surveillance
   - 1 dependent branch: Upstox Daily OHLCV (runs after securities update)

2. **Upstox Token Refresh Workflow** (Priority 1)
   - Schedule: Every day at 8:00 AM IST
   - Checks token expiry and refreshes if needed

3. **Weekly Industry Classification Scraper**
   - Schedule: Every Sunday at 10:00 AM IST
   - Uses Playwright to scrape NSE website

4. **Historical OHLCV Backfill Workflow**
   - Trigger: Manual/Webhook only
   - Fetches 5 years of data for all 2000+ securities

5. **Upstox Instrument Refresh Workflow**
   - Schedule: Every Saturday at 11:00 PM IST
   - Updates instrument master data (64,699+ instruments)

---

## Importing Workflows

### Method 1: Manual Import via UI
1. Open n8n UI: http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select JSON file from `n8n/workflows/` directory
4. Activate workflow

### Method 2: Using n8n CLI
```bash
# Export workflow
docker exec screener_n8n n8n export:workflow --id=1 --output=/home/node/.n8n/workflows/workflow.json

# Import workflow
docker exec screener_n8n n8n import:workflow --input=/home/node/.n8n/workflows/workflow.json
```

### Method 3: Using MCP Server (Recommended)
Once MCP is configured, use Claude Code to create workflows programmatically.

---

## Exporting Workflows

**Always export workflows after making changes:**

```bash
# Via UI: Workflow → Download
# Save to: n8n/workflows/{workflow-name}.json

# Commit to git
git add n8n/workflows/
git commit -m "feat: Update n8n workflow - {workflow-name}"
```

---

## Testing Workflows

### Test Individual Endpoints

Before creating workflows, verify all backend endpoints work:

```bash
# Test NSE Securities Ingestion
curl -X POST http://localhost:8001/api/v1/ingest/securities

# Test Upstox Token Status
curl http://localhost:8001/api/v1/auth/upstox/token-status

# Test Market Quotes
curl "http://localhost:8001/api/v1/auth/upstox/test-market-quotes?symbol=RELIANCE"
```

### Manual Workflow Execution

1. Open workflow in n8n UI
2. Click "Execute Workflow"
3. Check execution history for errors
4. Review `ingestion_logs` table:
   ```sql
   SELECT * FROM ingestion_logs ORDER BY timestamp DESC LIMIT 20;
   ```

### Test Parallel Execution

1. Simulate NSE downtime by temporarily blocking NSE URLs
2. Verify other branches continue execution
3. Check `Continue On Fail: TRUE` is set on all HTTP nodes

---

## Monitoring & Alerts

### Slack Integration (Optional)

Add Slack webhook URL to `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Configure Slack node in workflows:
- Daily EOD summary
- Token refresh failures
- Backfill completion reports

### Email Notifications (Optional)

Configure SMTP in n8n:
1. Settings → Community Nodes → Install `n8n-nodes-email`
2. Add SMTP credentials
3. Add email nodes to workflows

### Database Monitoring

Query ingestion status:
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

---

## Troubleshooting

### n8n Container Won't Start

**Check logs:**
```bash
docker-compose logs n8n
```

**Common issues:**
1. **PostgreSQL schema not created:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS n8n;
   GRANT ALL PRIVILEGES ON SCHEMA n8n TO screener_user;
   ```

2. **Missing environment variables:**
   ```bash
   docker-compose config | grep -A 20 n8n
   ```

3. **Port conflict:**
   ```bash
   lsof -i :5678
   # Kill conflicting process or change port in docker-compose.yml
   ```

### Workflow Execution Failures

1. **Check backend is running:**
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

2. **Check database connectivity:**
   ```bash
   docker exec screener_n8n nc -zv postgres 5432
   ```

3. **Check Upstox token expiry:**
   ```bash
   curl http://localhost:8001/api/v1/auth/upstox/token-status
   ```

### API Key Not Working

1. **Verify API key in .env:**
   ```bash
   grep N8N_API_KEY .env
   ```

2. **Restart n8n:**
   ```bash
   docker-compose restart n8n
   ```

3. **Test with curl:**
   ```bash
   curl -H "X-N8N-API-KEY: YOUR_KEY" http://localhost:5678/api/v1/workflows
   ```

---

## Missing Backend Endpoints

The following endpoints need to be implemented before workflows can run:

### 1. Market Status Endpoint
```
GET /api/v1/health/market-status

Response:
{
  "is_market_open": false,
  "is_trading_day": true,
  "current_time": "2025-12-06T21:00:00+05:30",
  "next_open": "2025-12-09T09:15:00+05:30",
  "message": "Market closed for the day"
}
```

**IMPORTANT for n8n workflows:**
- Daily EOD workflow runs at **9 PM IST** (AFTER market close)
- **Check `is_trading_day` field, NOT `is_market_open`**
- `is_trading_day === false` → Skip workflow (holiday/weekend)
- `is_trading_day === true` → Run workflow (market was open today)

**Field Meanings:**
- `is_market_open`: Currently open (9:15 AM - 3:30 PM IST) - **false at 9 PM**
- `is_trading_day`: Market was open today (excludes weekends/holidays) - **true at 9 PM on trading days**

### 2. Daily OHLCV Endpoint
```
POST /api/v1/ingest/daily-ohlcv

Request Body (optional):
{
  "symbols": ["RELIANCE", "TCS", "INFY"]  // If empty, fetch all active securities
}

Response:
{
  "success": true,
  "total_symbols": 2200,
  "successful": 2150,
  "failed": 50,
  "errors": [...]
}
```

### 3. Historical OHLCV Endpoint
```
POST /api/v1/ingest/historical-ohlcv/{symbol}

Query Parameters:
- from_date: YYYY-MM-DD (optional, defaults to 5 years ago or listing_date)
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

**Implementation priority:** Create these endpoints before building workflows.

---

## Best Practices

1. **Always use `Continue On Fail: TRUE`** on parallel branches
2. **Set appropriate timeouts** (60-300 seconds depending on operation)
3. **Add retry logic** for critical operations (3 retries with exponential backoff)
4. **Log all operations** to `ingestion_logs` table
5. **Use database aggregation** instead of n8n variables for status tracking
6. **Test manually** before scheduling
7. **Export workflows** after every change
8. **Version control** all workflow JSON files

---

## Next Steps

1. **Restart n8n** with new configuration:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Verify n8n setup:**
   - Access UI at http://localhost:5678
   - Login with credentials from .env
   - Check database connection in logs

3. **Implement missing backend endpoints** (see above)

4. **Create first workflow** (Upstox Token Refresh - simplest)

5. **Test workflow execution** manually

6. **Enable scheduling** after successful tests

7. **Set up monitoring** (Slack/Email notifications)
