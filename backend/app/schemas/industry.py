"""
Pydantic schemas for Industry Classification and Index Constituent models.

These schemas are used for API request/response validation for NSE industry data.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import date as date_type, datetime
from typing import Optional, List
from decimal import Decimal


class IndustryClassificationBase(BaseModel):
    """Base schema for Industry Classification with common fields."""
    symbol: str = Field(..., max_length=50, description="NSE trading symbol")
    macro: Optional[str] = Field(None, max_length=100, description="Macro industry category (e.g., 'Energy')")
    sector: Optional[str] = Field(None, max_length=100, description="Sector (e.g., 'Oil Gas & Consumable Fuels')")
    industry: Optional[str] = Field(None, max_length=100, description="Industry (e.g., 'Petroleum Products')")
    basic_industry: Optional[str] = Field(None, max_length=100, description="Basic industry (e.g., 'Refineries & Marketing')")


class IndustryClassificationCreate(IndustryClassificationBase):
    """Schema for creating industry classification."""
    pass


class IndustryClassificationResponse(IndustryClassificationBase):
    """Schema for industry classification API response."""
    created_at: date_typetime
    updated_at: date_typetime

    class Config:
        from_attributes = True


class IndexConstituentBase(BaseModel):
    """Base schema for Index Constituent with common fields."""
    index_id: int = Field(..., description="Foreign key to indices table")
    symbol: str = Field(..., max_length=50, description="Security symbol")
    effective_from: date_type = Field(..., description="Date this constituent relationship became effective")
    effective_to: Optional[date] = Field(None, description="Date this constituent relationship ended (NULL = current)")
    weightage: Optional[Decimal] = Field(None, description="Index weightage in percentage (NULL if not available)")


class IndexConstituentCreate(IndexConstituentBase):
    """Schema for creating index constituent."""
    pass


class IndexConstituentResponse(IndexConstituentBase):
    """Schema for index constituent API response."""
    id: int
    created_at: date_typetime
    updated_at: date_typetime

    class Config:
        from_attributes = True


class IndustryIngestionRequest(BaseModel):
    """Schema for industry classification ingestion API request."""
    limit: Optional[int] = Field(None, gt=0, le=5000, description="Limit number of symbols to scrape (for testing)")
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to scrape (e.g., ['RELIANCE', 'TCS'])")


class IndustryIngestionResponse(BaseModel):
    """Schema for industry classification ingestion API response."""
    success: bool
    total_symbols: int
    symbols_processed: int
    symbols_failed: int
    industry_records: int
    index_constituent_records: int
    errors: List[str]
    duration_seconds: int


class IndexConstituentListResponse(BaseModel):
    """Schema for listing index constituents."""
    index_name: str
    as_of_date: date_type
    constituents: List[str]
    count: int


class IndustryStatsResponse(BaseModel):
    """Schema for industry classification statistics."""
    total_securities: int
    securities_with_industry: int
    unique_macros: int
    unique_sectors: int
    unique_industries: int
    unique_basic_industries: int
