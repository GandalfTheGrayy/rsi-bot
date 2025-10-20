from __future__ import annotations

import re
from typing import Dict, List, Tuple

from config import BIST_LIST_PATH, MIDAS_LIST_PATH, MAX_SYMBOLS_PER_SOURCE


def load_bist_from_text(path: str = BIST_LIST_PATH) -> List[str]:
	# Parse tokens like AKBNK, THYAO into Yahoo symbols: AKBNK.IS
	with open(path, "r", encoding="utf-8") as f:
		content = f.read()
	# Filter tokens of letters/digits with length 3-6
	tokens = re.findall(r"[A-ZÇĞİÖŞÜ0-9]{3,6}", content)
	# Exclude non-tickers commonly found in the list
	excludes = {"ALTIN", "XU100", "XU500"}
	uniq = []
	seen = set()
	for t in tokens:
		if t in excludes:
			continue
		if t not in seen:
			seen.add(t)
			uniq.append(t)
	# Convert to Yahoo Finance tickers
	yahoo = [f"{t}.IS" for t in uniq][:MAX_SYMBOLS_PER_SOURCE]
	return yahoo


def load_binance_from_text(path: str = MIDAS_LIST_PATH) -> List[str]:
	# Parse tokens like BTCTRY, ETHTRY etc. Use TRY pairs directly on Binance if available.
	with open(path, "r", encoding="utf-8") as f:
		content = f.read()
	all_tokens = re.findall(r"[A-Z0-9]{3,12}", content)
	try_tokens = [t for t in all_tokens if t.endswith("TRY")]
	uniq: List[str] = []
	seen = set()
	for t in try_tokens:
		if t not in seen:
			seen.add(t)
			uniq.append(t)
	# Prefer well-known majors first to reduce 400 errors
	priority = [
		"BTCTRY","ETHTRY","BNBTRY","SOLTRY","ADATRY","XRPTRY","AVAXTRY","DOTTRY","LINKTRY","LTCTRY",
	]
	ordered = [t for t in priority if t in uniq]
	for t in uniq:
		if t not in ordered:
			ordered.append(t)
	return ordered[:MAX_SYMBOLS_PER_SOURCE]


def build_unified_symbol_map() -> Dict[str, Tuple[str, str]]:
	"""
	Return dict: key = display symbol, value = (source, code)
	- source in {"yahoo", "binance"}
	- code is provider-specific symbol
	"""
	bist = load_bist_from_text()
	binance = load_binance_from_text()

	result: Dict[str, Tuple[str, str]] = {}
	for s in bist:
		result[s] = ("yahoo", s)
	for p in binance:
		result[p] = ("binance", p)
	return result


