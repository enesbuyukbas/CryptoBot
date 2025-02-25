from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

# MongoDB URI'sini al
MONGODB_URI = os.getenv("MONGODB_URI")

# Binance API Key ve Secret Key ortam değişkenlerinden alınır
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Coin bilgileri
SPOT_URL = os.getenv("SPOT_URL")
INTERVAL = str(os.getenv("INTERVAL"))
LIMIT = int(os.getenv("LIMIT"))
FAST_LENGTH = int(os.getenv("FAST_LENGTH"))
SLOW_LENGTH = int(os.getenv("SLOW_LENGTH"))
SIGNAL_LENGTH = int(os.getenv("SIGNAL_LENGTH"))
ADX_PERIOD = 14
RSI_PERIOD = 14


MACD_THRESHOLDS = {
    'M2': {'long': int(os.getenv('MACD_THRESHOLDS_M2_LONG')), 'short': int(os.getenv('MACD_THRESHOLDS_M2_SHORT'))},
    'M3': {'long': int(os.getenv('MACD_THRESHOLDS_M3_LONG')), 'short': int(os.getenv('MACD_THRESHOLDS_M3_SHORT'))},
    'M4': {'long': int(os.getenv('MACD_THRESHOLDS_M4_LONG')), 'short': int(os.getenv('MACD_THRESHOLDS_M4_SHORT'))},
    'M5': {'long': int(os.getenv('MACD_THRESHOLDS_M5_LONG')), 'short': int(os.getenv('MACD_THRESHOLDS_M5_SHORT'))},
}

# RSI eşik değerleri
RSI_THRESHOLDS = {
    'C20': {'long': 20, 'short': -20},
    'C10': {'long': 10, 'short': -10}
}

# Order Block parametreleri
OB_PERIOD = 12  # Order Block hesaplama periyodu
ATR_PERIOD = 14  # ATR periyodu
MOMENTUM_PERIOD = 10  # Momentum hesaplama periyodu

# MA parametreleri
MA_PERIODS = {
    'MA200': 200,
    'MA50': 50,
    'MA20': 20
}

UPDATE_INTERVAL = 3600  # Güncelleme aralığı (saniye)
RETRY_DELAY = 2  # Hata durumunda bekleme süresi
MAX_RETRIES = 3  # Maksimum yeniden deneme sayısı
TOP_N_SYMBOLS = 200  # İzlenecek sembol sayısı
