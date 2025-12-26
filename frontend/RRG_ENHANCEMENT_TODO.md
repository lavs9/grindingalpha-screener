# RRG Charts Enhancement TODO

## Current Status (2025-12-26)

✅ **Completed:**
- Basic RRG scatter plot with 120 indices
- Quadrant classification (Leading, Weakening, Lagging, Improving)
- Color-coded visualization
- Sector details data table
- Database schema updated with `sector_category` and `is_sectoral` columns
- Sector/thematic index mapping created (`backend/data/sector_index_mapping.json`)

⏳ **Not Yet Implemented:**
- RRG tails/trails (lines showing historical movement)
- Sector filtering (only show sectoral/thematic indices)
- Timeframe selector (Daily/Weekly/Monthly candles)
- Tail length control (adjustable lookback period)
- Historical RRG data points from backend

---

## Requirements (Based on Competition Analysis)

### 1. RRG Tails/Trails Implementation

**Current:** Single point per index (snapshot)

**Required:** Line connecting historical positions showing sector rotation path

**Example:**
```
Current position (dot) → connected by line → Previous positions (trail)
```

**Backend Changes Needed:**
- New endpoint: `GET /api/v1/screeners/rrg-historical`
- Query params:
  - `timeframe`: 'daily' | 'weekly' | 'monthly'
  - `tail_length`: number (e.g., 5 for 5-period lookback)
  - `benchmark`: string (default: 'NIFTY')
  - `sectors`: array of sector categories (optional filter)

**Response Format:**
```json
{
  "screener": "RRG Charts Historical",
  "benchmark": "NIFTY",
  "timeframe": "daily",
  "tail_length": 5,
  "date_range": {
    "start": "2024-12-19",
    "end": "2024-12-24"
  },
  "results": [
    {
      "index_symbol": "BANKNIFTY",
      "sector_category": "Banking",
      "display_name": "Nifty Bank",
      "historical_points": [
        {
          "date": "2024-12-19",
          "rs_ratio": 99.5,
          "rs_momentum": -0.5,
          "quadrant": "Lagging"
        },
        {
          "date": "2024-12-20",
          "rs_ratio": 99.8,
          "rs_momentum": 0.2,
          "quadrant": "Improving"
        },
        {
          "date": "2024-12-24",
          "rs_ratio": 100.2,
          "rs_momentum": 1.5,
          "quadrant": "Leading"
        }
      ]
    }
  ]
}
```

**Frontend Changes:**
- Update `RRGChart` component to draw lines connecting points
- Use Plotly.js `lines` mode instead of just `markers`
- Different line styles for different quadrant transitions

### 2. Sector Filtering

**Database Migration:**
```sql
-- Already created: abc123456789_add_sector_category_to_index_ohlcv.py
-- Columns: sector_category (String), is_sectoral (Boolean)
```

**Populate Sector Data:**
```python
# Script needed: backend/scripts/populate_sector_categories.py
# Read from: backend/data/sector_index_mapping.json
# Update: index_ohlcv_daily table with sector_category and is_sectoral
```

**Frontend Filter UI:**
```tsx
// Add to RRG page:
- Checkbox: "Show Sectoral Only" (filters is_sectoral = 1)
- Checkbox: "Show Thematic Only" (filters type = 'Thematic')
- Multi-select: Specific sectors (Banking, IT, Pharma, etc.)
```

### 3. Timeframe Selector

**Backend:**
- Calculate RRG metrics on different timeframes:
  - Daily: Use daily candles (current implementation)
  - Weekly: Aggregate to weekly candles, calculate weekly RS-Ratio/RS-Momentum
  - Monthly: Aggregate to monthly candles

**Frontend:**
```tsx
<Select value={timeframe} onValueChange={setTimeframe}>
  <SelectItem value="daily">Daily</SelectItem>
  <SelectItem value="weekly">Weekly</SelectItem>
  <SelectItem value="monthly">Monthly</SelectItem>
</Select>
```

### 4. Tail Length Control

**Frontend:**
```tsx
<Slider
  min={3}
  max={20}
  step={1}
  value={tailLength}
  onValueChange={setTailLength}
  label={`Tail Length: ${tailLength} periods`}
/>
```

**Backend:**
- Use `tail_length` param to return N historical data points per index
- Default: 5 periods
- Max: 20 periods (to avoid overloading visualization)

---

## Implementation Plan

### Phase 1: Backend Enhancement (2-3 hours)

1. **Create sector population script**
   ```bash
   python backend/scripts/populate_sector_categories.py
   ```
   - Read `sector_index_mapping.json`
   - Update all existing index_ohlcv_daily records
   - Set sector_category and is_sectoral based on mapping

2. **Run migration**
   ```bash
   alembic upgrade head
   ```

3. **Create enhanced RRG endpoint**
   - File: `backend/app/api/v1/screeners.py`
   - Function: `get_rrg_charts_historical()`
   - Calculate historical RS-Ratio/RS-Momentum points
   - Support timeframe aggregation (daily/weekly/monthly)

4. **Test endpoint**
   ```bash
   curl "http://localhost:8001/api/v1/screeners/rrg-historical?timeframe=daily&tail_length=5"
   ```

### Phase 2: Frontend Enhancement (2-3 hours)

1. **Update RRGChart component**
   - Change Plotly traces from `markers+text` to `markers+lines+text`
   - Draw lines connecting historical points
   - Add arrow heads to show direction
   - Different line colors per quadrant

2. **Add filter controls**
   - Shadcn Checkbox for sectoral/thematic filter
   - Shadcn Multi-select for sector categories
   - Update chart when filters change

3. **Add timeframe selector**
   - Shadcn Select component
   - Re-fetch data when timeframe changes

4. **Add tail length slider**
   - Shadcn Slider component
   - Default: 5, Min: 3, Max: 20

### Phase 3: Testing & Polish (1 hour)

1. **Test with real data**
   - Verify tails display correctly
   - Check quadrant transitions
   - Test filters

2. **Performance optimization**
   - Limit indices displayed (max 30-40 for readability)
   - Debounce filter changes
   - Cache API responses

3. **UI/UX polish**
   - Add loading states
   - Error handling
   - Tooltips explaining metrics

---

## Files to Create/Modify

### Backend

**New Files:**
- `backend/scripts/populate_sector_categories.py` - Populate sector data
- `backend/app/services/calculators/rrg_historical_calculator.py` - Calculate historical RRG points

**Modified Files:**
- `backend/app/api/v1/screeners.py` - Add `get_rrg_charts_historical()` endpoint
- `backend/app/models/timeseries.py` - Already updated ✅

### Frontend

**Modified Files:**
- `frontend/components/charts/rrg-chart.tsx` - Add tails/trails visualization
- `frontend/app/screeners/rrg/page.tsx` - Add filter controls, timeframe selector, tail length slider
- `frontend/lib/api/screeners.ts` - Add `fetchRRGChartsHistorical()` function
- `frontend/lib/types/screener.ts` - Add historical RRG response types

---

## Reference: Competition RRG Features

**Observed Features:**
1. ✅ Tails showing 5-period historical movement
2. ✅ Clean visualization (20-30 indices max)
3. ✅ Only sectoral/thematic indices (no broad market)
4. ✅ Smooth line interpolation
5. ✅ Arrow heads showing direction
6. ⏳ Weekly timeframe (need to add)

**Visual Characteristics:**
- Tail color matches quadrant position
- Thicker lines for recent movement
- Index labels only on latest position
- Clean crosshairs at RS-Ratio=100, RS-Momentum=0

---

## Notes

- Current implementation uses Plotly.js (good choice for interactive charts)
- Backend has all raw data (index_ohlcv_daily with 113K+ records)
- Need to calculate historical RS-Ratio/RS-Momentum on-the-fly
- Consider caching historical calculations for performance

---

## Estimated Effort

- **Backend:** 3-4 hours
  - Sector population: 30 min
  - Historical RRG calculation: 2 hours
  - Endpoint creation: 1 hour
  - Testing: 30 min

- **Frontend:** 3-4 hours
  - Tail visualization: 2 hours
  - Filter UI: 1 hour
  - Timeframe/tail controls: 30 min
  - Testing & polish: 30 min

**Total:** 6-8 hours for complete RRG enhancement

---

## Next Session Action Items

1. Run migration: `alembic upgrade head`
2. Create and run sector population script
3. Build historical RRG backend endpoint
4. Update frontend chart with tails
5. Add all filter controls
6. Test with real data
7. Compare with competition screenshot
8. Iterate based on feedback
