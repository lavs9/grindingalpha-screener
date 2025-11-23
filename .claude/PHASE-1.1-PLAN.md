# Phase 1.1: Core Database Models & Schema

**Status:** Ready to Start
**Duration:** 4-6 days
**Prerequisites:** Phase 0 Complete ✅

## Overview

Create all 11 database tables from the Architecture.md schema and set up the Alembic migration framework. This phase establishes the data foundation for the entire platform.

## Database Schema Reference

Complete schema is defined in [Architecture.md](Architecture.md) Section 3.

**Tables to Create:**
1. **Master Tables (4):** securities, indices, industry_classification, market_holidays
2. **Time-Series Tables (3):** ohlcv_daily, market_cap_history, calculated_metrics
3. **Event Tables (3):** bulk_deals, block_deals, surveillance_measures
4. **Metadata Table (1):** ingestion_logs

**Note:** `index_constituents` table will be added in Phase 1.4

## Tasks Checklist

### Task 1: Create Master Table Models

#### 1.1 Securities Model
**File:** `backend/app/models/security.py`

```python
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database.base import Base
import enum

class SecurityType(str, enum.Enum):
    """Security type enumeration."""
    EQUITY = "EQUITY"
    ETF = "ETF"

class Security(Base):
    """
    Master table for all NSE securities (equities and ETFs).
    Source: NSE EQUITY_L.csv and ETF_L.csv
    """
    __tablename__ = 'securities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    isin = Column(String(12), unique=True, nullable=False, index=True)
    security_name = Column(String(255), nullable=False)
    series = Column(String(10))  # EQ, BE, etc.
    listing_date = Column(Date)
    paid_up_value = Column(Numeric(15, 2))
    market_lot = Column(Integer)
    face_value = Column(Numeric(10, 2))
    security_type = Column(Enum(SecurityType), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Security(symbol='{self.symbol}', name='{self.security_name}')>"
```

#### 1.2 Indices Model
**File:** `backend/app/models/security.py` (same file)

```python
class Index(Base):
    """
    Master table for market indices.
    Examples: Nifty 50, Nifty Bank, Sensex
    """
    __tablename__ = 'indices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String(100), unique=True, nullable=False)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    exchange = Column(String(20), default='NSE_INDEX')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Index(symbol='{self.symbol}', name='{self.index_name}')>"
```

#### 1.3 Industry Classification Model
**File:** `backend/app/models/metadata.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base

class IndustryClassification(Base):
    """
    Industry classification for each security.
    Source: NSE website API (scraped via Playwright)
    """
    __tablename__ = 'industry_classification'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   unique=True, nullable=False, index=True)
    macro = Column(String(100))
    sector = Column(String(100), index=True)
    industry = Column(String(100), index=True)
    basic_industry = Column(String(100))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<IndustryClassification(symbol='{self.symbol}', sector='{self.sector}')>"
```

#### 1.4 Market Holidays Model
**File:** `backend/app/models/metadata.py` (same file)

```python
class MarketHoliday(Base):
    """
    Market trading holidays.
    Source: Upstox API
    """
    __tablename__ = 'market_holidays'

    id = Column(Integer, primary_key=True, autoincrement=True)
    holiday_date = Column(Date, unique=True, nullable=False, index=True)
    holiday_name = Column(String(255))
    exchange = Column(String(20), default='NSE')
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<MarketHoliday(date='{self.holiday_date}', name='{self.holiday_name}')>"
```

### Task 2: Create Time-Series Table Models

#### 2.1 OHLCV Daily Model
**File:** `backend/app/models/timeseries.py`

```python
from sqlalchemy import Column, BigInteger, String, Date, Numeric, DateTime, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.sql import func
from app.database.base import Base

class OHLCVDaily(Base):
    """
    Daily OHLCV (Open-High-Low-Close-Volume) data for all securities and indices.
    Source: Upstox API

    Note: No foreign key on symbol for flexibility (indices don't exist in securities table)
    """
    __tablename__ = 'ohlcv_daily'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(15, 2), nullable=False)
    high = Column(Numeric(15, 2), nullable=False)
    low = Column(Numeric(15, 2), nullable=False)
    close = Column(Numeric(15, 2), nullable=False)
    volume = Column(BigInteger)  # Null for indices
    vwap = Column(Numeric(15, 2))
    prev_close = Column(Numeric(15, 2))
    change_pct = Column(Numeric(8, 4))
    upper_circuit = Column(Numeric(15, 2))
    lower_circuit = Column(Numeric(15, 2))
    week_52_high = Column(Numeric(15, 2))
    week_52_low = Column(Numeric(15, 2))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_ohlcv_symbol_date'),
        CheckConstraint('high >= low', name='ck_high_gte_low'),
        CheckConstraint('open >= low AND open <= high', name='ck_open_in_range'),
        CheckConstraint('close >= low AND close <= high', name='ck_close_in_range'),
        Index('idx_ohlcv_symbol_date', 'symbol', 'date'.desc()),
        Index('idx_ohlcv_date', 'date'.desc()),
    )

    def __repr__(self):
        return f"<OHLCVDaily(symbol='{self.symbol}', date='{self.date}', close={self.close})>"
```

#### 2.2 Market Cap History Model
**File:** `backend/app/models/timeseries.py` (same file)

```python
class MarketCapHistory(Base):
    """
    Daily market capitalization for all securities.
    Source: NSE MCAP_*.csv files
    """
    __tablename__ = 'market_cap_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    series = Column(String(10))
    security_name = Column(String(255))
    category = Column(String(50))
    last_trade_date = Column(Date)
    face_value = Column(Numeric(10, 2))
    issue_size = Column(BigInteger)
    close_price = Column(Numeric(15, 2))
    market_cap = Column(Numeric(20, 2), nullable=False, index=True)  # In ₹ crore
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_marketcap_symbol_date'),
        Index('idx_marketcap_symbol_date', 'symbol', 'date'.desc()),
        Index('idx_marketcap_date_mcap', 'date', 'market_cap'.desc()),
    )

    def __repr__(self):
        return f"<MarketCapHistory(symbol='{self.symbol}', date='{self.date}', mcap={self.market_cap})>"
```

#### 2.3 Calculated Metrics Model
**File:** `backend/app/models/timeseries.py` (same file)

```python
class CalculatedMetrics(Base):
    """
    Daily calculated technical indicators and metrics.
    Populated daily after OHLCV ingestion (Phase 2).
    """
    __tablename__ = 'calculated_metrics'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Relative Strength metrics
    rs_rating = Column(Numeric(5, 2))  # 0-100
    vars_value = Column(Numeric(10, 4))  # Value-Adjusted Relative Strength

    # Volatility metrics
    atr = Column(Numeric(15, 2))
    atr_pct = Column(Numeric(8, 4))

    # Trend metrics
    stage = Column(Integer)  # 1, 2, 3, or 4 (Stan Weinstein)
    vcp_score = Column(Numeric(5, 2))  # Volatility Contraction Pattern score

    # Volume metrics
    vol_20d_avg = Column(BigInteger)
    vol_vs_avg_pct = Column(Numeric(8, 2))

    # Moving averages
    ma_10 = Column(Numeric(15, 2))
    ma_20 = Column(Numeric(15, 2))
    ma_50 = Column(Numeric(15, 2))
    ma_200 = Column(Numeric(15, 2))

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_metrics_symbol_date'),
        Index('idx_metrics_symbol_date', 'symbol', 'date'.desc()),
        Index('idx_metrics_rs_rating', 'rs_rating'.desc()),
        Index('idx_metrics_stage', 'stage'),
    )

    def __repr__(self):
        return f"<CalculatedMetrics(symbol='{self.symbol}', date='{self.date}', rs_rating={self.rs_rating})>"
```

### Task 3: Create Event Table Models

#### 3.1 Bulk Deals Model
**File:** `backend/app/models/events.py`

```python
from sqlalchemy import Column, BigInteger, String, Date, Numeric, DateTime
from sqlalchemy.sql import func
from app.database.base import Base

class BulkDeal(Base):
    """
    Bulk deals transactions (>0.5% of equity).
    Source: NSE bulk.csv
    """
    __tablename__ = 'bulk_deals'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    security_name = Column(String(255))
    client_name = Column(String(255), nullable=False)
    deal_type = Column(String(10))  # 'BUY' or 'SELL'
    quantity = Column(BigInteger, nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<BulkDeal(symbol='{self.symbol}', date='{self.date}', type='{self.deal_type}')>"
```

#### 3.2 Block Deals Model
**File:** `backend/app/models/events.py` (same file)

```python
class BlockDeal(Base):
    """
    Block deals transactions (large off-market trades).
    Source: NSE block.csv
    """
    __tablename__ = 'block_deals'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    security_name = Column(String(255))
    client_name = Column(String(255), nullable=False)
    deal_type = Column(String(10))  # 'BUY' or 'SELL'
    quantity = Column(BigInteger, nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<BlockDeal(symbol='{self.symbol}', date='{self.date}', type='{self.deal_type}')>"
```

#### 3.3 Surveillance Measures Model
**File:** `backend/app/models/events.py` (same file)

```python
class SurveillanceMeasure(Base):
    """
    Securities under surveillance/ASM framework.
    Source: NSE REG1_IND*.csv
    """
    __tablename__ = 'surveillance_measures'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    security_name = Column(String(255))
    measure_type = Column(String(100))  # e.g., 'ASM Stage 1', 'GSM'
    reason = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<SurveillanceMeasure(symbol='{self.symbol}', date='{self.date}', type='{self.measure_type}')>"
```

### Task 4: Create Ingestion Logs Model

**File:** `backend/app/models/metadata.py`

```python
class IngestionLog(Base):
    """
    Tracks data ingestion status for all sources.
    Used by n8n workflows for aggregation and monitoring.
    """
    __tablename__ = 'ingestion_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)  # 'nse_securities', 'upstox_ohlcv', etc.
    status = Column(String(20), nullable=False)  # 'success', 'failure', 'partial'
    records_fetched = Column(Integer)
    records_inserted = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)
    errors = Column(JSON)  # Store error details as JSON
    execution_time_ms = Column(Integer)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<IngestionLog(source='{self.source}', status='{self.status}', timestamp='{self.timestamp}')>"
```

### Task 5: Update Model __init__.py Files

**File:** `backend/app/models/__init__.py`

```python
"""
SQLAlchemy models for all database tables.
Import all models here to ensure they're registered with Base.metadata.
"""
from app.models.security import Security, Index, SecurityType
from app.models.timeseries import OHLCVDaily, MarketCapHistory, CalculatedMetrics
from app.models.events import BulkDeal, BlockDeal, SurveillanceMeasure
from app.models.metadata import IndustryClassification, MarketHoliday, IngestionLog

__all__ = [
    # Master tables
    'Security',
    'Index',
    'SecurityType',

    # Time-series tables
    'OHLCVDaily',
    'MarketCapHistory',
    'CalculatedMetrics',

    # Event tables
    'BulkDeal',
    'BlockDeal',
    'SurveillanceMeasure',

    # Metadata tables
    'IndustryClassification',
    'MarketHoliday',
    'IngestionLog',
]
```

### Task 6: Create Pydantic Schemas

#### 6.1 Security Schemas
**File:** `backend/app/schemas/security.py`

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class SecurityBase(BaseModel):
    """Base schema for Security."""
    symbol: str = Field(..., max_length=50)
    isin: str = Field(..., max_length=12)
    security_name: str = Field(..., max_length=255)
    series: Optional[str] = Field(None, max_length=10)
    listing_date: Optional[date] = None
    paid_up_value: Optional[Decimal] = None
    market_lot: Optional[int] = None
    face_value: Optional[Decimal] = None
    security_type: str  # 'EQUITY' or 'ETF'

class SecurityCreate(SecurityBase):
    """Schema for creating a new security."""
    is_active: bool = True

class SecurityResponse(SecurityBase):
    """Schema for security response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### 6.2 OHLCV Schemas
**File:** `backend/app/schemas/ohlcv.py`

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class OHLCVBase(BaseModel):
    """Base schema for OHLCV data."""
    symbol: str = Field(..., max_length=50)
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Optional[int] = None
    vwap: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    change_pct: Optional[Decimal] = None
    upper_circuit: Optional[Decimal] = None
    lower_circuit: Optional[Decimal] = None
    week_52_high: Optional[Decimal] = None
    week_52_low: Optional[Decimal] = None

class OHLCVCreate(OHLCVBase):
    """Schema for creating OHLCV record."""
    pass

class OHLCVResponse(OHLCVBase):
    """Schema for OHLCV response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

*(Create similar schemas for all other models)*

### Task 7: Generate Alembic Migration

```bash
# In backend/ directory
alembic revision --autogenerate -m "Create all database tables"
```

**Review the generated migration file in `backend/alembic/versions/`**

Key things to check:
- All 11 tables are created
- Indexes are properly defined
- Constraints (unique, check, foreign key) are correct
- Enums are created (SecurityType)

### Task 8: Apply Migration

```bash
# Apply migration to database
docker exec -it screener_backend alembic upgrade head

# Verify tables were created
docker exec -it screener_postgres psql -U screener_user -d screener_db
\dt
\d securities
\d ohlcv_daily
```

## Success Criteria

- ✅ All 11 tables created in PostgreSQL
- ✅ All constraints (foreign keys, unique, check) enforced
- ✅ All indexes created on key columns
- ✅ Alembic migration works forward and backward
- ✅ Pydantic schemas validate sample data
- ✅ No migration errors in logs
- ✅ Database schema matches Architecture.md specification

## Testing Checklist

```bash
# 1. Verify table creation
docker exec -it screener_postgres psql -U screener_user -d screener_db -c "\dt"

# 2. Verify constraints on securities table
docker exec -it screener_postgres psql -U screener_user -d screener_db -c "\d securities"

# 3. Verify indexes on ohlcv_daily table
docker exec -it screener_postgres psql -U screener_user -d screener_db -c "\d ohlcv_daily"

# 4. Test unique constraint
docker exec -it screener_postgres psql -U screener_user -d screener_db -c \
  "INSERT INTO securities (symbol, isin, security_name, security_type) VALUES ('TEST', 'INE000000001', 'Test Company', 'EQUITY');"

# Should fail with duplicate key error:
docker exec -it screener_postgres psql -U screener_user -d screener_db -c \
  "INSERT INTO securities (symbol, isin, security_name, security_type) VALUES ('TEST', 'INE000000001', 'Test Company 2', 'EQUITY');"

# 5. Test rollback
docker exec -it screener_backend alembic downgrade -1
docker exec -it screener_backend alembic upgrade head
```

## Common Issues & Solutions

### Issue 1: Import Error for Models
**Error:** `ModuleNotFoundError: No module named 'app.models.security'`

**Solution:** Ensure all `__init__.py` files exist in model directories and imports are correct in `alembic/env.py`

### Issue 2: Enum Not Created
**Error:** `type "securitytype" does not exist`

**Solution:** Alembic should create enums automatically, but verify in migration file. May need to add:
```python
from sqlalchemy.dialects.postgresql import ENUM
security_type_enum = ENUM('EQUITY', 'ETF', name='securitytype', create_type=False)
```

### Issue 3: Foreign Key Constraint Fails
**Error:** `foreign key constraint "fk_..." violates foreign key constraint`

**Solution:** Ensure parent table is created before child table in migration. Check table creation order in migration file.

## Next Steps (Phase 1.2)

After completing Phase 1.1:
1. Implement NSE data fetchers (securities, market cap, deals)
2. Create ingestion API endpoints
3. Test data insertion with sample CSV files
4. Verify data validation and error handling

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Create all models | 3-4 hours |
| Create Pydantic schemas | 2-3 hours |
| Generate and review migration | 1 hour |
| Apply migration and test | 1-2 hours |
| Fix any issues | 2-4 hours |
| **Total** | **9-14 hours** |

**Recommended approach:** Spread over 2-3 days to allow for testing and debugging.
