import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from typing import List, Optional

from config import (
    SPOT_URL,
    TOP_SYMBOL_LIMIT,
    CANDLE_LIMIT,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)


def get_spot_symbols(limit: int = TOP_SYMBOL_LIMIT) -> List[str]:
    """
    Binance SPOT piyasasından en yüksek hacimli USDT paritelerini getirir.
    
    Args:
        limit: Getirilecek maksimum sembol sayısı
        
    Returns:
        USDT paritesi olan sembol listesi (hacme göre sıralı)
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Exchange bilgilerini çek
            response = requests.get(
                f"{SPOT_URL}/api/v3/exchangeInfo",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # USDT paritelerini ve TRADING durumunda olanları filtrele
            symbols = [
                symbol['symbol'] 
                for symbol in data['symbols']
                if symbol['symbol'].endswith('USDT') 
                and symbol['status'] == 'TRADING'
            ]

            logger.info(f"✅ {len(symbols)} USDT paritesi bulundu")

            # 24 saatlik hacimleri çek
            volumes = {}
            for i, symbol in enumerate(symbols):
                try:
                    response = requests.get(
                        f"{SPOT_URL}/api/v3/ticker/24hr",
                        params={"symbol": symbol},
                        timeout=REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    volume_data = response.json()
                    volumes[symbol] = float(volume_data["quoteVolume"])
                    
                    # Rate limiting için kısa bekleme
                    if i % 50 == 0 and i > 0:
                        time.sleep(0.5)
                    else:
                        time.sleep(0.05)
                        
                except Exception as e:
                    logger.warning(f"⚠️ {symbol} hacim verisi alınamadı: {e}")
                    volumes[symbol] = 0
                    continue

            # Hacme göre sırala ve ilk N tanesini al
            sorted_symbols = sorted(
                volumes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            result = [symbol for symbol, _ in sorted_symbols]
            logger.info(f"✅ Top {len(result)} yüksek hacimli sembol seçildi")
            
            return result

        except Exception as e:
            logger.error(f"❌ Sembol listesi hatası (deneme {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ Sembol listesi alınamadı, boş liste döndürülüyor")
                return []


def fetch_klines(symbol: str, interval: str, limit: int = CANDLE_LIMIT) -> Optional[pd.DataFrame]:
    """
    Belirtilen sembol ve timeframe için kline (mum) verilerini çeker.
    
    Args:
        symbol: Trading sembolü (örn: "BTCUSDT")
        interval: Timeframe (örn: "15m", "1h", "4h", "1d")
        limit: Çekilecek mum sayısı
        
    Returns:
        Mum verilerini içeren DataFrame veya hata durumunda None
        
    DataFrame kolonları:
        - open_time: Mumun açılış zamanı (datetime)
        - open: Açılış fiyatı
        - high: En yüksek fiyat
        - low: En düşük fiyat
        - close: Kapanış fiyatı
        - volume: İşlem hacmi
        - close_time: Mumun kapanış zamanı (datetime)
    """
    endpoint = "/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit + 1  # Son mumun incomplete olma ihtimaline karşı
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                SPOT_URL + endpoint,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                logger.warning(f"⚠️ {symbol} için veri boş")
                return None

            # DataFrame oluştur
            df = pd.DataFrame(
                data,
                columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_asset_volume", "number_of_trades",
                    "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                ]
            )

            # Timestamp dönüşümleri (UTC)
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)

            # Sayısal kolonları float'a çevir
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # NaN kontrolü
            df.dropna(subset=["close"], inplace=True)

            # Son mum incomplete olabilir, onu çıkar
            # (close_time şu andan küçük olanları al)
            current_time = pd.Timestamp.now(tz=timezone.utc)
            df = df[df["close_time"] < current_time]

            # İlk CANDLE_LIMIT kadarını al
            df = df.tail(limit)

            # Gereksiz kolonları kaldır
            df = df[["open_time", "open", "high", "low", "close", "volume", "close_time"]]

            # Index'i open_time olarak ayarla
            df.set_index("open_time", inplace=True)
            df = df.sort_index()

            logger.debug(f"✅ {symbol} - {interval}: {len(df)} mum çekildi")
            return df

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ {symbol} - {interval} istekleri hatası (deneme {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"❌ {symbol} - {interval} için veri çekilemedi")
                return None
                
        except Exception as e:
            logger.error(f"❌ {symbol} - {interval} beklenmeyen hata: {e}")
            return None