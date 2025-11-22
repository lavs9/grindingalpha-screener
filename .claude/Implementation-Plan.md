# Implementation Plan
## Indian Stock Market Screener Platform - Phase 1 (Data Storage)

**Version:** 1.0
**Date:** November 16, 2025
**Status:** Planning Phase

---

## Overview

This document outlines the phased implementation plan for Phase 1 (Data Storage & Infrastructure) of the Indian Stock Market Screener Platform. The plan is broken down into actionable sub-phases with clear dependencies, tasks, and success criteria.

**Total Estimated Timeline:** 6-8 weeks (Phase 1 only)

---

## Phase 0: Environment & Infrastructure Setup

**Duration:** 3-5 days
**Goal:** Set up development environment, Docker infrastructure, and project foundations

### Tasks

#### 0.1 Project Structure Reorganization
- [ ] Reorganize project structure with proper service separation
  ```
  /screener
  ├── .claude/                    # Planning docs (✓ Done)
  ├── .env.example                # Environment template (shared)
  ├── .env                        # Actual secrets (gitignored, shared)
  ├── .gitignore                  # Comprehensive gitignore
  ├── docker-compose.yml          # Multi-container orchestration
  ├── README.md                   # Project setup & overview
  ├── CLAUDE.md                   # Claude Code guidance (✓ Done)
  ├── CONTRIBUTING.md             # Contribution guidelines (✓ Done)
  │
  ├── backend/                    # FastAPI application
  │   ├── Dockerfile              # Backend container definition
  │   ├── requirements.txt        # Python dependencies
  │   ├── alembic.ini             # Database migration config
  │   ├── main.py                 # FastAPI application entry point
  │   │
  │   ├── alembic/                # Database migrations
  │   │   ├── env.py
  │   │   └── versions/           # Migration scripts
  │   │
  │   ├── app/                    # Application code
  │   │   ├── __init__.py
  │   │   │
  │   │   ├── api/                # API route handlers
  │   │   │   ├── __init__.py
  │   │   │   ├── v1/
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── ingestion.py    # POST /api/v1/ingest/*
  │   │   │   │   ├── query.py        # GET /api/v1/securities, /ohlcv
  │   │   │   │   ├── screeners.py    # GET /api/v1/screeners/* (Phase 2)
  │   │   │   │   └── health.py       # GET /health, /status
  │   │   │   └── deps.py             # Common dependencies
  │   │   │
  │   │   ├── core/               # Core configuration
  │   │   │   ├── __init__.py
  │   │   │   ├── config.py       # Settings (from .env)
  │   │   │   └── security.py     # Security utilities (future)
  │   │   │
  │   │   ├── database/           # Database layer
  │   │   │   ├── __init__.py
  │   │   │   ├── session.py      # DB session management
  │   │   │   └── base.py         # Base model class
  │   │   │
  │   │   ├── models/             # SQLAlchemy models (all 11 tables)
  │   │   │   ├── __init__.py
  │   │   │   ├── security.py     # Securities, Indices tables
  │   │   │   ├── timeseries.py   # OHLCV, MarketCap, Calculated
  │   │   │   ├── events.py       # BulkDeals, BlockDeals, Surveillance
  │   │   │   └── metadata.py     # Industry, Holidays, IndexConstituents, IngestionLogs
  │   │   │
  │   │   ├── schemas/            # Pydantic models (request/response)
  │   │   │   ├── __init__.py
  │   │   │   ├── ingestion.py    # Ingestion request/response schemas
  │   │   │   ├── security.py     # Security schemas
  │   │   │   └── ohlcv.py        # OHLCV schemas
  │   │   │
  │   │   ├── services/           # Business logic layer
  │   │   │   ├── __init__.py
  │   │   │   ├── nse/
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── securities_fetcher.py   # NSE securities list
  │   │   │   │   ├── marketcap_fetcher.py    # NSE market cap
  │   │   │   │   ├── deals_fetcher.py        # Bulk/block deals
  │   │   │   │   ├── surveillance_fetcher.py # Surveillance list
  │   │   │   │   └── industry_scraper.py     # Playwright-based scraper
  │   │   │   ├── upstox/
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── client.py               # Upstox SDK wrapper
  │   │   │   │   ├── historical.py           # Historical OHLCV
  │   │   │   │   ├── daily_quotes.py         # Daily quotes
  │   │   │   │   └── holidays.py             # Market holidays
  │   │   │   └── calculators/                # Metric calculators (Phase 2)
  │   │   │       ├── __init__.py
  │   │   │       ├── relative_strength.py    # RS, VARS calculations
  │   │   │       └── technical.py            # ATR, VCP, Stage analysis
  │   │   │
  │   │   └── utils/              # Utility functions
  │   │       ├── __init__.py
  │   │       ├── validators.py   # Data validation (ISIN, dates, OHLCV)
  │   │       ├── date_utils.py   # Date parsing/formatting
  │   │       ├── logger.py       # Structured logging
  │   │       └── retry.py        # Retry logic with backoff
  │   │
  │   └── tests/                  # Test suite
  │       ├── __init__.py
  │       ├── conftest.py         # Pytest fixtures
  │       ├── test_api/
  │       ├── test_services/
  │       ├── test_models/
  │       └── test_utils/
  │
  ├── n8n/                        # n8n workflow orchestration
  │   ├── Dockerfile              # Custom n8n image (if needed)
  │   ├── workflows/              # Workflow JSON exports
  │   │   ├── daily_eod_master.json           # Daily EOD workflow
  │   │   ├── historical_backfill.json        # One-time backfill
  │   │   ├── weekly_industry_scraper.json    # Weekly industry update
  │   │   └── manual_triggers.json            # Manual data ingestion
  │   └── README.md               # n8n setup instructions
  │
  ├── frontend/                   # React/Vue.js dashboard (Phase 3)
  │   ├── Dockerfile
  │   ├── package.json
  │   ├── src/
  │   └── public/
  │
  ├── scripts/                    # Database & deployment scripts
  │   ├── init_db.sql             # Database initialization
  │   ├── seed_data.sql           # Sample data for testing
  │   ├── backup.sh               # Database backup script
  │   └── restore.sh              # Database restore script
  │
  ├── logs/                       # Application logs (gitignored)
  │   ├── backend/
  │   └── n8n/
  │
  └── data/                       # Local data storage (gitignored)
      ├── downloads/              # Downloaded NSE files
      └── uploads/                # Manual upload staging
  ```

- [ ] **Migration steps from current structure:**
  1. Create new `backend/` directory
  2. Move `screener_project/*` contents to `backend/app/`
  3. Reorganize into proper module structure (api/, services/, models/, etc.)
  4. Create `n8n/` directory with workflows subdirectory
  5. Update import paths in all Python files
  6. Update `docker-compose.yml` volume mounts to point to `backend/`
  7. Move `screener_project/requirements.txt` to `backend/requirements.txt`
  8. Archive old `screener_project/` folder (don't delete until migration verified)

#### 0.2 Environment Configuration
- [ ] Create `.env.example` with all required variables
- [ ] Generate `.env` file with actual secrets:
  ```bash
  # Database
  DB_HOST=postgres
  DB_PORT=5432
  DB_NAME=screener_db
  DB_USER=screener_user
  DB_PASSWORD=$(openssl rand -base64 32)

  # Upstox API (to be filled by user)
  UPSTOX_API_KEY=your_api_key_here
  UPSTOX_API_SECRET=your_api_secret_here
  UPSTOX_ACCESS_TOKEN=your_access_token_here

  # n8n
  N8N_ENCRYPTION_KEY=$(openssl rand -base64 32)

  # Application
  ENV=development
  LOG_LEVEL=INFO
  ```
- [ ] Update `.gitignore` to exclude `.env`, `__pycache__`, `venv/`, `logs/`, etc.

#### 0.3 Docker Setup
- [ ] **Create `docker-compose.yml`** (root directory)
  ```yaml
  version: '3.8'

  services:
    postgres:
      container_name: screener_postgres
      image: postgres:15-alpine
      environment:
        POSTGRES_USER: ${DB_USER}
        POSTGRES_PASSWORD: ${DB_PASSWORD}
        POSTGRES_DB: ${DB_NAME}
      ports:
        - "5432:5432"
      volumes:
        - postgres_data:/var/lib/postgresql/data
        - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
      networks:
        - screener_network
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
        interval: 10s
        timeout: 5s
        retries: 5

    backend:
      container_name: screener_backend
      build:
        context: ./backend
        dockerfile: Dockerfile
      environment:
        DB_HOST: postgres
        DB_PORT: 5432
        DB_NAME: ${DB_NAME}
        DB_USER: ${DB_USER}
        DB_PASSWORD: ${DB_PASSWORD}
        UPSTOX_API_KEY: ${UPSTOX_API_KEY}
        UPSTOX_API_SECRET: ${UPSTOX_API_SECRET}
        UPSTOX_ACCESS_TOKEN: ${UPSTOX_ACCESS_TOKEN}
        ENV: ${ENV}
        LOG_LEVEL: ${LOG_LEVEL}
      ports:
        - "8000:8000"
      volumes:
        - ./backend:/app
        - ./logs/backend:/app/logs
        - ./data:/app/data
      depends_on:
        postgres:
          condition: service_healthy
      networks:
        - screener_network
      command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    n8n:
      container_name: screener_n8n
      image: n8nio/n8n:latest
      environment:
        N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
        N8N_HOST: ${N8N_HOST:-localhost}
        N8N_PORT: 5678
        N8N_PROTOCOL: http
        WEBHOOK_URL: http://localhost:5678/
        GENERIC_TIMEZONE: Asia/Kolkata
      ports:
        - "5678:5678"
      volumes:
        - n8n_data:/home/node/.n8n
        - ./n8n/workflows:/home/node/.n8n/workflows
      networks:
        - screener_network
      depends_on:
        - backend

  networks:
    screener_network:
      driver: bridge

  volumes:
    postgres_data:
    n8n_data:
  ```

- [ ] **Create `backend/Dockerfile`**
  ```dockerfile
  FROM python:3.12-slim

  WORKDIR /app

  # Install system dependencies
  RUN apt-get update && apt-get install -y \
      gcc \
      postgresql-client \
      && rm -rf /var/lib/apt/lists/*

  # Install Playwright dependencies (for NSE scraping)
  RUN apt-get update && apt-get install -y \
      libnss3 \
      libnspr4 \
      libatk1.0-0 \
      libatk-bridge2.0-0 \
      libcups2 \
      libdrm2 \
      libxkbcommon0 \
      libxcomposite1 \
      libxdamage1 \
      libxfixes3 \
      libxrandr2 \
      libgbm1 \
      libasound2 \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements and install Python dependencies
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Install Playwright browsers
  RUN playwright install chromium

  # Copy application code
  COPY . .

  # Expose port
  EXPOSE 8000

  # Run migrations on startup (in production, run separately)
  CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
  ```

- [ ] **Create `scripts/init_db.sql`** (database initialization)
  ```sql
  -- Create extensions if needed
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

  -- Grant privileges
  GRANT ALL PRIVILEGES ON DATABASE screener_db TO screener_user;
  ```

- [ ] **Create `n8n/README.md`** (n8n setup instructions)
  ```markdown
  # n8n Workflow Setup

  ## Initial Setup
  1. Access n8n UI: http://localhost:5678
  2. Create account (local n8n instance)
  3. Import workflows from `workflows/` directory

  ## Workflow Import
  - Go to Workflows → Import from File
  - Select JSON files from `n8n/workflows/`

  ## Workflow Configuration
  Each workflow requires:
  - HTTP Request nodes pointing to: http://backend:8000/api/v1/ingest/*
  - Cron triggers for scheduling
  - Error handling configured (Continue On Fail: TRUE)

  ## Testing Workflows
  - Use "Execute Workflow" button for manual testing
  - Check backend logs: `docker-compose logs -f backend`
  - Query ingestion_logs table for results
  ```

- [ ] Test Docker build: `docker-compose build`
- [ ] Test Docker startup: `docker-compose up -d`
- [ ] Verify services:
  - PostgreSQL: `docker exec -it screener_postgres psql -U screener_user -d screener_db`
  - Backend: `curl http://localhost:8000/health`
  - n8n: Open `http://localhost:5678` in browser
- [ ] Check container logs: `docker-compose logs -f`
- [ ] Verify network connectivity: Backend can reach PostgreSQL, n8n can reach Backend

#### 0.4 Backend Code Refactoring
- [ ] **Create `backend/app/core/config.py`** (centralized configuration)
  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      # Database
      DB_HOST: str
      DB_PORT: int = 5432
      DB_NAME: str
      DB_USER: str
      DB_PASSWORD: str

      # Upstox
      UPSTOX_API_KEY: str
      UPSTOX_API_SECRET: str
      UPSTOX_ACCESS_TOKEN: str

      # Application
      ENV: str = "development"
      LOG_LEVEL: str = "INFO"

      @property
      def database_url(self) -> str:
          return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

      class Config:
          env_file = ".env"
          case_sensitive = True

  settings = Settings()
  ```

- [ ] **Migrate `database/db_helper.py` → `backend/app/database/session.py`**
  - Replace hardcoded credentials with `settings.database_url`
  - Add connection pooling: `pool_size=20, max_overflow=40`
  - Add health check function: `check_db_connection()`

- [ ] **Create `backend/main.py`** (application entry point)
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings
  from app.api.v1 import health, ingestion, query
  from app.database.session import engine
  from app.database.base import Base

  app = FastAPI(
      title="Stock Screener API",
      version="1.0.0",
      description="Indian Stock Market Screener Platform"
  )

  # CORS middleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # Configure for production
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Include routers
  app.include_router(health.router, prefix="/api/v1", tags=["health"])
  app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
  app.include_router(query.router, prefix="/api/v1", tags=["query"])

  @app.on_event("startup")
  async def startup_event():
      # Create tables (later replaced by Alembic migrations)
      Base.metadata.create_all(bind=engine)

  @app.get("/")
  async def root():
      return {"message": "Stock Screener API", "env": settings.ENV}
  ```

- [ ] **Migrate existing code to new structure:**
  - `screener_project/database/` → `backend/app/database/`
  - `screener_project/data_ingester/` → `backend/app/services/nse/`
  - `screener_project/indexes_models/` → `backend/app/models/`
  - `screener_project/return_calculator/` → `backend/app/services/calculators/`
  - Update all import paths to use `app.` prefix

#### 0.5 Dependency Management
- [ ] Update `requirements.txt`:
  ```
  fastapi==0.109.2
  uvicorn[standard]==0.27.1
  sqlalchemy==2.0.27
  psycopg2-binary==2.9.9
  pydantic==2.6.1
  pydantic-settings==2.1.0
  pandas==2.2.0
  python-dateutil==2.8.2
  requests==2.31.0
  upstox-python-sdk==latest  # Check PyPI for exact version
  playwright==1.40.0
  python-dotenv==1.0.0
  python-json-logger==2.0.7
  alembic==1.13.1
  pytest==7.4.3
  pytest-asyncio==0.21.1
  ```
- [ ] Install Playwright browsers: `playwright install chromium`

### Success Criteria
- ✅ Docker Compose stack runs successfully (all 3 containers healthy)
- ✅ FastAPI `/health` endpoint returns 200
- ✅ PostgreSQL accepts connections from FastAPI container
- ✅ n8n UI accessible and workflow can be created
- ✅ No hardcoded credentials in codebase
- ✅ Logs directory created and writable

### Dependencies
None (foundational phase)

---

## Phase 1.1: Core Database Models & Schema

**Duration:** 4-6 days
**Goal:** Create all database models and set up migration framework

### Tasks

#### 1.1.1 Set Up Alembic for Database Migrations
- [ ] Initialize Alembic: `alembic init alembic`
- [ ] Configure `alembic.ini` to use environment variables
- [ ] Update `alembic/env.py` to import SQLAlchemy models
- [ ] Test migration: `alembic revision --autogenerate -m "Initial schema"`
- [ ] Apply migration: `alembic upgrade head`

#### 1.1.2 Create Master Table Models
Create SQLAlchemy models in `database/models.py`:

- [ ] **Securities Model**
  ```python
  class Security(Base):
      __tablename__ = 'securities'
      id = Column(Integer, primary_key=True)
      symbol = Column(String(50), unique=True, nullable=False, index=True)
      isin = Column(String(12), unique=True, nullable=False, index=True)
      security_name = Column(String(255), nullable=False)
      series = Column(String(10))
      listing_date = Column(Date)
      paid_up_value = Column(Numeric(15, 2))
      market_lot = Column(Integer)
      face_value = Column(Numeric(10, 2))
      security_type = Column(Enum('EQUITY', 'ETF', name='security_type_enum'), nullable=False)
      is_active = Column(Boolean, default=True)
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  ```

- [ ] **Indices Model**
  ```python
  class Index(Base):
      __tablename__ = 'indices'
      id = Column(Integer, primary_key=True)
      index_name = Column(String(100), unique=True, nullable=False)
      symbol = Column(String(50), unique=True, nullable=False, index=True)
      exchange = Column(String(20), default='NSE_INDEX')
      is_active = Column(Boolean, default=True)
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  ```

- [ ] **Industry Classification Model**
  ```python
  class IndustryClassification(Base):
      __tablename__ = 'industry_classification'
      id = Column(Integer, primary_key=True)
      symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'), unique=True, nullable=False)
      macro = Column(String(100))
      sector = Column(String(100), index=True)
      industry = Column(String(100), index=True)
      basic_industry = Column(String(100))
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  ```

- [ ] **Market Holidays Model**
  ```python
  class MarketHoliday(Base):
      __tablename__ = 'market_holidays'
      id = Column(Integer, primary_key=True)
      holiday_date = Column(Date, unique=True, nullable=False, index=True)
      holiday_name = Column(String(255))
      exchange = Column(String(20), default='NSE')
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

#### 1.1.3 Create Time-Series Table Models
- [ ] **OHLCV Daily Model**
  ```python
  class OHLCVDaily(Base):
      __tablename__ = 'ohlcv_daily'
      id = Column(BigInteger, primary_key=True)
      symbol = Column(String(50), nullable=False, index=True)
      date = Column(Date, nullable=False, index=True)
      open = Column(Numeric(15, 2), nullable=False)
      high = Column(Numeric(15, 2), nullable=False)
      low = Column(Numeric(15, 2), nullable=False)
      close = Column(Numeric(15, 2), nullable=False)
      volume = Column(BigInteger)
      vwap = Column(Numeric(15, 2))
      prev_close = Column(Numeric(15, 2))
      change_pct = Column(Numeric(8, 4))
      upper_circuit = Column(Numeric(15, 2))
      lower_circuit = Column(Numeric(15, 2))
      week_52_high = Column(Numeric(15, 2))
      week_52_low = Column(Numeric(15, 2))
      created_at = Column(DateTime, default=datetime.utcnow)

      __table_args__ = (
          UniqueConstraint('symbol', 'date', name='uq_ohlcv_symbol_date'),
          CheckConstraint('high >= low', name='ck_high_gte_low'),
          Index('idx_ohlcv_symbol_date', 'symbol', 'date'),
      )
  ```

- [ ] **Market Cap History Model**
  ```python
  class MarketCapHistory(Base):
      __tablename__ = 'market_cap_history'
      id = Column(BigInteger, primary_key=True)
      symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'), nullable=False, index=True)
      date = Column(Date, nullable=False, index=True)
      series = Column(String(10))
      security_name = Column(String(255))
      category = Column(String(50))
      last_trade_date = Column(Date)
      face_value = Column(Numeric(10, 2))
      issue_size = Column(BigInteger)
      close_price = Column(Numeric(15, 2))
      market_cap = Column(Numeric(20, 2), nullable=False, index=True)
      created_at = Column(DateTime, default=datetime.utcnow)

      __table_args__ = (
          UniqueConstraint('symbol', 'date', name='uq_marketcap_symbol_date'),
          Index('idx_marketcap_symbol_date', 'symbol', 'date'),
      )
  ```

#### 1.1.4 Create Event Table Models
- [ ] **Bulk Deals Model**
- [ ] **Block Deals Model** (same schema as bulk deals)
- [ ] **Surveillance Measures Model**

#### 1.1.5 Create Join Table Models
- [ ] **Index Constituents Model** (M:N relationship)

#### 1.1.6 Generate and Apply Migrations
- [ ] Generate migration: `alembic revision --autogenerate -m "Create all tables"`
- [ ] Review auto-generated migration in `alembic/versions/`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify tables in PostgreSQL:
  ```sql
  \dt  -- List all tables
  \d securities  -- Describe securities table
  ```

#### 1.1.7 Create Pydantic Schemas
Create schemas in `database/schemas.py` for request/response validation:
- [ ] `SecurityCreate`, `SecurityResponse`
- [ ] `OHLCVCreate`, `OHLCVResponse`
- [ ] `MarketCapCreate`, `MarketCapResponse`
- [ ] (Repeat for all models)

### Success Criteria
- ✅ All 10 tables created in PostgreSQL
- ✅ Constraints (foreign keys, unique, check) enforced
- ✅ Indexes created on key columns
- ✅ Alembic migrations work forward and backward (`upgrade`/`downgrade`)
- ✅ Pydantic schemas validate sample data

### Dependencies
- Phase 0 (Environment setup) completed

---

## Phase 1.2: NSE Data Sources Integration

**Duration:** 5-7 days
**Goal:** Fetch and ingest data from NSE archives (listed securities, market cap, bulk/block deals, surveillance)

**IMPORTANT:** Before implementing any parser, refer to [.claude/file-formats.md](.claude/file-formats.md) for exact format specifications, validation rules, and sample files.

### Tasks

#### 1.2.1 Create NSE Scraper Service
Create `services/nse_scraper.py`:

- [ ] **Fetch Listed Securities**
  ```python
  def fetch_listed_securities(security_type='EQUITY'):
      """
      Fetch from: https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
      Returns: List of dicts with symbol, isin, security_name, etc.
      """
  ```
  - Headers: User-Agent, Referer (as per data-storage.md)
  - Parse CSV with pandas
  - Return structured data

- [ ] **Fetch ETF List**
  ```python
  def fetch_etf_list():
      """
      Fetch from: https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv
      Returns: List of dicts
      """
  ```

- [ ] **Fetch Market Cap Data**
  ```python
  def fetch_market_cap(date: datetime.date):
      """
      1. Construct URL: https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{DDMMYY}.zip
      2. Download ZIP
      3. Extract MCAP{DDMMYYYY}.csv
      4. Parse and return data
      Handles: Missing files (404), corrupted ZIPs
      """
  ```

- [ ] **Fetch Bulk Deals**
  ```python
  def fetch_bulk_deals(date: datetime.date):
      """
      Fetch from: https://nsearchives.nseindia.com/content/equities/bulk.csv
      Returns: List of dicts
      """
  ```

- [ ] **Fetch Block Deals** (similar to bulk deals)

- [ ] **Fetch Surveillance Measures**
  ```python
  def fetch_surveillance_measures(date: datetime.date):
      """
      Fetch from: https://nsearchives.nseindia.com/content/cm/REG1_IND{DDMMYY}.csv
      Returns: List of dicts
      """
  ```

#### 1.2.2 Create Data Validators
Create `services/validators.py`:
- [ ] Validate symbol format (regex: `^[A-Z0-9&-]+$`)
- [ ] Validate ISIN format (12 chars, starts with IN)
- [ ] Validate OHLC consistency (high >= low, etc.)
- [ ] Validate date ranges (no future dates)
- [ ] Sanitize strings (remove special characters)

#### 1.2.3 Create Ingestion API Endpoints
Create `api/ingestion.py`:

- [ ] **POST /api/v1/ingest/securities**
  - Call `fetch_listed_securities()`
  - Validate data
  - Upsert to `securities` table (update if exists, insert if new)
  - Return summary (added, updated, errors)

- [ ] **POST /api/v1/ingest/etfs**
  - Same pattern as securities
  - Set `security_type='ETF'`

- [ ] **POST /api/v1/ingest/market-cap**
  - Accept optional `date` parameter (default: yesterday)
  - Call `fetch_market_cap(date)`
  - Filter: Only insert symbols that exist in `securities` table
  - Handle missing files gracefully (log warning, return success with note)

- [ ] **POST /api/v1/ingest/bulk-deals**
- [ ] **POST /api/v1/ingest/block-deals**
- [ ] **POST /api/v1/ingest/surveillance**

#### 1.2.4 Add Error Handling & Logging
- [ ] Wrap all fetch functions in try-except
- [ ] Log errors to `logs/screener.log` with context
- [ ] Return detailed error responses (400/500 with JSON error object)
- [ ] Add retry logic for network failures (exponential backoff, max 3 retries)

#### 1.2.5 Unit Tests
Create `tests/test_nse_scraper.py`:
- [ ] Test `fetch_listed_securities()` with mocked response
- [ ] Test market cap ZIP extraction
- [ ] Test handling of 404 errors (missing files)
- [ ] Test data validation (invalid ISIN, etc.)

#### 1.2.6 Manual Testing
- [ ] Test each endpoint via FastAPI Swagger UI (`/docs`)
- [ ] Verify data in PostgreSQL:
  ```sql
  SELECT COUNT(*) FROM securities;
  SELECT * FROM securities LIMIT 10;
  SELECT COUNT(*) FROM market_cap_history WHERE date = '2025-01-16';
  ```
- [ ] Test error scenarios (invalid date, network timeout)

### Success Criteria
- ✅ All NSE CSV endpoints fetch data successfully
- ✅ Market cap ZIP extraction works (handles missing files)
- ✅ Data inserted into PostgreSQL without errors
- ✅ `securities` table has 2000+ records
- ✅ Upsert logic works (re-running ingestion doesn't create duplicates)
- ✅ Error handling logs failures and continues processing

### Dependencies
- Phase 1.1 (Database models) completed

---

## Phase 1.3: Upstox Integration (Historical + Daily OHLCV)

**Duration:** 6-8 days
**Goal:** Integrate Upstox Python SDK for historical data backfill and daily OHLCV fetching

**IMPORTANT:** Before implementing API integrations, refer to [.claude/file-formats.md](.claude/file-formats.md) Section 5 (Upstox API Responses) for exact response structures and field mappings.

### Tasks

#### 1.3.1 Set Up Upstox SDK
- [ ] Install Upstox Python SDK: `pip install upstox-python-sdk`
- [ ] Study SDK documentation: https://upstox.com/developer/api-documentation/upstox-generated-sdk
- [ ] Create `services/upstox_client.py`:
  ```python
  import upstox_client
  from upstox_client.rest import ApiException

  class UpstoxClient:
      def __init__(self):
          self.api_key = os.getenv('UPSTOX_API_KEY')
          self.api_secret = os.getenv('UPSTOX_API_SECRET')
          self.access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
          self.configuration = upstox_client.Configuration()
          self.configuration.access_token = self.access_token

      def get_historical_candle_data(self, instrument_key, from_date, to_date, interval='1day'):
          """Fetch historical OHLCV data"""
          pass

      def get_full_market_quote(self, instrument_keys):
          """Fetch full market quote for multiple symbols"""
          pass

      def get_market_holidays(self, date=None):
          """Fetch market holidays"""
          pass
  ```

#### 1.3.2 Implement Instrument Key Mapping
- [ ] Upstox uses `instrument_key` format: `NSE_EQ|INE002A01018` (exchange_segment|ISIN)
- [ ] Create helper function:
  ```python
  def get_instrument_key(symbol, isin, security_type='EQUITY'):
      """
      Construct Upstox instrument key
      EQUITY: NSE_EQ|{ISIN}
      ETF: NSE_EQ|{ISIN}
      INDEX: NSE_INDEX|{symbol}
      """
      if security_type == 'INDEX':
          return f"NSE_INDEX|{symbol}"
      else:
          return f"NSE_EQ|{isin}"
  ```

#### 1.3.3 Implement Historical Data Fetching
- [ ] **Function: `fetch_historical_ohlcv(symbol, from_date, to_date)`**
  - Get instrument_key from `securities` or `indices` table
  - Call Upstox `get_historical_candle_data()`
  - Parse response (format: list of candles)
  - Convert to list of dicts:
    ```python
    {
      'symbol': symbol,
      'date': candle_date,
      'open': candle[1],
      'high': candle[2],
      'low': candle[3],
      'close': candle[4],
      'volume': candle[5]  # or None for indices
    }
    ```
  - Handle rate limits (check SDK for limits, add throttling if needed)
  - Return data

#### 1.3.4 Implement Daily OHLCV Fetching
- [ ] **Function: `fetch_daily_ohlcv_all(symbols)`**
  - Accept list of symbols
  - Batch symbols (Upstox allows up to 500 symbols per request - verify in docs)
  - Call `get_full_market_quote()` for each batch
  - Parse response (extract OHLC, volume, VWAP, circuits, 52w high/low)
  - Return list of dicts

#### 1.3.5 Implement Market Holidays Fetching
- [ ] **Function: `fetch_market_holidays()`**
  - Call Upstox `get_market_holidays()`
  - Parse response (list of dates)
  - Return list of dicts: `{holiday_date, holiday_name, exchange}`

#### 1.3.6 Create Ingestion API Endpoints
- [ ] **POST /api/v1/ingest/historical-ohlcv/{symbol}**
  - Query parameters: `from_date`, `to_date` (optional, defaults to 5 years)
  - Get symbol details from `securities` table (validate symbol exists)
  - Calculate `from_date`:
    - If not provided: `max(listing_date, 5 years ago)`
  - Call `fetch_historical_ohlcv(symbol, from_date, to_date)`
  - Bulk insert to `ohlcv_daily` (use SQLAlchemy `bulk_insert_mappings`)
  - Handle duplicates (ON CONFLICT DO NOTHING or UPDATE)
  - Return summary: `{records_added, date_range, gaps_detected}`

- [ ] **POST /api/v1/ingest/daily-ohlcv**
  - Query parameters: `symbols` (optional, defaults to all active securities)
  - Get all active symbols from `securities` and `indices` tables
  - Call `fetch_daily_ohlcv_all(symbols)`
  - Insert to `ohlcv_daily`
  - Return summary: `{total_symbols, successful, failed, errors}`

- [ ] **POST /api/v1/ingest/market-holidays**
  - Call `fetch_market_holidays()`
  - Insert to `market_holidays` table
  - Return count of holidays inserted

#### 1.3.7 Implement Rate Limiting
- [ ] Check Upstox API rate limits (consult SDK docs or Upstox support)
- [ ] Implement throttling:
  - Option A: Use `time.sleep()` between requests
  - Option B: Use `ratelimit` library
  - Example:
    ```python
    from ratelimit import limits, sleep_and_retry

    @sleep_and_retry
    @limits(calls=10, period=1)  # 10 calls per second (adjust per Upstox limits)
    def call_upstox_api():
        pass
    ```

#### 1.3.8 Handle Upstox API Errors
- [ ] Wrap API calls in try-except for `ApiException`
- [ ] Log errors with request details
- [ ] Return appropriate HTTP status codes:
  - 404: Symbol not found in Upstox
  - 429: Rate limit exceeded
  - 500: Upstox API error
  - 503: Upstox service unavailable

#### 1.3.9 Historical Backfill Script
Create `scripts/backfill_historical_data.py`:
- [ ] Get all symbols from `securities` and `indices` tables
- [ ] Loop through each symbol:
  - Calculate `from_date` (5 years ago or listing_date)
  - POST to `/api/v1/ingest/historical-ohlcv/{symbol}`
  - Log progress (symbol X of Y)
  - Handle errors (log and continue)
- [ ] Generate report:
  - Total symbols processed
  - Successful: count, total records
  - Failed: list of symbols with errors
- [ ] Save report to `logs/backfill_report_YYYYMMDD.json`

#### 1.3.10 Testing
- [ ] **Unit Tests:**
  - Mock Upstox SDK responses
  - Test `fetch_historical_ohlcv()` with sample data
  - Test error handling (API exceptions)

- [ ] **Integration Tests:**
  - Test single symbol historical fetch (use a known symbol like "RELIANCE")
  - Test daily OHLCV fetch for 10 symbols
  - Test market holidays fetch
  - Verify data in PostgreSQL

- [ ] **POC Test (1 Stock):**
  - Manually test historical backfill for 1 stock (e.g., RELIANCE)
  - Verify 5 years of data inserted
  - Check for gaps (excluding weekends/holidays)

### Success Criteria
- ✅ Upstox SDK configured with API credentials
- ✅ Historical OHLCV fetch works for 1 POC stock (5 years of data)
- ✅ Daily OHLCV fetch works for all 2000+ securities
- ✅ Market holidays table populated
- ✅ Rate limiting prevents API quota exhaustion
- ✅ Error handling logs failures without crashing
- ✅ Backfill script can be run independently

### Dependencies
- Phase 1.1 (Database models) completed
- Phase 1.2 (NSE integration) completed (for securities list)

---

## Phase 1.4: Supporting Data Sources (Industry/Sector, Index Constituents)

**Duration:** 5-7 days
**Goal:** Automate industry classification scraping and implement index constituents management

**IMPORTANT:** Refer to [.claude/file-formats.md](.claude/file-formats.md) Section 7 (NSE Industry Classification) and Section 6 (Index Constituents) for exact formats.

### Tasks

#### 1.4.1 Set Up Playwright for NSE Scraping
- [ ] Install Playwright: `pip install playwright`
- [ ] Install browsers: `playwright install chromium`
- [ ] Test Playwright:
  ```python
  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto('https://www.nseindia.com')
      print(page.title())
      browser.close()
  ```

#### 1.4.2 Implement Industry Classification Scraper
Create `services/nse_industry_scraper.py`:

- [ ] **Function: `get_nse_cookies()`**
  ```python
  def get_nse_cookies():
      """
      Launch Playwright browser
      Navigate to NSE homepage
      Wait for cookies to be set (detect _abck cookie)
      Extract all cookies
      Return cookies as dict
      """
  ```

- [ ] **Function: `fetch_industry_for_symbol(symbol, cookies)`**
  ```python
  def fetch_industry_for_symbol(symbol, cookies):
      """
      GET https://www.nseindia.com/api/quote-equity?symbol={symbol}
      Headers: User-Agent, Accept, Referer, Cookie
      Extract: industryInfo.macro, sector, industry, basicIndustry
      Returns: dict or None (if error)
      Handles: 403 (expired cookie - raise exception to refresh)
      """
  ```

- [ ] **Function: `scrape_all_industries()`**
  ```python
  def scrape_all_industries():
      """
      Main orchestrator function:
      1. Get all symbols from securities table
      2. Get fresh cookies via get_nse_cookies()
      3. Loop through symbols:
         - fetch_industry_for_symbol()
         - If 403 error, refresh cookies (max 3 times)
         - Sleep 1 second between requests
         - Yield results (generator pattern for progress tracking)
      4. Return summary (updated, failed)
      """
  ```

#### 1.4.3 Create Industry Classification Endpoint
- [ ] **POST /api/v1/ingest/industry-classification**
  - Optional body: `{symbols: []}` (defaults to all securities)
  - Call `scrape_all_industries()`
  - Upsert to `industry_classification` table
  - Return summary: `{updated, failed, cookie_refreshes}`

#### 1.4.4 Implement Index Constituents Management
- [ ] **POST /api/v1/ingest/index-constituents**
  - Body:
    ```json
    {
      "index_name": "Nifty 50",
      "effective_from": "2025-01-16",
      "constituents": [
        {
          "symbol": "RELIANCE",
          "company_name": "Reliance Industries Limited",
          "industry": "Refineries",
          "weightage": 10.25
        },
        ...
      ]
    }
    ```
  - Validate: Index exists in `indices` table
  - Insert to `index_constituents` table
  - Set `effective_to = effective_from - 1 day` for previous constituents
  - Return summary

- [ ] **GET /api/v1/indices/{index_name}/constituents**
  - Query parameter: `effective_date` (default: today)
  - Query `index_constituents` where `effective_from <= date AND (effective_to IS NULL OR effective_to >= date)`
  - Return list of constituents

#### 1.4.5 Create Manual Upload Script for Index Constituents
Create `scripts/upload_index_constituents.py`:
- [ ] Accept CSV file path as argument
- [ ] Parse CSV (columns: symbol, company_name, industry, weightage)
- [ ] Prompt for index_name and effective_from
- [ ] POST to `/api/v1/ingest/index-constituents`
- [ ] Print summary

#### 1.4.6 Testing
- [ ] **Industry Scraper Tests:**
  - Test cookie extraction (verify _abck cookie present)
  - Test single symbol fetch (e.g., "RELIANCE")
  - Test 403 handling (mock expired cookie scenario)
  - Test rate limiting (verify 1 second delay between requests)

- [ ] **Index Constituents Tests:**
  - Upload sample Nifty 50 constituents CSV
  - Query constituents endpoint
  - Verify historical tracking (upload new constituents with different effective_from)

### Success Criteria
- ✅ Playwright successfully navigates NSE and extracts cookies
- ✅ Industry classification scraped for ≥95% of securities (some may fail)
- ✅ Cookie refresh mechanism works (handles 403 errors)
- ✅ Index constituents can be uploaded and queried
- ✅ Historical tracking works (effective_from/effective_to dates)

### Dependencies
- Phase 1.1 (Database models) completed
- Phase 1.2 (NSE integration) completed (for securities list)

---

## Phase 1.5: n8n Workflow Setup & Automation

**Duration:** 5-7 days
**Goal:** Create n8n workflows for automated daily data ingestion and weekly industry scraping

### Tasks

#### 1.5.1 Set Up n8n
- [ ] Access n8n UI: `http://localhost:5678`
- [ ] Create initial user account
- [ ] Configure timezone: Asia/Kolkata
- [ ] Enable workflow saving to `/home/node/.n8n/workflows` (mounted volume)

#### 1.5.2 Create Common Workflow Nodes (Templates)
Create reusable sub-workflows or templates:

- [ ] **Error Handler Template**
  - Error Trigger node
  - Code node: Format error message
  - HTTP Request: POST to `/api/v1/logs` (create this endpoint)
  - Email/Slack notification node (optional)

- [ ] **Notification Template**
  - Input: `{status, message, details}`
  - If node: Check status (success/failure)
  - Email/Slack node with formatted message
  - Template:
    ```
    📊 Daily EOD Update
    Status: {{$json.status}}

    Securities: {{$json.securities.added}} added, {{$json.securities.updated}} updated
    OHLCV: {{$json.ohlcv.successful}}/{{$json.ohlcv.total}} symbols
    Errors: {{$json.errors.length}}

    Execution time: {{$json.execution_time}}s
    ```

#### 1.5.3 Create Daily EOD Workflow (CORRECTED - Independent Execution)
Workflow name: `Daily_EOD_Data_Fetch`

**IMPORTANT DESIGN:** Parallel branches execute INDEPENDENTLY. Each logs to `ingestion_logs` table. Aggregation queries the database (not n8n workflow state). See [Architecture.md Section 5.2.1](.claude/Architecture.md) for detailed diagram.

- [ ] **1. Cron Trigger**
  - Schedule: `30 20 * * 1-5 Asia/Kolkata` (8:30 PM IST, Mon-Fri)
  - Name: "Trigger at 8:30 PM IST"

- [ ] **2. Check Trading Day**
  - HTTP Request node
  - Method: GET
  - URL: `http://fastapi:8000/api/v1/status/is-trading-day?date={{$now.format('YYYY-MM-DD')}}`
  - If `is_trading_day === false` → Stop workflow

- [ ] **3. Independent Parallel Branches (6 total)**

  **CRITICAL CONFIG FOR EACH BRANCH:**
  - **Continue On Fail:** TRUE (don't stop workflow if one branch fails)
  - **Timeout:** 120 seconds
  - **Error Trigger:** Catch errors, log them, but continue

  **Branch 1: NSE Securities**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/securities`
  - On success/failure: Endpoint logs to `ingestion_logs` table (source='nse_securities')

  **Branch 2: NSE ETFs**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/etfs`
  - Logs to `ingestion_logs` (source='nse_etfs')

  **Branch 3: Market Cap**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/market-cap`
  - Logs to `ingestion_logs` (source='nse_market_cap')

  **Branch 4: Bulk Deals**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/bulk-deals`
  - Logs to `ingestion_logs` (source='nse_bulk_deals')

  **Branch 5: Block Deals**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/block-deals`
  - Logs to `ingestion_logs` (source='nse_block_deals')

  **Branch 6: Surveillance**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/surveillance`
  - Logs to `ingestion_logs` (source='nse_surveillance')

- [ ] **4. Database Aggregation (Not Wait for All)**
  - HTTP Request: GET `http://fastapi:8000/api/v1/status/ingestion`
  - This queries `ingestion_logs` table for today's results
  - Returns: `{sources: {nse_securities: {status, timestamp, ...}, ...}}`

- [ ] **5. Critical Dependency Check**
  - If node: Check if `sources.nse_securities.status === 'success'`
  - Rationale: OHLCV fetch needs securities list
  - If TRUE → Proceed to step 6
  - If FALSE → Skip OHLCV, log reason, send alert, jump to step 7

- [ ] **6. Fetch Daily OHLCV (Conditional)**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/daily-ohlcv`
  - Timeout: 300 seconds (longer for 2000+ symbols)
  - Logs to `ingestion_logs` (source='upstox_daily')

- [ ] **7. Final Aggregation**
  - HTTP Request: GET `http://fastapi:8000/api/v1/status/ingestion` (query again)
  - Code node: Format summary
    - List each source: name, status, record counts, errors
    - Calculate total success/failure count

- [ ] **8. Smart Notification**
  - If all success → Slack notification (non-urgent)
  - If any failure → Email alert with failed sources list
  - If critical failure (securities/OHLCV) → High-priority alert
  - Template:
    ```
    📊 Daily EOD Status

    ✓ Securities: 2145 records
    ✗ Market Cap: FAILED (NSE archive unavailable)
    ✓ Bulk Deals: 45 records
    ✓ Block Deals: 12 records
    ✓ Surveillance: 38 records
    ✓ OHLCV: 2140/2145 symbols (5 failed)

    Action Required: Market cap data missing for today
    Manual retry: POST /api/v1/ingest/market-cap
    ```

- [ ] **Manual Retry Capability:**
  - Document how to re-run individual sources:
    - `curl -X POST http://localhost:8000/api/v1/ingest/market-cap`
  - Failed sources can be retried independently without re-running entire workflow

#### 1.5.4 Create Weekly Industry Classification Workflow
Workflow name: `Weekly_Industry_Classification`

- [ ] **1. Cron Trigger**
  - Schedule: `0 22 * * 0 Asia/Kolkata` (10:00 PM IST, Sundays)

- [ ] **2. Fetch Industry Classification**
  - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/industry-classification`
  - Timeout: 3600 seconds (1 hour for 2000 symbols at 1 req/sec)

- [ ] **3. Send Summary**
  - Notification Template
  - Email/Slack with updated/failed counts

#### 1.5.5 Create Historical Backfill Workflow (Manual Trigger)
Workflow name: `Historical_Data_Backfill`

- [ ] **1. Manual Trigger**
  - Webhook or manual execution button

- [ ] **2. Get All Symbols**
  - HTTP Request: GET `http://fastapi:8000/api/v1/securities?limit=10000`

- [ ] **3. SplitInBatches Node**
  - Batch size: 50 symbols

- [ ] **4. Loop Through Batch**
  - For each symbol in batch:
    - HTTP Request: POST `http://fastapi:8000/api/v1/ingest/historical-ohlcv/{{$json.symbol}}`
    - Error handling: Log and continue

- [ ] **5. Wait for Batch**
  - Aggregate success/failure counts

- [ ] **6. Next Batch** (loop back to step 4)

- [ ] **7. Final Report**
  - Send email with total summary

#### 1.5.6 Export Workflow Templates
- [ ] Export each workflow as JSON
- [ ] Save to `n8n_workflows/` directory:
  - `daily_eod_fetch.json`
  - `weekly_industry_classification.json`
  - `historical_backfill.json`
- [ ] Document import instructions in README.md

#### 1.5.7 Testing Workflows
- [ ] **Daily EOD Workflow:**
  - Test with "Test workflow" button (uses mock date)
  - Verify all nodes execute successfully
  - Check database for new records
  - Test error scenario (simulate API failure)

- [ ] **Weekly Industry Workflow:**
  - Manually trigger (don't wait for Sunday)
  - Monitor progress (should take ~35-40 minutes for 2000 symbols)
  - Verify `industry_classification` table updates

- [ ] **Historical Backfill Workflow:**
  - Test with 5 symbols first (not full universe)
  - Verify historical data inserted
  - Test failure handling (invalid symbol)

#### 1.5.8 Create Health Check Endpoint
- [ ] **GET /api/v1/status/is-trading-day**
  - Query parameters: `date` (YYYY-MM-DD)
  - Query `market_holidays` table
  - Check if date is weekend (Saturday/Sunday)
  - Return: `{is_trading_day: true/false, date: date, reason: "holiday/weekend/trading"}`

### Success Criteria
- ✅ All 3 workflows created and saved in n8n
- ✅ Daily EOD workflow executes successfully (test mode)
- ✅ Weekly industry workflow completes for ≥95% symbols
- ✅ Historical backfill workflow tested with 5 symbols
- ✅ Error handling works (logs errors, sends notifications)
- ✅ Workflow JSON templates exported and documented

### Dependencies
- Phase 1.1, 1.2, 1.3, 1.4 all completed (all endpoints functional)

---

## Phase 1.6: Data Quality, Monitoring & Documentation

**Duration:** 3-4 days
**Goal:** Implement data quality checks, monitoring endpoints, and comprehensive documentation

### Tasks

#### 1.6.1 Create Data Quality Endpoints
- [ ] **GET /api/v1/status/data-quality**
  - Query:
    - Total securities count
    - OHLCV coverage for last trading day (% of securities with data)
    - Market cap coverage (% of securities with latest market cap)
    - Industry classification coverage (% of securities with industry data)
    - Gap detection: Missing dates in OHLCV for top 50 securities (sample)
  - Return JSON report

- [ ] **GET /api/v1/status/ingestion**
  - Create new table: `ingestion_logs`
    ```sql
    CREATE TABLE ingestion_logs (
      id SERIAL PRIMARY KEY,
      source VARCHAR(50),  -- 'nse_securities', 'upstox_ohlcv', etc.
      status VARCHAR(20),  -- 'success', 'failure', 'partial'
      records_fetched INTEGER,
      records_inserted INTEGER,
      records_failed INTEGER,
      errors JSONB,
      execution_time_ms INTEGER,
      timestamp TIMESTAMP DEFAULT NOW()
    );
    ```
  - Update all ingestion endpoints to log to this table
  - Query latest status for each source
  - Return summary

#### 1.6.2 Implement Logging Infrastructure
- [ ] Configure structured logging (JSON format)
  ```python
  # utils/logger.py
  import logging
  from pythonjsonlogger import jsonlogger

  def get_logger(name):
      logger = logging.getLogger(name)
      handler = logging.FileHandler('/app/logs/screener.log')
      formatter = jsonlogger.JsonFormatter(
          '%(timestamp)s %(level)s %(name)s %(message)s'
      )
      handler.setFormatter(formatter)
      logger.addHandler(handler)
      logger.setLevel(logging.INFO)
      return logger
  ```
- [ ] Add logging to all services:
  - Log start/end of each function
  - Log errors with full traceback
  - Log API requests (URL, status code, response time)

#### 1.6.3 Create Data Quality Checker Script
Create `scripts/data_quality_check.py`:
- [ ] Check for duplicates in time-series tables
- [ ] Check for OHLC consistency violations (high < low, etc.)
- [ ] Check for outliers (>20% daily price moves)
- [ ] Check for gaps in date sequences
- [ ] Generate report and email if issues found

#### 1.6.4 Set Up Automated Backups
Create `scripts/backup.sh`:
```bash
#!/bin/bash
# Daily PostgreSQL backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="screener_db"

# Create backup
docker exec screener_postgres pg_dump -U screener_user $DB_NAME | gzip > $BACKUP_DIR/screener_db_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "screener_db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: screener_db_$DATE.sql.gz"
```
- [ ] Add to cron: `0 2 * * * /path/to/backup.sh` (daily at 2 AM)

#### 1.6.5 Update README.md
- [ ] **Installation Instructions**
  - Prerequisites (Docker, Docker Compose)
  - Clone repository
  - Set up `.env` file
  - Build and start containers
  - Access n8n and import workflows

- [ ] **Configuration**
  - Upstox API credentials setup
  - Environment variables explanation

- [ ] **Usage**
  - How to trigger historical backfill
  - How to monitor workflows (n8n UI)
  - How to check data quality
  - API documentation link

- [ ] **Troubleshooting**
  - Common errors and solutions
  - How to view logs
  - How to restart containers

- [ ] **Architecture Overview**
  - Link to Architecture.md
  - High-level diagram

#### 1.6.6 Create API Documentation
- [ ] Ensure all endpoints have Pydantic models with descriptions
- [ ] Add docstrings to all endpoint functions
- [ ] Access auto-generated docs at `http://localhost:8000/docs`
- [ ] Export OpenAPI spec: `http://localhost:8000/openapi.json`
- [ ] Create Postman collection (optional)

#### 1.6.7 Final Integration Testing
- [ ] **End-to-End Test:**
  - Fresh database (drop and recreate)
  - Run historical backfill for 10 symbols
  - Trigger daily EOD workflow (test mode)
  - Query data via API endpoints
  - Check data quality endpoint
  - Verify logs

- [ ] **Performance Testing:**
  - Time OHLCV query for 5-year data (single symbol)
  - Time screener-like query (filter by market cap, RS, etc.)
  - Verify response times <1 second

- [ ] **Error Recovery Testing:**
  - Simulate Upstox API failure (mock 503 error)
  - Verify retry logic works
  - Simulate NSE website down
  - Verify error logging and notifications

#### 1.6.8 Create Runbook
Create `RUNBOOK.md`:
- [ ] **Daily Operations:**
  - Verify daily EOD workflow success (check email/Slack)
  - Monitor data quality dashboard
  - Review error logs

- [ ] **Weekly Operations:**
  - Verify industry classification update
  - Review data completeness

- [ ] **Monthly Operations:**
  - Update index constituents (manual CSV upload)
  - Review disk usage
  - Verify backups

- [ ] **Incident Response:**
  - Workflow failure → Check logs, retry manually
  - Database full → Cleanup old logs, resize volume
  - Upstox API quota exceeded → Contact Upstox support

### Success Criteria
- ✅ Data quality endpoint returns comprehensive metrics
- ✅ Ingestion logs tracked for all sources
- ✅ Structured logging implemented across all services
- ✅ Automated backups configured and tested
- ✅ README.md has complete setup instructions
- ✅ API documentation is accurate and comprehensive
- ✅ End-to-end test passes with 10 symbols
- ✅ Performance benchmarks met (<1s query response)

### Dependencies
- All previous phases (1.1-1.5) completed

---

## Phase 1 Completion Checklist

### Pre-Production Readiness

- [ ] **Database**
  - ✅ All 10 tables created with proper constraints
  - ✅ Indexes on key columns
  - ✅ 2000+ securities in `securities` table
  - ✅ Historical OHLCV data for ≥95% of universe (5 years)
  - ✅ Market cap data for ≥80% of universe (5 years or 1 year)
  - ✅ Industry classification coverage ≥95%

- [ ] **API Endpoints**
  - ✅ All ingestion endpoints functional
  - ✅ All query endpoints functional
  - ✅ Health and monitoring endpoints working
  - ✅ Error handling comprehensive
  - ✅ API documentation complete

- [ ] **n8n Workflows**
  - ✅ Daily EOD workflow scheduled and tested
  - ✅ Weekly industry workflow scheduled and tested
  - ✅ Historical backfill workflow tested
  - ✅ Error notifications configured
  - ✅ Workflow templates exported

- [ ] **Data Quality**
  - ✅ Data quality checks passing (≥95% completeness)
  - ✅ No duplicate records in time-series tables
  - ✅ OHLC consistency validated
  - ✅ Gap detection implemented

- [ ] **Monitoring & Observability**
  - ✅ Structured logging implemented
  - ✅ Ingestion logs tracked
  - ✅ Error alerts configured (email/Slack)
  - ✅ Data quality dashboard accessible

- [ ] **Operations**
  - ✅ Automated backups configured
  - ✅ README.md complete
  - ✅ Runbook created
  - ✅ Troubleshooting guide documented

- [ ] **Testing**
  - ✅ Unit tests pass (≥80% coverage target)
  - ✅ Integration tests pass
  - ✅ End-to-end test passes
  - ✅ Performance benchmarks met

- [ ] **Security**
  - ✅ No hardcoded credentials in code
  - ✅ Environment variables used for secrets
  - ✅ `.env` file gitignored
  - ✅ Database user has least privilege

### Sign-Off Criteria

**Before proceeding to Phase 2 (Calculation Engine & Screeners), verify:**

1. **Data Availability:**
   - Daily EOD workflow runs successfully for 30 consecutive days without manual intervention
   - Data quality score ≥95% consistently

2. **Performance:**
   - API response times <1 second for typical queries
   - Database can handle 10M+ records without degradation

3. **Reliability:**
   - No critical errors in last 7 days
   - Backup restore tested successfully

4. **Documentation:**
   - All stakeholders can set up the system using README.md
   - API documentation is accessible and accurate

---

## Post-Phase 1: Next Steps (Phase 2 Preview)

**Phase 2: Calculation Engine (Est. 4-6 weeks)**

### 2.1 Daily Metrics Calculation
- Implement calculation service for 30+ technical indicators
- Schedule post-EOD (after daily OHLCV ingestion)
- Store in `calculated_metrics` table

### 2.2 Screener Implementation
- Start with RRG Charts (priority #1)
- Implement remaining 10 screeners one by one
- Create screener API endpoints
- Build frontend dashboard (optional)

### 2.3 Performance Optimization
- Evaluate PostgreSQL performance with full dataset
- Consider ClickHouse migration if needed
- Implement caching (Redis) for frequently accessed data

---

## Risk Management

### High-Risk Items

| Risk | Mitigation | Contingency |
|------|-----------|-------------|
| **Upstox API rate limits** | Implement throttling, batch requests | Contact Upstox for increased quota |
| **NSE changes data format** | Add format validators, log warnings | Manual data fixes, alert on schema changes |
| **Database performance** | Index optimization, query profiling | Migrate to ClickHouse early |
| **n8n workflow failures** | Comprehensive error handling | Manual fallback scripts |
| **Disk space exhaustion** | Monitor disk usage, set up alerts | Automated cleanup, volume resize |

### Medium-Risk Items

| Risk | Mitigation |
|------|-----------|
| **Cookie expiration (NSE)** | Auto-refresh via Playwright |
| **Network timeouts** | Retry logic with exponential backoff |
| **Data quality issues** | Validation at ingestion, alerts |

---

## Resource Allocation

### Development Time Estimate

| Phase | Estimated Days | Developer Effort |
|-------|---------------|------------------|
| 0: Setup | 3-5 | 1 developer |
| 1.1: Models | 4-6 | 1 developer |
| 1.2: NSE Integration | 5-7 | 1 developer |
| 1.3: Upstox Integration | 6-8 | 1 developer |
| 1.4: Supporting Data | 5-7 | 1 developer |
| 1.5: n8n Workflows | 5-7 | 1 developer |
| 1.6: Quality & Docs | 3-4 | 1 developer |
| **Total Phase 1** | **31-44 days** | **6-9 weeks** |

### Infrastructure Requirements

**Local Development:**
- Docker Desktop (8GB RAM allocation recommended)
- 50 GB disk space (for PostgreSQL data)
- Internet connection (for data fetching)

**Cloud Deployment (Future):**
- VPS: 4 vCPU, 8 GB RAM, 100 GB SSD
- Estimated cost: $40-60/month (DigitalOcean, Linode)

---

## Appendix A: Quick Start Commands

### Setup
```bash
# Clone and setup
git clone <repo_url>
cd screener
cp .env.example .env
# Edit .env with your Upstox credentials

# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f fastapi
```

### Common Operations
```bash
# Restart API after code changes
docker-compose restart fastapi

# Access PostgreSQL
docker exec -it screener_postgres psql -U screener_user -d screener_db

# Run migrations
docker exec -it screener_api alembic upgrade head

# Trigger historical backfill (via n8n)
# Open http://localhost:5678, navigate to "Historical_Data_Backfill", click "Execute Workflow"

# View API docs
# Open http://localhost:8000/docs
```

### Troubleshooting
```bash
# View container logs
docker-compose logs fastapi
docker-compose logs postgres
docker-compose logs n8n

# Check disk usage
docker system df

# Cleanup unused volumes
docker volume prune

# Reset database (DANGER: deletes all data)
docker-compose down -v
docker-compose up -d
```

---

## Appendix B: Data Volume Estimates

**Assumptions:**
- 2,000 securities
- 5 years of historical data
- 250 trading days/year

**Storage Requirements:**

| Table | Records/Day | 5-Year Total | Size Estimate |
|-------|-------------|--------------|---------------|
| securities | - | 2,000 | <1 MB |
| indices | - | 100 | <1 MB |
| ohlcv_daily | 2,000 | 2.5M | ~500 MB |
| market_cap_history | 2,000 | 2.5M | ~400 MB |
| bulk_deals | ~50 | 62,500 | ~10 MB |
| block_deals | ~20 | 25,000 | ~5 MB |
| surveillance_measures | ~50 | - | ~5 MB |
| industry_classification | - | 2,000 | <1 MB |
| index_constituents | - | 5,000 | <1 MB |
| **Total (Phase 1)** | | **~5M records** | **~1 GB** |

**Phase 2 (Calculated Metrics):**
- Additional 2,000 × 250 × 5 = 2.5M records
- Estimated size: ~800 MB
- **Total with Phase 2:** ~2 GB

**Growth Rate:**
- Daily: +2,000 records (~1 MB/day)
- Annual: +500,000 records (~400 MB/year)

**Recommendation:** 50 GB disk allocation provides 10+ years of runway.

---

**Document Owner:** Development Team
**Last Updated:** November 16, 2025
**Next Review:** After Phase 1.1 Completion
