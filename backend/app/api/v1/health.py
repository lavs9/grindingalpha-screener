"""
Health check and status endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.session import check_db_connection, get_db
from app.core.config import settings
from app.models.metadata import MarketHoliday
import pytz


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check with database status."""
    status: str
    environment: str
    database_connected: bool
    message: str


class MarketStatusResponse(BaseModel):
    """Market trading status response."""
    is_market_open: bool
    is_trading_day: bool
    current_time: str
    next_open: str | None
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        HealthResponse: Service status
    """
    return HealthResponse(
        status="healthy",
        message="Stock Screener API is running",
        environment=settings.ENV
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check including database connectivity.

    Returns:
        DetailedHealthResponse: Detailed service status

    Raises:
        HTTPException: If critical services are down
    """
    db_connected = check_db_connection()

    if not db_connected:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

    return DetailedHealthResponse(
        status="healthy",
        environment=settings.ENV,
        database_connected=db_connected,
        message="All services are operational"
    )


@router.get("/health/market-status", response_model=MarketStatusResponse)
async def market_status(db: Session = Depends(get_db)):
    """
    Check if the market is currently open and if today is a trading day.

    Market hours: Mon-Fri, 9:15 AM - 3:30 PM IST (except holidays)

    Args:
        db: Database session

    Returns:
        MarketStatusResponse: Current market status with next open time
    """
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_date = current_time.date()

    # Check if today is weekend (Saturday=5, Sunday=6)
    is_weekend = current_time.weekday() >= 5

    # Check if today is a market holiday
    holiday = db.query(MarketHoliday).filter(
        MarketHoliday.holiday_date == current_date
    ).first()
    is_holiday = holiday is not None

    # Check if market is currently open (9:15 AM - 3:30 PM IST on trading days)
    market_open_time = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close_time = current_time.replace(hour=15, minute=30, second=0, microsecond=0)

    is_trading_day = not (is_weekend or is_holiday)
    is_market_open = (
        is_trading_day and
        market_open_time <= current_time <= market_close_time
    )

    # Calculate next market open time
    next_open = None
    if is_market_open:
        message = "Market is currently open for trading"
    elif is_trading_day and current_time < market_open_time:
        next_open = market_open_time.isoformat()
        message = f"Market opens today at 9:15 AM IST"
    else:
        # Find next trading day
        check_date = current_date + timedelta(days=1)
        days_checked = 0
        while days_checked < 14:  # Check up to 2 weeks ahead
            # Skip weekends
            if check_date.weekday() < 5:
                # Check if it's a holiday
                holiday_check = db.query(MarketHoliday).filter(
                    MarketHoliday.holiday_date == check_date
                ).first()
                if not holiday_check:
                    next_open_datetime = ist.localize(
                        datetime.combine(check_date, datetime.min.time())
                    ).replace(hour=9, minute=15)
                    next_open = next_open_datetime.isoformat()
                    break
            check_date += timedelta(days=1)
            days_checked += 1

        if is_holiday:
            message = f"Market closed - {holiday.holiday_name}"
        elif is_weekend:
            message = "Market closed - Weekend"
        elif current_time > market_close_time:
            message = "Market closed for the day"
        else:
            message = "Market is closed"

    return MarketStatusResponse(
        is_market_open=is_market_open,
        is_trading_day=is_trading_day,
        current_time=current_time.isoformat(),
        next_open=next_open,
        message=message
    )
