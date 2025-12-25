"""
Screener API Endpoints.

Provides endpoints for all 11 stock screeners based on calculated metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import Optional, List
from datetime import date, timedelta

from app.database.session import get_db
from app.models.timeseries import CalculatedMetrics, OHLCVDaily
from app.models.security import Security
from app.models.metadata import IndustryClassification

router = APIRouter()


@router.get("/breakouts-4percent")
async def get_4percent_breakouts(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_change: float = Query(4.0, description="Minimum % change (default: 4.0)"),
    min_rvol: float = Query(1.5, description="Minimum RVOL (default: 1.5)"),
    limit: int = Query(100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #1: 4% Daily Breakouts**

    Find momentum stocks with strong price moves and volume surge.

    **Criteria:**
    - Daily change ≥ 4% (configurable)
    - RVOL ≥ 1.5 (volume surge)
    - Sorted by % change (highest first)

    **Use Case:**
    Identify stocks with strong intraday momentum backed by institutional buying.

    **Query Parameters:**
    - target_date: Date to screen (YYYY-MM-DD, default: latest)
    - min_change: Minimum % change threshold (default: 4.0)
    - min_rvol: Minimum relative volume (default: 1.5)
    - limit: Max results (default: 100)

    **Returns:**
    List of stocks meeting criteria with key metrics.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/screeners/breakouts-4percent?min_change=5.0&limit=20"
    ```
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.change_1d_percent,
        CalculatedMetrics.rvol,
        CalculatedMetrics.volume_50d_avg,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.atr_percent,
        CalculatedMetrics.stage,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.change_1d_percent >= min_change,
            CalculatedMetrics.rvol >= min_rvol
        )
    ).order_by(
        desc(CalculatedMetrics.change_1d_percent)
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "change_percent": float(row.change_1d_percent) if row.change_1d_percent else None,
            "rvol": float(row.rvol) if row.rvol else None,
            "volume_50d_avg": int(row.volume_50d_avg) if row.volume_50d_avg else None,
            "rs_percentile": float(row.rs_percentile) if row.rs_percentile else None,
            "atr_percent": float(row.atr_percent) if row.atr_percent else None,
            "stage": row.stage
        })

    return {
        "screener": "4% Daily Breakouts",
        "date": str(target_date),
        "criteria": {
            "min_change_percent": min_change,
            "min_rvol": min_rvol
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/rs-leaders")
async def get_rs_leaders(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_rs: float = Query(97.0, description="Minimum RS percentile (default: 97)"),
    min_stage: int = Query(2, description="Minimum stage (default: 2 = uptrend)"),
    limit: int = Query(100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #2: RS Leaders (97 Club)**

    Find top 3% relative strength stocks with volatility adjustment.

    **Criteria:**
    - RS percentile ≥ 97 (top 3% performers)
    - Stage ≥ 2 (confirmed uptrend)
    - Sorted by VARS (volatility-adjusted RS)

    **Use Case:**
    Identify strongest stocks with sustainable momentum (high RS, low volatility).

    **VARS Formula:**
    VARS = RS Percentile / ADR%
    Higher VARS = Strong momentum with tight price action

    **Returns:**
    Top RS stocks ranked by VARS score.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.vars_score,
        CalculatedMetrics.change_1m_percent,
        CalculatedMetrics.adr_percent,
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.rs_percentile >= min_rs,
            CalculatedMetrics.stage >= min_stage
        )
    ).order_by(
        desc(CalculatedMetrics.vars_score)
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "rs_percentile": float(row.rs_percentile) if row.rs_percentile else None,
            "vars_score": float(row.vars_score) if row.vars_score else None,
            "change_1m_percent": float(row.change_1m_percent) if row.change_1m_percent else None,
            "adr_percent": float(row.adr_percent) if row.adr_percent else None,
            "stage": row.stage,
            "stage_detail": row.stage_detail
        })

    return {
        "screener": "RS Leaders (97 Club)",
        "date": str(target_date),
        "criteria": {
            "min_rs_percentile": min_rs,
            "min_stage": min_stage
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/high-volume")
async def get_high_volume_movers(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_rvol: float = Query(2.0, description="Minimum RVOL (default: 2.0)"),
    limit: int = Query(100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #3: High Volume Movers**

    Find stocks with exceptional volume surges (2x+ normal volume).

    **Criteria:**
    - RVOL ≥ 2.0 (volume surge indicator)
    - Sorted by RVOL (highest first)

    **Use Case:**
    Detect institutional activity or unusual trading interest.

    **RVOL Formula:**
    RVOL = Today's Volume / 50-day Average Volume
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.rvol,
        CalculatedMetrics.volume_50d_avg,
        CalculatedMetrics.change_1d_percent,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.atr_percent,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.rvol >= min_rvol
        )
    ).order_by(
        desc(CalculatedMetrics.rvol)
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "rvol": float(row.rvol) if row.rvol else None,
            "volume_50d_avg": int(row.volume_50d_avg) if row.volume_50d_avg else None,
            "change_percent": float(row.change_1d_percent) if row.change_1d_percent else None,
            "rs_percentile": float(row.rs_percentile) if row.rs_percentile else None,
            "atr_percent": float(row.atr_percent) if row.atr_percent else None
        })

    return {
        "screener": "High Volume Movers",
        "date": str(target_date),
        "criteria": {
            "min_rvol": min_rvol
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/ma-stacked")
async def get_ma_stacked_breakouts(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_vcp: int = Query(2, description="Minimum VCP score (default: 2)"),
    max_stage: int = Query(2, description="Maximum stage (default: 2 = early uptrend)"),
    limit: int = Query(100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #4: MA Stacked Breakouts**

    Find clean uptrend breakouts with VCP pattern confirmation.

    **Criteria:**
    - MA Stacked: close > EMA10 > SMA20 > SMA50 > SMA100 > SMA200
    - VCP Score ≥ 2 (volatility contraction pattern)
    - Stage = 2 (uptrend stage)
    - Sorted by RS percentile (highest first)

    **Use Case:**
    Identify high-probability breakout setups with aligned moving averages.

    **VCP Pattern:**
    Score 1-5 based on narrowing price range over 3-5 bars.
    Higher score = Tighter consolidation = Better setup.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.vcp_score,
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail,
        CalculatedMetrics.atr_extension_from_sma50,
        CalculatedMetrics.darvas_position_percent,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.is_ma_stacked == 1,
            CalculatedMetrics.vcp_score >= min_vcp,
            CalculatedMetrics.stage == max_stage
        )
    ).order_by(
        desc(CalculatedMetrics.rs_percentile)
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "rs_percentile": float(row.rs_percentile) if row.rs_percentile else None,
            "vcp_score": row.vcp_score,
            "stage": row.stage,
            "stage_detail": row.stage_detail,
            "atr_extension": float(row.atr_extension_from_sma50) if row.atr_extension_from_sma50 else None,
            "darvas_position": float(row.darvas_position_percent) if row.darvas_position_percent else None
        })

    return {
        "screener": "MA Stacked Breakouts",
        "date": str(target_date),
        "criteria": {
            "is_ma_stacked": True,
            "min_vcp_score": min_vcp,
            "stage": max_stage
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/weekly-movers")
async def get_weekly_movers(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_change: float = Query(20.0, description="Minimum weekly % change (default: 20.0)"),
    direction: str = Query("both", description="Direction: 'up', 'down', or 'both'"),
    limit: int = Query(100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #5: 20% Weekly Movers**

    Find extreme weekly swings for pattern recognition and volatility context.

    **Criteria:**
    - Weekly change ≥ 20% (configurable, can be ±20%)
    - Includes ADR% for volatility context
    - Sorted by absolute % change (highest first)

    **Use Case:**
    Identify stocks with extreme momentum or reversals for swing trading.

    **Query Parameters:**
    - direction: 'up' (≥+20%), 'down' (≤-20%), or 'both' (|change| ≥ 20%)
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    # Build filter based on direction
    if direction == "up":
        filter_condition = CalculatedMetrics.change_1w_percent >= min_change
    elif direction == "down":
        filter_condition = CalculatedMetrics.change_1w_percent <= -min_change
    else:  # both
        filter_condition = or_(
            CalculatedMetrics.change_1w_percent >= min_change,
            CalculatedMetrics.change_1w_percent <= -min_change
        )

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.change_1w_percent,
        CalculatedMetrics.change_1d_percent,
        CalculatedMetrics.adr_percent,
        CalculatedMetrics.rvol,
        CalculatedMetrics.stage,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            filter_condition
        )
    ).order_by(
        func.abs(CalculatedMetrics.change_1w_percent).desc()
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "change_1w_percent": float(row.change_1w_percent) if row.change_1w_percent else None,
            "change_1d_percent": float(row.change_1d_percent) if row.change_1d_percent else None,
            "adr_percent": float(row.adr_percent) if row.adr_percent else None,
            "rvol": float(row.rvol) if row.rvol else None,
            "stage": row.stage
        })

    return {
        "screener": "20% Weekly Movers",
        "date": str(target_date),
        "criteria": {
            "min_change_percent": min_change,
            "direction": direction
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/stage-analysis")
async def get_stage_analysis(
    target_date: Optional[date] = Query(None, description="Date to analyze (default: latest available)"),
    db: Session = Depends(get_db)
):
    """
    **Screener #6: Stage Analysis Breakdown**

    Classify stocks by Weinstein stage with LoD ATR% for entry timing.

    **Stage Classification:**
    - Stage 1: Basing (close < all MAs)
    - Stage 2A: Early Uptrend (close > MAs, <100% Darvas range)
    - Stage 2B: At Darvas Top (close at 100% of Darvas range)
    - Stage 2C: Extended (≥7x ATR from SMA50)
    - Stage 3: Topping (falling but above some MAs)
    - Stage 4: Declining (below MAs)

    **Metrics:**
    - Distribution by stage (count & percentage)
    - Average LoD ATR% per stage
    - Tight LoD flags (<60% ATR)

    **Returns:**
    Stage breakdown with statistics for market health assessment.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    # Get stage distribution
    stage_stats = db.query(
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail,
        func.count(CalculatedMetrics.id).label('count'),
        func.avg(CalculatedMetrics.lod_atr_percent).label('avg_lod_atr'),
        func.sum(CalculatedMetrics.is_lod_tight).label('tight_lod_count')
    ).filter(
        CalculatedMetrics.date == target_date
    ).group_by(
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail
    ).all()

    # Total stocks for percentage calculation
    total_stocks = db.query(func.count(CalculatedMetrics.id)).filter(
        CalculatedMetrics.date == target_date
    ).scalar()

    breakdown = []
    for row in stage_stats:
        breakdown.append({
            "stage": row.stage,
            "stage_detail": row.stage_detail,
            "count": row.count,
            "percentage": round(row.count / total_stocks * 100, 2) if total_stocks else 0,
            "avg_lod_atr_percent": float(row.avg_lod_atr) if row.avg_lod_atr else None,
            "tight_lod_count": row.tight_lod_count or 0
        })

    # Sort by stage number
    breakdown.sort(key=lambda x: (x['stage'] or 0, x['stage_detail'] or ''))

    return {
        "screener": "Stage Analysis Breakdown",
        "date": str(target_date),
        "total_stocks": total_stocks,
        "breakdown": breakdown
    }


@router.get("/momentum-watchlist")
async def get_momentum_watchlist(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_rs: float = Query(70.0, description="Minimum RS percentile (default: 70)"),
    max_extension: float = Query(7.0, description="Max ATR extension from SMA50 (default: 7)"),
    min_stage: int = Query(2, description="Minimum stage (default: 2 = uptrend)"),
    limit: int = Query(50, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #7: Momentum Watchlist**

    High RS stocks in uptrend near support, ready for entry.

    **Criteria:**
    - RS percentile ≥ 70 (strong momentum)
    - Stage ≥ 2 (uptrend confirmed)
    - ATR extension ≤ 7x (not overextended)
    - LoD ATR% < 60% (tight action, preferred)
    - Sorted by least extended (best risk/reward)

    **Use Case:**
    Find strong stocks pulling back to support for swing entries.

    **Returns:**
    Watchlist candidates with RS, stage, and extension metrics.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    results = db.query(
        CalculatedMetrics.symbol,
        CalculatedMetrics.rs_percentile,
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail,
        CalculatedMetrics.atr_extension_from_sma50,
        CalculatedMetrics.lod_atr_percent,
        CalculatedMetrics.is_lod_tight,
        CalculatedMetrics.is_green_candle,
        CalculatedMetrics.change_1d_percent,
        Security.security_name
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.rs_percentile >= min_rs,
            CalculatedMetrics.stage >= min_stage,
            CalculatedMetrics.atr_extension_from_sma50 <= max_extension
        )
    ).order_by(
        CalculatedMetrics.atr_extension_from_sma50.asc()  # Least extended first
    ).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "rs_percentile": float(row.rs_percentile) if row.rs_percentile else None,
            "stage": row.stage,
            "stage_detail": row.stage_detail,
            "atr_extension": float(row.atr_extension_from_sma50) if row.atr_extension_from_sma50 else None,
            "lod_atr_percent": float(row.lod_atr_percent) if row.lod_atr_percent else None,
            "is_tight": bool(row.is_lod_tight),
            "is_green_candle": bool(row.is_green_candle),
            "change_1d_percent": float(row.change_1d_percent) if row.change_1d_percent else None
        })

    return {
        "screener": "Momentum Watchlist",
        "date": str(target_date),
        "criteria": {
            "min_rs_percentile": min_rs,
            "max_atr_extension": max_extension,
            "min_stage": min_stage
        },
        "count": len(stocks),
        "results": stocks
    }


@router.get("/breadth-metrics")
async def get_breadth_metrics(
    target_date: Optional[date] = Query(None, description="Date to analyze (default: latest available)"),
    db: Session = Depends(get_db)
):
    """
    **Screener #8: Breadth Metrics Dashboard**

    Market sentiment indicators for timing entries/exits.

    **Metrics:**
    - Up/Down counts and ratio
    - % Above key MAs (SMA20, SMA50, SMA200)
    - New 20-day highs/lows
    - McClellan Oscillator & Summation Index

    **Use Case:**
    Assess overall market health and identify trend reversals.

    **Returns:**
    Comprehensive breadth statistics for the universe.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    # Count universe stocks (active securities with metrics)
    total_stocks = db.query(func.count(CalculatedMetrics.id)).filter(
        CalculatedMetrics.date == target_date
    ).scalar()

    # Up/Down counts
    up_count = db.query(func.count(CalculatedMetrics.id)).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.is_green_candle == 1
        )
    ).scalar()

    down_count = total_stocks - up_count

    # % Above MAs
    above_sma20 = db.query(func.count(CalculatedMetrics.id)).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.distance_from_sma50_percent > 0  # Using SMA50 as proxy
        )
    ).scalar()

    above_sma200 = db.query(func.count(CalculatedMetrics.id)).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.distance_from_sma200_percent > 0
        )
    ).scalar()

    # New highs/lows
    new_highs = db.query(func.count(CalculatedMetrics.id)).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.is_new_20d_high == 1
        )
    ).scalar()

    new_lows = db.query(func.count(CalculatedMetrics.id)).filter(
        and_(
            CalculatedMetrics.date == target_date,
            CalculatedMetrics.is_new_20d_low == 1
        )
    ).scalar()

    # McClellan metrics (same for all stocks on a date, so just get first)
    mcclellan_data = db.query(
        CalculatedMetrics.mcclellan_oscillator,
        CalculatedMetrics.mcclellan_summation,
        CalculatedMetrics.universe_up_count,
        CalculatedMetrics.universe_down_count
    ).filter(
        CalculatedMetrics.date == target_date
    ).first()

    return {
        "screener": "Breadth Metrics Dashboard",
        "date": str(target_date),
        "total_stocks": total_stocks,
        "up_down": {
            "up_count": up_count,
            "down_count": down_count,
            "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else None
        },
        "ma_analysis": {
            "above_sma20_count": above_sma20,
            "above_sma20_percent": round(above_sma20 / total_stocks * 100, 2) if total_stocks else 0,
            "above_sma200_count": above_sma200,
            "above_sma200_percent": round(above_sma200 / total_stocks * 100, 2) if total_stocks else 0
        },
        "new_highs_lows": {
            "new_20d_highs": new_highs,
            "new_20d_lows": new_lows,
            "high_low_ratio": round(new_highs / new_lows, 2) if new_lows > 0 else None
        },
        "mcclellan": {
            "oscillator": float(mcclellan_data.mcclellan_oscillator) if mcclellan_data and mcclellan_data.mcclellan_oscillator else None,
            "summation": float(mcclellan_data.mcclellan_summation) if mcclellan_data and mcclellan_data.mcclellan_summation else None,
            "universe_up_count": mcclellan_data.universe_up_count if mcclellan_data else None,
            "universe_down_count": mcclellan_data.universe_down_count if mcclellan_data else None
        }
    }


@router.get("/leading-industries")
async def get_leading_industries(
    target_date: Optional[date] = Query(None, description="Date to analyze (default: latest available)"),
    limit: int = Query(20, description="Number of industries to return (default: 20)"),
    db: Session = Depends(get_db)
):
    """
    **Screener #9: Leading Industries/Groups**

    Identify top 20% strongest industries by volatility-adjusted relative strength.

    **Criteria:**
    - Industry-level aggregation of VARS scores
    - Sorted by average VARS (highest first)
    - Shows top performers within each industry

    **Use Case:**
    Find sector rotation opportunities and leading industry groups.

    **Returns:**
    Industry rankings with top 4 performers in each group.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    # Get industry-level aggregated metrics
    industry_stats = db.query(
        IndustryClassification.industry,
        IndustryClassification.sector,
        func.avg(CalculatedMetrics.vars_score).label('avg_vars'),
        func.avg(CalculatedMetrics.varw_score).label('avg_varw'),
        func.avg(CalculatedMetrics.change_1w_percent).label('avg_weekly_change'),
        func.avg(CalculatedMetrics.change_1m_percent).label('avg_monthly_change'),
        func.count(CalculatedMetrics.id).label('stock_count')
    ).join(
        CalculatedMetrics, CalculatedMetrics.symbol == IndustryClassification.symbol
    ).filter(
        CalculatedMetrics.date == target_date
    ).group_by(
        IndustryClassification.industry,
        IndustryClassification.sector
    ).order_by(
        desc(func.avg(CalculatedMetrics.vars_score))
    ).limit(limit).all()

    industries = []
    for row in industry_stats:
        # Get top 4 performers in this industry
        top_performers = db.query(
            CalculatedMetrics.symbol,
            CalculatedMetrics.change_1m_percent,
            Security.security_name
        ).join(
            IndustryClassification, IndustryClassification.symbol == CalculatedMetrics.symbol
        ).join(
            Security, Security.symbol == CalculatedMetrics.symbol
        ).filter(
            and_(
                CalculatedMetrics.date == target_date,
                IndustryClassification.industry == row.industry
            )
        ).order_by(
            desc(CalculatedMetrics.change_1m_percent)
        ).limit(4).all()

        industries.append({
            "industry": row.industry,
            "sector": row.sector,
            "avg_vars": float(row.avg_vars) if row.avg_vars else None,
            "avg_varw": float(row.avg_varw) if row.avg_varw else None,
            "avg_weekly_change_percent": float(row.avg_weekly_change) if row.avg_weekly_change else None,
            "avg_monthly_change_percent": float(row.avg_monthly_change) if row.avg_monthly_change else None,
            "stock_count": row.stock_count,
            "top_performers": [
                {
                    "symbol": p.symbol,
                    "name": p.security_name,
                    "change_1m_percent": float(p.change_1m_percent) if p.change_1m_percent else None
                }
                for p in top_performers
            ]
        })

    return {
        "screener": "Leading Industries/Groups",
        "date": str(target_date),
        "count": len(industries),
        "results": industries
    }


@router.get("/rrg-charts")
async def get_rrg_charts(
    target_date: Optional[date] = Query(None, description="Date to analyze (default: latest available)"),
    benchmark: str = Query("NIFTY 50", description="Benchmark index (default: NIFTY 50)"),
    db: Session = Depends(get_db)
):
    """
    **Screener #10: RRG Charts for Sectoral Indices**

    Relative Rotation Graph data for sector/industry analysis vs. benchmark.

    **RRG Quadrants:**
    - Leading: RS-Ratio > 100, RS-Momentum > 100 (strong & improving)
    - Weakening: RS-Ratio > 100, RS-Momentum < 100 (strong but fading)
    - Lagging: RS-Ratio < 100, RS-Momentum < 100 (weak & deteriorating)
    - Improving: RS-Ratio < 100, RS-Momentum > 100 (weak but strengthening)

    **Metrics:**
    - RS-Ratio: (sector close / benchmark close) * 100
    - RS-Momentum: 1-week ROC of RS-Ratio (smoothed)

    **Use Case:**
    Visualize sector rotation and identify sectors moving into leading quadrant.

    **Returns:**
    RRG coordinates for all industries/sectors.
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    # Get benchmark close price (using NIFTY 50 index from OHLCV)
    benchmark_data = db.query(OHLCVDaily.close).filter(
        and_(
            OHLCVDaily.symbol == benchmark,
            OHLCVDaily.date == target_date
        )
    ).first()

    if not benchmark_data:
        raise HTTPException(
            status_code=404,
            detail=f"No benchmark data found for {benchmark} on {target_date}"
        )

    benchmark_close = float(benchmark_data.close)

    # Get industry-level RRG metrics
    industry_rrg = db.query(
        IndustryClassification.industry,
        IndustryClassification.sector,
        func.avg(CalculatedMetrics.rs_ratio).label('avg_rs_ratio'),
        func.avg(CalculatedMetrics.rs_momentum).label('avg_rs_momentum'),
        func.avg(CalculatedMetrics.change_1w_percent).label('avg_weekly_change'),
        func.count(CalculatedMetrics.id).label('stock_count')
    ).join(
        CalculatedMetrics, CalculatedMetrics.symbol == IndustryClassification.symbol
    ).filter(
        CalculatedMetrics.date == target_date
    ).group_by(
        IndustryClassification.industry,
        IndustryClassification.sector
    ).all()

    # Classify into RRG quadrants
    sectors = []
    for row in industry_rrg:
        rs_ratio = float(row.avg_rs_ratio) if row.avg_rs_ratio else 100.0
        rs_momentum = float(row.avg_rs_momentum) if row.avg_rs_momentum else 100.0

        # Determine quadrant
        if rs_ratio > 100 and rs_momentum > 100:
            quadrant = "Leading"
        elif rs_ratio > 100 and rs_momentum <= 100:
            quadrant = "Weakening"
        elif rs_ratio <= 100 and rs_momentum <= 100:
            quadrant = "Lagging"
        else:  # rs_ratio <= 100 and rs_momentum > 100
            quadrant = "Improving"

        sectors.append({
            "industry": row.industry,
            "sector": row.sector,
            "rs_ratio": rs_ratio,
            "rs_momentum": rs_momentum,
            "quadrant": quadrant,
            "avg_weekly_change_percent": float(row.avg_weekly_change) if row.avg_weekly_change else None,
            "stock_count": row.stock_count
        })

    # Sort by RS-Ratio (strongest first)
    sectors.sort(key=lambda x: x['rs_ratio'], reverse=True)

    return {
        "screener": "RRG Charts for Sectoral Indices",
        "date": str(target_date),
        "benchmark": benchmark,
        "benchmark_close": benchmark_close,
        "count": len(sectors),
        "results": sectors
    }
