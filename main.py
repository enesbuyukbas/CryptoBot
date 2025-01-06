from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
import time
from datetime import datetime
import config  # API anahtarlarını saklayacağımız config dosyası

# Binance client'ı başlat
client = Client(config.API_KEY, config.API_SECRET)

def get_historical_data(symbol, interval, lookback):
    """Geçmiş fiyat verilerini çeker"""
    try:
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        df['close'] = pd.to_numeric(df['close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None

def calculate_signals(df):
    """Teknik analiz göstergelerini hesaplar ve alım/satım sinyalleri üretir"""
    # Hareketli ortalamalar
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    
    # RSI hesaplama
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Alım/Satım sinyalleri
    df['signal'] = 'bekle'
    
    # Alım sinyali: MA20 > MA50 ve RSI < 70
    buy_condition = (df['MA20'] > df['MA50']) & (df['RSI'] < 70)
    df.loc[buy_condition, 'signal'] = 'al'
    
    # Satım sinyali: MA20 < MA50 ve RSI > 30
    sell_condition = (df['MA20'] < df['MA50']) & (df['RSI'] > 30)
    df.loc[sell_condition, 'signal'] = 'sat'
    
    return df

def run_bot():
    """Trading bot'un ana fonksiyonu"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # İzlenecek coinler
    interval = Client.KLINE_INTERVAL_1HOUR  # 1 saatlik mum
    lookback = "100 hours ago UTC"  # Geriye dönük veri miktarı
    
    while True:
        try:
            for symbol in symbols:
                print(f"\n{datetime.now()} - {symbol} analiz ediliyor...")
                
                # Verileri çek
                df = get_historical_data(symbol, interval, lookback)
                if df is None:
                    continue
                
                # Sinyalleri hesapla
                df = calculate_signals(df)
                
                # Son sinyali kontrol et
                last_signal = df['signal'].iloc[-1]
                current_price = float(df['close'].iloc[-1])
                
                if last_signal == 'al':
                    print(f"{symbol} için ALIM sinyali! Fiyat: {current_price}")
                elif last_signal == 'sat':
                    print(f"{symbol} için SATIM sinyali! Fiyat: {current_price}")
                
            # Her 5 dakikada bir güncelle
            time.sleep(300)
            
        except Exception as e:
            print(f"Hata oluştu: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()