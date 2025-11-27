"""
SQLAlchemy models for all database tables.

Import all models here to ensure they're registered with Base.metadata
before Alembic migration generation.

Total Tables: 14 (11 original + 4 surveillance tables - 1 old surveillance table)
- Master tables (4): Security, Index, IndustryClassification, MarketHoliday
- Time-series tables (3): OHLCVDaily, MarketCapHistory, CalculatedMetrics
- Event tables (2): BulkDeal, BlockDeal
- Surveillance tables (4): SurveillanceList, SurveillanceFundamentalFlags,
                           SurveillancePriceMovement, SurveillancePriceVariation
- Metadata table (1): IngestionLog

Schema Status: BASELINE - Models will be refined as we process actual data in Phase 1.2+
Surveillance models follow .claude/file-formats-surveillance.md specification
"""
from app.models.security import Security, Index, SecurityType
from app.models.timeseries import OHLCVDaily, MarketCapHistory, CalculatedMetrics
from app.models.events import BulkDeal, BlockDeal
from app.models.surveillance import (
    SurveillanceList,
    SurveillanceFundamentalFlags,
    SurveillancePriceMovement,
    SurveillancePriceVariation
)
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

    # Surveillance tables (4-table normalized design)
    'SurveillanceList',
    'SurveillanceFundamentalFlags',
    'SurveillancePriceMovement',
    'SurveillancePriceVariation',

    # Metadata tables
    'IndustryClassification',
    'MarketHoliday',
    'IngestionLog',
]
