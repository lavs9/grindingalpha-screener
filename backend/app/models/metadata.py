"""
Metadata models: Industry Classification, Index Constituents, Market Holidays, and Ingestion Logs.

NOTE: These models support core platform operations and data tracking.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, ForeignKey, JSON, Index, Numeric
from sqlalchemy.sql import func
from app.database.base import Base


class IndustryClassification(Base):
    """
    Industry/sector classification for each security.

    Data Source: NSE website API (scraped via Playwright)
    Endpoint: https://www.nseindia.com/api/quote-equity?symbol={symbol}

    Schema Status: BASELINE - Will verify with actual API response in Phase 1.4

    Note: NSE provides 4-level classification: Macro > Sector > Industry > Basic Industry
    This data requires cookie management via Playwright for API access
    """
    __tablename__ = 'industry_classification'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   unique=True, nullable=False, index=True,
                   comment="Security symbol (foreign key to securities table)")
    macro = Column(String(100), comment="Macro-level classification (broadest)")
    sector = Column(String(100), index=True, comment="Sector classification")
    industry = Column(String(100), index=True, comment="Industry classification")
    basic_industry = Column(String(100), comment="Basic industry (most specific)")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(),
                       comment="Last update timestamp - classification can change")

    def __repr__(self):
        return f"<IndustryClassification(symbol='{self.symbol}', sector='{self.sector}', industry='{self.industry}')>"


class IndexConstituent(Base):
    """
    Tracks which securities belong to which indices over time.

    Data Source: NSE Quote Equity API (metadata.pdSectorIndAll)
    Endpoint: https://www.nseindia.com/api/quote-equity?symbol={symbol}

    Schema Status: ACTIVE - Automated from NSE Quote API

    Note: Weightage is NULL until source is identified.
    Historical tracking via effective_from/effective_to dates allows
    backtesting and analysis of index composition changes.

    Example Queries:
    - Which stocks are currently in NIFTY 50? → WHERE index_id=X AND effective_to IS NULL
    - Which stocks were in NIFTY 50 on 2024-01-01? → WHERE index_id=X AND effective_from <= '2024-01-01' AND (effective_to IS NULL OR effective_to >= '2024-01-01')
    - When did RELIANCE exit NIFTY ENERGY? → WHERE symbol='RELIANCE' AND index_id=Y AND effective_to IS NOT NULL
    """
    __tablename__ = 'index_constituents'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    index_id = Column(Integer, ForeignKey('indices.id', ondelete='CASCADE'),
                     nullable=False, index=True,
                     comment="Foreign key to indices table")
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True,
                   comment="Security symbol (foreign key to securities table)")
    effective_from = Column(Date, nullable=False, index=True,
                           comment="Date this constituent relationship became effective (first seen in pdSectorIndAll)")
    effective_to = Column(Date, nullable=True, index=True,
                         comment="Date this constituent relationship ended (NULL = current, removed from pdSectorIndAll)")
    weightage = Column(Numeric(6, 4), nullable=True,
                      comment="Index weightage in percentage (NULL - not available in NSE Quote API)")
    created_at = Column(DateTime, server_default=func.now(),
                       comment="Record creation timestamp")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(),
                       comment="Record last update timestamp")

    # Composite indexes for common queries
    __table_args__ = (
        # Partial index for active constituents (most common query)
        Index('idx_index_constituents_active', 'index_id', 'symbol',
              postgresql_where=(effective_to == None)),
        # Index for date range queries (backtesting)
        Index('idx_index_constituents_dates', 'index_id', 'effective_from', 'effective_to'),
        # Index for symbol-based queries
        Index('idx_index_constituents_symbol_date', 'symbol', 'effective_from'),
    )

    def __repr__(self):
        return f"<IndexConstituent(index_id={self.index_id}, symbol='{self.symbol}', from='{self.effective_from}', to='{self.effective_to}')>"


class MarketHoliday(Base):
    """
    Market trading holidays for NSE and NFO.

    Data Source: Upstox API (/v2/market/holidays/{date})
    Documentation: https://upstox.com/developer/api-documentation/get-market-holidays

    Schema Status: VERIFIED - Matches Upstox API response structure

    Note: Based on Upstox API research, we filter for:
    - holiday_type == "TRADING_HOLIDAY" only
    - "NSE" or "NFO" in closed_exchanges array
    - Stores closed_exchanges as JSON for flexibility

    API Response Structure:
    {
      "data": [{
        "date": "2024-01-26",
        "description": "Republic Day",
        "holiday_type": "TRADING_HOLIDAY",
        "closed_exchanges": ["NSE", "NFO", "CDS", "BSE"]
      }]
    }
    """
    __tablename__ = 'market_holidays'

    id = Column(Integer, primary_key=True, autoincrement=True)
    holiday_date = Column(Date, unique=True, nullable=False, index=True,
                         comment="Holiday date in YYYY-MM-DD format")
    holiday_name = Column(String(255), nullable=False,
                         comment="Holiday description from Upstox API")
    holiday_type = Column(String(50), default='TRADING_HOLIDAY',
                         comment="Type: TRADING_HOLIDAY, SETTLEMENT_HOLIDAY, or SPECIAL_TIMING")
    closed_exchanges = Column(JSON, comment="JSON array of closed exchanges (e.g., ['NSE', 'NFO', 'BSE'])")
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<MarketHoliday(date='{self.holiday_date}', name='{self.holiday_name}', exchanges={self.closed_exchanges})>"


class IngestionLog(Base):
    """
    Tracks data ingestion status for all sources.

    Purpose: Used by n8n workflows for aggregation, monitoring, and error tracking

    Schema Status: FINALIZED - Critical for Phase 1.5 n8n workflows

    Note: This table is central to the database-driven aggregation pattern.
    n8n workflows log results here, and aggregation queries this table
    instead of relying on n8n workflow state.

    Usage Pattern:
    1. Each n8n workflow node logs its execution to this table
    2. Aggregation node queries this table with date filter
    3. Alerts/notifications based on status field
    4. Manual retry by querying failed sources
    """
    __tablename__ = 'ingestion_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True,
                   comment="Data source identifier (e.g., 'nse_securities', 'upstox_ohlcv', 'nse_market_cap')")
    status = Column(String(20), nullable=False,
                   comment="Execution status: 'success', 'failure', or 'partial'")
    records_fetched = Column(Integer, comment="Number of records fetched from source")
    records_inserted = Column(Integer, comment="Number of new records inserted")
    records_updated = Column(Integer, comment="Number of existing records updated")
    records_failed = Column(Integer, comment="Number of records that failed validation/insertion")
    errors = Column(JSON, comment="JSON array of error details for debugging")
    execution_time_ms = Column(Integer, comment="Execution time in milliseconds")
    timestamp = Column(DateTime, server_default=func.now(), index=True,
                      comment="Execution timestamp for this ingestion run")

    def __repr__(self):
        return f"<IngestionLog(source='{self.source}', status='{self.status}', timestamp='{self.timestamp}')>"
