# Sample Data Files

This directory contains sample data files from external sources for testing and reference purposes.

## Purpose

- **Parser Testing:** Use samples to test data ingestion logic without hitting live APIs
- **Format Reference:** Quick reference for field structures when coding
- **Version Control:** Track format changes over time
- **Onboarding:** Help new developers understand data structures

## Guidelines

### Adding Sample Files

1. **File Naming Convention:**
   - Use descriptive names matching source
   - Include date if format may change: `EQUITY_L_20250116_sample.csv`
   - For API responses: `upstox_historical_candle_sample.json`

2. **Sample Size:**
   - CSV files: 5-10 rows (header + data)
   - JSON responses: 2-3 complete records
   - Keep files < 50 KB

3. **Data Anonymization:**
   - Use real security symbols (RELIANCE, TCS, etc.) - publicly available
   - Anonymize any client names in bulk/block deals
   - No personal information

4. **Git Tracking:**
   - **DO commit** sample files (they're small and valuable)
   - **DO NOT commit** full production data files
   - Update `.gitignore` for `*_full.csv` or similar patterns

### Required Samples

Based on [file-formats.md](../file-formats.md), we need samples for:

- [ ] `EQUITY_L_sample.csv` - NSE listed securities
- [ ] `eq_etfseclist_sample.csv` - NSE ETF list
- [ ] `PR160125_sample.zip` - Market cap archive (with MCAP*.csv inside)
- [ ] `bulk_sample.csv` - Bulk deals
- [ ] `block_sample.csv` - Block deals
- [ ] `REG1_IND160125_sample.csv` - Surveillance measures
- [ ] `upstox_historical_candle_sample.json` - Historical OHLCV API response
- [ ] `upstox_full_market_quote_sample.json` - Market quote API response
- [ ] `upstox_market_holidays_sample.json` - Holidays API response
- [ ] `nse_quote_equity_sample.json` - Industry classification response
- [ ] `nifty50_constituents_sample.csv` - Index constituents (manual format)

## Using Sample Files in Tests

```python
# Example: Test NSE securities parser
import os
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent.parent / '.claude' / 'samples'

def test_parse_nse_securities():
    sample_file = SAMPLES_DIR / 'EQUITY_L_sample.csv'
    result = parse_nse_securities(sample_file)
    assert len(result) == 5  # Expect 5 sample rows
    assert result[0]['SYMBOL'] == 'RELIANCE'
```

## Updating Samples

**When to Update:**
- External source changes format
- New fields added/removed
- Data structure changes

**Process:**
1. Download new sample from live source
2. Anonymize if needed
3. Replace old sample file
4. Update [file-formats.md](../file-formats.md) with change log entry
5. Update parser code if format changed
6. Commit both sample file and documentation together

## DO NOT Store Here

- Full production datasets
- API credentials
- Personal data
- Files > 1 MB (use external storage, link in docs)

---

**Last Updated:** 2025-01-16
