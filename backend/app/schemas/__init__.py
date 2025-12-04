"""
Pydantic schemas for API request/response validation.

Additional schemas will be created in Phase 1.2+ as endpoints are implemented.
"""
from app.schemas.security import (
    SecurityBase,
    SecurityCreate,
    SecurityUpdate,
    SecurityResponse,
    IndexBase,
    IndexCreate,
    IndexResponse,
)
from app.schemas.ohlcv import (
    OHLCVBase,
    OHLCVCreate,
    OHLCVResponse,
    OHLCVBulkCreate,
)
from app.schemas.surveillance import (
    SurveillanceListBase,
    SurveillanceListCreate,
    SurveillanceListResponse,
    SurveillanceFundamentalFlagsBase,
    SurveillanceFundamentalFlagsCreate,
    SurveillanceFundamentalFlagsResponse,
    SurveillancePriceMovementBase,
    SurveillancePriceMovementCreate,
    SurveillancePriceMovementResponse,
    SurveillancePriceVariationBase,
    SurveillancePriceVariationCreate,
    SurveillancePriceVariationResponse,
    SurveillanceAggregatedResponse,
    SurveillanceIngestionRequest,
    SurveillanceIngestionResponse,
)
from app.schemas.industry import (
    IndustryClassificationBase,
    IndustryClassificationCreate,
    IndustryClassificationResponse,
    IndexConstituentBase,
    IndexConstituentCreate,
    IndexConstituentResponse,
    IndustryIngestionRequest,
    IndustryIngestionResponse,
    IndexConstituentListResponse,
    IndustryStatsResponse,
)
from app.schemas.upstox import (
    UpstoxLoginRequest,
    UpstoxLoginResponse,
    UpstoxInstrumentBase,
    UpstoxInstrumentResponse,
    InstrumentIngestionResponse,
    SymbolInstrumentMappingBase,
    SymbolInstrumentMappingResponse,
    MappingStatsResponse,
)

__all__ = [
    # Security schemas
    'SecurityBase',
    'SecurityCreate',
    'SecurityUpdate',
    'SecurityResponse',

    # Index schemas
    'IndexBase',
    'IndexCreate',
    'IndexResponse',

    # OHLCV schemas
    'OHLCVBase',
    'OHLCVCreate',
    'OHLCVResponse',
    'OHLCVBulkCreate',

    # Surveillance schemas
    'SurveillanceListBase',
    'SurveillanceListCreate',
    'SurveillanceListResponse',
    'SurveillanceFundamentalFlagsBase',
    'SurveillanceFundamentalFlagsCreate',
    'SurveillanceFundamentalFlagsResponse',
    'SurveillancePriceMovementBase',
    'SurveillancePriceMovementCreate',
    'SurveillancePriceMovementResponse',
    'SurveillancePriceVariationBase',
    'SurveillancePriceVariationCreate',
    'SurveillancePriceVariationResponse',
    'SurveillanceAggregatedResponse',
    'SurveillanceIngestionRequest',
    'SurveillanceIngestionResponse',

    # Industry classification schemas
    'IndustryClassificationBase',
    'IndustryClassificationCreate',
    'IndustryClassificationResponse',
    'IndexConstituentBase',
    'IndexConstituentCreate',
    'IndexConstituentResponse',
    'IndustryIngestionRequest',
    'IndustryIngestionResponse',
    'IndexConstituentListResponse',
    'IndustryStatsResponse',

    # Upstox schemas
    'UpstoxLoginRequest',
    'UpstoxLoginResponse',
    'UpstoxInstrumentBase',
    'UpstoxInstrumentResponse',
    'InstrumentIngestionResponse',
    'SymbolInstrumentMappingBase',
    'SymbolInstrumentMappingResponse',
    'MappingStatsResponse',
]
