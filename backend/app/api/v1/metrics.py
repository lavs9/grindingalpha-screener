"""
Metrics Calculation API Endpoints.

Provides endpoints for calculating and retrieving technical metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, timedelta

from app.database.session import get_db
from app.services.calculators.daily_metrics_calculator import DailyMetricsCalculator
from app.utils.resource_monitor import monitor_resources

router = APIRouter()


@router.post("/calculate-daily")
@monitor_resources("Daily Metrics Calculation")
async def calculate_daily_metrics(
    target_date: Optional[date] = Query(None, description="Date to calculate metrics for (default: yesterday)"),
    symbols: Optional[List[str]] = Query(None, description="Optional list of symbols (default: all active)"),
    db: Session = Depends(get_db)
):
    """
    Calculate all technical metrics for a specific date.

    This endpoint calculates 47 technical indicators for all active securities
    (or a subset if symbols are specified) for the given date.

    **Metrics Calculated:**
    - Price Changes: 1D, 1W, 1M, 3M, 6M
    - Relative Strength: RS Percentile, VARS, VARW
    - Volatility: ATR-14, ATR%, ADR%
    - Volume: RVOL, 50-day avg, volume surge flag
    - Moving Averages: EMA10, SMA20/50/100/200
    - ATR Extension: From SMA50, LoD ATR%
    - Darvas Box: 20-day high/low, position %
    - Pattern Recognition: VCP Score (1-5)
    - Stage Classification: Weinstein Stage (1-4)
    - Breadth Metrics: Universe up/down counts, McClellan
    - RRG Metrics: RS-Ratio, RS-Momentum
    - And more...

    **Query Parameters:**
    - target_date: Date to calculate for (YYYY-MM-DD). Defaults to yesterday.
    - symbols: Optional list of symbols. If not provided, calculates for all active securities.

    **Returns:**
    - success: Whether calculation completed successfully
    - target_date: Date metrics were calculated for
    - records_inserted: Number of new metric records created
    - records_updated: Number of existing records updated
    - errors: List of any errors encountered

    **Example Usage:**
    ```bash
    # Calculate for yesterday (all securities)
    curl -X POST http://localhost:8000/api/v1/metrics/calculate-daily

    # Calculate for specific date
    curl -X POST "http://localhost:8000/api/v1/metrics/calculate-daily?target_date=2024-12-24"

    # Calculate for specific symbols
    curl -X POST "http://localhost:8000/api/v1/metrics/calculate-daily?symbols=RELIANCE&symbols=TCS"
    ```

    **Note:** This endpoint requires at least 200 days of historical OHLCV data
    for each symbol to calculate SMA200 and other long-period indicators.
    """
    # Default to yesterday if no date specified
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    # Initialize calculator
    calculator = DailyMetricsCalculator(db)

    # Calculate metrics
    result = calculator.calculate_metrics_for_date(
        target_date=target_date,
        symbols=symbols
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Metrics calculation failed",
                "target_date": result["target_date"],
                "errors": result.get("errors", []),
                "records_inserted": result.get("records_inserted", 0),
                "records_updated": result.get("records_updated", 0)
            }
        )

    return {
        "message": "Metrics calculation completed successfully",
        "success": True,
        "target_date": result["target_date"],
        "records_inserted": result["records_inserted"],
        "records_updated": result["records_updated"],
        "errors": result.get("errors", [])
    }


@router.get("/latest")
async def get_latest_metrics(
    symbol: str = Query(..., description="Security symbol"),
    limit: int = Query(10, description="Number of recent dates to fetch"),
    db: Session = Depends(get_db)
):
    """
    Get latest calculated metrics for a symbol.

    **Query Parameters:**
    - symbol: Security symbol (e.g., RELIANCE, TCS)
    - limit: Number of recent dates to return (default: 10)

    **Returns:**
    List of metric records ordered by date (most recent first)

    **Example:**
    ```bash
    curl "http://localhost:8000/api/v1/metrics/latest?symbol=RELIANCE&limit=5"
    ```
    """
    from app.models.timeseries import CalculatedMetrics

    metrics = db.query(CalculatedMetrics).filter(
        CalculatedMetrics.symbol == symbol
    ).order_by(
        CalculatedMetrics.date.desc()
    ).limit(limit).all()

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for symbol {symbol}"
        )

    # Convert to dict
    result = []
    for metric in metrics:
        metric_dict = {
            "symbol": metric.symbol,
            "date": str(metric.date),
            "rs_percentile": float(metric.rs_percentile) if metric.rs_percentile else None,
            "vars_score": float(metric.vars_score) if metric.vars_score else None,
            "atr_percent": float(metric.atr_percent) if metric.atr_percent else None,
            "rvol": float(metric.rvol) if metric.rvol else None,
            "stage": metric.stage,
            "stage_detail": metric.stage_detail,
            "vcp_score": metric.vcp_score,
            "is_ma_stacked": metric.is_ma_stacked,
            "change_1d_percent": float(metric.change_1d_percent) if metric.change_1d_percent else None,
            "change_1w_percent": float(metric.change_1w_percent) if metric.change_1w_percent else None,
            "change_1m_percent": float(metric.change_1m_percent) if metric.change_1m_percent else None,
        }
        result.append(metric_dict)

    return {
        "symbol": symbol,
        "count": len(result),
        "metrics": result
    }
