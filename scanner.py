from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from config import (
	PIVOT_LEFT,
	PIVOT_RIGHT,
	RANGE_LOWER,
	RANGE_UPPER,
	RSI_PERIOD,
	TIMEFRAMES,
    CONFIRM_RIGHT,
)
from data_sources import fetch_binance_klines, fetch_yahoo
from indicators import detect_bullish_regular_divergence


def _empty_df() -> pd.DataFrame:
	return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])  # noqa: N815


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
	if df is None or len(df) == 0:
		return _empty_df()
	# Flatten MultiIndex columns if present
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = ["_".join([str(p) for p in col if p is not None]) for col in df.columns.to_list()]
	# Standardize known names
	rename_map = {
		"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume",
		"open": "open", "high": "high", "low": "low", "close": "close", "adj close": "adj_close", "volume": "volume",
	}
	std_cols = {c: rename_map.get(c, c) for c in df.columns}
	df = df.rename(columns=std_cols)
	# Lowercase all
	df.columns = [c.lower() if isinstance(c, str) else str(c).lower() for c in df.columns]
	# Keep only needed
	required = ["open", "high", "low", "close", "volume"]
	if not all(col in df.columns for col in required):
		return _empty_df()
	return df[required]


def _fetch(symbol: str, source: str, timeframe: str) -> pd.DataFrame:
	if source == "binance":
		# Map timeframe to Binance intervals
		binance_tf = {"1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}[timeframe]
		return fetch_binance_klines(symbol, binance_tf)
	elif source == "yahoo":
		df = fetch_yahoo(symbol, timeframe)
		df = _normalize_ohlcv(df)
		# Resample 1h to 4h if needed
		if timeframe == "4h" and len(df) > 0:
			try:
				df = df.resample("4h").agg({
					"open": "first",
					"high": "max",
					"low": "min",
					"close": "last",
					"volume": "sum",
				}).dropna()
			except Exception as e:
				print(f"Resample error for {symbol}: {e}")
		return df
	else:
		raise ValueError(f"Unknown source {source}")


def scan_symbol_timeframe(symbol: str, source: str, timeframe: str, confirm: bool | None = None):
	df = _fetch(symbol, source, timeframe)
	# Ensure required columns
	if df is None or len(df) == 0 or not all(c in df.columns for c in ["open", "high", "low", "close", "volume"]):
		return []
	# Closed-candle policy:
	# - If confirming right pivots (like Pine offset=-lbR), we must wait for lbR bars -> drop last lbR bars
	# - If instant alerts requested, use only last closed bar -> drop last 1 bar while scanning pivots across history
	use_confirm = CONFIRM_RIGHT if confirm is None else confirm
	if use_confirm:
		if len(df) > PIVOT_RIGHT:
			df = df.iloc[: -PIVOT_RIGHT]
	else:
		if len(df) > 1:
			df = df.iloc[:-1]
	if len(df) == 0:
		return []
	return detect_bullish_regular_divergence(
		close=df["close"],
		high=df["high"],
		low=df["low"],
		period=RSI_PERIOD,
		left=PIVOT_LEFT,
		right=(PIVOT_RIGHT if (use_confirm) else 0),
		range_lower=RANGE_LOWER,
		range_upper=RANGE_UPPER,
		symbol=symbol,
		timeframe=timeframe,
	)


