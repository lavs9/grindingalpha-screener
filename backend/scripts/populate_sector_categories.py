"""
Populate sector_category and is_sectoral columns in index_ohlcv_daily table.

Reads from: backend/data/sector_index_mapping.json
Updates: index_ohlcv_daily table with sector categorization
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.database.session import SessionLocal
from app.models.timeseries import IndexOHLCVDaily
from sqlalchemy import update

def load_sector_mapping():
    """Load sector mapping from JSON file."""
    mapping_file = Path(__file__).parent.parent / "data" / "sector_index_mapping.json"
    with open(mapping_file, 'r') as f:
        return json.load(f)

def populate_sectors():
    """Populate sector categories for all indices."""
    db = SessionLocal()

    try:
        # Load mapping
        mapping_data = load_sector_mapping()

        # Combine all indices
        all_indices = {}

        # Sectoral indices
        for symbol, data in mapping_data.get('sectoral_indices', {}).items():
            all_indices[symbol] = {
                'category': data['category'],
                'is_sectoral': 1
            }

        # Thematic indices
        for symbol, data in mapping_data.get('thematic_indices', {}).items():
            all_indices[symbol] = {
                'category': data['category'],
                'is_sectoral': 1
            }

        # Broad market indices (not sectoral)
        for symbol, data in mapping_data.get('broad_market_indices', {}).items():
            all_indices[symbol] = {
                'category': data['category'],
                'is_sectoral': 0
            }

        print(f"Loaded {len(all_indices)} index mappings")
        print(f"- Sectoral: {len(mapping_data.get('sectoral_indices', {}))}")
        print(f"- Thematic: {len(mapping_data.get('thematic_indices', {}))}")
        print(f"- Broad Market: {len(mapping_data.get('broad_market_indices', {}))}")

        # Update database
        updated_count = 0
        for symbol, data in all_indices.items():
            result = db.execute(
                update(IndexOHLCVDaily).
                where(IndexOHLCVDaily.symbol == symbol).
                values(
                    sector_category=data['category'],
                    is_sectoral=data['is_sectoral']
                )
            )
            rows_affected = result.rowcount
            if rows_affected > 0:
                updated_count += 1
                print(f"✓ Updated {symbol}: {data['category']} (is_sectoral={data['is_sectoral']}) - {rows_affected} rows")

        db.commit()
        print(f"\n✅ Successfully updated {updated_count} indices")

        # Verify
        sectoral_count = db.query(IndexOHLCVDaily).filter(IndexOHLCVDaily.is_sectoral == 1).distinct(IndexOHLCVDaily.symbol).count()
        broad_count = db.query(IndexOHLCVDaily).filter(IndexOHLCVDaily.is_sectoral == 0).distinct(IndexOHLCVDaily.symbol).count()

        print(f"\nDatabase Stats:")
        print(f"- Sectoral/Thematic indices: {sectoral_count}")
        print(f"- Broad market indices: {broad_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_sectors()
