"""
Pydantic schemas for Security and Index models.

These schemas are used for API request/response validation.
Will be expanded in Phase 1.2 as API endpoints are created.
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class SecurityBase(BaseModel):
    """Base schema for Security with common fields."""
    symbol: str = Field(..., max_length=50, description="NSE trading symbol")
    isin: str = Field(..., max_length=12, pattern=r"^IN[A-Z0-9]{10}$", description="12-character ISIN code starting with 'IN'")
    security_name: str = Field(..., max_length=255, description="Full company/ETF name")
    series: Optional[str] = Field(None, max_length=10, description="Trading series (e.g., 'EQ', 'BE')")
    listing_date: Optional[date] = Field(None, description="Date of listing on NSE")
    paid_up_value: Optional[Decimal] = Field(None, description="Paid-up value in rupees")
    market_lot: Optional[int] = Field(None, gt=0, description="Minimum trading quantity")
    face_value: Optional[Decimal] = Field(None, gt=0, description="Face value per share")
    security_type: str = Field(..., pattern=r"^(EQUITY|ETF)$", description="EQUITY or ETF")


class SecurityCreate(SecurityBase):
    """Schema for creating a new security."""
    is_active: bool = True


class SecurityUpdate(BaseModel):
    """Schema for updating a security (partial updates allowed)."""
    security_name: Optional[str] = Field(None, max_length=255)
    series: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class SecurityResponse(SecurityBase):
    """Schema for security API response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class IndexBase(BaseModel):
    """Base schema for Index with common fields."""
    index_name: str = Field(..., max_length=100, description="Full index name (e.g., 'Nifty 50')")
    symbol: str = Field(..., max_length=50, description="Upstox symbol or instrument key")
    exchange: str = Field(default='NSE_INDEX', max_length=20, description="Exchange identifier")


class IndexCreate(IndexBase):
    """Schema for creating a new index."""
    is_active: bool = True


class IndexResponse(IndexBase):
    """Schema for index API response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
