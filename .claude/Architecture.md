# System Architecture Document
## Indian Stock Market Screener Platform

**Version:** 1.0
**Date:** November 16, 2025
**Status:** Planning Phase

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        External Data Sources                         │
├──────────────┬──────────────────┬──────────────────┬────────────────┤
│ NSE Archives │  NSE Website     │   Upstox API     │ Manual Upload  │
│ (CSV/ZIP)    │  (JSON w/Cookie) │   (REST + SDK)   │ (Index Const.) │
└──────┬───────┴────────┬─────────┴────────┬─────────┴────────┬───────┘
       │                │                  │                  │
       │                │                  │                  │
       ▼                ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    n8n Workflow Orchestration                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Daily EOD   │  │ Industry     │  │ Historical   │  │ Manual   │ │
│  │ Workflow    │  │ Scraper      │  │ Backfill     │  │ Triggers │ │
│  │ (Cron 8:30) │  │ (Weekly)     │  │ (One-time)   │  │          │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                │                  │                │       │
│         └────────────────┴──────────────────┴────────────────┘       │
│                                 │                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │ HTTP Requests
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Ingestion   │  │   Query      │  │   Health &   │              │
│  │  Endpoints   │  │  Endpoints   │  │  Monitoring  │              │
│  │              │  │              │  │              │              │
│  │ POST /ingest │  │ GET /        │  │ GET /health  │              │
│  │              │  │ securities   │  │ GET /status  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│         └─────────────────┴──────────────────┘                       │
│                           │                                          │
│  ┌────────────────────────┼──────────────────────────────────┐      │
│  │        Business Logic Layer                                │      │
│  │  ┌─────────────────────────────────────────────────────┐  │      │
│  │  │  Data Validators  │  Transformers  │  Calculators   │  │      │
│  │  └─────────────────────────────────────────────────────┘  │      │
│  └────────────────────────┬───────────────────────────────────┘      │
│                           │                                          │
└───────────────────────────┼──────────────────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Master     │  │ Time-Series │  │  Deals &    │  │  Lookup    │ │
│  │  Tables     │  │   Tables    │  │  Events     │  │  Tables    │ │
│  │             │  │             │  │             │  │            │ │
│  │ securities  │  │ ohlcv_daily │  │ bulk_deals  │  │ industry   │ │
│  │ indices     │  │ market_cap  │  │ block_deals │  │ holidays   │ │
│  │ etfs        │  │ calculated  │  │ surveillance│  │ index_cons │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                                       │
│  Indexes: Symbol+Date, ISIN, Industry, etc.                         │
│  Constraints: Foreign Keys, Unique Composites                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Future: ClickHouse Migration                       │
│  (Time-series data for faster aggregations on large datasets)       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Deployment Architecture (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Docker Compose Stack                            │
│                                                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   n8n           │    │   FastAPI       │    │  PostgreSQL     │ │
│  │                 │    │                 │    │                 │ │
│  │ Port: 5678      │───▶│ Port: 8000      │───▶│ Port: 5432      │ │
│  │ Image: n8nio/n8n│    │ Image: Custom   │    │ Image: postgres │ │
│  │                 │    │ (Dockerfile)    │    │ Version: 15     │ │
│  │ Workflows:      │    │                 │    │                 │ │
│  │ /home/node/.n8n │    │ Volumes:        │    │ Volumes:        │ │
│  │                 │    │ - ./app         │    │ - pgdata:/var   │
│  │                 │    │ - .env          │    │                 │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                       │
│  Network: screener_network (bridge)                                 │
│  Environment: .env file (shared secrets)                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.109.2 | REST API server |
| **ASGI Server** | Uvicorn | 0.27.1 | Production server |
| **Database** | PostgreSQL | 15+ | Primary data store |
| **ORM** | SQLAlchemy | 2.0.27 | Database abstraction |
| **DB Driver** | psycopg2-binary | 2.9.9 | PostgreSQL adapter |
| **Validation** | Pydantic | 2.6.1 | Data validation |
| **Data Processing** | Pandas | 2.2.0 | CSV/data manipulation |
| **Workflow Engine** | n8n | Latest | Automation orchestration |
| **Web Scraping** | Playwright | Latest | Browser automation (NSE) |
| **Market Data SDK** | Upstox Python SDK | Latest | Official API client |
| **Containerization** | Docker | 20.10+ | Local deployment |
| **Orchestration** | Docker Compose | 2.0+ | Multi-container mgmt |

### 2.2 Development Tools

| Tool | Purpose |
|------|---------|
| **Alembic** | Database migrations |
| **Pylint / Black** | Code linting / formatting |
| **pytest** | Unit/integration testing |
| **mypy** | Static type checking |
| **dotenv** | Environment variable management |

### 2.3 Future Technologies

| Technology | Purpose | Migration Timeline |
|-----------|---------|-------------------|
| **ClickHouse** | Time-series optimization | After 10M+ records or query degradation |
| **Redis** | Caching layer | Phase 2 (screener optimization) |
| **Celery** | Alternative to n8n for complex jobs | If n8n limitations encountered |
| **React/Vue.js** | Frontend dashboard | Phase 3 |

---

## 3. Database Design

### 3.1 Schema Overview

#### 3.1.1 Master Tables (Reference Data)

**Table: `securities`**
*Stores all listed equities and ETFs*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `symbol` | VARCHAR(50) | UNIQUE, NOT NULL | NSE trading symbol |
| `isin` | VARCHAR(12) | UNIQUE, NOT NULL | International identifier |
| `security_name` | VARCHAR(255) | NOT NULL | Full company name |
| `series` | VARCHAR(10) | | Trading series (EQ, BE, etc.) |
| `listing_date` | DATE | | Date of listing on NSE |
| `paid_up_value` | DECIMAL(15,2) | | Paid-up capital |
| `market_lot` | INTEGER | | Minimum lot size |
| `face_value` | DECIMAL(10,2) | | Face value per share |
| `security_type` | ENUM | NOT NULL | 'EQUITY' or 'ETF' |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active trading status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

**Indexes:**
- `idx_securities_symbol` (symbol)
- `idx_securities_isin` (isin)
- `idx_securities_type` (security_type)

---

**Table: `indices`**
*Stores NSE indices*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `index_name` | VARCHAR(100) | UNIQUE, NOT NULL | Index name (e.g., "Nifty 50") |
| `symbol` | VARCHAR(50) | UNIQUE, NOT NULL | Index symbol |
| `exchange` | VARCHAR(20) | DEFAULT 'NSE_INDEX' | Exchange identifier |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

**Indexes:**
- `idx_indices_symbol` (symbol)

---

**Table: `industry_classification`**
*Stores industry/sector mappings*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `symbol` | VARCHAR(50) | UNIQUE, NOT NULL | Security symbol |
| `macro` | VARCHAR(100) | | Highest-level category |
| `sector` | VARCHAR(100) | | Sector classification |
| `industry` | VARCHAR(100) | | Industry classification |
| `basic_industry` | VARCHAR(100) | | Most granular level |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last scrape date |

**Foreign Keys:**
- `symbol` → `securities.symbol` (ON DELETE CASCADE)

**Indexes:**
- `idx_industry_symbol` (symbol)
- `idx_industry_sector` (sector)
- `idx_industry_industry` (industry)

---

**Table: `market_holidays`**
*NSE market holidays calendar*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `holiday_date` | DATE | UNIQUE, NOT NULL | Holiday date |
| `holiday_name` | VARCHAR(255) | | Holiday description |
| `exchange` | VARCHAR(20) | DEFAULT 'NSE' | Exchange identifier |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Indexes:**
- `idx_holidays_date` (holiday_date)

---

#### 3.1.2 Time-Series Tables (High-Volume Data)

**Table: `ohlcv_daily`**
*Daily OHLCV data for all securities and indices*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `symbol` | VARCHAR(50) | NOT NULL | Security/index symbol |
| `date` | DATE | NOT NULL | Trading date |
| `open` | DECIMAL(15,2) | NOT NULL | Opening price |
| `high` | DECIMAL(15,2) | NOT NULL | High price |
| `low` | DECIMAL(15,2) | NOT NULL | Low price |
| `close` | DECIMAL(15,2) | NOT NULL | Closing price |
| `volume` | BIGINT | | Trading volume (NULL for indices) |
| `vwap` | DECIMAL(15,2) | | Volume-weighted avg price |
| `prev_close` | DECIMAL(15,2) | | Previous close |
| `change_pct` | DECIMAL(8,4) | | % change from prev close |
| `upper_circuit` | DECIMAL(15,2) | | Upper circuit limit |
| `lower_circuit` | DECIMAL(15,2) | | Lower circuit limit |
| `week_52_high` | DECIMAL(15,2) | | 52-week high |
| `week_52_low` | DECIMAL(15,2) | | 52-week low |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints:**
- UNIQUE (`symbol`, `date`)
- CHECK (`high >= low`)
- CHECK (`open BETWEEN low AND high`)
- CHECK (`close BETWEEN low AND high`)

**Foreign Keys:**
- `symbol` → `securities.symbol` OR `indices.symbol` (logical FK, not enforced for flexibility)

**Indexes:**
- `idx_ohlcv_symbol_date` (symbol, date DESC) **[PRIMARY QUERY INDEX]**
- `idx_ohlcv_date` (date DESC)

**Partitioning Strategy:**
- Phase 1: No partitioning (simpler, <10M records)
- Phase 2+: Monthly partitioning when data volume/performance requires it
- See Section 10 (Migration Strategy) for detailed implementation plan

---

**Table: `market_cap_history`**
*Daily market cap data*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `date` | DATE | NOT NULL | Trade date |
| `series` | VARCHAR(10) | | Trading series |
| `security_name` | VARCHAR(255) | | Security name (snapshot) |
| `category` | VARCHAR(50) | | Security category |
| `last_trade_date` | DATE | | Last trading date |
| `face_value` | DECIMAL(10,2) | | Face value |
| `issue_size` | BIGINT | | Issued shares |
| `close_price` | DECIMAL(15,2) | | Closing price |
| `market_cap` | DECIMAL(20,2) | NOT NULL | Market cap (₹ crore) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints:**
- UNIQUE (`symbol`, `date`)

**Foreign Keys:**
- `symbol` → `securities.symbol` (ON DELETE CASCADE)

**Indexes:**
- `idx_marketcap_symbol_date` (symbol, date DESC)
- `idx_marketcap_date` (date DESC)
- `idx_marketcap_value` (market_cap)

---

**Table: `calculated_metrics`** *(Phase 2)*
*Daily calculated technical indicators*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `date` | DATE | NOT NULL | Calculation date |
| `change_1d` | DECIMAL(8,4) | | 1-day % change |
| `change_1w` | DECIMAL(8,4) | | 1-week % change |
| `change_1m` | DECIMAL(8,4) | | 1-month % change |
| `change_3m` | DECIMAL(8,4) | | 3-month % change |
| `change_6m` | DECIMAL(8,4) | | 6-month % change |
| `rs_1d` | DECIMAL(6,2) | | RS percentile (1D) |
| `rs_1w` | DECIMAL(6,2) | | RS percentile (1W) |
| `rs_1m` | DECIMAL(6,2) | | RS percentile (1M) |
| `rs_3m` | DECIMAL(6,2) | | RS percentile (3M) |
| `rs_6m` | DECIMAL(6,2) | | RS percentile (6M) |
| `vars_1d` | DECIMAL(8,4) | | Volatility-Adjusted RS (1D) |
| `vars_1w` | DECIMAL(8,4) | | Volatility-Adjusted RS (1W) |
| `vars_1m` | DECIMAL(8,4) | | Volatility-Adjusted RS (1M) |
| `varw_1m` | DECIMAL(8,4) | | Volatility-Adjusted Weakness |
| `ema_10` | DECIMAL(15,2) | | 10-day EMA |
| `sma_20` | DECIMAL(15,2) | | 20-day SMA |
| `sma_50` | DECIMAL(15,2) | | 50-day SMA |
| `sma_100` | DECIMAL(15,2) | | 100-day SMA |
| `sma_200` | DECIMAL(15,2) | | 200-day SMA |
| `atr_14` | DECIMAL(15,4) | | 14-day ATR |
| `atr_pct` | DECIMAL(8,4) | | ATR % (ATR/Close × 100) |
| `atr_from_sma50` | DECIMAL(8,4) | | ATR extension from SMA50 |
| `adr_pct` | DECIMAL(8,4) | | Avg Daily Range % (20D) |
| `atr_extension` | DECIMAL(8,4) | | ATR extension metric |
| `darvas_high` | DECIMAL(15,2) | | 20-day Darvas box high |
| `darvas_low` | DECIMAL(15,2) | | 20-day Darvas box low |
| `darvas_pct` | DECIMAL(8,4) | | Price-to-range % |
| `rvol` | DECIMAL(8,4) | | Relative volume |
| `orh` | DECIMAL(15,2) | | Opening range high |
| `m30_reorh` | BOOLEAN | | M30 Re-ORH flag |
| `lod_atr_pct` | DECIMAL(8,4) | | LoD distance to ATR % |
| `vcp_score` | INTEGER | | VCP score (1-5) |
| `stage` | INTEGER | | Stage analysis (1-4) |
| `candle_type` | VARCHAR(10) | | 'GREEN' or 'RED' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints:**
- UNIQUE (`symbol`, `date`)

**Indexes:**
- `idx_metrics_symbol_date` (symbol, date DESC)
- `idx_metrics_vars_1m` (vars_1m DESC) **[Screener queries]**
- `idx_metrics_stage` (stage)

---

#### 3.1.3 Event Tables (Deals & Surveillance)

**Table: `bulk_deals`**
*NSE bulk deal transactions*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `date` | DATE | NOT NULL | Deal date |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `security_name` | VARCHAR(255) | | Security name |
| `client_name` | VARCHAR(255) | NOT NULL | Client/entity name |
| `deal_type` | VARCHAR(10) | NOT NULL | 'BUY' or 'SELL' |
| `quantity` | BIGINT | NOT NULL | Shares traded |
| `trade_price` | DECIMAL(15,2) | NOT NULL | Avg trade price |
| `remarks` | TEXT | | Additional notes |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints:**
- UNIQUE (`date`, `symbol`, `client_name`, `deal_type`) - same client may buy/sell same day

**Foreign Keys:**
- `symbol` → `securities.symbol`

**Indexes:**
- `idx_bulk_symbol_date` (symbol, date DESC)
- `idx_bulk_date` (date DESC)

---

**Table: `block_deals`**
*NSE block deal transactions (same schema as bulk_deals)*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `date` | DATE | NOT NULL | Deal date |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `security_name` | VARCHAR(255) | | Security name |
| `client_name` | VARCHAR(255) | NOT NULL | Client/entity name |
| `deal_type` | VARCHAR(10) | NOT NULL | 'BUY' or 'SELL' |
| `quantity` | BIGINT | NOT NULL | Shares traded |
| `trade_price` | DECIMAL(15,2) | NOT NULL | Avg trade price |
| `remarks` | TEXT | | Additional notes |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints & Indexes:** Same as `bulk_deals`

---

**Table: `surveillance_measures`**
*NSE surveillance actions*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-increment ID |
| `date` | DATE | NOT NULL | Action date |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `security_name` | VARCHAR(255) | | Security name |
| `surveillance_action` | VARCHAR(50) | | ASM, GSM, etc. |
| `reason` | TEXT | | Reason for action |
| `is_active` | BOOLEAN | DEFAULT TRUE | Current status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

**Constraints:**
- UNIQUE (`symbol`, `date`, `surveillance_action`)

**Foreign Keys:**
- `symbol` → `securities.symbol`

**Indexes:**
- `idx_surveillance_symbol` (symbol)
- `idx_surveillance_active` (is_active)

---

#### 3.1.4 Workflow Tracking Tables

**Table: `ingestion_logs`**
*Tracks all data ingestion operations for monitoring and debugging*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `source` | VARCHAR(50) | NOT NULL, INDEX | Data source identifier |
| `status` | VARCHAR(20) | NOT NULL | 'success', 'failure', 'partial' |
| `records_fetched` | INTEGER | DEFAULT 0 | Records retrieved from source |
| `records_inserted` | INTEGER | DEFAULT 0 | Records successfully inserted |
| `records_failed` | INTEGER | DEFAULT 0 | Records that failed validation |
| `errors` | JSONB | | Error details (if any) |
| `execution_time_ms` | INTEGER | | Execution duration in milliseconds |
| `timestamp` | TIMESTAMP | DEFAULT NOW(), INDEX | Execution timestamp |
| `workflow_id` | VARCHAR(100) | | n8n workflow execution ID (optional) |

**Source Values:**
- `nse_securities` - NSE listed securities fetch
- `nse_etfs` - NSE ETF list fetch
- `nse_market_cap` - Market cap data fetch
- `nse_bulk_deals` - Bulk deals fetch
- `nse_block_deals` - Block deals fetch
- `nse_surveillance` - Surveillance measures fetch
- `nse_industry` - Industry classification scrape
- `upstox_historical` - Historical OHLCV backfill
- `upstox_daily` - Daily OHLCV fetch
- `upstox_holidays` - Market holidays fetch
- `manual_index_constituents` - Manual index constituents upload

**Indexes:**
- `idx_ingestion_source_timestamp` (source, timestamp DESC)
- `idx_ingestion_status` (status)

**Usage:**
- Each ingestion endpoint logs execution results to this table
- n8n workflows query this table for aggregation (instead of relying on workflow state)
- Data quality dashboard queries this table for last successful fetch timestamps

---

#### 3.1.5 Join Tables

**Table: `index_constituents`**
*M:N relationship between indices and securities*

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `index_id` | INTEGER | NOT NULL | Index reference |
| `symbol` | VARCHAR(50) | NOT NULL | Security symbol |
| `company_name` | VARCHAR(255) | | Company name |
| `industry` | VARCHAR(100) | | Industry (from file) |
| `weightage` | DECIMAL(6,4) | | Weightage in index (%) |
| `effective_from` | DATE | NOT NULL | Start date |
| `effective_to` | DATE | | End date (NULL = current) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Constraints:**
- UNIQUE (`index_id`, `symbol`, `effective_from`)

**Foreign Keys:**
- `index_id` → `indices.id` (ON DELETE CASCADE)
- `symbol` → `securities.symbol` (ON DELETE CASCADE)

**Indexes:**
- `idx_constituents_index` (index_id)
- `idx_constituents_symbol` (symbol)
- `idx_constituents_current` (effective_to IS NULL)

---

### 3.2 Entity Relationship Diagram (ERD)

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   securities    │         │     indices      │         │industry_classif │
├─────────────────┤         ├──────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)          │         │ id (PK)         │
│ symbol (UQ)     │─────┐   │ index_name (UQ)  │   ┌─────│ symbol (FK,UQ)  │
│ isin (UQ)       │     │   │ symbol (UQ)      │   │     │ macro           │
│ security_name   │     │   │ exchange         │   │     │ sector          │
│ series          │     │   │ is_active        │   │     │ industry        │
│ listing_date    │     │   │ created_at       │   │     │ basic_industry  │
│ paid_up_value   │     │   │ updated_at       │   │     │ updated_at      │
│ market_lot      │     │   └──────────────────┘   │     └─────────────────┘
│ face_value      │     │            │              │
│ security_type   │     │            │              │
│ is_active       │     │            │              │
│ created_at      │     │            │              │
│ updated_at      │     │            │              │
└─────────────────┘     │            │              │
         │              │            │              │
         │              │            │              │
         │              │    ┌───────▼──────────────▼──────┐
         │              │    │   index_constituents (M:N)  │
         │              └───▶│─────────────────────────────│
         │                   │ id (PK)                     │
         │                   │ index_id (FK)               │
         │                   │ symbol (FK)                 │
         │                   │ company_name                │
         │                   │ industry                    │
         │                   │ weightage                   │
         │                   │ effective_from              │
         │                   │ effective_to                │
         │                   │ created_at                  │
         │                   └─────────────────────────────┘
         │
         │              ┌──────────────────┐
         │              │  market_holidays │
         │              ├──────────────────┤
         │              │ id (PK)          │
         │              │ holiday_date (UQ)│
         │              │ holiday_name     │
         │              │ exchange         │
         │              │ created_at       │
         │              └──────────────────┘
         │
         ├───────────────────────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐           ┌──────────────────┐
│  ohlcv_daily    │           │ market_cap_hist  │
├─────────────────┤           ├──────────────────┤
│ id (PK)         │           │ id (PK)          │
│ symbol (FK)     │           │ symbol (FK)      │
│ date            │           │ date             │
│ open            │           │ series           │
│ high            │           │ security_name    │
│ low             │           │ category         │
│ close           │           │ last_trade_date  │
│ volume          │           │ face_value       │
│ vwap            │           │ issue_size       │
│ prev_close      │           │ close_price      │
│ change_pct      │           │ market_cap       │
│ upper_circuit   │           │ created_at       │
│ lower_circuit   │           └──────────────────┘
│ week_52_high    │
│ week_52_low     │
│ created_at      │
└─────────────────┘
         │
         │
         ├───────────────────────────────┬────────────────────────────────┐
         │                               │                                │
         ▼                               ▼                                ▼
┌─────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│  bulk_deals     │           │  block_deals     │           │ surveillance_meas│
├─────────────────┤           ├──────────────────┤           ├──────────────────┤
│ id (PK)         │           │ id (PK)          │           │ id (PK)          │
│ date            │           │ date             │           │ date             │
│ symbol (FK)     │           │ symbol (FK)      │           │ symbol (FK)      │
│ security_name   │           │ security_name    │           │ security_name    │
│ client_name     │           │ client_name      │           │ surveillance_act │
│ deal_type       │           │ deal_type        │           │ reason           │
│ quantity        │           │ quantity         │           │ is_active        │
│ trade_price     │           │ trade_price      │           │ created_at       │
│ remarks         │           │ remarks          │           │ updated_at       │
│ created_at      │           │ created_at       │           └──────────────────┘
└─────────────────┘           └──────────────────┘

                ┌──────────────────┐
                │calculated_metrics│ (Phase 2)
                ├──────────────────┤
                │ id (PK)          │
                │ symbol (FK)      │
                │ date             │
                │ change_1d/1w/... │
                │ rs_1d/1w/...     │
                │ vars_1d/1w/...   │
                │ varw_1m          │
                │ ema_10           │
                │ sma_20/50/100/200│
                │ atr_14           │
                │ atr_pct          │
                │ atr_from_sma50   │
                │ adr_pct          │
                │ atr_extension    │
                │ darvas_high/low  │
                │ rvol             │
                │ orh, m30_reorh   │
                │ lod_atr_pct      │
                │ vcp_score        │
                │ stage            │
                │ candle_type      │
                │ created_at       │
                └──────────────────┘
```

---

## 4. API Design

### 4.1 API Architectural Principles

1. **RESTful Design:** Resource-based URLs, HTTP methods (GET, POST, PUT, DELETE)
2. **Versioning:** `/api/v1/` prefix for future-proofing
3. **Pagination:** Limit/offset for large result sets (default: 100 records)
4. **Error Handling:** Standard HTTP status codes + JSON error details
5. **Documentation:** Auto-generated via FastAPI (OpenAPI/Swagger at `/docs`)

### 4.2 Endpoint Structure (Phase 1)

#### 4.2.1 Health & Monitoring

```
GET /health
Response: {
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-16T20:30:00Z"
}
```

```
GET /status/ingestion
Response: {
  "last_successful_fetch": "2025-01-16T20:35:00Z",
  "sources": [
    {
      "name": "nse_securities",
      "last_update": "2025-01-16T20:30:15Z",
      "status": "success",
      "records_fetched": 2145
    },
    {
      "name": "upstox_ohlcv",
      "last_update": "2025-01-16T20:45:22Z",
      "status": "success",
      "records_fetched": 2145
    },
    ...
  ]
}
```

```
GET /status/data-quality
Response: {
  "total_securities": 2145,
  "ohlcv_coverage": {
    "last_date": "2025-01-16",
    "coverage_pct": 98.5,
    "missing_symbols": ["XYZ", "ABC"]
  },
  "market_cap_coverage": 95.2,
  "industry_classification_coverage": 96.8
}
```

#### 4.2.2 Data Ingestion (POST)

**Base URL:** `/api/v1/ingest`

```
POST /api/v1/ingest/securities
Body: {
  "force_refresh": false  // Optional: re-fetch even if today's data exists
}
Response: {
  "status": "success",
  "records_added": 15,
  "records_updated": 2130,
  "records_total": 2145,
  "execution_time_ms": 1245
}
```

```
POST /api/v1/ingest/etfs
(Same structure as securities)
```

```
POST /api/v1/ingest/market-cap
Body: {
  "date": "2025-01-16"  // Optional: defaults to yesterday
}
Response: {
  "status": "success",
  "date": "2025-01-16",
  "records_added": 2100,
  "skipped_symbols": 45,  // Not in securities table
  "file_source": "https://nsearchives.nseindia.com/.../PR160125.zip"
}
```

```
POST /api/v1/ingest/historical-ohlcv/{symbol}
Path Params: symbol (e.g., "RELIANCE")
Body: {
  "from_date": "2020-01-16",  // Optional: defaults to 5 years ago
  "to_date": "2025-01-16",    // Optional: defaults to yesterday
  "interval": "1day"          // Optional: defaults to 1day
}
Response: {
  "status": "success",
  "symbol": "RELIANCE",
  "records_added": 1250,
  "date_range": {
    "from": "2020-01-16",
    "to": "2025-01-16"
  },
  "gaps_detected": []  // List of missing dates (excluding holidays)
}
```

```
POST /api/v1/ingest/daily-ohlcv
Body: {
  "symbols": ["RELIANCE", "TCS", ...]  // Optional: defaults to all securities
}
Response: {
  "status": "success",
  "total_symbols": 2145,
  "successful": 2140,
  "failed": 5,
  "errors": [
    {"symbol": "XYZ", "error": "Symbol not found in Upstox"}
  ]
}
```

```
POST /api/v1/ingest/bulk-deals
POST /api/v1/ingest/block-deals
(Similar structure: fetch CSV, parse, store)
```

```
POST /api/v1/ingest/surveillance
(Same pattern)
```

```
POST /api/v1/ingest/industry-classification
Body: {
  "symbols": [...]  // Optional: defaults to all securities
}
Response: {
  "status": "success",
  "updated": 2100,
  "failed": 45,
  "cookie_refreshes": 2  // How many times browser session was refreshed
}
```

#### 4.2.3 Data Retrieval (GET)

**Base URL:** `/api/v1`

```
GET /api/v1/securities?limit=100&offset=0&security_type=EQUITY&is_active=true
Query Params:
  - limit: int (default 100, max 1000)
  - offset: int (default 0)
  - security_type: EQUITY | ETF
  - is_active: boolean
  - search: string (fuzzy search on symbol/name)

Response: {
  "total": 2145,
  "limit": 100,
  "offset": 0,
  "data": [
    {
      "symbol": "RELIANCE",
      "isin": "INE002A01018",
      "security_name": "Reliance Industries Limited",
      "series": "EQ",
      "listing_date": "1977-11-29",
      "security_type": "EQUITY",
      "is_active": true,
      "industry": {
        "sector": "Energy",
        "industry": "Refineries & Marketing"
      }
    },
    ...
  ]
}
```

```
GET /api/v1/securities/{symbol}
Response: {
  "symbol": "RELIANCE",
  "isin": "INE002A01018",
  "security_name": "Reliance Industries Limited",
  "series": "EQ",
  "listing_date": "1977-11-29",
  "paid_up_value": 1000000000,
  "market_lot": 1,
  "face_value": 10.00,
  "security_type": "EQUITY",
  "is_active": true,
  "industry": {
    "macro": "Energy",
    "sector": "Energy",
    "industry": "Refineries & Marketing",
    "basic_industry": "Refineries"
  },
  "latest_ohlcv": {
    "date": "2025-01-16",
    "close": 2850.50,
    "change_pct": 1.25
  },
  "latest_market_cap": 1925000.00  // ₹ crore
}
```

```
GET /api/v1/securities/{symbol}/ohlcv?from=2024-01-01&to=2025-01-16&limit=1000
Query Params:
  - from: date (YYYY-MM-DD)
  - to: date (YYYY-MM-DD)
  - limit: int (default 365, max 5000)

Response: {
  "symbol": "RELIANCE",
  "date_range": {
    "from": "2024-01-01",
    "to": "2025-01-16"
  },
  "total_records": 250,
  "data": [
    {
      "date": "2025-01-16",
      "open": 2820.00,
      "high": 2860.50,
      "low": 2815.00,
      "close": 2850.50,
      "volume": 12500000,
      "vwap": 2838.25,
      "prev_close": 2815.00,
      "change_pct": 1.26
    },
    ...
  ]
}
```

```
GET /api/v1/securities/{symbol}/market-cap?from=2024-01-01&to=2025-01-16
(Similar structure to OHLCV)
```

```
GET /api/v1/indices?is_active=true
Response: {
  "total": 85,
  "data": [
    {
      "index_name": "Nifty 50",
      "symbol": "NIFTY_50",
      "exchange": "NSE_INDEX",
      "is_active": true,
      "constituents_count": 50
    },
    ...
  ]
}
```

```
GET /api/v1/indices/{index_name}/constituents?effective_date=2025-01-16
Query Params:
  - effective_date: date (default: today)

Response: {
  "index_name": "Nifty 50",
  "effective_date": "2025-01-16",
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

```
GET /api/v1/bulk-deals?symbol=RELIANCE&from=2024-01-01&to=2025-01-16
GET /api/v1/block-deals?symbol=RELIANCE&from=2024-01-01&to=2025-01-16
(Standard query structure)
```

```
GET /api/v1/surveillance?is_active=true
Response: {
  "total": 45,
  "data": [
    {
      "symbol": "XYZ",
      "security_name": "XYZ Limited",
      "surveillance_action": "ASM",
      "reason": "Price volatility",
      "date": "2025-01-10",
      "is_active": true
    },
    ...
  ]
}
```

### 4.3 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": {
      "field": "from_date",
      "expected": "YYYY-MM-DD",
      "received": "01-01-2025"
    },
    "timestamp": "2025-01-16T20:30:00Z"
  }
}
```

**Standard Error Codes:**
- `VALIDATION_ERROR` (400)
- `NOT_FOUND` (404)
- `RATE_LIMIT_EXCEEDED` (429)
- `INTERNAL_SERVER_ERROR` (500)
- `SERVICE_UNAVAILABLE` (503) - External API down

---

## 5. n8n Workflow Architecture

### 5.1 Workflow Design Principles

1. **Modularity:** Each data source = separate workflow or independent sub-flow
2. **Reusability:** Common nodes (error handling, notifications) as templates
3. **Observability:** Structured logging at each step via `ingestion_logs` table
4. **Fault Tolerance:** Retry logic with exponential backoff, graceful degradation
5. **Idempotency:** Safe to re-run workflows (upsert logic in API)
6. **Independence:** Parallel branches execute independently; one failure doesn't block others
7. **Database-Driven Aggregation:** Workflows query `ingestion_logs` table for status (not n8n state)

### 5.2 Workflow Templates

#### 5.2.1 Daily EOD Master Workflow (CORRECTED - Independent Execution)

**IMPORTANT:** Each parallel branch executes independently and logs to `ingestion_logs` table. One failure doesn't block others. Aggregation queries the database instead of n8n workflow state.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Daily EOD Master Workflow                         │
│  Trigger: Cron (Mon-Fri 8:30 PM IST, check holidays)               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Check if Trading Day  │
                    │  GET /status/is-trading│
                    └────────┬───────────────┘
                             │ If holiday → [Stop]
                             │ If trading day
                             ▼
                ┌────────────────────────────────────┐
                │ INDEPENDENT Parallel Branches      │
                │ (Each completes independently)     │
                │ No data passed between branches    │
                └──────────┬─────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬──────────────┐
        │                  │                  │              │
        ▼                  ▼                  ▼              ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐   ┌──────────┐
  │ Branch 1 │      │ Branch 2 │      │ Branch 3 │   │ Branch 4 │
  │ NSE Sec. │      │Market Cap│      │Bulk Deals│   │Surveill. │
  └────┬─────┘      └────┬─────┘      └────┬─────┘   └────┬─────┘
       │                 │                  │              │
       │  POST /ingest/* │                  │              │
       │  → DB logs      │                  │              │
       │                 │                  │              │
       ▼                 ▼                  ▼              ▼
   [Complete]       [Complete]          [Complete]    [Complete]
    success/fail     success/fail        success/fail  success/fail
       │                 │                  │              │
       └─────────────────┴──────────────────┴──────────────┘
                           │
         All branches log to ingestion_logs table
                           │
                           ▼
              ┌────────────────────────────┐
              │  Query Ingestion Status    │
              │  GET /status/ingestion     │
              │  (Reads ingestion_logs DB) │
              └────────┬───────────────────┘
                       │
                       │ Check: Did nse_securities succeed?
                       │
              ┌────────┴────────┐
              ▼ YES             ▼ NO (Critical)
    ┌──────────────────┐   ┌──────────────────┐
    │ Fetch OHLCV      │   │ Skip OHLCV       │
    │ POST /ingest/    │   │ Log: Missing deps│
    │ daily-ohlcv      │   │ Send alert       │
    └────────┬─────────┘   └────────┬─────────┘
             │                      │
             └──────────┬───────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │ Final Aggregation        │
            │ (Query ingestion_logs)   │
            │                          │
            │ Today's Status:          │
            │ ✓ Securities: success    │
            │ ✗ Market Cap: failure    │
            │ ✓ Bulk Deals: success    │
            │ ✓ Surveillance: success  │
            │ ✓ OHLCV: success         │
            └────────┬─────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  ┌──────────────┐         ┌──────────────┐
  │ All Success  │         │ Partial Fail │
  │ Notification │         │ Alert Email  │
  │              │         │              │
  │ "EOD ✓"      │         │ "Failed:     │
  │              │         │  Market Cap" │
  └──────────────┘         └──────────────┘
```

**Critical Node Details:**

1. **Cron Trigger:** `30 20 * * 1-5 Asia/Kolkata` (8:30 PM IST, Mon-Fri)

2. **Check Trading Day:**
   - HTTP Request: `GET /api/v1/status/is-trading-day?date=today`
   - If `is_trading_day === false` → Stop workflow

3. **Independent Parallel Branches (6 total):**

   Each branch is configured with:
   - **Continue On Fail**: TRUE (critical!)
   - **Timeout**: 120 seconds
   - **Error Trigger**: Catches errors, doesn't stop workflow

   **Branch 1: NSE Securities**
   - POST `/api/v1/ingest/securities`
   - On success: Endpoint logs to `ingestion_logs` with status='success'
   - On error: Endpoint logs to `ingestion_logs` with status='failure', errors JSON

   **Branch 2: NSE ETFs**
   - POST `/api/v1/ingest/etfs`
   - Same logging pattern

   **Branch 3: Market Cap**
   - POST `/api/v1/ingest/market-cap`
   - Same logging pattern

   **Branch 4: Bulk Deals**
   - POST `/api/v1/ingest/bulk-deals`

   **Branch 5: Block Deals**
   - POST `/api/v1/ingest/block-deals`

   **Branch 6: Surveillance**
   - POST `/api/v1/ingest/surveillance`

4. **Database Aggregation (NOT n8n state):**
   - HTTP Request: `GET /api/v1/status/ingestion`
   - Returns latest status for each source from `ingestion_logs` table
   - Response example:
     ```json
     {
       "sources": {
         "nse_securities": {"status": "success", "timestamp": "2025-01-16T20:31:00Z"},
         "nse_market_cap": {"status": "failure", "timestamp": "2025-01-16T20:31:15Z"},
         ...
       }
     }
     ```

5. **Critical Dependency Check:**
   - If node: `{{$json.sources.nse_securities.status}} === 'success'`
   - Rationale: OHLCV fetch requires symbols from securities table
   - If failed: Skip OHLCV, alert user, log reason to DB

6. **OHLCV Fetch (Conditional):**
   - HTTP Request: POST `/api/v1/ingest/daily-ohlcv`
   - Timeout: 300 seconds (longer for 2000+ symbols)
   - Logs to `ingestion_logs` as source='upstox_daily'

7. **Final Aggregation:**
   - Code node: Format summary from latest `ingestion_logs` entries
   - Include: source name, status, record counts, errors

8. **Smart Notifications:**
   - If all success → Slack notification (non-urgent)
   - If any failure → Email alert with failed sources list
   - If critical failure (securities/OHLCV) → SMS/high-priority alert

**Manual Retry Capability:**
- Each ingestion endpoint can be called independently
- Failed sources can be re-run without triggering entire workflow
- Example: `curl -X POST http://localhost:8000/api/v1/ingest/market-cap`

---

#### 5.2.2 Weekly Industry Classification Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│             Weekly Industry Classification Workflow                 │
│  Trigger: Cron (Sundays 10:00 PM IST)                              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Launch Playwright     │
                    │  Browser (Headless)    │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Navigate to NSE       │
                    │  Homepage              │
                    │  (Get Session Cookies) │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Get All Symbols       │
                    │  (Query securities tbl)│
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Loop Through Symbols  │
                    │  (SplitInBatches: 100) │
                    └────────┬───────────────┘
                             │
                        ┌────┴────┐
                        │ For Each│
                        │ Symbol  │
                        └────┬────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  GET NSE API           │
                    │  /quote-equity?symbol=X│
                    │  (With Cookies)        │
                    └────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    ▼ If 200         ▼ If 403 (Expired Cookie)
            ┌───────────────┐   ┌─────────────────┐
            │ Extract       │   │ Refresh Browser │
            │ industryInfo  │   │ Session         │
            └───────┬───────┘   │ Retry (Max 3x)  │
                    │           └────────┬────────┘
                    │                    │
                    │◄───────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ POST /ingest/ │
            │ industry-     │
            │ classification│
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Sleep 1 sec   │
            │ (Rate Limit)  │
            └───────┬───────┘
                    │
                    ▼
            [Next Symbol]
                    │
                    ▼ (After all symbols)
            ┌───────────────┐
            │ Close Browser │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Send Summary  │
            │ (Updated: X,  │
            │  Failed: Y)   │
            └───────────────┘
```

**Key Nodes:**
1. **Playwright Browser Launch:**
   - Code node with Playwright library
   - Headless: true (for server environments)
2. **Cookie Acquisition:**
   - Navigate to `https://www.nseindia.com`
   - Wait for cookies to be set (detect `_abck` cookie)
3. **Symbol Loop:**
   - HTTP Request in loop with dynamic URL
   - Header: `Cookie: {{$json.cookies}}`
4. **Error Handling:**
   - If 403: Trigger sub-workflow to refresh cookies
   - Max 3 cookie refresh attempts
   - If still fails: Log symbol to failures, continue
5. **Rate Limiting:**
   - Wait node: 1000ms between requests

---

#### 5.2.3 Historical Data Backfill Workflow (Manual Trigger)

```
┌─────────────────────────────────────────────────────────────────────┐
│             Historical OHLCV Backfill Workflow                       │
│  Trigger: Manual (n8n UI or Webhook)                               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Get All Symbols       │
                    │  (Equities + ETFs +    │
                    │   Indices)             │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  SplitInBatches        │
                    │  (Batch size: 50)      │
                    └────────┬───────────────┘
                             │
                        ┌────┴────┐
                        │For Each │
                        │ Batch   │
                        └────┬────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  For Each Symbol       │
                    │  in Batch              │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Calculate from_date   │
                    │  (5 years ago or       │
                    │   listing_date)        │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  POST /ingest/         │
                    │  historical-ohlcv/     │
                    │  {symbol}              │
                    │  Body: {from_date}     │
                    └────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    ▼ Success        ▼ Failure
            ┌───────────────┐   ┌─────────────────┐
            │ Increment     │   │ Log Error       │
            │ Success Count │   │ Increment Fail  │
            └───────┬───────┘   └────────┬────────┘
                    │                    │
                    └────────┬───────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Wait for Batch        │
                    │  Completion            │
                    └────────┬───────────────┘
                             │
                             ▼
                    [Next Batch]
                             │
                             ▼ (After all batches)
                    ┌────────────────────────┐
                    │  Generate Report       │
                    │  - Total symbols: X    │
                    │  - Successful: Y       │
                    │  - Failed: Z           │
                    │  - Total records: N    │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Send Completion Email │
                    └────────────────────────┘
```

**Optimization:**
- Batch processing to respect Upstox API rate limits
- Progress tracking via workflow variables
- Pause/Resume capability (store last processed symbol in DB)

---

### 5.3 Common Workflow Patterns

#### 5.3.1 Error Handling Template

```
[Any HTTP Request Node]
        │
        ├───▶ (Success Path)
        │
        └───▶ (Error Trigger)
                    │
                    ▼
            ┌───────────────┐
            │ Log Error     │
            │ to Database   │
            │ POST /logs    │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ If Retryable  │
            │ (5xx errors)  │
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        ▼ Yes                   ▼ No
┌───────────────┐       ┌───────────────┐
│ Retry Node    │       │ Send Alert    │
│ (Max 3x,      │       │ (Slack/Email) │
│  Exp Backoff) │       └───────────────┘
└───────┬───────┘
        │
        └───▶ [Original Node]
```

#### 5.3.2 Notification Template

```
[Workflow End]
        │
        ▼
┌───────────────┐
│ Aggregate     │
│ Results       │
│ (Set vars)    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Format Message│
│ (Jinja2/JSON) │
│               │
│ Template:     │
│ "Daily EOD    │
│  Complete:    │
│  ✅ 2140/2145"│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ If Failures   │
│ > 0           │
└───────┬───────┘
        │
    ┌───┴───┐
    ▼       ▼
  Email   Slack
  (Alert) (Summary)
```

---

## 6. Data Flow Diagrams

### 6.1 Daily EOD Data Flow

```
8:30 PM IST - Trading Day
│
▼
[n8n Cron Trigger]
│
├─▶ NSE Archives ──┐
│   (CSV/ZIP)      │
│                  ▼
├─▶ Upstox API ───▶ [Fetch Raw Data]
│                  │
│                  ▼
│             [Transform]
│             (Pandas/Code)
│                  │
│                  ▼
│             [Validate]
│             (Pydantic)
│                  │
│                  ▼
│             [POST /ingest/*]
│                  │
│                  ▼
│             [FastAPI]
│                  │
│             ┌────┴────┐
│             ▼         ▼
│      [Validators] [Deduplicator]
│             │         │
│             └────┬────┘
│                  ▼
│             [SQLAlchemy ORM]
│                  │
│                  ▼
│             [PostgreSQL]
│             ┌────┴────┐
│             ▼         ▼
│      [securities] [ohlcv_daily]
│      [market_cap] [bulk_deals]
│             │         │
│             └────┬────┘
│                  ▼
│             [Commit Transaction]
│                  │
│                  ▼
│             [Return Success]
│                  │
│                  ▼
│             [n8n Receives Response]
│                  │
│                  ▼
│             [Send Notification]
│
▼
9:00 PM IST - EOD Complete
```

### 6.2 Query Flow (Screener Execution - Phase 2)

```
[User/Scheduler Requests Screener]
│
▼
[GET /api/v1/screeners/rrg-charts]
│
▼
[FastAPI Endpoint]
│
▼
[Screener Logic]
│
├─▶ Query: calculated_metrics
│   WHERE date = latest
│   AND stage = 2
│   AND vars_1m >= 97
│
├─▶ Query: ohlcv_daily
│   JOIN securities
│   WHERE surveillance.is_active = false
│   AND market_cap >= 100 crore
│
└─▶ Aggregate Results
    │
    ▼
[Compute RRG Metrics]
(RS-Ratio, RS-Momentum)
    │
    ▼
[Format JSON Response]
    │
    ▼
[Return to User/Scheduler]
    │
    ▼
[Cache in Redis] (Future)
```

---

## 7. Security Architecture

### 7.1 Secrets Management

**Environment Variables (.env file):**
```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=screener_db
DB_USER=screener_user
DB_PASSWORD=<strong_password>  # Generate via: openssl rand -base64 32

# Upstox API
UPSTOX_API_KEY=<your_api_key>
UPSTOX_API_SECRET=<your_api_secret>
UPSTOX_ACCESS_TOKEN=<your_access_token>

# n8n
N8N_ENCRYPTION_KEY=<random_key>  # For credential encryption

# Application
ENV=development  # development | production
LOG_LEVEL=INFO   # DEBUG | INFO | WARNING | ERROR

# Optional: Notifications
SLACK_WEBHOOK_URL=<your_webhook>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<app_password>
```

**Docker Secrets (Production):**
- Store `.env` outside container, mount as volume
- Use Docker secrets for sensitive values in production

### 7.2 Network Security

**Development (Local):**
- All services on `screener_network` (Docker bridge)
- No external exposure except:
  - n8n: `localhost:5678` (UI access)
  - FastAPI: `localhost:8000` (API access)
  - PostgreSQL: Internal only (no host port mapping)

**Production (Future):**
- Reverse proxy (Nginx) for HTTPS
- API authentication (JWT tokens)
- Rate limiting (per IP, per user)
- CORS restrictions

### 7.3 Database Security

- **No hardcoded credentials** (use environment variables)
- **Least privilege principle:** Create dedicated `screener_user` with limited permissions
- **SSL connections** in production
- **Regular backups:** Automated daily snapshots
- **Audit logging:** Track schema changes and sensitive queries

---

## 8. Deployment Strategy

### 8.1 Docker Compose Configuration

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: screener_postgres
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"  # Expose for local debugging (remove in prod)
    networks:
      - screener_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  fastapi:
    build:
      context: ./screener_project
      dockerfile: Dockerfile
    container_name: screener_api
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - UPSTOX_API_KEY=${UPSTOX_API_KEY}
      - UPSTOX_API_SECRET=${UPSTOX_API_SECRET}
      - UPSTOX_ACCESS_TOKEN=${UPSTOX_ACCESS_TOKEN}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./screener_project:/app
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - screener_network
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  n8n:
    image: n8nio/n8n:latest
    container_name: screener_n8n
    environment:
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - WEBHOOK_URL=http://n8n:5678/
      - N8N_TIMEZONE=Asia/Kolkata
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n_workflows:/home/node/.n8n/workflows
    ports:
      - "5678:5678"
    depends_on:
      - fastapi
    networks:
      - screener_network

volumes:
  pgdata:
  n8n_data:

networks:
  screener_network:
    driver: bridge
```

**File: `screener_project/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright (for NSE scraping)
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
```

### 8.2 Database Initialization Script

**File: `scripts/init.sql`**
```sql
-- Create database user with limited privileges
CREATE USER screener_user WITH PASSWORD 'change_me_in_env';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE screener_db TO screener_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO screener_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO screener_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Initial schema creation handled by SQLAlchemy
```

### 8.3 Deployment Steps

**Phase 1 - Local Development:**
1. Clone repository
2. Create `.env` file from `.env.example`
3. `docker-compose up -d`
4. Access n8n at `http://localhost:5678`
5. Import workflow templates from `./n8n_workflows`
6. Trigger historical backfill workflow manually
7. Enable daily EOD workflow cron

**Phase 2 - Cloud Deployment (Future):**
1. Provision VPS (DigitalOcean, AWS EC2, etc.)
2. Install Docker + Docker Compose
3. Clone repository
4. Configure `.env` with production secrets
5. Update `docker-compose.yml`:
   - Remove port 5432 exposure (PostgreSQL)
   - Add Nginx reverse proxy container
   - Enable HTTPS (Let's Encrypt)
6. `docker-compose up -d`
7. Configure firewall (UFW): Allow 80, 443; Block 5432, 5678
8. Set up automated backups (cron + S3/GCS)

---

## 9. Monitoring & Observability

### 9.1 Logging Strategy

**Application Logs (FastAPI):**
```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("screener")
logHandler = logging.FileHandler("/app/logs/screener.log")
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

**Log Fields:**
- `timestamp`: ISO 8601
- `level`: DEBUG/INFO/WARNING/ERROR
- `module`: Python module name
- `message`: Human-readable message
- `context`: Dict with request ID, user, etc.

**n8n Logs:**
- Built-in execution logs (UI: Executions tab)
- Export to file: Mount `/home/node/.n8n/logs` volume

### 9.2 Metrics to Track

**System Metrics:**
- Database connection pool size
- API response times (p50, p95, p99)
- n8n workflow execution times
- Disk usage (PostgreSQL volume)

**Business Metrics:**
- Daily data ingestion success rate
- Data completeness % (OHLCV coverage)
- Screener execution frequency
- API error rate by endpoint

**Future: Prometheus + Grafana Integration**

---

## 10. Migration Strategy: PostgreSQL → ClickHouse

### 10.1 Migration Triggers
- Time-series tables exceed 50M records
- Query response time > 2 seconds for aggregations
- PostgreSQL disk usage > 500 GB

### 10.2 Migration Plan

**Step 1: Hybrid Architecture**
- Keep PostgreSQL for master tables (securities, indices, industry_classification)
- Migrate only time-series tables to ClickHouse:
  - `ohlcv_daily` → `ohlcv_daily_ch`
  - `market_cap_history` → `market_cap_history_ch`
  - `calculated_metrics` → `calculated_metrics_ch`

**Step 2: Dual-Write Pattern**
- Write new data to both PostgreSQL and ClickHouse
- Phase out PostgreSQL reads gradually
- Validate data consistency

**Step 3: Historical Data Migration**
- Batch export from PostgreSQL (CSV/Parquet)
- Import to ClickHouse via `INSERT INTO ... SELECT`
- Verify row counts and spot-check values

**Step 4: Cutover**
- Update FastAPI queries to use ClickHouse client
- Keep PostgreSQL for 30 days as backup
- Decommission PostgreSQL time-series tables

**ClickHouse Schema Example:**
```sql
CREATE TABLE ohlcv_daily_ch (
    symbol String,
    date Date,
    open Decimal(15, 2),
    high Decimal(15, 2),
    low Decimal(15, 2),
    close Decimal(15, 2),
    volume UInt64,
    vwap Decimal(15, 2),
    prev_close Decimal(15, 2),
    change_pct Decimal(8, 4)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (symbol, date)
SETTINGS index_granularity = 8192;
```

---

## 11. PostgreSQL Monthly Partitioning Strategy (Future)

### 11.1 When to Implement Partitioning

**Triggers:**
- `ohlcv_daily` table exceeds 10M records (~4 years of data for 2000 securities)
- Query performance degrades (>2 seconds for 1-year date range queries)
- Vacuum/analyze operations take >30 minutes

**Decision Point:** Phase 1 starts with NO partitioning for simplicity. Monitor performance quarterly.

### 11.2 Monthly Partitioning Implementation

**Why Monthly (Not Yearly or Symbol-based)?**
- Most queries filter by date ranges (1M, 3M, 6M, 1Y)
- Monthly partitions align with trading periods
- Easier to manage than daily partitions (12 partitions/year vs. 250+)
- Vacuum/analyze can run partition-by-partition
- Old partitions can be archived/dropped easily

**Implementation Steps:**

#### Step 1: Create Partitioned Table (Zero Downtime)

```sql
-- 1. Create new partitioned table structure
CREATE TABLE ohlcv_daily_partitioned (
    id BIGSERIAL,
    symbol VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(15, 2) NOT NULL,
    high DECIMAL(15, 2) NOT NULL,
    low DECIMAL(15, 2) NOT NULL,
    close DECIMAL(15, 2) NOT NULL,
    volume BIGINT,
    vwap DECIMAL(15, 2),
    prev_close DECIMAL(15, 2),
    change_pct DECIMAL(8, 4),
    upper_circuit DECIMAL(15, 2),
    lower_circuit DECIMAL(15, 2),
    week_52_high DECIMAL(15, 2),
    week_52_low DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (symbol, date),
    CHECK (high >= low)
) PARTITION BY RANGE (date);

-- 2. Create initial partitions (example for 2025)
CREATE TABLE ohlcv_daily_2025_01 PARTITION OF ohlcv_daily_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE ohlcv_daily_2025_02 PARTITION OF ohlcv_daily_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- ... create partitions for all existing months

-- 3. Create indexes on each partition (automatically inherited)
CREATE INDEX idx_ohlcv_partitioned_symbol_date
    ON ohlcv_daily_partitioned (symbol, date DESC);
```

#### Step 2: Migrate Historical Data (Off-Hours)

```sql
-- Copy data in batches (by month for efficiency)
INSERT INTO ohlcv_daily_partitioned
SELECT * FROM ohlcv_daily
WHERE date >= '2025-01-01' AND date < '2025-02-01';

INSERT INTO ohlcv_daily_partitioned
SELECT * FROM ohlcv_daily
WHERE date >= '2025-02-01' AND date < '2025-03-01';

-- ... continue for all months

-- Verify row counts match
SELECT COUNT(*) FROM ohlcv_daily;  -- Original
SELECT COUNT(*) FROM ohlcv_daily_partitioned;  -- New
```

#### Step 3: Atomic Table Swap (Minimal Downtime)

```sql
-- During maintenance window (< 1 minute downtime):

BEGIN;

-- Rename old table
ALTER TABLE ohlcv_daily RENAME TO ohlcv_daily_old;

-- Rename new table to active name
ALTER TABLE ohlcv_daily_partitioned RENAME TO ohlcv_daily;

-- Update sequence (if needed)
ALTER SEQUENCE ohlcv_daily_partitioned_id_seq RENAME TO ohlcv_daily_id_seq;

COMMIT;

-- Application automatically uses new partitioned table
```

#### Step 4: Verify and Cleanup

```sql
-- Test queries on new partitioned table
EXPLAIN ANALYZE
SELECT * FROM ohlcv_daily
WHERE symbol = 'RELIANCE' AND date >= '2024-01-01';
-- Should show "Seq Scan on ohlcv_daily_2024_01" (partition pruning working)

-- Keep old table for 30 days as backup
-- After validation period:
DROP TABLE ohlcv_daily_old;
```

### 11.3 Automated Partition Creation

**Option A: Trigger-Based (Recommended)**

```sql
-- Function to auto-create next month's partition
CREATE OR REPLACE FUNCTION create_next_partition()
RETURNS void AS $$
DECLARE
    next_month DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Calculate next month
    next_month := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '2 months');

    -- Generate partition name (e.g., ohlcv_daily_2025_03)
    partition_name := 'ohlcv_daily_' || TO_CHAR(next_month, 'YYYY_MM');

    -- Check if partition already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        -- Create partition
        start_date := TO_CHAR(next_month, 'YYYY-MM-DD');
        end_date := TO_CHAR(next_month + INTERVAL '1 month', 'YYYY-MM-DD');

        EXECUTE format(
            'CREATE TABLE %I PARTITION OF ohlcv_daily
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Schedule via cron (1st of every month)
-- Or call from FastAPI startup event
```

**Option B: FastAPI Startup Check**

```python
# database/partition_manager.py
from datetime import datetime, timedelta
from sqlalchemy import text

def ensure_partitions_exist(db_session, months_ahead=2):
    """Create partitions for next N months if they don't exist"""
    today = datetime.now()

    for i in range(months_ahead + 1):
        target_month = today + timedelta(days=30 * i)
        partition_name = f"ohlcv_daily_{target_month.strftime('%Y_%m')}"

        # Check if partition exists
        check_query = text(f"""
            SELECT 1 FROM pg_class WHERE relname = :partition_name
        """)
        exists = db_session.execute(check_query, {"partition_name": partition_name}).first()

        if not exists:
            # Create partition
            start_date = target_month.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1)

            create_query = text(f"""
                CREATE TABLE {partition_name} PARTITION OF ohlcv_daily
                FOR VALUES FROM ('{start_date.strftime('%Y-%m-%d')}')
                TO ('{end_date.strftime('%Y-%m-%d')}')
            """)
            db_session.execute(create_query)
            db_session.commit()
            print(f"Created partition: {partition_name}")

# main.py
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    ensure_partitions_exist(db, months_ahead=2)
```

### 11.4 Partition Maintenance

**Monthly Tasks:**
- Auto-create next month's partition (via cron or FastAPI startup)
- Vacuum/analyze completed months: `VACUUM ANALYZE ohlcv_daily_2025_01;`

**Quarterly Tasks:**
- Review partition sizes: `SELECT pg_size_pretty(pg_total_relation_size('ohlcv_daily_2025_01'));`
- Archive old partitions (e.g., >5 years) to S3/GCS

**Archival Strategy (After 5 Years):**
```sql
-- Detach partition (data still exists but not queryable)
ALTER TABLE ohlcv_daily DETACH PARTITION ohlcv_daily_2020_01;

-- Export to CSV
COPY ohlcv_daily_2020_01 TO '/backups/ohlcv_2020_01.csv' CSV HEADER;

-- Drop partition
DROP TABLE ohlcv_daily_2020_01;
```

### 11.5 Performance Benefits

**Before Partitioning (Single 10M row table):**
- 1-year query: Full table scan of 10M rows
- VACUUM time: 30+ minutes
- Index bloat: Continuous maintenance needed

**After Partitioning (Monthly partitions):**
- 1-year query: Scans only 12 partitions (~250K rows each)
- VACUUM time: <5 minutes per partition, parallelizable
- Partition pruning: 90%+ reduction in scanned data
- Easier archival: Drop old partitions without affecting active data

**Benchmark Estimate:**
- Query speedup: 5-10x for date-range queries
- Maintenance window: Reduced from hours to minutes

### 11.6 Changing Partitioning Strategy Later

**Scenario:** Need to switch from monthly to weekly partitions (unlikely)

**Solution:** Same migration pattern (create new, copy data, swap tables)

**Risk:** Low (monthly partitions sufficient for 10+ years based on data volume estimates)

---

## 12. Appendix

### 11.1 Technology Decision Matrix

| Requirement | Option A | Option B | **Selected** | Rationale |
|------------|----------|----------|--------------|-----------|
| Database | PostgreSQL | ClickHouse | **PostgreSQL** | Simpler for initial development; migrate later if needed |
| Workflow Engine | APScheduler | n8n | **n8n** | Visual interface, easier to extend, better observability |
| Web Scraping | Requests + Manual Cookie | Playwright | **Playwright** | Auto cookie refresh, more robust |
| API Framework | Flask | FastAPI | **FastAPI** | Auto-generated docs, async support, type validation |
| Deployment | Docker | Kubernetes | **Docker Compose** | Sufficient for single-node deployment |

### 11.2 References

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- n8n Documentation: https://docs.n8n.io/
- Upstox API Docs: https://upstox.com/developer/api-documentation/
- Playwright: https://playwright.dev/python/

---

**Document Owner:** Development Team
**Last Updated:** November 16, 2025
**Next Review:** After Phase 1.2 Completion
