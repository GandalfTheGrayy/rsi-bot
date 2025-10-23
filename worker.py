from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from config import TIMEFRAMES, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from notifier import notify_if_new
from scanner import scan_symbol_timeframe
from symbols import build_unified_symbol_map


SCAN_INTERVAL_SECS = int(os.getenv("SCAN_INTERVAL_SECS", 60))


def main():
    symbol_map = build_unified_symbol_map()  # display -> (source, code)
    all_display = sorted(symbol_map.keys())

    print(f"Loaded {len(all_display)} symbols. Starting worker...")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] Telegram creds not configured; messages will not be sent.")

    first_run = True
    while True:
        start = time.time()
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"\n[SCAN] {utc_now}")
        for tf in TIMEFRAMES:
            sent_count = 0
            for disp in all_display:
                source, code = symbol_map[disp]
                try:
                    signals = scan_symbol_timeframe(code, source, tf, confirm=False)
                except Exception as e:
                    print(f"[ERR] {disp} {tf}: {e}")
                    continue
                if not signals:
                    continue
                sig = signals[-1]
                text = (
                    f"*RSI Bullish Divergence*\n"
                    f"{sig.symbol} | {sig.timeframe} | {sig.bar_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    f"RSI: {sig.prev_rsi_pivot:.2f} -> {sig.rsi_at_pivot:.2f} (HL)\n"
                    f"Low: {sig.prev_price_pivot:.4f} -> {sig.price_at_pivot:.4f} (LL)"
                )
                key = f"{sig.symbol}:{sig.timeframe}:{sig.bar_time.isoformat()}"
                # İlk çalıştırmada sadece state'i doldur, mesaj gönderme
                send_telegram = not first_run
                if notify_if_new(key, text, send_message=send_telegram):
                    sent_count += 1
            print(f"[TF {tf}] sent={sent_count}")
        
        if first_run:
            print("[INFO] İlk tarama tamamlandı. State kaydedildi. Sonraki taramada SADECE YENİ sinyaller gönderilecek.")
            first_run = False
        
        elapsed = time.time() - start
        sleep_left = max(1, SCAN_INTERVAL_SECS - int(elapsed))
        time.sleep(sleep_left)


if __name__ == "__main__":
    main()


