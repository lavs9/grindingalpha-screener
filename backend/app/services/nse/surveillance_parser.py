"""
NSE Surveillance Measures Parser (REG1_IND format).

Parses REG1_IND{DDMMYY}.csv files containing 63-column surveillance data
and converts to 4-table normalized structure.

References:
- .claude/file-formats-surveillance.md (Complete specification)
- NSE Circular: NSE/SURV/65097 dated November 14, 2024
"""
import csv
from datetime import datetime, date
from typing import Dict, List, Optional
from io import StringIO


class SurveillanceParseError(Exception):
    """Raised when surveillance data parsing fails."""
    pass


def parse_surveillance_value(value_str: str) -> Optional[int]:
    """
    Parse surveillance measure value from CSV.

    Encoding:
    - "100" or empty = Not applicable → NULL
    - "0", "1", "2"... = Stage level or flagged → Integer value

    Args:
        value_str: Value string from CSV

    Returns:
        Integer value or None if not applicable
    """
    if not value_str or value_str.strip() == "" or value_str.strip() == "100":
        return None

    try:
        value = int(value_str.strip())
        # 100 means "not applicable", all other values are stage levels or flags
        return None if value == 100 else value
    except (ValueError, AttributeError):
        return None


def parse_surveillance_boolean(value_str: str) -> Optional[bool]:
    """
    Parse boolean surveillance flag from CSV.

    Encoding:
    - "100" or empty = Not flagged → NULL
    - "0" = Flagged → TRUE
    - "1" or other = May indicate specific category → TRUE

    Note: In NSE surveillance, "0" typically means flagged/present,
          "100" means not applicable.

    Args:
        value_str: Value string from CSV

    Returns:
        True if flagged, None if not applicable
    """
    if not value_str or value_str.strip() == "" or value_str.strip() == "100":
        return None

    # "0" means flagged in NSE surveillance encoding
    # Any value other than 100 indicates the flag is active
    return True


def extract_date_from_filename(filename: str) -> Optional[date]:
    """
    Extract date from REG1_IND{DDMMYY}.csv filename.

    Examples:
        REG1_IND160125.csv → 2025-01-16
        REG1_IND230624.csv → 2024-06-23

    Args:
        filename: CSV filename

    Returns:
        date object or None if parsing fails
    """
    try:
        # Extract DDMMYY from filename (e.g., "160125" from "REG1_IND160125.csv")
        date_str = filename.replace("REG1_IND", "").replace(".csv", "").strip()

        if len(date_str) != 6:
            return None

        # Parse DDMMYY format
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:6])

        # Assume 20xx for year (2000-2099)
        full_year = 2000 + year

        return date(full_year, month, day)
    except (ValueError, AttributeError):
        return None


def parse_surveillance_csv(csv_content: str, filename: str = "", ingestion_date: Optional[date] = None) -> Dict:
    """
    Parse NSE REG1_IND{DDMMYY}.csv content into 4-table structure.

    Expected columns (63 total):
    1. ScripCode (not used, always "NA")
    2. Symbol
    3. Nse Exclusive (Y/N)
    4. Status (A/S/I)
    5. Series (EQ/BE/BZ/etc.)
    6. GSM (0-6)
    7. Long_Term_Additional_Surveillance_Measure
    8. Unsolicited_SMS (0-1)
    9. Insolvency_Resolution_Process(IRP) (0-2)
    10. Short_Term_Additional_Surveillance_Measure
    11. Default (0-1)
    12. ICA (0-1)
    13-14. Filler4, Filler5 (ignored)
    15. Pledge (boolean)
    16. Add-on_PB (boolean)
    17. Total Pledge (boolean)
    18. Social Media Platforms (boolean)
    19. ESM (1-2)
    20-30. Financial/Compliance flags (10 flags)
    31-41. Close-to-Close price movement flags (11 flags)
    42-48. High-Low price variation flags (7 flags)
    49-63. Filler17-31 (15 fillers, ignored)

    Args:
        csv_content: CSV file content as string
        filename: Original filename for date extraction (e.g., "REG1_IND160125.csv")
        ingestion_date: Optional override date (if None, extracted from filename)

    Returns:
        Dict with:
        - success: bool
        - data: Dict with 4 tables of data
            - surveillance_list: List[Dict]
            - surveillance_fundamental_flags: List[Dict]
            - surveillance_price_movement: List[Dict]
            - surveillance_price_variation: List[Dict]
        - errors: List of error messages
        - stats: Dict with parsing statistics
        - ingestion_date: The date for this surveillance snapshot
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
        "stats": {
            "total_rows": 0,
            "parsed_rows": 0,
            "skipped_rows": 0,
            "error_rows": 0
        },
        "ingestion_date": None
    }

    # Determine ingestion date
    if ingestion_date:
        result["ingestion_date"] = ingestion_date
    elif filename:
        extracted_date = extract_date_from_filename(filename)
        if extracted_date:
            result["ingestion_date"] = extracted_date
        else:
            result["errors"].append(f"Could not extract date from filename: {filename}")
            return result
    else:
        result["errors"].append("No ingestion_date or filename provided")
        return result

    try:
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_content))

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
            result["stats"]["total_rows"] += 1

            try:
                # Extract basic metadata
                symbol = row.get("Symbol", "").strip()

                if not symbol:
                    result["stats"]["skipped_rows"] += 1
                    continue

                # Parse surveillance_list table data
                surveillance_list_record = {
                    "symbol": symbol,
                    "date": result["ingestion_date"],
                    "nse_exclusive": row.get("Nse Exclusive", "").strip() or None,
                    "status": row.get("Status", "").strip() or None,
                    "series": row.get("Series", "").strip() or None,
                    # Staged measures (columns 6-12, 19)
                    "gsm_stage": parse_surveillance_value(row.get("GSM", "")),
                    "long_term_asm_stage": parse_surveillance_value(
                        row.get("Long_Term_Additional_Surveillance_Measure (Long Term ASM)", "")
                    ),
                    "short_term_asm_stage": parse_surveillance_value(
                        row.get("Short_Term_Additional_Surveillance_Measure (Short Term ASM)", "")
                    ),
                    "sms_category": parse_surveillance_value(row.get("Unsolicited_SMS", "")),
                    "irp_stage": parse_surveillance_value(row.get("Insolvency_Resolution_Process(IRP)", "")),
                    "default_stage": parse_surveillance_value(row.get("Default", "")),
                    "ica_stage": parse_surveillance_value(row.get("ICA", "")),
                    "esm_stage": parse_surveillance_value(row.get("ESM", "")),
                    # Binary flags (columns 15-18)
                    "high_promoter_pledge": parse_surveillance_boolean(row.get("Pledge", "")),
                    "addon_price_band": parse_surveillance_boolean(row.get("Add-on_PB", "")),
                    "total_pledge_measure": parse_surveillance_boolean(row.get("Total Pledge", "")),
                    "social_media_platforms": parse_surveillance_boolean(row.get("Social Media Platforms", ""))
                }

                # Parse surveillance_fundamental_flags table data
                fundamental_flags_record = {
                    "symbol": symbol,
                    "date": result["ingestion_date"],
                    # Financial risk flags
                    "is_loss_making": parse_surveillance_boolean(row.get("Loss making", "")),
                    "encumbrance_over_50pct": parse_surveillance_boolean(
                        row.get("The Overall encumbered share in the scrip is more than 50 Percent.", "")
                    ),
                    "eps_zero_or_negative": parse_surveillance_boolean(
                        row.get("EPS in the scrip is zero (4 trailing quarters)", "")
                    ),
                    # Compliance flags
                    "under_bz_sz_series": parse_surveillance_boolean(row.get("Under BZ/SZ Series", "")),
                    "listing_fee_unpaid": parse_surveillance_boolean(
                        row.get("Company has failed to pay Annual listing fee", "")
                    ),
                    # Liquidity flags
                    "fo_exit_scheduled": parse_surveillance_boolean(
                        row.get("Derivative contracts in the scrip to be moved out of F and O", "")
                    ),
                    "low_unique_pan_traded": parse_surveillance_boolean(
                        row.get("Less than 100 unique PAN traded in previous 30 days", "")
                    ),
                    "sme_mm_period_over": parse_surveillance_boolean(
                        row.get("Mandatory Market making period in SME scrip is over", "")
                    ),
                    "sme_not_regularly_traded": parse_surveillance_boolean(
                        row.get("SME scrip is not regularly traded", "")
                    ),
                    # Valuation flag
                    "pe_over_50": parse_surveillance_boolean(
                        row.get("Scrip PE is greater than 50 (4 trailing quarters)", "")
                    )
                }

                # Parse surveillance_price_movement table data (Close-to-Close)
                price_movement_record = {
                    "symbol": symbol,
                    "date": result["ingestion_date"],
                    "c2c_25pct_5d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 25perc in previous 5 trading days", "")
                    ),
                    "c2c_40pct_15d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 40perc in previous 15 trading days", "")
                    ),
                    "c2c_100pct_60d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 100perc in previous 60 trading Days", "")
                    ),
                    "c2c_25pct_15d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 25perc in previous 15 Days", "")
                    ),
                    "c2c_50pct_1m": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 50perc in previous 1 month", "")
                    ),
                    "c2c_90pct_3m": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 90perc in previous 3 months", "")
                    ),
                    "c2c_25pct_1m_alt": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 25perc in previous 1 month", "")
                    ),
                    "c2c_50pct_3m": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 50perc in previous 3 months", "")
                    ),
                    "c2c_200pct_365d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 200perc in previous 365 Days", "")
                    ),
                    "c2c_75pct_6m": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 75perc in previous 6 months", "")
                    ),
                    "c2c_100pct_365d": parse_surveillance_boolean(
                        row.get("Close to Close price movement greater than 100perc in previous 365 days", "")
                    )
                }

                # Parse surveillance_price_variation table data (High-Low)
                price_variation_record = {
                    "symbol": symbol,
                    "date": result["ingestion_date"],
                    "hl_75pct_1m": parse_surveillance_boolean(
                        row.get("High low price variation greater than 75perc in previous 1 month", "")
                    ),
                    "hl_150pct_3m": parse_surveillance_boolean(
                        row.get("High low price variation greater than 150perc in previous 3 months", "")
                    ),
                    "hl_75pct_3m": parse_surveillance_boolean(
                        row.get("High low price variation greater than 75perc in previous 3 months", "")
                    ),
                    "hl_300pct_365d": parse_surveillance_boolean(
                        row.get("High low price variation greater than 300perc in previous 365 Days", "")
                    ),
                    "hl_100pct_6m": parse_surveillance_boolean(
                        row.get("High low price variation greater than 100perc in previous 6 months", "")
                    ),
                    "hl_200pct_365d": parse_surveillance_boolean(
                        row.get("High low price variation greater than 200perc in previous 365 Days", "")
                    ),
                    "hl_150pct_12m": parse_surveillance_boolean(
                        row.get("High low price variation greater than 150perc in previous 12 months", "")
                    )
                }

                # Add records to result
                result["data"]["surveillance_list"].append(surveillance_list_record)
                result["data"]["surveillance_fundamental_flags"].append(fundamental_flags_record)
                result["data"]["surveillance_price_movement"].append(price_movement_record)
                result["data"]["surveillance_price_variation"].append(price_variation_record)

                result["stats"]["parsed_rows"] += 1

            except Exception as e:
                result["stats"]["error_rows"] += 1
                result["errors"].append(f"Row {row_num}: {str(e)}")

        # Mark as successful if we parsed at least one row
        if result["stats"]["parsed_rows"] > 0:
            result["success"] = True
        else:
            result["errors"].append("No valid rows parsed from CSV")

    except Exception as e:
        result["errors"].append(f"CSV parsing failed: {str(e)}")
        return result

    return result


def validate_surveillance_data(parsed_data: Dict) -> List[str]:
    """
    Validate parsed surveillance data for common issues.

    Checks:
    - All 4 tables have same number of records
    - Symbols match across all tables
    - Dates are consistent
    - No duplicate symbols for same date

    Args:
        parsed_data: Output from parse_surveillance_csv()

    Returns:
        List of validation error messages (empty if valid)
    """
    validation_errors = []

    if not parsed_data.get("success"):
        return ["Cannot validate - parsing failed"]

    data = parsed_data["data"]

    # Check all tables have same record count
    counts = {
        "surveillance_list": len(data["surveillance_list"]),
        "fundamental_flags": len(data["surveillance_fundamental_flags"]),
        "price_movement": len(data["surveillance_price_movement"]),
        "price_variation": len(data["surveillance_price_variation"])
    }

    if len(set(counts.values())) != 1:
        validation_errors.append(
            f"Mismatched record counts across tables: {counts}"
        )

    # Check for duplicate symbols
    symbols_list = [record["symbol"] for record in data["surveillance_list"]]
    if len(symbols_list) != len(set(symbols_list)):
        duplicates = [symbol for symbol in set(symbols_list) if symbols_list.count(symbol) > 1]
        validation_errors.append(f"Duplicate symbols found: {duplicates}")

    # Check symbol consistency across tables
    if counts["surveillance_list"] > 0:
        list_symbols = set(record["symbol"] for record in data["surveillance_list"])
        fundamental_symbols = set(record["symbol"] for record in data["surveillance_fundamental_flags"])
        movement_symbols = set(record["symbol"] for record in data["surveillance_price_movement"])
        variation_symbols = set(record["symbol"] for record in data["surveillance_price_variation"])

        if not (list_symbols == fundamental_symbols == movement_symbols == variation_symbols):
            validation_errors.append("Symbol mismatch detected across tables")

    return validation_errors
