Updated Finalized List of Screeners/Scanners
Based on the additional input from TradersLab.io (the provided dashboard image showing "Equal Weight NDX Breadth Snapshot" with advances/declines, new highs/lows, % above KMAs, and McClellan charts for breadth analysis) and a deep review of Jeff Sun's Substack guide, I've refined the list.
The TradersLab dashboard emphasizes equal-weighted breadth metrics (e.g., NDX equivalent to Nifty 50/500), McClellan Oscillator/Summation Index for momentum divergence, and % stocks above key moving averages (KMAs like SMA20/50/200)—this enhances the Breadth Metrics Dashboard (Section 10) with McClellan components and equal-weighting specifics.
From Jeff Sun's guide (verified as of October 29, 2025):

Core Enhancements: Adds ADR% (Average Daily Range % for volatility/position sizing), RVOL (Relative Volume, already partial but now with ORH/M30 Re-ORH for entry confirmation), ATR% multiples from 50-MA (expands ATR Extension with XxATR% for partial profits), VCP (Volatility Contraction Pattern for pre-breakout contraction), and PEAD (Post-Earnings Drift, but requires earnings data—flagged as additional).
Glossary/Process Ties: Incorporates LoD distance to ATR (<60% for tight entries), R-Multiple for risk (T+3 tracking), VARS/VARW (Volatility-Adjusted RS/Weakness for better percentile calcs).
Indicators: Swing Data (integrates ADR%, RVOL, float %) and ATR% from 50-MA scripts—add to daily calcs for screeners like MA Stacked Breakouts and Momentum Watchlist.
No Major New Screeners: These refine existing ones (e.g., add VCP filter to Breakouts; ADR% to High-Volume Movers for sizing). PEAD needs new data, so it's in the "additional" section below.

The list remains NSE-adapted, using stored data (OHLCV, market cap, industry/sector, bulk/block deals). Universal filters: Listed equities/ETFs, market cap ≥ ₹100 crore, exclude surveillance-flagged, volume ≥100K.

For each:
Purpose: Updated with enhancements.
Data Required to Calculate: Inputs, now including new indicators.
Data to be Shown: Outputs, with refinements.

1. 4% Daily Breakouts/Gainers (Inspired by @PradeepBonde - Stockbee; Enhanced with Jeff Sun's ORH/M30 Re-ORH)
Purpose: Momentum stocks up ≥4% with volume surge; now filters for M30 Re-ORH (post-open 30-min reclaim of opening range high) for confirmation, adapting to NSE intraday if available (or proxy with EOD).
Data Required to Calculate:

Daily OHLCV (open, close, volume; intraday for ORH if extended).
Previous day's volume.
Opening range (first 30-min high from OHLCV or proxy).
Market cap (filter ≥ ₹100 crore).

Data to be Shown:

Ticker, % Change, Volume, Rel Volume (RVOL), M30 Re-ORH (Yes/No), Market Cap.
Sorted by % Change; separate +4%/-4% lists.

2. 20% Weekly Moves (Inspired by @PradeepBonde - Stockbee; Enhanced with ADR% for Volatility Context)
Purpose: Extreme swings for pattern study; add ADR% to flag high-volatility moves (e.g., >3% for expansive behavior).
Data Required to Calculate:

Historical OHLCV (closes over 5 days).
Volume avg ≥100K.
ADR% (avg (high-low)/close * 100 over 20 days).
Market cap (filter ≥ ₹100 crore).

Data to be Shown:

Ticker, Weekly % Change, Volume Avg, ADR%, Market Cap, Industry/Sector.
Separate +20%/-20% lists, sorted by absolute change.

3. High-Volume Movers (Inspired by @PradeepBonde - Stockbee 9M; Enhanced with Jeff Sun's RVOL and Swing Data)
Purpose: Volume surges (≥5M shares NSE-adapted); integrate RVOL and float % (if added to stored data) for liquidity.
Data Required to Calculate:

Daily OHLCV (volume).
50-day avg volume for RVOL ≥1.25.
Market cap (filter ≥ ₹100 crore).
Optional: Bulk/block deals.

Data to be Shown:

Ticker, Volume, RVOL, % Change, Float % (if available), Market Cap, Industry/Sector.
Sorted by volume descending.

4. Relative Strength Leaders ("97 Club" Style, Inspired by @SteveDJacobs; Enhanced with VARS from Jeff Sun)
Purpose: Top 3% RS; use Volatility-Adjusted RS (VARS: RS / ATR% to normalize for vol).
Data Required to Calculate:

Historical OHLCV (closes for changes).
ATR% for VARS adjustment.
Market cap (filter ≥ ₹100 crore).

Data to be Shown:

Ticker, VARS Day/Week/Month, % Change (1M), Market Cap, Industry/Sector.
Highlight ≥97; sorted by average VARS.

5. MA Stacked Breakouts (Inspired by @SteveDJacobs Qullamaggie and @FranVezz; Enhanced with VCP and ATR% from 50-MA)
Purpose: Uptrend breakouts with range ≥50%; add VCP (vol contraction: narrowing ranges pre-breakout) and XxATR% from 50-MA for extensions.
Data Required to Calculate:

Historical OHLCV for EMA10, SMA20/50/100/200, 20-day range.
ATR (14-day), ATR% from 50-MA (multiples).
VCP: Consecutive narrowing (high-low) over 3-5 bars.
RS ≥97 (1W/1M/3M/6M percentiles).
Market cap (filter ≥ ₹100 crore).

Data to be Shown:

Ticker, RS (max), ATR% from 50-MA (e.g., 3x), VCP Score (1-5), Price-to-Range, Market Cap, Industry/Sector.
Sorted by least extension; bold ≥7x.

6. ATR Extension Matrix for Sectors (Inspired by @SteveDJacobs; Enhanced with ADR% Bands)
Purpose: Sector rotations by extensions; add ADR% for volatility bands.
Data Required to Calculate:

Historical OHLCV for sectoral indices.
ATR (14-day), SMA50, ADR% (20-day).

Data to be Shown:

Sector, ATR Extension, ADR%, Weekly % Change, Monthly % Change.
Sorted by extension descending.

7. Leading Industries/Groups (Inspired by @SteveDJacobs and @FranVezz; Enhanced with VARW for Weakness)
Purpose: Top 20% strength; add Volatility-Adjusted Relative Weakness (VARW: inverse VARS) for laggards.
Data Required to Calculate:

Industry/sector mappings.
OHLCV for group strength (weekly/monthly RS/ADR-adjusted).
Daily % changes for top 4.

Data to be Shown:

Industry Group, Weekly Strength (VARS %), Monthly Strength, VARW (for laggards), Top 4 Performers (Tickers, % Change).
Highlight top 20% (green).

8. Stage Analysis Breakdown (Inspired by @SteveDJacobs; Enhanced with LoD ATR Distance)
Purpose: Stage classification; add LoD distance to ATR (<60% for tight Stage 2 entries, per Jeff Sun).
Data Required to Calculate:

Historical OHLCV for EMA10, SMA20/50, ATR, Darvas box.
LoD (daily low) vs. ATR.

Data to be Shown:

% Breakdown by Stage, Counts, Avg LoD ATR %.
Bar chart + table; highlight tight LoD.

9. Momentum Watchlist (Inspired by @FranVezz and @PradeepBonde; Enhanced with PEAD Proxy via Deals)
Purpose: RS + MA holds; use bulk/block deals as PEAD proxy (post-event drift).

Data Required to Calculate:

Historical OHLCV for RS, green candles, SMA50 holds.
Bulk/block deals (catalyst flag).
Market cap (filter ≥ ₹100 crore).

Data to be Shown:

Ticker, RS (1M), Candle Type, LoD ATR % (<60%), Recent Deal (Yes/No), Industry/Sector.
Sorted by least extended.

10. Breadth Metrics Dashboard (Inspired by @SteveDJacobs and @PradeepBonde; Enhanced with TradersLab McClellan and Equal-Weighting)
Purpose: Sentiment via ratios; add McClellan Oscillator/Summation Index (EMA diff of advances/declines) and equal-weighted (per TradersLab image).
Data Required to Calculate:

Daily/historical OHLCV for universes (Nifty 50/500, Composite).
SMA20/50/200, new highs/lows.
Up/down counts (1D/1W/1M); McClellan: 19-day EMA advances - 39-day EMA declines.

Data to be Shown:

Table: Universe (Equal-Weighted), Up/Down Ratio, % Above SMA20/50/200, McClellan Oscillator, New Highs/Lows.
Stacked bars + line charts (McClellan divergence).

11. RRG Charts for Sectoral Indices (As Requested; Enhanced with ADR% Coloring)
Purpose: Sector rotation; color points by ADR% (high vol = red tails for risk).
Data Required to Calculate:

Historical OHLCV for sectors/benchmark (Nifty 50).
RS-Ratio, RS-Momentum (ROC), smoothed MAs.
ADR% for coloring.

Data to be Shown:

Scatter: X (RS-Ratio), Y (RS-Momentum), tails (10 weeks), quadrants, ADR% color scale.
Hover: RS values, % change.

Updated List of Daily Calculated Data Points
Post-EOD (8-9 PM IST) cron: Compute/store in ClickHouse for screeners. New additions from Jeff Sun/TradersLab: ADR%, VARS/VARW, VCP score, LoD ATR %, McClellan, ORH/M30 proxy.

1. Price Changes: 1D/1W/1M/3M/6M %.
2. Relative Strength (RS): Percentiles; now VARS (RS / ATR%).
3. VARW: Inverse VARS for weakness.
4. Moving Averages: EMA10, SMA20/50/100/200.
5. ATR (14-day): Wilder from OHLC.
6. ATR % and RS: (ATR/close * 100), percentile.
7. ATR % from 50-MA: Multiples (e.g., 3x).
8. ADR%: Avg (high-low)/close * 100 (20 days).
9. ATR Extension: ((close / SMA50) - 1) / (ATR/close).
10. 20-Day Darvas Box: High/low; price-to-range %.
11. RVOL: Today / 50-day avg volume.
12. ORH/M30 Re-ORH: Opening range high; 30-min reclaim (proxy if no intraday).
13. LoD ATR %: (LoD - close) / ATR * 100 (<60% flag).
14. New 20-Day Highs/Lows: Counts.
15. Industry/Sector Strength: Equal-weighted VARS %.
16. RRG Metrics: RS-Ratio, RS-Momentum, ADR% color.
17. Candle Type: Green/Red % change.
18. Up/Down Counts: 1D/1W/1M.
19. McClellan Oscillator/Summation: EMA diff of advances/declines.
20. VCP Score: Narrowing ranges (1-5 over 3-5 bars).
21. Stage Classification: 1-4 with LoD flag.

These support all screeners; compute incrementally for efficiency.