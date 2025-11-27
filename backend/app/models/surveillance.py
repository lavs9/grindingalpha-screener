"""
NSE Surveillance Data Models (63-column REG1_IND format).

Data Source: NSE REG1_IND{DDMMYY}.csv files
Documentation: .claude/file-formats-surveillance.md
Reference Circular: NSE/SURV/65097 dated November 14, 2024

This module implements a 4-table normalized design for surveillance data:
1. surveillance_list - Core staged measures + binary flags (16 columns)
2. surveillance_fundamental_flags - Financial/compliance risks (10 columns)
3. surveillance_price_movement - Close-to-close indicators (11 columns)
4. surveillance_price_variation - High-low volatility (7 columns)

Total: 45 columns stored across 4 tables (18 filler columns ignored)

Encoding Pattern:
- Staged measures: NULL = not applicable (CSV value "100"), integer = stage level
- Binary flags: NULL = not flagged (CSV value "100"), TRUE = flagged (CSV value "0")
"""
from sqlalchemy import Column, String, Date, SmallInteger, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.database.base import Base


class SurveillanceList(Base):
    """
    Core surveillance measures and binary flags.

    Primary Key: (symbol, date) - Daily historical tracking
    Foreign Key: symbol (loose coupling, no constraint per Architecture.md)

    Contains:
    - 5 metadata columns (symbol, date, nse_exclusive, status, series)
    - 8 staged surveillance measures (GSM, ASM, ESM, IRP, Default, ICA, SMS)
    - 4 binary surveillance flags (pledge, price band, social media)
    """
    __tablename__ = 'surveillance_list'

    # Primary Key
    symbol = Column(String(11), primary_key=True, nullable=False,
                   comment="NSE security symbol")
    date = Column(Date, primary_key=True, nullable=False,
                 comment="Data ingestion date (daily historical tracking)")

    # Basic Metadata (CSV Columns 3-5)
    nse_exclusive = Column(String(1), comment="Y=NSE exclusive listing, N=also listed elsewhere")
    status = Column(String(1), comment="A=Active, S=Suspended, I=Inactive")
    series = Column(String(2), comment="Trading series: EQ, BE, BZ, SM, ST, etc.")

    # Staged Surveillance Measures (CSV Columns 6-12, 19)
    # NULL = not applicable (CSV "100"), integer = stage level
    gsm_stage = Column(SmallInteger,
                      comment="Graded Surveillance Measure (0-6): Unusual price/volume patterns")
    long_term_asm_stage = Column(SmallInteger,
                                 comment="Long Term ASM (1-4): Sustained unusual activity")
    short_term_asm_stage = Column(SmallInteger,
                                  comment="Short Term ASM (1-2): Recent unusual activity")
    sms_category = Column(SmallInteger,
                         comment="Unsolicited SMS (0=Info, 1=Watchlist): Securities mentioned in SMS campaigns")
    irp_stage = Column(SmallInteger,
                      comment="Insolvency Resolution Process (0-2): IBC proceedings")
    default_stage = Column(SmallInteger,
                          comment="Payment Default (0-1): Company disclosed defaults")
    ica_stage = Column(SmallInteger,
                      comment="Interconnected Agreements (0-1): Related party transactions under surveillance")
    esm_stage = Column(SmallInteger,
                      comment="Enhanced Surveillance Measure (1-2): Most common indicator")

    # Binary Surveillance Flags (CSV Columns 15-18)
    # NULL = not applicable, TRUE = flagged (CSV "0" means flagged)
    high_promoter_pledge = Column(Boolean,
                                  comment="Promoter shareholding pledged above NSE threshold")
    addon_price_band = Column(Boolean,
                             comment="Additional price band restrictions applied")
    total_pledge_measure = Column(Boolean,
                                  comment="Promoter + Non-Promoter pledge holdings exceed threshold")
    social_media_platforms = Column(Boolean,
                                   comment="Flagged due to social media mentions/campaigns")

    # Audit Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Common query patterns
        Index('idx_surveillance_date', 'date', postgresql_ops={'date': 'DESC'}),
        Index('idx_surveillance_gsm', 'date', 'gsm_stage', postgresql_where='gsm_stage IS NOT NULL'),
        Index('idx_surveillance_esm', 'date', 'esm_stage', postgresql_where='esm_stage IS NOT NULL'),
        Index('idx_surveillance_asm', 'date', 'long_term_asm_stage', 'short_term_asm_stage',
             postgresql_where='long_term_asm_stage IS NOT NULL OR short_term_asm_stage IS NOT NULL'),
    )

    def __repr__(self):
        stages = []
        if self.gsm_stage is not None:
            stages.append(f"GSM:{self.gsm_stage}")
        if self.esm_stage is not None:
            stages.append(f"ESM:{self.esm_stage}")
        if self.long_term_asm_stage is not None:
            stages.append(f"LT-ASM:{self.long_term_asm_stage}")
        if self.short_term_asm_stage is not None:
            stages.append(f"ST-ASM:{self.short_term_asm_stage}")

        measures_str = ', '.join(stages) if stages else 'None'
        return f"<SurveillanceList(symbol='{self.symbol}', date='{self.date}', measures=[{measures_str}])>"


class SurveillanceFundamentalFlags(Base):
    """
    Financial and compliance risk indicators.

    Primary Key: (symbol, date) - Daily historical tracking

    Contains 10 boolean flags indicating:
    - Financial risks (loss-making, high encumbrance, zero EPS)
    - Compliance issues (BZ/SZ series, unpaid listing fee)
    - Liquidity concerns (low participation, SME trading issues)
    - Valuation metrics (high P/E ratio, F&O exit)
    """
    __tablename__ = 'surveillance_fundamental_flags'

    # Primary Key
    symbol = Column(String(11), primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)

    # Financial Risk Flags (CSV Columns 20-21, 27)
    # NULL = not applicable, TRUE = flagged (CSV "0" means under this category)
    is_loss_making = Column(Boolean,
                           comment="≥8 quarters loss (mainboard) or ≥2 years (SME) on consolidated basis")
    encumbrance_over_50pct = Column(Boolean,
                                   comment="Promoter/promoter group encumbrance ≥50% of total capital")
    eps_zero_or_negative = Column(Boolean,
                                 comment="EPS zero or negative for 4 trailing quarters (aggregated)")

    # Compliance Flags (CSV Columns 22-23)
    under_bz_sz_series = Column(Boolean,
                               comment="In BZ/SZ series due to SEBI SOP Circular non-compliance")
    listing_fee_unpaid = Column(Boolean,
                               comment="Failed to pay annual listing fee to exchange")

    # Liquidity/Market Flags (CSV Columns 25, 28-30)
    fo_exit_scheduled = Column(Boolean,
                              comment="Derivative contracts exiting F&O segment (no new far-month contracts)")
    low_unique_pan_traded = Column(Boolean,
                                  comment="<100 unique PAN cards traded in previous 30 days (low participation)")
    sme_mm_period_over = Column(Boolean,
                               comment="SME mandatory market-making period ended (exit may be difficult)")
    sme_not_regularly_traded = Column(Boolean,
                                     comment="SME security not regularly traded (exit may be difficult)")

    # Valuation Flag (CSV Column 26)
    pe_over_50 = Column(Boolean,
                       comment="P/E ratio >50 based on 4 trailing quarters")

    # Audit Timestamp
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # Indexes for filtering by specific risk flags
        Index('idx_fundamental_date', 'date', postgresql_ops={'date': 'DESC'}),
        Index('idx_fundamental_loss_making', 'date', 'is_loss_making',
             postgresql_where='is_loss_making = TRUE'),
        Index('idx_fundamental_high_encumbrance', 'date', 'encumbrance_over_50pct',
             postgresql_where='encumbrance_over_50pct = TRUE'),
    )

    def __repr__(self):
        flags = []
        if self.is_loss_making:
            flags.append("Loss-Making")
        if self.encumbrance_over_50pct:
            flags.append("High-Encumbrance")
        if self.under_bz_sz_series:
            flags.append("BZ/SZ")

        flags_str = ', '.join(flags) if flags else 'None'
        return f"<SurveillanceFundamentalFlags(symbol='{self.symbol}', date='{self.date}', flags=[{flags_str}])>"


class SurveillancePriceMovement(Base):
    """
    Close-to-close price movement indicators.

    Primary Key: (symbol, date) - Daily historical tracking

    Contains 11 boolean flags measuring close-to-close price movements:
    - Short term: 5 days, 15 days, 1 month (various thresholds: 25%, 40%, 50%)
    - Medium term: 60 days, 3 months, 6 months (thresholds: 50%, 75%, 90%, 100%)
    - Long term: 365 days (thresholds: 100%, 200%)

    Note: "Top Three Criteria" logic per NSE/SURV/64402 (Para 4.5)
    CSV "100" = not in top 3 criteria, CSV "0" = flagged as top 3
    """
    __tablename__ = 'surveillance_price_movement'

    # Primary Key
    symbol = Column(String(11), primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)

    # Close-to-Close Price Movement Flags (CSV Columns 31-41)
    # NULL = not flagged, TRUE = flagged as per "top 3 criteria"
    c2c_25pct_5d = Column(Boolean, comment=">25% in 5 trading days")
    c2c_40pct_15d = Column(Boolean, comment=">40% in 15 trading days")
    c2c_100pct_60d = Column(Boolean, comment=">100% in 60 trading days (doubled)")
    c2c_25pct_15d = Column(Boolean, comment=">25% in 15 days")
    c2c_50pct_1m = Column(Boolean, comment=">50% in 1 month")
    c2c_90pct_3m = Column(Boolean, comment=">90% in 3 months")
    c2c_25pct_1m_alt = Column(Boolean, comment=">25% in 1 month (alternate threshold)")
    c2c_50pct_3m = Column(Boolean, comment=">50% in 3 months")
    c2c_200pct_365d = Column(Boolean, comment=">200% in 365 days (tripled)")
    c2c_75pct_6m = Column(Boolean, comment=">75% in 6 months")
    c2c_100pct_365d = Column(Boolean, comment=">100% in 365 days (doubled)")

    # Audit Timestamp
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # Index for finding high momentum stocks
        Index('idx_price_movement_date', 'date', postgresql_ops={'date': 'DESC'}),
        Index('idx_price_movement_high_momentum', 'date',
             postgresql_where='c2c_100pct_60d = TRUE OR c2c_200pct_365d = TRUE'),
    )

    def __repr__(self):
        flags = []
        if self.c2c_100pct_60d:
            flags.append("100%/60d")
        if self.c2c_200pct_365d:
            flags.append("200%/365d")
        if self.c2c_100pct_365d:
            flags.append("100%/365d")

        flags_str = ', '.join(flags) if flags else 'None'
        return f"<SurveillancePriceMovement(symbol='{self.symbol}', date='{self.date}', movements=[{flags_str}])>"


class SurveillancePriceVariation(Base):
    """
    High-low price variation (volatility) indicators.

    Primary Key: (symbol, date) - Daily historical tracking

    Contains 7 boolean flags measuring high-low price variations:
    - Short term: 1 month (75%)
    - Medium term: 3 months (75%, 150%), 6 months (100%)
    - Long term: 12 months (150%), 365 days (200%, 300%)

    Note: "Top Three Criteria" logic applies per NSE/SURV/64402
    """
    __tablename__ = 'surveillance_price_variation'

    # Primary Key
    symbol = Column(String(11), primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)

    # High-Low Price Variation Flags (CSV Columns 42-48)
    # NULL = not flagged, TRUE = flagged as per "top 3 criteria"
    hl_75pct_1m = Column(Boolean, comment=">75% in 1 month")
    hl_150pct_3m = Column(Boolean, comment=">150% in 3 months")
    hl_75pct_3m = Column(Boolean, comment=">75% in 3 months")
    hl_300pct_365d = Column(Boolean, comment=">300% in 365 days (extreme volatility)")
    hl_100pct_6m = Column(Boolean, comment=">100% in 6 months")
    hl_200pct_365d = Column(Boolean, comment=">200% in 365 days (high volatility)")
    hl_150pct_12m = Column(Boolean, comment=">150% in 12 months")

    # Audit Timestamp
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # Index for finding high volatility stocks
        Index('idx_price_variation_date', 'date', postgresql_ops={'date': 'DESC'}),
        Index('idx_price_variation_high_volatility', 'date',
             postgresql_where='hl_300pct_365d = TRUE OR hl_200pct_365d = TRUE'),
    )

    def __repr__(self):
        flags = []
        if self.hl_300pct_365d:
            flags.append("300%/365d")
        if self.hl_200pct_365d:
            flags.append("200%/365d")
        if self.hl_150pct_12m:
            flags.append("150%/12m")

        flags_str = ', '.join(flags) if flags else 'None'
        return f"<SurveillancePriceVariation(symbol='{self.symbol}', date='{self.date}', variations=[{flags_str}])>"
