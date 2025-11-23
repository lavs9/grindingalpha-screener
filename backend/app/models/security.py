"""
Security and Index models.

NOTE: Schema will be refined in Phase 1.2 when actual NSE CSV files are processed.
Verify column names and types match EQUITY_L.csv and ETF_L.csv formats.
"""
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

    Data Source:
    - NSE EQUITY_L.csv for equities
    - NSE ETF_L.csv for ETFs

    Schema Status: BASELINE - Verify with actual CSV in Phase 1.2
    """
    __tablename__ = 'securities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True,
                   comment="NSE trading symbol (e.g., 'RELIANCE', 'TCS')")
    isin = Column(String(12), unique=True, nullable=False, index=True,
                 comment="12-character ISIN code starting with 'IN'")
    security_name = Column(String(255), nullable=False,
                          comment="Full company/ETF name")
    series = Column(String(10), comment="Trading series (e.g., 'EQ', 'BE')")
    listing_date = Column(Date, comment="Date of listing on NSE")
    paid_up_value = Column(Numeric(15, 2), comment="Paid-up value in rupees")
    market_lot = Column(Integer, comment="Minimum trading quantity")
    face_value = Column(Numeric(10, 2), comment="Face value per share")
    security_type = Column(Enum(SecurityType), nullable=False,
                          comment="EQUITY or ETF")
    is_active = Column(Boolean, default=True, index=True,
                      comment="Whether security is currently traded")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Security(symbol='{self.symbol}', name='{self.security_name}')>"


class Index(Base):
    """
    Master table for market indices.

    Examples: Nifty 50, Nifty Bank, Sensex, Nifty Midcap 100

    Data Source: Manual entry or Upstox API

    Schema Status: BASELINE - May add fields based on requirements
    """
    __tablename__ = 'indices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String(100), unique=True, nullable=False,
                       comment="Full index name (e.g., 'Nifty 50')")
    symbol = Column(String(50), unique=True, nullable=False, index=True,
                   comment="Upstox symbol (e.g., 'Nifty 50' or instrument key)")
    exchange = Column(String(20), default='NSE_INDEX',
                     comment="Exchange identifier for API calls")
    is_active = Column(Boolean, default=True,
                      comment="Whether index is tracked")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Index(symbol='{self.symbol}', name='{self.index_name}')>"
