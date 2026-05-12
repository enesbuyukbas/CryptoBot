import os
import logging
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# ================== MONGODB AYARLARI ==================
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI ortam değişkeni tanımlanmamış!")

# ================== BINANCE API AYARLARI ==================
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
SPOT_URL = os.getenv("SPOT_URL", "https://api.binance.com")

# ================== TIMEFRAME VE SEMBOL AYARLARI ==================
TIMEFRAMES = ["15m", "1h", "4h", "1d"]
MIN_QUOTE_VOLUME = 500_000  # Minimum 24h USDT hacmi — bu altındaki coinler likit değil
CANDLE_LIMIT = 200      # Çekilecek mum sayısı

# ================== TEKNİK ANALİZ PARAMETRELERİ ==================
# EMA Periyotları
EMA_PERIODS = {
    'EMA20': 20,
    'EMA50': 50,
    'EMA200': 200
}

# RSI Parametreleri
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ATR Parametreleri
ATR_PERIOD = 14

# ADX Parametreleri
ADX_PERIOD = 14
ADX_STRONG_TREND = 25

# MACD Parametreleri
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ROC Parametreleri
ROC_PERIOD = 10

# ================== SİNYAL AYARLARI ==================
# Sinyal gücü threshold'ları
SIGNAL_STRENGTH_STRONG = 80
SIGNAL_STRENGTH_MODERATE = 50

# MongoDB'de sinyal saklama süresi (saniye)
SIGNAL_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 gün

# expires_at tabanlı retention — açık sinyaller
OPEN_SIGNAL_RETENTION_SECONDS = {
    "15m": 3  * 24 * 3600,   # 3 gün
    "1h":  7  * 24 * 3600,   # 7 gün
    "4h":  15 * 24 * 3600,   # 15 gün
    "1d":  30 * 24 * 3600,   # 30 gün
}

# expires_at tabanlı retention — kapanmış sinyaller (TP/SL)
CLOSED_SIGNAL_RETENTION_SECONDS = {
    "15m": 3  * 24 * 3600,   # 3 gün
    "1h":  7  * 24 * 3600,   # 7 gün
    "4h":  15 * 24 * 3600,   # 15 gün
    "1d":  30 * 24 * 3600,   # 30 gün
}

# Aynı yönde sinyal maksimum güncelleme süresi (saniye)
# Bu süreyi geçen sinyal "yeni" sayılır, mevcut belge üzerine yazılmaz
SIGNAL_MAX_AGE_SECONDS = {
    "15m": 4 * 3600,       # 4 saat
    "1h":  24 * 3600,      # 1 gün
    "4h":  4 * 24 * 3600,  # 4 gün
    "1d":  14 * 24 * 3600, # 14 gün
}

# ================== PARALEL İŞLEME AYARLARI ==================
MAX_WORKERS = 5  # ThreadPoolExecutor için maksimum worker sayısı

# ================== LOGGING AYARLARI ==================
# Lambda/CloudWatch: FileHandler yok (filesystem ephemeral), timestamp yok (CloudWatch ekler)
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

# ================== API İSTEK AYARLARI ==================
REQUEST_TIMEOUT = 10  # Saniye
MAX_RETRIES = 3
RETRY_DELAY = 2  # Saniye