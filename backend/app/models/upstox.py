"""
Upstox-related database models.

This module contains models for:
- UpstoxToken: Access token storage with daily expiry (23:59 IST)
- UpstoxInstrument: Cached instrument master data from Upstox API
- SymbolInstrumentMapping: Maps NSE securities to Upstox instrument keys
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date,
    Numeric, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.sql import func
from app.database.base import Base


class UpstoxToken(Base):
    """
    Stores Upstox access tokens with daily expiration (23:59 IST).

    Data Source: Upstox OAuth2 endpoint (/v2/login/authorization/token)

    Schema Rationale:
    - Access tokens expire at 23:59 IST daily, requiring daily refresh
    - Refresh tokens are longer-lived (30-90 days) and used to get new access tokens
    - Tracks token metadata for debugging and rotation
    """
    __tablename__ = 'upstox_tokens'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # OAuth2 tokens
    access_token = Column(Text, nullable=False, unique=True,
                         comment="JWT access token for API calls")
    refresh_token = Column(Text, nullable=True,
                          comment="Refresh token for token renewal (can be NULL if using API key auth)")

    # Token metadata
    token_type = Column(String(20), default='Bearer',
                       comment="Token type (always 'Bearer' for OAuth2)")
    expires_at = Column(DateTime, nullable=False,
                       comment="Token expiration timestamp (typically 23:59 IST)")

    # Tracking
    is_active = Column(Boolean, default=True, index=True,
                      comment="Whether token is currently valid and usable")
    last_used_at = Column(DateTime, nullable=True,
                         comment="Last time this token was used for API calls")

    # Metadata
    created_at = Column(DateTime, server_default=func.now(),
                       comment="Token issuance timestamp")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(),
                       comment="Last update timestamp")

    __table_args__ = (
        Index('idx_upstox_tokens_active_expires', 'is_active', 'expires_at'),
    )

    def __repr__(self):
        return f"<UpstoxToken(id={self.id}, is_active={self.is_active}, expires_at='{self.expires_at}')>"


class UpstoxInstrument(Base):
    """
    Caches Upstox instrument master data for quick lookup.

    Data Source: Upstox API (/v2/market/instruments/{exchange})
    Updates: Daily (or weekly batch) via n8n workflow

    Schema Rationale:
    - Upstox returns 2000+ instruments per exchange
    - Caching locally avoids repeated API calls for symbol lookups
    - Instrument keys are needed for all OHLCV/quote API calls
    - Indexed for fast lookups by symbol or instrument_key
    """
    __tablename__ = 'upstox_instruments'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Upstox identifiers
    instrument_key = Column(String(50), unique=True, nullable=False, index=True,
                           comment="Unique Upstox instrument identifier (e.g., 'NSE_EQ|INE002A01018')")
    exchange = Column(String(20), nullable=False, index=True,
                     comment="Exchange (NSE, BSE, NFO, MCX, etc.)")

    # Security identifiers
    symbol = Column(String(50), nullable=False, index=True,
                   comment="NSE/BSE trading symbol (e.g., 'RELIANCE')")
    isin = Column(String(12), nullable=True, index=True,
                 comment="12-character ISIN code")

    # Instrument metadata
    name = Column(String(255), nullable=False,
                 comment="Full instrument name from Upstox")
    instrument_type = Column(String(50), nullable=True,
                            comment="Instrument type (EQUITY, INDEX, DERIVATIVE, etc.)")

    # Status flags
    is_active = Column(Boolean, default=True, index=True,
                      comment="Whether instrument is actively traded")

    # Sync tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(),
                       comment="Last sync from Upstox API")

    __table_args__ = (
        UniqueConstraint('exchange', 'symbol', name='uq_upstox_exchange_symbol'),
        Index('idx_upstox_instr_symbol_exchange', 'symbol', 'exchange'),
    )

    def __repr__(self):
        return f"<UpstoxInstrument(symbol='{self.symbol}', key='{self.instrument_key}')>"


class SymbolInstrumentMapping(Base):
    """
    Maps NSE securities to Upstox instruments.

    Purpose: Enables quick lookup of Upstox instrument_key from NSE symbol

    Schema Rationale:
    - NSE symbols (RELIANCE) != Upstox instrument keys (NSE_EQ|INE002A01018)
    - n8n workflows need fast symbol→instrument_key resolution
    - One NSE symbol may map to multiple Upstox instruments (rare edge case)
    - Enables bulk OHLCV fetch with proper instrument identification
    """
    __tablename__ = 'symbol_instrument_mapping'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    security_id = Column(Integer, ForeignKey('securities.id', ondelete='CASCADE'),
                        nullable=False, index=True,
                        comment="FK to securities table")
    instrument_id = Column(Integer, ForeignKey('upstox_instruments.id', ondelete='CASCADE'),
                          nullable=False, index=True,
                          comment="FK to upstox_instruments table")

    # Identifiers (denormalized for query speed)
    symbol = Column(String(50), nullable=False, index=True,
                   comment="NSE symbol (denormalized from securities.symbol)")
    instrument_key = Column(String(50), nullable=False,
                           comment="Upstox instrument_key (denormalized from upstox_instruments)")

    # Mapping metadata
    is_primary = Column(Boolean, default=True,
                       comment="Whether this is the primary mapping for this symbol")
    confidence = Column(Numeric(5, 2), default=100.00,
                       comment="Confidence score (0-100) for mapping accuracy")
    match_method = Column(String(50), nullable=True,
                         comment="How mapping was created (auto_isin, auto_symbol, manual)")

    # Tracking
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('security_id', 'instrument_id', name='uq_mapping_security_instrument'),
        Index('idx_mapping_symbol_instrument', 'symbol', 'instrument_key'),
    )

    def __repr__(self):
        return f"<SymbolInstrumentMapping(symbol='{self.symbol}', key='{self.instrument_key}')>"
