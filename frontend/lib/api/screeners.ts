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
} from '../types/screener';

// 1. 4% Daily Breakouts
export async function fetch4PercentBreakouts(params?: {
  targetDate?: string;
  minChange?: number;
  minRvol?: number;
  limit?: number;
}): Promise<ScreenerResponse<Breakout4PercentStock>> {
  const response = await apiClient.get('/screeners/breakouts-4percent', { params });
  return response.data;
}

// 2. RS Leaders (97 Club)
export async function fetchRSLeaders(params?: {
  targetDate?: string;
  minRs?: number;
  limit?: number;
}): Promise<ScreenerResponse<RSLeaderStock>> {
  const response = await apiClient.get('/screeners/rs-leaders', { params });
  return response.data;
}

// 3. High Volume Movers
export async function fetchHighVolume(params?: {
  targetDate?: string;
  minRvol?: number;
  limit?: number;
}): Promise<ScreenerResponse<HighVolumeStock>> {
  const response = await apiClient.get('/screeners/high-volume', { params });
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
  const response = await apiClient.get('/screeners/weekly-movers', { params });
  return response.data;
}

// 6. Stage Analysis Breakdown
export async function fetchStageAnalysis(params?: {
  targetDate?: string;
}): Promise<StageAnalysisResponse> {
  const response = await apiClient.get('/screeners/stage-analysis', { params });
  return response.data;
}

// 7. Momentum Watchlist
export async function fetchMomentumWatchlist(params?: {
  targetDate?: string;
  minRs?: number;
  maxLodAtr?: number;
  limit?: number;
}): Promise<ScreenerResponse<MomentumStock>> {
  const response = await apiClient.get('/screeners/momentum-watchlist', { params });
  return response.data;
}

// 8. Breadth Metrics Dashboard
export async function fetchBreadthMetrics(params?: {
  targetDate?: string;
}): Promise<BreadthMetricsResponse> {
  const response = await apiClient.get('/screeners/breadth-metrics', { params });
  return response.data;
}

// 9. Leading Industries/Groups
export async function fetchLeadingIndustries(params?: {
  targetDate?: string;
  topN?: number;
  limit?: number;
}): Promise<ScreenerResponse<LeadingIndustry>> {
  const response = await apiClient.get('/screeners/leading-industries', { params });
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
  const response = await apiClient.get('/screeners/rrg-charts', { params });
  return response.data;
}
