"""
Pydantic schemas for OHLCV data.

These schemas validate daily price data from Upstox API.
Will be refined in Phase 1.3 based on actual API responses.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class OHLCVBase(BaseModel):
    """Base schema for OHLCV data with validation rules."""
    symbol: str = Field(..., max_length=50, description="Security symbol or index name")
    date: date = Field(..., description="Trading date")
    open: Decimal = Field(..., gt=0, description="Opening price")
    high: Decimal = Field(..., gt=0, description="Highest price")
    low: Decimal = Field(..., gt=0, description="Lowest price")
    close: Decimal = Field(..., gt=0, description="Closing price")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume (NULL for indices)")
    vwap: Optional[Decimal] = Field(None, gt=0, description="Volume-Weighted Average Price")
    prev_close: Optional[Decimal] = Field(None, gt=0, description="Previous day closing price")
    change_pct: Optional[Decimal] = Field(None, description="Percentage change from prev_close")
    upper_circuit: Optional[Decimal] = Field(None, gt=0, description="Upper circuit limit")
    lower_circuit: Optional[Decimal] = Field(None, gt=0, description="Lower circuit limit")
    week_52_high: Optional[Decimal] = Field(None, gt=0, description="52-week high price")
    week_52_low: Optional[Decimal] = Field(None, gt=0, description="52-week low price")

    @field_validator('high')
    @classmethod
    def high_must_be_greater_than_low(cls, v, info):
        """Validate that high >= low."""
        if 'low' in info.data and v < info.data['low']:
            raise ValueError('high must be >= low')
        return v

    @field_validator('open', 'close')
    @classmethod
    def ohlc_must_be_in_range(cls, v, info):
        """Validate that open and close are within [low, high] range."""
        if 'low' in info.data and 'high' in info.data:
            if v < info.data['low'] or v > info.data['high']:
                raise ValueError(f'{info.field_name} must be between low and high')
        return v


class OHLCVCreate(OHLCVBase):
    """Schema for creating OHLCV record."""
    pass


class OHLCVResponse(OHLCVBase):
    """Schema for OHLCV API response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OHLCVBulkCreate(BaseModel):
    """Schema for bulk OHLCV insertion (daily ingestion)."""
    records: list[OHLCVCreate] = Field(..., min_length=1, description="List of OHLCV records")

    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "symbol": "RELIANCE",
                        "date": "2025-01-15",
                        "open": 2450.50,
                        "high": 2475.00,
                        "low": 2445.00,
                        "close": 2468.75,
                        "volume": 5234567,
                        "vwap": 2460.30
                    }
                ]
            }
        }
