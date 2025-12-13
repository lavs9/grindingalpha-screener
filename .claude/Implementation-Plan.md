# Implementation Plan
## Indian Stock Market Screener Platform - Phase 1 (Data Storage)

**Version:** 1.2
**Date:** December 13, 2025
**Status:** In Progress - Phase 1.6 (Data Quality & OHLCV Ingestion)

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
- [x] Reorganize project structure with proper service separation
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

- [x] **Migration steps from current structure:**
  1. Create new `backend/` directory
  2. Move `screener_project/*` contents to `backend/app/`
  3. Reorganize into proper module structure (api/, services/, models/, etc.)
  4. Create `n8n/` directory with workflows subdirectory
  5. Update import paths in all Python files
  6. Update `docker-compose.yml` volume mounts to point to `backend/`
  7. Move `screener_project/requirements.txt` to `backend/requirements.txt`
  8. Archive old `screener_project/` folder (don't delete until migration verified)

#### 0.2 Environment Configuration
- [x] Create `.env.example` with all required variables
- [x] Generate `.env` file with actual secrets:
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
- [x] Update `.gitignore` to exclude `.env`, `__pycache__`, `venv/`, `logs/`, etc.

#### 0.3 Docker Setup
- [x] **Create `docker-compose.yml`** (root directory)
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

- [x] **Create `backend/Dockerfile`**
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

- [x] **Create `scripts/init_db.sql`** (database initialization)
  ```sql
  -- Create extensions if needed
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

  -- Grant privileges
  GRANT ALL PRIVILEGES ON DATABASE screener_db TO screener_user;
  ```

- [x] **Create `n8n/README.md`** (n8n setup instructions)
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

- [x] Test Docker build: `docker-compose build`
- [x] Test Docker startup: `docker-compose up -d`
- [x] Verify services:
  - PostgreSQL: `docker exec -it screener_postgres psql -U screener_user -d screener_db`
  - Backend: `curl http://localhost:8001/health`
  - n8n: Open `http://localhost:5678` in browser
- [x] Check container logs: `docker-compose logs -f`
- [x] Verify network connectivity: Backend can reach PostgreSQL, n8n can reach Backend

#### 0.4 Backend Code Refactoring
- [x] **Create `backend/app/core/config.py`** (centralized configuration)
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

- [x] **Migrate `database/db_helper.py` → `backend/app/database/session.py`**
  - Replace hardcoded credentials with `settings.database_url`
  - Add connection pooling: `pool_size=20, max_overflow=40`
  - Add health check function: `check_db_connection()`

- [x] **Create `backend/main.py`** (application entry point)
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

- [x] **Migrate existing code to new structure:**
  - `screener_project/database/` → `backend/app/database/`
  - `screener_project/data_ingester/` → `backend/app/services/nse/`
  - `screener_project/indexes_models/` → `backend/app/models/`
  - `screener_project/return_calculator/` → `backend/app/services/calculators/`
  - Update all import paths to use `app.` prefix

#### 0.5 Dependency Management
- [x] Update `requirements.txt`:
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
- [x] Install Playwright browsers: `playwright install chromium`

### Success Criteria
- ✅ Docker Compose stack runs successfully (all 3 containers healthy) - **COMPLETED**
- ✅ FastAPI `/health` endpoint returns 200 - **COMPLETED**
- ✅ PostgreSQL accepts connections from FastAPI container - **COMPLETED**
- ✅ n8n UI accessible and workflow can be created - **COMPLETED**
- ✅ No hardcoded credentials in codebase - **COMPLETED**
- ✅ Logs directory created and writable - **COMPLETED**

### Dependencies
None (foundational phase)

### Status: ✅ **PHASE 0 COMPLETED** (November 29, 2025)

---

## Phase 0.6: PostgreSQL 17 + Resource Monitoring Setup ✅ COMPLETED

**Duration:** 1-2 days
**Goal:** Set up PostgreSQL 17 with comprehensive resource monitoring for cloud sizing decisions

**Strategy:** Run everything locally with monitoring to determine actual vCPU/RAM needs before cloud deployment.

**Decision:** Using standard PostgreSQL 17 Alpine (not TimescaleDB) because:
- DigitalOcean Managed PostgreSQL uses Apache edition which lacks advanced TimescaleDB features
- Proper indexing on symbol + date columns provides excellent performance for our query patterns
- Simpler operational overhead and wider hosting options available

### Tasks

#### 0.6.1 PostgreSQL 17 Setup ✅
- [x] Update `docker-compose.yml` postgres service to use PostgreSQL 17 Alpine
- [x] Update `scripts/init_db.sql` to create uuid-ossp extension only
- [x] Remove TimescaleDB references from all documentation
- [x] Verify PostgreSQL 17 is running with proper extensions

#### 0.6.2 Add Resource Monitoring Stack
- [ ] Add monitoring services to `docker-compose.yml`:
  ```yaml
  # Prometheus for metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: screener_prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - screener_network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: screener_grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - screener_network
    depends_on:
      - prometheus

  # cAdvisor for container metrics
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: screener_cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    networks:
      - screener_network

  # Postgres Exporter for database metrics
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: screener_postgres_exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}?sslmode=disable"
    ports:
      - "9187:9187"
    networks:
      - screener_network
    depends_on:
      - postgres

  volumes:
    prometheus_data:
    grafana_data:
  ```

#### 0.6.3 Create Prometheus Configuration
- [ ] Create `monitoring/prometheus.yml`:
  ```yaml
  global:
    scrape_interval: 15s
    evaluation_interval: 15s

  scrape_configs:
    # FastAPI backend metrics
    - job_name: 'backend'
      static_configs:
        - targets: ['backend:8000']

    # PostgreSQL metrics
    - job_name: 'postgres'
      static_configs:
        - targets: ['postgres_exporter:9187']

    # Container metrics
    - job_name: 'cadvisor'
      static_configs:
        - targets: ['cadvisor:8080']

    # n8n metrics (if available)
    - job_name: 'n8n'
      static_configs:
        - targets: ['n8n:5678']
  ```

#### 0.6.4 Add Prometheus Metrics to FastAPI
- [ ] Install dependencies: `pip install prometheus-fastapi-instrumentator`
- [ ] Update `backend/main.py`:
  ```python
  from prometheus_fastapi_instrumentator import Instrumentator

  app = FastAPI(...)

  # Add Prometheus metrics
  Instrumentator().instrument(app).expose(app, endpoint="/metrics")
  ```
- [ ] Custom metrics for calculations:
  ```python
  # backend/app/utils/metrics.py
  from prometheus_client import Counter, Histogram, Gauge

  calculation_duration = Histogram(
      'calculation_duration_seconds',
      'Time spent on metric calculations',
      ['metric_type']
  )

  memory_usage = Gauge(
      'backend_memory_mb',
      'Backend memory usage in MB'
  )

  calculation_errors = Counter(
      'calculation_errors_total',
      'Total calculation errors',
      ['error_type']
  )
  ```

#### 0.6.5 Create Grafana Dashboards
- [ ] Create `monitoring/grafana/datasources/prometheus.yml`:
  ```yaml
  apiVersion: 1
  datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
  ```

- [ ] Create `monitoring/grafana/dashboards/dashboard.yml`:
  ```yaml
  apiVersion: 1
  providers:
    - name: 'Screener Dashboards'
      folder: ''
      type: file
      options:
        path: /etc/grafana/provisioning/dashboards
  ```

- [ ] Create dashboard JSON files:
  - `monitoring/grafana/dashboards/backend_resources.json` - Backend CPU/RAM
  - `monitoring/grafana/dashboards/database_performance.json` - PostgreSQL metrics
  - `monitoring/grafana/dashboards/calculation_performance.json` - Phase 2 metrics

#### 0.6.6 Create Resource Monitoring Guide
- [ ] Create `monitoring/README.md`:
  ```markdown
  # Resource Monitoring Guide

  ## Access Dashboards
  - Grafana: http://localhost:3000 (admin/admin)
  - Prometheus: http://localhost:9090
  - cAdvisor: http://localhost:8080

  ## Key Metrics to Monitor

  ### Backend (Phase 2 Calculations)
  - CPU usage during daily calculations
  - RAM usage peak (determine vCPU tier)
  - Calculation duration (target: <1 hour)

  ### Database
  - Query duration (target: <1s)
  - Connection pool usage
  - Disk I/O (for compression decision)
  - Table sizes (compression effectiveness)

  ### Container Resource Usage
  - Backend container: CPU/RAM/Disk
  - PostgreSQL container: CPU/RAM/Disk

  ## Cloud Sizing Decision Matrix

  **Backend Specs (based on Phase 2 monitoring):**
  | Peak RAM | vCPU Needed | DigitalOcean Plan | Cost |
  |----------|-------------|-------------------|------|
  | <2 GB    | 1 vCPU      | Basic ($6/mo)     | $6   |
  | 2-4 GB   | 2 vCPU      | Basic ($12/mo)    | $12  |
  | 4-8 GB   | 2-4 vCPU    | General Purpose   | $24  |

  **Database Specs (already decided):**
  - 1 vCPU, 1 GB RAM, 10 GB storage = $15/month

  ## Monitoring Commands
  ```bash
  # Check container stats
  docker stats

  # View Prometheus targets
  curl http://localhost:9090/api/v1/targets

  # Query metrics manually
  curl http://localhost:8000/metrics
  ```
  ```

#### 0.6.7 Add Resource Usage Logging
- [ ] Create `backend/app/utils/resource_logger.py`:
  ```python
  import psutil
  import logging
  from datetime import datetime

  logger = logging.getLogger(__name__)

  def log_resource_usage(operation: str):
      """Log CPU and RAM usage before/after operations"""
      process = psutil.Process()
      memory_mb = process.memory_info().rss / 1024 / 1024
      cpu_percent = process.cpu_percent(interval=1)

      logger.info(
          f"Resource usage during {operation}: "
          f"RAM={memory_mb:.2f}MB, CPU={cpu_percent}%"
      )

      return {
          "operation": operation,
          "timestamp": datetime.utcnow(),
          "memory_mb": memory_mb,
          "cpu_percent": cpu_percent
      }
  ```

- [ ] Integrate in calculation endpoints:
  ```python
  # backend/app/services/calculators/technical.py
  from app.utils.resource_logger import log_resource_usage

  def calculate_all_metrics(symbols: List[str]):
      log_resource_usage("start_calculations")

      # Perform calculations
      results = []
      for symbol in symbols:
          # Calculate metrics
          pass

      log_resource_usage("end_calculations")
      return results
  ```

### Success Criteria
- ✅ PostgreSQL 17 Alpine running successfully
- ✅ Prometheus collecting metrics from all services (4 targets: backend, postgres, cadvisor, prometheus)
- ✅ Grafana accessible at http://localhost:3000 (admin/screener_grafana_2024)
- ✅ cAdvisor showing container resource usage
- ✅ FastAPI `/metrics` endpoint exposing Prometheus metrics
- ✅ Postgres Exporter tracking database metrics (size, connections, cache hit ratio)
- ✅ Resource monitoring utility created (`backend/app/utils/resource_monitor.py`)
- ✅ Comprehensive monitoring guide documented ([MONITORING_SETUP.md](MONITORING_SETUP.md))

### Dependencies
- Phase 0 (Docker setup) completed ✅

### Status: ✅ **COMPLETED** (December 12, 2025)

**Implementation Summary:**
- All 7 Docker containers running: postgres, backend, n8n, prometheus, grafana, cadvisor, postgres_exporter
- Removed TimescaleDB (using standard PostgreSQL 17 for better hosting compatibility)
- Monitoring stack ready for Phase 1 data ingestion resource tracking

---

## Phase 1.1: Core Database Models & Schema

**Duration:** 4-6 days
**Goal:** Create all database models and set up migration framework

### Tasks

#### 1.1.1 Set Up Alembic for Database Migrations
- [x] Initialize Alembic: `alembic init alembic`
- [x] Configure `alembic.ini` to use environment variables
- [x] Update `alembic/env.py` to import SQLAlchemy models
- [x] Test migration: `alembic revision --autogenerate -m "Initial schema"`
- [x] Apply migration: `alembic upgrade head`

#### 1.1.2 Create Master Table Models
Create SQLAlchemy models in `database/models.py`:

- [x] **Securities Model**
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

- [x] **Indices Model**
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

- [x] **Industry Classification Model**
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

- [x] **Market Holidays Model**
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
- [x] **OHLCV Daily Model**
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

- [x] **Market Cap History Model**
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
- [x] **Bulk Deals Model**
- [x] **Block Deals Model** (same schema as bulk deals)
- [x] **Surveillance Measures Model**

#### 1.1.5 Create Join Table Models
- [x] **Index Constituents Model** (M:N relationship) - **Added in Phase 1.5**

#### 1.1.6 Generate and Apply Migrations
- [x] Generate migration: `alembic revision --autogenerate -m "Create all tables"`
- [x] Review auto-generated migration in `alembic/versions/`
- [x] Apply migration: `alembic upgrade head`
- [x] Verify tables in PostgreSQL:
  ```sql
  \dt  -- List all tables
  \d securities  -- Describe securities table
  ```

#### 1.1.7 Create Pydantic Schemas
Create schemas in `database/schemas.py` for request/response validation:
- [x] `SecurityCreate`, `SecurityResponse`
- [x] `OHLCVCreate`, `OHLCVResponse`
- [x] `MarketCapCreate`, `MarketCapResponse`
- [x] `BulkDealCreate`, `BlockDealCreate`, `SurveillanceCreate`, `SurveillanceResponse`
- [x] `IndustryClassificationCreate`, `IndexConstituentCreate` - **Added in Phase 1.5**

### Success Criteria
- ✅ All 15 tables created in PostgreSQL (11 planned + 4 surveillance variants) - **COMPLETED**
- ✅ Constraints (foreign keys, unique, check) enforced - **COMPLETED**
- ✅ Indexes created on key columns - **COMPLETED**
- ✅ Alembic migrations work forward and backward (`upgrade`/`downgrade`) - **COMPLETED**
- ✅ Pydantic schemas validate sample data - **COMPLETED**

### Dependencies
- Phase 0 (Environment setup) completed

### Status: ✅ **PHASE 1.1 COMPLETED** (November 29, 2025)

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

**Duration:** 6-8 days (Completed in 1 day)
**Goal:** Integrate Upstox API for authentication, instrument mapping, and data fetching

**Status:** ✅ **PHASE 1.3 COMPLETED** (December 4, 2025)

**IMPORTANT:** Before implementing API integrations, refer to [.claude/file-formats.md](.claude/file-formats.md) Section 5 (Upstox API Responses) for exact response structures and field mappings.

**Implementation Notes:**
- **Database-backed token storage** instead of SDK-only approach for better persistence
- **Playwright automation** for OAuth flow (with manual fallback due to redirect timeout)
- **Full instrument ingestion** (64,699 instruments from NSE.json.gz)
- **Auto-mapping success rate:** 87.5% (1,924 of 2,200 securities mapped with 100% confidence via ISIN)
- **Test endpoints created** for validation (market quotes, historical data, holidays)
- **Exchange filter fix:** Changed from `NSE_EQ` to `NSE` with `instrument_type='EQ'` for correct mapping
- **Known limitations:** OAuth redirect timeout (webhook.site workaround), 12.5% securities unmapped automatically

### Tasks

#### 1.3.1 Set Up Upstox SDK
- [x] Install Upstox Python SDK dependencies: `pyotp==2.9.0`, `pytz==2024.1`
- [x] Study Upstox API documentation and authentication flow
- [x] Create database-backed token manager (`services/upstox/token_manager.py`):
  ```python
  # Implemented: UpstoxTokenManager with IST timezone support
  # Location: backend/app/services/upstox/token_manager.py
  # Features: get_active_token(), store_token() with 23:59 IST expiry
  ```
- [x] Create Upstox API client helper (`services/upstox/upstox_client.py`):
  ```python
  # Implemented: UpstoxClient with get_headers() method
  # Uses token_manager to fetch active token for API calls
  ```

#### 1.3.2 Implement Database Models for Upstox
- [x] Create `UpstoxToken` model for token storage (23:59 IST daily expiry)
- [x] Create `UpstoxInstrument` model for caching 64,699+ instruments
- [x] Create `SymbolInstrumentMapping` model for auto-mapping securities to instrument keys
- [x] Generate Alembic migration: `alembic revision --autogenerate -m "Add Upstox tables"`
- [x] Apply migration: `alembic upgrade head`

#### 1.3.3 Implement Upstox Authentication
- [x] Create Playwright-based authentication service (`services/upstox/auth_service.py`):
  - Navigate to Upstox authorization dialog
  - Enter mobile number
  - Generate and enter TOTP-based OTP
  - Enter PIN
  - Extract authorization code
  - Exchange code for access token
- [x] Create authentication endpoint: `POST /api/v1/auth/upstox/login`
- [x] Add environment variables to `docker-compose.yml`: UPSTOX_REDIRECT_URI, UPSTOX_MOBILE, UPSTOX_PIN, UPSTOX_TOTP_SECRET

#### 1.3.4 Implement Instrument Key Mapping
- [x] Upstox uses `instrument_key` format: `NSE_EQ|INE002A01018` (exchange|instrument_type|ISIN)
- [x] Download and parse NSE.json.gz from Upstox (64,699 instruments)
- [x] Create auto-mapping function:
  ```python
  # Implemented: Auto-mapping via ISIN (primary) and symbol (fallback)
  # Location: backend/app/services/upstox/instrument_service.py
  # Function: create_symbol_mappings()
  # Results: 1,924 mappings created (87.5% of 2,200 securities)
  # Confidence: 100.00% for ISIN matches, 90.00% for symbol-only matches
  ```
- [x] Create instrument ingestion service (`services/upstox/instrument_service.py`):
  - `fetch_upstox_instruments()`: Download NSE.json.gz
  - `ingest_upstox_instruments()`: Bulk UPSERT (batch size: 500)
  - `create_symbol_mappings()`: Auto-match by ISIN/symbol
- [x] Create ingestion endpoint: `POST /api/v1/ingest/upstox-instruments`

#### 1.3.5 Create Test Endpoints for Validation
- [x] **GET /api/v1/auth/upstox/token-status** - Check token validity
- [x] **GET /api/v1/auth/upstox/test-api** - Verify user profile (token test)
- [x] **GET /api/v1/auth/upstox/test-market-quotes?symbol=RELIANCE** - Fetch live quotes
- [x] **GET /api/v1/auth/upstox/test-historical-data?symbol=RELIANCE** - Fetch OHLCV data (30 days)
- [x] **GET /api/v1/auth/upstox/test-market-holidays?date=2025-12-04** - Fetch holiday calendar

#### 1.3.6 Testing & Validation
- [x] **Authentication Testing:**
  - Token storage with 23:59 IST expiry verified
  - Manual token refresh working (OAuth timeout workaround)

- [x] **Instrument Ingestion Testing:**
  - 64,699 instruments ingested (93.5% success rate)
  - 1,924 symbol mappings created (87.5% of securities)
  - All mappings use 100% confidence (ISIN-based matching)

- [x] **API Integration Testing:**
  - User profile endpoint: ✅ Working
  - Market quotes: ✅ Working (live OHLC data for RELIANCE)
  - Historical data: ✅ Working (30 days OHLCV for RELIANCE)
  - Market holidays: ✅ Working (holiday calendar retrieved)

#### 1.3.7 Implementation Deviations from Original Plan
- **Authentication:** Implemented database-backed token storage instead of SDK-only approach for better persistence across container restarts
- **OAuth Flow:** Playwright automation times out at redirect step; using manual token refresh as workaround (production solution: create `/callback` endpoint)
- **Instrument Mapping:** Implemented full ingestion (64,699 instruments) instead of on-demand mapping for better performance
- **Exchange Filter:** Fixed from `exchange='NSE_EQ'` to `exchange='NSE'` with `instrument_type='EQ'` to match actual Upstox data format
- **Testing:** Created comprehensive test endpoints instead of unit tests for faster validation
- **Historical OHLCV:** ✅ Implemented in Phase 1.6 (batch endpoint created)
- **Daily OHLCV:** ✅ Implemented in Phase 1.6 (daily endpoint created)
- **Market Holidays:** Test endpoint created; full ingestion deferred to Phase 1.6

### Success Criteria (Actual Results)
- ✅ **Upstox authentication configured** with database-backed token storage (23:59 IST expiry)
- ✅ **Instrument mapping completed** - 64,699 instruments ingested, 1,924 securities mapped (87.5%)
- ✅ **API integration validated** - All test endpoints working (quotes, historical data, holidays)
- ✅ **Token management working** - Active token retrieval, expiry detection, manual refresh capability
- ✅ **Error handling implemented** - Graceful handling of API errors, database conflicts, missing mappings
- ⚠️ **OAuth flow partially working** - Playwright automation times out at redirect; manual fallback functional
- ✅ **Historical OHLCV ingestion** - Completed in Phase 1.6 (POST /api/v1/ingest/historical-ohlcv-batch)
- ✅ **Daily OHLCV ingestion** - Completed in Phase 1.6 (POST /api/v1/ingest/daily-ohlcv)
- ⏳ **Market holidays full ingestion** - Test endpoint working, full ingestion deferred to Phase 1.6

### Files Created/Modified
**New Files (13):**
- `backend/app/models/upstox.py` (3 models: UpstoxToken, UpstoxInstrument, SymbolInstrumentMapping)
- `backend/app/schemas/upstox.py` (Request/response schemas)
- `backend/app/services/upstox/token_manager.py` (Token lifecycle management)
- `backend/app/services/upstox/auth_service.py` (Playwright OAuth automation)
- `backend/app/services/upstox/instrument_service.py` (Instrument ingestion + mapping)
- `backend/app/services/upstox/upstox_client.py` (API client helper)
- `backend/app/api/v1/auth.py` (Authentication + test endpoints)
- `backend/alembic/versions/f5d9c4b8e2a1_add_upstox_tables.py` (Migration)

**Modified Files (3):**
- `backend/app/models/__init__.py` (Export Upstox models)
- `backend/app/schemas/__init__.py` (Export Upstox schemas)
- `backend/main.py` (Register auth router)
- `docker-compose.yml` (Add 4 Upstox env vars)
- `backend/requirements.txt` (Add pyotp, pytz)

### Dependencies
- ✅ Phase 1.1 (Database models) completed
- ✅ Phase 1.2 (NSE integration) completed (for securities list)

---

## Phase 1.4: Supporting Data Sources (Industry/Sector, Index Constituents)

**Duration:** 5-7 days
**Goal:** Automate industry classification scraping and implement index constituents management

**NOTE:** This phase was implemented ahead of schedule (before Upstox integration) at user request.

**IMPORTANT:** Refer to [.claude/file-formats.md](.claude/file-formats.md) Section 7 (NSE Industry Classification) and Section 6 (Index Constituents) for exact formats.

### Tasks

#### 1.4.1 Set Up Playwright for NSE Scraping
- [x] Install Playwright: `pip install playwright`
- [x] Install browsers: `playwright install chromium`
- [x] Test Playwright:
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
Create `services/nse/industry_service.py`:

- [x] **Class: `NSECookieManager`** (Playwright-based async cookie management with auto-refresh)
- [x] **Function: `fetch_quote_data(symbol, cookie_manager)`** (Async HTTP request with cookie auth)
- [x] **Function: `parse_industry_classification(quote_data, symbol)`** (Extract 4-level hierarchy)
- [x] **Function: `parse_index_constituents(quote_data, symbol, scrape_date)`** (Extract pdSectorIndAll array)
- [x] **Function: `scrape_all_securities(db, limit, symbols)`** (Main orchestrator with rate limiting)
- [x] **Function: `process_index_constituents(db, symbol_list, cookie_manager, scrape_date)`** (Entry/exit tracking)
- [x] **Function: `upsert_industry_classification(db, industry_data)`** (UPSERT pattern)
- [x] **Function: `ensure_indices_exist(db, index_names)`** (Auto-create indices from API data)
- [x] **Function: `get_industry_by_symbol(db, symbol)`** (Query helper)
- [x] **Function: `get_index_constituents(db, index_name, as_of_date)`** (Query with historical support)

#### 1.4.3 Create Industry Classification Endpoint
- [x] **POST /api/v1/ingest/industry-classification**
  - Query parameters: `limit` (optional), `symbols` (optional array)
  - Call `scrape_all_securities(db, limit, symbols)`
  - Upsert to `industry_classification` table
  - Auto-create indices and track constituents
  - Return summary: `{success, total_symbols, symbols_processed, symbols_failed, industry_records, index_constituent_records, errors, duration_seconds}`

#### 1.4.4 Implement Index Constituents Management
- [x] **Automated Index Constituent Tracking** (via NSE Quote API pdSectorIndAll field)
  - Index names extracted from API response
  - Auto-create indices in `indices` table if missing
  - Track entry/exit with `effective_from`/`effective_to` dates
  - Compare current API state with database state to detect changes
  - Insert new constituents with `effective_from = scrape_date`
  - Mark removed constituents with `effective_to = scrape_date - 1`
  - NULL `effective_to` indicates current membership

- [x] **Pydantic Schemas Created:**
  - `IndustryClassificationBase/Create/Response`
  - `IndexConstituentBase/Create/Response`
  - `IndustryIngestionRequest/Response`
  - `IndexConstituentListResponse`
  - `IndustryStatsResponse`

#### 1.4.5 Database Schema Enhancements
- [x] Created `index_constituents` table with historical tracking
- [x] Added Alembic migration `33796dd55aff` for `index_constituents` table
- [x] Added Alembic migration `725e3b233476` to increase `indices.symbol` from VARCHAR(50) to VARCHAR(100)
- [x] Added composite indexes for efficient querying:
  - `idx_index_constituents_active` (partial index for active constituents)
  - `idx_index_constituents_dates` (for date range queries)
  - `idx_index_constituents_symbol_date` (for symbol-based queries)

#### 1.4.6 Testing
- [x] **Industry Scraper Tests:**
  - Tested cookie extraction with Playwright (verified _abck, nsit, nseappid cookies)
  - Tested 3 symbols (RELIANCE, TCS, INFY) - all successful
  - Verified 403 handling with automatic cookie refresh
  - Verified rate limiting (1 second delay between requests)
  - Execution time: 17 seconds for 3 symbols

- [x] **Index Constituents Tests:**
  - Auto-created 50 unique indices from NSE API data
  - Created 107 index constituent relationships (RELIANCE: 32, TCS: 40, INFY: 35)
  - Verified historical tracking with proper `effective_from` dates
  - Verified database integrity with foreign key constraints

- [x] **Data Verification:**
  - Confirmed 3 industry classification records with full 4-level hierarchy
  - Verified RELIANCE classification: Energy > Oil Gas & Consumable Fuels > Petroleum Products > Refineries & Marketing
  - All data properly timestamped

### Success Criteria
- ✅ Playwright successfully navigates NSE and extracts cookies - **COMPLETED**
- ✅ Industry classification scraped for 100% of test symbols (3/3 success) - **COMPLETED**
- ✅ Cookie refresh mechanism works (handles 403 errors with max 3 retries) - **COMPLETED**
- ✅ Index constituents auto-extracted from NSE Quote API - **COMPLETED**
- ✅ Historical tracking works (effective_from/effective_to dates) - **COMPLETED**
- ✅ Auto-create indices from API data - **COMPLETED**
- ✅ Entry/exit detection logic functional - **COMPLETED**

### Dependencies
- Phase 1.1 (Database models) completed

### Status: ✅ **PHASE 1.4 COMPLETED** (November 30, 2025)

**Implementation Notes:**
- Implemented using async/await pattern for better performance
- Used Playwright async API instead of sync API
- Added comprehensive error handling with detailed error messages
- Fixed Pydantic 2.6 import issues (`date: date` → `date: date_type`)
- Fixed Index model bugs (column name mismatches)
- Added missing Playwright dependencies (libpango, libcairo) to Dockerfile
- Changed Docker ports to avoid conflicts (PostgreSQL: 5433, Backend: 8001)
- Weightage field remains NULL (not available in NSE Quote API)

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
  - If all success → Telegram notification (non-urgent)
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

**Status:** ⏳ **IN PROGRESS** - OHLCV ingestion endpoints completed (December 13, 2025)

### Tasks

#### 1.6.0 OHLCV Data Ingestion ✅ COMPLETED
- [x] **Create `ingestion_logs` table**
  - Migration: `e9dd4cc896bc_add_ingestion_logs_table.py` ✅
  - Table structure: id, source, status, records_fetched, records_inserted, records_updated, records_failed, errors (JSON), execution_time_ms, timestamp
  - Indexes: source+timestamp, timestamp

- [x] **POST /api/v1/ingest/historical-ohlcv-batch**
  - Batch processing for historical OHLCV data (default: 5 years)
  - Features: Batch size control (default: 50), resource monitoring, error handling
  - Uses existing `BatchHistoricalService`
  - Logs results to `ingestion_logs` table
  - Test results: 3 symbols, 78 records, 931ms execution time ✅

- [x] **POST /api/v1/ingest/daily-ohlcv**
  - Single-day OHLCV ingestion (default: yesterday)
  - Designed for daily automated n8n workflows
  - Batch processing with error handling
  - Logs results to `ingestion_logs` table

**Known Issues:**
- `@monitor_resources` decorator has async compatibility issue (temporarily disabled with TODO comment)

#### 1.6.1 Create Data Quality Endpoints
- [ ] **GET /api/v1/status/data-quality**
  - Query:
    - Total securities count
    - OHLCV coverage for last trading day (% of securities with data)
    - Market cap coverage (% of securities with latest market cap)
    - Industry classification coverage (% of securities with industry data)
    - Gap detection: Missing dates in OHLCV for top 50 securities (sample)
  - Return JSON report

- [x] **GET /api/v1/status/ingestion** - Partially implemented
  - ✅ `ingestion_logs` table created and functional
  - ⏳ Need to create query endpoint to return latest status for each source
  - ⏳ Need to update remaining ingestion endpoints to log to this table

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
