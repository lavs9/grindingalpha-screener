"""
Index Historical OHLCV Data Service.

Handles ingestion of historical daily candle data for NSE indices from Upstox API.
"""
import time
import requests
from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.timeseries import IndexOHLCVDaily
from app.models.upstox import UpstoxInstrument
from app.services.upstox.token_manager import UpstoxTokenManager
from app.services.upstox.upstox_client import UpstoxClient


class IndexHistoricalService:
    """Service for ingesting historical OHLCV data for NSE indices."""

    def __init__(self, db: Session):
        self.db = db
        self.token_manager = UpstoxTokenManager(db)
        self.upstox_client = UpstoxClient(db)
        self.base_url = "https://api.upstox.com/v2"

    def ingest_historical_ohlcv_batch(
        self,
        index_symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 20
    ) -> Dict:
        """
        Ingest historical OHLCV data for multiple indices.

        Args:
            index_symbols: List of index symbols (e.g., ['NIFTY 50', 'NIFTY BANK'])
            start_date: Start date for historical data (default: 5 years ago)
            end_date: End date (default: yesterday)
            batch_size: Number of indices to process in parallel

        Returns:
            Dict with statistics and errors
        """
        start_time = time.time()

        # Default dates
        if end_date is None:
            end_date = date.today() - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=365 * 5)  # 5 years

        # Get token
        token = self.token_manager.get_active_token()
        if not token:
            return {
                "success": False,
                "indices_processed": 0,
                "records_inserted": 0,
                "records_updated": 0,
                "indices_failed": 0,
                "errors": ["No valid Upstox token available"],
                "execution_time_ms": 0
            }

        # Token is managed by upstox_client

        # Get list of indices
        if index_symbols:
            indices_query = self.db.query(
                UpstoxInstrument.symbol,
                UpstoxInstrument.instrument_key
            ).filter(
                UpstoxInstrument.exchange == 'NSE',
                UpstoxInstrument.instrument_type == 'INDEX',
                UpstoxInstrument.symbol.in_(index_symbols)
            )
        else:
            indices_query = self.db.query(
                UpstoxInstrument.symbol,
                UpstoxInstrument.instrument_key
            ).filter(
                UpstoxInstrument.exchange == 'NSE',
                UpstoxInstrument.instrument_type == 'INDEX'
            )

        indices = [(row.symbol, row.instrument_key) for row in indices_query.all()]

        if not indices:
            return {
                "success": False,
                "indices_processed": 0,
                "records_inserted": 0,
                "records_updated": 0,
                "indices_failed": 0,
                "errors": ["No indices found"],
                "execution_time_ms": 0
            }

        # Process indices
        total_inserted = 0
        total_updated = 0
        failed_count = 0
        errors = []

        for i, (symbol, instrument_key) in enumerate(indices):
            try:
                result = self._fetch_and_insert_ohlcv(
                    symbol=symbol,
                    instrument_key=instrument_key,
                    start_date=start_date,
                    end_date=end_date
                )

                total_inserted += result["inserted"]
                total_updated += result["updated"]

                if i % 10 == 0:
                    print(f"Progress: {i}/{len(indices)} indices processed")

                # Rate limiting (1 call per second)
                time.sleep(1)

            except Exception as e:
                failed_count += 1
                errors.append(f"{symbol}: {str(e)}")

        execution_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "indices_processed": len(indices) - failed_count,
            "records_inserted": total_inserted,
            "records_updated": total_updated,
            "indices_failed": failed_count,
            "errors": errors,
            "execution_time_ms": execution_time
        }

    def _fetch_and_insert_ohlcv(
        self,
        symbol: str,
        instrument_key: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Fetch historical candles for one index and insert into database."""
        # Fetch from Upstox API
        headers = self.upstox_client.get_headers()
        if not headers:
            return {"inserted": 0, "updated": 0}

        # API endpoint: /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        url = f"{self.base_url}/historical-candle/{instrument_key}/day/{end_date.isoformat()}/{start_date.isoformat()}"

        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success" or 'data' not in data or 'candles' not in data['data']:
                return {"inserted": 0, "updated": 0}

            candles = data['data']['candles']
        except Exception as e:
            print(f"Error fetching candles for {symbol}: {e}")
            return {"inserted": 0, "updated": 0}

        # Parse and insert candles
        inserted = 0
        updated = 0

        for candle in candles:
            try:
                # Candle format: [timestamp, open, high, low, close, volume, oi]
                candle_date = date.fromisoformat(candle[0].split('T')[0])

                # Check if record exists
                existing = self.db.query(IndexOHLCVDaily).filter(
                    IndexOHLCVDaily.symbol == symbol,
                    IndexOHLCVDaily.date == candle_date
                ).first()

                if existing:
                    # Update
                    existing.open = candle[1]
                    existing.high = candle[2]
                    existing.low = candle[3]
                    existing.close = candle[4]
                    existing.volume = candle[5] if len(candle) > 5 else None
                    updated += 1
                else:
                    # Insert
                    new_record = IndexOHLCVDaily(
                        symbol=symbol,
                        date=candle_date,
                        open=candle[1],
                        high=candle[2],
                        low=candle[3],
                        close=candle[4],
                        volume=candle[5] if len(candle) > 5 else None
                    )
                    self.db.add(new_record)
                    inserted += 1

            except Exception as e:
                print(f"Error processing candle for {symbol}: {e}")
                continue

        # Commit in batches
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

        return {"inserted": inserted, "updated": updated}
