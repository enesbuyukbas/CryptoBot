import logging
import pandas as pd
import numpy as np
import talib

from config import (
    EMA_PERIODS,
    RSI_PERIOD,
    ATR_PERIOD,
    ADX_PERIOD,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    ROC_PERIOD
)

logger = logging.getLogger(__name__)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame'e teknik indikatörleri ekler.
    
    Hesaplanan indikatörler:
    - EMA20, EMA50, EMA200
    - RSI (14)
    - ATR (14)
    - ADX (14), +DI, -DI
    - MACD (12, 26, 9)
    - ROC (10)
    
    Args:
        df: OHLCV verilerini içeren DataFrame
        
    Returns:
        İndikatörlerin eklendiği DataFrame
    """
    if df is None or len(df) < 200:
        logger.warning(f"⚠️ Yetersiz veri (mevcut: {len(df) if df is not None else 0}, gerekli: 200)")
        return df

    try:
        df = df.copy()
        
        # ================== HAREKETLI ORTALAMALAR ==================
        df['ema20'] = talib.EMA(df['close'], timeperiod=EMA_PERIODS['EMA20'])
        df['ema50'] = talib.EMA(df['close'], timeperiod=EMA_PERIODS['EMA50'])
        df['ema200'] = talib.EMA(df['close'], timeperiod=EMA_PERIODS['EMA200'])
        
        # ================== RSI ==================
        df['rsi'] = talib.RSI(df['close'], timeperiod=RSI_PERIOD)
        
        # ================== ATR (Volatilite) ==================
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=ATR_PERIOD)
        
        # ================== ADX (Trend Gücü) ==================
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)
        df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)
        df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=ADX_PERIOD)
        
        # ================== MACD ==================
        macd, macd_signal, macd_hist = talib.MACD(
            df['close'],
            fastperiod=MACD_FAST,
            slowperiod=MACD_SLOW,
            signalperiod=MACD_SIGNAL
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # ================== ROC (Rate of Change - Momentum) ==================
        df['roc'] = talib.ROC(df['close'], timeperiod=ROC_PERIOD)
        
        logger.debug(f"✅ İndikatörler hesaplandı (toplam: {len(df)} satır)")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ İndikatör hesaplama hatası: {e}")
        import traceback
        traceback.print_exc()
        return df


def get_trend_direction(df: pd.DataFrame) -> str:
    """
    Mevcut trend yönünü belirler.
    
    Args:
        df: İndikatörleri içeren DataFrame
        
    Returns:
        "UP", "DOWN" veya "NEUTRAL"
    """
    if df is None or len(df) < 2:
        return "NEUTRAL"
    
    try:
        last_row = df.iloc[-1]
        
        # Close > EMA200 ve EMA20 > EMA50 → Trend UP
        if (not pd.isna(last_row['ema200']) and 
            not pd.isna(last_row['ema20']) and 
            not pd.isna(last_row['ema50'])):
            
            if last_row['close'] > last_row['ema200'] and last_row['ema20'] > last_row['ema50']:
                return "UP"
            elif last_row['close'] < last_row['ema200'] and last_row['ema20'] < last_row['ema50']:
                return "DOWN"
        
        return "NEUTRAL"
        
    except Exception as e:
        logger.warning(f"⚠️ Trend yönü belirlenemedi: {e}")
        return "NEUTRAL"


def get_momentum_status(df: pd.DataFrame) -> str:
    """
    Momentum durumunu belirler.
    
    Args:
        df: İndikatörleri içeren DataFrame
        
    Returns:
        "POSITIVE", "NEGATIVE" veya "NEUTRAL"
    """
    if df is None or len(df) < 2:
        return "NEUTRAL"
    
    try:
        last_row = df.iloc[-1]
        
        # ROC > 0 → Pozitif momentum
        if not pd.isna(last_row['roc']):
            if last_row['roc'] > 0:
                return "POSITIVE"
            elif last_row['roc'] < 0:
                return "NEGATIVE"
        
        return "NEUTRAL"
        
    except Exception as e:
        logger.warning(f"⚠️ Momentum durumu belirlenemedi: {e}")
        return "NEUTRAL"


def is_strong_trend(df: pd.DataFrame) -> bool:
    """
    Güçlü trend kontrolü yapar.
    
    Args:
        df: İndikatörleri içeren DataFrame
        
    Returns:
        ADX > 25 ise True, değilse False
    """
    if df is None or len(df) < 1:
        return False
    
    try:
        last_row = df.iloc[-1]
        
        if not pd.isna(last_row['adx']):
            return last_row['adx'] > 25
        
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ Güçlü trend kontrolü yapılamadı: {e}")
        return False