"""
Upstox Token Manager - Handles token lifecycle and storage.

This module manages Upstox access tokens with daily expiry (23:59 IST).
"""

from sqlalchemy.orm import Session
from datetime import datetime
import pytz
from typing import Optional
from app.models.upstox import UpstoxToken


class UpstoxTokenManager:
    """Manages Upstox token lifecycle (daily expiry at 23:59 IST)."""

    def __init__(self, db: Session):
        self.db = db
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_active_token(self) -> Optional[str]:
        """
        Get current valid access token.

        Returns:
            Access token string if valid token exists, None otherwise
        """
        now = datetime.now(self.ist)

        token_record = self.db.query(UpstoxToken).filter(
            UpstoxToken.is_active == True,
            UpstoxToken.expires_at > now
        ).order_by(UpstoxToken.created_at.desc()).first()

        if token_record:
            # Update last_used_at
            token_record.last_used_at = now
            self.db.commit()
            return token_record.access_token

        return None

    def store_token(
        self,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> UpstoxToken:
        """
        Store new token with expiry at 23:59 IST today.

        Args:
            access_token: JWT access token from Upstox OAuth
            refresh_token: Optional refresh token

        Returns:
            Newly created UpstoxToken record
        """
        now = datetime.now(self.ist)

        # Calculate expiry: 23:59:59 today IST
        expires_at = now.replace(hour=23, minute=59, second=59, microsecond=0)

        # Deactivate old tokens
        self.db.query(UpstoxToken).filter(
            UpstoxToken.is_active == True
        ).update({"is_active": False})

        # Create new token
        new_token = UpstoxToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            is_active=True
        )

        self.db.add(new_token)
        self.db.commit()
        self.db.refresh(new_token)

        return new_token

    def is_token_expired(self) -> bool:
        """
        Check if current token is expired.

        Returns:
            True if token is expired or doesn't exist, False otherwise
        """
        token = self.get_active_token()
        return token is None

    def get_token_info(self) -> Optional[dict]:
        """
        Get current token metadata (without exposing full token).

        Returns:
            Dict with token info or None if no active token
        """
        now = datetime.now(self.ist)

        token_record = self.db.query(UpstoxToken).filter(
            UpstoxToken.is_active == True,
            UpstoxToken.expires_at > now
        ).order_by(UpstoxToken.created_at.desc()).first()

        if not token_record:
            return None

        return {
            "id": token_record.id,
            "token_preview": token_record.access_token[:20] + "...",  # Masked
            "expires_at": token_record.expires_at,
            "last_used_at": token_record.last_used_at,
            "created_at": token_record.created_at,
            "is_active": token_record.is_active
        }
