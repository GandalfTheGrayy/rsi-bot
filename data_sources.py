from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import requests
import yfinance as yf

from config import REQUEST_TIMEOUT_SECS


def _now_utc() -> datetime:
	return datetime.now(timezone.utc)


def _interval_to_minutes(tf: str) -> int:
	return {
		"1h": 60,
		"4h": 240,
		"1d": 60 * 24,
		"1w": 60 * 24 * 7,
	}[tf]



@lru_cache(maxsize=1)
def _binance_symbol_set() -> set[str]:
	try:
		r = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=REQUEST_TIMEOUT_SECS)
		r.raise_for_status()
		data = r.json()
		return {s.get("symbol", "") for s in data.get("symbols", [])}
	except Exception:
		return set()


def _empty_ohlcv_df() -> pd.DataFrame:
	return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])  # noqa: N815


def fetch_binance_klines(symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
	# symbol like "BTCUSDT" or "BTCTRY"; validate and fallback TRY->USDT if needed
	available = _binance_symbol_set()
	use_symbol = symbol.upper()
	if available and use_symbol not in available:
		alt = use_symbol
		if use_symbol.endswith("TRY"):
			alt = use_symbol[:-3] + "USDT"
		if alt not in available:
			return _empty_ohlcv_df()
		use_symbol = alt

	url = "https://api.binance.com/api/v3/klines"
	params = {"symbol": use_symbol, "interval": timeframe, "limit": limit}
	try:
		r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECS)
		r.raise_for_status()
		arr = r.json()
	except requests.HTTPError:
		return _empty_ohlcv_df()
	df = pd.DataFrame(
		arr,
		columns=[
			"open_time",
			"open",
			"high",
			"low",
			"close",
			"volume",
			"close_time",
			"qav",
			"num_trades",
			"taker_base",
			"taker_quote",
			"ignore",
		],
	)
	df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
	df.set_index("open_time", inplace=True)
	for col in ["open", "high", "low", "close", "volume"]:
		df[col] = df[col].astype(float)
	return df[["open", "high", "low", "close", "volume"]]


def fetch_yahoo(symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
	# BIST symbol like "AKBNK.IS"
	# Yahoo supports: 1m, 5m, 15m, 30m, 60m, 90m, 1h, 4h, 1d, 5d, 1wk, 1mo, 3mo
	# We'll fetch 1h for 4h (and resample in scanner), 1d for others
	if timeframe == "1h":
		intv = "60m"
	elif timeframe == "4h":
		intv = "1h"  # Fetch 1h, resample to 4h in scanner
	elif timeframe == "1d":
		intv = "1d"
	elif timeframe == "1w":
		intv = "1wk"
	else:
		intv = "1d"
	
	try:
		import warnings
		with warnings.catch_warnings():
			warnings.filterwarnings("ignore", category=UserWarning)
			df = yf.download(tickers=symbol, interval=intv, period="730d", auto_adjust=False, progress=False)
	except Exception:
		return _empty_ohlcv_df()
	
	if df is None or len(df) == 0:
		return _empty_ohlcv_df()
	# Normalize columns
	df = df.rename(columns={
		"Open": "open",
		"High": "high",
		"Low": "low",
		"Close": "close",
		"Adj Close": "adj_close",
		"Volume": "volume",
	})
	# Ensure tz-aware UTC index
	df.index = pd.to_datetime(df.index, utc=True)
	return df[["open", "high", "low", "close", "volume"]].tail(limit)


