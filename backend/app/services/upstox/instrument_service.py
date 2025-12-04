"""
Upstox Instrument Service - Manages instrument master data.

This module handles:
- Downloading NSE.json.gz from Upstox
- Parsing and ingesting instruments
- Auto-creating symbol-to-instrument mappings
"""

import requests
import gzip
import json
import time
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.upstox import UpstoxInstrument, SymbolInstrumentMapping
from app.models.security import Security


def fetch_upstox_instruments(exchange: str = "NSE") -> Dict:
    """
    Download and decompress Upstox instruments JSON.

    Source: https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz

    Args:
        exchange: Exchange name (NSE, BSE, etc.)

    Returns:
        Dict with success, data (list of instruments), errors, source
    """
    result = {
        "success": False,
        "data": [],
        "errors": [],
        "source": ""
    }

    try:
        url = f"https://assets.upstox.com/market-quote/instruments/exchange/{exchange}.json.gz"
        result["source"] = url

        # Download gzipped JSON (60-second timeout for large file)
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Decompress
        decompressed = gzip.decompress(response.content)
        json_content = decompressed.decode('utf-8')

        # Parse JSON
        instruments = json.loads(json_content)
        result["success"] = True
        result["data"] = instruments

    except requests.exceptions.RequestException as e:
        result["errors"].append(f"HTTP request failed: {str(e)}")
    except gzip.BadGzipFile as e:
        result["errors"].append(f"Decompression failed: {str(e)}")
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON parsing failed: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")

    return result


def ingest_upstox_instruments(db: Session, instruments_data: List[dict]) -> Dict:
    """
    Bulk insert/update Upstox instruments using UPSERT.

    Args:
        db: Database session
        instruments_data: List of instrument dicts from Upstox API

    Returns:
        Dict with success, instruments_inserted, instruments_updated, errors
    """
    result = {
        "success": False,
        "instruments_inserted": 0,
        "instruments_updated": 0,
        "errors": []
    }

    if not instruments_data:
        result["errors"].append("No instrument data provided")
        return result

    batch_size = 500
    inserted_count = 0
    updated_count = 0

    try:
        for i in range(0, len(instruments_data), batch_size):
            batch = instruments_data[i:i + batch_size]

            for instr_dict in batch:
                try:
                    # UPSERT on instrument_key
                    stmt = insert(UpstoxInstrument).values(
                        instrument_key=instr_dict.get('instrument_key'),
                        exchange=instr_dict.get('exchange'),
                        symbol=instr_dict.get('trading_symbol'),
                        isin=instr_dict.get('isin'),
                        name=instr_dict.get('name'),
                        instrument_type=instr_dict.get('instrument_type'),
                        is_active=True
                    )

                    stmt = stmt.on_conflict_do_update(
                        index_elements=['instrument_key'],
                        set_={
                            'symbol': stmt.excluded.symbol,
                            'name': stmt.excluded.name,
                            'instrument_type': stmt.excluded.instrument_type,
                            'updated_at': stmt.excluded.updated_at
                        }
                    )

                    db.execute(stmt)
                    inserted_count += 1

                except Exception as e:
                    result["errors"].append(
                        f"Error ingesting {instr_dict.get('instrument_key', 'unknown')}: {str(e)}"
                    )

            # Commit batch
            db.commit()

        result["success"] = True
        result["instruments_inserted"] = inserted_count
        result["instruments_updated"] = 0  # Can't distinguish from insert in UPSERT

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database error: {str(e)}")

    return result


def create_symbol_mappings(db: Session) -> Dict:
    """
    Auto-create mappings between securities and Upstox instruments.

    Matching logic:
    1. For equities: exchange='NSE_EQ', match by ISIN (primary) or symbol (fallback)
    2. For indices: manual mapping only (not automated here)

    Args:
        db: Database session

    Returns:
        Dict with mappings_created, errors
    """
    result = {
        "mappings_created": 0,
        "errors": []
    }

    try:
        # Get all active equities
        securities = db.query(Security).filter(
            Security.is_active == True,
            Security.security_type == 'EQUITY'
        ).all()

        for security in securities:
            try:
                # Primary: Match by ISIN
                instrument = db.query(UpstoxInstrument).filter(
                    UpstoxInstrument.exchange == 'NSE_EQ',
                    UpstoxInstrument.isin == security.isin
                ).first()

                match_method = 'auto_isin'
                confidence = 100.00

                if not instrument:
                    # Fallback: Match by symbol
                    instrument = db.query(UpstoxInstrument).filter(
                        UpstoxInstrument.exchange == 'NSE_EQ',
                        UpstoxInstrument.symbol == security.symbol
                    ).first()
                    match_method = 'auto_symbol'
                    confidence = 90.00

                if instrument:
                    # Check if mapping already exists
                    existing = db.query(SymbolInstrumentMapping).filter(
                        SymbolInstrumentMapping.security_id == security.id,
                        SymbolInstrumentMapping.instrument_id == instrument.id
                    ).first()

                    if not existing:
                        mapping = SymbolInstrumentMapping(
                            security_id=security.id,
                            instrument_id=instrument.id,
                            symbol=security.symbol,
                            instrument_key=instrument.instrument_key,
                            is_primary=True,
                            confidence=confidence,
                            match_method=match_method
                        )
                        db.add(mapping)
                        result["mappings_created"] += 1

            except Exception as e:
                result["errors"].append(f"Error mapping {security.symbol}: {str(e)}")

        db.commit()

    except Exception as e:
        db.rollback()
        result["errors"].append(f"Database error in mapping: {str(e)}")

    return result


def ingest_instruments_from_upstox(db: Session) -> Dict:
    """
    Orchestration function: fetch, ingest, create mappings.

    Args:
        db: Database session

    Returns:
        Dict with success, total_instruments, instruments_inserted,
        instruments_updated, mappings_created, errors, duration_seconds
    """
    start_time = time.time()

    # Step 1: Fetch instruments from Upstox
    fetch_result = fetch_upstox_instruments(exchange="NSE")
    if not fetch_result["success"]:
        return {
            "success": False,
            "total_instruments": 0,
            "instruments_inserted": 0,
            "instruments_updated": 0,
            "mappings_created": 0,
            "errors": fetch_result["errors"],
            "duration_seconds": int(time.time() - start_time)
        }

    # Step 2: Ingest instruments
    ingest_result = ingest_upstox_instruments(db, fetch_result["data"])

    # Step 3: Create symbol mappings
    mapping_result = create_symbol_mappings(db)

    duration = int(time.time() - start_time)

    return {
        "success": True,
        "total_instruments": len(fetch_result["data"]),
        "instruments_inserted": ingest_result["instruments_inserted"],
        "instruments_updated": ingest_result["instruments_updated"],
        "mappings_created": mapping_result["mappings_created"],
        "errors": ingest_result["errors"] + mapping_result["errors"],
        "duration_seconds": duration
    }
