"""
Pydantic schemas for Upstox authentication and instrument management.

This module contains request/response schemas for:
- Upstox login (Playwright automation)
- Instrument ingestion
- Token management
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime as datetime_type
from typing import Optional, List
from decimal import Decimal


# ============================================================================
# Token/Authentication Schemas
# ============================================================================

class UpstoxLoginRequest(BaseModel):
    """Request schema for automated Upstox login."""
    mobile: str = Field(..., description="Mobile number for Upstox login")
    pin: str = Field(..., min_length=4, max_length=6, description="Upstox PIN (4-6 digits)")
    totp_secret: str = Field(..., description="TOTP secret key for 2FA OTP generation")


class UpstoxLoginResponse(BaseModel):
    """Response schema for Upstox login endpoint."""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Status message")
    access_token: Optional[str] = Field(None, description="Access token (masked for security)")
    expires_at: Optional[datetime_type] = Field(None, description="Token expiration timestamp (23:59 IST)")
    errors: Optional[List[str]] = Field(None, description="List of errors if login failed")


# ============================================================================
# Instrument Schemas
# ============================================================================

class UpstoxInstrumentBase(BaseModel):
    """Base schema for Upstox instrument data."""
    instrument_key: str = Field(..., max_length=50, description="Unique Upstox identifier (e.g., NSE_EQ|INE002A01018)")
    exchange: str = Field(..., max_length=20, description="Exchange (NSE_EQ, NSE_INDEX, BSE, etc.)")
    symbol: str = Field(..., max_length=50, description="Trading symbol (e.g., RELIANCE)")
    isin: Optional[str] = Field(None, max_length=12, description="12-character ISIN code")
    name: str = Field(..., max_length=255, description="Full instrument name")
    instrument_type: Optional[str] = Field(None, max_length=50, description="Type (EQUITY, INDEX, etc.)")


class UpstoxInstrumentResponse(UpstoxInstrumentBase):
    """Response schema for instrument queries."""
    id: int
    is_active: bool
    created_at: datetime_type
    updated_at: datetime_type

    class Config:
        from_attributes = True


class InstrumentIngestionResponse(BaseModel):
    """Response schema for instrument ingestion endpoint."""
    success: bool = Field(..., description="Whether ingestion completed successfully")
    total_instruments: int = Field(..., description="Total instruments in source file")
    instruments_inserted: int = Field(..., description="New instruments added to database")
    instruments_updated: int = Field(..., description="Existing instruments updated")
    mappings_created: int = Field(..., description="Symbol-instrument mappings auto-created")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    duration_seconds: int = Field(..., description="Total execution time in seconds")


# ============================================================================
# Symbol Mapping Schemas
# ============================================================================

class SymbolInstrumentMappingBase(BaseModel):
    """Base schema for symbol-instrument mapping."""
    symbol: str = Field(..., max_length=50, description="NSE symbol (e.g., RELIANCE)")
    instrument_key: str = Field(..., max_length=50, description="Upstox instrument key")
    is_primary: bool = Field(True, description="Whether this is the primary mapping for the symbol")
    confidence: Decimal = Field(default=Decimal("100.00"), ge=0, le=100,
                               description="Match confidence (0-100, 100=exact ISIN match)")
    match_method: Optional[str] = Field(None, max_length=50,
                                       description="Matching method (auto_isin, auto_symbol, manual)")


class SymbolInstrumentMappingResponse(SymbolInstrumentMappingBase):
    """Response schema for mapping queries."""
    id: int
    security_id: int
    instrument_id: int
    created_at: datetime_type

    class Config:
        from_attributes = True


class MappingStatsResponse(BaseModel):
    """Statistics for symbol-instrument mappings."""
    total_mappings: int
    primary_mappings: int
    high_confidence: int  # confidence >= 90
    medium_confidence: int  # 50 <= confidence < 90
    low_confidence: int  # confidence < 50
    auto_isin_matches: int
    auto_symbol_matches: int
    manual_matches: int
