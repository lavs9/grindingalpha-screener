"""
Upstox Authentication Service - Automates login using Playwright.

This module handles Upstox OAuth2 authentication flow with:
- Playwright browser automation for login
- TOTP-based 2FA
- Token exchange and storage
"""

from playwright.async_api import async_playwright
import pyotp
import requests
import urllib.parse
from typing import Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.upstox.token_manager import UpstoxTokenManager


async def automate_upstox_login(
    mobile: str,
    pin: str,
    totp_secret: str,
    db: Session
) -> Dict:
    """
    Automate Upstox login using Playwright and TOTP.

    Args:
        mobile: Mobile number for Upstox account
        pin: 4-6 digit PIN
        totp_secret: TOTP secret key for 2FA
        db: Database session

    Returns:
        Dict with success status, message, access_token, expires_at, errors
    """

    result = {
        "success": False,
        "message": "",
        "access_token": None,
        "expires_at": None,
        "errors": []
    }

    async def run_automation():
        """Run Playwright automation to get authorization code."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                # Step 1: Navigate to authorization dialog
                endpoint = (
                    "https://api.upstox.com/v2/login/authorization/dialog"
                    f"?response_type=code"
                    f"&client_id={settings.UPSTOX_API_KEY}"
                    f"&redirect_uri={settings.UPSTOX_REDIRECT_URI}"
                )
                await page.goto(endpoint, wait_until="domcontentloaded", timeout=30000)

                # Step 2: Enter mobile number
                await page.wait_for_selector("#mobileNum", timeout=30000)
                await page.fill("#mobileNum", mobile)
                await page.click("#getOtp")

                # Step 3: Generate and enter TOTP
                otp = pyotp.TOTP(totp_secret).now()
                await page.wait_for_selector("#otpNum", timeout=30000)
                await page.fill("#otpNum", otp)
                await page.click("#continueBtn")

                # Step 4: Enter PIN
                await page.wait_for_selector("#pinCode", timeout=30000)
                await page.fill("#pinCode", pin)
                await page.click("#pinContinueBtn")
                await page.wait_for_timeout(2000)

                # Step 5: Wait for redirect and extract code
                await page.wait_for_url(f"{settings.UPSTOX_REDIRECT_URI}*", timeout=30000)
                url = page.url

                await browser.close()
                return url

            except Exception as e:
                await browser.close()
                raise Exception(f"Playwright automation failed: {str(e)}")

    try:
        # Run Playwright automation
        redirect_url = await run_automation()

        # Extract authorization code
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(redirect_url)
        code = parse_qs(parsed.query).get("code", [None])[0]

        if not code:
            result["errors"].append("No authorization code found in redirect URL")
            result["message"] = "Authorization code extraction failed"
            return result

        # Exchange code for tokens
        token_url = "https://api.upstox.com/v2/login/authorization/token"
        payload = {
            "code": code,
            "client_id": settings.UPSTOX_API_KEY,
            "client_secret": settings.UPSTOX_API_SECRET,
            "redirect_uri": settings.UPSTOX_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        encoded_payload = urllib.parse.urlencode(payload)
        resp = requests.post(token_url, data=encoded_payload, headers=headers, timeout=30)
        resp.raise_for_status()

        tokens = resp.json()

        # Store token in database
        token_manager = UpstoxTokenManager(db)
        token_record = token_manager.store_token(
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token")
        )

        result["success"] = True
        result["message"] = "Login successful"
        result["access_token"] = token_record.access_token[:20] + "..."  # Masked
        result["expires_at"] = token_record.expires_at

    except requests.exceptions.HTTPError as e:
        result["errors"].append(f"Token exchange failed: {e.response.status_code} - {e.response.text}")
        result["message"] = "Token exchange failed"
    except Exception as e:
        result["errors"].append(str(e))
        result["message"] = "Login failed"

    return result
