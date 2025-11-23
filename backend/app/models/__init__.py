"""
SQLAlchemy models for all database tables.

Import all models here to ensure they're registered with Base.metadata
before Alembic migration generation.

Total Tables: 11
- Master tables (4): Security, Index, IndustryClassification, MarketHoliday
- Time-series tables (3): OHLCVDaily, MarketCapHistory, CalculatedMetrics
- Event tables (3): BulkDeal, BlockDeal, SurveillanceMeasure
- Metadata table (1): IngestionLog

Schema Status: BASELINE - Models will be refined as we process actual data in Phase 1.2+
"""
from app.models.security import Security, Index, SecurityType
from app.models.timeseries import OHLCVDaily, MarketCapHistory, CalculatedMetrics
from app.models.events import BulkDeal, BlockDeal, SurveillanceMeasure
from app.models.metadata import IndustryClassification, MarketHoliday, IngestionLog

__all__ = [
    # Master tables
    'Security',
    'Index',
    'SecurityType',

    # Time-series tables
    'OHLCVDaily',
    'MarketCapHistory',
    'CalculatedMetrics',

    # Event tables
    'BulkDeal',
    'BlockDeal',
    'SurveillanceMeasure',

    # Metadata tables
    'IndustryClassification',
    'MarketHoliday',
    'IngestionLog',
]
