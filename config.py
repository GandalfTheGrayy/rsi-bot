import os


# Default RSI/divergence settings (match Pine PINKRSI defaults)
RSI_PERIOD = int(os.getenv("RSI_PERIOD", 14))
PIVOT_LEFT = int(os.getenv("PIVOT_LEFT", 5))
PIVOT_RIGHT = int(os.getenv("PIVOT_RIGHT", 5))
RANGE_LOWER = int(os.getenv("RANGE_LOWER", 5))
RANGE_UPPER = int(os.getenv("RANGE_UPPER", 60))
CONFIRM_RIGHT = os.getenv("CONFIRM_RIGHT", "false").lower() in {"1", "true", "yes"}

# Timeframes to scan
TIMEFRAMES = [
	"1h",
	"4h",
	"1d",
	"1w",
]

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8410459098:AAG-8PWEkn-xTaZLGuY-kYSHGOJHf5tTw9s")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003102401756")

# Scanning behavior
MAX_SYMBOLS_PER_SOURCE = int(os.getenv("MAX_SYMBOLS_PER_SOURCE", 1000))
REQUEST_TIMEOUT_SECS = float(os.getenv("REQUEST_TIMEOUT_SECS", 10))

# Paths
STATE_DIR = os.getenv("STATE_DIR", "state")
SENT_STATE_PATH = os.path.join(STATE_DIR, "signals_sent.json")

# Input lists (produced earlier from docx)
BIST_LIST_PATH = os.getenv("BIST_LIST_PATH", "BİST.txt")
MIDAS_LIST_PATH = os.getenv("MIDAS_LIST_PATH", "MİDAS COİN YENİ.txt")


