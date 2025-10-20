## RSI Bullish Divergence Streamlit + Telegram

Scan symbols for bullish regular divergences on RSI using Pine-like settings (RSI=14, lbL=5, lbR=5, range 5-60 bars). Timeframes: 1h, 4h, 1d, 1w.

### Setup
1. Python 3.10+
2. Install deps:
```
pip install -r requirements.txt
```
3. Prepare input lists from existing text files:
   - `BİST.txt` (parsed into Yahoo tickers like `AKBNK.IS`)
   - `MİDAS COİN YENİ.txt` (maps common TRY pairs to Binance USDT pairs)

Optional: set environment variables (defaults in `config.py`):
```
set TELEGRAM_BOT_TOKEN=... 
set TELEGRAM_CHAT_ID=...
```

### Run
```
streamlit run app.py
```

### Notes
- Yahoo intervals are used for BIST; Binance klines for crypto.
- Signals are deduplicated per symbol/timeframe/bar before sending to Telegram.
- This implementation mirrors the core of the provided Pine logic for "Regular Bullish" divergence: price LL with RSI HL between consecutive RSI pivot lows within the 5-60 bars window.


