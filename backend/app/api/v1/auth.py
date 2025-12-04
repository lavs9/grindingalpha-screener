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
