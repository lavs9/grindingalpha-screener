# Contributing Guide

This document outlines coding standards, development practices, and contribution guidelines for the Indian Stock Market Screener Platform.

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Coding Standards](#coding-standards)
3. [Database Development](#database-development)
4. [API Development](#api-development)
5. [Data Validation](#data-validation)
6. [Error Handling](#error-handling)
7. [Testing Requirements](#testing-requirements)
8. [Git Workflow](#git-workflow)
9. [Documentation](#documentation)

---

## Before You Start

### Required Reading
1. **[CLAUDE.md](CLAUDE.md)** - Project overview and architecture
2. **[.claude/file-formats.md](.claude/file-formats.md)** - Data source specifications
3. **[.claude/Architecture.md](.claude/Architecture.md)** - Database schema and system design
4. **[.claude/Implementation-Plan.md](.claude/Implementation-Plan.md)** - Current phase tasks

### Critical Rule: File Format Documentation
**ALWAYS check `.claude/file-formats.md` before writing any parser or data model.**

This is not optional. The file contains:
- Exact column names and data types
- Validation rules and constraints
- Sample file locations
- Known edge cases

**Bad example (don't do this):**
```python
# Guessing column names
df = pd.read_csv(file_path)
symbol = df['symbol']  # Wrong! Actual column is 'SYMBOL'
```

**Good example:**
```python
# 1. Check .claude/file-formats.md first
# 2. See column is 'SYMBOL' (uppercase)
# 3. Use exact name
df = pd.read_csv(file_path)
symbol = df['SYMBOL']
```

---

## Coding Standards

### Python Style Guide

**Follow PEP 8 with these project-specific rules:**

1. **Use type hints for all function signatures:**
```python
# Good
def parse_equity_list(file_path: str) -> dict[str, Any]:
    pass

# Bad
def parse_equity_list(file_path):
    pass
```

2. **Maximum line length: 100 characters** (not 79)

3. **Use descriptive variable names (no abbreviations unless obvious):**
```python
# Good
market_cap_crore = 15000.50
transaction_date = datetime.now()

# Bad
mc = 15000.50
tx_dt = datetime.now()
```

4. **Constants in UPPER_CASE:**
```python
MAX_RETRY_ATTEMPTS = 3
DEFAULT_BATCH_SIZE = 1000
NSE_BASE_URL = "https://nsearchives.nseindia.com"
```

5. **Use docstrings for all public functions:**
```python
def fetch_nse_securities(date: str) -> dict[str, Any]:
    """
    Fetch NSE securities list for a given date.

    Args:
        date: Date in DD-MMM-YYYY format (e.g., "15-JAN-2024")

    Returns:
        Dictionary with 'success', 'data', and 'message' keys

    Raises:
        ValueError: If date format is invalid
        requests.HTTPError: If NSE API returns error
    """
    pass
```

### Code Organization

**Module structure (after Phase 0 reorganization):**
```
backend/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── main.py                # FastAPI application entry point
├── alembic/               # Database migrations
│   ├── env.py
│   └── versions/
└── app/
    ├── api/
    │   ├── v1/            # API v1 routes
    │   │   ├── ingestion.py    # POST /api/v1/ingest/*
    │   │   ├── query.py        # GET /api/v1/securities, /ohlcv
    │   │   ├── screeners.py    # GET /api/v1/screeners/* (Phase 2)
    │   │   └── health.py       # GET /health, /status
    │   └── deps.py             # Dependency injection
    ├── core/
    │   ├── config.py           # Settings from .env
    │   └── security.py         # Auth utilities (future)
    ├── database/
    │   ├── session.py          # DB session management
    │   └── base.py             # Base model class
    ├── models/                  # SQLAlchemy models (11 tables)
    │   ├── security.py          # Securities, Indices
    │   ├── timeseries.py        # OHLCV, MarketCap, Calculated
    │   ├── events.py            # BulkDeals, BlockDeals, Surveillance
    │   └── metadata.py          # Industry, Holidays, IndexConstituents, IngestionLogs
    ├── schemas/                 # Pydantic models
    │   ├── ingestion.py
    │   ├── security.py
    │   └── ohlcv.py
    ├── services/                # Business logic
    │   ├── nse/
    │   │   ├── securities_fetcher.py
    │   │   ├── marketcap_fetcher.py
    │   │   ├── deals_fetcher.py
    │   │   └── industry_scraper.py
    │   ├── upstox/
    │   │   ├── client.py
    │   │   ├── historical.py
    │   │   └── daily_quotes.py
    │   └── calculators/         # Phase 2
    │       ├── relative_strength.py
    │       └── technical.py
    └── utils/
        ├── validators.py
        ├── date_utils.py
        ├── logger.py
        └── retry.py
```

**Separation of concerns:**
- **API layer:** Only handles HTTP request/response, calls service layer
- **Service layer:** Contains business logic, can be used outside API
- **Database layer:** Only handles data persistence

```python
# Good: API calls service, service calls database
@app.post("/ingest/securities")
async def ingest_securities(request: IngestRequest):
    result = nse_service.fetch_and_store_securities(request.date)
    return result

# Bad: API directly interacts with database
@app.post("/ingest/securities")
async def ingest_securities(request: IngestRequest):
    with get_db() as db:
        # Don't do business logic in API handlers
        securities = fetch_from_nse()
        db.add_all(securities)
```

---

## Database Development

### Schema Adherence

**All database models MUST match the schema in `.claude/Architecture.md` Section 3.**

When creating SQLAlchemy models:
1. Check Architecture.md for table definition
2. Use exact column names, types, and constraints
3. Include all indexes specified
4. Add composite unique constraints

**Example:**
```python
from sqlalchemy import Column, Integer, String, Date, DECIMAL, Boolean, Index
from sqlalchemy import UniqueConstraint, CheckConstraint
from database.db_helper import Base

class Security(Base):
    __tablename__ = 'securities'

    # Columns (match Architecture.md exactly)
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False)
    isin = Column(String(12), unique=True, nullable=False)
    security_name = Column(String(255), nullable=False)
    series = Column(String(10))
    listing_date = Column(Date)
    paid_up_value = Column(DECIMAL(15, 2))
    market_lot = Column(Integer)
    face_value = Column(DECIMAL(10, 2))
    security_type = Column(String(10), nullable=False)  # 'EQUITY' or 'ETF'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes (from Architecture.md Section 3.1.1)
    __table_args__ = (
        Index('idx_securities_symbol', 'symbol'),
        Index('idx_securities_isin', 'isin'),
        Index('idx_securities_type', 'security_type'),
    )
```

### Query Optimization

**Always use indexes for filtering:**
```python
# Good: Uses idx_ohlcv_symbol_date index
db.query(OHLCVDaily)\
  .filter(OHLCVDaily.symbol == 'RELIANCE')\
  .filter(OHLCVDaily.date >= '2024-01-01')\
  .order_by(OHLCVDaily.date.desc())\
  .all()

# Bad: No index on security_name (slow query)
db.query(Security).filter(Security.security_name.like('%Reliance%')).all()
```

**Use bulk inserts for large datasets:**
```python
# Good: Batch insert (1000x faster)
db.bulk_insert_mappings(OHLCVDaily, ohlcv_records)
db.commit()

# Bad: Individual inserts
for record in ohlcv_records:
    db.add(OHLCVDaily(**record))
    db.commit()  # Don't commit in loop!
```

### Migration Strategy

**No partitioning in Phase 1** (see Architecture.md Section 11):
- Start with simple tables
- Monthly partitioning only after >10M records or >2s queries
- Document when to implement in code comments

```python
# models.py
class OHLCVDaily(Base):
    """
    Daily OHLCV data for all securities.

    NOTE: This table is NOT partitioned in Phase 1.
    See .claude/Architecture.md Section 11 for monthly partitioning
    migration procedure (implement when >10M records).
    """
    __tablename__ = 'ohlcv_daily'
    # ... rest of model
```

---

## API Development

### Endpoint Design

**Follow RESTful conventions:**
- `POST /api/v1/ingest/{source}` - Data ingestion
- `GET /api/v1/securities` - List securities
- `GET /api/v1/securities/{symbol}` - Single security
- `GET /api/v1/ohlcv/{symbol}` - OHLCV data (query params: start_date, end_date)

**Always use Pydantic models for request/response:**
```python
from pydantic import BaseModel, Field, field_validator
from datetime import date

class IngestSecuritiesRequest(BaseModel):
    date: str = Field(..., description="Date in DD-MMM-YYYY format")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, '%d-%b-%Y')
            return v
        except ValueError:
            raise ValueError("Date must be in DD-MMM-YYYY format (e.g., '15-JAN-2024')")

class IngestResponse(BaseModel):
    success: bool
    records_inserted: int
    records_failed: int
    message: str
    errors: list[str] | None = None
```

### Logging in Endpoints

**Log all ingestion operations to `ingestion_logs` table:**
```python
from datetime import datetime
from database.models import IngestionLog

async def log_ingestion(
    source: str,
    status: str,  # 'success', 'failure', 'partial'
    records_fetched: int,
    records_inserted: int,
    records_failed: int,
    errors: dict | None = None,
    execution_time_ms: int = 0
):
    with get_db_context() as db:
        log = IngestionLog(
            source=source,
            status=status,
            records_fetched=records_fetched,
            records_inserted=records_inserted,
            records_failed=records_failed,
            errors=errors,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now()
        )
        db.add(log)
        db.commit()
```

**Source values** (use exact strings from Architecture.md Section 3.1.4):
- `nse_securities`
- `nse_etfs`
- `nse_market_cap`
- `nse_bulk_deals`
- `nse_block_deals`
- `nse_surveillance`
- `nse_industry`
- `upstox_historical`
- `upstox_daily`
- `upstox_holidays`
- `manual_index_constituents`

---

## Data Validation

### Input Validation Rules

**Check `.claude/file-formats.md` for validation rules before parsing.**

**Example: NSE Equity List validation**
```python
import re
from datetime import datetime

def validate_equity_record(record: dict) -> tuple[bool, str]:
    """
    Validate NSE equity record.
    See .claude/file-formats.md Section 1.1 for rules.
    """
    # Symbol: Alphanumeric, &, - allowed
    if not re.match(r'^[A-Z0-9&-]+$', record['SYMBOL']):
        return False, f"Invalid symbol format: {record['SYMBOL']}"

    # ISIN: Must start with IN, exactly 12 chars
    if not re.match(r'^IN[A-Z0-9]{10}$', record['ISIN NUMBER']):
        return False, f"Invalid ISIN: {record['ISIN NUMBER']}"

    # Face value: Must be positive
    if record.get('FACE VALUE'):
        face_value = float(record['FACE VALUE'])
        if face_value <= 0:
            return False, f"Face value must be positive: {face_value}"

    # Market lot: Must be > 0
    market_lot = int(record['MARKET LOT'])
    if market_lot <= 0:
        return False, f"Market lot must be positive: {market_lot}"

    return True, "Valid"
```

### Date Format Handling

**NSE uses `DD-MMM-YYYY`, Upstox uses `YYYY-MM-DD`:**
```python
# utils/date_utils.py
from datetime import datetime, date

def parse_nse_date(date_str: str) -> date:
    """Parse NSE date format: DD-MMM-YYYY (e.g., '29-NOV-1977')"""
    return datetime.strptime(date_str, '%d-%b-%Y').date()

def parse_upstox_date(date_str: str) -> date:
    """Parse Upstox date format: YYYY-MM-DD (e.g., '2024-01-15')"""
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def format_nse_date(d: date) -> str:
    """Format date for NSE API: DD-MMM-YYYY"""
    return d.strftime('%d-%b-%Y').upper()

def format_upstox_date(d: date) -> str:
    """Format date for Upstox API: YYYY-MM-DD"""
    return d.strftime('%Y-%m-%d')
```

### Price Data Validation

**Check constraints from Architecture.md Section 3.1.2:**
```python
def validate_ohlcv(record: dict) -> tuple[bool, str]:
    """
    Validate OHLCV data.
    Enforces constraints: high >= low, open/close within range.
    """
    o, h, l, c = record['open'], record['high'], record['low'], record['close']

    # High >= Low
    if h < l:
        return False, f"High ({h}) must be >= Low ({l})"

    # Open within range
    if not (l <= o <= h):
        return False, f"Open ({o}) must be between Low ({l}) and High ({h})"

    # Close within range
    if not (l <= c <= h):
        return False, f"Close ({c}) must be between Low ({l}) and High ({h})"

    return True, "Valid"
```

---

## Error Handling

### Standard Error Response Format

```python
from fastapi import HTTPException

# Service layer returns dict
def fetch_nse_data(date: str) -> dict:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json(),
            "message": f"Fetched {len(data)} records"
        }
    except requests.HTTPError as e:
        return {
            "success": False,
            "data": None,
            "message": f"NSE API error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Unexpected error: {str(e)}"
        }

# API layer raises HTTPException
@app.post("/ingest/securities")
async def ingest_securities(request: IngestRequest):
    result = nse_service.fetch_and_store_securities(request.date)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result
```

### Retry Logic for External APIs

**Use exponential backoff for NSE/Upstox APIs:**
```python
import time
from typing import Callable

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0
) -> Any:
    """
    Retry function with exponential backoff.
    Delay: 1s, 2s, 4s
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise

            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
```

---

## Testing Requirements

### Unit Tests

**Required for all service layer functions:**
```python
# tests/test_services/test_nse_fetcher.py
import pytest
from services.nse_fetcher import parse_equity_list

def test_parse_equity_list_valid_sample():
    """Test parser with sample file from .claude/samples/"""
    sample_path = ".claude/samples/EQUITY_L_sample.csv"
    result = parse_equity_list(sample_path)

    assert result["success"] is True
    assert len(result["data"]) > 0

    # Validate first record structure
    first_record = result["data"][0]
    assert "symbol" in first_record
    assert "isin" in first_record
    assert re.match(r'^IN[A-Z0-9]{10}$', first_record["isin"])

def test_parse_equity_list_invalid_isin():
    """Test parser rejects invalid ISIN"""
    # Create test CSV with invalid ISIN
    invalid_csv = "SYMBOL,ISIN NUMBER\nRELIANCE,INVALID123"

    with pytest.raises(ValueError, match="Invalid ISIN"):
        parse_equity_list(StringIO(invalid_csv))
```

### Integration Tests

**Test database operations:**
```python
# tests/test_database/test_models.py
import pytest
from database.models import Security
from database.db_helper import get_db_context

@pytest.fixture
def test_db():
    # Setup test database
    # (Use separate test database, not production)
    pass

def test_security_unique_constraint(test_db):
    """Test that duplicate symbols are rejected"""
    with get_db_context() as db:
        sec1 = Security(symbol="RELIANCE", isin="INE002A01018", ...)
        db.add(sec1)
        db.commit()

        # Duplicate symbol should fail
        sec2 = Security(symbol="RELIANCE", isin="INE002A01019", ...)
        db.add(sec2)

        with pytest.raises(IntegrityError):
            db.commit()
```

### API Tests

**Use FastAPI TestClient:**
```python
from fastapi.testclient import TestClient
from screener_project.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ingest_securities_invalid_date():
    response = client.post("/api/v1/ingest/securities", json={
        "date": "2024-01-15"  # Wrong format (should be DD-MMM-YYYY)
    })
    assert response.status_code == 422  # Validation error
```

---

## Git Workflow

### Branch Naming

**Format:** `<username>/<feature-description>`

Examples:
- `mayank/phase0-docker-setup`
- `mayank/nse-securities-ingestion`
- `mayank/fix-ohlcv-validation`

### Commit Messages

**Format:**
```
<type>: <short description>

<detailed description if needed>

```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructuring (no behavior change)
- `docs:` Documentation only
- `test:` Adding tests
- `chore:` Build/config changes

**Examples:**
```
feat: Add NSE securities ingestion endpoint

Implements POST /api/v1/ingest/securities endpoint that:
- Fetches EQUITY_L.csv from NSE archives
- Validates ISIN and symbol formats per file-formats.md
- Logs results to ingestion_logs table

Follows Architecture.md Section 3.1.1 schema for securities table.


```

### Pull Request Guidelines

**PR Title:** Same format as commit message

**PR Description Template:**
```markdown
## Summary
Brief description of changes (1-2 sentences)

## Changes
- Added X endpoint
- Updated Y model
- Fixed Z validation

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manually tested with sample data from .claude/samples/

## Documentation Updated
- [ ] Updated CLAUDE.md if architecture changed
- [ ] Updated .claude/file-formats.md if new data source added
- [ ] Added docstrings to new functions

## Checklist
- [ ] Code follows CONTRIBUTING.md guidelines
- [ ] Checked .claude/file-formats.md for data specifications
- [ ] Database models match .claude/Architecture.md schema
- [ ] Added logging to ingestion_logs table (if applicable)
- [ ] No hardcoded credentials (use environment variables)
```

---

## Documentation

### When to Update Documentation

**Update `.claude/file-formats.md` when:**
- Adding new data source
- External API format changes
- Discovering new validation rules
- Adding sample files

**Update `.claude/Architecture.md` when:**
- Adding/modifying database tables
- Changing workflow design
- Updating technology stack

**Update `CLAUDE.md` when:**
- Adding new commands
- Changing project structure
- Updating development workflow

### Inline Code Documentation

**Document WHY, not WHAT:**
```python
# Good: Explains reasoning
# NSE date format is DD-MMM-YYYY (e.g., "15-JAN-2024")
# This differs from Upstox which uses YYYY-MM-DD
date_str = format_nse_date(trade_date)

# Bad: States the obvious
# Format the date
date_str = format_nse_date(trade_date)
```

**Reference documentation in comments:**
```python
# See .claude/Architecture.md Section 3.1.4 for ingestion_logs schema
log = IngestionLog(source='nse_securities', ...)

# Validation rules from .claude/file-formats.md Section 1.1
if not re.match(r'^IN[A-Z0-9]{10}$', isin):
    raise ValueError("Invalid ISIN format")
```

---

## Security Best Practices

### Environment Variables

**NEVER commit credentials:**
```python
# Good: Use environment variables
import os
DB_PASSWORD = os.getenv('DB_PASSWORD')
UPSTOX_API_KEY = os.getenv('UPSTOX_API_KEY')

# Bad: Hardcoded credentials
DB_PASSWORD = "Password@123"  # Don't do this!
```

**Add to `.gitignore`:**
```
.env
.env.local
*.pem
*.key
credentials.json
```

### SQL Injection Prevention

**Always use SQLAlchemy ORM or parameterized queries:**
```python
# Good: ORM (safe)
db.query(Security).filter(Security.symbol == user_input).first()

# Good: Parameterized query (safe)
db.execute(text("SELECT * FROM securities WHERE symbol = :symbol"), {"symbol": user_input})

# Bad: String interpolation (SQL injection risk)
db.execute(f"SELECT * FROM securities WHERE symbol = '{user_input}'")  # NEVER do this!
```

---

## Common Pitfalls

### 1. Not Checking File Formats
**Problem:** Guessing column names leads to runtime errors
**Solution:** Always check `.claude/file-formats.md` first

### 2. Ignoring Database Schema
**Problem:** Creating tables that don't match Architecture.md
**Solution:** Copy exact column definitions from Section 3

### 3. Committing in Loops
**Problem:** Slow inserts (1000x slower than bulk)
**Solution:** Use `bulk_insert_mappings()` for >100 records

### 4. No Error Logging
**Problem:** Can't debug failed ingestions
**Solution:** Always log to `ingestion_logs` table

### 5. Hardcoded Dates
**Problem:** Tests fail when date changes
**Solution:** Use dynamic dates or fixtures

---

## Getting Help

**Documentation:**
- Read [CLAUDE.md](CLAUDE.md) for project overview
- Check [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md) for current phase tasks
- Review [.claude/Architecture.md](.claude/Architecture.md) for design decisions

**Questions:**
- Open GitHub issue with `question` label
- Reference specific documentation section in question
- Include code snippet and error message if applicable

---

## Summary Checklist

Before submitting code, verify:

- [ ] ✅ Checked `.claude/file-formats.md` for data specifications
- [ ] ✅ Database models match `.claude/Architecture.md` schema
- [ ] ✅ Used type hints for all function signatures
- [ ] ✅ Added docstrings to public functions
- [ ] ✅ Implemented input validation with proper error messages
- [ ] ✅ Logged ingestion operations to `ingestion_logs` table
- [ ] ✅ Used environment variables (no hardcoded credentials)
- [ ] ✅ Added unit tests with >80% coverage
- [ ] ✅ Tested with sample files from `.claude/samples/`
- [ ] ✅ Followed RESTful API conventions
- [ ] ✅ Updated relevant documentation
- [ ] ✅ Meaningful commit message with type prefix
- [ ] ✅ No SQL injection vulnerabilities
- [ ] ✅ Used bulk inserts for large datasets
- [ ] ✅ Implemented retry logic for external APIs

---

**Last Updated:** 2025-11-22
