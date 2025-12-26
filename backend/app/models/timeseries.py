"""
Time-series data models for OHLCV, Market Cap, and Calculated Metrics.

NOTE: These models will be refined in Phase 1.2-1.3 when actual data sources are integrated.
Column names and types should match Upstox API and NSE CSV formats exactly.
"""
from sqlalchemy import Column, BigInteger, String, Date, Numeric, DateTime, Integer, ForeignKey
from sqlalchemy import UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.sql import func
from app.database.base import Base


class IndexOHLCVDaily(Base):
    """
    Daily OHLCV data for NSE indices (NIFTY 50, sectoral indices, etc.).

    Data Source: Upstox API historical candles for NSE indices

    Schema Status: ACTIVE - Separate table from stock OHLCV for better data organization

    Note: Indices have different characteristics than stocks (no volume for some indices)
    Used for: RRG Charts, Benchmarking, Sectoral analysis
    """
    __tablename__ = 'index_ohlcv_daily'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True,
                   comment="Index symbol (e.g., NIFTY 50, NIFTY BANK)")
    date = Column(Date, nullable=False, index=True, comment="Trading date")

    open = Column(Numeric(12, 2), nullable=False, comment="Opening index value")
    high = Column(Numeric(12, 2), nullable=False, comment="Highest index value")
    low = Column(Numeric(12, 2), nullable=False, comment="Lowest index value")
    close = Column(Numeric(12, 2), nullable=False, comment="Closing index value")
    volume = Column(BigInteger, nullable=True, comment="Volume (may be null for some indices)")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_index_ohlcv_symbol_date'),
        Index('idx_index_ohlcv_symbol_date_desc', 'symbol', text('date DESC')),
        Index('idx_index_ohlcv_date', 'date'),
    )

    def __repr__(self):
        return f"<IndexOHLCVDaily(symbol='{self.symbol}', date='{self.date}', close={self.close})>"


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

    Schema Status: PHASE 2 - Complete schema with all 40+ metrics for screeners

    Note: This table will be populated daily after OHLCV ingestion
    All metrics are calculated from historical price and volume data
    """
    __tablename__ = 'calculated_metrics'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(50), ForeignKey('securities.symbol', ondelete='CASCADE'),
                   nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # ===== PRICE CHANGES =====
    change_1d_percent = Column(Numeric(10, 4), comment="1-day % change")
    change_1d_value = Column(Numeric(12, 2), comment="1-day absolute change")
    change_1w_percent = Column(Numeric(10, 4), comment="1-week (5 trading days) % change")
    change_1m_percent = Column(Numeric(10, 4), comment="1-month (21 days) % change")
    change_3m_percent = Column(Numeric(10, 4), comment="3-month (63 days) % change")
    change_6m_percent = Column(Numeric(10, 4), comment="6-month (126 days) % change")

    # ===== RELATIVE STRENGTH =====
    rs_percentile = Column(Numeric(5, 2), comment="RS percentile rank (0-100) based on 1M change")
    vars_score = Column(Numeric(10, 4), comment="Volatility-Adjusted RS = RS / ADR%")
    varw_score = Column(Numeric(10, 4), comment="Volatility-Adjusted Relative Weakness for laggards")

    # ===== VOLATILITY METRICS =====
    atr_14 = Column(Numeric(10, 4), comment="14-day ATR (Average True Range)")
    atr_percent = Column(Numeric(10, 4), comment="ATR as % of close (ATR/close * 100)")
    adr_percent = Column(Numeric(10, 4), comment="20-day Average Daily Range %")
    today_range_percent = Column(Numeric(10, 4), comment="Today's (high-low)/close %")

    # ===== VOLUME METRICS =====
    volume_50d_avg = Column(BigInteger, comment="50-day average volume")
    rvol = Column(Numeric(10, 4), comment="Relative Volume (today/50d avg)")
    is_volume_surge = Column(Integer, comment="1 if RVOL >= 1.5, else 0")

    # ===== MOVING AVERAGES =====
    ema_10 = Column(Numeric(10, 4), comment="10-day EMA")
    sma_20 = Column(Numeric(10, 4), comment="20-day SMA")
    sma_50 = Column(Numeric(10, 4), comment="50-day SMA")
    sma_100 = Column(Numeric(10, 4), comment="100-day SMA")
    sma_200 = Column(Numeric(10, 4), comment="200-day SMA")

    # Distance from MAs (as %)
    distance_from_ema10_percent = Column(Numeric(10, 4), comment="(close - EMA10) / EMA10 * 100")
    distance_from_sma50_percent = Column(Numeric(10, 4), comment="(close - SMA50) / SMA50 * 100")
    distance_from_sma200_percent = Column(Numeric(10, 4), comment="(close - SMA200) / SMA200 * 100")

    # MA Alignment (for MA Stacked screener)
    is_ma_stacked = Column(Integer, comment="1 if close > EMA10 > SMA20 > SMA50 > SMA100 > SMA200")

    # ===== ATR EXTENSION =====
    atr_extension_from_sma50 = Column(
        Numeric(10, 4),
        comment="((close/SMA50) - 1) / (ATR/close) - how extended from SMA50 in ATR units"
    )
    lod_atr_percent = Column(
        Numeric(10, 4),
        comment="((low - close) / ATR * 100) - Low of Day distance in ATR%"
    )
    is_lod_tight = Column(Integer, comment="1 if LoD < 60% ATR, else 0")

    # ===== DARVAS BOX (20-DAY) =====
    darvas_20d_high = Column(Numeric(15, 2), comment="20-day highest high")
    darvas_20d_low = Column(Numeric(15, 2), comment="20-day lowest low")
    darvas_position_percent = Column(
        Numeric(10, 4),
        comment="(close - low) / (high - low) * 100 within 20-day range"
    )

    # ===== NEW HIGHS/LOWS =====
    is_new_20d_high = Column(Integer, comment="1 if high >= 20-day max high")
    is_new_20d_low = Column(Integer, comment="1 if low <= 20-day min low")

    # ===== ORH/M30 Re-ORH (Proxy from Daily) =====
    orh_proxy = Column(Numeric(15, 2), comment="Opening Range High proxy (first bar high)")
    is_m30_reclaim = Column(Integer, comment="1 if close > ORH proxy (approximation)")

    # ===== VCP PATTERN SCORE =====
    vcp_score = Column(Integer, comment="1-5 based on narrowing range over 3-5 bars")

    # ===== STAGE CLASSIFICATION =====
    stage = Column(Integer, comment="1=Basing, 2A=Early Uptrend, 2B=At Darvas 100%, 2C=Extended (7x ATR), 3=Topping, 4=Declining")
    stage_detail = Column(String(10), comment="Stage detail like '2A', '2B', '2C'")

    # ===== BREADTH METRICS (Universe-wide, same for all stocks on a date) =====
    universe_up_count = Column(Integer, comment="# stocks up for the day (universe-wide)")
    universe_down_count = Column(Integer, comment="# stocks down for the day (universe-wide)")
    mcclellan_oscillator = Column(Numeric(10, 4), comment="McClellan Oscillator (advances-declines)")
    mcclellan_summation = Column(Numeric(12, 4), comment="McClellan Summation Index (cumulative)")

    # ===== RRG METRICS (for sector/industry level) =====
    rs_ratio = Column(Numeric(10, 4), comment="(security close / benchmark close) * 100")
    rs_momentum = Column(Numeric(10, 4), comment="1-week ROC of RS-Ratio, smoothed")

    # ===== CANDLE TYPE =====
    is_green_candle = Column(Integer, comment="1 if close >= open, else 0")

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_metrics_symbol_date'),
        Index('idx_metrics_symbol_date_desc', 'symbol', text('date DESC')),
        Index('idx_metrics_rs_percentile_desc', text('rs_percentile DESC')),
        Index('idx_metrics_vars_desc', text('vars_score DESC')),
        Index('idx_metrics_stage', 'stage'),
        Index('idx_metrics_date_rs', 'date', text('rs_percentile DESC')),
        Index('idx_metrics_volume_surge', 'is_volume_surge', 'date'),
    )

    def __repr__(self):
        return f"<CalculatedMetrics(symbol='{self.symbol}', date='{self.date}', rs_percentile={self.rs_percentile})>"
