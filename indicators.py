from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


def compute_rsi(prices: pd.Series, period: int) -> pd.Series:
	prices = prices.astype(float)
	delta = prices.diff()
	gain = delta.clip(lower=0.0)
	loss = -delta.clip(upper=0.0)
	avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
	avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
	rs = avg_gain / avg_loss.replace(0, np.nan)
	rsi = 100 - (100 / (1 + rs))
	return rsi.bfill().fillna(50.0)


def _find_pivots(series: pd.Series, left: int, right: int) -> Tuple[pd.Series, pd.Series]:
	# Robust pivot detection using numpy to avoid pandas boolean ambiguity
	low_flags = pd.Series(False, index=series.index)
	high_flags = pd.Series(False, index=series.index)
	vals = series.to_numpy(dtype=float, copy=False)
	if left + right >= len(vals):
		return low_flags, high_flags
	for i in range(left, len(vals) - right):
		window_vals = vals[i - left : i + right + 1]
		center = vals[i]
		# center position inside window is exactly at index `left`
		if len(window_vals) > 0:
			if center <= float(np.min(window_vals)) and int(np.argmin(window_vals)) == left:
				low_flags.iloc[i] = True
			if center >= float(np.max(window_vals)) and int(np.argmax(window_vals)) == left:
				high_flags.iloc[i] = True
	return low_flags, high_flags


@dataclass
class DivergenceSignal:
	symbol: str
	timeframe: str
	bar_time: pd.Timestamp
	rsi_at_pivot: float
	price_at_pivot: float
	prev_rsi_pivot: float
	prev_price_pivot: float


def detect_bullish_regular_divergence(
	close: pd.Series,
	high: pd.Series,
	low: pd.Series,
	period: int,
	left: int,
	right: int,
	range_lower: int,
	range_upper: int,
	symbol: str,
	timeframe: str,
) -> List[DivergenceSignal]:
	# Matches Pine logic: Regular Bullish where price forms LL while RSI forms HL within recent range
	rsi = compute_rsi(close, period)
	low_pivots, high_pivots = _find_pivots(rsi, left, right)

	signals: List[DivergenceSignal] = []
	indices = np.where(low_pivots.to_numpy(dtype=bool, copy=False))[0]
	if len(indices) < 2:
		return signals
	
	# Convert to numpy for fast element access without deprecation warnings
	rsi_vals = rsi.to_numpy(dtype=float, copy=False)
	low_vals = low.to_numpy(dtype=float, copy=False)
	close_idx = close.index.to_numpy()

	for j in range(1, len(indices)):
		curr_idx = indices[j]
		prev_idx = indices[j - 1]
		bars_since_prev = curr_idx - prev_idx
		if bars_since_prev < range_lower or bars_since_prev > range_upper:
			continue

		osc_hl = rsi_vals[curr_idx] > rsi_vals[prev_idx]
		price_ll = low_vals[curr_idx] < low_vals[prev_idx]
		if osc_hl and price_ll:
			bar_time = pd.Timestamp(close_idx[curr_idx])
			signals.append(
				DivergenceSignal(
					symbol=symbol,
					timeframe=timeframe,
					bar_time=bar_time,
					rsi_at_pivot=rsi_vals[curr_idx],
					price_at_pivot=low_vals[curr_idx],
					prev_rsi_pivot=rsi_vals[prev_idx],
					prev_price_pivot=low_vals[prev_idx],
				)
			)
	return signals


