"""
Service for fetching historical OHLCV data from Upstox API.
"""
import requests
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.security import Security
from app.models.timeseries import OHLCVDaily
from app.models.upstox import SymbolInstrumentMapping
from app.models.metadata import MarketHoliday
from app.services.upstox.token_manager import UpstoxTokenManager
from app.services.upstox.upstox_client import UpstoxClient
import logging

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Service for fetching and storing historical OHLCV data."""

    def __init__(self, db: Session):
        self.db = db
        self.token_manager = UpstoxTokenManager(db)
        self.upstox_client = UpstoxClient(db)
        self.base_url = "https://api.upstox.com/v2"

    def fetch_historical_ohlcv(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Fetch historical OHLCV data for a single symbol.

        Args:
            symbol: Security symbol
            from_date: Start date (defaults to 5 years ago or listing_date)
            to_date: End date (defaults to today)

        Returns:
            Dict with success status, records count, and errors
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "symbol": symbol,
            "records_inserted": 0,
            "records_updated": 0,
            "date_range": {},
            "gaps_detected": [],
            "errors": []
        }

        try:
            # Get security details
            security = self.db.query(Security).filter(
                Security.symbol == symbol
            ).first()

            if not security:
                result["errors"].append(f"Security {symbol} not found")
                return result

            # Calculate date range
            if not to_date:
                to_date = datetime.now().date()

            if not from_date:
                # Use listing date or 5 years ago, whichever is later
                five_years_ago = datetime.now().date() - timedelta(days=5*365)
                if security.listing_date:
                    from_date = max(security.listing_date, five_years_ago)
                else:
                    from_date = five_years_ago

            result["date_range"] = {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }

            # Get instrument key
            from app.models.upstox import UpstoxInstrument
            mapping = self.db.query(
                SymbolInstrumentMapping, UpstoxInstrument
            ).join(
                UpstoxInstrument,
                SymbolInstrumentMapping.instrument_id == UpstoxInstrument.id
            ).join(
                Security,
                SymbolInstrumentMapping.security_id == Security.id
            ).filter(
                Security.symbol == symbol
            ).first()

            if not mapping:
                result["errors"].append(f"No instrument mapping found for {symbol}")
                return result

            instrument_key = mapping[1].instrument_key  # UpstoxInstrument is second element

            # Fetch historical candles from Upstox
            candles = self._fetch_historical_candles(
                instrument_key,
                from_date,
                to_date
            )

            if not candles:
                result["errors"].append("No candle data received from Upstox")
                return result

            # Process and insert candles
            for candle in candles:
                try:
                    # Candle format: [timestamp, open, high, low, close, volume, oi]
                    # timestamp is in ISO format
                    candle_date = datetime.fromisoformat(candle[0]).date()
                    open_price = candle[1]
                    high_price = candle[2]
                    low_price = candle[3]
                    close_price = candle[4]
                    volume = candle[5] if len(candle) > 5 else 0

                    # Check if record exists
                    existing = self.db.query(OHLCVDaily).filter(
                        OHLCVDaily.symbol == symbol,
                        OHLCVDaily.date == candle_date
                    ).first()

                    if existing:
                        # Update existing record
                        existing.open = open_price
                        existing.high = high_price
                        existing.low = low_price
                        existing.close = close_price
                        existing.volume = volume
                        result["records_updated"] += 1
                    else:
                        # Insert new record
                        new_ohlcv = OHLCVDaily(
                            symbol=symbol,
                            date=candle_date,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume
                        )
                        self.db.add(new_ohlcv)
                        result["records_inserted"] += 1

                except Exception as e:
                    result["errors"].append({
                        "candle": candle,
                        "error": str(e)
                    })
                    logger.error(f"Error processing candle for {symbol}: {str(e)}")

            # Commit all changes
            self.db.commit()

            # Detect gaps (missing trading days)
            result["gaps_detected"] = self._detect_gaps(symbol, from_date, to_date)

            result["success"] = True

        except Exception as e:
            self.db.rollback()
            result["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Fatal error in fetch_historical_ohlcv for {symbol}: {str(e)}")

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result["execution_time_ms"] = int(execution_time)

        return result

    def _fetch_historical_candles(
        self,
        instrument_key: str,
        from_date: date,
        to_date: date
    ) -> List[List]:
        """
        Fetch historical candle data from Upstox API.

        Args:
            instrument_key: Upstox instrument key
            from_date: Start date
            to_date: End date

        Returns:
            List of candles
        """
        try:
            headers = self.upstox_client.get_headers()
            if not headers:
                logger.error("Failed to get Upstox headers (token issue)")
                return []

            # Upstox date format: YYYY-MM-DD
            from_date_str = from_date.isoformat()
            to_date_str = to_date.isoformat()

            # API endpoint: /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
            url = f"{self.base_url}/historical-candle/{instrument_key}/day/{to_date_str}/{from_date_str}"

            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                candles = data.get("data", {}).get("candles", [])
                return candles
            else:
                logger.error(f"Upstox API error: {data.get('message', 'Unknown error')}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching historical candles: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching historical candles: {str(e)}")
            return []

    def _detect_gaps(self, symbol: str, from_date: date, to_date: date) -> List[str]:
        """
        Detect missing trading days in OHLCV data.

        Args:
            symbol: Security symbol
            from_date: Start date
            to_date: End date

        Returns:
            List of missing dates (ISO format strings)
        """
        try:
            # Get all OHLCV records for this symbol in date range
            records = self.db.query(OHLCVDaily.date).filter(
                OHLCVDaily.symbol == symbol,
                OHLCVDaily.date >= from_date,
                OHLCVDaily.date <= to_date
            ).order_by(OHLCVDaily.date).all()

            existing_dates = {record.date for record in records}

            # Get all market holidays
            holidays = self.db.query(MarketHoliday.holiday_date).filter(
                MarketHoliday.holiday_date >= from_date,
                MarketHoliday.holiday_date <= to_date
            ).all()
            holiday_dates = {holiday.holiday_date for holiday in holidays}

            # Check each date in range
            gaps = []
            current_date = from_date
            while current_date <= to_date:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    # Skip holidays
                    if current_date not in holiday_dates:
                        # Check if OHLCV data exists
                        if current_date not in existing_dates:
                            gaps.append(current_date.isoformat())

                current_date += timedelta(days=1)

            return gaps[:10]  # Return first 10 gaps only

        except Exception as e:
            logger.error(f"Error detecting gaps for {symbol}: {str(e)}")
            return []
