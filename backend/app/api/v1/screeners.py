"""
Screener API Endpoints.

Provides endpoints for all 15 stock screeners based on calculated metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import Optional, List
from datetime import date, timedelta

from app.database.session import get_db
from app.models.timeseries import CalculatedMetrics, OHLCVDaily, IndexOHLCVDaily, MarketCapHistory
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
        CalculatedMetrics.stage,
        CalculatedMetrics.stage_detail,
        Security.security_name,
        OHLCVDaily.volume,
        OHLCVDaily.close,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "change_1d_percent": float(row.change_1d_percent) if row.change_1d_percent else 0.0,
            "rvol": float(row.rvol) if row.rvol else 0.0,
            "volume": int(row.volume) if row.volume else 0,
            "close": float(row.close) if row.close else 0.0,
            "stage": row.stage if row.stage else 0,
            "stage_detail": row.stage_detail if row.stage_detail else "",
            "market_cap": float(row.market_cap) if row.market_cap else None
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
        Security.security_name,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "stage_detail": row.stage_detail,
            "market_cap": float(row.market_cap) if row.market_cap else None
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
        CalculatedMetrics.change_1d_percent,
        Security.security_name,
        OHLCVDaily.volume,
        OHLCVDaily.close,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "volume": int(row.volume) if row.volume else 0,
            "rvol": float(row.rvol) if row.rvol else 0.0,
            "change_1d_percent": float(row.change_1d_percent) if row.change_1d_percent else 0.0,
            "close": float(row.close) if row.close else 0.0,
            "market_cap": float(row.market_cap) if row.market_cap else None
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
        Security.security_name,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "darvas_position": float(row.darvas_position_percent) if row.darvas_position_percent else None,
            "market_cap": float(row.market_cap) if row.market_cap else None
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
        CalculatedMetrics.stage_detail,
        Security.security_name,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "stage": row.stage,
            "stage_detail": row.stage_detail if row.stage_detail else "",
            "market_cap": float(row.market_cap) if row.market_cap else None
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
        Security.security_name,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
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
            "change_1d_percent": float(row.change_1d_percent) if row.change_1d_percent else None,
            "market_cap": float(row.market_cap) if row.market_cap else None
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
            Security.security_name,
            MarketCapHistory.market_cap
        ).join(
            IndustryClassification, IndustryClassification.symbol == CalculatedMetrics.symbol
        ).join(
            Security, Security.symbol == CalculatedMetrics.symbol
        ).outerjoin(
            MarketCapHistory, and_(
                MarketCapHistory.symbol == CalculatedMetrics.symbol,
                MarketCapHistory.date == target_date
            )
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
                    "change_1m_percent": float(p.change_1m_percent) if p.change_1m_percent else None,
                    "market_cap": float(p.market_cap) if p.market_cap else None
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


def aggregate_to_weekly(daily_data: list) -> list:
    """
    Aggregate daily OHLCV data to weekly data.
    Weekly close = last trading day's close in the week.
    Returns list of (date, close) tuples for weekly data.
    """
    from datetime import timedelta
    from collections import defaultdict

    # Group by week (ISO week - Monday is start)
    weekly_groups = defaultdict(list)
    for row in daily_data:
        # Get ISO week number
        week_key = row.date.isocalendar()[:2]  # (year, week_number)
        weekly_groups[week_key].append(row)

    # For each week, take the last day's close
    weekly_data = []
    for week_key in sorted(weekly_groups.keys()):
        week_rows = sorted(weekly_groups[week_key], key=lambda x: x.date)
        last_row = week_rows[-1]  # Last trading day of the week
        weekly_data.append(last_row)

    return weekly_data


def aggregate_to_monthly(daily_data: list) -> list:
    """
    Aggregate daily OHLCV data to monthly data.
    Monthly close = last trading day's close in the month.
    Returns list of (date, close) tuples for monthly data.
    """
    from collections import defaultdict

    # Group by month
    monthly_groups = defaultdict(list)
    for row in daily_data:
        month_key = (row.date.year, row.date.month)
        monthly_groups[month_key].append(row)

    # For each month, take the last day's close
    monthly_data = []
    for month_key in sorted(monthly_groups.keys()):
        month_rows = sorted(monthly_groups[month_key], key=lambda x: x.date)
        last_row = month_rows[-1]  # Last trading day of the month
        monthly_data.append(last_row)

    return monthly_data


@router.get("/rrg-charts")
async def get_rrg_charts(
    target_date: Optional[date] = Query(None, description="Date to analyze (default: latest available)"),
    benchmark: str = Query("NIFTY", description="Benchmark index symbol (default: NIFTY)"),
    short_period: int = Query(21, description="Short momentum period in trading days (default: 21)"),
    long_period: int = Query(63, description="Long momentum period in trading days (default: 63 ~3 months)"),
    tail_length: int = Query(10, description="Number of historical points for RRG tails (default: 10, max: 60)"),
    show_sectoral_only: bool = Query(True, description="Show only sectoral/thematic indices (default: true)"),
    timeframe: Optional[str] = Query("daily", description="Timeframe: daily, weekly, or monthly (default: daily)"),
    db: Session = Depends(get_db)
):
    """
    **Screener #10: RRG Charts for Sectoral Indices (JdK Methodology)**

    Relative Rotation Graph data for sectoral indices (NIFTY BANK, NIFTY IT, etc.) vs. benchmark.

    **RRG Quadrants (axes cross at 100):**
    - Leading: RS-Ratio > 100, RS-Momentum > 100 (outperforming & gaining strength)
    - Weakening: RS-Ratio > 100, RS-Momentum ≤ 100 (outperforming but losing strength)
    - Lagging: RS-Ratio ≤ 100, RS-Momentum ≤ 100 (underperforming & weakening)
    - Improving: RS-Ratio ≤ 100, RS-Momentum > 100 (underperforming but gaining strength)

    **RRG Metrics (RRGPy methodology):**
    - RS-Ratio: 100 + ((raw_ratio - rolling_mean) / rolling_std) where raw_ratio = 100 * (index/benchmark)
    - RS-Momentum: 101 + ((roc - rolling_mean) / rolling_std) where roc = rate-of-change of RS-Ratio
    - Rolling window: 14 periods (default)

    **Use Case:**
    Visualize sector rotation and identify sectors moving into leading quadrant.
    Essential for sector rotation strategies.

    **Query Parameters:**
    - target_date: Date to analyze (default: latest)
    - benchmark: Benchmark symbol like "NIFTY" or "NIFTY 500" (default: NIFTY)
    - short_period: Rolling window for normalization (default: 14 days, ignored if using RRGPy method)
    - long_period: Historical data periods (default: 63 days for sufficient data)
    - tail_length: Number of historical points for RRG tails (default: 10, max: 60)
    - show_sectoral_only: Show only sectoral/thematic indices (default: true)
    - timeframe: Timeframe for candles - daily, weekly, or monthly (default: daily)

    **Returns:**
    RRG coordinates for all sectoral indices with values hovering around 100.
    """
    # Validate timeframe parameter
    valid_timeframes = ["daily", "weekly", "monthly"]
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}")

    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(IndexOHLCVDaily.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No index data available")
        target_date = latest

    # Limit tail_length to max 60 periods
    tail_length = min(tail_length, 60)

    # Rolling window for RRG normalization (standard is 14 periods)
    rolling_window = 14

    # Need enough data for: tail_length + 2*rolling_window
    # - First rolling_window for RS-Ratio normalization
    # - Second rolling_window for RS-Momentum normalization (which needs ROC of RS-Ratio)
    # - Plus tail_length for the actual display
    total_periods_needed = tail_length + (2 * rolling_window)

    # For weekly/monthly, we need more daily data to aggregate
    # Weekly: ~5 trading days per week, Monthly: ~21 trading days per month
    if timeframe == "weekly":
        fetch_periods = total_periods_needed * 7  # Fetch ~7 days per week to be safe
    elif timeframe == "monthly":
        fetch_periods = total_periods_needed * 30  # Fetch ~30 days per month to be safe
    else:  # daily
        fetch_periods = total_periods_needed

    benchmark_data_raw = db.query(
        IndexOHLCVDaily.date,
        IndexOHLCVDaily.close
    ).filter(
        and_(
            IndexOHLCVDaily.symbol == benchmark,
            IndexOHLCVDaily.date <= target_date
        )
    ).order_by(IndexOHLCVDaily.date.desc()).limit(fetch_periods).all()

    if not benchmark_data_raw:
        raise HTTPException(status_code=404, detail="No benchmark data available")

    # Reverse to chronological order
    benchmark_data_raw = list(reversed(benchmark_data_raw))

    # Apply timeframe aggregation
    if timeframe == "weekly":
        benchmark_data = aggregate_to_weekly(benchmark_data_raw)
    elif timeframe == "monthly":
        benchmark_data = aggregate_to_monthly(benchmark_data_raw)
    else:  # daily
        benchmark_data = benchmark_data_raw

    if len(benchmark_data) < total_periods_needed:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient historical data for benchmark. Need {total_periods_needed} {timeframe} periods, found {len(benchmark_data)}"
        )

    # Build benchmark price dict
    benchmark_prices = {row.date: float(row.close) for row in benchmark_data}

    # Get all sectoral indices query
    sectoral_query = db.query(IndexOHLCVDaily.symbol).filter(
        IndexOHLCVDaily.date == target_date
    )

    # Apply sector filter if show_sectoral_only is True
    if show_sectoral_only:
        sectoral_query = sectoral_query.filter(IndexOHLCVDaily.is_sectoral == 1)
    else:
        # Exclude only benchmark and VIX
        excluded_symbols = [benchmark, 'India VIX']
        sectoral_query = sectoral_query.filter(~IndexOHLCVDaily.symbol.in_(excluded_symbols))

    sectoral_indices = sectoral_query.distinct().all()

    sectors = []
    for (symbol,) in sectoral_indices:
        # Get historical data for this index
        index_data_raw = db.query(
            IndexOHLCVDaily.date,
            IndexOHLCVDaily.close,
            IndexOHLCVDaily.sector_category
        ).filter(
            and_(
                IndexOHLCVDaily.symbol == symbol,
                IndexOHLCVDaily.date <= target_date
            )
        ).order_by(IndexOHLCVDaily.date.desc()).limit(fetch_periods).all()

        if not index_data_raw:
            continue

        # Reverse to chronological order
        index_data_raw = list(reversed(index_data_raw))

        # Apply timeframe aggregation
        if timeframe == "weekly":
            index_data = aggregate_to_weekly(index_data_raw)
        elif timeframe == "monthly":
            index_data = aggregate_to_monthly(index_data_raw)
        else:  # daily
            index_data = index_data_raw

        if len(index_data) < total_periods_needed:
            continue

        # Build index price dict
        index_prices = {row.date: float(row.close) for row in index_data}
        sector_category = index_data[0].sector_category if index_data else None

        # Step 1: Calculate raw RS-Ratio: (index/benchmark) × 100
        rs_ratio_raw = []
        for i in range(len(index_data)):
            idx_price = index_prices.get(index_data[i].date)
            bench_price = benchmark_prices.get(index_data[i].date)
            if idx_price and bench_price and bench_price > 0:
                rs_ratio_raw.append((idx_price / bench_price) * 100)
            else:
                rs_ratio_raw.append(None)

        # Step 2: Calculate normalized RS-Ratio using rolling Z-score
        # RS-Ratio = 100 + ((raw_ratio - rolling_mean) / rolling_std)
        rs_ratio_normalized = []
        import statistics
        for i in range(len(rs_ratio_raw)):
            if i < rolling_window - 1:
                # Not enough data for rolling window
                rs_ratio_normalized.append(None)
            else:
                # Get rolling window
                window_data = [v for v in rs_ratio_raw[i - rolling_window + 1:i + 1] if v is not None]
                if len(window_data) >= rolling_window * 0.8:  # Allow 20% missing data
                    mean_val = statistics.mean(window_data)
                    std_val = statistics.stdev(window_data) if len(window_data) > 1 else 1
                    if rs_ratio_raw[i] is not None and std_val > 0:
                        normalized = 100 + ((rs_ratio_raw[i] - mean_val) / std_val)
                        rs_ratio_normalized.append(normalized)
                    else:
                        rs_ratio_normalized.append(None)
                else:
                    rs_ratio_normalized.append(None)

        # Step 3: Calculate Rate of Change (ROC) of normalized RS-Ratio
        # ROC = 100 * ((current / previous) - 1)
        rsr_roc = []
        for i in range(len(rs_ratio_normalized)):
            if i == 0 or rs_ratio_normalized[i] is None or rs_ratio_normalized[i-1] is None:
                rsr_roc.append(None)
            else:
                prev_val = rs_ratio_normalized[i-1]
                if prev_val != 0:
                    roc_val = 100 * ((rs_ratio_normalized[i] / prev_val) - 1)
                    rsr_roc.append(roc_val)
                else:
                    rsr_roc.append(None)

        # Step 4: Calculate RS-Momentum using rolling Z-score of ROC
        # RS-Momentum = 101 + ((roc - rolling_mean) / rolling_std)
        rs_momentum_normalized = []
        for i in range(len(rsr_roc)):
            if i < rolling_window - 1:
                # Not enough data for rolling window
                rs_momentum_normalized.append(None)
            else:
                # Get rolling window
                window_data = [v for v in rsr_roc[i - rolling_window + 1:i + 1] if v is not None]
                if len(window_data) >= rolling_window * 0.8:  # Allow 20% missing data
                    mean_val = statistics.mean(window_data)
                    std_val = statistics.stdev(window_data) if len(window_data) > 1 else 1
                    if rsr_roc[i] is not None and std_val > 0:
                        normalized = 101 + ((rsr_roc[i] - mean_val) / std_val)
                        rs_momentum_normalized.append(normalized)
                    else:
                        rs_momentum_normalized.append(None)
                else:
                    rs_momentum_normalized.append(None)

        # Calculate weekly change (1 week = ~5 trading days)
        current_close = float(index_prices.get(target_date, 0.0))
        if len(index_data) >= 6:  # Need at least 6 days (1 week + current)
            weekly_start_idx = -6
            weekly_start_price = float(index_data[weekly_start_idx].close)
            weekly_change = ((current_close - weekly_start_price) / weekly_start_price * 100) if weekly_start_price > 0 else 0.0
        else:
            weekly_change = 0.0

        # Store normalized values for this sector
        # Extract last tail_length points (only those with valid RS-Ratio and RS-Momentum)
        # Get the actual dates corresponding to the last tail_length data points
        tail_dates = [str(index_data[-(i+1)].date) for i in range(tail_length-1, -1, -1)]

        sectors.append({
            "symbol": symbol,
            "sector_category": sector_category,
            "rs_ratio_normalized": rs_ratio_normalized[-tail_length:],  # Last tail_length points
            "rs_momentum_normalized": rs_momentum_normalized[-tail_length:],
            "dates": tail_dates,
            "weekly_change_percent": round(weekly_change, 2),
            "current_close": current_close
        })

    # Build final sector objects with historical points
    final_sectors = []
    for sector in sectors:
        historical_points = []

        for i in range(len(sector["dates"])):
            ratio_val = sector["rs_ratio_normalized"][i]
            momentum_val = sector["rs_momentum_normalized"][i]

            if ratio_val is not None and momentum_val is not None:
                # Determine quadrant (axes cross at 100)
                if ratio_val > 100 and momentum_val > 100:
                    quadrant = "Leading"
                elif ratio_val > 100 and momentum_val <= 100:
                    quadrant = "Weakening"
                elif ratio_val <= 100 and momentum_val <= 100:
                    quadrant = "Lagging"
                else:  # ratio_val <= 100 and momentum_val > 100
                    quadrant = "Improving"

                historical_points.append({
                    "date": sector["dates"][i],
                    "rs_ratio": round(ratio_val, 4),
                    "rs_momentum": round(momentum_val, 4),
                    "quadrant": quadrant
                })

        if historical_points:
            latest_point = historical_points[-1]
            final_sectors.append({
                "index_symbol": sector["symbol"],
                "sector_category": sector["sector_category"],
                "rs_ratio": latest_point["rs_ratio"],
                "rs_momentum": latest_point["rs_momentum"],
                "quadrant": latest_point["quadrant"],
                "weekly_change_percent": sector["weekly_change_percent"],
                "current_close": round(sector["current_close"], 2),
                "historical_points": historical_points
            })
        else:
            # Debug: Log sectors with no historical points
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Sector {sector['symbol']} has no valid historical points. "
                       f"RS-Ratio count: {len([v for v in sector['rs_ratio_normalized'] if v is not None])}, "
                       f"RS-Momentum count: {len([v for v in sector['rs_momentum_normalized'] if v is not None])}")

    # Sort by RS-Ratio (strongest first)
    final_sectors.sort(key=lambda x: x['rs_ratio'], reverse=True)

    benchmark_current_close = benchmark_prices.get(target_date, 0.0)

    return {
        "screener": "RRG Charts for Sectoral Indices (RRGPy Methodology)",
        "date": str(target_date),
        "benchmark": benchmark,
        "benchmark_close": round(benchmark_current_close, 2),
        "short_period": rolling_window,
        "long_period": total_periods_needed,
        "tail_length": tail_length,
        "timeframe": timeframe,
        "show_sectoral_only": show_sectoral_only,
        "count": len(final_sectors),
        "quadrant_counts": {
            "Leading": sum(1 for s in final_sectors if s['quadrant'] == 'Leading'),
            "Weakening": sum(1 for s in final_sectors if s['quadrant'] == 'Weakening'),
            "Lagging": sum(1 for s in final_sectors if s['quadrant'] == 'Lagging'),
            "Improving": sum(1 for s in final_sectors if s['quadrant'] == 'Improving')
        },
        "results": final_sectors
    }


@router.get("/rsi-scanner")
async def get_rsi_scanner(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_rsi: Optional[float] = Query(None, description="Minimum RSI value"),
    max_rsi: Optional[float] = Query(None, description="Maximum RSI value"),
    show_oversold: bool = Query(False, description="Show only oversold stocks (RSI < 30)"),
    show_overbought: bool = Query(False, description="Show only overbought stocks (RSI > 70)"),
    limit: int = Query(200, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #12: RSI Overbought/Oversold Scanner**

    Identify potential reversals using 14-period RSI (Relative Strength Index).

    **Criteria:**
    - Oversold: RSI < 30 (potential buy signal)
    - Overbought: RSI > 70 (potential sell signal)
    - Neutral: RSI between 30-70
    - Uses Wilder's smoothing method (14-period)

    **Query Parameters:**
    - target_date: Date to screen (YYYY-MM-DD, default: latest)
    - min_rsi: Minimum RSI value filter
    - max_rsi: Maximum RSI value filter
    - show_oversold: Filter for RSI < 30 only
    - show_overbought: Filter for RSI > 70 only
    - limit: Max results (default: 200)

    **Returns:**
    List of stocks with RSI values, oversold/overbought flags, and price metrics.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/screeners/rsi-scanner?show_oversold=true"
    ```

    **Reference:**
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    query = db.query(
        CalculatedMetrics.symbol,
        Security.security_name,
        CalculatedMetrics.rsi_14,
        CalculatedMetrics.rsi_oversold,
        CalculatedMetrics.rsi_overbought,
        OHLCVDaily.close,
        CalculatedMetrics.change_1w_percent,
        OHLCVDaily.volume,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
    ).filter(
        CalculatedMetrics.date == target_date,
        Security.is_active == True,
        CalculatedMetrics.rsi_14.isnot(None)
    )

    # Apply filters
    if min_rsi is not None:
        query = query.filter(CalculatedMetrics.rsi_14 >= min_rsi)
    if max_rsi is not None:
        query = query.filter(CalculatedMetrics.rsi_14 <= max_rsi)
    if show_oversold:
        query = query.filter(CalculatedMetrics.rsi_oversold == 1)
    if show_overbought:
        query = query.filter(CalculatedMetrics.rsi_overbought == 1)

    results = query.order_by(desc(CalculatedMetrics.rsi_14)).limit(limit).all()

    stocks = []
    for row in results:
        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "rsi_14": float(row.rsi_14),
            "is_oversold": bool(row.rsi_oversold),
            "is_overbought": bool(row.rsi_overbought),
            "close": float(row.close),
            "change_1w_percent": float(row.change_1w_percent) if row.change_1w_percent else None,
            "volume": int(row.volume),
            "market_cap": float(row.market_cap) if row.market_cap else None
        })

    return {
        "screener": "RSI Overbought/Oversold Scanner",
        "date": str(target_date),
        "total_results": len(stocks),
        "results": stocks
    }


@router.get("/macd-crossover")
async def get_macd_crossover(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    crossover_type: str = Query("all", description="Filter by crossover type: 'all', 'bullish', 'bearish'"),
    min_histogram: Optional[float] = Query(None, description="Minimum histogram value"),
    limit: int = Query(200, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #13: MACD Crossover Scanner**

    Detect trend and momentum shifts using MACD (Moving Average Convergence Divergence).

    **Criteria:**
    - Bullish Crossover: MACD line crosses above signal line (momentum turning positive)
    - Bearish Crossover: MACD line crosses below signal line (momentum turning negative)
    - Histogram: MACD line - Signal line (momentum strength)
    - Uses 12-EMA, 26-EMA, 9-EMA signal line

    **Query Parameters:**
    - target_date: Date to screen (YYYY-MM-DD, default: latest)
    - crossover_type: 'all', 'bullish', or 'bearish' (default: all)
    - min_histogram: Minimum histogram value filter
    - limit: Max results (default: 200)

    **Returns:**
    List of stocks with MACD values, crossover type, and momentum metrics.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/screeners/macd-crossover?crossover_type=bullish"
    ```

    **Reference:**
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    query = db.query(
        CalculatedMetrics.symbol,
        Security.security_name,
        CalculatedMetrics.macd_line,
        CalculatedMetrics.macd_signal,
        CalculatedMetrics.macd_histogram,
        CalculatedMetrics.is_macd_bullish_cross,
        CalculatedMetrics.is_macd_bearish_cross,
        OHLCVDaily.close,
        CalculatedMetrics.change_1m_percent,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
    ).filter(
        CalculatedMetrics.date == target_date,
        Security.is_active == True,
        CalculatedMetrics.macd_line.isnot(None)
    )

    # Apply crossover filter
    if crossover_type == "bullish":
        query = query.filter(CalculatedMetrics.is_macd_bullish_cross == 1)
    elif crossover_type == "bearish":
        query = query.filter(CalculatedMetrics.is_macd_bearish_cross == 1)

    # Apply histogram filter
    if min_histogram is not None:
        query = query.filter(CalculatedMetrics.macd_histogram >= min_histogram)

    results = query.order_by(desc(CalculatedMetrics.macd_histogram)).limit(limit).all()

    stocks = []
    for row in results:
        # Determine crossover type
        crossover = "None"
        if row.is_macd_bullish_cross:
            crossover = "Bullish"
        elif row.is_macd_bearish_cross:
            crossover = "Bearish"

        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "macd_line": float(row.macd_line),
            "macd_signal": float(row.macd_signal),
            "macd_histogram": float(row.macd_histogram),
            "crossover_type": crossover,
            "close": float(row.close),
            "change_1m_percent": float(row.change_1m_percent) if row.change_1m_percent else None,
            "market_cap": float(row.market_cap) if row.market_cap else None
        })

    return {
        "screener": "MACD Crossover Scanner",
        "date": str(target_date),
        "total_results": len(stocks),
        "results": stocks
    }


@router.get("/bollinger-squeeze")
async def get_bollinger_squeeze(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    max_bandwidth: float = Query(10.0, description="Maximum bandwidth % for squeeze (default: 10.0)"),
    show_squeeze_only: bool = Query(True, description="Show only squeezes (default: true)"),
    limit: int = Query(200, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #14: Bollinger Band Squeeze Scanner**

    Identify low-volatility contractions that often precede significant breakouts.

    **Criteria:**
    - Squeeze: Bandwidth < 10% (low volatility, breakout likely)
    - Upper Band: 20-SMA + 2*StdDev
    - Middle Band: 20-SMA
    - Lower Band: 20-SMA - 2*StdDev
    - Bandwidth %: ((Upper - Lower) / Middle) * 100
    - Breakout Direction: Above Upper, Below Lower, or Within Bands

    **Query Parameters:**
    - target_date: Date to screen (YYYY-MM-DD, default: latest)
    - max_bandwidth: Maximum bandwidth % to consider squeeze (default: 10.0)
    - show_squeeze_only: Filter for squeezes only (default: true)
    - limit: Max results (default: 200)

    **Returns:**
    List of stocks with Bollinger Band values, bandwidth %, and breakout direction.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/screeners/bollinger-squeeze?max_bandwidth=8.0"
    ```

    **Reference:**
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    query = db.query(
        CalculatedMetrics.symbol,
        Security.security_name,
        CalculatedMetrics.bb_bandwidth_percent,
        CalculatedMetrics.is_bb_squeeze,
        OHLCVDaily.close,
        CalculatedMetrics.bb_upper,
        CalculatedMetrics.bb_middle,
        CalculatedMetrics.bb_lower,
        CalculatedMetrics.change_1w_percent,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
    ).filter(
        CalculatedMetrics.date == target_date,
        Security.is_active == True,
        CalculatedMetrics.bb_bandwidth_percent.isnot(None)
    )

    # Apply squeeze filter
    if show_squeeze_only:
        query = query.filter(CalculatedMetrics.bb_bandwidth_percent <= max_bandwidth)

    results = query.order_by(CalculatedMetrics.bb_bandwidth_percent.asc()).limit(limit).all()

    stocks = []
    for row in results:
        # Determine breakout direction
        if row.close > row.bb_upper:
            breakout_direction = "Above Upper"
        elif row.close < row.bb_lower:
            breakout_direction = "Below Lower"
        else:
            breakout_direction = "Within Bands"

        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "bb_bandwidth_percent": float(row.bb_bandwidth_percent),
            "is_squeeze": bool(row.is_bb_squeeze),
            "close": float(row.close),
            "bb_upper": float(row.bb_upper),
            "bb_middle": float(row.bb_middle),
            "bb_lower": float(row.bb_lower),
            "breakout_direction": breakout_direction,
            "change_1w_percent": float(row.change_1w_percent) if row.change_1w_percent else None,
            "market_cap": float(row.market_cap) if row.market_cap else None
        })

    return {
        "screener": "Bollinger Band Squeeze Scanner",
        "date": str(target_date),
        "total_results": len(stocks),
        "results": stocks
    }


@router.get("/adx-trend")
async def get_adx_trend(
    target_date: Optional[date] = Query(None, description="Date to screen (default: latest available)"),
    min_adx: float = Query(25.0, description="Minimum ADX value (default: 25.0)"),
    trend_direction: str = Query("all", description="Filter by trend: 'all', 'bullish', 'bearish'"),
    limit: int = Query(200, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    **Screener #15: ADX Trend Strength Scanner**

    Identify strong trends using ADX (Average Directional Index).

    **Criteria:**
    - Strong Trend: ADX > 25
    - Very Strong Trend: ADX > 50
    - Bullish Trend: +DI > -DI (uptrend with strong momentum)
    - Bearish Trend: -DI > +DI (downtrend with strong momentum)
    - ADX only measures trend strength, not direction

    **Query Parameters:**
    - target_date: Date to screen (YYYY-MM-DD, default: latest)
    - min_adx: Minimum ADX value (default: 25.0)
    - trend_direction: 'all', 'bullish', or 'bearish' (default: all)
    - limit: Max results (default: 200)

    **Returns:**
    List of stocks with ADX values, +DI/-DI indicators, and trend direction.

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/screeners/adx-trend?min_adx=40&trend_direction=bullish"
    ```

    **Reference:**
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx
    """
    # Default to latest available date
    if target_date is None:
        latest = db.query(func.max(CalculatedMetrics.date)).scalar()
        if not latest:
            raise HTTPException(status_code=404, detail="No metrics data available")
        target_date = latest

    query = db.query(
        CalculatedMetrics.symbol,
        Security.security_name,
        CalculatedMetrics.adx_14,
        CalculatedMetrics.di_plus,
        CalculatedMetrics.di_minus,
        CalculatedMetrics.is_strong_trend,
        OHLCVDaily.close,
        CalculatedMetrics.change_1m_percent,
        MarketCapHistory.market_cap
    ).join(
        Security, Security.symbol == CalculatedMetrics.symbol
    ).join(
        OHLCVDaily, and_(
            OHLCVDaily.symbol == CalculatedMetrics.symbol,
            OHLCVDaily.date == target_date
        )
    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )
    ).filter(
        CalculatedMetrics.date == target_date,
        Security.is_active == True,
        CalculatedMetrics.adx_14.isnot(None)
    )

    # Apply ADX filter
    if min_adx is not None:
        query = query.filter(CalculatedMetrics.adx_14 >= min_adx)

    # Apply trend direction filter
    if trend_direction == "bullish":
        query = query.filter(CalculatedMetrics.di_plus > CalculatedMetrics.di_minus)
    elif trend_direction == "bearish":
        query = query.filter(CalculatedMetrics.di_minus > CalculatedMetrics.di_plus)

    results = query.order_by(desc(CalculatedMetrics.adx_14)).limit(limit).all()

    stocks = []
    for row in results:
        # Determine trend direction
        if row.di_plus > row.di_minus:
            direction = "Bullish"
        elif row.di_minus > row.di_plus:
            direction = "Bearish"
        else:
            direction = "Neutral"

        stocks.append({
            "symbol": row.symbol,
            "name": row.security_name,
            "adx_14": float(row.adx_14),
            "di_plus": float(row.di_plus),
            "di_minus": float(row.di_minus),
            "trend_direction": direction,
            "is_strong_trend": bool(row.is_strong_trend),
            "close": float(row.close),
            "change_1m_percent": float(row.change_1m_percent) if row.change_1m_percent else None,
            "market_cap": float(row.market_cap) if row.market_cap else None
        })

    return {
        "screener": "ADX Trend Strength Scanner",
        "date": str(target_date),
        "total_results": len(stocks),
        "results": stocks
    }
