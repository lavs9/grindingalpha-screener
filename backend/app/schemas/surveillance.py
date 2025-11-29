"""
Pydantic schemas for Surveillance models.

These schemas are used for API request/response validation for the
4-table normalized surveillance design.

References:
- app/models/surveillance.py (SQLAlchemy models)
- .claude/file-formats-surveillance.md (Specification)
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import date as date_type, datetime
from typing import Optional


# ========== SURVEILLANCE_LIST SCHEMAS ==========

class SurveillanceListBase(BaseModel):
    """Base schema for SurveillanceList with common fields."""
    symbol: str = Field(..., max_length=11, description="NSE security symbol")
    date: date_type = Field(..., description="Data ingestion date for daily historical tracking")
    nse_exclusive: Optional[str] = Field(None, max_length=1, pattern=r"^[YN]$",
                                         description="Y=NSE exclusive, N=also listed elsewhere")
    status: Optional[str] = Field(None, max_length=1, pattern=r"^[ASI]$",
                                  description="A=Active, S=Suspended, I=Inactive")
    series: Optional[str] = Field(None, max_length=2, description="Trading series: EQ, BE, BZ, SM, ST, etc.")

    # Staged surveillance measures (NULL = not applicable, integer = stage level)
    gsm_stage: Optional[int] = Field(None, ge=0, le=6, description="Graded Surveillance Measure (0-6)")
    long_term_asm_stage: Optional[int] = Field(None, ge=1, le=4, description="Long Term ASM (1-4)")
    short_term_asm_stage: Optional[int] = Field(None, ge=1, le=2, description="Short Term ASM (1-2)")
    sms_category: Optional[int] = Field(None, ge=0, le=1, description="Unsolicited SMS (0-1)")
    irp_stage: Optional[int] = Field(None, ge=0, le=2, description="Insolvency Resolution Process (0-2)")
    default_stage: Optional[int] = Field(None, ge=0, le=1, description="Payment Default (0-1)")
    ica_stage: Optional[int] = Field(None, ge=0, le=1, description="Interconnected Agreements (0-1)")
    esm_stage: Optional[int] = Field(None, ge=1, le=2, description="Enhanced Surveillance Measure (1-2)")

    # Binary surveillance flags (NULL = not flagged, True = flagged)
    high_promoter_pledge: Optional[bool] = Field(None, description="High promoter pledge flag")
    addon_price_band: Optional[bool] = Field(None, description="Additional price band restrictions")
    total_pledge_measure: Optional[bool] = Field(None, description="Total pledge measure flag")
    social_media_platforms: Optional[bool] = Field(None, description="Social media platforms flag")


class SurveillanceListCreate(SurveillanceListBase):
    """Schema for creating a new surveillance list record."""
    pass


class SurveillanceListResponse(SurveillanceListBase):
    """Schema for surveillance list API response."""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== SURVEILLANCE_FUNDAMENTAL_FLAGS SCHEMAS ==========

class SurveillanceFundamentalFlagsBase(BaseModel):
    """Base schema for SurveillanceFundamentalFlags."""
    symbol: str = Field(..., max_length=11, description="NSE security symbol")
    date: date_type = Field(..., description="Data ingestion date")

    # Financial risk flags (NULL = not applicable, True = flagged)
    is_loss_making: Optional[bool] = Field(None, description="≥8 quarters loss (mainboard) or ≥2 years (SME)")
    encumbrance_over_50pct: Optional[bool] = Field(None, description="Promoter encumbrance ≥50%")
    eps_zero_or_negative: Optional[bool] = Field(None, description="EPS zero or negative for 4 quarters")

    # Compliance flags
    under_bz_sz_series: Optional[bool] = Field(None, description="In BZ/SZ series")
    listing_fee_unpaid: Optional[bool] = Field(None, description="Listing fee not paid")

    # Liquidity/Market flags
    fo_exit_scheduled: Optional[bool] = Field(None, description="F&O contracts exiting")
    low_unique_pan_traded: Optional[bool] = Field(None, description="<100 unique PAN in 30 days")
    sme_mm_period_over: Optional[bool] = Field(None, description="SME market making period over")
    sme_not_regularly_traded: Optional[bool] = Field(None, description="SME not regularly traded")

    # Valuation flag
    pe_over_50: Optional[bool] = Field(None, description="P/E ratio >50")


class SurveillanceFundamentalFlagsCreate(SurveillanceFundamentalFlagsBase):
    """Schema for creating a new fundamental flags record."""
    pass


class SurveillanceFundamentalFlagsResponse(SurveillanceFundamentalFlagsBase):
    """Schema for fundamental flags API response."""
    created_at: datetime

    class Config:
        from_attributes = True


# ========== SURVEILLANCE_PRICE_MOVEMENT SCHEMAS ==========

class SurveillancePriceMovementBase(BaseModel):
    """Base schema for SurveillancePriceMovement (Close-to-Close movements)."""
    symbol: str = Field(..., max_length=11, description="NSE security symbol")
    date: date_type = Field(..., description="Data ingestion date")

    # Close-to-Close price movement flags (NULL = not flagged, True = flagged per "top 3 criteria")
    c2c_25pct_5d: Optional[bool] = Field(None, description=">25% in 5 trading days")
    c2c_40pct_15d: Optional[bool] = Field(None, description=">40% in 15 trading days")
    c2c_100pct_60d: Optional[bool] = Field(None, description=">100% in 60 trading days (doubled)")
    c2c_25pct_15d: Optional[bool] = Field(None, description=">25% in 15 days")
    c2c_50pct_1m: Optional[bool] = Field(None, description=">50% in 1 month")
    c2c_90pct_3m: Optional[bool] = Field(None, description=">90% in 3 months")
    c2c_25pct_1m_alt: Optional[bool] = Field(None, description=">25% in 1 month (alternate)")
    c2c_50pct_3m: Optional[bool] = Field(None, description=">50% in 3 months")
    c2c_200pct_365d: Optional[bool] = Field(None, description=">200% in 365 days (tripled)")
    c2c_75pct_6m: Optional[bool] = Field(None, description=">75% in 6 months")
    c2c_100pct_365d: Optional[bool] = Field(None, description=">100% in 365 days (doubled)")


class SurveillancePriceMovementCreate(SurveillancePriceMovementBase):
    """Schema for creating a new price movement record."""
    pass


class SurveillancePriceMovementResponse(SurveillancePriceMovementBase):
    """Schema for price movement API response."""
    created_at: datetime

    class Config:
        from_attributes = True


# ========== SURVEILLANCE_PRICE_VARIATION SCHEMAS ==========

class SurveillancePriceVariationBase(BaseModel):
    """Base schema for SurveillancePriceVariation (High-Low volatility)."""
    symbol: str = Field(..., max_length=11, description="NSE security symbol")
    date: date_type = Field(..., description="Data ingestion date")

    # High-Low price variation flags (NULL = not flagged, True = flagged per "top 3 criteria")
    hl_75pct_1m: Optional[bool] = Field(None, description=">75% in 1 month")
    hl_150pct_3m: Optional[bool] = Field(None, description=">150% in 3 months")
    hl_75pct_3m: Optional[bool] = Field(None, description=">75% in 3 months")
    hl_300pct_365d: Optional[bool] = Field(None, description=">300% in 365 days (extreme volatility)")
    hl_100pct_6m: Optional[bool] = Field(None, description=">100% in 6 months")
    hl_200pct_365d: Optional[bool] = Field(None, description=">200% in 365 days (high volatility)")
    hl_150pct_12m: Optional[bool] = Field(None, description=">150% in 12 months")


class SurveillancePriceVariationCreate(SurveillancePriceVariationBase):
    """Schema for creating a new price variation record."""
    pass


class SurveillancePriceVariationResponse(SurveillancePriceVariationBase):
    """Schema for price variation API response."""
    created_at: datetime

    class Config:
        from_attributes = True


# ========== COMBINED/AGGREGATE SCHEMAS ==========

class SurveillanceAggregatedResponse(BaseModel):
    """
    Aggregated surveillance data for a single symbol.

    Combines all 4 tables for easier frontend consumption.
    Used in API endpoints that return full surveillance profile.
    """
    symbol: str
    date: date

    # From surveillance_list
    nse_exclusive: Optional[str] = None
    status: Optional[str] = None
    series: Optional[str] = None
    gsm_stage: Optional[int] = None
    long_term_asm_stage: Optional[int] = None
    short_term_asm_stage: Optional[int] = None
    sms_category: Optional[int] = None
    irp_stage: Optional[int] = None
    default_stage: Optional[int] = None
    ica_stage: Optional[int] = None
    esm_stage: Optional[int] = None
    high_promoter_pledge: Optional[bool] = None
    addon_price_band: Optional[bool] = None
    total_pledge_measure: Optional[bool] = None
    social_media_platforms: Optional[bool] = None

    # From surveillance_fundamental_flags
    is_loss_making: Optional[bool] = None
    encumbrance_over_50pct: Optional[bool] = None
    eps_zero_or_negative: Optional[bool] = None
    under_bz_sz_series: Optional[bool] = None
    listing_fee_unpaid: Optional[bool] = None
    fo_exit_scheduled: Optional[bool] = None
    low_unique_pan_traded: Optional[bool] = None
    sme_mm_period_over: Optional[bool] = None
    sme_not_regularly_traded: Optional[bool] = None
    pe_over_50: Optional[bool] = None

    # From surveillance_price_movement
    c2c_25pct_5d: Optional[bool] = None
    c2c_40pct_15d: Optional[bool] = None
    c2c_100pct_60d: Optional[bool] = None
    c2c_25pct_15d: Optional[bool] = None
    c2c_50pct_1m: Optional[bool] = None
    c2c_90pct_3m: Optional[bool] = None
    c2c_25pct_1m_alt: Optional[bool] = None
    c2c_50pct_3m: Optional[bool] = None
    c2c_200pct_365d: Optional[bool] = None
    c2c_75pct_6m: Optional[bool] = None
    c2c_100pct_365d: Optional[bool] = None

    # From surveillance_price_variation
    hl_75pct_1m: Optional[bool] = None
    hl_150pct_3m: Optional[bool] = None
    hl_75pct_3m: Optional[bool] = None
    hl_300pct_365d: Optional[bool] = None
    hl_100pct_6m: Optional[bool] = None
    hl_200pct_365d: Optional[bool] = None
    hl_150pct_12m: Optional[bool] = None

    class Config:
        from_attributes = True


class SurveillanceIngestionRequest(BaseModel):
    """
    Request schema for manual surveillance data ingestion.

    Used when ingesting from URL or file upload.
    """
    filename: Optional[str] = Field(None, description="Original CSV filename for date extraction")
    ingestion_date: Optional[date] = Field(None, description="Override date (if not using filename)")
    source_url: Optional[str] = Field(None, description="NSE URL for the CSV file")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "REG1_IND160125.csv",
                "ingestion_date": "2025-01-16",
                "source_url": "https://nsearchives.nseindia.com/surveillance/REG1_IND160125.csv"
            }
        }


class SurveillanceIngestionResponse(BaseModel):
    """
    Response schema for surveillance data ingestion endpoint.

    Returns parsing statistics and ingestion results.
    """
    success: bool
    ingestion_date: Optional[date] = None
    stats: dict = Field(default_factory=dict, description="Parsing statistics")
    records_inserted: dict = Field(default_factory=dict, description="Records inserted per table")
    errors: list = Field(default_factory=list, description="Error messages")
    message: str = Field(default="", description="Human-readable summary")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ingestion_date": "2025-01-16",
                "stats": {
                    "total_rows": 2500,
                    "parsed_rows": 2497,
                    "skipped_rows": 3,
                    "error_rows": 0
                },
                "records_inserted": {
                    "surveillance_list": 2497,
                    "surveillance_fundamental_flags": 2497,
                    "surveillance_price_movement": 2497,
                    "surveillance_price_variation": 2497
                },
                "errors": [],
                "message": "Successfully ingested surveillance data for 2025-01-16"
            }
        }
