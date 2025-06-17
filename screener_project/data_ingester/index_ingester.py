import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from ..database.db_helper import get_db_context
from ..indexes_models.nifty_bank import NiftyBank
import os
from pathlib import Path

def parse_date(date_str: str) -> datetime:
    """Convert date string to datetime object"""
    return datetime.strptime(date_str, "%d %b %Y")

def ingest_index_data(index_name: str, csv_path: str) -> dict:
    """
    Ingest index data from CSV file into the database
    
    Args:
        index_name (str): Name of the index (e.g., 'NIFTY BANK')
        csv_path (str): Path to the CSV file
    
    Returns:
        dict: Statistics about the ingestion process
    """
    # Resolve CSV path – allow user to pass relative path like "index_csv/.." even
    # after the project was packaged. If the path as-is doesn't exist, fall back
    # to <package_root>/index_csv/<basename>.
    resolved_path = Path(csv_path)
    if not resolved_path.exists():
        package_root = Path(__file__).resolve().parent.parent  # screener_project/
        fallback = package_root / "index_csv" / resolved_path.name
        if fallback.exists():
            resolved_path = fallback
        else:
            return {
                "success": False,
                "message": f"CSV file not found. Tried '{csv_path}' and '{fallback}'.",
                "records_processed": 0,
                "records_added": 0,
                "errors": []
            }

    try:
        df = pd.read_csv(resolved_path)
        
        required_columns = ["Index Name", "Date", "Open", "High", "Low", "Close"]
        if not all(col in df.columns for col in required_columns):
            return {
                "success": False,
                "message": "CSV file missing required columns",
                "records_processed": 0,
                "records_added": 0,
                "errors": ["Missing required columns"]
            }

        # Filter data for the specified index
        df = df[df["Index Name"] == index_name]
        
        if df.empty:
            return {
                "success": False,
                "message": f"No data found for index {index_name}",
                "records_processed": 0,
                "records_added": 0,
                "errors": []
            }

        records_processed = 0
        records_added = 0
        errors = []

        with get_db_context() as db:
            for _, row in df.iterrows():
                try:
                    # Create record
                    record = NiftyBank(
                        index_name=row["Index Name"],
                        date=parse_date(row["Date"]),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"])
                    )
                    
                    # Add to database
                    db.add(record)
                    records_added += 1
                    
                except (ValueError, IntegrityError) as e:
                    errors.append(f"Error processing row {records_processed + 1}: {str(e)}")
                
                records_processed += 1
            
            db.commit()

        return {
            "success": True,
            "message": f"Successfully processed {records_processed} records",
            "records_processed": records_processed,
            "records_added": records_added,
            "errors": errors
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing file: {str(e)}",
            "records_processed": records_processed if 'records_processed' in locals() else 0,
            "records_added": records_added if 'records_added' in locals() else 0,
            "errors": [str(e)]
        } 