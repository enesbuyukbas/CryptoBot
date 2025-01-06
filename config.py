from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

# Binance API Key ve Secret Key ortam değişkenlerinden alınır
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
