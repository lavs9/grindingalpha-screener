"""
Time-series data models for OHLCV, Market Cap, and Calculated Metrics.

NOTE: These models will be refined in Phase 1.2-1.3 when actual data sources are integrated.
Column names and types should match Upstox API and NSE CSV formats exactly.
"""
from sqlalchemy import Column, BigInteger, String, Date, Numeric, DateTime, Integer, ForeignKey
from sqlalchemy import UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.sql import func
from app.database.base import Base


class OHLCVDaily(Base):
    """
    Daily OHLCV (Open-High-Low-Close-Volume) data for all securities and indices.

    Data Source: Upstox API (/v2/historical-candle and /v2/market-quote/quotes)

    Schema Status: BASELINE - Will verify against actual Upstox API response in Phase 1.3

    Note: No foreign key on symbol for flexibility - indices don't exist in securities table
    """
    __tablename__ = 'ohlcv_daily'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True,
                   comment="Security symbol or index name")
    date = Column(Date, nullable=False, index=True,
                 comment="Trading date")
    open = Column(Numeric(15, 2), nullable=False,
                 comment="Opening price")
    high = Column(Numeric(15, 2), nullable=False,
                 comment="Highest price of the day")
    low = Column(Numeric(15, 2), nullable=False,
                comment="Lowest price of the day")
    close = Column(Numeric(15, 2), nullable=False,
                  comment="Closing price")
    volume = Column(BigInteger, comment="Trading volume (NULL for indices)")
    vwap = Column(Numeric(15, 2), comment="Volume-Weighted Average Price")
    prev_close = Column(Numeric(15, 2), comment="Previous day closing price")
    change_pct = Column(Numeric(8, 4), comment="Percentage change from prev_close")
    upper_circuit = Column(Numeric(15, 2), comment="Upper circuit limit")
    lower_circuit = Column(Numeric(15, 2), comment="Lower circuit limit")
    week_52_high = Column(Numeric(15, 2), comment="52-week high price")
    week_52_low = Column(Numeric(15, 2), comment="52-week low price")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_ohlcv_symbol_date'),
        CheckConstraint('high >= low', name='ck_high_gte_low'),
        CheckConstraint('open >= low AND open <= high', name='ck_open_in_range'),
        CheckConstraint('close >= low AND close <= high', name='ck_close_in_range'),
        Index('idx_ohlcv_symbol_date_desc', 'symbol', text('date DESC')),
        Index('idx_ohlcv_date_desc', text('date DESC')),
    )

    def __repr__(self):
        return f"<OHLCVDaily(symbol='{self.symbol}', date='{self.date}', close={self.close})>"


class MarketCapHistory(Base):
    """
    Daily market capitalization for all securities.

    Data Source: NSE MCAP_*.csv files (downloaded from NSE archives)

    Schema Status: BASELINE - Will verify with actual MCAP CSV format in Phase 1.2

    Note: Market cap values are stored in ₹ crore as per NSE format
    """
    __tablename__ = 'market_cap_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True,
                   comment="Security symbol (foreign key to securities table)")
    date = Column(Date, nullable=False, index=True,
                 comment="Market cap calculation date")
    series = Column(String(10), comment="Trading series")
    security_name = Column(String(255), comment="Security name from CSV")
    category = Column(String(50), comment="Market cap category (if provided)")
    last_trade_date = Column(Date, comment="Last trading date for the security")
    face_value = Column(Numeric(10, 2), comment="Face value per share")
    issue_size = Column(BigInteger, comment="Total issued shares")
    close_price = Column(Numeric(15, 2), comment="Closing price on this date")
    market_cap = Column(Numeric(20, 2), nullable=False, index=True,
                       comment="Market capitalization in ₹ crore")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_marketcap_symbol_date'),
        Index('idx_marketcap_symbol_date_desc', 'symbol', text('date DESC')),
        Index('idx_marketcap_date_mcap_desc', 'date', text('market_cap DESC')),
    )

    def __repr__(self):
        return f"<MarketCapHistory(symbol='{self.symbol}', date='{self.date}', mcap={self.market_cap})>"


class CalculatedMetrics(Base):
    """
    Daily calculated technical indicators and metrics.

    Data Source: Calculated internally based on OHLCV data (Phase 2)

    Schema Status: BASELINE - Structure defined, will be populated in Phase 2

    Note: This table will be populated daily after OHLCV ingestion
    All metrics are calculated from historical price and volume data
    """
    __tablename__ = 'calculated_metrics'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Relative Strength metrics (for RRG charts and screening)
    rs_rating = Column(Numeric(5, 2), comment="Relative Strength rating (0-100)")
    vars_value = Column(Numeric(10, 4), comment="Value-Adjusted Relative Strength")

    # Volatility metrics
    atr = Column(Numeric(15, 2), comment="Average True Range (absolute)")
    atr_pct = Column(Numeric(8, 4), comment="ATR as percentage of close price")

    # Trend metrics (Stan Weinstein Stage Analysis)
    stage = Column(Integer, comment="Market stage: 1=Accumulation, 2=Markup, 3=Distribution, 4=Decline")
    vcp_score = Column(Numeric(5, 2), comment="Volatility Contraction Pattern score (0-100)")

    # Volume metrics
    vol_20d_avg = Column(BigInteger, comment="20-day average volume")
    vol_vs_avg_pct = Column(Numeric(8, 2), comment="Current volume vs 20-day average (%)")

    # Moving averages
    ma_10 = Column(Numeric(15, 2), comment="10-day simple moving average")
    ma_20 = Column(Numeric(15, 2), comment="20-day simple moving average")
    ma_50 = Column(Numeric(15, 2), comment="50-day simple moving average")
    ma_200 = Column(Numeric(15, 2), comment="200-day simple moving average")

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_metrics_symbol_date'),
        Index('idx_metrics_symbol_date_desc', 'symbol', text('date DESC')),
        Index('idx_metrics_rs_rating_desc', text('rs_rating DESC')),
        Index('idx_metrics_stage', 'stage'),
    )

    def __repr__(self):
        return f"<CalculatedMetrics(symbol='{self.symbol}', date='{self.date}', rs_rating={self.rs_rating})>"
