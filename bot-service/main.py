import os
import sys
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import talib
from pymongo import MongoClient
from bson.objectid import ObjectId
import traceback


# Ana dizini Python yoluna ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    SPOT_URL,
    INTERVAL,
    LIMIT,
    RSI_PERIOD,
    FAST_LENGTH,
    SLOW_LENGTH,
    SIGNAL_LENGTH,
    MACD_THRESHOLDS,
    ADX_PERIOD,
    MONGODB_URI,
)

# MongoDB bağlantısını yap
client = MongoClient(MONGODB_URI)
db = client["cryptoDB"]


def get_spot_symbols():
    """Binance spot işlem çiftlerini çeker"""
    max_retries = 3  # Maksimum deneme sayısı
    retry_delay = 2  # Denemeler arası bekleme süresi (saniye)

    for attempt in range(max_retries):
        try:
            response = requests.get(f"{SPOT_URL}/api/v3/exchangeInfo", timeout=10)
            response.raise_for_status()
            data = response.json()

            # Sadece USDT çiftlerini al ve aktif olanları filtrele
            symbols = [               
                symbol['symbol'] for symbol in data['symbols']
                if symbol['symbol'].endswith('USDT') 
                and symbol['status'] == 'TRADING'
            ]

            # İşlem hacmine göre sırala ve ilk 200'ü al
            volumes = {}
            for symbol in symbols:
                try:
                    # 24 saatlik işlem hacmini al
                    for retry in range(max_retries):
                        try:
                            response = requests.get(
                                f"{SPOT_URL}/api/v3/ticker/24hr",
                                params={"symbol": symbol},
                                timeout=10,
                            )
                            response.raise_for_status()
                            volume_data = response.json()
                            volumes[symbol] = float(volume_data["quoteVolume"])
                            time.sleep(0.1)  # API limit aşımını önlemek için
                            break  # Başarılı olursa döngüden çık
                        except Exception as e:
                            if retry == max_retries - 1:  # Son deneme başarısız olduysa
                                print(f"Hacim verisi alınamadı - {symbol}: {e}")
                                volumes[symbol] = 0
                            else:
                                time.sleep(retry_delay)
                                continue
                except Exception as e:
                    print(f"Hacim verisi alınamadı - {symbol}: {e}")
                    volumes[symbol] = 0

            # Hacme göre sırala ve ilk 200'ü al
            sorted_symbols = sorted(volumes.items(), key=lambda x: x[1], reverse=True)[
                :200
            ]
            return [symbol for symbol, _ in sorted_symbols]

        except Exception as e:
            if attempt == max_retries - 1:  # Son deneme başarısız olduysa
                print(f"Sembol listesi alınamadı: {e}")
                return []
            else:
                print(
                    f"Bağlantı hatası, yeniden deneniyor ({attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                continue




from datetime import datetime

from datetime import datetime, timedelta

def fetch_price_data(symbol, interval="1h", limit=1000):
    """Binance spot fiyat verilerini çeker"""
    endpoint = "/api/v3/klines"  
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        fetch_time_tr = datetime.utcnow() + timedelta(hours=3)  # 🌟 Türkiye saatine çevir

        response = requests.get(SPOT_URL + endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(
            data,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )

        # Veri tiplerini düzenle
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms") + timedelta(hours=3)  # ✅ Türkiye saatine çevir
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["close"], inplace=True)

        df["fetch_time"] = fetch_time_tr  # ✅ Türkiye saatiyle kaydet

        df["ma200"] = df["close"].rolling(window=200).mean()
        df["rsi_close"] = talib.RSI(df["close"], timeperiod=RSI_PERIOD)
        df["rsi_change_close"] = df["rsi_close"].diff()
        df["adx"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=ADX_PERIOD)
        df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)
        df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)

        macd, signal, hist = talib.MACD(df["close"])
        df["macd_change"] = macd
        df["signal_change"] = signal

        df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
        df["momentum"] = df["close"].pct_change(10) * 100
        df["ob_high"] = df["high"].rolling(window=12).max()
        df["ob_low"] = df["low"].rolling(window=12).min()

        df.set_index("open_time", inplace=True)
        return df
    except Exception as e:
        print(f"Veri çekme hatası - {symbol}: {e}")
        traceback.print_exc()  
        return None





def initialize_db():
    """MongoDB'ye koleksiyonları oluşturur (Atlas için güncellendi)"""
    if "price_data" not in db.list_collection_names():
        db.create_collection("price_data")  # Capped kaldırıldı

    if "signals" not in db.list_collection_names():
        db.create_collection("signals")  # Capped kaldırıldı


def calculate_signals(df):
    """Tüm teknik sinyalleri hesaplar"""
    signals = []

    # 🕒 **Gerçek sinyal zamanı: Türkiye saati olarak kaydediyoruz!**
    current_time_tr = (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

    rsi_signals = []
    if df['rsi_change_close'].iloc[-1] > 20 and df['rsi_change_close'].iloc[-2] <= 20:
        rsi_signals.append('C20L')
    elif df['rsi_change_close'].iloc[-1] > 10 and df['rsi_change_close'].iloc[-2] <= 10:
        rsi_signals.append('C10L')
    elif df['rsi_change_close'].iloc[-1] < -20 and df['rsi_change_close'].iloc[-2] >= -20:
        rsi_signals.append('C20S')
    elif df['rsi_change_close'].iloc[-1] < -10 and df['rsi_change_close'].iloc[-2] >= -10:
        rsi_signals.append('C10S')

    macd_signals = []
    for level in ['M2', 'M3', 'M4', 'M5']:
        threshold = int(level[1])
        if df['macd_change'].iloc[-1] > threshold and df['macd_change'].iloc[-2] <= threshold:
            macd_signals.append(f'{level}L')
        elif df['macd_change'].iloc[-1] < -threshold and df['macd_change'].iloc[-2] >= -threshold:
            macd_signals.append(f'{level}S')

    ma_signals = []
    if df['close'].iloc[-1] > df['ma200'].iloc[-1] and df['close'].iloc[-2] <= df['ma200'].iloc[-2]:
        ma_signals.append('MA200L')
    elif df['close'].iloc[-1] < df['ma200'].iloc[-1] and df['close'].iloc[-2] >= df['ma200'].iloc[-2]:
        ma_signals.append('MA200S')

    all_signals = rsi_signals + macd_signals + ma_signals
    if all_signals:
        signal_type = 'Long' if any(s.endswith('L') for s in all_signals) else 'Short'
        signals.append({
            'signal_type': signal_type,
            'signal_time': current_time_tr,  # ✅ Türkiye saatine göre kaydediyoruz!
            'price': df['close'].iloc[-1],
            'pullback_level': df['low'].iloc[-1] if signal_type == 'Long' else df['high'].iloc[-1],
            'strength': len(all_signals),
            'indicators': ','.join(all_signals),
            'rsi': df['rsi_close'].iloc[-1],
            'macd': df['macd_change'].iloc[-1],
            'momentum': df['momentum'].iloc[-1],
            'atr': df['atr'].iloc[-1]
        })
    
    return signals




def save_price_data(symbol, df):
    """Fiyat verilerini MongoDB'ye kaydeder"""
    if df is None or df.empty:
        return

    try:
        last_row = df.iloc[-1:].copy()

        # `open_time` sütununu datetime formatına çevir
        last_row.index = last_row.index.astype(str)  # 🛠️ MongoDB'ye uygun hale getir
        
        data_to_save = {
            'symbol': symbol,
            'timestamp': datetime.strptime(last_row.index[0], "%Y-%m-%d %H:%M:%S"),  # ✅ ISODate formatına çevir
            'open': last_row['open'].iloc[0],
            'high': last_row['high'].iloc[0],
            'low': last_row['low'].iloc[0],
            'close': last_row['close'].iloc[0],
            'volume': last_row['volume'].iloc[0],
            'ma200': last_row['ma200'].iloc[0] if 'ma200' in last_row else None,
            'rsi_close': last_row['rsi_close'].iloc[0] if 'rsi_close' in last_row else None,
            'rsi_change_close': last_row['rsi_change_close'].iloc[0] if 'rsi_change_close' in last_row else None,
            'adx': last_row['adx'].iloc[0] if 'adx' in last_row else None,
            'plus_di': last_row['+DI'].iloc[0] if '+DI' in last_row else None,
            'minus_di': last_row['-DI'].iloc[0] if '-DI' in last_row else None,
            'macd_change': last_row['macd_change'].iloc[0] if 'macd_change' in last_row else None,
            'signal_change': last_row['signal_change'].iloc[0] if 'signal_change' in last_row else None,
            'atr': last_row['atr'].iloc[0] if 'atr' in last_row else None,
            'momentum': last_row['momentum'].iloc[0] if 'momentum' in last_row else None,
            'ob_high': last_row['ob_high'].iloc[0] if 'ob_high' in last_row else None,
            'ob_low': last_row['ob_low'].iloc[0] if 'ob_low' in last_row else None
        }
        
        db.price_data.update_one(
            {"symbol": symbol, "timestamp": data_to_save["timestamp"]},  
            {"$set": data_to_save},
            upsert=True  # Eğer yoksa ekle, varsa güncelle
        )
    except Exception as e:
        print(f"Veri kaydetme hatası - {symbol}: {e}")



def save_signals(symbol, signals):
    """Sinyalleri MongoDB'ye kaydeder"""
    if not signals:
        return

    try:
        for signal in signals:
            signal_data = {
                "symbol": symbol,
                "signal_time": signal["signal_time"],
                "signal_type": signal["signal_type"],
                "price": signal["price"],
                "pullback_level": signal["pullback_level"],
                "strength": signal["strength"],
                "indicators": signal["indicators"],
            }
            db.signals.update_one(
                {"symbol": symbol, "signal_time": signal_data["signal_time"]},
                {"$set": signal_data},
                upsert=True,  # Eğer yoksa ekle, varsa güncelle
            )

            # En güçlü 3 sinyali göster
            top_signals = (
                db.signals.find().sort([("strength", -1), ("signal_time", -1)]).limit(3)
            )
            if top_signals:
                print("\n🏆 En Güçlü 3 Sinyal:")
                for signal in top_signals:
                    print(
                        f"💫 {signal['symbol']} - {signal['signal_type']} (Güç: {signal['strength']}) - {signal['indicators']}"
                    )
    except Exception as e:
        print(f"Sinyal kaydetme hatası - {symbol}: {e}")


def main():
    """Ana program döngüsü"""
    print("Program başlatılıyor...")
    initialize_db()

    while True:
        try:
            print("Spot işlem çiftleri alınıyor...")
            symbols = get_spot_symbols()
            print(f"Toplam {len(symbols)} çift bulundu.")

            for symbol in symbols:
                try:
                    print(f"{symbol} için veriler çekiliyor...")
                    df = fetch_price_data(symbol)

                    if df is not None:
                        # Verileri kaydet
                        save_price_data(symbol, df)

                        # Sinyalleri hesapla ve kaydet
                        signals = calculate_signals(df)
                        save_signals(symbol, signals)

                        if signals:  # Yeni sinyal varsa bildir
                            for signal in signals:
                                print(
                                    f"🔔 {symbol} - {signal['signal_type']} Sinyali @ {signal['signal_time']}"
                                )

                        print(f"✅ {symbol} için veriler güncellendi.")

                    time.sleep(0.5)  # API limit aşımını önlemek için
                except Exception as e:
                    print(f"❌ {symbol} işlenirken hata: {e}")
                    continue

            print("Tüm veriler güncellendi. 1 saat bekleniyor...")
            time.sleep(3600)  # 1 saat bekle
        except Exception as e:
            print(f"Genel hata oluştu: {e}")
            time.sleep(60)  # Hata durumunda 1 dakika bekle


if __name__ == "__main__":
    main()
