"""
NSE Surveillance Measures Service.

Handles fetching, parsing, and storing NSE surveillance data (REG1_IND format).
Data is stored across 4 normalized tables for efficient querying.
"""
import requests
from typing import Dict, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.models.surveillance import (
    SurveillanceList,
    SurveillanceFundamentalFlags,
    SurveillancePriceMovement,
    SurveillancePriceVariation
)
from app.services.nse.surveillance_parser import parse_surveillance_csv, validate_surveillance_data


# NSE Surveillance URL pattern
# Example: https://nsearchives.nseindia.com/surveillance/REG1_IND160125.csv
SURVEILLANCE_URL_TEMPLATE = "https://nsearchives.nseindia.com/surveillance/{filename}"


class SurveillanceServiceError(Exception):
    """Raised when surveillance service operations fail."""
    pass


def fetch_surveillance_data(
    filename: Optional[str] = None,
    ingestion_date: Optional[date] = None,
    file_path: Optional[str] = None
) -> Dict:
    """
    Fetch and parse NSE surveillance data (REG1_IND format).

    Args:
        filename: NSE filename (e.g., "REG1_IND160125.csv")
        ingestion_date: Optional override date (if not using filename extraction)
        file_path: Optional local file path (for testing or manual uploads)

    Returns:
        Dict with:
        - success: bool
        - data: Dict with 4 tables of parsed records
        - errors: List of error messages
        - source: URL or file path
        - ingestion_date: The date for this surveillance snapshot
        - stats: Parsing statistics
    """
    result = {
        "success": False,
        "data": {
            "surveillance_list": [],
            "surveillance_fundamental_flags": [],
            "surveillance_price_movement": [],
            "surveillance_price_variation": []
        },
        "errors": [],
        "source": "",
        "ingestion_date": None,
        "stats": {}
    }

    try:
        # Fetch CSV content
        if file_path:
            # Read from local file (for testing or manual uploads)
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            result["source"] = f"file://{file_path}"
            # Use filename from path if not provided
            if not filename:
                import os
                filename = os.path.basename(file_path)
        else:
            # Fetch from NSE archive
            if not filename:
                result["errors"].append("Either filename or file_path must be provided")
                return result

            url = SURVEILLANCE_URL_TEMPLATE.format(filename=filename)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            csv_content = response.text
            result["source"] = url

        # Parse CSV
        parse_result = parse_surveillance_csv(
            csv_content,
            filename=filename or "",
            ingestion_date=ingestion_date
        )

        result["success"] = parse_result["success"]
        result["data"] = parse_result["data"]
        result["errors"] = parse_result["errors"]
        result["stats"] = parse_result["stats"]
        result["ingestion_date"] = parse_result.get("ingestion_date")

        # Validate parsed data
        if result["success"]:
            validation_errors = validate_surveillance_data(parse_result)
            if validation_errors:
                result["errors"].extend(validation_errors)
                result["success"] = False

    except requests.exceptions.RequestException as e:
        result["errors"].append(f"HTTP request failed: {str(e)}")
        result["success"] = False
    except FileNotFoundError as e:
        result["errors"].append(f"File not found: {str(e)}")
        result["success"] = False
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        result["success"] = False

    return result


def ingest_surveillance(
    db: Session,
    surveillance_data: Dict,
    skip_missing_symbols: bool = True
) -> Dict:
    """
    Insert surveillance records into database (4-table structure).

    Uses UPSERT pattern (ON CONFLICT DO UPDATE) since surveillance data for
    a given date should replace previous data for that date.

    Args:
        db: SQLAlchemy database session
        surveillance_data: Dict with 4 lists from parser (surveillance_list, etc.)
        skip_missing_symbols: If True, skip symbols not in securities table (default: True)

    Returns:
        Dict with ingestion statistics per table
    """
    result = {
        "success": False,
        "records_inserted": {
            "surveillance_list": 0,
            "surveillance_fundamental_flags": 0,
            "surveillance_price_movement": 0,
            "surveillance_price_variation": 0
        },
        "records_updated": {
            "surveillance_list": 0,
            "surveillance_fundamental_flags": 0,
            "surveillance_price_movement": 0,
            "surveillance_price_variation": 0
        },
        "records_failed": 0,
        "records_skipped": 0,
        "errors": []
    }

    try:
        # Ingest surveillance_list table
        if surveillance_data.get("surveillance_list"):
            list_result = _ingest_table(
                db,
                SurveillanceList,
                surveillance_data["surveillance_list"],
                skip_missing_symbols
            )
            result["records_inserted"]["surveillance_list"] = list_result["inserted"]
            result["records_updated"]["surveillance_list"] = list_result["updated"]
            result["records_skipped"] += list_result["skipped"]
            result["records_failed"] += list_result["failed"]
            result["errors"].extend(list_result["errors"])

        # Ingest surveillance_fundamental_flags table
        if surveillance_data.get("surveillance_fundamental_flags"):
            flags_result = _ingest_table(
                db,
                SurveillanceFundamentalFlags,
                surveillance_data["surveillance_fundamental_flags"],
                skip_missing_symbols
            )
            result["records_inserted"]["surveillance_fundamental_flags"] = flags_result["inserted"]
            result["records_updated"]["surveillance_fundamental_flags"] = flags_result["updated"]
            result["records_skipped"] += flags_result["skipped"]
            result["records_failed"] += flags_result["failed"]
            result["errors"].extend(flags_result["errors"])

        # Ingest surveillance_price_movement table
        if surveillance_data.get("surveillance_price_movement"):
            movement_result = _ingest_table(
                db,
                SurveillancePriceMovement,
                surveillance_data["surveillance_price_movement"],
                skip_missing_symbols
            )
            result["records_inserted"]["surveillance_price_movement"] = movement_result["inserted"]
            result["records_updated"]["surveillance_price_movement"] = movement_result["updated"]
            result["records_skipped"] += movement_result["skipped"]
            result["records_failed"] += movement_result["failed"]
            result["errors"].extend(movement_result["errors"])

        # Ingest surveillance_price_variation table
        if surveillance_data.get("surveillance_price_variation"):
            variation_result = _ingest_table(
                db,
                SurveillancePriceVariation,
                surveillance_data["surveillance_price_variation"],
                skip_missing_symbols
            )
            result["records_inserted"]["surveillance_price_variation"] = variation_result["inserted"]
            result["records_updated"]["surveillance_price_variation"] = variation_result["updated"]
            result["records_skipped"] += variation_result["skipped"]
            result["records_failed"] += variation_result["failed"]
            result["errors"].extend(variation_result["errors"])

        # Commit transaction
        db.commit()
        result["success"] = True

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database transaction failed: {str(e)}")
        result["success"] = False

    return result


def _ingest_table(
    db: Session,
    model_class,
    records: list,
    skip_missing_symbols: bool
) -> Dict:
    """
    Ingest records into a single surveillance table using UPSERT.

    Args:
        db: Database session
        model_class: SQLAlchemy model class (SurveillanceList, etc.)
        records: List of record dicts from parser
        skip_missing_symbols: If True, skip symbols not in securities table

    Returns:
        Dict with table-level statistics
    """
    stats = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "errors": []
    }

    if not records:
        return stats

    try:
        # Build UPSERT statement
        # Primary key is (symbol, date), so ON CONFLICT updates all other columns
        stmt = insert(model_class).values(records)

        # Determine columns to update on conflict (all except primary key and timestamps)
        update_cols = {
            col.name: col
            for col in stmt.excluded
            if col.name not in ("symbol", "date", "created_at")
        }

        # Execute UPSERT
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=update_cols
        )

        # Note: PostgreSQL doesn't easily return INSERT vs UPDATE count with ON CONFLICT
        # We'll track total affected rows
        result = db.execute(stmt)
        stats["inserted"] = result.rowcount  # This includes both inserts and updates

    except IntegrityError as e:
        stats["failed"] = len(records)
        stats["errors"].append(f"Integrity error in {model_class.__tablename__}: {str(e)}")
    except Exception as e:
        stats["failed"] = len(records)
        stats["errors"].append(f"Unexpected error in {model_class.__tablename__}: {str(e)}")

    return stats


def get_surveillance_by_symbol(
    db: Session,
    symbol: str,
    target_date: Optional[date] = None
) -> Optional[Dict]:
    """
    Get aggregated surveillance data for a single symbol.

    Joins all 4 surveillance tables to return complete profile.

    Args:
        db: Database session
        symbol: NSE symbol
        target_date: Optional date filter (defaults to latest available)

    Returns:
        Dict with aggregated surveillance data or None if not found
    """
    query_date = target_date if target_date else date.today()

    # Query all 4 tables
    list_record = db.query(SurveillanceList).filter(
        SurveillanceList.symbol == symbol,
        SurveillanceList.date == query_date
    ).first()

    if not list_record:
        return None

    flags_record = db.query(SurveillanceFundamentalFlags).filter(
        SurveillanceFundamentalFlags.symbol == symbol,
        SurveillanceFundamentalFlags.date == query_date
    ).first()

    movement_record = db.query(SurveillancePriceMovement).filter(
        SurveillancePriceMovement.symbol == symbol,
        SurveillancePriceMovement.date == query_date
    ).first()

    variation_record = db.query(SurveillancePriceVariation).filter(
        SurveillancePriceVariation.symbol == symbol,
        SurveillancePriceVariation.date == query_date
    ).first()

    # Combine into single dict
    result = {
        "symbol": symbol,
        "date": query_date,
        # From surveillance_list
        "nse_exclusive": list_record.nse_exclusive,
        "status": list_record.status,
        "series": list_record.series,
        "gsm_stage": list_record.gsm_stage,
        "long_term_asm_stage": list_record.long_term_asm_stage,
        "short_term_asm_stage": list_record.short_term_asm_stage,
        "sms_category": list_record.sms_category,
        "irp_stage": list_record.irp_stage,
        "default_stage": list_record.default_stage,
        "ica_stage": list_record.ica_stage,
        "esm_stage": list_record.esm_stage,
        "high_promoter_pledge": list_record.high_promoter_pledge,
        "addon_price_band": list_record.addon_price_band,
        "total_pledge_measure": list_record.total_pledge_measure,
        "social_media_platforms": list_record.social_media_platforms,
    }

    # Add fundamental flags if exists
    if flags_record:
        result.update({
            "is_loss_making": flags_record.is_loss_making,
            "encumbrance_over_50pct": flags_record.encumbrance_over_50pct,
            "eps_zero_or_negative": flags_record.eps_zero_or_negative,
            "under_bz_sz_series": flags_record.under_bz_sz_series,
            "listing_fee_unpaid": flags_record.listing_fee_unpaid,
            "fo_exit_scheduled": flags_record.fo_exit_scheduled,
            "low_unique_pan_traded": flags_record.low_unique_pan_traded,
            "sme_mm_period_over": flags_record.sme_mm_period_over,
            "sme_not_regularly_traded": flags_record.sme_not_regularly_traded,
            "pe_over_50": flags_record.pe_over_50,
        })

    # Add price movement if exists
    if movement_record:
        result.update({
            "c2c_25pct_5d": movement_record.c2c_25pct_5d,
            "c2c_40pct_15d": movement_record.c2c_40pct_15d,
            "c2c_100pct_60d": movement_record.c2c_100pct_60d,
            "c2c_25pct_15d": movement_record.c2c_25pct_15d,
            "c2c_50pct_1m": movement_record.c2c_50pct_1m,
            "c2c_90pct_3m": movement_record.c2c_90pct_3m,
            "c2c_25pct_1m_alt": movement_record.c2c_25pct_1m_alt,
            "c2c_50pct_3m": movement_record.c2c_50pct_3m,
            "c2c_200pct_365d": movement_record.c2c_200pct_365d,
            "c2c_75pct_6m": movement_record.c2c_75pct_6m,
            "c2c_100pct_365d": movement_record.c2c_100pct_365d,
        })

    # Add price variation if exists
    if variation_record:
        result.update({
            "hl_75pct_1m": variation_record.hl_75pct_1m,
            "hl_150pct_3m": variation_record.hl_150pct_3m,
            "hl_75pct_3m": variation_record.hl_75pct_3m,
            "hl_300pct_365d": variation_record.hl_300pct_365d,
            "hl_100pct_6m": variation_record.hl_100pct_6m,
            "hl_200pct_365d": variation_record.hl_200pct_365d,
            "hl_150pct_12m": variation_record.hl_150pct_12m,
        })

    return result


def get_surveillance_list_by_date(
    db: Session,
    target_date: date,
    filter_measure: Optional[str] = None
) -> list:
    """
    Get all symbols under surveillance for a specific date.

    Args:
        db: Database session
        target_date: Date to query
        filter_measure: Optional filter (e.g., "gsm", "esm", "long_term_asm")

    Returns:
        List of symbols with surveillance measures
    """
    query = db.query(SurveillanceList).filter(
        SurveillanceList.date == target_date
    )

    # Apply filters based on measure type
    if filter_measure == "gsm":
        query = query.filter(SurveillanceList.gsm_stage.isnot(None))
    elif filter_measure == "esm":
        query = query.filter(SurveillanceList.esm_stage.isnot(None))
    elif filter_measure == "long_term_asm":
        query = query.filter(SurveillanceList.long_term_asm_stage.isnot(None))
    elif filter_measure == "short_term_asm":
        query = query.filter(SurveillanceList.short_term_asm_stage.isnot(None))
    elif filter_measure == "any":
        # Any surveillance measure active
        query = query.filter(
            (SurveillanceList.gsm_stage.isnot(None)) |
            (SurveillanceList.esm_stage.isnot(None)) |
            (SurveillanceList.long_term_asm_stage.isnot(None)) |
            (SurveillanceList.short_term_asm_stage.isnot(None))
        )

    records = query.all()
    return [record.symbol for record in records]
