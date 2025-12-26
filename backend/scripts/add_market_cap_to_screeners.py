"""
Script to add market_cap field to all screener endpoints.
This script updates the backend screeners.py file to include MarketCapHistory joins.
"""
import re

SCREENERS_FILE = "/Users/mayanklavania/projects/screener/backend/app/api/v1/screeners.py"

# Read the file
with open(SCREENERS_FILE, 'r') as f:
    content = f.read()

# List of screener functions that need market_cap (all except breakouts-4percent which is already done)
screeners_to_update = [
    'get_rs_leaders',
    'get_high_volume_movers',
    'get_ma_stacked_breakouts',
    'get_weekly_movers',
    'get_momentum_watchlist'
]

# For each screener function
for screener_func in screeners_to_update:
    # Find the function definition
    func_pattern = rf'(async def {screener_func}\([^)]+\)[^:]*:.*?(?=@router\.|$))'
    match = re.search(func_pattern, content, re.DOTALL)

    if not match:
        print(f"Could not find function {screener_func}")
        continue

    func_content = match.group(1)

    # Check if already has market_cap
    if 'MarketCapHistory.market_cap' in func_content:
        print(f"Skipping {screener_func} - already has market_cap")
        continue

    # Add MarketCapHistory.market_cap to the query SELECT
    # Find the db.query( section
    query_pattern = r'(results = db\.query\([^)]+)'
    query_match = re.search(query_pattern, func_content)

    if query_match:
        old_query = query_match.group(1)
        # Add market_cap before the closing parenthesis
        new_query = old_query.rstrip() + ',\n        MarketCapHistory.market_cap'
        func_content = func_content.replace(old_query, new_query)

    # Add outerjoin for MarketCapHistory
    # Find the last join before .filter(
    join_pattern = r'(\)\s*\.filter\()'
    join_match = re.search(join_pattern, func_content)

    if join_match:
        # Insert outerjoin before .filter(
        outerjoin_code = '''\n    ).outerjoin(
        MarketCapHistory, and_(
            MarketCapHistory.symbol == CalculatedMetrics.symbol,
            MarketCapHistory.date == target_date
        )'''
        func_content = func_content.replace(join_match.group(0), outerjoin_code + join_match.group(0))

    # Add market_cap to the stocks.append({}) dictionary
    append_pattern = r'(stocks\.append\(\{[^}]+})'
    append_match = re.search(append_pattern, func_content, re.DOTALL)

    if append_match:
        append_block = append_match.group(1)
        # Add market_cap before the closing }
        if '"market_cap"' not in append_block:
            new_append_block = append_block.rstrip('}') + ',\n            "market_cap": float(row.market_cap) if row.market_cap else None\n        }'
            func_content = func_content.replace(append_block, new_append_block)

    # Replace the function in content
    content = content.replace(match.group(1), func_content)
    print(f"Updated {screener_func}")

# Write back
with open(SCREENERS_FILE, 'w') as f:
    f.write(content)

print("\nDone! Market cap added to all screeners.")
