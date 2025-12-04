"""
SQLAlchemy models for all database tables.

Import all models here to ensure they're registered with Base.metadata
before Alembic migration generation.

Total Tables: 18 (15 original + 3 Upstox tables)
- Master tables (5): Security, Index, IndustryClassification, IndexConstituent, MarketHoliday
- Time-series tables (3): OHLCVDaily, MarketCapHistory, CalculatedMetrics
- Event tables (2): BulkDeal, BlockDeal
- Surveillance tables (4): SurveillanceList, SurveillanceFundamentalFlags,
                           SurveillancePriceMovement, SurveillancePriceVariation
- Metadata table (1): IngestionLog
- Upstox tables (3): UpstoxToken, UpstoxInstrument, SymbolInstrumentMapping

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
from app.models.metadata import IndustryClassification, IndexConstituent, MarketHoliday, IngestionLog
from app.models.upstox import UpstoxToken, UpstoxInstrument, SymbolInstrumentMapping

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
    'IndexConstituent',
    'MarketHoliday',
    'IngestionLog',

    # Upstox tables
    'UpstoxToken',
    'UpstoxInstrument',
    'SymbolInstrumentMapping',
]
