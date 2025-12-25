# Phase 2: Backend Screeners Implementation - Detailed Plan

## Overview

**Objective**: Build all 11 screeners with calculated metrics engine using existing Docker PostgreSQL database.

**Timeline**: 6 weeks (42 days)
**Database**: Existing Docker PostgreSQL (will migrate to Supabase in Phase 4 if needed)

**Strategy**:
1. **Week 1-2**: Build metrics calculation foundation (30+ metrics)
2. **Week 3-4**: Implement 11 screener endpoints (priority order)
3. **Week 5**: Sector/Industry aggregation & RRG calculations
4. **Week 6**: Testing, optimization, documentation

---

# Week 1-2: Calculated Metrics Foundation

## Day 1-3: Database Schema & Migration

### Task 1.1: Update `calculated_metrics` Table Schema

**Current State**: Empty table with only `id`, `security_id`, `date`

**File**: `backend/app/models/timeseries.py`

**Action**: Add all 40+ metric columns

```python
class CalculatedMetrics(Base):
    __tablename__ = "calculated_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    security_id = Column(UUID(as_uuid=True), ForeignKey("securities.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # ===== PRICE CHANGES =====
    # Current vs Previous Close
    change_1d_percent = Column(Numeric(10, 4), comment="1-day % change")
    change_1d_value = Column(Numeric(12, 2), comment="1-day absolute change")

    # Historical Changes
    change_1w_percent = Column(Numeric(10, 4), comment="1-week (5 trading days) % change")
    change_1m_percent = Column(Numeric(10, 4), comment="1-month (21 days) % change")
    change_3m_percent = Column(Numeric(10, 4), comment="3-month (63 days) % change")
    change_6m_percent = Column(Numeric(10, 4), comment="6-month (126 days) % change")

    # ===== RELATIVE STRENGTH =====
    # Percentile rank (0-100) based on 1-month performance
    rs_percentile = Column(Numeric(5, 2), comment="RS percentile rank (0-100)")

    # VARS = RS Percentile / ADR% (higher is better)
    vars_score = Column(Numeric(10, 4), comment="Volatility-Adjusted RS")

    # VARW = (100 - RS Percentile) / ADR% (for laggards)
    varw_score = Column(Numeric(10, 4), comment="Volatility-Adjusted Relative Weakness")

    # ===== VOLATILITY METRICS =====
    # Average True Range
    atr_14 = Column(Numeric(10, 4), comment="14-day ATR")
    atr_percent = Column(Numeric(10, 4), comment="ATR as % of close (ATR/close * 100)")

    # Average Daily Range
    adr_percent = Column(Numeric(10, 4), comment="20-day Average Daily Range %")

    # Daily range today
    today_range_percent = Column(Numeric(10, 4), comment="Today's (high-low)/close %")

    # ===== VOLUME METRICS =====
    # Relative Volume
    volume_50d_avg = Column(BigInteger, comment="50-day average volume")
    rvol = Column(Numeric(10, 4), comment="Relative Volume (today/50d avg)")

    # Volume surge flag
    is_volume_surge = Column(Boolean, comment="RVOL >= 1.5")

    # ===== MOVING AVERAGES =====
    ema_10 = Column(Numeric(10, 4), comment="10-day EMA")
    sma_20 = Column(Numeric(10, 4), comment="20-day SMA")
    sma_50 = Column(Numeric(10, 4), comment="50-day SMA")
    sma_100 = Column(Numeric(10, 4), comment="100-day SMA")
    sma_200 = Column(Numeric(10, 4), comment="200-day SMA")

    # Distance from MAs (as %)
    distance_from_ema10_percent = Column(Numeric(10, 4))
    distance_from_sma50_percent = Column(Numeric(10, 4))
    distance_from_sma200_percent = Column(Numeric(10, 4))

    # MA Alignment (for MA Stacked screener)
    is_ma_stacked = Column(Boolean, comment="close > EMA10 > SMA20 > SMA50 > SMA100 > SMA200")

    # ===== ATR EXTENSION =====
    # How extended price is from SMA50 in ATR units
    atr_extension_from_sma50 = Column(
        Numeric(10, 4),
        comment="((close/SMA50) - 1) / (ATR/close)"
    )

    # Low of Day as ATR %
    lod_atr_percent = Column(
        Numeric(10, 4),
        comment="(low - close) / ATR * 100"
    )

    # ===== DARVAS BOX (20-DAY HIGH/LOW) =====
    darvas_box_20d_high = Column(Numeric(10, 4), comment="20-day high")
    darvas_box_20d_low = Column(Numeric(10, 4), comment="20-day low")
    darvas_box_range_percent = Column(
        Numeric(10, 4),
        comment="(20d_high - 20d_low) / close * 100"
    )

    # ===== NEW HIGHS/LOWS =====
    is_new_20d_high = Column(Boolean, comment="Today's high == 20-day high")
    is_new_20d_low = Column(Boolean, comment="Today's low == 20-day low")
    is_new_52w_high = Column(Boolean, comment="52-week high")
    is_new_52w_low = Column(Boolean, comment="52-week low")

    # ===== PATTERN RECOGNITION =====
    # VCP Score (1-5 based on narrowing high-low ranges)
    vcp_score = Column(Integer, comment="Volatility Contraction Pattern score (1-5)")

    # Stage Classification (1-4)
    stage = Column(Integer, comment="1=Basing, 2=Uptrend, 3=Topping, 4=Downtrend")

    # Candle Type
    candle_type = Column(String(10), comment="'green' if close >= open, else 'red'")
    candle_body_percent = Column(Numeric(10, 4), comment="(close-open)/open * 100")

    # ===== SECTOR/INDUSTRY STRENGTH =====
    # Populated by separate sector calculation job
    sector_strength = Column(Numeric(10, 4), comment="Sector avg % change vs market")
    industry_strength = Column(Numeric(10, 4), comment="Industry avg % change vs market")

    # Sector/Industry from industry_classification table (denormalized for speed)
    sector = Column(String(100))
    industry = Column(String(100))
    basic_industry = Column(String(100))

    # ===== RRG METRICS (FOR SECTOR INDICES) =====
    # Only populated for sector index constituents
    rs_ratio = Column(Numeric(10, 4), comment="Relative Strength Ratio vs benchmark")
    rs_momentum = Column(Numeric(10, 4), comment="Rate of change of RS-Ratio")

    # ===== BREADTH INDICATORS (MARKET-WIDE) =====
    # Populated once per day for market-level metrics
    pct_above_sma20 = Column(Numeric(5, 2), comment="% of stocks above SMA20")
    pct_above_sma50 = Column(Numeric(5, 2), comment="% of stocks above SMA50")
    pct_above_sma200 = Column(Numeric(5, 2), comment="% of stocks above SMA200")

    advance_decline_ratio = Column(Numeric(10, 4), comment="Advancing / Declining stocks")
    mcclellan_oscillator = Column(Numeric(10, 4), comment="McClellan Oscillator")
    mcclellan_summation = Column(Numeric(10, 4), comment="McClellan Summation Index")

    # ===== METADATA =====
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_calculated_metrics_security_date'),
        Index('ix_calculated_metrics_security_date_desc', 'security_id', desc('date')),
        Index('ix_calculated_metrics_date', 'date'),
        Index('ix_calculated_metrics_rs_percentile', 'rs_percentile'),
        Index('ix_calculated_metrics_vars_score', 'vars_score'),
        Index('ix_calculated_metrics_stage', 'stage'),
        Index('ix_calculated_metrics_sector', 'sector'),
    )
```

**Create Migration**:
```bash
cd backend
alembic revision --autogenerate -m "Add 40+ calculated metrics columns"
alembic upgrade head
```

**Verification**:
```bash
docker exec -it screener_postgres psql -U screener_user -d screener_db

\d calculated_metrics
# Should show all 40+ columns
```

---

## Day 4-10: Metrics Calculator Service

### Task 1.2: Core Metrics Calculator

**File**: `backend/app/services/calculators/metrics_calculator.py` (NEW)

Create comprehensive calculator with these methods:

#### Method Structure

```python
class DailyMetricsCalculator:
    def __init__(self, db: Session):
        self.db = db

    # ==== MAIN ENTRY POINT ====
    def calculate_for_date(self, target_date: date) -> Dict:
        """Calculate ALL metrics for ALL securities for a date."""
        pass

    # ==== INDIVIDUAL SECURITY CALCULATIONS ====
    def _calculate_security_metrics(self, security_id: str, target_date: date) -> Dict:
        """Calculate all metrics for ONE security."""
        pass

    # ==== PRICE CHANGE CALCULATIONS ====
    def _calc_price_changes(self, df: pd.DataFrame, target_date: date) -> Dict:
        """Calculate 1d, 1w, 1m, 3m, 6m % changes."""
        pass

    # ==== VOLATILITY CALCULATIONS ====
    def _calc_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        pass

    def _calc_adr(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Average Daily Range %."""
        pass

    # ==== MOVING AVERAGE CALCULATIONS ====
    def _calc_moving_averages(self, df: pd.DataFrame, target_date: date) -> Dict:
        """Calculate EMA10, SMA20/50/100/200 and distances."""
        pass

    def _check_ma_stacked(self, close, ema10, sma20, sma50, sma100, sma200) -> bool:
        """Check if MAs are perfectly aligned."""
        pass

    # ==== PATTERN RECOGNITION ====
    def _calc_vcp_score(self, df: pd.DataFrame, target_date: date) -> int:
        """Calculate Volatility Contraction Pattern score (1-5)."""
        pass

    def _calc_stage(self, close, sma50, sma200) -> int:
        """Classify stock into stage 1-4."""
        pass

    # ==== RELATIVE STRENGTH (BATCH OPERATION) ====
    def _calculate_rs_percentiles(self, target_date: date):
        """Calculate RS percentile ranks across ALL securities."""
        pass

    def _calculate_vars_scores(self, target_date: date):
        """Calculate VARS and VARW scores after RS percentiles."""
        pass

    # ==== SECTOR STRENGTH (BATCH OPERATION) ====
    def _calculate_sector_strength(self, target_date: date):
        """Calculate sector-level strength metrics."""
        pass

    # ==== BREADTH INDICATORS (MARKET-WIDE) ====
    def _calculate_breadth_metrics(self, target_date: date):
        """Calculate market-wide breadth indicators."""
        pass

    # ==== PERSISTENCE ====
    def _save_metrics(self, security_id: str, target_date: date, metrics: Dict):
        """Save or update calculated metrics."""
        pass
```

---

### Detailed Implementation: Each Calculation Method

#### 1. Price Changes

```python
def _calc_price_changes(self, df: pd.DataFrame, target_date: date) -> Dict:
    """
    Calculate % changes over multiple periods.

    Formula: ((current_close - prev_close) / prev_close) * 100

    Periods:
    - 1d: 1 trading day
    - 1w: 5 trading days
    - 1m: 21 trading days
    - 3m: 63 trading days
    - 6m: 126 trading days
    """
    if target_date not in df.index:
        return {}

    dates = df.index.tolist()
    target_idx = dates.index(target_date)
    current_close = df.loc[target_date, 'close']

    changes = {}
    periods = {
        'change_1d_percent': 1,
        'change_1w_percent': 5,
        'change_1m_percent': 21,
        'change_3m_percent': 63,
        'change_6m_percent': 126
    }

    for key, days in periods.items():
        if target_idx >= days:
            prev_date = dates[target_idx - days]
            prev_close = df.loc[prev_date, 'close']
            changes[key] = ((current_close - prev_close) / prev_close) * 100
        else:
            changes[key] = None

    # Absolute change (1-day only)
    if target_idx >= 1:
        prev_close_1d = df.loc[dates[target_idx - 1], 'close']
        changes['change_1d_value'] = current_close - prev_close_1d
    else:
        changes['change_1d_value'] = None

    return changes
```

---

#### 2. Average True Range (ATR)

```python
def _calc_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    True Range = max of:
    - high - low
    - |high - prev_close|
    - |low - prev_close|

    ATR = 14-day moving average of True Range
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=period).mean()

    return atr
```

---

#### 3. Moving Averages & Alignment

```python
def _calc_moving_averages(self, df: pd.DataFrame, target_date: date) -> Dict:
    """Calculate all MAs and distance from MAs."""
    if target_date not in df.index:
        return {}

    close = df.loc[target_date, 'close']

    # Calculate MAs
    ema_10 = df['close'].ewm(span=10, adjust=False).mean().loc[target_date] if len(df) >= 10 else None
    sma_20 = df['close'].rolling(20).mean().loc[target_date] if len(df) >= 20 else None
    sma_50 = df['close'].rolling(50).mean().loc[target_date] if len(df) >= 50 else None
    sma_100 = df['close'].rolling(100).mean().loc[target_date] if len(df) >= 100 else None
    sma_200 = df['close'].rolling(200).mean().loc[target_date] if len(df) >= 200 else None

    # Distance from MAs (%)
    distance_ema10 = ((close - ema_10) / ema_10 * 100) if ema_10 else None
    distance_sma50 = ((close - sma_50) / sma_50 * 100) if sma_50 else None
    distance_sma200 = ((close - sma_200) / sma_200 * 100) if sma_200 else None

    # MA Stacked Check
    is_stacked = self._check_ma_stacked(close, ema_10, sma_20, sma_50, sma_100, sma_200)

    return {
        'ema_10': ema_10,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'sma_100': sma_100,
        'sma_200': sma_200,
        'distance_from_ema10_percent': distance_ema10,
        'distance_from_sma50_percent': distance_sma50,
        'distance_from_sma200_percent': distance_sma200,
        'is_ma_stacked': is_stacked
    }

def _check_ma_stacked(self, close, ema10, sma20, sma50, sma100, sma200) -> bool:
    """Check perfect MA alignment: close > EMA10 > SMA20 > SMA50 > SMA100 > SMA200"""
    if any(ma is None for ma in [ema10, sma20, sma50, sma100, sma200]):
        return False

    return (
        close > ema10 > sma20 > sma50 > sma100 > sma200
    )
```

---

#### 4. VCP Score (Volatility Contraction Pattern)

```python
def _calc_vcp_score(self, df: pd.DataFrame, target_date: date) -> Optional[int]:
    """
    Calculate VCP score (1-5).

    Logic:
    - Look at last 5 bars
    - Calculate (high - low) / close % for each
    - Count how many consecutive bars have narrowing ranges
    - Score = number of narrowing bars (1-5)

    Example:
    Bar 1: 3.5% range
    Bar 2: 3.0% range (narrowing)
    Bar 3: 2.5% range (narrowing)
    Bar 4: 2.0% range (narrowing)
    Bar 5: 1.8% range (narrowing)
    VCP Score = 4 (4 consecutive narrowing bars)
    """
    try:
        # Get last 5 bars including target_date
        recent_df = df.loc[:target_date].tail(5)

        if len(recent_df) < 5:
            return None

        # Calculate range %
        recent_df = recent_df.copy()
        recent_df['range_pct'] = ((recent_df['high'] - recent_df['low']) / recent_df['close']) * 100

        ranges = recent_df['range_pct'].values

        # Count narrowing bars
        narrowing_count = 0
        for i in range(1, len(ranges)):
            if ranges[i] < ranges[i-1]:
                narrowing_count += 1

        # Score 1-5
        return max(1, narrowing_count)
    except:
        return None
```

---

#### 5. Stage Classification

```python
def _calc_stage(self, close: float, sma_50: Optional[float], sma_200: Optional[float]) -> Optional[int]:
    """
    Mark Minervini's Stage Analysis (4 stages).

    Stage 1 (Basing): Price below both MAs, 50 SMA below 200 SMA
    Stage 2 (Uptrend): Price above both MAs, 50 SMA above 200 SMA
    Stage 3 (Topping): Price above 200 but below 50, or 50 crossing below 200
    Stage 4 (Downtrend): Price below both MAs, 50 SMA below 200 SMA

    Simplified Logic:
    - Stage 2: close > SMA50 > SMA200 (strongest)
    - Stage 3: close > SMA200 but close < SMA50 (weakening)
    - Stage 4: close < SMA200 < SMA50 (weakest)
    - Stage 1: Everything else (consolidation)
    """
    if sma_50 is None or sma_200 is None:
        return None

    above_50 = close > sma_50
    above_200 = close > sma_200
    ma_50_above_200 = sma_50 > sma_200

    if above_50 and above_200 and ma_50_above_200:
        return 2  # Uptrend
    elif above_200 and not above_50:
        return 3  # Topping
    elif not above_200 and not above_50 and not ma_50_above_200:
        return 4  # Downtrend
    else:
        return 1  # Basing
```

---

#### 6. Relative Strength Percentiles (Batch Operation)

```python
def _calculate_rs_percentiles(self, target_date: date):
    """
    Calculate RS percentile ranks across ALL securities.

    Logic:
    1. Get all securities with metrics for target_date
    2. Sort by change_1m_percent
    3. Assign percentile rank (0-100)
    4. Update rs_percentile column

    Example:
    - 2000 securities
    - Security ranked 1940th (best performer) = 97th percentile
    - Security ranked 1000th (middle) = 50th percentile
    - Security ranked 60th (worst) = 3rd percentile
    """
    # Get all metrics for this date
    metrics = self.db.query(CalculatedMetrics).filter(
        CalculatedMetrics.date == target_date
    ).all()

    if not metrics:
        return

    # Extract (security_id, change_1m_percent) pairs
    changes = [
        (m.security_id, float(m.change_1m_percent) if m.change_1m_percent else 0)
        for m in metrics
    ]

    # Sort by change (ascending)
    changes_sorted = sorted(changes, key=lambda x: x[1])

    total = len(changes_sorted)

    # Create percentile map
    percentile_map = {}
    for rank, (sec_id, change) in enumerate(changes_sorted, start=1):
        percentile = (rank / total) * 100
        percentile_map[sec_id] = round(percentile, 2)

    # Update metrics
    for metric in metrics:
        metric.rs_percentile = percentile_map.get(metric.security_id)

    self.db.commit()
```

---

#### 7. VARS and VARW Scores

```python
def _calculate_vars_scores(self, target_date: date):
    """
    Calculate VARS and VARW after RS percentiles.

    VARS = RS Percentile / ADR%
    - Higher VARS = Strong performance with low volatility
    - Best for finding stable leaders

    VARW = (100 - RS Percentile) / ADR%
    - Higher VARW = Weak performance with low volatility
    - Used to find laggards for potential rotation
    """
    metrics = self.db.query(CalculatedMetrics).filter(
        CalculatedMetrics.date == target_date
    ).all()

    for metric in metrics:
        if metric.rs_percentile is not None and metric.adr_percent and metric.adr_percent > 0:
            # VARS
            metric.vars_score = metric.rs_percentile / metric.adr_percent

            # VARW
            metric.varw_score = (100 - metric.rs_percentile) / metric.adr_percent
        else:
            metric.vars_score = None
            metric.varw_score = None

    self.db.commit()
```

---

#### 8. Sector Strength Calculations

```python
def _calculate_sector_strength(self, target_date: date):
    """
    Calculate sector-level strength metrics.

    Logic:
    1. Group all securities by sector
    2. Calculate sector average % change
    3. Compare to market average
    4. Store sector_strength = sector_avg - market_avg

    Also denormalize sector/industry to calculated_metrics for faster queries.
    """
    from app.models.metadata import IndustryClassification

    # Get market average
    market_avg = self.db.query(
        func.avg(CalculatedMetrics.change_1m_percent)
    ).filter(
        CalculatedMetrics.date == target_date
    ).scalar() or 0

    # Get distinct sectors
    sectors = self.db.query(IndustryClassification.sector).distinct().all()

    sector_strength_map = {}

    for (sector,) in sectors:
        if not sector:
            continue

        # Get all securities in this sector
        sector_securities = self.db.query(Security.id).join(
            IndustryClassification,
            Security.id == IndustryClassification.security_id
        ).filter(
            IndustryClassification.sector == sector
        ).all()

        sector_ids = [s.id for s in sector_securities]

        # Calculate sector average
        sector_avg = self.db.query(
            func.avg(CalculatedMetrics.change_1m_percent)
        ).filter(
            and_(
                CalculatedMetrics.security_id.in_(sector_ids),
                CalculatedMetrics.date == target_date
            )
        ).scalar() or 0

        sector_strength = sector_avg - market_avg
        sector_strength_map[sector] = sector_strength

    # Update metrics with sector strength
    metrics = self.db.query(CalculatedMetrics).filter(
        CalculatedMetrics.date == target_date
    ).all()

    for metric in metrics:
        # Get sector from industry_classification
        industry_rec = self.db.query(IndustryClassification).filter(
            IndustryClassification.security_id == metric.security_id
        ).first()

        if industry_rec:
            metric.sector = industry_rec.sector
            metric.industry = industry_rec.industry
            metric.basic_industry = industry_rec.basic_industry
            metric.sector_strength = sector_strength_map.get(industry_rec.sector)

    self.db.commit()
```

---

#### 9. Breadth Indicators (Market-Wide)

```python
def _calculate_breadth_metrics(self, target_date: date):
    """
    Calculate market-wide breadth indicators.

    Metrics:
    - % of stocks above SMA20/50/200
    - Advance/Decline ratio
    - McClellan Oscillator
    - McClellan Summation Index

    Note: These are market-level metrics, stored in FIRST row
    (or create separate market_breadth table in future)
    """
    # Get all metrics for this date
    all_metrics = self.db.query(CalculatedMetrics).filter(
        CalculatedMetrics.date == target_date
    ).all()

    total = len(all_metrics)
    if total == 0:
        return

    # % above MAs
    above_sma20 = sum(1 for m in all_metrics if m.distance_from_ema10_percent and m.distance_from_ema10_percent > -10)  # Approx SMA20
    above_sma50 = sum(1 for m in all_metrics if m.distance_from_sma50_percent and m.distance_from_sma50_percent > 0)
    above_sma200 = sum(1 for m in all_metrics if m.distance_from_sma200_percent and m.distance_from_sma200_percent > 0)

    pct_above_sma20 = (above_sma20 / total) * 100
    pct_above_sma50 = (above_sma50 / total) * 100
    pct_above_sma200 = (above_sma200 / total) * 100

    # Advance/Decline
    advancing = sum(1 for m in all_metrics if m.change_1d_percent and m.change_1d_percent > 0)
    declining = sum(1 for m in all_metrics if m.change_1d_percent and m.change_1d_percent < 0)

    ad_ratio = advancing / declining if declining > 0 else 0

    # McClellan Oscillator (simplified - needs historical data)
    # TODO: Implement with historical advance/decline data

    # Store in first metric row (or create market_breadth table)
    if all_metrics:
        first_metric = all_metrics[0]
        first_metric.pct_above_sma20 = pct_above_sma20
        first_metric.pct_above_sma50 = pct_above_sma50
        first_metric.pct_above_sma200 = pct_above_sma200
        first_metric.advance_decline_ratio = ad_ratio

    self.db.commit()
```

---

## Day 11-14: API Endpoint for Metrics Calculation

**File**: `backend/app/api/v1/metrics.py` (NEW)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.database.session import get_db
from app.services.calculators.metrics_calculator import DailyMetricsCalculator
from app.core.resource_monitor import monitor_resources

router = APIRouter()


@router.post("/calculate-daily")
@monitor_resources
async def calculate_daily_metrics(
    target_date: Optional[str] = Query(None, description="Date (YYYY-MM-DD). Default: yesterday"),
    db: Session = Depends(get_db)
):
    """
    Calculate all 40+ metrics for all securities.

    Execution order:
    1. Individual security metrics (prices, MAs, ATR, etc.)
    2. RS percentiles (batch, needs all securities)
    3. VARS/VARW scores (depends on RS percentiles)
    4. Sector strength (batch)
    5. Breadth indicators (market-wide)

    Called by n8n workflow daily at 9:00 PM IST.
    """
    # Parse date
    if target_date:
        try:
            calc_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, detail="Invalid date format")
    else:
        calc_date = (datetime.now() - timedelta(days=1)).date()

    # Initialize calculator
    calculator = DailyMetricsCalculator(db)

    # Step 1: Calculate individual security metrics
    results = calculator.calculate_for_date(calc_date)

    # Step 2: Calculate RS percentiles (batch)
    calculator._calculate_rs_percentiles(calc_date)

    # Step 3: Calculate VARS/VARW scores
    calculator._calculate_vars_scores(calc_date)

    # Step 4: Calculate sector strength
    calculator._calculate_sector_strength(calc_date)

    # Step 5: Calculate breadth indicators
    calculator._calculate_breadth_metrics(calc_date)

    return {
        "success": True,
        "date": calc_date.isoformat(),
        "securities_processed": results["securities_processed"],
        "metrics_calculated": results["metrics_calculated"],
        "errors": results["errors"]
    }


@router.get("/latest/{symbol}")
async def get_latest_metrics(symbol: str, db: Session = Depends(get_db)):
    """Get latest calculated metrics for a symbol."""
    from app.models.security import Security
    from app.models.timeseries import CalculatedMetrics
    from sqlalchemy import desc

    security = db.query(Security).filter(Security.symbol == symbol).first()
    if not security:
        raise HTTPException(404, detail=f"Symbol {symbol} not found")

    metrics = db.query(CalculatedMetrics).filter(
        CalculatedMetrics.security_id == security.id
    ).order_by(desc(CalculatedMetrics.date)).first()

    if not metrics:
        raise HTTPException(404, detail=f"No metrics for {symbol}")

    return {
        "symbol": symbol,
        "date": metrics.date.isoformat(),
        "metrics": {
            "change_1d_percent": float(metrics.change_1d_percent) if metrics.change_1d_percent else None,
            "change_1w_percent": float(metrics.change_1w_percent) if metrics.change_1w_percent else None,
            "change_1m_percent": float(metrics.change_1m_percent) if metrics.change_1m_percent else None,
            "rs_percentile": float(metrics.rs_percentile) if metrics.rs_percentile else None,
            "vars_score": float(metrics.vars_score) if metrics.vars_score else None,
            "atr_percent": float(metrics.atr_percent) if metrics.atr_percent else None,
            "rvol": float(metrics.rvol) if metrics.rvol else None,
            "stage": metrics.stage,
            "vcp_score": metrics.vcp_score,
            # ... include all 40+ metrics
        }
    }
```

**Register in** `backend/main.py`:
```python
from app.api.v1 import metrics

app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics Calculation"])
```

---

## Day 15-18: n8n Daily Metrics Workflow

**File**: `n8n/workflows/daily_metrics_calculation.json`

**Workflow Steps**:
1. **Schedule Trigger**: Mon-Fri, 9:00 PM IST (after OHLCV ingestion)
2. **HTTP Request**: POST to `http://backend:8000/api/v1/metrics/calculate-daily`
3. **Conditional Check**: If `success == true`
4. **Log Success**: Insert to `ingestion_logs` table
5. **Error Handler**: If failed, log error with details

**Export from n8n UI** and commit to repo.

---

## Testing Week 1-2

**Manual Testing**:
```bash
# 1. Run migration
cd backend
alembic upgrade head

# 2. Test metrics calculation for yesterday
curl -X POST "http://localhost:8000/api/v1/metrics/calculate-daily"

# 3. Check results
docker exec -it screener_postgres psql -U screener_user -d screener_db

SELECT COUNT(*) FROM calculated_metrics WHERE date = CURRENT_DATE - INTERVAL '1 day';
-- Should return ~2000 (number of active securities)

# 4. Verify metrics for RELIANCE
SELECT
    date,
    change_1d_percent,
    change_1m_percent,
    rs_percentile,
    vars_score,
    stage,
    vcp_score
FROM calculated_metrics cm
JOIN securities s ON cm.security_id = s.id
WHERE s.symbol = 'RELIANCE'
ORDER BY date DESC
LIMIT 5;
```

**Automated Testing**:
```python
# backend/tests/test_metrics_calculator.py
import pytest
from app.services.calculators.metrics_calculator import DailyMetricsCalculator

def test_price_changes():
    # Test 1-day, 1-week, 1-month calculations
    pass

def test_atr_calculation():
    # Test ATR with known dataset
    pass

def test_vcp_score():
    # Test VCP scoring logic
    pass

def test_stage_classification():
    # Test stage 1-4 classification
    pass
```

---

# Week 3-4: 11 Screener Endpoints (Priority Order)

## Screener Implementation Order

**Priority 1 (Week 3)**: Most requested screeners
1. RRG Charts (Sector Rotation)
2. 4% Breakouts
3. RS Leaders (97 Club)
4. Breadth Metrics Dashboard
5. Weekly Movers (20%)

**Priority 2 (Week 4)**: Pattern/Technical screeners
6. MA Stacked Breakouts
7. High Volume Movers
8. ATR Extension Matrix
9. Stage Analysis Breakdown
10. Momentum Watchlist
11. Leading Industries/Groups

---

## Screener 1: RRG Charts (Relative Rotation Graphs)

**File**: `backend/app/api/v1/screeners.py` (NEW)

**Endpoint**: `POST /api/v1/screeners/rrg`

**Purpose**: Visualize sector rotation using RS-Ratio (X-axis) and RS-Momentum (Y-axis).

**Quadrants**:
- **Leading** (top-right): High RS-Ratio, positive momentum
- **Improving** (top-left): Low RS-Ratio, positive momentum
- **Lagging** (bottom-left): Low RS-Ratio, negative momentum
- **Weakening** (bottom-right): High RS-Ratio, negative momentum

**Implementation**:

```python
@router.post("/rrg")
async def rrg_screener(
    benchmark: str = Query("NIFTY 50", description="Benchmark index"),
    weeks: int = Query(100, description="Weeks of tail history"),
    db: Session = Depends(get_db)
):
    """
    RRG Screener - Sector Rotation Analysis.

    Returns:
    - Sector name
    - RS-Ratio (relative to benchmark)
    - RS-Momentum (rate of change of RS-Ratio)
    - ADR% (for color coding volatility)
    - Historical tail (last 100 weeks of RS-Ratio/Momentum)
    """
    from app.models.metadata import IndustryClassification
    from sqlalchemy import func, and_

    # Get latest date
    latest_date = db.query(func.max(CalculatedMetrics.date)).scalar()
    if not latest_date:
        return {"error": "No data"}

    # Get all sectors
    sectors = db.query(IndustryClassification.sector).distinct().all()

    # Calculate market average (benchmark)
    market_avg = db.query(
        func.avg(CalculatedMetrics.change_1m_percent)
    ).filter(
        CalculatedMetrics.date == latest_date
    ).scalar() or 0

    results = []

    for (sector,) in sectors:
        if not sector:
            continue

        # Get all securities in sector
        sector_securities = db.query(Security.id).join(
            IndustryClassification,
            Security.id == IndustryClassification.security_id
        ).filter(
            IndustryClassification.sector == sector
        ).all()

        sector_ids = [s.id for s in sector_securities]
        if not sector_ids:
            continue

        # Calculate sector average metrics
        sector_metrics = db.query(
            func.avg(CalculatedMetrics.change_1m_percent).label('avg_change'),
            func.avg(CalculatedMetrics.adr_percent).label('avg_adr')
        ).filter(
            and_(
                CalculatedMetrics.security_id.in_(sector_ids),
                CalculatedMetrics.date == latest_date
            )
        ).first()

        if not sector_metrics.avg_change:
            continue

        # RS-Ratio = 100 + (sector_avg - market_avg)
        rs_ratio = 100 + (sector_metrics.avg_change - market_avg)

        # RS-Momentum: Get previous week's RS-Ratio
        prev_week_date = latest_date - timedelta(days=7)

        prev_sector_avg = db.query(
            func.avg(CalculatedMetrics.change_1m_percent)
        ).filter(
            and_(
                CalculatedMetrics.security_id.in_(sector_ids),
                CalculatedMetrics.date == prev_week_date
            )
        ).scalar()

        prev_market_avg = db.query(
            func.avg(CalculatedMetrics.change_1m_percent)
        ).filter(
            CalculatedMetrics.date == prev_week_date
        ).scalar()

        if prev_sector_avg and prev_market_avg:
            prev_rs_ratio = 100 + (prev_sector_avg - prev_market_avg)
            rs_momentum = 100 + (rs_ratio - prev_rs_ratio)
        else:
            rs_momentum = 100

        # Get historical tail (last 100 weeks)
        # TODO: Implement tail data retrieval

        results.append({
            "name": sector,
            "rs_ratio": round(rs_ratio, 2),
            "rs_momentum": round(rs_momentum, 2),
            "adr_percent": round(sector_metrics.avg_adr, 2) if sector_metrics.avg_adr else 0,
            "tail": []  # Historical data points
        })

    return {
        "date": latest_date.isoformat(),
        "benchmark": benchmark,
        "sectors": results
    }
```

**Test**:
```bash
curl -X POST "http://localhost:8000/api/v1/screeners/rrg"
```

---

## Screener 2: 4% Breakouts

**Endpoint**: `POST /api/v1/screeners/breakouts-4percent`

**Purpose**: Find stocks with ≥4% daily gain and volume surge.

**Filters**:
- `min_change`: Default 4.0%
- `min_rvol`: Default 1.5x
- `min_market_cap`: Optional (in crores)

```python
@router.post("/breakouts-4percent")
async def breakouts_4percent(
    min_change: float = Query(4.0, description="Min % change"),
    min_rvol: float = Query(1.5, description="Min RVOL"),
    min_market_cap: Optional[float] = Query(None, description="Min market cap (Cr)"),
    db: Session = Depends(get_db)
):
    """
    4% Breakouts Screener.

    Returns stocks with:
    - change_1d_percent >= min_change
    - rvol >= min_rvol
    - Optional: market cap filter
    """
    from app.models.timeseries import MarketCapHistory

    latest_date = db.query(func.max(CalculatedMetrics.date)).scalar()

    query = db.query(
        Security.symbol,
        Security.name,
        CalculatedMetrics.change_1d_percent,
        CalculatedMetrics.rvol,
        MarketCapHistory.market_cap
    ).join(
        CalculatedMetrics,
        Security.id == CalculatedMetrics.security_id
    ).outerjoin(
        MarketCapHistory,
        and_(
            Security.id == MarketCapHistory.security_id,
            MarketCapHistory.date == latest_date
        )
    ).filter(
        and_(
            CalculatedMetrics.date == latest_date,
            CalculatedMetrics.change_1d_percent >= min_change,
            CalculatedMetrics.rvol >= min_rvol,
            Security.is_active == True
        )
    )

    if min_market_cap:
        query = query.filter(MarketCapHistory.market_cap >= min_market_cap * 10000000)  # Convert Cr to rupees

    results = query.order_by(desc(CalculatedMetrics.change_1d_percent)).limit(100).all()

    return {
        "date": latest_date.isoformat(),
        "filters": {"min_change": min_change, "min_rvol": min_rvol, "min_market_cap": min_market_cap},
        "total": len(results),
        "data": [
            {
                "symbol": r.symbol,
                "name": r.name,
                "change_percent": round(float(r.change_1d_percent), 2),
                "rvol": round(float(r.rvol), 2) if r.rvol else None,
                "market_cap_cr": round(float(r.market_cap) / 10000000, 2) if r.market_cap else None
            }
            for r in results
        ]
    }
```

---

## Screener 3: RS Leaders (97 Club)

**Endpoint**: `POST /api/v1/screeners/rs-leaders`

**Purpose**: Find top 3% performers (RS percentile ≥ 97).

```python
@router.post("/rs-leaders")
async def rs_leaders(
    min_rs_percentile: float = Query(97.0, description="Min RS percentile"),
    min_vars: Optional[float] = Query(None, description="Min VARS score"),
    db: Session = Depends(get_db)
):
    """
    RS Leaders (97 Club) Screener.

    Returns stocks in top 3% (RS percentile ≥ 97).
    """
    latest_date = db.query(func.max(CalculatedMetrics.date)).scalar()

    query = db.query(
        Security.symbol,
        Security.name,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.vars_score,
        CalculatedMetrics.change_1m_percent,
        CalculatedMetrics.stage
    ).join(
        CalculatedMetrics,
        Security.id == CalculatedMetrics.security_id
    ).filter(
        and_(
            CalculatedMetrics.date == latest_date,
            CalculatedMetrics.rs_percentile >= min_rs_percentile,
            Security.is_active == True
        )
    )

    if min_vars:
        query = query.filter(CalculatedMetrics.vars_score >= min_vars)

    results = query.order_by(desc(CalculatedMetrics.rs_percentile)).limit(100).all()

    return {
        "date": latest_date.isoformat(),
        "filters": {"min_rs_percentile": min_rs_percentile, "min_vars": min_vars},
        "total": len(results),
        "data": [
            {
                "symbol": r.symbol,
                "name": r.name,
                "rs_percentile": round(float(r.rs_percentile), 2) if r.rs_percentile else None,
                "vars_score": round(float(r.vars_score), 2) if r.vars_score else None,
                "change_1m_percent": round(float(r.change_1m_percent), 2) if r.change_1m_percent else None,
                "stage": r.stage
            }
            for r in results
        ]
    }
```

---

## Screener 4: Breadth Metrics Dashboard

**Endpoint**: `GET /api/v1/screeners/breadth-metrics`

**Purpose**: Market-wide health indicators.

```python
@router.get("/breadth-metrics")
async def breadth_metrics(db: Session = Depends(get_db)):
    """
    Breadth Metrics Dashboard.

    Returns:
    - % above SMA20/50/200
    - Advance/Decline ratio
    - McClellan Oscillator
    - Stage distribution
    """
    latest_date = db.query(func.max(CalculatedMetrics.date)).scalar()

    # Get first metric (contains breadth data)
    breadth = db.query(CalculatedMetrics).filter(
        CalculatedMetrics.date == latest_date
    ).first()

    # Stage distribution
    stage_dist = db.query(
        CalculatedMetrics.stage,
        func.count(CalculatedMetrics.id).label('count')
    ).filter(
        CalculatedMetrics.date == latest_date
    ).group_by(CalculatedMetrics.stage).all()

    return {
        "date": latest_date.isoformat(),
        "breadth": {
            "pct_above_sma20": round(float(breadth.pct_above_sma20), 2) if breadth and breadth.pct_above_sma20 else None,
            "pct_above_sma50": round(float(breadth.pct_above_sma50), 2) if breadth and breadth.pct_above_sma50 else None,
            "pct_above_sma200": round(float(breadth.pct_above_sma200), 2) if breadth and breadth.pct_above_sma200 else None,
            "advance_decline_ratio": round(float(breadth.advance_decline_ratio), 2) if breadth and breadth.advance_decline_ratio else None
        },
        "stage_distribution": [
            {"stage": s.stage, "count": s.count}
            for s in stage_dist
        ]
    }
```

---

## Screener 5: Weekly Movers (20%)

**Endpoint**: `POST /api/v1/screeners/weekly-movers`

**Purpose**: Stocks with ≥20% weekly move (up or down).

```python
@router.post("/weekly-movers")
async def weekly_movers(
    min_change: float = Query(20.0, description="Min abs % change"),
    db: Session = Depends(get_db)
):
    """
    Weekly Movers (≥20% change).

    Returns separate lists for gainers (+20%) and losers (-20%).
    """
    latest_date = db.query(func.max(CalculatedMetrics.date)).scalar()

    # Gainers
    gainers = db.query(
        Security.symbol,
        Security.name,
        CalculatedMetrics.change_1w_percent
    ).join(
        CalculatedMetrics,
        Security.id == CalculatedMetrics.security_id
    ).filter(
        and_(
            CalculatedMetrics.date == latest_date,
            CalculatedMetrics.change_1w_percent >= min_change,
            Security.is_active == True
        )
    ).order_by(desc(CalculatedMetrics.change_1w_percent)).limit(50).all()

    # Losers
    losers = db.query(
        Security.symbol,
        Security.name,
        CalculatedMetrics.change_1w_percent
    ).join(
        CalculatedMetrics,
        Security.id == CalculatedMetrics.security_id
    ).filter(
        and_(
            CalculatedMetrics.date == latest_date,
            CalculatedMetrics.change_1w_percent <= -min_change,
            Security.is_active == True
        )
    ).order_by(CalculatedMetrics.change_1w_percent).limit(50).all()

    return {
        "date": latest_date.isoformat(),
        "filters": {"min_change": min_change},
        "gainers": [
            {"symbol": r.symbol, "name": r.name, "change_percent": round(float(r.change_1w_percent), 2)}
            for r in gainers
        ],
        "losers": [
            {"symbol": r.symbol, "name": r.name, "change_percent": round(float(r.change_1w_percent), 2)}
            for r in losers
        ]
    }
```

---

## Screeners 6-11 (Week 4)

Implement remaining screeners following same pattern:

### 6. MA Stacked Breakouts
Filter: `is_ma_stacked == True` + `change_1d_percent >= 2%`

### 7. High Volume Movers
Filter: `rvol >= 2.0` + `change_1d_percent >= 2%`

### 8. ATR Extension Matrix
Return heatmap data: `sector` x `atr_extension_from_sma50`

### 9. Stage Analysis Breakdown
Group by `stage`, show count and avg metrics per stage

### 10. Momentum Watchlist
Filter: `rs_percentile >= 90` + `stage == 2` + `is_ma_stacked == True`

### 11. Leading Industries
Group by `industry`, calculate avg `change_1m_percent`, top 20%

---

# Week 5: Sector Aggregation & RRG Tail Data

## Task: Historical RRG Tail Calculation

**Purpose**: Calculate RS-Ratio and RS-Momentum for last 100 weeks for each sector.

**Approach**:
1. Create `sector_rrg_history` table to store weekly sector metrics
2. Backfill 100 weeks of data
3. Update daily with latest week's data

**Table Schema**:
```python
class SectorRRGHistory(Base):
    __tablename__ = "sector_rrg_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sector = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    rs_ratio = Column(Numeric(10, 4))
    rs_momentum = Column(Numeric(10, 4))

    __table_args__ = (
        UniqueConstraint('sector', 'date'),
    )
```

**Backfill Script**:
```python
# backend/scripts/backfill_rrg_history.py
def backfill_rrg_data(weeks=100):
    for week in range(weeks):
        target_date = datetime.now().date() - timedelta(weeks=week)
        # Calculate RS-Ratio and RS-Momentum for each sector
        # Store in sector_rrg_history
```

---

# Week 6: Testing, Optimization & Documentation

## Performance Testing

**Metrics**:
- Daily calculation time: Target <5 minutes for 2000 securities
- Screener query time: Target <2 seconds for 100 results
- Database size: Monitor growth rate

**Optimization**:
```sql
-- Add composite indexes for screener queries
CREATE INDEX idx_calc_metrics_date_rs ON calculated_metrics(date, rs_percentile DESC);
CREATE INDEX idx_calc_metrics_date_vars ON calculated_metrics(date, vars_score DESC);
CREATE INDEX idx_calc_metrics_date_stage ON calculated_metrics(date, stage);
```

---

## Documentation

**Create**: `backend/docs/screeners.md`
- Document all 11 screeners
- Query examples
- Filter options
- Response formats

---

# Success Criteria

**Phase 2 Complete When**:
- ✅ All 40+ metrics calculated daily
- ✅ All 11 screener endpoints functional
- ✅ Metrics calculation completes in <5 minutes
- ✅ Screener queries return in <2 seconds
- ✅ n8n workflow runs daily at 9 PM IST
- ✅ All endpoints tested via Swagger UI
- ✅ Documentation complete

---

**END OF BACKEND SCREENERS PLAN**

Ready to start Day 1: Database Schema Updates!