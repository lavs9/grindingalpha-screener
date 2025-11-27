# NSE Surveillance Data Format Specification

**Data Source:** NSE Regulatory Surveillance Files (REG1_IND format)
**File Pattern:** `REG1_IND[DDMMYY].csv`
**Update Frequency:** Daily (T+0, published after market close)
**Total Columns:** 63
**Reference Circular:** NSE/SURV/65097 dated November 14, 2024
**Sample File:** [.claude/samples/REG1_IND160125.csv](.claude/samples/REG1_IND160125.csv)
**Documentation PDF:** [.claude/samples/2818.pdf](.claude/samples/2818.pdf)

---

## Overview

NSE publishes daily surveillance data for all listed securities across 63 columns categorizing various risk indicators:
- **Staged Surveillance Measures** (GSM, ASM, ESM, IRP, etc.) - Progressive severity levels
- **Fundamental Risk Flags** (loss-making, high pledge, compliance failures)
- **Price Movement Indicators** (close-to-close percentage changes)
- **Volatility Indicators** (high-low price variations)

**Key Encoding Pattern:**
- `100` = Not applicable / Not under this measure
- `0`, `1`, `2`, etc. = Active surveillance stage or flagged condition

---

## Column Structure (All 63 Columns)

### A. BASIC METADATA (Columns 1-5)

| Column | Field Name | Type | Description | Values |
|--------|------------|------|-------------|--------|
| 1 | ScripCode | Integer | Legacy code (not used) | Always "NA" |
| 2 | Symbol | Char(11) | NSE security symbol | e.g., "RELIANCE", "TCS" |
| 3 | NSE Exclusive | Char(1) | NSE-exclusive listing | Y/N |
| 4 | Status | Char(1) | Trading status | A=Active, S=Suspended, I=Inactive |
| 5 | Series | Char(2) | Scrip series | EQ, BE, BZ, SM, ST, etc. |

---

### B. MAJOR SURVEILLANCE MEASURES (Columns 6-19)

#### Staged Surveillance (Progressive Severity)

| Column | Field Name | Type | Description | Stages | Notes |
|--------|------------|------|-------------|--------|-------|
| 6 | GSM | Char(3) | Graded Surveillance Measure | 100=Not applicable<br>0=Identified<br>1-4, 6=Stage 1-4, 6 | No Stage 5 mentioned |
| 7 | Long_Term_Additional_Surveillance_Measure | Char(3) | Long Term ASM | 100=Not applicable<br>1-4=Stage 1-4 | |
| 10 | Short_Term_Additional_Surveillance_Measure | Char(3) | Short Term ASM | 100=Not applicable<br>1-2=Stage 1-2 | |
| 19 | ESM | Char(3) | Enhanced Surveillance Measure | 100=Not applicable<br>1-2=Stage I-II | **Most common in sample data** |

#### Other Surveillance Categories

| Column | Field Name | Type | Description | Values | Notes |
|--------|------------|------|-------------|--------|-------|
| 8 | Unsolicited_SMS | Char(3) | SMS surveillance | 100=Not under SMS<br>1=Current Watchlist<br>0=For Information List | |
| 9 | Insolvency_Resolution_Process(IRP) | Char(3) | IBC proceedings | 100=Not under IRP<br>0=Corporate disclosure received<br>1=IBC Stage I<br>2=IBC Stage II | |
| 11 | Default | Char(3) | Payment default disclosure | 100=Not under default<br>0=Identified<br>1=Under Additional Surveillance | |
| 12 | ICA | Char(3) | Interconnected Agreements | 100=Not under ICA<br>0=Identified<br>1=Under Surveillance Measure | |
| 15 | Pledge | Char(3) | High promoter pledge | 100=Not under measure<br>1=Under surveillance | Binary flag |
| 16 | Add-on_PB | Char(3) | Add-on Price Band | 100=Not under measure<br>1=Under add-on price band | Binary flag |
| 17 | Total Pledge | Char(3) | Total pledge holdings (Promoter + Non-Promoter) | 100=No action required<br>1=Under regulatory measure | Binary flag |
| 18 | Social Media Platforms | Char(3) | Social media mention surveillance | 100=Not under measure<br>2=Under Surveillance Measure list | Binary flag |

#### Reserved Columns

| Column | Field Name | Type | Description |
|--------|------------|------|-------------|
| 13-14 | Filler4, Filler5 | - | Reserved for future surveillance measures |

---

### C. FUNDAMENTAL/FINANCIAL INDICATORS (Columns 20-30)

**All are Binary Flags:** 100 = Not under this category, 0 = Under this category

| Column | Field Name | Description | Criteria |
|--------|------------|-------------|----------|
| 20 | Loss making | Loss-making company | ≥8 quarters (mainboard) or ≥2 years (SME) on consolidated basis |
| 21 | The Overall encumbered share in the scrip is more than 50 Percent | High encumbrance | Promoter/promoter group encumbrance ≥50% of total capital |
| 22 | Under BZ/SZ Group | Non-compliance series | In BZ/SZ series due to SEBI SOP Circular non-compliance |
| 23 | Company has failed to pay Annual listing fee | Listing fee default | Annual listing fee unpaid |
| 24 | Filler12 | Reserved | - |
| 25 | Derivative contracts in the scrip to be moved out of F and O | F&O exit scheduled | No new far-month contracts, existing contracts to expire |
| 26 | Scrip PE is greater than 50 (4 trailing quarters) | High valuation | P/E ratio > 50 based on 4 trailing quarters |
| 27 | EPS in the scrip is zero (4 trailing quarters) | Zero/negative earnings | Includes companies with negative aggregated EPS |
| 28 | Less than 100 unique PAN traded in previous 30 days | Low participation | Low liquidity/participation indicator |
| 29 | Mandatory Market making period in SME scrip is over | SME market making ended | Exit may be difficult |
| 30 | SME scrip is not regularly traded | SME low liquidity | Exit may be difficult |

---

### D. PRICE MOVEMENT INDICATORS (Columns 31-41)

**All are Binary Flags:** 100 = Not under this category, 0 = Under this category
**Important Note:** "Not under this category" means criterion is NOT within top three criteria per NSE/SURV/64402 dated Oct 04, 2024 (Para 4.5)

**Close-to-Close Price Movement Thresholds:**

| Column | Field Name | Threshold | Timeframe |
|--------|------------|-----------|-----------|
| 31 | Close to Close price movement > 25% in previous 5 trading days | >25% | 5 trading days |
| 32 | Close to Close price movement > 40% in previous 15 trading days | >40% | 15 trading days |
| 33 | Close to Close price movement > 100% in previous 60 trading days | >100% | 60 trading days |
| 34 | Close to Close price movement > 25% in previous 15 days | >25% | 15 days |
| 35 | Close to Close price movement > 50% in previous 1 month | >50% | 1 month |
| 36 | Close to Close price movement > 90% in previous 3 months | >90% | 3 months |
| 37 | Close to Close price movement > 25% in previous 1 month | >25% | 1 month (duplicate timeframe, different threshold) |
| 38 | Close to Close price movement > 50% in previous 3 months | >50% | 3 months |
| 39 | Close to Close price movement > 200% in previous 365 days | >200% | 365 days |
| 40 | Close to Close price movement > 75% in previous 6 months | >75% | 6 months |
| 41 | Close to Close price movement > 100% in previous 365 days | >100% | 365 days |

---

### E. HIGH-LOW PRICE VARIATION INDICATORS (Columns 42-48)

**All are Binary Flags:** 100 = Not under this category, 0 = Under this category
**Same Note:** Top three criteria logic applies per NSE/SURV/64402

**High-Low Price Variation Thresholds:**

| Column | Field Name | Threshold | Timeframe |
|--------|------------|-----------|-----------|
| 42 | High low price variation > 75% in previous 1 month | >75% | 1 month |
| 43 | High low price variation > 150% in previous 3 months | >150% | 3 months |
| 44 | High low price variation > 75% in previous 3 months | >75% | 3 months |
| 45 | High low price variation > 300% in previous 365 days | >300% | 365 days |
| 46 | High low price variation > 100% in previous 6 months | >100% | 6 months |
| 47 | High low price variation > 200% in previous 365 days | >200% | 365 days |
| 48 | High low price variation > 150% in previous 12 months | >150% | 12 months |

---

### F. RESERVED FILLER COLUMNS (Columns 49-63)

| Column Range | Field Names | Purpose |
|--------------|-------------|---------|
| 49-63 | Filler17 through Filler31 | Reserved for future surveillance measures (15 columns) |

---

## Database Schema Design

### Architecture: Normalized Multi-Table Design

**Rationale:**
- Query performance (targeted queries without scanning 60+ columns)
- Clear logical categorization matching NSE's grouping
- Efficient indexing for common surveillance queries
- Storage optimization (NULL handling vs storing "100" repeatedly)
- Maintainability (15 reserved filler columns available for future NSE measures)

---

### TABLE 1: `surveillance_list`

**Purpose:** Core staged surveillance measures and binary flags
**Primary Key:** (`symbol`, `date`)
**Foreign Key:** `symbol` references `securities(symbol)` (NO CONSTRAINT - loose coupling)

```sql
CREATE TABLE surveillance_list (
    symbol VARCHAR(11) NOT NULL,
    date DATE NOT NULL,

    -- Basic metadata
    nse_exclusive CHAR(1),
    status CHAR(1),  -- A=Active, S=Suspended, I=Inactive
    series VARCHAR(2),

    -- Staged surveillance measures (NULL = not applicable)
    gsm_stage SMALLINT,  -- NULL, 0, 1-4, 6
    long_term_asm_stage SMALLINT,  -- NULL, 1-4
    short_term_asm_stage SMALLINT,  -- NULL, 1-2
    sms_category SMALLINT,  -- NULL, 0 (info), 1 (watchlist)
    irp_stage SMALLINT,  -- NULL, 0-2
    default_stage SMALLINT,  -- NULL, 0, 1
    ica_stage SMALLINT,  -- NULL, 0, 1
    esm_stage SMALLINT,  -- NULL, 1-2

    -- Binary surveillance flags (NULL = not applicable)
    high_promoter_pledge BOOLEAN,
    addon_price_band BOOLEAN,
    total_pledge_measure BOOLEAN,
    social_media_platforms BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, date)
);

-- Indexes for common queries
CREATE INDEX idx_surveillance_date ON surveillance_list(date DESC);
CREATE INDEX idx_surveillance_gsm ON surveillance_list(date, gsm_stage) WHERE gsm_stage IS NOT NULL;
CREATE INDEX idx_surveillance_esm ON surveillance_list(date, esm_stage) WHERE esm_stage IS NOT NULL;
CREATE INDEX idx_surveillance_asm ON surveillance_list(date, long_term_asm_stage, short_term_asm_stage)
    WHERE long_term_asm_stage IS NOT NULL OR short_term_asm_stage IS NOT NULL;
```

**Column Mapping:**

| CSV Column # | CSV Column Name | DB Column | Data Type | Values |
|-------------|-----------------|-----------|-----------|--------|
| 2 | Symbol | `symbol` | VARCHAR(11) | Primary key |
| - | Date | `date` | DATE | Primary key (ingestion date) |
| 3 | NSE Exclusive | `nse_exclusive` | CHAR(1) | Y/N |
| 4 | Status | `status` | CHAR(1) | A/S/I |
| 5 | Series | `series` | VARCHAR(2) | EQ/BE/BZ/SM/ST |
| 6 | GSM | `gsm_stage` | SMALLINT | NULL, 0, 1-4, 6 |
| 7 | Long_Term_Additional_Surveillance_Measure | `long_term_asm_stage` | SMALLINT | NULL, 1-4 |
| 10 | Short_Term_Additional_Surveillance_Measure | `short_term_asm_stage` | SMALLINT | NULL, 1-2 |
| 8 | Unsolicited_SMS | `sms_category` | SMALLINT | NULL, 0, 1 |
| 9 | Insolvency_Resolution_Process(IRP) | `irp_stage` | SMALLINT | NULL, 0-2 |
| 11 | Default | `default_stage` | SMALLINT | NULL, 0, 1 |
| 12 | ICA | `ica_stage` | SMALLINT | NULL, 0, 1 |
| 19 | ESM | `esm_stage` | SMALLINT | NULL, 1-2 |
| 15 | Pledge | `high_promoter_pledge` | BOOLEAN | NULL/true |
| 16 | Add-on_PB | `addon_price_band` | BOOLEAN | NULL/true |
| 17 | Total Pledge | `total_pledge_measure` | BOOLEAN | NULL/true |
| 18 | Social Media Platforms | `social_media_platforms` | BOOLEAN | NULL/true |

---

### TABLE 2: `surveillance_fundamental_flags`

**Purpose:** Financial and compliance risk indicators
**Primary Key:** (`symbol`, `date`)
**No Foreign Key Constraint** (loose coupling)

```sql
CREATE TABLE surveillance_fundamental_flags (
    symbol VARCHAR(11) NOT NULL,
    date DATE NOT NULL,

    -- All boolean flags (NULL = not applicable, TRUE = flagged)
    is_loss_making BOOLEAN,
    encumbrance_over_50pct BOOLEAN,
    under_bz_sz_series BOOLEAN,
    listing_fee_unpaid BOOLEAN,
    fo_exit_scheduled BOOLEAN,
    pe_over_50 BOOLEAN,
    eps_zero_or_negative BOOLEAN,
    low_unique_pan_traded BOOLEAN,
    sme_mm_period_over BOOLEAN,
    sme_not_regularly_traded BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, date)
);

-- Indexes for filtering by specific risk flags
CREATE INDEX idx_fundamental_date ON surveillance_fundamental_flags(date DESC);
CREATE INDEX idx_fundamental_loss_making ON surveillance_fundamental_flags(date, is_loss_making) WHERE is_loss_making = TRUE;
CREATE INDEX idx_fundamental_high_encumbrance ON surveillance_fundamental_flags(date, encumbrance_over_50pct) WHERE encumbrance_over_50pct = TRUE;
```

**Column Mapping:**

| CSV Column # | CSV Column Name | DB Column | Data Type |
|-------------|-----------------|-----------|-----------|
| 2 | Symbol | `symbol` | VARCHAR(11) |
| - | Date | `date` | DATE |
| 20 | Loss making | `is_loss_making` | BOOLEAN |
| 21 | The Overall encumbered share in the scrip is more than 50 Percent | `encumbrance_over_50pct` | BOOLEAN |
| 22 | Under BZ/SZ Group | `under_bz_sz_series` | BOOLEAN |
| 23 | Company has failed to pay Annual listing fee | `listing_fee_unpaid` | BOOLEAN |
| 25 | Derivative contracts in the scrip to be moved out of F and O | `fo_exit_scheduled` | BOOLEAN |
| 26 | Scrip PE is greater than 50 (4 trailing quarters) | `pe_over_50` | BOOLEAN |
| 27 | EPS in the scrip is zero (4 trailing quarters) | `eps_zero_or_negative` | BOOLEAN |
| 28 | Less than 100 unique PAN traded in previous 30 days | `low_unique_pan_traded` | BOOLEAN |
| 29 | Mandatory Market making period in SME scrip is over | `sme_mm_period_over` | BOOLEAN |
| 30 | SME scrip is not regularly traded | `sme_not_regularly_traded` | BOOLEAN |

---

### TABLE 3: `surveillance_price_movement`

**Purpose:** Close-to-close price movement indicators
**Primary Key:** (`symbol`, `date`)
**No Foreign Key Constraint** (loose coupling)

```sql
CREATE TABLE surveillance_price_movement (
    symbol VARCHAR(11) NOT NULL,
    date DATE NOT NULL,

    -- All boolean flags (NULL = not flagged, TRUE = flagged as per "top 3 criteria")
    c2c_25pct_5d BOOLEAN,       -- >25% in 5 trading days
    c2c_40pct_15d BOOLEAN,      -- >40% in 15 trading days
    c2c_100pct_60d BOOLEAN,     -- >100% in 60 trading days
    c2c_25pct_15d BOOLEAN,      -- >25% in 15 days
    c2c_50pct_1m BOOLEAN,       -- >50% in 1 month
    c2c_90pct_3m BOOLEAN,       -- >90% in 3 months
    c2c_25pct_1m_alt BOOLEAN,   -- >25% in 1 month (alternate threshold)
    c2c_50pct_3m BOOLEAN,       -- >50% in 3 months
    c2c_200pct_365d BOOLEAN,    -- >200% in 365 days
    c2c_75pct_6m BOOLEAN,       -- >75% in 6 months
    c2c_100pct_365d BOOLEAN,    -- >100% in 365 days

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, date)
);

-- Index for finding high momentum stocks
CREATE INDEX idx_price_movement_date ON surveillance_price_movement(date DESC);
CREATE INDEX idx_price_movement_high_momentum ON surveillance_price_movement(date)
    WHERE c2c_100pct_60d = TRUE OR c2c_200pct_365d = TRUE;
```

**Column Mapping:**

| CSV Column # | CSV Column Name | DB Column | Data Type |
|-------------|-----------------|-----------|-----------|
| 2 | Symbol | `symbol` | VARCHAR(11) |
| - | Date | `date` | DATE |
| 31 | Close to Close price movement > 25% in previous 5 trading days | `c2c_25pct_5d` | BOOLEAN |
| 32 | Close to Close price movement > 40% in previous 15 trading days | `c2c_40pct_15d` | BOOLEAN |
| 33 | Close to Close price movement > 100% in previous 60 trading days | `c2c_100pct_60d` | BOOLEAN |
| 34 | Close to Close price movement > 25% in previous 15 days | `c2c_25pct_15d` | BOOLEAN |
| 35 | Close to Close price movement > 50% in previous 1 month | `c2c_50pct_1m` | BOOLEAN |
| 36 | Close to Close price movement > 90% in previous 3 months | `c2c_90pct_3m` | BOOLEAN |
| 37 | Close to Close price movement > 25% in previous 1 month | `c2c_25pct_1m_alt` | BOOLEAN |
| 38 | Close to Close price movement > 50% in previous 3 months | `c2c_50pct_3m` | BOOLEAN |
| 39 | Close to Close price movement > 200% in previous 365 days | `c2c_200pct_365d` | BOOLEAN |
| 40 | Close to Close price movement > 75% in previous 6 months | `c2c_75pct_6m` | BOOLEAN |
| 41 | Close to Close price movement > 100% in previous 365 days | `c2c_100pct_365d` | BOOLEAN |

---

### TABLE 4: `surveillance_price_variation`

**Purpose:** High-low volatility indicators
**Primary Key:** (`symbol`, `date`)
**No Foreign Key Constraint** (loose coupling)

```sql
CREATE TABLE surveillance_price_variation (
    symbol VARCHAR(11) NOT NULL,
    date DATE NOT NULL,

    -- All boolean flags (NULL = not flagged, TRUE = flagged as per "top 3 criteria")
    hl_75pct_1m BOOLEAN,        -- >75% in 1 month
    hl_150pct_3m BOOLEAN,       -- >150% in 3 months
    hl_75pct_3m BOOLEAN,        -- >75% in 3 months
    hl_300pct_365d BOOLEAN,     -- >300% in 365 days
    hl_100pct_6m BOOLEAN,       -- >100% in 6 months
    hl_200pct_365d BOOLEAN,     -- >200% in 365 days
    hl_150pct_12m BOOLEAN,      -- >150% in 12 months

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, date)
);

-- Index for finding high volatility stocks
CREATE INDEX idx_price_variation_date ON surveillance_price_variation(date DESC);
CREATE INDEX idx_price_variation_high_volatility ON surveillance_price_variation(date)
    WHERE hl_300pct_365d = TRUE OR hl_200pct_365d = TRUE;
```

**Column Mapping:**

| CSV Column # | CSV Column Name | DB Column | Data Type |
|-------------|-----------------|-----------|-----------|
| 2 | Symbol | `symbol` | VARCHAR(11) |
| - | Date | `date` | DATE |
| 42 | High low price variation > 75% in previous 1 month | `hl_75pct_1m` | BOOLEAN |
| 43 | High low price variation > 150% in previous 3 months | `hl_150pct_3m` | BOOLEAN |
| 44 | High low price variation > 75% in previous 3 months | `hl_75pct_3m` | BOOLEAN |
| 45 | High low price variation > 300% in previous 365 days | `hl_300pct_365d` | BOOLEAN |
| 46 | High low price variation > 100% in previous 6 months | `hl_100pct_6m` | BOOLEAN |
| 47 | High low price variation > 200% in previous 365 days | `hl_200pct_365d` | BOOLEAN |
| 48 | High low price variation > 150% in previous 12 months | `hl_150pct_12m` | BOOLEAN |

---

## Field Metadata for UI Integration

### Python Constants for Field Descriptions

Use these constants in your application code for consistent field descriptions across API responses, UI tooltips, and documentation.

```python
# app/constants/surveillance_metadata.py

from enum import Enum
from typing import Dict, Optional

class SurveillanceFieldMetadata:
    """Metadata for surveillance database fields - descriptions for UI integration"""

    # Table 1: surveillance_list
    SURVEILLANCE_LIST_FIELDS = {
        'nse_exclusive': {
            'label': 'NSE Exclusive',
            'description': 'Security is exclusively listed on NSE',
            'type': 'char',
            'values': {'Y': 'Yes', 'N': 'No'}
        },
        'status': {
            'label': 'Trading Status',
            'description': 'Current trading status of the security',
            'type': 'char',
            'values': {'A': 'Active', 'S': 'Suspended', 'I': 'Inactive'}
        },
        'series': {
            'label': 'Scrip Series',
            'description': 'Trading series classification',
            'type': 'varchar',
            'values': 'EQ (Equity), BE, BZ (Non-compliance), SM, ST (SME), etc.'
        },
        'gsm_stage': {
            'label': 'GSM Stage',
            'description': 'Graded Surveillance Measure - Progressive surveillance stages for securities with unusual price/volume patterns',
            'type': 'smallint',
            'values': {0: 'Identified', 1: 'Stage 1', 2: 'Stage 2', 3: 'Stage 3', 4: 'Stage 4', 6: 'Stage 6'},
            'severity': 'high'
        },
        'long_term_asm_stage': {
            'label': 'Long Term ASM',
            'description': 'Long Term Additional Surveillance Measure - Applied to securities with sustained unusual activity',
            'type': 'smallint',
            'values': {1: 'Stage 1', 2: 'Stage 2', 3: 'Stage 3', 4: 'Stage 4'},
            'severity': 'high'
        },
        'short_term_asm_stage': {
            'label': 'Short Term ASM',
            'description': 'Short Term Additional Surveillance Measure - Applied to securities with recent unusual activity',
            'type': 'smallint',
            'values': {1: 'Stage 1', 2: 'Stage 2'},
            'severity': 'medium'
        },
        'sms_category': {
            'label': 'Unsolicited SMS',
            'description': 'Securities mentioned in unsolicited SMS campaigns',
            'type': 'smallint',
            'values': {0: 'For Information List', 1: 'Current Watchlist'},
            'severity': 'medium'
        },
        'irp_stage': {
            'label': 'IRP Stage',
            'description': 'Insolvency Resolution Process - Company under IBC (Insolvency and Bankruptcy Code) proceedings',
            'type': 'smallint',
            'values': {0: 'Corporate Disclosure Received', 1: 'IBC Stage I', 2: 'IBC Stage II'},
            'severity': 'critical'
        },
        'default_stage': {
            'label': 'Default Status',
            'description': 'Company has disclosed payment defaults',
            'type': 'smallint',
            'values': {0: 'Default Identified', 1: 'Additional Surveillance for Default'},
            'severity': 'high'
        },
        'ica_stage': {
            'label': 'ICA Status',
            'description': 'Interconnected Agreements - Related party transactions under surveillance',
            'type': 'smallint',
            'values': {0: 'Identified', 1: 'Under Surveillance Measure'},
            'severity': 'medium'
        },
        'esm_stage': {
            'label': 'ESM Stage',
            'description': 'Enhanced Surveillance Measure - Most commonly triggered surveillance indicator',
            'type': 'smallint',
            'values': {1: 'Stage I', 2: 'Stage II'},
            'severity': 'high'
        },
        'high_promoter_pledge': {
            'label': 'High Promoter Pledge',
            'description': 'Promoter shareholding pledged above NSE threshold',
            'type': 'boolean',
            'severity': 'high'
        },
        'addon_price_band': {
            'label': 'Add-on Price Band',
            'description': 'Additional price band restrictions applied to limit volatility',
            'type': 'boolean',
            'severity': 'medium'
        },
        'total_pledge_measure': {
            'label': 'Total Pledge Measure',
            'description': 'Combined promoter and non-promoter pledge holdings exceed threshold',
            'type': 'boolean',
            'severity': 'high'
        },
        'social_media_platforms': {
            'label': 'Social Media Surveillance',
            'description': 'Security flagged due to social media platform mentions/campaigns',
            'type': 'boolean',
            'severity': 'medium'
        }
    }

    # Table 2: surveillance_fundamental_flags
    FUNDAMENTAL_FLAGS_FIELDS = {
        'is_loss_making': {
            'label': 'Loss Making',
            'description': 'Company reporting losses for ≥8 quarters (mainboard) or ≥2 years (SME) on consolidated basis',
            'type': 'boolean',
            'severity': 'high',
            'category': 'financial'
        },
        'encumbrance_over_50pct': {
            'label': 'High Encumbrance',
            'description': 'Promoter/promoter group shareholding encumbrance ≥50% of total capital',
            'type': 'boolean',
            'severity': 'critical',
            'category': 'financial'
        },
        'under_bz_sz_series': {
            'label': 'BZ/SZ Series',
            'description': 'Security moved to BZ/SZ series due to non-compliance with SEBI SOP Circular',
            'type': 'boolean',
            'severity': 'high',
            'category': 'compliance'
        },
        'listing_fee_unpaid': {
            'label': 'Listing Fee Unpaid',
            'description': 'Company has failed to pay annual listing fee to exchange',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'compliance'
        },
        'fo_exit_scheduled': {
            'label': 'F&O Exit Scheduled',
            'description': 'Derivative contracts in the security to be moved out of Futures & Options segment (no new far-month contracts)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity'
        },
        'pe_over_50': {
            'label': 'High P/E Ratio',
            'description': 'Price-to-Earnings ratio greater than 50 based on 4 trailing quarters',
            'type': 'boolean',
            'severity': 'low',
            'category': 'valuation'
        },
        'eps_zero_or_negative': {
            'label': 'Zero/Negative EPS',
            'description': 'Earnings Per Share is zero or negative for 4 trailing quarters (aggregated)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'financial'
        },
        'low_unique_pan_traded': {
            'label': 'Low Participation',
            'description': 'Less than 100 unique PAN cards traded in previous 30 days (low investor participation)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity'
        },
        'sme_mm_period_over': {
            'label': 'SME MM Period Over',
            'description': 'Mandatory market-making period for SME security has ended (exit may be difficult)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity'
        },
        'sme_not_regularly_traded': {
            'label': 'SME Low Trading',
            'description': 'SME security is not regularly traded (exit may be difficult)',
            'type': 'boolean',
            'severity': 'medium',
            'category': 'liquidity'
        }
    }

    # Table 3: surveillance_price_movement
    PRICE_MOVEMENT_FIELDS = {
        'c2c_25pct_5d': {
            'label': 'C2C >25% (5D)',
            'description': 'Close-to-close price movement greater than 25% in previous 5 trading days',
            'type': 'boolean',
            'threshold': '25%',
            'period': '5 trading days',
            'category': 'short_term'
        },
        'c2c_40pct_15d': {
            'label': 'C2C >40% (15D)',
            'description': 'Close-to-close price movement greater than 40% in previous 15 trading days',
            'type': 'boolean',
            'threshold': '40%',
            'period': '15 trading days',
            'category': 'short_term'
        },
        'c2c_100pct_60d': {
            'label': 'C2C >100% (60D)',
            'description': 'Close-to-close price movement greater than 100% in previous 60 trading days (doubled)',
            'type': 'boolean',
            'threshold': '100%',
            'period': '60 trading days',
            'category': 'medium_term'
        },
        'c2c_25pct_15d': {
            'label': 'C2C >25% (15D)',
            'description': 'Close-to-close price movement greater than 25% in previous 15 days',
            'type': 'boolean',
            'threshold': '25%',
            'period': '15 days',
            'category': 'short_term'
        },
        'c2c_50pct_1m': {
            'label': 'C2C >50% (1M)',
            'description': 'Close-to-close price movement greater than 50% in previous 1 month',
            'type': 'boolean',
            'threshold': '50%',
            'period': '1 month',
            'category': 'medium_term'
        },
        'c2c_90pct_3m': {
            'label': 'C2C >90% (3M)',
            'description': 'Close-to-close price movement greater than 90% in previous 3 months',
            'type': 'boolean',
            'threshold': '90%',
            'period': '3 months',
            'category': 'medium_term'
        },
        'c2c_25pct_1m_alt': {
            'label': 'C2C >25% (1M Alt)',
            'description': 'Close-to-close price movement greater than 25% in previous 1 month (alternate threshold)',
            'type': 'boolean',
            'threshold': '25%',
            'period': '1 month',
            'category': 'medium_term'
        },
        'c2c_50pct_3m': {
            'label': 'C2C >50% (3M)',
            'description': 'Close-to-close price movement greater than 50% in previous 3 months',
            'type': 'boolean',
            'threshold': '50%',
            'period': '3 months',
            'category': 'medium_term'
        },
        'c2c_200pct_365d': {
            'label': 'C2C >200% (1Y)',
            'description': 'Close-to-close price movement greater than 200% in previous 365 days (tripled)',
            'type': 'boolean',
            'threshold': '200%',
            'period': '365 days',
            'category': 'long_term'
        },
        'c2c_75pct_6m': {
            'label': 'C2C >75% (6M)',
            'description': 'Close-to-close price movement greater than 75% in previous 6 months',
            'type': 'boolean',
            'threshold': '75%',
            'period': '6 months',
            'category': 'medium_term'
        },
        'c2c_100pct_365d': {
            'label': 'C2C >100% (1Y)',
            'description': 'Close-to-close price movement greater than 100% in previous 365 days (doubled)',
            'type': 'boolean',
            'threshold': '100%',
            'period': '365 days',
            'category': 'long_term'
        }
    }

    # Table 4: surveillance_price_variation
    PRICE_VARIATION_FIELDS = {
        'hl_75pct_1m': {
            'label': 'H/L >75% (1M)',
            'description': 'High-low price variation greater than 75% in previous 1 month',
            'type': 'boolean',
            'threshold': '75%',
            'period': '1 month',
            'category': 'short_term'
        },
        'hl_150pct_3m': {
            'label': 'H/L >150% (3M)',
            'description': 'High-low price variation greater than 150% in previous 3 months',
            'type': 'boolean',
            'threshold': '150%',
            'period': '3 months',
            'category': 'medium_term'
        },
        'hl_75pct_3m': {
            'label': 'H/L >75% (3M)',
            'description': 'High-low price variation greater than 75% in previous 3 months',
            'type': 'boolean',
            'threshold': '75%',
            'period': '3 months',
            'category': 'medium_term'
        },
        'hl_300pct_365d': {
            'label': 'H/L >300% (1Y)',
            'description': 'High-low price variation greater than 300% in previous 365 days (extreme volatility)',
            'type': 'boolean',
            'threshold': '300%',
            'period': '365 days',
            'category': 'long_term'
        },
        'hl_100pct_6m': {
            'label': 'H/L >100% (6M)',
            'description': 'High-low price variation greater than 100% in previous 6 months',
            'type': 'boolean',
            'threshold': '100%',
            'period': '6 months',
            'category': 'medium_term'
        },
        'hl_200pct_365d': {
            'label': 'H/L >200% (1Y)',
            'description': 'High-low price variation greater than 200% in previous 365 days (high volatility)',
            'type': 'boolean',
            'threshold': '200%',
            'period': '365 days',
            'category': 'long_term'
        },
        'hl_150pct_12m': {
            'label': 'H/L >150% (12M)',
            'description': 'High-low price variation greater than 150% in previous 12 months',
            'type': 'boolean',
            'threshold': '150%',
            'period': '12 months',
            'category': 'long_term'
        }
    }

    @classmethod
    def get_field_description(cls, table: str, field: str) -> Optional[str]:
        """Get user-friendly description for a field"""
        field_map = {
            'surveillance_list': cls.SURVEILLANCE_LIST_FIELDS,
            'surveillance_fundamental_flags': cls.FUNDAMENTAL_FLAGS_FIELDS,
            'surveillance_price_movement': cls.PRICE_MOVEMENT_FIELDS,
            'surveillance_price_variation': cls.PRICE_VARIATION_FIELDS
        }
        table_fields = field_map.get(table, {})
        return table_fields.get(field, {}).get('description')

    @classmethod
    def get_field_label(cls, table: str, field: str) -> Optional[str]:
        """Get short label for a field (UI display)"""
        field_map = {
            'surveillance_list': cls.SURVEILLANCE_LIST_FIELDS,
            'surveillance_fundamental_flags': cls.FUNDAMENTAL_FLAGS_FIELDS,
            'surveillance_price_movement': cls.PRICE_MOVEMENT_FIELDS,
            'surveillance_price_variation': cls.PRICE_VARIATION_FIELDS
        }
        table_fields = field_map.get(table, {})
        return table_fields.get(field, {}).get('label')

    @classmethod
    def get_all_fields_for_table(cls, table: str) -> Dict:
        """Get all field metadata for a table"""
        field_map = {
            'surveillance_list': cls.SURVEILLANCE_LIST_FIELDS,
            'surveillance_fundamental_flags': cls.FUNDAMENTAL_FLAGS_FIELDS,
            'surveillance_price_movement': cls.PRICE_MOVEMENT_FIELDS,
            'surveillance_price_variation': cls.PRICE_VARIATION_FIELDS
        }
        return field_map.get(table, {})
```

### Usage Examples in API/UI

#### Example 1: API Response with Field Metadata
```python
from app.constants.surveillance_metadata import SurveillanceFieldMetadata

def get_surveillance_summary(symbol: str):
    # ... fetch data from database ...

    response = {
        'symbol': symbol,
        'surveillance_measures': {
            'esm_stage': {
                'value': 2,
                'label': SurveillanceFieldMetadata.get_field_label('surveillance_list', 'esm_stage'),
                'description': SurveillanceFieldMetadata.get_field_description('surveillance_list', 'esm_stage')
            },
            'high_promoter_pledge': {
                'value': True,
                'label': SurveillanceFieldMetadata.get_field_label('surveillance_list', 'high_promoter_pledge'),
                'description': SurveillanceFieldMetadata.get_field_description('surveillance_list', 'high_promoter_pledge')
            }
        }
    }
    return response

# Output:
# {
#   "symbol": "EXAMPLE",
#   "surveillance_measures": {
#     "esm_stage": {
#       "value": 2,
#       "label": "ESM Stage",
#       "description": "Enhanced Surveillance Measure - Most commonly triggered surveillance indicator"
#     },
#     "high_promoter_pledge": {
#       "value": true,
#       "label": "High Promoter Pledge",
#       "description": "Promoter shareholding pledged above NSE threshold"
#     }
#   }
# }
```

#### Example 2: Frontend UI Tooltips
```typescript
// React component example
import { surveillanceMetadata } from './constants';

function SurveillanceIndicator({ field, value }) {
  const metadata = surveillanceMetadata.surveillance_list[field];

  return (
    <Tooltip title={metadata.description}>
      <Chip
        label={metadata.label}
        color={value ? 'error' : 'default'}
      />
    </Tooltip>
  );
}
```

#### Example 3: Dynamic Form Generation
```python
def generate_surveillance_filter_form():
    """Generate filter form with descriptions for screener UI"""
    form_fields = []

    for field, metadata in SurveillanceFieldMetadata.SURVEILLANCE_LIST_FIELDS.items():
        form_fields.append({
            'field': field,
            'label': metadata['label'],
            'description': metadata['description'],
            'type': metadata['type'],
            'severity': metadata.get('severity', 'low')
        })

    return form_fields
```

---

## Data Parsing Logic

### Encoding Conversion Rules

#### For Staged Measures (Columns 6-12, 19)
```python
def parse_surveillance_stage(value: str) -> Optional[int]:
    """
    Convert NSE surveillance stage encoding to database format.

    Args:
        value: CSV value (e.g., "100", "0", "1", "2")

    Returns:
        NULL if not applicable (100), else integer stage value
    """
    if not value or value.strip() == "100":
        return None  # Not under this surveillance measure
    return int(value)

# Examples:
# "100" → NULL (not applicable)
# "0" → 0 (identified/initial stage)
# "1" → 1 (Stage 1)
# "4" → 4 (Stage 4)
```

#### For Binary Flags (Columns 15-18, 20-48)
```python
def parse_surveillance_flag(value: str) -> Optional[bool]:
    """
    Convert NSE binary flag encoding to database boolean.

    Args:
        value: CSV value ("100" or "0")

    Returns:
        NULL if not applicable (100), TRUE if flagged (0)
    """
    if not value or value.strip() == "100":
        return None  # Not under this category
    return True  # "0" means flagged/under this category

# Examples:
# "100" → NULL (not flagged)
# "0" → TRUE (flagged/under surveillance)
```

### CSV Parsing Example

```python
import csv
from datetime import datetime
from typing import Dict, List

def parse_surveillance_csv(file_path: str, ingestion_date: datetime.date) -> Dict[str, List]:
    """
    Parse NSE REG1_IND surveillance CSV file.

    Returns:
        Dictionary with 4 keys (one per table):
        - 'surveillance_list': List of core surveillance records
        - 'fundamental_flags': List of fundamental risk records
        - 'price_movement': List of price movement records
        - 'price_variation': List of price variation records
    """
    result = {
        'surveillance_list': [],
        'fundamental_flags': [],
        'price_movement': [],
        'price_variation': []
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            symbol = row['Symbol'].strip()

            # TABLE 1: surveillance_list
            result['surveillance_list'].append({
                'symbol': symbol,
                'date': ingestion_date,
                'nse_exclusive': row['NSE Exclusive'],
                'status': row['Status'],
                'series': row['Series'],
                'gsm_stage': parse_surveillance_stage(row['GSM']),
                'long_term_asm_stage': parse_surveillance_stage(row['Long_Term_Additional_Surveillance_Measure']),
                'short_term_asm_stage': parse_surveillance_stage(row['Short_Term_Additional_Surveillance_Measure']),
                'sms_category': parse_surveillance_stage(row['Unsolicited_SMS']),
                'irp_stage': parse_surveillance_stage(row['Insolvency_Resolution_Process(IRP)']),
                'default_stage': parse_surveillance_stage(row['Default']),
                'ica_stage': parse_surveillance_stage(row['ICA']),
                'esm_stage': parse_surveillance_stage(row['ESM']),
                'high_promoter_pledge': parse_surveillance_flag(row['Pledge']),
                'addon_price_band': parse_surveillance_flag(row['Add-on_PB']),
                'total_pledge_measure': parse_surveillance_flag(row['Total Pledge']),
                'social_media_platforms': parse_surveillance_flag(row['Social Media Platforms'])
            })

            # TABLE 2: fundamental_flags
            result['fundamental_flags'].append({
                'symbol': symbol,
                'date': ingestion_date,
                'is_loss_making': parse_surveillance_flag(row['Loss making']),
                'encumbrance_over_50pct': parse_surveillance_flag(row['The Overall encumbered share in the scrip is more than 50 Percent']),
                'under_bz_sz_series': parse_surveillance_flag(row['Under BZ/SZ Group']),
                'listing_fee_unpaid': parse_surveillance_flag(row['Company has failed to pay Annual listing fee']),
                'fo_exit_scheduled': parse_surveillance_flag(row['Derivative contracts in the scrip to be moved out of F and O']),
                'pe_over_50': parse_surveillance_flag(row['Scrip PE is greater than 50 (4 trailing quarters)']),
                'eps_zero_or_negative': parse_surveillance_flag(row['EPS in the scrip is zero (4 trailing quarters)']),
                'low_unique_pan_traded': parse_surveillance_flag(row['Less than 100 unique PAN traded in previous 30 days']),
                'sme_mm_period_over': parse_surveillance_flag(row['Mandatory Market making period in SME scrip is over']),
                'sme_not_regularly_traded': parse_surveillance_flag(row['SME scrip is not regularly traded'])
            })

            # TABLE 3: price_movement (11 columns)
            result['price_movement'].append({
                'symbol': symbol,
                'date': ingestion_date,
                'c2c_25pct_5d': parse_surveillance_flag(row['Close to Close price movement > 25% in previous 5 trading days']),
                'c2c_40pct_15d': parse_surveillance_flag(row['Close to Close price movement > 40% in previous 15 trading days']),
                'c2c_100pct_60d': parse_surveillance_flag(row['Close to Close price movement > 100% in previous 60 trading days']),
                'c2c_25pct_15d': parse_surveillance_flag(row['Close to Close price movement > 25% in previous 15 days']),
                'c2c_50pct_1m': parse_surveillance_flag(row['Close to Close price movement > 50% in previous 1 month']),
                'c2c_90pct_3m': parse_surveillance_flag(row['Close to Close price movement > 90% in previous 3 months']),
                'c2c_25pct_1m_alt': parse_surveillance_flag(row['Close to Close price movement > 25% in previous 1 month']),  # Column 37
                'c2c_50pct_3m': parse_surveillance_flag(row['Close to Close price movement > 50% in previous 3 months']),
                'c2c_200pct_365d': parse_surveillance_flag(row['Close to Close price movement > 200% in previous 365 days']),
                'c2c_75pct_6m': parse_surveillance_flag(row['Close to Close price movement > 75% in previous 6 months']),
                'c2c_100pct_365d': parse_surveillance_flag(row['Close to Close price movement > 100% in previous 365 days'])
            })

            # TABLE 4: price_variation (7 columns)
            result['price_variation'].append({
                'symbol': symbol,
                'date': ingestion_date,
                'hl_75pct_1m': parse_surveillance_flag(row['High low price variation > 75% in previous 1 month']),
                'hl_150pct_3m': parse_surveillance_flag(row['High low price variation > 150% in previous 3 months']),
                'hl_75pct_3m': parse_surveillance_flag(row['High low price variation > 75% in previous 3 months']),
                'hl_300pct_365d': parse_surveillance_flag(row['High low price variation > 300% in previous 365 days']),
                'hl_100pct_6m': parse_surveillance_flag(row['High low price variation > 100% in previous 6 months']),
                'hl_200pct_365d': parse_surveillance_flag(row['High low price variation > 200% in previous 365 days']),
                'hl_150pct_12m': parse_surveillance_flag(row['High low price variation > 150% in previous 12 months'])
            })

    return result
```

---

## Ignored Columns

**Not Stored in Database:**

| Column # | Column Name | Reason |
|----------|-------------|--------|
| 1 | ScripCode | Always "NA", legacy field |
| 13-14 | Filler4, Filler5 | Reserved for future use |
| 24 | Filler12 | Reserved for future use |
| 49-63 | Filler17-31 | Reserved for future use (15 columns) |

**Total Ignored:** 18 columns
**Total Stored:** 45 columns across 4 tables

---

## Common Query Patterns

### Example 1: Find all stocks under ESM Stage 2
```sql
SELECT symbol, date, esm_stage
FROM surveillance_list
WHERE date = '2025-01-16'
  AND esm_stage = 2
ORDER BY symbol;
```

### Example 2: Find loss-making stocks with high pledge
```sql
SELECT
    sl.symbol,
    sl.date,
    sff.is_loss_making,
    sl.high_promoter_pledge
FROM surveillance_list sl
JOIN surveillance_fundamental_flags sff
    ON sl.symbol = sff.symbol AND sl.date = sff.date
WHERE sl.date = '2025-01-16'
  AND sff.is_loss_making = TRUE
  AND sl.high_promoter_pledge = TRUE;
```

### Example 3: Find high momentum stocks (>100% in 60 days)
```sql
SELECT
    spm.symbol,
    spm.date,
    spm.c2c_100pct_60d,
    spm.c2c_200pct_365d
FROM surveillance_price_movement spm
WHERE spm.date = '2025-01-16'
  AND spm.c2c_100pct_60d = TRUE
ORDER BY symbol;
```

### Example 4: Track surveillance status changes over time
```sql
-- Find stocks that entered ESM in the last 30 days
SELECT
    current.symbol,
    current.date AS entered_date,
    current.esm_stage
FROM surveillance_list current
LEFT JOIN surveillance_list previous
    ON current.symbol = previous.symbol
    AND previous.date = current.date - INTERVAL '1 day'
WHERE current.date >= CURRENT_DATE - INTERVAL '30 days'
  AND current.esm_stage IS NOT NULL
  AND previous.esm_stage IS NULL
ORDER BY current.date DESC, current.symbol;
```

---

## Data Ingestion Workflow

### Frequency
**Daily** (after market close, typically around 6:00 PM IST)

### Source URL Pattern
```
https://nsearchives.nseindia.com/surveillance/REG1_IND[DDMMYY].csv
```

**Example:** `REG1_IND160125.csv` for January 16, 2025

### n8n Workflow Integration
Will be added to **Daily EOD Master Workflow** as a new parallel branch:

1. HTTP Request node → Fetch CSV from NSE Archives
2. Parse CSV → Extract all 63 columns
3. HTTP Request → POST to FastAPI endpoint `/api/v1/ingest/surveillance`
4. Aggregation → Log success/failure to `ingestion_logs` table

### Data Validation
- Symbol format validation (alphanumeric + allowed special chars: `&`, `-`)
- Status value check (A/S/I only)
- Stage value range checks (e.g., GSM 0-6, ESM 1-2)
- Date validation (ingestion date >= file date)

---

## Implementation Phases

### Phase 1.4: NSE Surveillance Data Ingestion

**Tasks:**
1. Create 4 database tables with indexes
2. Write Alembic migration
3. Implement CSV parser service (`app/services/nse/surveillance_parser.py`)
4. Create FastAPI endpoint (`/api/v1/ingest/surveillance`)
5. Add n8n workflow node to Daily EOD workflow
6. Write unit tests with sample CSV
7. Document API endpoint in Swagger

**Success Criteria:**
- All 4 tables populated daily with ~2,000 securities
- Historical tracking of surveillance status changes
- Query response time <500ms for single-day queries
- Zero data loss (all 45 stored columns populated correctly)

---

## Notes

### Important Considerations

1. **"Top Three Criteria" Logic (Columns 31-48):**
   NSE Circular NSE/SURV/64402 (Para 4.5) states that only the top 3 criteria trigger the flag. This means a stock might meet multiple thresholds but only be flagged if it's in the top 3 by severity. The CSV already reflects this logic (100 = not in top 3).

2. **Stage Progression:**
   Surveillance stages typically progress (Stage 1 → 2 → 3), but stocks can skip stages or exit surveillance entirely. Historical data is critical for tracking these transitions.

3. **Multiple Surveillance Measures:**
   A single stock can be under multiple measures simultaneously (e.g., ESM Stage 2 + High Pledge + Loss-making).

4. **Data Freshness:**
   NSE updates this file daily after market close. Missing daily ingestion means lost historical tracking of entry/exit points.

5. **No Partitioning (Phase 1):**
   With ~2,000 securities × 4 tables × 365 days = ~3M records/year, PostgreSQL can handle this without partitioning. Monthly partitioning can be added in Phase 2+ if needed.

### Future Enhancements (Phase 2+)

- **Alerting System:** Notify when stock enters/exits specific surveillance measures
- **Historical Analysis:** Track average time spent in each surveillance stage
- **Correlation Analysis:** Link surveillance measures to price performance
- **Screener Integration:** Filter stocks by surveillance criteria (e.g., "avoid ESM stocks")
- **Trend Detection:** Identify sectors with increasing surveillance activity

---

## References

- **NSE Circular:** NSE/SURV/65097 dated November 14, 2024
- **Top 3 Criteria Circular:** NSE/SURV/64402 dated October 04, 2024
- **Sample CSV:** [.claude/samples/REG1_IND160125.csv](.claude/samples/REG1_IND160125.csv)
- **Documentation PDF:** [.claude/samples/2818.pdf](.claude/samples/2818.pdf)
- **NSE Archives URL:** https://nsearchives.nseindia.com/surveillance/

---

**Document Version:** 1.0
**Last Updated:** 2025-01-26
**Author:** System Design (for Phase 1.4 implementation)
