Market Metrics Dashboard Documentation: Screeners, Scanners, and Calculations
Introduction
This document provides a comprehensive guide for building the codebase of the Market Metrics Dashboard POC, adapted for the NSE Indian stock market. It compiles the finalized list of screeners/scanners based on research from X accounts (@SteveDJacobs, @PradeepBonde, @FranVezz), TradersLab.io dashboard, and Jeff Sun's Substack process. The dashboard uses stored data: historical/daily OHLCV (Open, High, Low, Close, Volume), market cap, industry/sector mappings, and bulk/block deals.
The focus is on momentum, relative strength (RS), price action, volume, and breadth screeners. All are NSE-adapted (e.g., universes like Nifty 50/500, market cap ≥ ₹100 crore, exclude surveillance-flagged, volume ≥100K for liquidity). Implementation uses Python (FastAPI backend, frontend, postgres supabase DB).
Key Principles

Daily Processing: Run EOD (8-9 PM IST) cron to ingest data, compute metrics, and update screeners.
Historical Storage:
Required for Most: Store historical OHLCV/market cap (at least 2 years, ideally 5) in postgres supabase for calculations like MAs (need 200+ days), RS percentiles, RRG tails (100 weeks), McClellan trends. This enables backtesting/trending (e.g., stage breakdowns over time).
Optional/Non-Historical: Pure daily screeners (e.g., 4% gainers) can overwrite snapshots, but retain history for charts/analysis.
Decision Rule: Keep historical if screener involves time-series (e.g., RRG, breadth charts) or patterns (e.g., VCP over 3-5 bars). Purge old data (>5 years) for storage efficiency.

Universal Filters: Apply to all: NSE equities/ETFs, market cap ≥ ₹100 crore, no surveillance flags, volume ≥100K.
Tech Stack Notes: Use pandas/numpy/ta-lib for calcs; postgres supabase MergeTree for time-series (partition by date/ticker); Dash for visuals (tables/charts).

Section 1: Daily Calculated Data Points
These are pre-computed EOD metrics stored in postgres supabase (e.g., 'daily_metrics' table with date/ticker keys). Compute universe-wide (full NSE listed stocks) for percentiles. Retain historical (append daily) for trends/backtesting.

Price Changes: 1D/1W/1M/3M/6M % = (close_t / close_t-n - 1) * 100. (From OHLCV.)
Relative Strength (RS): Percentile rank of price changes vs. universe (numpy.percentile or postgres supabase quantile); now VARS = RS / ATR%.
VARW (Volatility-Adjusted Relative Weakness): Inverse VARS (1 - VARS) for laggards.
Moving Averages: EMA10 (exponential), SMA20/50/100/200 (simple) via pandas/ta-lib.
ATR (14-day): Wilder ATR = max(high-low, |high-prev_close|, |low-prev_close|), averaged over 14 days.
ATR % and RS: (ATR / close * 100), percentile vs. universe.
ATR % from 50-MA: Multiples, e.g., ((close / SMA50) - 1) / (ATR / close).
ADR% (Average Daily Range %): Avg ((high - low) / close * 100) over 20 days.
ATR Extension: ((close / SMA50) - 1) / (ATR / close).
20-Day Darvas Box: Max high/min low over 20 days; price-to-range % = (close - low) / (high - low) * 100.
RVOL (Relative Volume): Today's volume / 50-day avg volume.
ORH/M30 Re-ORH: Opening range high (first 30-min high, proxy from daily if no intraday); M30 reclaim (close > ORH post-30 min).
LoD ATR %: ((low_of_day - close) / ATR * 100); flag <60%.
New 20-Day Highs/Lows: Count if high ≥ max(20-day highs) or low ≤ min(20-day lows).
Industry/Sector Strength: Equal-weighted weekly/monthly % changes/VARS for groups (aggregate stock OHLCV by sector).
RRG Metrics: RS-Ratio = (sector close / benchmark close) * 100 (normalized); RS-Momentum = 1-week ROC of RS-Ratio; smoothed with 1-week MA.
Candle Type: Green if close ≥ open (with % change); red otherwise.
Up/Down Counts: # stocks up/down over 1D/1W/1M for universes.
McClellan Oscillator/Summation: Oscillator = 19-day EMA (advances - declines) - 39-day EMA; Summation = cumulative Oscillator.
VCP Score: 1-5 based on narrowing (high-low) over 3-5 bars (e.g., each narrower bar +1).
Stage Classification: 1 (close < all MAs), 2A (close > MAs but <100% Darvas), 2B (at 100% Darvas), 2C (≥7x ATR from SMA50), 3 (topping: falling but above some MAs), 4 (declining: below MAs); with LoD flag.

Computation Flow:

Ingest EOD OHLCV/market cap/sector data.
Update historical tables (append new rows).
Run batch calcs (e.g., pandas on universe DataFrame or postgres supabase SQL for percentiles).
Store with date for history (e.g., query past McClellan for charts).

Section 2: Detailed Screener/Scanner Descriptions
Each screener outputs to Dash (tables/charts). Historical: Store daily results in postgres supabase for trending (e.g., view past RRG rotations), unless noted as snapshot-only.
1. 4% Daily Breakouts/Gainers
Purpose: Momentum stocks up ≥4% with volume surge; M30 Re-ORH for confirmation.
Data Required to Calculate: Daily OHLCV (open, close, volume; prior day vol); market cap.
Data to be Shown: Table: Ticker, % Change, Volume, RVOL, M30 Re-ORH (Yes/No), Market Cap. Separate +4%/-4% lists, sorted by % Change.
Historical Storage: Snapshot-only (daily refresh), but retain for breadth trends.
2. 20% Weekly Moves
Purpose: Extreme swings for patterns; ADR% for vol context.
Data Required to Calculate: Historical OHLCV (5-day closes, vol avg); ADR%; market cap.
Data to be Shown: Table: Ticker, Weekly % Change, Volume Avg, ADR%, Market Cap, Industry/Sector. Separate +20%/-20%, sorted by absolute change.
Historical Storage: Retain (append daily rolls) for pattern studies over time.
3. High-Volume Movers
Purpose: Volume surges; RVOL and float % for liquidity (float from market cap proxy if not stored).
Data Required to Calculate: Daily OHLCV (volume, 50-day avg); market cap.
Data to be Shown: Table: Ticker, Volume, RVOL, % Change, Float % (cap-derived), Market Cap, Industry/Sector. Sorted by volume.
Historical Storage: Snapshot-only, but retain for volume trend analysis.
4. Relative Strength Leaders ("97 Club" Style)
Purpose: Top 3% RS; VARS for vol adjustment.
Data Required to Calculate: Historical OHLCV (changes); ATR% for VARS; market cap.
Data to be Shown: Table: Ticker, VARS Day/Week/Month, % Change (1M), Market Cap, Industry/Sector. Highlight ≥97; sorted by avg VARS.
Historical Storage: Retain (daily RS history) for leadership trends.
5. MA Stacked Breakouts
Purpose: Uptrend breakouts; VCP and ATR% from 50-MA for extensions.
Data Required to Calculate: Historical OHLCV (MAs, range, ATR/ATR%); VCP score; RS; market cap.
Data to be Shown: Table: Ticker, RS (max), ATR% from 50-MA, VCP Score, Price-to-Range, Market Cap, Industry/Sector. Sorted by least extension; bold ≥7x.
Historical Storage: Retain (VCP needs prior bars) for breakout history.
6. ATR Extension Matrix for Sectors
Purpose: Sector rotations; ADR% bands for vol.
Data Required to Calculate: Historical OHLCV (sector indices: ATR, SMA50, ADR%).
Data to be Shown: Table: Sector, ATR Extension, ADR%, Weekly % Change, Monthly % Change. Sorted by extension.
Historical Storage: Retain (extensions over time) for sector trends.
7. Leading Industries/Groups
Purpose: Top 20% strength; VARW for laggards.
Data Required to Calculate: Industry mappings; OHLCV (group VARS %); daily changes.
Data to be Shown: Table: Group, Weekly VARS %, Monthly VARS, VARW, Top 4 Performers (Tickers, % Change). Highlight top 20%.
Historical Storage: Retain (strength history) for group rotation.
8. Stage Analysis Breakdown
Purpose: Stage classification; LoD ATR % for entries.
Data Required to Calculate: Historical OHLCV (MAs, ATR, Darvas); LoD ATR %.
Data to be Shown: Bar Chart + Table: %/Counts by Stage, Avg LoD ATR %. Highlight tight LoD.
Historical Storage: Retain (daily breakdowns) for market health trends.
9. Momentum Watchlist
Purpose: RS + MA holds; PEAD proxy via deals.
Data Required to Calculate: Historical OHLCV (RS, candles, SMA50); deals; market cap.
Data to be Shown: Table: Ticker, RS (1M), Candle Type, LoD ATR % (<60%), Recent Deal (Yes/No), Industry/Sector. Sorted by least extended.
Historical Storage: Snapshot-only, but retain for watchlist evolution.
10. Breadth Metrics Dashboard
Purpose: Sentiment ratios; McClellan/equal-weighting from TradersLab.
Data Required to Calculate: OHLCV (universes: up/down, % above KMAs, highs/lows); McClellan calcs.
Data to be Shown: Table: Universe (Equal-Weighted), Up/Down Ratio, % Above SMA20/50/200, McClellan Oscillator/Summation, New Highs/Lows. Stacked bars + line charts.
Historical Storage: Retain (McClellan cumulative) for divergence charts.
11. RRG Charts for Sectoral Indices
Purpose: Sector rotation; ADR% coloring for vol risk.
Data Required to Calculate: Historical OHLCV (sectors/benchmark: RS-Ratio/Momentum, smoothed); ADR%.
Data to be Shown: Scatter Plot: X (RS-Ratio), Y (RS-Momentum), tails (10 weeks), quadrants, ADR% colors. Hover: RS values, % change.
Historical Storage: Retain (100+ weeks) for tails/trends.
This documentation is self-contained for codebase building—start with daily calcs in cron, then screeners in FastAPI/Dash.