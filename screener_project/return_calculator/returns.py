from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, desc, asc
from ..database.db_helper import get_db_context
from ..indexes_models.nifty_bank import NiftyBank

# Map index names (normalised) to SQLAlchemy models
INDEX_MODEL_MAP = {
    "nifty bank": NiftyBank,
    "nifty_bank": NiftyBank,
}

# Timeframe -> relativedelta for the look-back
TIMEFRAME_DELTAS = {
    "1w": relativedelta(days=7),
    "1m": relativedelta(months=1),
    "3m": relativedelta(months=3),
    "6m": relativedelta(months=6),
    "1y": relativedelta(years=1),
    "3y": relativedelta(years=3),
    "5y": relativedelta(years=5),
}

# Approximate row limits to grab in a single query (buffer included for holidays/weekends)
TIMEFRAME_ROW_LIMITS = {
    "1w": 15,   # < 30 trading days covers 1w comfortably
    "1m": 60,   # 1m ‑> 60 rows (31 + buffer)
    "3m": 120,  # 3m ‑> 180 rows
    "6m": 250,  # 6m ‑> 1y trading days approx
    "1y": 500,  # 1y
    "3y": 1500, # 3y
    "5y": 2500, # 5y
    "ytd": 500, # reuse 1y window
}

def _normalise(name: str) -> str:
    return name.lower().replace(" ", "_")


def _nearest_on_or_after(records, target: date):
    """Return first record whose date >= target. Records must be sorted ascending."""
    for rec in records:
        if rec.date >= target:
            return rec
    return None


def _fetch_records(db, model, timeframe: str):
    """Fetch recent records for a model in a single query.

    The query always sorts by *descending* date (latest first) as requested. For
    limited timeframes it applies a limit from TIMEFRAME_ROW_LIMITS. For
    'inception' it loads the full dataset. The returned list is *ascending*
    (oldest → newest) to make further processing consistent.
    """
    if timeframe == "inception":
        stmt = select(model).order_by(desc(model.date))  # always DESC
        desc_records = db.execute(stmt).scalars().all()
    else:
        limit = TIMEFRAME_ROW_LIMITS.get(timeframe)
        if limit is None:
            return []
        stmt = select(model).order_by(desc(model.date)).limit(limit)
        desc_records = db.execute(stmt).scalars().all()

    # Convert to ascending order for easier calculations
    return list(reversed(desc_records))


def _get_start_record(db, model, records, timeframe, end_date):
    """Return the appropriate start record for the given timeframe.

    If the required record cannot be found (insufficient historical data), the
    function returns ``None`` so that the caller can react accordingly.
    """
    # Inception: earliest available record
    if timeframe == "inception":
        return records[0] if records else None

    # Year-to-date: first trading day on/after 1 Jan of the current year
    if timeframe == "ytd":
        jan_first = date(end_date.year, 1, 1)
        return _nearest_on_or_after(records, jan_first)

    # Relative delta timeframes (1w, 1m, 3m, ...)
    delta = TIMEFRAME_DELTAS[timeframe]
    target_date = end_date - delta

    # Try within the already-fetched window first
    start_record = _nearest_on_or_after(records, target_date)
    if start_record is not None:
        return start_record

    # Fallback: full table scan when limited window didn't reach far enough
    full_records = db.execute(select(model).order_by(asc(model.date))).scalars().all()
    return _nearest_on_or_after(full_records, target_date)


def calculate_return(index_name: str, timeframe: str):
    """Calculate return for a given index and timeframe with a single DB fetch."""

    model = INDEX_MODEL_MAP.get(_normalise(index_name))
    if not model:
        return {"success": False, "timeframe": timeframe, "return": None, "message": "Unsupported index"}

    # Validate timeframe
    valid_timeframes = set(TIMEFRAME_DELTAS.keys()) | {"ytd", "inception"}
    if timeframe not in valid_timeframes:
        return {"success": False, "timeframe": timeframe, "return": None, "message": "Unsupported timeframe"}

    with get_db_context() as db:
        records = _fetch_records(db, model, timeframe)

        if not records:
            return {"success": False, "timeframe": timeframe, "return": None, "message": "No data"}

        end_record = records[-1]
        end_price = end_record.close
        end_date = end_record.date

        # Determine start record using helper
        start_record = _get_start_record(db, model, records, timeframe, end_date)
        if start_record is None:
            return {"success": False, "timeframe": timeframe, "return": None, "message": "Insufficient data"}
        start_price = start_record.close
        if start_price == 0:
            return {"success": False, "timeframe": timeframe, "return": None, "message": "Start price is zero"}

        returns_val = ((end_price / start_price) - 1) * 100
        return {"success": True, "timeframe": timeframe, "return": round(returns_val, 2), "message": "OK"} 