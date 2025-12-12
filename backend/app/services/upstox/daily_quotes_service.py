"""
Service for fetching daily OHLCV data from Upstox API.
"""
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.security import Security
from app.models.timeseries import OHLCVDaily
from app.models.upstox import SymbolInstrumentMapping
from app.models.metadata import IngestionLog
from app.services.upstox.token_manager import UpstoxTokenManager
from app.services.upstox.upstox_client import UpstoxClient
import logging

logger = logging.getLogger(__name__)


class DailyQuotesService:
    """Service for fetching and storing daily OHLCV data."""

    def __init__(self, db: Session):
        self.db = db
        self.token_manager = UpstoxTokenManager(db)
        self.upstox_client = UpstoxClient(db)
        self.base_url = "https://api.upstox.com/v2"

    def fetch_daily_ohlcv(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch daily OHLCV data for multiple securities from Upstox.

        Args:
            symbols: Optional list of symbols to fetch. If None, fetches all active securities.

        Returns:
            Dict with success status, counts, and errors
        """
        start_time = datetime.now()
        results = {
            "success": True,
            "total_symbols": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        try:
            # Get symbols to process
            if symbols:
                securities_query = self.db.query(Security).filter(
                    Security.symbol.in_(symbols),
                    Security.is_active == True
                )
            else:
                securities_query = self.db.query(Security).filter(
                    Security.is_active == True
                )

            securities = securities_query.all()
            results["total_symbols"] = len(securities)

            if not securities:
                results["success"] = False
                results["errors"].append("No active securities found")
                return results

            # Get instrument mappings
            from app.models.upstox import UpstoxInstrument
            symbols_list = [sec.symbol for sec in securities]
            mappings = self.db.query(
                SymbolInstrumentMapping, UpstoxInstrument, Security
            ).join(
                UpstoxInstrument,
                SymbolInstrumentMapping.instrument_id == UpstoxInstrument.id
            ).join(
                Security,
                SymbolInstrumentMapping.security_id == Security.id
            ).filter(
                SymbolInstrumentMapping.security_id.in_([sec.id for sec in securities])
            ).all()

            # Create symbol to instrument_key mapping
            symbol_to_instrument = {}
            for mapping, instrument, security in mappings:
                symbol_to_instrument[security.symbol] = instrument.instrument_key

            # Prepare instrument keys for batch request
            instrument_keys = list(symbol_to_instrument.values())

            if not instrument_keys:
                results["success"] = False
                results["errors"].append("No instrument mappings found for securities")
                return results

            # Fetch quotes from Upstox (batch request)
            quotes_data = self._fetch_market_quotes(instrument_keys)

            if not quotes_data:
                results["success"] = False
                results["errors"].append("Failed to fetch quotes from Upstox")
                return results

            # Process each quote and insert to database
            for security in securities:
                try:
                    instrument_key = symbol_to_instrument.get(security.symbol)
                    if not instrument_key:
                        results["failed"] += 1
                        results["errors"].append({
                            "symbol": security.symbol,
                            "error": "No instrument mapping found"
                        })
                        continue

                    quote = quotes_data.get(instrument_key)
                    if not quote:
                        results["failed"] += 1
                        results["errors"].append({
                            "symbol": security.symbol,
                            "error": "Quote not found in Upstox response"
                        })
                        continue

                    # Extract OHLCV data
                    ohlc = quote.get("ohlc", {})
                    if not ohlc:
                        results["failed"] += 1
                        results["errors"].append({
                            "symbol": security.symbol,
                            "error": "No OHLC data in quote"
                        })
                        continue

                    # Insert or update OHLCV data
                    self._upsert_ohlcv(security.symbol, ohlc, quote)
                    results["successful"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "symbol": security.symbol,
                        "error": str(e)
                    })
                    logger.error(f"Error processing {security.symbol}: {str(e)}")

            # Commit all changes
            self.db.commit()

            # Update success status
            if results["failed"] > 0:
                results["success"] = False

        except Exception as e:
            self.db.rollback()
            results["success"] = False
            results["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Fatal error in fetch_daily_ohlcv: {str(e)}")

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        results["execution_time_ms"] = int(execution_time)

        # Log to ingestion_logs table
        self._log_ingestion(results, source="upstox_daily")

        return results

    def _fetch_market_quotes(self, instrument_keys: List[str]) -> Dict[str, Dict]:
        """
        Fetch market quotes from Upstox API for multiple instruments.

        Args:
            instrument_keys: List of instrument keys

        Returns:
            Dict mapping instrument_key to quote data
        """
        try:
            headers = self.upstox_client.get_headers()
            if not headers:
                logger.error("Failed to get Upstox headers (token issue)")
                return {}

            # Upstox allows comma-separated instrument keys
            # Batch size: 500 instruments per request (Upstox limit)
            batch_size = 500
            all_quotes = {}

            for i in range(0, len(instrument_keys), batch_size):
                batch = instrument_keys[i:i + batch_size]
                instrument_param = ",".join(batch)

                url = f"{self.base_url}/market-quote/quotes"
                params = {"instrument_key": instrument_param}

                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                if data.get("status") == "success":
                    quotes = data.get("data", {})
                    all_quotes.update(quotes)
                else:
                    logger.error(f"Upstox API error: {data.get('message', 'Unknown error')}")

            return all_quotes

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching market quotes: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching market quotes: {str(e)}")
            return {}

    def _upsert_ohlcv(self, symbol: str, ohlc: Dict, quote: Dict):
        """
        Insert or update OHLCV data for a symbol.

        Args:
            symbol: Security symbol
            ohlc: OHLC data from quote
            quote: Full quote data
        """
        # Get today's date
        today = datetime.now().date()

        # Check if record exists
        existing = self.db.query(OHLCVDaily).filter(
            OHLCVDaily.symbol == symbol,
            OHLCVDaily.date == today
        ).first()

        # Extract data
        open_price = ohlc.get("open")
        high_price = ohlc.get("high")
        low_price = ohlc.get("low")
        close_price = ohlc.get("close")
        volume = quote.get("volume", 0)

        # VWAP and other fields
        vwap = quote.get("average_price") or quote.get("vwap")
        upper_circuit = quote.get("upper_circuit_limit")
        lower_circuit = quote.get("lower_circuit_limit")

        # 52-week high/low
        week_52_high = quote.get("ohlc", {}).get("high")  # This might need adjustment based on actual response
        week_52_low = quote.get("ohlc", {}).get("low")

        if existing:
            # Update existing record
            existing.open = open_price
            existing.high = high_price
            existing.low = low_price
            existing.close = close_price
            existing.volume = volume
            existing.vwap = vwap
            existing.upper_circuit = upper_circuit
            existing.lower_circuit = lower_circuit
            existing.week_52_high = week_52_high
            existing.week_52_low = week_52_low
        else:
            # Insert new record
            new_ohlcv = OHLCVDaily(
                symbol=symbol,
                date=today,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                vwap=vwap,
                upper_circuit=upper_circuit,
                lower_circuit=lower_circuit,
                week_52_high=week_52_high,
                week_52_low=week_52_low
            )
            self.db.add(new_ohlcv)

    def _log_ingestion(self, result: Dict[str, Any], source: str):
        """
        Log ingestion results to ingestion_logs table.

        Args:
            result: Result dictionary from ingestion
            source: Source identifier (e.g., 'upstox_daily')
        """
        try:
            status = "success" if result["success"] else "failure"
            if result.get("failed", 0) > 0 and result.get("successful", 0) > 0:
                status = "partial"

            log_entry = IngestionLog(
                source=source,
                status=status,
                records_fetched=result.get("total_symbols", 0),
                records_inserted=result.get("successful", 0),
                records_updated=0,  # Daily quotes always upsert
                records_failed=result.get("failed", 0),
                errors=result.get("errors", [])[:50],  # Limit to first 50 errors
                execution_time_ms=result.get("execution_time_ms", 0)
            )

            self.db.add(log_entry)
            self.db.commit()
            logger.info(f"Ingestion logged to database: source={source}, status={status}")

        except Exception as e:
            logger.error(f"Failed to log ingestion to database: {str(e)}")
            self.db.rollback()
