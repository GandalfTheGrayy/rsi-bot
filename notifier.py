from __future__ import annotations

import json
import os
from typing import Dict

import requests

from config import SENT_STATE_PATH, STATE_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, REQUEST_TIMEOUT_SECS


def _ensure_state():
	if not os.path.isdir(STATE_DIR):
		os.makedirs(STATE_DIR, exist_ok=True)
	if not os.path.exists(SENT_STATE_PATH):
		with open(SENT_STATE_PATH, "w", encoding="utf-8") as f:
			json.dump({}, f)


def _load_sent() -> Dict[str, str]:
	_ensure_state()
	with open(SENT_STATE_PATH, "r", encoding="utf-8") as f:
		try:
			return json.load(f)
		except json.JSONDecodeError:
			return {}


def _save_sent(data: Dict[str, str]) -> None:
	with open(SENT_STATE_PATH, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def _telegram_send(text: str) -> None:
	if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
		return
	url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
	try:
		resp = requests.post(
			url,
			json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True},
			timeout=REQUEST_TIMEOUT_SECS,
		)
		resp.raise_for_status()
	except requests.exceptions.RequestException as e:
		print(f"[Telegram] Error sending message: {e}")
		# Don't crash, just log


def notify_if_new(key: str, message: str, send_message: bool = True) -> bool:
	"""Return True if sent, False if duplicate."""
	sent = _load_sent()
	if sent.get(key) == message:
		return False
	if send_message:
		_telegram_send(message)
	sent[key] = message
	_save_sent(sent)
	return True


