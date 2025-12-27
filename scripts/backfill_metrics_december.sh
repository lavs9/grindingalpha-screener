#!/bin/bash

# Backfill Technical Metrics for December 2025
# This script calculates all 64 technical indicators (including RSI, MACD, Bollinger, ADX)
# for each trading day in December 2025.

set -e  # Exit on error

BASE_URL="http://localhost:8001"
START_DATE="2025-12-01"
END_DATE="2025-12-26"

echo "===== Backfilling Technical Metrics for December 2025 ====="
echo "Date Range: $START_DATE to $END_DATE"
echo "Target URL: $BASE_URL/api/v1/metrics/calculate-daily"
echo ""

# Convert dates to arrays
current_date="$START_DATE"
end_date="$END_DATE"

while [[ "$current_date" < "$end_date" ]] || [[ "$current_date" == "$end_date" ]]; do
    echo "------------------------------------------------------------"
    echo "Processing: $current_date"
    echo "------------------------------------------------------------"

    # Call the metrics calculation endpoint
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/metrics/calculate-daily?target_date=$current_date")

    # Extract HTTP code (last line)
    http_code=$(echo "$response" | tail -n 1)

    # Extract response body (all but last line)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -eq 200 ]]; then
        # Parse success response
        records_inserted=$(echo "$body" | grep -o '"records_inserted":[0-9]*' | cut -d':' -f2)
        records_updated=$(echo "$body" | grep -o '"records_updated":[0-9]*' | cut -d':' -f2)

        echo "✅ SUCCESS: $current_date"
        echo "   Inserted: $records_inserted records"
        echo "   Updated: $records_updated records"
    else
        echo "❌ FAILED: $current_date (HTTP $http_code)"
        echo "   Response: $body"
    fi

    echo ""

    # Move to next day
    current_date=$(date -j -v+1d -f "%Y-%m-%d" "$current_date" +"%Y-%m-%d" 2>/dev/null || date -d "$current_date + 1 day" +"%Y-%m-%d")

    # Small delay to avoid overwhelming the server
    sleep 1
done

echo "===== Backfill Complete ====="
echo ""
echo "Verify results with:"
echo "  curl http://localhost:8001/api/v1/status/data-quality"
echo "  docker exec screener_postgres psql -U screener_user -d screener_db -c \"SELECT date, COUNT(*) FROM calculated_metrics WHERE date >= '2025-12-01' GROUP BY date ORDER BY date;\""
