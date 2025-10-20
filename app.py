from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import TIMEFRAMES, CONFIRM_RIGHT
from notifier import notify_if_new
from scanner import scan_symbol_timeframe
from symbols import build_unified_symbol_map


st.set_page_config(page_title="RSI Bullish Divergence Scanner", layout="wide")


@st.cache_data(ttl=300)
def load_symbols():
	return build_unified_symbol_map()


def format_signal(sig) -> str:
	import math
	import numpy as np
	# Convert numpy scalars to Python floats safely
	def to_float(val):
		if isinstance(val, np.ndarray):
			val = val.item()
		return float(val)
	
	prev_rsi = to_float(sig.prev_rsi_pivot)
	curr_rsi = to_float(sig.rsi_at_pivot)
	prev_price = to_float(sig.prev_price_pivot)
	curr_price = to_float(sig.price_at_pivot)
	
	# Format with NaN checks
	prev_rsi_str = f"{prev_rsi:.2f}" if not math.isnan(prev_rsi) else "N/A"
	curr_rsi_str = f"{curr_rsi:.2f}" if not math.isnan(curr_rsi) else "N/A"
	prev_price_str = f"{prev_price:.4f}" if not math.isnan(prev_price) else "N/A"
	curr_price_str = f"{curr_price:.4f}" if not math.isnan(curr_price) else "N/A"
	
	return (
		f"{sig.symbol} | {sig.timeframe} | {sig.bar_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
		f"RSI: {prev_rsi_str} -> {curr_rsi_str} (HL)\n"
		f"Low: {prev_price_str} -> {curr_price_str} (LL)"
	)


def main():
	st.title("RSI Pozitif Uyumsuzluk Tarayıcı")
	st.caption("1h / 4h / 1d / 1w kapanışında boğa uyumsuzluğu (Pine ayarları ile).")

	symbol_map = load_symbols()  # display -> (source, code)
	all_display = sorted(symbol_map.keys())

	with st.sidebar:
		st.subheader("Semboller")
		selected = st.multiselect("Taranacak semboller", options=all_display, default=all_display)
		auto_refresh = st.checkbox("Otomatik yenile (60 sn)", value=True)
		send_telegram = st.checkbox("Telegram'a gönder", value=False)
		confirm = st.checkbox(
			"lbR teyitli (gecikmeli) sinyal",
			value=CONFIRM_RIGHT,
			help="Açık ise Pine'daki offset=-lbR teyidi beklenir (daha geç ama daha kesin). Kapalı ise kapanışta anlık bildirim.",
		)

	if auto_refresh:
		st_autorefresh(interval=60_000, key="auto-refresh-60s")

	results: List[Tuple[str, str, object]] = []
	cols = st.columns(len(TIMEFRAMES))
	for idx, tf in enumerate(TIMEFRAMES):
		with cols[idx]:
			st.subheader(tf)
			hits: List[str] = []
			for disp in selected:
				source, code = symbol_map[disp]
				signals = scan_symbol_timeframe(code, source, tf, confirm=confirm)
				for sig in signals[-1:]:  # show latest
					text = format_signal(sig)
					hits.append(text)
					if send_telegram:
						key = f"{sig.symbol}:{sig.timeframe}:{sig.bar_time.isoformat()}"
						notify_if_new(key, f"*RSI Bullish Divergence*\n{text}")
			if hits:
				st.code("\n\n".join(hits))
			else:
				st.write("Sinyal yok")

	st.caption("Veriler Binance ve Yahoo Finance kaynaklıdır. Gecikmeler olabilir.")


if __name__ == "__main__":
	main()


