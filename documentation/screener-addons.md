12. RSI Overbought/Oversold Scanner
Purpose: Flags extremes/divergences for reversals.
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi
(14-period Wilder RSI: RS = Avg Gain / Avg Loss (smoothed); RSI = 100 - 100/(1+RS). Overbought >70, oversold <30.)
Data Required: Historical closes (14+ periods).
Data to be Shown: Ticker, RSI, Divergence (Bullish/Bearish), % Change (1W).
Historical: Retain for divergences.
13. MACD Crossover Scanner
Purpose: Trend/momentum shifts via crossovers.
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator
(MACD Line = 12-EMA - 26-EMA closes; Signal = 9-EMA of Line; Histogram = Line - Signal.)
Data Required: Historical closes (26+ periods).
Data to be Shown: Ticker, Crossover Type, Histogram, % Change (1M).
Historical: Retain for histogram trends.
14. Bollinger Band Squeeze Scanner
Purpose: Low-vol contractions for breakouts.
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/bollinger-bands
(Middle = 20-SMA closes; Upper/Lower = Middle ± 2 std dev; Bandwidth = (Upper-Lower)/Middle.)
Data Required: Historical closes/highs/lows (20+ periods).
Data to be Shown: Ticker, Bandwidth %, Breakout Direction, % Change (1W).
Historical: Retain for squeeze history.
15. Chart Patterns Scanner (Flags/Pennants)
Purpose: Continuation consolidations.
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/flag-pennant
(Flag: Parallel channel against trend; Pennant: Converging triangle. Preceded by pole; breakout on volume.)
Data Required: Historical OHLCV (20+ bars for channel detection).
Data to be Shown: Ticker, Pattern Type, Duration, Breakout RVOL.
Historical: Retain for pattern validation.


16. ADX Trend Strength Scanner
Purpose: Strong trends (>25 ADX).
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx
(+DI/-DI from directional movement; DX = |+DI - -DI| / (+DI + -DI); ADX = 14-EMA of DX.)
Data Required: Historical highs/lows/closes (14+ periods).
Data to be Shown: Ticker, ADX, Direction (+DI > -DI bullish), % Change (1M).
Historical: Retain for trend persistence.
Bonus: McClellan Oscillator (Enhance Breadth Section 10)
Calculation Link: https://chartschool.stockcharts.com/table-of-contents/market-indicators/mcclellan-oscillator
(Ratio-Adjusted Net Advances = (Adv - Decl)/(Adv + Decl); Oscillator = 19-EMA RANA - 39-EMA RANA.)
Data Required: Daily advances/declines (from NSE breadth data—add if available).
Data to be Shown: In Breadth Dashboard: Oscillator value, Summation cumulative.
Historical: Retain for divergence charts.
Implement these in daily calcs—links ensure exact StockCharts formulas. No extra data beyond OHLCV (except McClellan needs A/D counts).