"""
Batch service for fetching historical OHLCV data from Upstox API.

This service handles bulk historical data ingestion for multiple securities with:
- Batch processing (50 symbols per batch to avoid rate limits)
- Resource monitoring
- Ingestion log tracking
- Error handling and retry logic
"""
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.security import Security
from app.models.timeseries import OHLCVDaily
from app.models.upstox import SymbolInstrumentMapping, UpstoxInstrument
from app.models.metadata import IngestionLog
from app.services.upstox.historical_service import HistoricalDataService
import logging

logger = logging.getLogger(__name__)


class BatchHistoricalService:
    """Service for batch processing historical OHLCV data."""

    def __init__(self, db: Session):
        self.db = db
        self.historical_service = HistoricalDataService(db)

    def fetch_batch_historical_ohlcv(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch historical OHLCV data for multiple symbols in batches.

        Args:
            symbols: Optional list of symbols. If None, fetches all active securities.
            start_date: Start date (defaults to 5 years ago)
            end_date: End date (defaults to yesterday)
            batch_size: Number of symbols to process per batch (default: 50)

        Returns:
            Dict with success status, counts, and errors
        """
        start_time = datetime.now()
        result = {
            "success": True,
            "symbols_processed": 0,
            "records_inserted": 0,
            "records_updated": 0,
            "symbols_failed": 0,
            "errors": [],
            "execution_time_ms": 0
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
            total_securities = len(securities)

            if not securities:
                result["success"] = False
                result["errors"].append("No active securities found")
                self._log_ingestion(result, source="upstox_historical")
                return result

            logger.info(f"Starting batch historical OHLCV ingestion for {total_securities} securities")

            # Calculate default date range
            if not end_date:
                end_date = (datetime.now() - timedelta(days=1)).date()  # Yesterday

            if not start_date:
                start_date = datetime.now().date() - timedelta(days=5*365)  # 5 years ago

            # Process in batches
            for i in range(0, total_securities, batch_size):
                batch = securities[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_securities + batch_size - 1) // batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} symbols)")

                for security in batch:
                    try:
                        # Fetch historical data for this symbol
                        symbol_result = self.historical_service.fetch_historical_ohlcv(
                            symbol=security.symbol,
                            from_date=start_date,
                            to_date=end_date
                        )

                        if symbol_result["success"]:
                            result["symbols_processed"] += 1
                            result["records_inserted"] += symbol_result.get("records_inserted", 0)
                            result["records_updated"] += symbol_result.get("records_updated", 0)
                            logger.info(f"✓ {security.symbol}: {symbol_result['records_inserted']} inserted, {symbol_result['records_updated']} updated")
                        else:
                            result["symbols_failed"] += 1
                            result["errors"].append({
                                "symbol": security.symbol,
                                "errors": symbol_result.get("errors", [])
                            })
                            logger.warning(f"✗ {security.symbol}: Failed - {symbol_result.get('errors')}")

                    except Exception as e:
                        result["symbols_failed"] += 1
                        result["errors"].append({
                            "symbol": security.symbol,
                            "error": str(e)
                        })
                        logger.error(f"✗ {security.symbol}: Exception - {str(e)}")

                # Add delay between batches to respect rate limits
                if i + batch_size < total_securities:
                    logger.info(f"Batch {batch_num} complete. Waiting 2 seconds before next batch...")
                    time.sleep(2)

            # Determine overall success
            if result["symbols_failed"] > 0:
                result["success"] = False if result["symbols_processed"] == 0 else True  # Partial success

            logger.info(f"Batch historical OHLCV ingestion complete: {result['symbols_processed']} succeeded, {result['symbols_failed']} failed")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Fatal error: {str(e)}")
            logger.error(f"Fatal error in batch historical OHLCV ingestion: {str(e)}")

        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result["execution_time_ms"] = int(execution_time)

        # Log to ingestion_logs table
        self._log_ingestion(result, source="upstox_historical")

        return result

    def _log_ingestion(self, result: Dict[str, Any], source: str):
        """
        Log ingestion results to ingestion_logs table.

        Args:
            result: Result dictionary from ingestion
            source: Source identifier (e.g., 'upstox_historical', 'upstox_daily')
        """
        try:
            status = "success" if result["success"] else "failure"
            if result.get("symbols_failed", 0) > 0 and result.get("symbols_processed", 0) > 0:
                status = "partial"

            log_entry = IngestionLog(
                source=source,
                status=status,
                records_fetched=result.get("symbols_processed", 0) + result.get("symbols_failed", 0),
                records_inserted=result.get("records_inserted", 0),
                records_updated=result.get("records_updated", 0),
                records_failed=result.get("symbols_failed", 0),
                errors=result.get("errors", [])[:50],  # Limit to first 50 errors
                execution_time_ms=result.get("execution_time_ms", 0)
            )

            self.db.add(log_entry)
            self.db.commit()
            logger.info(f"Ingestion logged to database: source={source}, status={status}")

        except Exception as e:
            logger.error(f"Failed to log ingestion to database: {str(e)}")
            self.db.rollback()
