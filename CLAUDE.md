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
├── frontend/                   # Next.js + Shadcn/ui dashboard (Phase 2 - In Planning)
├── scripts/                    # Database & deployment scripts
├── logs/                       # Application logs (gitignored)
└── documentation/             # Screener specifications
```

**NOTE:** Current codebase has `screener_project/` folder. Phase 0 will reorganize into `backend/` and `n8n/` structure as shown above.

## Before Writing Code

**📖 Read [CONTRIBUTING.md](CONTRIBUTING.md) first** - It contains essential coding standards, validation rules, testing requirements, and common pitfalls to avoid.

## Git Workflow - Branch-Based Development

**CRITICAL: Always work on feature branches, NEVER commit directly to master.**

### Branch Naming Convention
```
feature/{phase}-{description}  # For backend features
frontend/{phase}-{description} # For frontend features (Phase 3+)
bugfix/{issue-description}     # For bug fixes
refactor/{component-name}      # For refactoring
docs/{update-description}      # For documentation

Examples:
Backend (Phase 1-2):
- feature/phase-1.6-data-quality-endpoints
- feature/phase-2-rrg-screener
- bugfix/ohlcv-duplicate-records
- refactor/upstox-token-service

Frontend (Phase 3):
- frontend/phase-3-initial-setup
- frontend/phase-3-screener-tables
- frontend/phase-3-rrg-charts
- frontend/phase-3-dashboard-layout
```

### Frontend Development Branch Strategy (Phase 3)

**IMPORTANT: All frontend work MUST be done on `frontend/*` branches.**

Frontend development follows a separate branch strategy to isolate UI changes from backend:

1. **Base Branch:** All frontend branches start from `master`
2. **Branch Prefix:** Use `frontend/phase-3-{feature-name}` format
3. **Integration:** Frontend branches merge back to master only when feature is complete and tested
4. **Isolation:** Frontend and backend can be developed in parallel without conflicts

**Frontend Branch Workflow:**
```bash
# 1. Start new frontend feature
git checkout master
git pull origin master
git checkout -b frontend/phase-3-screener-tables

# 2. Work on frontend, commit regularly
cd frontend
pnpm dev  # Start dev server
# Make changes...
git add .
git commit -m "feat: Implement screener data tables"

# 3. Push to remote
git push origin frontend/phase-3-screener-tables

# 4. Create Pull Request on GitHub
# 5. After testing & approval, merge to master
# 6. Delete branch
git checkout master
git pull origin master
git branch -d frontend/phase-3-screener-tables
git push origin --delete frontend/phase-3-screener-tables
```

**Why Separate Frontend Branches:**
- Backend APIs are stable (Phase 2 complete)
- Frontend can iterate rapidly without affecting backend
- Easy rollback if UI changes need revision
- Clear separation in git history

### Development Workflow

**Before starting any work:**
```bash
# 1. Ensure master is up to date
git checkout master
git pull origin master

# 2. Create feature branch
git checkout -b feature/phase-1.6-data-quality-endpoints

# 3. Make changes, commit regularly
git add .
git commit -m "feat: Add data quality endpoint"

# 4. Push feature branch to remote
git push origin feature/phase-1.6-data-quality-endpoints

# 5. Create Pull Request on GitHub
# 6. After PR approval, merge to master (via GitHub UI)
# 7. Delete feature branch locally and remotely
git checkout master
git pull origin master
git branch -d feature/phase-1.6-data-quality-endpoints
git push origin --delete feature/phase-1.6-data-quality-endpoints
```

**NEVER do this:**
```bash
# ❌ WRONG - Direct commit to master
git checkout master
git add .
git commit -m "changes"
git push origin master
```

**Always do this:**
```bash
# ✅ CORRECT - Feature branch workflow
git checkout -b feature/my-feature
git add .
git commit -m "feat: Add my feature"
git push origin feature/my-feature
# Then create Pull Request on GitHub
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation updates
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): Add data quality endpoint

Implement GET /api/v1/status/data-quality endpoint to check
data completeness, missing dates, and outliers.

Closes #45

---

fix(upstox): Handle token expiry edge case

Fixed issue where tokens expiring at exactly 23:59 IST were
not being detected as expired.

Closes #78

---

refactor(services): Extract OHLCV ingestion logic

Move common OHLCV ingestion logic from individual services
to BatchHistoricalService for better code reuse.
```

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
# - Supabase URL and Anon Key (Phase 2)

# Start services
docker-compose up -d
```

### Backend Screeners Development (Phase 2)

**Start backend with hot reload:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Calculate metrics manually:**
```bash
# Via API endpoint
curl -X POST "http://localhost:8000/api/v1/metrics/calculate-daily"

# Or via n8n UI (after Phase 1.5 workflows deployed)
# Open http://localhost:5678, execute "Daily_Metrics_Calculation" workflow
```

**Access screener endpoints:**
```bash
# Example: RRG Charts
curl -X POST "http://localhost:8000/api/v1/screeners/rrg"

# Example: 4% Breakouts with filters
curl -X POST "http://localhost:8000/api/v1/screeners/breakouts-4percent?min_change=4.0&min_rvol=1.5"

# See all endpoints at http://localhost:8000/docs
```

### Frontend Development (Phase 3)

**Local development:**
```bash
cd frontend
npm install
npm run dev
```

**Access points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Supabase Dashboard: https://[project-id].supabase.co

**Build for production:**
```bash
cd frontend
npm run build
npm run start  # Production server
```

**Shadcn components (add as needed):**
```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add data-table
npx shadcn@latest add dialog
# See .claude/plans/phase-3-frontend-technical-specs.md for full list
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

**OHLCV Ingestion Endpoints (Backend):**
- `POST /api/v1/ingest/historical-ohlcv-batch` - Batch historical OHLCV data ingestion
  - Query params: `symbols` (optional list), `start_date` (default: 5 years ago), `end_date` (default: yesterday), `batch_size` (default: 50)
  - Returns: `{symbols_processed, records_inserted, records_updated, symbols_failed, errors, execution_time_ms}`
  - Example: `curl -X POST "http://localhost:8001/api/v1/ingest/historical-ohlcv-batch?symbols=RELIANCE&symbols=TCS"`

- `POST /api/v1/ingest/daily-ohlcv` - Daily OHLCV data ingestion
  - Query params: `symbols` (optional list), `target_date` (default: yesterday), `batch_size` (default: 50)
  - Returns: `{symbols_processed, records_inserted, records_updated, symbols_failed, errors, execution_time_ms}`
  - Example: `curl -X POST "http://localhost:8001/api/v1/ingest/daily-ohlcv"`

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

## Frontend Development Guidelines (Phase 3)

### Screenshot & Debugging Workflow

**For sharing UI issues, console errors, or layout problems:**

1. **Screenshot Method:** Save screenshots to `/tmp/` directory
   ```bash
   # Example: Take screenshot and save as
   /tmp/screenshot.png
   /tmp/console-error.png
   /tmp/layout-issue.png
   ```

2. **Share with Claude:** Provide the path in conversation
   ```
   "Check /tmp/screenshot.png - the table columns are misaligned"
   "See console error at /tmp/console-error.png"
   ```

3. **Chrome DevTools MCP:** Installed for automated debugging
   - Claude can read console errors directly via MCP
   - Network request inspection
   - DOM element inspection
   - Real-time error detection

**Best Practices:**
- Clear `/tmp/` old screenshots before new sessions
- Use descriptive filenames (e.g., `/tmp/rrg-chart-rendering-issue.png`)
- For complex issues, share multiple screenshots with context
- Console errors are automatically captured via Chrome MCP when dev server is running

### Frontend Tech Stack (Phase 3)

**Framework & UI:**
- **Next.js 14+** (App Router, Server Components)
- **Shadcn/ui** (Mira preset, Zinc theme, JetBrains Mono font)
- **TailwindCSS** (Utility-first styling)
- **Lucide Icons** (Icon library)

**Data & State:**
- **TanStack Table v8** (Data tables with sorting, filtering, pagination)
- **TanStack Query** (Server state management, caching)
- **Zustand** (Client state management)

**Charts:**
- **TradingView Lightweight Charts** (OHLCV candlestick charts)
- **Plotly.js** (RRG scatter plots, heatmaps)
- **Recharts** (Simple bar/line charts for breadth metrics)

**Authentication (Deferred):**
- **Supabase Auth** (Email OTP, Google, GitHub OAuth)
- Not implemented in initial setup - focus on screener functionality first

**Package Manager:**
- **pnpm** (Fast, efficient, strict dependencies)

**Shadcn Configuration:**
```json
{
  "preset": "base",
  "style": "mira",
  "baseColor": "zinc",
  "theme": "zinc",
  "iconLibrary": "lucide",
  "font": "jetbrains-mono",
  "menuAccent": "subtle",
  "menuColor": "default",
  "radius": "small",
  "template": "next"
}
```

## Testing Approach

**Backend (Phase 1-2):**
- No test framework currently
- Planned: pytest for unit tests, database fixtures

**Frontend (Phase 3):**
- **Component Testing:** Vitest + React Testing Library
- **E2E Testing:** Playwright (deferred to post-MVP)
- **Visual Testing:** Manual via screenshot sharing to `/tmp/`

## Related Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Coding standards, development practices, and contribution guidelines (READ THIS FIRST before writing code)
- **[.claude/PRD.md](.claude/PRD.md)** - Complete product requirements (objectives, scope, user stories)
- **[.claude/Architecture.md](.claude/Architecture.md)** - System architecture (database schema, n8n workflows, Docker setup)
- **[.claude/Implementation-Plan.md](.claude/Implementation-Plan.md)** - Master implementation plan (Phases 1-3 overview with links to detailed plans)
- **[.claude/file-formats.md](.claude/file-formats.md)** - Data source format specifications (MUST reference before parsing)
- **[.claude/UPDATES.md](.claude/UPDATES.md)** - Summary of design decisions and changes
- **[documentation/screeners-idea.md](documentation/screeners-idea.md)** - All 11 screener specifications

**Phase-Specific Plans:**
- **[.claude/plans/phase-2-backend-screeners.md](.claude/plans/phase-2-backend-screeners.md)** - Phase 2 detailed plan (6 weeks, backend screeners implementation)
- **[.claude/plans/phase-3-frontend-technical-specs.md](.claude/plans/phase-3-frontend-technical-specs.md)** - Phase 3 technical specifications (67 pages - frontend architecture, database schemas, code examples)
- **[.claude/plans/implementation-roadmap-phases-2-3.md](.claude/plans/implementation-roadmap-phases-2-3.md)** - Phase 2-3 execution roadmap (day-by-day timeline)

## Current Development Status

**Last Updated:** 2025-12-25

**Current Phase:** Phase 2 - Backend Screeners (Planning Complete) 📋

**Completed Phases:**
- ✅ **Phase 0:** Docker Compose environment setup (November 29, 2025)
- ✅ **Phase 0.6:** PostgreSQL 17 + Resource Monitoring Setup (December 12, 2025)
- ✅ **Phase 1:** Data Storage & Infrastructure (Complete)
  - ✅ **Phase 1.1:** Database models and migrations (14 tables: 11 core + 3 Upstox)
  - ✅ **Phase 1.2:** NSE data ingestion (securities, ETFs, market cap, bulk/block deals, surveillance)
  - ✅ **Phase 1.3:** Upstox authentication, instrument mapping, and API integration
  - ✅ **Phase 1.4:** NSE Industry Classification scraping
  - ✅ **Phase 1.5:** n8n Workflows (4 workflows: Daily EOD, Token Refresh, Weekly Industry, Historical Backfill)
  - ✅ **Phase 1.6:** OHLCV Ingestion, Data Quality Monitoring & Structured Logging (December 14, 2025)

**Planned Phases:**
- 📋 **Phase 2:** Backend Screeners (6 weeks)
  - 40+ calculated technical metrics (VARS, ATR%, VCP, Stage Analysis)
  - 11 screener API endpoints (RRG Charts, 4% Breakouts, RS Leaders, etc.)
  - Daily metrics calculation automation
  - See [.claude/plans/phase-2-backend-screeners.md](.claude/plans/phase-2-backend-screeners.md)

- 🔜 **Phase 3:** Frontend Dashboard (5 weeks)
  - Next.js + Shadcn/ui + TanStack Table
  - Supabase authentication (email OTP, Google, GitHub)
  - 11 screener pages with interactive charts
  - Customizable dashboard widgets
  - See [.claude/plans/phase-3-frontend-technical-specs.md](.claude/plans/phase-3-frontend-technical-specs.md)

**Recent Changes (Phase 1.6 - Completed December 14, 2025):**

**OHLCV Ingestion:**
- Created `ingestion_logs` table for tracking all data ingestion operations
- Implemented `POST /api/v1/ingest/historical-ohlcv-batch` endpoint (batch historical OHLCV data)
  - Default: 5 years historical data for all active securities
  - Batch processing: 50 symbols per batch to respect Upstox API rate limits
  - Resource monitoring with `@monitor_resources` decorator
  - Automatic logging to `ingestion_logs` table
- Implemented `POST /api/v1/ingest/daily-ohlcv` endpoint (single-day OHLCV data)
  - Default: Yesterday's data for all active securities
  - Designed for daily automated n8n workflows
  - Batch processing with error handling
- Successfully tested with real Upstox API data (3 symbols, 78 records, 931ms execution time)
- Added `BatchHistoricalService` for reusable OHLCV ingestion logic

**n8n Workflows (Phase 1.5):**
- Fixed `@monitor_resources` async decorator (now using `asyncio.iscoroutinefunction()`)
- Created 4 production-ready workflows:
  1. Daily EOD Data Ingestion (Mon-Fri 8:30 PM IST) - 6 parallel branches + conditional OHLCV
  2. Upstox Token Refresh (Mon-Fri 8:00 AM IST) - Automatic Playwright authentication
  3. Weekly Industry Classification (Sundays 10:00 PM IST) - NSE Quote Equity scraper
  4. Historical Backfill OHLCV (Manual trigger) - 5-year backfill for all securities

**Data Quality & Monitoring (Phase 1.6):**
- Implemented `GET /api/v1/status/data-quality` endpoint:
  - OHLCV coverage metrics (last date, coverage %, missing symbols)
  - Market cap coverage
  - Industry classification coverage
  - Data quality issue detection (invalid OHLCV, negative prices)
  - Actionable recommendations
- Implemented `GET /api/v1/status/ingestion` endpoint:
  - Recent ingestion logs (last 24 hours)
  - Latest status per source
  - Summary by status (success/failure counts)
- Implemented `GET /api/v1/status/is-trading-day` endpoint:
  - Weekend and holiday detection
  - Used by n8n Daily EOD workflow

**Structured Logging:**
- Created `app/core/logging_config.py` with:
  - JSON-formatted file logging (structured logs)
  - Rotating file handler (10MB per file, 10 backups)
  - Separate error log (ERROR and CRITICAL only)
  - Console logging with human-readable format
  - Module-specific log levels
- Integrated logging in main.py (startup/shutdown events)
- Added `logs/` directory to .gitignore

**Next Steps - Phase 2 (Frontend):**
- 📋 **Phase 2.0-2.8:** Frontend implementation (6 weeks)
  - Next.js 14+ with Shadcn/ui components
  - Supabase authentication (email OTP, Google, GitHub)
  - 11 screener pages with data tables and charts
  - Customizable dashboard with React Grid Layout
  - TradingView Lightweight Charts (OHLCV)
  - Plotly.js (RRG charts, heatmaps)
  - Vercel deployment + Docker local dev
  - See [Phase 3 technical specs](.claude/plans/phase-3-frontend-technical-specs.md) for complete architecture

**Next Steps - Phase 2:**
- Implement `calculated_metrics` table schema (40+ metric columns)
- Build `DailyMetricsCalculator` service (pandas/NumPy calculations)
- Create 11 screener API endpoints starting with RRG Charts
- Set up daily metrics calculation n8n workflow
- See detailed plan: [.claude/plans/phase-2-backend-screeners.md](.claude/plans/phase-2-backend-screeners.md)
