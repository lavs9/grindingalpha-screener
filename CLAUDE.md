# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Indian stock market screener platform that aggregates data from NSE (National Stock Exchange) and Upstox API to identify trading opportunities using advanced technical analysis. The project is in **Phase 1: Data Storage & Infrastructure** phase.

**Key Architecture:**
- **Backend:** FastAPI + PostgreSQL + SQLAlchemy ORM
- **Orchestration:** n8n workflows for data pipeline automation
- **Deployment:** Docker Compose (local containers)
- **Data Sources:** NSE Archives (CSV/ZIP), NSE website (JSON with cookie auth), Upstox API (REST SDK), Manual uploads

**Project Structure:**
```
/screener
├── .claude/                    # Planning & architecture docs
├── CLAUDE.md                   # This file
├── CONTRIBUTING.md             # Coding standards & guidelines
├── docker-compose.yml          # Multi-container orchestration
├── .env                        # Environment variables (gitignored)
│
├── backend/                    # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                # Application entry point
│   ├── alembic/               # Database migrations
│   └── app/
│       ├── api/v1/            # API route handlers
│       ├── core/              # Configuration (settings from .env)
│       ├── database/          # DB session & base
│       ├── models/            # SQLAlchemy models (11 tables)
│       ├── schemas/           # Pydantic request/response models
│       ├── services/          # Business logic (nse/, upstox/, calculators/)
│       └── utils/             # Validators, date utils, logging
│
├── n8n/                        # Workflow orchestration
│   └── workflows/             # JSON workflow exports
│       ├── daily_eod_master.json
│       ├── historical_backfill.json
│       └── weekly_industry_scraper.json
│
├── frontend/                   # Dashboard (Phase 3)
├── scripts/                    # Database & deployment scripts
├── logs/                       # Application logs (gitignored)
└── documentation/             # Screener specifications
```

**NOTE:** Current codebase has `screener_project/` folder. Phase 0 will reorganize into `backend/` and `n8n/` structure as shown above.

## Before Writing Code

**📖 Read [CONTRIBUTING.md](CONTRIBUTING.md) first** - It contains essential coding standards, validation rules, testing requirements, and common pitfalls to avoid.

## Critical Development Rules

### 1. File Format Documentation System
**ALWAYS check [.claude/file-formats.md](.claude/file-formats.md) before creating parsers or data models.**

This file contains exact specifications for all external data sources:
- NSE CSV formats (EQUITY_L.csv, MCAP_*.csv, etc.)
- Upstox API response structures
- Column names, data types, validation rules
- Sample file locations in `.claude/samples/`

**Example workflow:**
1. Read `.claude/file-formats.md` → Find "NSE Equity List" specification
2. Check `.claude/samples/EQUITY_L_sample.csv` → See actual data
3. Write parser matching exact column names and types

### 2. Database Schema Reference
The complete database schema with 11 tables is defined in [.claude/Architecture.md](.claude/Architecture.md) Section 3.

**Key tables:**
- **Master tables:** `securities`, `indices`, `industry_classification`, `market_holidays`
- **Time-series:** `ohlcv_daily`, `market_cap_history`, `calculated_metrics`
- **Events:** `bulk_deals`, `block_deals`, `surveillance_list`
- **Metadata:** `index_constituents`, `ingestion_logs`

**Partitioning:** Phase 1 uses NO partitioning. Monthly partitioning strategy is documented in Architecture.md Section 11 for future implementation (Phase 2+, when >10M records).

### 3. n8n Workflow Pattern - Independent Parallel Execution
All n8n workflows use **database-driven aggregation** pattern (Architecture.md Section 5.2.1):

**Critical workflow config:**
- Each parallel branch has `Continue On Fail: TRUE` (failures don't block other branches)
- No data passed between branches (independent execution)
- All results logged to `ingestion_logs` table
- Aggregation step queries database, not n8n workflow state

**Example:** Daily EOD workflow has 6 parallel branches (NSE securities, ETFs, market cap, bulk deals, block deals, surveillance). If NSE market cap fails, other 5 sources still complete successfully.

### 4. Implementation Plan Reference
Follow phased implementation in [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md):

**Phase 0:** Docker setup, environment config, project structure
**Phase 1.1-1.6:** Data sources (NSE, Upstox, n8n workflows)
**Phase 2+:** Screeners, metrics calculation, frontend

Each phase has clear tasks, dependencies, and success criteria.

## Commands

### Development (Current - Phase 0)

**Start the application (legacy structure):**
```bash
cd screener_project
source venv/bin/activate  # Activate virtual environment
uvicorn main:app --reload
```

### Development (After Phase 0 Reorganization)

**Using Docker Compose (recommended):**
```bash
# Build and start all services (postgres, backend, n8n)
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f n8n

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build backend
```

**Local development (backend only):**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI with hot reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Access points:**
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **n8n UI:** http://localhost:5678

### n8n Workflows

**Import workflows:**
1. Open n8n UI: http://localhost:5678
2. Go to Workflows → Import from File
3. Select JSON files from `n8n/workflows/`

**Manual workflow execution:**
```bash
# Trigger Daily EOD workflow via n8n UI
# OR call backend endpoints directly:
curl -X POST http://localhost:8000/api/v1/ingest/securities
curl -X POST http://localhost:8000/api/v1/ingest/market-cap
curl -X POST http://localhost:8000/api/v1/ingest/daily-ohlcv
```

**Export workflows:**
- n8n UI → Workflow → Download
- Save to `n8n/workflows/` directory
- Commit to git (workflows are version-controlled)

### Database

**Connect to PostgreSQL (Docker):**
```bash
docker exec -it screener_postgres psql -U screener_user -d screener_db
```

**Run migrations:**
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

**Database backup/restore:**
```bash
# Backup
docker exec screener_postgres pg_dump -U screener_user screener_db > backup.sql

# Restore
docker exec -i screener_postgres psql -U screener_user screener_db < backup.sql
```

**Query ingestion status:**
```sql
-- Check recent ingestion logs
SELECT source, status, records_inserted, timestamp
FROM ingestion_logs
ORDER BY timestamp DESC
LIMIT 20;

-- Check today's data
SELECT COUNT(*) FROM ohlcv_daily WHERE date = CURRENT_DATE;
SELECT COUNT(*) FROM securities WHERE is_active = TRUE;
```

### Environment Setup

**Initial setup (Phase 0):**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - Database password
# - Upstox API key/secret/token
# - n8n encryption key

# Start services
docker-compose up -d
```

## Architecture Highlights

### Database Schema Principles
- **Foreign keys:** Used selectively (not enforced on `ohlcv_daily.symbol` for flexibility)
- **Composite unique constraints:** Prevent duplicates (e.g., `symbol` + `date`)
- **Indexes:** Optimized for screener queries (symbol+date DESC, metric columns)
- **Data validation:** CHECK constraints for price relationships (high >= low, open/close within range)
- **Upstox mapping tables:** 3 additional tables for token storage, instrument cache, and symbol-to-instrument mappings

### Upstox Integration Architecture
- **Token Management:** Database-backed storage with 23:59 IST daily expiry
  - Table: `upstox_tokens` (access_token, expires_at, is_active)
  - Service: `UpstoxTokenManager` with timezone-aware expiry checks
- **Instrument Mapping:** Full ingestion (64,699 instruments) with auto-mapping
  - Table: `upstox_instruments` (instrument_key, exchange, symbol, ISIN)
  - Table: `symbol_instrument_mapping` (security_id → instrument_id with confidence scores)
  - Matching logic: ISIN-based (100% confidence) or symbol-based (90% confidence)
- **Authentication:** Playwright-based OAuth automation with manual fallback
  - Endpoint: `POST /api/v1/auth/upstox/login` (mobile + PIN + TOTP)
  - Workaround: Manual token refresh (OAuth redirect timeout issue)
- **Test Endpoints:** Comprehensive validation suite
  - `/api/v1/auth/upstox/test-api` (user profile)
  - `/api/v1/auth/upstox/test-market-quotes` (live quotes)
  - `/api/v1/auth/upstox/test-historical-data` (OHLCV data)
  - `/api/v1/auth/upstox/test-market-holidays` (holiday calendar)

### Data Ingestion Workflow
1. **n8n workflow** triggers FastAPI endpoints via HTTP POST
2. **FastAPI endpoints** (`/api/v1/ingest/*`) receive data
3. **Service layer** fetches from external sources (NSE, Upstox)
4. **Validators** check data quality (regex, constraints, completeness)
5. **SQLAlchemy ORM** inserts/updates database (UPSERT for idempotency)
6. **Ingestion logs** table tracks success/failure for aggregation

### Current vs. Planned Features

**Currently Implemented (Phase 0-1.5 completed):**
- ✅ FastAPI application with environment-based configuration (.env)
- ✅ Docker Compose deployment (postgres, backend, n8n)
- ✅ All 11 database tables + 3 Upstox tables (14 total)
- ✅ NSE data ingestion (8 sources):
  - Securities list (EQUITY_L.csv)
  - ETF list (ETF_L.csv)
  - Market cap history (MCAP_*.csv)
  - Bulk deals and block deals
  - Surveillance lists
  - Industry classification (Playwright scraper)
  - Index constituents (manual upload)
- ✅ Upstox integration:
  - Database-backed token storage (23:59 IST expiry)
  - Instrument master data (64,699 instruments)
  - Symbol-to-instrument auto-mapping (87.5% success)
  - Authentication endpoints (OAuth + manual fallback)
  - Test endpoints (quotes, historical data, holidays)
- ✅ Data validation framework (Pydantic schemas + validators)
- ✅ Alembic migrations for schema versioning
- ⏳ n8n workflows (planned for Phase 1.6)

**Planned in Phase 1.6 (In Progress):**
- Daily EOD workflow automation
- Weekly industry classification refresh
- Historical backfill workflow
- Upstox token refresh workflow

**Planned in Phase 2:**
- 11 screeners (RRG charts priority)
- 30+ calculated metrics daily
- Frontend dashboard

## Key Data Sources

### NSE Archives (CSV Downloads)
- Securities list: https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
- ETF list: https://nsearchives.nseindia.com/content/equities/ETF_L.csv
- Market cap: https://nsearchives.nseindia.com/content/CM/MCAP_*.csv
- Bulk deals, block deals, surveillance: Various NSE URLs (see file-formats.md)

### NSE Website (JSON with Cookie Auth)
- Industry classification: Requires Playwright automation for cookie management
- See Architecture.md Section 6.2.2 for implementation details

### Upstox API
**Authentication:**
- OAuth2 flow: Playwright automation (mobile + PIN + TOTP)
- Token storage: Database table `upstox_tokens` with 23:59 IST daily expiry
- Token retrieval: `UpstoxTokenManager.get_active_token()` with automatic expiry detection
- Manual refresh: Direct database insert as fallback (OAuth redirect timeout issue)

**Instrument Master:**
- Source: https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz
- Format: Gzipped JSON (64,699+ instruments)
- Ingestion: UPSERT on `instrument_key` (batch size: 500)
- Mapping: Auto-create via ISIN (100% confidence) or symbol (90% confidence)

**Market Data Endpoints:**
- Historical OHLCV: `/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}`
- Daily quotes: `/v2/market-quote/quotes?instrument_key={key}`
- Market holidays: `/v2/market/holidays/{date}`
- User profile: `/v2/user/profile` (for token validation)

**Test Endpoints (Backend):**
- `GET /api/v1/auth/upstox/token-status` - Check active token
- `GET /api/v1/auth/upstox/test-api` - Verify token validity
- `GET /api/v1/auth/upstox/test-market-quotes?symbol=RELIANCE` - Live quotes
- `GET /api/v1/auth/upstox/test-historical-data?symbol=RELIANCE` - 30-day OHLCV
- `GET /api/v1/auth/upstox/test-market-holidays?date=2025-12-04` - Holiday calendar

## Important Notes

### Security
- ✅ Database credentials migrated to .env file (Phase 0 completed)
- ✅ Upstox API credentials in environment variables (UPSTOX_API_KEY, UPSTOX_API_SECRET, etc.)
- ✅ Token storage secured in database (not in environment variables)
- ⚠️ Never commit `.env` files or API credentials to git
- ⚠️ Ensure `.env` has no spaces around equals signs (`KEY=value`, not `KEY = value`)

### Data Volume
- Universe: 2,000+ securities (all NSE equities + ETFs)
- Historical data: 5 years OHLCV
- Expected Phase 1 data: ~5-10M time-series records
- PostgreSQL is sufficient for Phase 1; ClickHouse migration planned for >10M records

### Screener Specifications
All 11 planned screeners are documented in [documentation/screeners-idea.md](documentation/screeners-idea.md):
1. RRG Charts (Relative Rotation Graphs) - **Priority #1**
2. 4% Breakout Stocks
3. 20% Weekly Move Stocks
4. Market Breadth Metrics
5. Strongest/Weakest Performers
6. VCP (Volatility Contraction Pattern)
7. Stage Analysis
8. ATR Extension Analysis
9. Institutional Activity Tracker
10. Sector Rotation Heatmap
11. Gap Analysis

### Common Gotchas
- **NSE data dates:** Use format `DD-MMM-YYYY` (e.g., "29-NOV-1977")
- **Upstox dates:** Use format `YYYY-MM-DD` (e.g., "2024-01-15")
- **Market cap units:** NSE reports in ₹ crore (store as-is, don't convert)
- **ISIN validation:** Must start with "IN" and be exactly 12 characters
- **Symbol naming:** NSE allows `&` and `-` in symbols (e.g., "M&M", "L&T")
- **Upstox exchange filter:** Use `exchange='NSE'` with `instrument_type='EQ'` (NOT `exchange='NSE_EQ'`)
- **Upstox instrument_key format:** `NSE_EQ|INE002A01018` (exchange_instrument_type|ISIN)
- **Environment file formatting:** No spaces around equals (`KEY=value`, not `KEY = value`)
- **Token expiry:** Upstox tokens expire at 23:59 IST daily (not UTC, not midnight)
- **Mapping confidence:** 100% = ISIN match, 90% = symbol-only match, lower = manual review needed

## Testing Approach

**Current state:** No test framework set up

**Planned (Phase 0):**
- Unit tests with pytest
- Sample files in `.claude/samples/` for parser testing
- Database fixtures for integration tests

**Example test pattern:**
```python
def test_equity_parser():
    # Use sample file from .claude/samples/EQUITY_L_sample.csv
    sample_path = ".claude/samples/EQUITY_L_sample.csv"
    result = parse_equity_list(sample_path)
    assert result["success"] == True
    assert len(result["data"]) > 0
```

## Related Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Coding standards, development practices, and contribution guidelines (READ THIS FIRST before writing code)
- **[.claude/PRD.md](.claude/PRD.md)** - Complete product requirements (objectives, scope, user stories)
- **[.claude/Architecture.md](.claude/Architecture.md)** - System architecture (database schema, n8n workflows, Docker setup)
- **[.claude/Implementation-Plan.md](.claude/Implementation-Plan.md)** - Phased implementation plan (6-8 weeks, detailed tasks)
- **[.claude/file-formats.md](.claude/file-formats.md)** - Data source format specifications (MUST reference before parsing)
- **[.claude/UPDATES.md](.claude/UPDATES.md)** - Summary of design decisions and changes
- **[documentation/screeners-idea.md](documentation/screeners-idea.md)** - All 11 screener specifications

## Current Development Status

**Last Updated:** 2025-12-04

**Current Phase:** Phase 1.3 completed - Upstox Integration

**Completed Phases:**
- ✅ **Phase 0:** Docker Compose environment setup
- ✅ **Phase 1.1:** Database models and migrations (11 tables)
- ✅ **Phase 1.2:** NSE data ingestion (securities, ETFs, market cap, bulk/block deals, surveillance)
- ✅ **Phase 1.3:** Upstox authentication, instrument mapping, and API integration
- ✅ **Phase 1.4:** NSE Industry Classification scraping
- ✅ **Phase 1.5:** Index Constituents management

**Recent Changes (Phase 1.3):**
- Implemented database-backed Upstox token storage (23:59 IST expiry)
- Created Playwright-based OAuth automation with manual fallback
- Ingested 64,699 instruments from Upstox NSE.json.gz
- Auto-mapped 1,924 securities to instrument keys (87.5% success rate, 100% confidence via ISIN)
- Created comprehensive test endpoints for validation (quotes, historical data, holidays)
- Fixed exchange filter bug (`NSE_EQ` → `NSE` with `instrument_type='EQ'`)

**Next Steps:**
- Phase 1.6: Create n8n workflows for automated daily data ingestion
  - Daily EOD workflow (6 parallel branches: securities, ETFs, market cap, deals, surveillance, OHLCV)
  - Weekly industry classification scraper
  - Historical backfill workflow
  - Upstox token refresh workflow (daily 8 AM)
- Phase 2: Implement 11 screeners with calculated metrics
