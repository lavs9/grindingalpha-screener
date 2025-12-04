"""
Authentication API endpoints.

This module provides endpoints for Upstox authentication and token management.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.upstox import UpstoxLoginRequest, UpstoxLoginResponse
from app.services.upstox.auth_service import automate_upstox_login
from app.services.upstox.token_manager import UpstoxTokenManager
from app.services.upstox.upstox_client import UpstoxClient
from app.models.upstox import SymbolInstrumentMapping
import requests
from datetime import datetime, timedelta


router = APIRouter()


@router.post("/upstox/login", response_model=UpstoxLoginResponse)
async def login_upstox(
    request: UpstoxLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Automate Upstox login using Playwright and TOTP.

    This endpoint uses headless browser automation to:
    1. Navigate to Upstox authorization dialog
    2. Enter mobile number
    3. Generate and enter TOTP-based OTP
    4. Enter PIN
    5. Extract authorization code
    6. Exchange code for access token
    7. Store token in database with 23:59 IST expiry

    **Returns:**
    - success: Whether authentication succeeded
    - message: Status message
    - access_token: Current access token (masked for security)
    - expires_at: Token expiration time (23:59 IST)
    - errors: List of errors if failed

    **Note:** This endpoint is for internal use only (n8n workflows, manual refresh).
    """

    result = await automate_upstox_login(
        mobile=request.mobile,
        pin=request.pin,
        totp_secret=request.totp_secret,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail={
                "message": result["message"],
                "errors": result.get("errors", [])
            }
        )

    return UpstoxLoginResponse(**result)


@router.get("/upstox/token-status")
async def get_token_status(db: Session = Depends(get_db)):
    """
    Get current Upstox token status.

    **Returns:**
    - Token metadata (masked) if active token exists
    - null if no active token

    **Use case:** Check if token refresh is needed before making API calls
    """

    token_manager = UpstoxTokenManager(db)
    token_info = token_manager.get_token_info()

    if not token_info:
        return {
            "active": False,
            "message": "No active token found. Please login."
        }

    return {
        "active": True,
        "token_info": token_info
    }


@router.get("/upstox/test-api")
async def test_upstox_api(db: Session = Depends(get_db)):
    """
    Test endpoint to verify Upstox API token works.

    Makes a simple API call to Upstox to fetch user profile.

    **Returns:**
    - Success status
    - API response data
    - Token validity confirmation
    """
    try:
        upstox_client = UpstoxClient(db)
        headers = upstox_client.get_headers()

        # Test API call: Get user profile
        response = requests.get(
            "https://api.upstox.com/v2/user/profile",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Upstox API token is valid",
                "token_valid": True,
                "user_profile": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Upstox API returned error: {response.status_code}",
                "token_valid": False,
                "error": response.text
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to test Upstox API",
                "error": str(e)
            }
        )


@router.get("/upstox/test-market-quotes")
async def test_market_quotes(
    symbol: str = "RELIANCE",
    db: Session = Depends(get_db)
):
    """
    Test endpoint to fetch market quotes for a symbol.

    **Parameters:**
    - symbol: Stock symbol (default: RELIANCE)

    **Returns:**
    - Latest market quote (OHLC, LTP, volume, etc.)
    """
    try:
        upstox_client = UpstoxClient(db)
        headers = upstox_client.get_headers()

        # Get instrument_key for symbol from mapping
        mapping = db.query(SymbolInstrumentMapping).filter(
            SymbolInstrumentMapping.symbol == symbol
        ).first()

        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No instrument mapping found for symbol: {symbol}"
            )

        instrument_key = mapping.instrument_key

        # Fetch market quote
        response = requests.get(
            f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={instrument_key}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return {
                "success": True,
                "symbol": symbol,
                "instrument_key": instrument_key,
                "quote_data": response.json()
            }
        else:
            return {
                "success": False,
                "error": response.text
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch market quote", "error": str(e)}
        )


@router.get("/upstox/test-historical-data")
async def test_historical_data(
    symbol: str = "RELIANCE",
    interval: str = "day",
    to_date: str = "2025-12-04",
    db: Session = Depends(get_db)
):
    """
    Test endpoint to fetch historical candle data.

    **Parameters:**
    - symbol: Stock symbol (default: RELIANCE)
    - interval: Candle interval (day, week, month)
    - to_date: End date (YYYY-MM-DD format)

    **Returns:**
    - Historical OHLCV data
    """
    try:
        upstox_client = UpstoxClient(db)
        headers = upstox_client.get_headers()

        # Get instrument_key for symbol
        mapping = db.query(SymbolInstrumentMapping).filter(
            SymbolInstrumentMapping.symbol == symbol
        ).first()

        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No instrument mapping found for symbol: {symbol}"
            )

        instrument_key = mapping.instrument_key

        # Calculate from_date (30 days back)
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        from_dt = to_dt - timedelta(days=30)
        from_date = from_dt.strftime("%Y-%m-%d")

        # Fetch historical data
        url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "symbol": symbol,
                "instrument_key": instrument_key,
                "interval": interval,
                "from_date": from_date,
                "to_date": to_date,
                "candles_count": len(data.get("data", {}).get("candles", [])),
                "historical_data": data
            }
        else:
            return {
                "success": False,
                "error": response.text
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch historical data", "error": str(e)}
        )


@router.get("/upstox/test-market-holidays")
async def test_market_holidays(
    date: str = "2025-12-04",
    db: Session = Depends(get_db)
):
    """
    Test endpoint to fetch market holidays.

    **Parameters:**
    - date: Date in YYYY-MM-DD format

    **Returns:**
    - List of market holidays
    """
    try:
        upstox_client = UpstoxClient(db)
        headers = upstox_client.get_headers()

        # Fetch market holidays
        response = requests.get(
            f"https://api.upstox.com/v2/market/holidays/{date}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return {
                "success": True,
                "date": date,
                "holidays": response.json()
            }
        else:
            return {
                "success": False,
                "error": response.text
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch market holidays", "error": str(e)}
        )
