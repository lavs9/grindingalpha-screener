"""
Data quality, ingestion status, and monitoring endpoints.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from datetime import datetime, timedelta, date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Dict, List, Optional, Any
from app.database.session import get_db
from app.models.security import Security
from app.models.timeseries import OHLCVDaily, MarketCapHistory
from app.models.metadata import IndustryClassification, IngestionLog, MarketHoliday
import pytz


router = APIRouter()


class DataQualityResponse(BaseModel):
    """Data quality metrics response."""
    total_securities: int
    active_securities: int
    ohlcv_coverage_percent: float
    ohlcv_last_date: Optional[str]
    ohlcv_securities_with_data: int
    market_cap_coverage_percent: float
    market_cap_last_date: Optional[str]
    market_cap_securities_with_data: int
    industry_coverage_percent: float
    securities_with_industry: int
    gaps_detected: List[Dict[str, Any]]
    timestamp: str


class IngestionStatusSource(BaseModel):
    """Single source ingestion status."""
    source: str
    last_run: Optional[str]
    status: Optional[str]
    records_fetched: Optional[int]
    records_inserted: Optional[int]
    records_updated: Optional[int]
    records_failed: Optional[int]
    execution_time_ms: Optional[int]
    errors: Optional[List[Any]]


class IngestionStatusResponse(BaseModel):
    """Ingestion status for all sources."""
    sources: List[IngestionStatusSource]
    total_sources: int
    successful_sources: int
    failed_sources: int
    last_check: str


class TradingDayResponse(BaseModel):
    """Trading day check response."""
    is_trading_day: bool
    date: str
    reason: str


@router.get("/data-quality", response_model=DataQualityResponse)
async def get_data_quality(
    check_gaps_for_top: int = Query(50, description="Number of top securities to check for OHLCV gaps"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive data quality metrics.

    Checks:
    - Total and active securities count
    - OHLCV coverage for last trading day
    - Market cap coverage
    - Industry classification coverage
    - Gap detection in OHLCV data for top securities

    Args:
        check_gaps_for_top: Number of top securities to check for gaps (default: 50)
        db: Database session

    Returns:
        DataQualityResponse: Comprehensive data quality report
    """
    # Total securities count
    total_securities = db.query(Security).count()
    active_securities = db.query(Security).filter(Security.is_active == True).count()

    # Get last trading date from OHLCV data
    last_ohlcv_date = db.query(func.max(OHLCVDaily.date)).scalar()

    # OHLCV coverage for last trading day
    ohlcv_coverage = 0.0
    ohlcv_securities_with_data = 0
    if last_ohlcv_date:
        ohlcv_securities_with_data = db.query(func.count(func.distinct(OHLCVDaily.symbol))).filter(
            OHLCVDaily.date == last_ohlcv_date
        ).scalar() or 0
        if active_securities > 0:
            ohlcv_coverage = (ohlcv_securities_with_data / active_securities) * 100

    # Get last market cap date
    last_market_cap_date = db.query(func.max(MarketCapHistory.date)).scalar()

    # Market cap coverage
    market_cap_coverage = 0.0
    market_cap_securities_with_data = 0
    if last_market_cap_date:
        market_cap_securities_with_data = db.query(func.count(func.distinct(MarketCapHistory.symbol))).filter(
            MarketCapHistory.date == last_market_cap_date
        ).scalar() or 0
        if active_securities > 0:
            market_cap_coverage = (market_cap_securities_with_data / active_securities) * 100

    # Industry classification coverage
    # Count active securities that have a matching industry_classification record
    securities_with_industry = db.query(func.count(func.distinct(Security.symbol))).join(
        IndustryClassification,
        Security.symbol == IndustryClassification.symbol
    ).filter(
        Security.is_active == True
    ).scalar() or 0

    industry_coverage = 0.0
    if active_securities > 0:
        industry_coverage = (securities_with_industry / active_securities) * 100

    # Gap detection for top securities (by market cap or alphabetically)
    gaps_detected = []
    if last_ohlcv_date and check_gaps_for_top > 0:
        # Get top N securities with latest market cap
        top_securities_query = db.query(Security.symbol).join(
            MarketCapHistory,
            and_(
                Security.symbol == MarketCapHistory.symbol,
                MarketCapHistory.date == last_market_cap_date
            ),
            isouter=True
        ).filter(
            Security.is_active == True
        ).order_by(
            desc(MarketCapHistory.market_cap)
        ).limit(check_gaps_for_top)

        top_symbols = [row.symbol for row in top_securities_query.all()]

        # Check for gaps in last 30 trading days
        check_start_date = last_ohlcv_date - timedelta(days=45)  # ~30 trading days

        for symbol in top_symbols[:10]:  # Limit to first 10 to avoid slow response
            # Get all dates for this symbol
            dates_query = db.query(OHLCVDaily.date).filter(
                and_(
                    OHLCVDaily.symbol == symbol,
                    OHLCVDaily.date >= check_start_date,
                    OHLCVDaily.date <= last_ohlcv_date
                )
            ).order_by(OHLCVDaily.date).all()

            dates = [row.date for row in dates_query]

            if len(dates) > 0:
                # Check for gaps (missing dates between first and last)
                expected_trading_days = (last_ohlcv_date - dates[0]).days
                actual_days = len(dates)

                # Allow for weekends/holidays (rough estimate: 5/7 ratio)
                expected_approx = int(expected_trading_days * 5 / 7)

                if actual_days < expected_approx * 0.9:  # Missing > 10% of expected days
                    gaps_detected.append({
                        "symbol": symbol,
                        "first_date": dates[0].isoformat(),
                        "last_date": dates[-1].isoformat(),
                        "actual_records": actual_days,
                        "expected_approx": expected_approx,
                        "gap_percent": round((1 - actual_days / expected_approx) * 100, 2)
                    })

    return DataQualityResponse(
        total_securities=total_securities,
        active_securities=active_securities,
        ohlcv_coverage_percent=round(ohlcv_coverage, 2),
        ohlcv_last_date=last_ohlcv_date.isoformat() if last_ohlcv_date else None,
        ohlcv_securities_with_data=ohlcv_securities_with_data,
        market_cap_coverage_percent=round(market_cap_coverage, 2),
        market_cap_last_date=last_market_cap_date.isoformat() if last_market_cap_date else None,
        market_cap_securities_with_data=market_cap_securities_with_data,
        industry_coverage_percent=round(industry_coverage, 2),
        securities_with_industry=securities_with_industry,
        gaps_detected=gaps_detected,
        timestamp=datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
    )


@router.get("/ingestion", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    hours: int = Query(24, description="Check ingestion logs from last N hours"),
    db: Session = Depends(get_db)
):
    """
    Get ingestion status for all data sources.

    Queries the `ingestion_logs` table to return the latest status for each source.

    Args:
        hours: Number of hours to look back (default: 24)
        db: Database session

    Returns:
        IngestionStatusResponse: Latest status for each ingestion source
    """
    # Get cutoff time
    ist = pytz.timezone('Asia/Kolkata')
    cutoff_time = datetime.now(ist) - timedelta(hours=hours)

    # Get all unique sources
    all_sources = db.query(func.distinct(IngestionLog.source)).all()
    source_names = [row[0] for row in all_sources]

    sources_status = []
    successful_count = 0
    failed_count = 0

    for source_name in source_names:
        # Get latest log for this source
        latest_log = db.query(IngestionLog).filter(
            IngestionLog.source == source_name
        ).order_by(desc(IngestionLog.timestamp)).first()

        if latest_log:
            source_status = IngestionStatusSource(
                source=latest_log.source,
                last_run=latest_log.timestamp.isoformat() if latest_log.timestamp else None,
                status=latest_log.status,
                records_fetched=latest_log.records_fetched,
                records_inserted=latest_log.records_inserted,
                records_updated=latest_log.records_updated,
                records_failed=latest_log.records_failed,
                execution_time_ms=latest_log.execution_time_ms,
                errors=latest_log.errors if latest_log.errors else []
            )

            if latest_log.status == "success":
                successful_count += 1
            elif latest_log.status == "failure":
                failed_count += 1

            sources_status.append(source_status)

    return IngestionStatusResponse(
        sources=sources_status,
        total_sources=len(sources_status),
        successful_sources=successful_count,
        failed_sources=failed_count,
        last_check=datetime.now(ist).isoformat()
    )


@router.get("/is-trading-day", response_model=TradingDayResponse)
async def is_trading_day(
    date: Optional[date_type] = Query(None, description="Date to check (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db)
):
    """
    Check if a given date is a trading day (not weekend or holiday).

    Used by n8n workflows to determine if data ingestion should run.

    Args:
        date: Date to check (defaults to today)
        db: Database session

    Returns:
        TradingDayResponse: Whether the date is a trading day with reason
    """
    if date is None:
        ist = pytz.timezone('Asia/Kolkata')
        date = datetime.now(ist).date()

    # Check if weekend (Saturday=5, Sunday=6)
    is_weekend = date.weekday() >= 5

    # Check if market holiday
    holiday = db.query(MarketHoliday).filter(
        MarketHoliday.holiday_date == date
    ).first()

    is_holiday = holiday is not None
    is_trading = not (is_weekend or is_holiday)

    # Determine reason
    if is_trading:
        reason = "trading"
    elif is_holiday:
        reason = f"holiday - {holiday.holiday_name}"
    else:
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][date.weekday()]
        reason = f"weekend - {day_name}"

    return TradingDayResponse(
        is_trading_day=is_trading,
        date=date.isoformat(),
        reason=reason
    )
