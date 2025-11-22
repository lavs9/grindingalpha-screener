# n8n Workflow Setup

## Initial Setup

1. **Access n8n UI**: http://localhost:5678
2. **Create account** (local n8n instance - use any email/password)
3. **Configure timezone**: Settings → General → Timezone → Asia/Kolkata

## Workflow Import

1. Go to **Workflows** → **Import from File**
2. Select JSON files from `n8n/workflows/` directory
3. Available workflows (will be created in Phase 1.5):
   - `daily_eod_master.json` - Daily EOD data ingestion
   - `historical_backfill.json` - One-time historical data backfill
   - `weekly_industry_scraper.json` - Weekly industry classification update

## Workflow Configuration

Each workflow requires:

- **HTTP Request nodes** pointing to: `http://backend:8000/api/v1/ingest/*`
- **Cron triggers** for scheduling (configured in workflow)
- **Error handling** configured (Continue On Fail: TRUE for parallel branches)

### Backend API Endpoints

Workflows will call these endpoints:

- `POST /api/v1/ingest/securities` - Fetch NSE securities list
- `POST /api/v1/ingest/etfs` - Fetch NSE ETF list
- `POST /api/v1/ingest/market-cap` - Fetch market cap data
- `POST /api/v1/ingest/bulk-deals` - Fetch bulk deals
- `POST /api/v1/ingest/block-deals` - Fetch block deals
- `POST /api/v1/ingest/surveillance` - Fetch surveillance measures
- `POST /api/v1/ingest/daily-ohlcv` - Fetch daily OHLCV from Upstox
- `POST /api/v1/ingest/industry-classification` - Scrape industry data

## Testing Workflows

1. **Manual execution**: Click "Execute Workflow" button in n8n UI
2. **Check backend logs**: `docker-compose logs -f backend`
3. **Query database**: Check `ingestion_logs` table for results
   ```sql
   SELECT source, status, records_inserted, timestamp
   FROM ingestion_logs
   ORDER BY timestamp DESC
   LIMIT 10;
   ```

## Workflow Schedules

- **Daily EOD**: Mon-Fri at 8:30 PM IST (after market closes at 3:30 PM)
- **Weekly Industry**: Sundays at 10:00 PM IST
- **Historical Backfill**: Manual trigger only

## Troubleshooting

### Workflow fails to connect to backend
- Verify backend container is running: `docker ps`
- Check network connectivity: Use `http://backend:8000` (not `localhost`)
- View backend logs: `docker-compose logs -f backend`

### Data not appearing in database
- Check backend API response in n8n execution logs
- Query `ingestion_logs` table for error details
- Manually test endpoint: `curl -X POST http://localhost:8000/api/v1/ingest/securities`

### Manual retry for failed sources
If a specific data source fails, you can retry it manually:
```bash
# Securities
curl -X POST http://localhost:8000/api/v1/ingest/securities

# Market cap
curl -X POST http://localhost:8000/api/v1/ingest/market-cap

# Daily OHLCV
curl -X POST http://localhost:8000/api/v1/ingest/daily-ohlcv
```

## Next Steps (Phase 1.5)

1. Create Daily EOD Master workflow with 6 parallel branches
2. Create Weekly Industry Classification workflow
3. Create Historical Backfill workflow with batch processing
4. Export workflows as JSON to this directory
5. Test all workflows and verify data ingestion

## References

- n8n Documentation: https://docs.n8n.io
- Backend API Docs: http://localhost:8000/docs
- Architecture Details: See `.claude/Architecture.md` Section 5
