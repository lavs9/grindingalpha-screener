"""
Upstox API Client - Helper for making authenticated requests.

This module provides a simple client for making Upstox API calls
with automatic token management.
"""

from sqlalchemy.orm import Session
from typing import Dict
from app.services.upstox.token_manager import UpstoxTokenManager


class UpstoxClient:
    """Helper class for making authenticated Upstox API calls."""

    def __init__(self, db: Session):
        """
        Initialize Upstox client.

        Args:
            db: Database session for token retrieval
        """
        self.db = db
        self.token_manager = UpstoxTokenManager(db)

    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with current valid Bearer token.

        Returns:
            Dict with Authorization and Accept headers

        Raises:
            Exception: If no valid token is available
        """
        token = self.token_manager.get_active_token()

        if not token:
            raise Exception(
                "No valid Upstox token available. Please login first using "
                "POST /api/v1/auth/upstox/login"
            )

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def is_token_valid(self) -> bool:
        """
        Check if a valid token exists.

        Returns:
            True if valid token exists, False otherwise
        """
        return not self.token_manager.is_token_expired()

    def get_token_info(self) -> Dict:
        """
        Get current token metadata.

        Returns:
            Dict with token info or None if no active token
        """
        return self.token_manager.get_token_info()
