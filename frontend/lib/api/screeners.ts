/**
 * Screener API Service Functions
 *
 * Functions to fetch data from backend screener endpoints.
 */

import apiClient from './client';
import type {
  ScreenerResponse,
  Breakout4PercentStock,
  RSLeaderStock,
  HighVolumeStock,
  MAStackedStock,
  WeeklyMoverStock,
  StageAnalysisResponse,
  MomentumStock,
  BreadthMetricsResponse,
  LeadingIndustry,
  RRGChartsResponse,
  RSIStock,
  MACDStock,
  BollingerStock,
  ADXStock,
} from '../types/screener';

// 1. 4% Daily Breakouts
export async function fetch4PercentBreakouts(params?: {
  targetDate?: string;
  minChange?: number;
  minRvol?: number;
  limit?: number;
}): Promise<ScreenerResponse<Breakout4PercentStock>> {
  const response = await apiClient.get('/screeners/breakouts-4percent', {
    params: {
      target_date: params?.targetDate,
      min_change: params?.minChange,
      min_rvol: params?.minRvol,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 2. RS Leaders (97 Club)
export async function fetchRSLeaders(params?: {
  targetDate?: string;
  minRs?: number;
  limit?: number;
}): Promise<ScreenerResponse<RSLeaderStock>> {
  const response = await apiClient.get('/screeners/rs-leaders', {
    params: {
      target_date: params?.targetDate,
      min_rs: params?.minRs,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 3. High Volume Movers
export async function fetchHighVolume(params?: {
  targetDate?: string;
  minRvol?: number;
  limit?: number;
}): Promise<ScreenerResponse<HighVolumeStock>> {
  const response = await apiClient.get('/screeners/high-volume', {
    params: {
      target_date: params?.targetDate,
      min_rvol: params?.minRvol,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 4. MA Stacked Breakouts
export async function fetchMAStacked(params?: {
  targetDate?: string;
  minVcp?: number;
  limit?: number;
}): Promise<ScreenerResponse<MAStackedStock>> {
  const response = await apiClient.get('/screeners/ma-stacked', {
    params: {
      target_date: params?.targetDate,
      min_vcp: params?.minVcp,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 5. 20% Weekly Movers
export async function fetchWeeklyMovers(params?: {
  targetDate?: string;
  minChange?: number;
  direction?: 'up' | 'down' | 'both';
  limit?: number;
}): Promise<ScreenerResponse<WeeklyMoverStock>> {
  const response = await apiClient.get('/screeners/weekly-movers', {
    params: {
      target_date: params?.targetDate,
      min_change: params?.minChange,
      direction: params?.direction,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 6. Stage Analysis Breakdown
export async function fetchStageAnalysis(params?: {
  targetDate?: string;
}): Promise<StageAnalysisResponse> {
  const response = await apiClient.get('/screeners/stage-analysis', {
    params: {
      target_date: params?.targetDate,
    }
  });
  return response.data;
}

// 7. Momentum Watchlist
export async function fetchMomentumWatchlist(params?: {
  targetDate?: string;
  minRs?: number;
  maxLodAtr?: number;
  limit?: number;
}): Promise<ScreenerResponse<MomentumStock>> {
  const response = await apiClient.get('/screeners/momentum-watchlist', {
    params: {
      target_date: params?.targetDate,
      min_rs: params?.minRs,
      max_lod_atr: params?.maxLodAtr,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 8. Breadth Metrics Dashboard
export async function fetchBreadthMetrics(params?: {
  targetDate?: string;
}): Promise<BreadthMetricsResponse> {
  const response = await apiClient.get('/screeners/breadth-metrics', {
    params: {
      target_date: params?.targetDate,
    }
  });
  return response.data;
}

// 9. Leading Industries/Groups
export async function fetchLeadingIndustries(params?: {
  targetDate?: string;
  limit?: number;
}): Promise<ScreenerResponse<LeadingIndustry>> {
  const response = await apiClient.get('/screeners/leading-industries', {
    params: {
      target_date: params?.targetDate,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 10. RRG Charts for Sectoral Indices
export async function fetchRRGCharts(params?: {
  targetDate?: string;
  benchmark?: string;
  lookbackDays?: number;
  timeframe?: 'daily' | 'weekly' | 'monthly';
  tailLength?: number;
}): Promise<RRGChartsResponse> {
  const response = await apiClient.get('/screeners/rrg-charts', {
    params: {
      target_date: params?.targetDate,
      benchmark: params?.benchmark,
      lookback_days: params?.lookbackDays,
      timeframe: params?.timeframe,
      tail_length: params?.tailLength,
    }
  });
  return response.data;
}

// 11. RSI Scanner
export async function fetchRSIScanner(params?: {
  targetDate?: string;
  minRsi?: number;
  maxRsi?: number;
  showOversold?: boolean;
  showOverbought?: boolean;
  limit?: number;
}): Promise<ScreenerResponse<RSIStock>> {
  const response = await apiClient.get('/screeners/rsi-scanner', {
    params: {
      target_date: params?.targetDate,
      min_rsi: params?.minRsi,
      max_rsi: params?.maxRsi,
      show_oversold: params?.showOversold,
      show_overbought: params?.showOverbought,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 12. MACD Crossover
export async function fetchMACDCrossover(params?: {
  targetDate?: string;
  crossoverType?: string;
  minHistogram?: number;
  limit?: number;
}): Promise<ScreenerResponse<MACDStock>> {
  const response = await apiClient.get('/screeners/macd-crossover', {
    params: {
      target_date: params?.targetDate,
      crossover_type: params?.crossoverType,
      min_histogram: params?.minHistogram,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 13. Bollinger Band Squeeze
export async function fetchBollingerSqueeze(params?: {
  targetDate?: string;
  maxBandwidth?: number;
  showSqueezeOnly?: boolean;
  limit?: number;
}): Promise<ScreenerResponse<BollingerStock>> {
  const response = await apiClient.get('/screeners/bollinger-squeeze', {
    params: {
      target_date: params?.targetDate,
      max_bandwidth: params?.maxBandwidth,
      show_squeeze_only: params?.showSqueezeOnly,
      limit: params?.limit,
    }
  });
  return response.data;
}

// 14. ADX Trend Strength
export async function fetchADXTrend(params?: {
  targetDate?: string;
  minAdx?: number;
  trendDirection?: string;
  limit?: number;
}): Promise<ScreenerResponse<ADXStock>> {
  const response = await apiClient.get('/screeners/adx-trend', {
    params: {
      target_date: params?.targetDate,
      min_adx: params?.minAdx,
      trend_direction: params?.trendDirection,
      limit: params?.limit,
    }
  });
  return response.data;
}
