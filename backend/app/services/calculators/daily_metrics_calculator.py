"""
Daily Metrics Calculator Service.

Calculates all 47 technical indicators and metrics for the calculated_metrics table.
Uses pandas for efficient vectorized calculations across all securities.

Metrics Categories:
1. Price Changes (6 metrics)
2. Relative Strength (3 metrics)
3. Volatility (4 metrics)
4. Volume (3 metrics)
5. Moving Averages (11 metrics)
6. ATR Extension (3 metrics)
7. Darvas Box (3 metrics)
8. New Highs/Lows (2 metrics)
9. ORH/M30 (2 metrics)
10. VCP Score (1 metric)
11. Stage Classification (2 metrics)
12. Breadth Metrics (4 metrics)
13. RRG Metrics (2 metrics)
14. Candle Type (1 metric)

Total: 47 metrics
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.timeseries import OHLCVDaily, CalculatedMetrics
from app.models.security import Security


class DailyMetricsCalculator:
    """
    Calculate daily technical metrics for all securities.

    Usage:
        calculator = DailyMetricsCalculator(db_session)
        result = calculator.calculate_metrics_for_date(target_date)
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_metrics_for_date(
        self,
        target_date: date,
        symbols: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate all metrics for a specific date.

        Args:
            target_date: Date to calculate metrics for
            symbols: Optional list of symbols (if None, calculates for all active securities)

        Returns:
            Dict with success status, records_inserted, and errors
        """
        result = {
            "success": False,
            "target_date": str(target_date),
            "records_inserted": 0,
            "records_updated": 0,
            "errors": []
        }

        try:
            # Get list of symbols to process
            if symbols is None:
                symbols_query = self.db.query(Security.symbol).filter(Security.is_active == True)
                symbols = [row.symbol for row in symbols_query.all()]

            if not symbols:
                result["errors"].append("No active securities found")
                return result

            # For each symbol, we need historical OHLCV data
            # Lookback: 200 days for SMA200, plus buffer
            lookback_days = 250
            start_date = target_date - timedelta(days=lookback_days * 1.5)  # 1.5x buffer for weekends

            # Fetch OHLCV data for all symbols
            ohlcv_data = self._fetch_ohlcv_data(symbols, start_date, target_date)

            if ohlcv_data.empty:
                result["errors"].append(f"No OHLCV data found for {target_date}")
                return result

            # Calculate metrics for each symbol
            all_metrics = []
            universe_metrics = self._calculate_universe_metrics(ohlcv_data, target_date)

            for symbol in symbols:
                symbol_data = ohlcv_data[ohlcv_data['symbol'] == symbol].copy()

                if symbol_data.empty or target_date not in symbol_data['date'].values:
                    result["errors"].append(f"{symbol}: No data for {target_date}")
                    continue

                # Calculate metrics for this symbol
                metrics = self._calculate_symbol_metrics(
                    symbol,
                    symbol_data,
                    target_date,
                    universe_metrics
                )

                if metrics:
                    all_metrics.append(metrics)

            # Calculate RS percentiles across universe (requires all symbols' 1M changes)
            if all_metrics:
                all_metrics = self._calculate_rs_percentiles(all_metrics)

            # Bulk insert/update to database
            if all_metrics:
                inserted, updated = self._save_metrics_to_db(all_metrics, target_date)
                result["records_inserted"] = inserted
                result["records_updated"] = updated
                result["success"] = True

        except Exception as e:
            result["errors"].append(f"Calculation failed: {str(e)}")

        return result

    def _fetch_ohlcv_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch OHLCV data for symbols in date range."""
        query = self.db.query(
            OHLCVDaily.symbol,
            OHLCVDaily.date,
            OHLCVDaily.open,
            OHLCVDaily.high,
            OHLCVDaily.low,
            OHLCVDaily.close,
            OHLCVDaily.volume
        ).filter(
            OHLCVDaily.symbol.in_(symbols),
            OHLCVDaily.date >= start_date,
            OHLCVDaily.date <= end_date
        ).order_by(
            OHLCVDaily.symbol,
            OHLCVDaily.date
        )

        df = pd.read_sql(query.statement, self.db.bind)
        return df

    def _calculate_universe_metrics(self, ohlcv_data: pd.DataFrame, target_date: date) -> Dict:
        """Calculate universe-wide metrics (breadth, McClellan)."""
        target_data = ohlcv_data[ohlcv_data['date'] == target_date]

        if target_data.empty:
            return {
                "universe_up_count": 0,
                "universe_down_count": 0,
                "mcclellan_oscillator": 0,
                "mcclellan_summation": 0
            }

        # Breadth: Count up/down stocks
        universe_up = (target_data['close'] >= target_data['open']).sum()
        universe_down = (target_data['close'] < target_data['open']).sum()

        # McClellan Oscillator: (advances - declines)
        # Simplified: Use 19-day and 39-day EMA of (up_count - down_count)
        # TODO: Implement proper McClellan calculation with historical data
        advances_minus_declines = universe_up - universe_down

        return {
            "universe_up_count": int(universe_up),
            "universe_down_count": int(universe_down),
            "mcclellan_oscillator": float(advances_minus_declines),  # Simplified
            "mcclellan_summation": 0  # TODO: Cumulative sum of oscillator
        }

    def _calculate_symbol_metrics(
        self,
        symbol: str,
        symbol_data: pd.DataFrame,
        target_date: date,
        universe_metrics: Dict
    ) -> Optional[Dict]:
        """Calculate all 47 metrics for a single symbol."""
        # Sort by date
        df = symbol_data.sort_values('date').reset_index(drop=True)

        # Get target row index
        target_idx = df[df['date'] == target_date].index
        if len(target_idx) == 0:
            return None
        target_idx = target_idx[0]

        # Need at least 200 days for SMA200
        if target_idx < 200:
            return None

        metrics = {
            "symbol": symbol,
            "date": target_date
        }

        # Current values
        current = df.loc[target_idx]
        close = current['close']
        high = current['high']
        low = current['low']
        open_price = current['open']
        volume = current['volume']

        # ===== 1. PRICE CHANGES =====
        metrics.update(self._calc_price_changes(df, target_idx))

        # ===== 2. VOLATILITY METRICS =====
        metrics.update(self._calc_volatility(df, target_idx))

        # ===== 3. VOLUME METRICS =====
        metrics.update(self._calc_volume_metrics(df, target_idx))

        # ===== 4. MOVING AVERAGES =====
        metrics.update(self._calc_moving_averages(df, target_idx))

        # ===== 5. ATR EXTENSION =====
        metrics.update(self._calc_atr_extension(df, target_idx, metrics))

        # ===== 6. DARVAS BOX =====
        metrics.update(self._calc_darvas(df, target_idx))

        # ===== 7. NEW HIGHS/LOWS =====
        metrics.update(self._calc_new_highs_lows(df, target_idx))

        # ===== 8. ORH/M30 (Proxy) =====
        metrics['orh_proxy'] = float(high)
        metrics['is_m30_reclaim'] = 1 if close > high * 0.99 else 0  # Proxy

        # ===== 9. VCP SCORE =====
        metrics['vcp_score'] = self._calc_vcp_score(df, target_idx)

        # ===== 10. STAGE CLASSIFICATION =====
        metrics.update(self._calc_stage(df, target_idx, metrics))

        # ===== 11. BREADTH METRICS (Universe-wide) =====
        metrics.update(universe_metrics)

        # ===== 12. RRG METRICS (Placeholder - requires benchmark) =====
        # TODO: Calculate RS-Ratio and RS-Momentum vs. benchmark index
        metrics['rs_ratio'] = 100.0  # Placeholder
        metrics['rs_momentum'] = 0.0  # Placeholder

        # ===== 13. CANDLE TYPE =====
        metrics['is_green_candle'] = 1 if close >= open_price else 0

        # ===== 14. RELATIVE STRENGTH (Universe-wide percentile) =====
        # This requires all symbols' 1M changes - calculate after gathering all symbols
        # For now, set placeholder (will update in batch after calculating all symbols)
        metrics['rs_percentile'] = 50.0  # Placeholder
        metrics['vars_score'] = 0.0  # Placeholder
        metrics['varw_score'] = 0.0  # Placeholder

        return metrics

    def _calc_price_changes(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate 1D, 1W, 1M, 3M, 6M % changes."""
        close = df.loc[idx, 'close']

        changes = {}
        periods = {
            '1d': 1,
            '1w': 5,
            '1m': 21,
            '3m': 63,
            '6m': 126
        }

        for period_name, days in periods.items():
            prev_idx = idx - days
            if prev_idx >= 0:
                prev_close = df.loc[prev_idx, 'close']
                pct_change = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
                changes[f'change_{period_name}_percent'] = float(pct_change)
            else:
                changes[f'change_{period_name}_percent'] = None

        # 1D absolute change
        if idx > 0:
            changes['change_1d_value'] = float(close - df.loc[idx - 1, 'close'])
        else:
            changes['change_1d_value'] = None

        return changes

    def _calc_volatility(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate ATR, ATR%, ADR%."""
        # ATR (14-day)
        atr_14 = self._calc_atr(df, idx, period=14)
        close = df.loc[idx, 'close']

        atr_percent = (atr_14 / close * 100) if close > 0 and atr_14 else 0

        # ADR% (20-day average daily range %)
        adr_pct = self._calc_adr(df, idx, period=20)

        # Today's range %
        high = df.loc[idx, 'high']
        low = df.loc[idx, 'low']
        today_range = ((high - low) / close * 100) if close > 0 else 0

        return {
            'atr_14': float(atr_14) if atr_14 else None,
            'atr_percent': float(atr_percent),
            'adr_percent': float(adr_pct),
            'today_range_percent': float(today_range)
        }

    def _calc_atr(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate Average True Range (Wilder's method)."""
        if idx < period:
            return 0

        true_ranges = []
        for i in range(idx - period + 1, idx + 1):
            high = df.loc[i, 'high']
            low = df.loc[i, 'low']
            prev_close = df.loc[i - 1, 'close'] if i > 0 else df.loc[i, 'open']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        return np.mean(true_ranges)

    def _calc_adr(self, df: pd.DataFrame, idx: int, period: int = 20) -> float:
        """Calculate Average Daily Range % over period."""
        if idx < period:
            return 0

        ranges = []
        for i in range(idx - period + 1, idx + 1):
            high = df.loc[i, 'high']
            low = df.loc[i, 'low']
            close = df.loc[i, 'close']

            range_pct = ((high - low) / close * 100) if close > 0 else 0
            ranges.append(range_pct)

        return float(np.mean(ranges))

    def _calc_volume_metrics(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate RVOL and volume surge flag."""
        if idx < 50:
            return {
                'volume_50d_avg': None,
                'rvol': None,
                'is_volume_surge': 0
            }

        volume_50d_avg = df.loc[idx - 50:idx - 1, 'volume'].mean()
        current_volume = df.loc[idx, 'volume']

        rvol = (current_volume / volume_50d_avg) if volume_50d_avg > 0 else 0
        is_volume_surge = 1 if rvol >= 1.5 else 0

        return {
            'volume_50d_avg': int(volume_50d_avg),
            'rvol': float(rvol),
            'is_volume_surge': is_volume_surge
        }

    def _calc_moving_averages(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate EMA10, SMA20/50/100/200 and distances."""
        close = df.loc[idx, 'close']

        # EMAs and SMAs
        ema_10 = df.loc[max(0, idx - 10):idx, 'close'].ewm(span=10, adjust=False).mean().iloc[-1] if idx >= 10 else None
        sma_20 = df.loc[max(0, idx - 20):idx, 'close'].mean() if idx >= 20 else None
        sma_50 = df.loc[max(0, idx - 50):idx, 'close'].mean() if idx >= 50 else None
        sma_100 = df.loc[max(0, idx - 100):idx, 'close'].mean() if idx >= 100 else None
        sma_200 = df.loc[max(0, idx - 200):idx, 'close'].mean() if idx >= 200 else None

        # Distances from MAs
        dist_ema10 = ((close - ema_10) / ema_10 * 100) if ema_10 else None
        dist_sma50 = ((close - sma_50) / sma_50 * 100) if sma_50 else None
        dist_sma200 = ((close - sma_200) / sma_200 * 100) if sma_200 else None

        # MA Stacked check
        is_stacked = 0
        if all([ema_10, sma_20, sma_50, sma_100, sma_200]):
            is_stacked = 1 if (close > ema_10 > sma_20 > sma_50 > sma_100 > sma_200) else 0

        return {
            'ema_10': float(ema_10) if ema_10 else None,
            'sma_20': float(sma_20) if sma_20 else None,
            'sma_50': float(sma_50) if sma_50 else None,
            'sma_100': float(sma_100) if sma_100 else None,
            'sma_200': float(sma_200) if sma_200 else None,
            'distance_from_ema10_percent': float(dist_ema10) if dist_ema10 else None,
            'distance_from_sma50_percent': float(dist_sma50) if dist_sma50 else None,
            'distance_from_sma200_percent': float(dist_sma200) if dist_sma200 else None,
            'is_ma_stacked': is_stacked
        }

    def _calc_atr_extension(self, df: pd.DataFrame, idx: int, metrics: Dict) -> Dict:
        """Calculate ATR extension from SMA50 and LoD ATR%."""
        close = df.loc[idx, 'close']
        low = df.loc[idx, 'low']
        sma_50 = metrics.get('sma_50')
        atr_14 = metrics.get('atr_14')

        # ATR Extension from SMA50
        atr_ext = None
        if sma_50 and atr_14 and close > 0:
            atr_ext = ((close / sma_50) - 1) / (atr_14 / close) if atr_14 > 0 else 0

        # LoD ATR%
        lod_atr_pct = None
        is_lod_tight = 0
        if atr_14:
            lod_atr_pct = ((low - close) / atr_14 * 100) if atr_14 > 0 else 0
            is_lod_tight = 1 if abs(lod_atr_pct) < 60 else 0

        return {
            'atr_extension_from_sma50': float(atr_ext) if atr_ext else None,
            'lod_atr_percent': float(lod_atr_pct) if lod_atr_pct else None,
            'is_lod_tight': is_lod_tight
        }

    def _calc_darvas(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate 20-day Darvas box."""
        if idx < 20:
            return {
                'darvas_20d_high': None,
                'darvas_20d_low': None,
                'darvas_position_percent': None
            }

        darvas_high = df.loc[idx - 20:idx, 'high'].max()
        darvas_low = df.loc[idx - 20:idx, 'low'].min()
        close = df.loc[idx, 'close']

        # Position within range
        range_span = darvas_high - darvas_low
        position = ((close - darvas_low) / range_span * 100) if range_span > 0 else 50

        return {
            'darvas_20d_high': float(darvas_high),
            'darvas_20d_low': float(darvas_low),
            'darvas_position_percent': float(position)
        }

    def _calc_new_highs_lows(self, df: pd.DataFrame, idx: int) -> Dict:
        """Check if current high/low is 20-day extreme."""
        if idx < 20:
            return {
                'is_new_20d_high': 0,
                'is_new_20d_low': 0
            }

        high_20d = df.loc[idx - 20:idx - 1, 'high'].max()
        low_20d = df.loc[idx - 20:idx - 1, 'low'].min()

        current_high = df.loc[idx, 'high']
        current_low = df.loc[idx, 'low']

        return {
            'is_new_20d_high': 1 if current_high >= high_20d else 0,
            'is_new_20d_low': 1 if current_low <= low_20d else 0
        }

    def _calc_vcp_score(self, df: pd.DataFrame, idx: int) -> int:
        """Calculate VCP score (1-5) based on narrowing range."""
        if idx < 5:
            return 0

        # Check last 5 bars for narrowing range
        ranges = []
        for i in range(idx - 4, idx + 1):
            high = df.loc[i, 'high']
            low = df.loc[i, 'low']
            ranges.append(high - low)

        # Count how many consecutive bars have narrowing ranges
        narrowing_count = 0
        for i in range(1, len(ranges)):
            if ranges[i] < ranges[i - 1]:
                narrowing_count += 1

        # VCP score: 1-5 (more narrowing = higher score)
        return min(narrowing_count, 5)

    def _calc_stage(self, df: pd.DataFrame, idx: int, metrics: Dict) -> Dict:
        """Calculate Weinstein Stage Classification."""
        close = df.loc[idx, 'close']
        sma_50 = metrics.get('sma_50')
        sma_200 = metrics.get('sma_200')
        darvas_position = metrics.get('darvas_position_percent')
        atr_ext = metrics.get('atr_extension_from_sma50')

        # Default: Stage 1 (basing)
        stage = 1
        stage_detail = "1"

        if sma_50 and sma_200:
            if close > sma_50 and close > sma_200:
                # Stage 2 variants (uptrend)
                if darvas_position and darvas_position >= 90:
                    stage = 2
                    stage_detail = "2B"  # At top of range
                elif atr_ext and atr_ext >= 7:
                    stage = 2
                    stage_detail = "2C"  # Extended
                else:
                    stage = 2
                    stage_detail = "2A"  # Early uptrend
            elif close < sma_50 and close < sma_200:
                stage = 4  # Decline
                stage_detail = "4"
            else:
                stage = 3  # Topping/distribution
                stage_detail = "3"

        return {
            'stage': stage,
            'stage_detail': stage_detail
        }

    def _calculate_rs_percentiles(self, all_metrics: List[Dict]) -> List[Dict]:
        """
        Calculate RS percentile and VARS/VARW for all symbols.

        This must be done after individual metrics are calculated,
        since it requires ranking across the entire universe.
        """
        # Extract 1M changes for all symbols
        changes_1m = []
        for metrics in all_metrics:
            change = metrics.get('change_1m_percent')
            if change is not None:
                changes_1m.append((metrics['symbol'], float(change)))

        if not changes_1m:
            return all_metrics

        # Sort by 1M change
        changes_1m.sort(key=lambda x: x[1])

        # Calculate percentile rank for each symbol
        total = len(changes_1m)
        percentile_map = {}
        for rank, (symbol, change) in enumerate(changes_1m):
            percentile = (rank / (total - 1)) * 100 if total > 1 else 50.0
            percentile_map[symbol] = percentile

        # Update metrics with RS percentile and calculate VARS/VARW
        for metrics in all_metrics:
            symbol = metrics['symbol']
            if symbol in percentile_map:
                rs_percentile = percentile_map[symbol]
                adr_percent = metrics.get('adr_percent')

                metrics['rs_percentile'] = round(rs_percentile, 2)

                # VARS = RS Percentile / ADR% (higher is better - strong + low volatility)
                if adr_percent and adr_percent > 0:
                    vars_score = rs_percentile / adr_percent
                    metrics['vars_score'] = round(vars_score, 4)

                    # VARW = (100 - RS Percentile) / ADR% (for finding laggards)
                    varw_score = (100 - rs_percentile) / adr_percent
                    metrics['varw_score'] = round(varw_score, 4)
                else:
                    metrics['vars_score'] = 0.0
                    metrics['varw_score'] = 0.0

        return all_metrics

    def _save_metrics_to_db(self, metrics_list: List[Dict], target_date: date) -> tuple:
        """Save calculated metrics to database (UPSERT)."""
        inserted = 0
        updated = 0

        for metrics in metrics_list:
            # Check if record exists
            existing = self.db.query(CalculatedMetrics).filter(
                CalculatedMetrics.symbol == metrics['symbol'],
                CalculatedMetrics.date == target_date
            ).first()

            if existing:
                # Update existing record
                for key, value in metrics.items():
                    if key not in ['symbol', 'date']:
                        setattr(existing, key, value)
                updated += 1
            else:
                # Insert new record
                new_record = CalculatedMetrics(**metrics)
                self.db.add(new_record)
                inserted += 1

        self.db.commit()
        return inserted, updated
