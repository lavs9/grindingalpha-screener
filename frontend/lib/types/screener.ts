/**
 * TypeScript Type Definitions for Screeners
 *
 * Matches backend API response schemas.
 */

// Common types
export interface ScreenerResponse<T> {
  screener: string;
  date: string;
  count: number;
  results: T[];
}

// 4% Breakouts
export interface Breakout4PercentStock {
  symbol: string;
  name: string;
  change_1d_percent: number;
  rvol: number;
  volume: number;
  close: number;
  stage: number;
  stage_detail: string;
  market_cap: number | null;
}

// RS Leaders (97 Club)
export interface RSLeaderStock {
  symbol: string;
  name: string;
  rs_percentile: number;
  vars_score: number;
  change_1m_percent: number;
  change_1w_percent: number;
  stage: number;
  stage_detail: string;
  market_cap: number | null;
}

// High Volume Movers
export interface HighVolumeStock {
  symbol: string;
  name: string;
  volume: number;
  rvol: number;
  change_1d_percent: number;
  close: number;
  market_cap: number | null;
}

// MA Stacked Breakouts
export interface MAStackedStock {
  symbol: string;
  name: string;
  rs_percentile: number;
  vcp_score: number;
  stage: number;
  stage_detail: string;
  atr_extension: number;
  darvas_position: number;
  market_cap: number | null;
}

// Weekly Movers
export interface WeeklyMoverStock {
  symbol: string;
  name: string;
  change_1w_percent: number;
  change_1d_percent: number;
  adr_percent: number;
  rvol: number;
  stage: number;
  stage_detail: string;
  market_cap: number | null;
}

// Stage Analysis
export interface StageBreakdown {
  stage: number;
  stage_detail: string;
  count: number;
  percentage: number;
  avg_lod_atr_percent: number;
  tight_lod_count: number;
}

export interface StageAnalysisResponse {
  screener: string;
  date: string;
  total_stocks: number;
  breakdown: StageBreakdown[];
}

// Momentum Watchlist
export interface MomentumStock {
  symbol: string;
  name: string;
  rs_percentile: number;
  change_1d_percent: number;
  lod_atr_percent: number | null;
  atr_extension: number | null;
  is_tight: boolean;
  is_green_candle: boolean;
  stage: number;
  stage_detail: string;
  market_cap: number | null;
}

// Breadth Metrics
export interface BreadthMetricsResponse {
  screener: string;
  date: string;
  total_stocks: number;
  up_down: {
    up_count: number;
    down_count: number;
    up_down_ratio: number;
  };
  ma_analysis: {
    above_sma20_count: number;
    above_sma20_percent: number;
    above_sma200_count: number;
    above_sma200_percent: number;
  };
  new_highs_lows: {
    new_20d_highs: number;
    new_20d_lows: number;
    high_low_ratio: number;
  };
  mcclellan: {
    oscillator: number;
    summation: number;
    universe_up_count: number;
    universe_down_count: number;
  };
}

// Leading Industries
export interface TopPerformer {
  symbol: string;
  name: string;
  change_1m_percent: number;
  market_cap: number | null;
}

export interface LeadingIndustry {
  industry: string;
  sector: string;
  avg_vars: number;
  avg_varw: number;
  avg_weekly_change_percent: number;
  avg_monthly_change_percent: number;
  stock_count: number;
  top_performers: TopPerformer[];
}

// RRG Charts
export interface RRGPoint {
  date: string;
  rs_ratio: number;
  rs_momentum: number;
  quadrant: 'Leading' | 'Weakening' | 'Lagging' | 'Improving';
}

export interface RRGSector {
  index_symbol: string;
  sector_category: string | null;
  rs_ratio: number;
  rs_momentum: number;
  quadrant: 'Leading' | 'Weakening' | 'Lagging' | 'Improving';
  weekly_change_percent: number;
  current_close: number;
  historical_points: RRGPoint[];
}

export interface RRGChartsResponse {
  screener: string;
  date: string;
  benchmark: string;
  benchmark_close: number;
  short_period: number;
  long_period: number;
  tail_length: number;
  timeframe: 'daily' | 'weekly' | 'monthly';
  show_sectoral_only: boolean;
  count: number;
  quadrant_counts: {
    Leading: number;
    Weakening: number;
    Lagging: number;
    Improving: number;
  };
  results: RRGSector[];
}

// RSI Scanner
export interface RSIStock {
  symbol: string;
  name: string;
  rsi_14: number;
  is_oversold: boolean;
  is_overbought: boolean;
  close: number;
  change_1w_percent: number | null;
  volume: number;
  market_cap: number | null;
}

// MACD Crossover
export interface MACDStock {
  symbol: string;
  name: string;
  macd_line: number;
  macd_signal: number;
  macd_histogram: number;
  crossover_type: string;  // "Bullish", "Bearish", "None"
  close: number;
  change_1m_percent: number | null;
  market_cap: number | null;
}

// Bollinger Band Squeeze
export interface BollingerStock {
  symbol: string;
  name: string;
  bb_bandwidth_percent: number;
  is_squeeze: boolean;
  close: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  breakout_direction: string;  // "Above Upper", "Below Lower", "Within Bands"
  change_1w_percent: number | null;
  market_cap: number | null;
}

// ADX Trend Strength
export interface ADXStock {
  symbol: string;
  name: string;
  adx_14: number;
  di_plus: number;
  di_minus: number;
  trend_direction: string;  // "Bullish", "Bearish", "Neutral"
  is_strong_trend: boolean;
  close: number;
  change_1m_percent: number | null;
  market_cap: number | null;
}
