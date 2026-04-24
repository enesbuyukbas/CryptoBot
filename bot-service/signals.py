import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict, List

from config import SIGNAL_STRENGTH_STRONG, SIGNAL_STRENGTH_MODERATE

logger = logging.getLogger(__name__)

# ================== TIMEFRAME RİSK AYARLARI ==================
TIMEFRAME_RISK_SETTINGS = {
    "15m": {"atr_sl": 1.5, "rr": 1.5},
    "1h":  {"atr_sl": 1.8, "rr": 1.8},
    "4h":  {"atr_sl": 2.0, "rr": 2.0},
    "1d":  {"atr_sl": 2.5, "rr": 2.0},
}


def calculate_atr_based_levels(entry_price: float, atr_value: float, direction: str, timeframe: str) -> Dict:
    """
    ATR tabanlı stop-loss ve target_price hesaplar.
    
    Args:
        entry_price: Giriş fiyatı (son kapanış)
        atr_value: ATR değeri
        direction: "BUY" veya "SELL"
        timeframe: Zaman dilimi (15m, 1h, 4h, 1d)
        
    Returns:
        {
            "stop_loss": float,
            "target_price": float,
            "risk_reward": float,
            "risk_amount": float,
            "reward_amount": float
        }
    """
    # Timeframe'e göre risk ayarlarını al
    risk_settings = TIMEFRAME_RISK_SETTINGS.get(timeframe, {"atr_sl": 2.0, "rr": 2.0})
    atr_sl_multiplier = risk_settings["atr_sl"]
    rr = risk_settings["rr"]
    
    if direction == "BUY":
        # BUY için: stop aşağıda, target yukarıda
        stop_loss = entry_price - (atr_value * atr_sl_multiplier)
        target_price = entry_price + (atr_value * atr_sl_multiplier * rr)
        
    elif direction == "SELL":
        # SELL için: stop yukarıda, target aşağıda
        stop_loss = entry_price + (atr_value * atr_sl_multiplier)
        target_price = entry_price - (atr_value * atr_sl_multiplier * rr)
        
    else:
        # Geçersiz direction
        return {
            "stop_loss": entry_price,
            "target_price": entry_price,
            "risk_reward": 0,
            "risk_amount": 0,
            "reward_amount": 0
        }
    
    # Risk ve reward miktarlarını hesapla
    risk_amount = abs(entry_price - stop_loss)
    reward_amount = abs(target_price - entry_price)
    
    # Risk/Reward oranını hesapla
    actual_rr = reward_amount / risk_amount if risk_amount > 0 else 0
    
    return {
        "stop_loss": round(stop_loss, 8),
        "target_price": round(target_price, 8),
        "risk_reward": round(actual_rr, 2),
        "risk_amount": round(risk_amount, 8),
        "reward_amount": round(reward_amount, 8)
    }


def generate_signal(df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[Dict]:
    """
    Teknik indikatörlere göre BUY/SELL sinyali üretir.
    
    Sinyal Kuralları (DAHA SIKI):
    - BUY: 
        * Trend UP (Close > EMA200 ve EMA20 > EMA50)
        * Güçlü Momentum (ROC > 2)
        * Güçlü Trend (ADX > 30)
        * RSI sağlıklı aralıkta (30-70)
        * Volume ortalamanın üstünde
        
    - SELL:
        * Trend DOWN (Close < EMA200 ve EMA20 < EMA50)
        * Negatif Momentum (ROC < -2)
        * Güçlü Trend (ADX > 30)
        * RSI sağlıklı aralıkta (30-70)
        * Volume ortalamanın üstünde
    
    Args:
        df: İndikatörleri içeren DataFrame
        symbol: Trading sembolü
        timeframe: Zaman dilimi (15m, 1h, 4h, 1d)
        
    Returns:
        Sinyal dictionary veya None
    """
    if df is None or len(df) < 2:
        logger.debug(f"⚠️ {symbol} - {timeframe}: Yetersiz veri")
        return None
    
    try:
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # NaN kontrolü
        required_fields = ['close', 'adx', 'plus_di', 'minus_di', 'roc', 'ema20', 'ema50', 'ema200', 'rsi', 'volume', 'atr', 'close_time']
        for field in required_fields:
            if pd.isna(last_row.get(field)):
                logger.debug(f"⚠️ {symbol} - {timeframe}: {field} eksik")
                return None
        
        # ================== TEMEL FİLTRELER ==================
        
        # 1. ADX > 30 (Güçlü trend olmalı)
        if last_row['adx'] < 30:
            logger.debug(f"⚠️ {symbol} - {timeframe}: ADX yetersiz ({last_row['adx']:.2f} < 30)")
            return None
        
        # 2. Volume kontrolü (son 20 mumun ortalamasının üstünde olmalı)
        avg_volume = df['volume'].tail(20).mean()
        if last_row['volume'] < avg_volume * 0.8:  # %80'den fazla olmalı
            logger.debug(f"⚠️ {symbol} - {timeframe}: Volume düşük")
            return None
        
        # 3. RSI aşırı bölgelerde olmamalı
        if last_row['rsi'] > 75 or last_row['rsi'] < 25:
            logger.debug(f"⚠️ {symbol} - {timeframe}: RSI aşırı bölgede ({last_row['rsi']:.2f})")
            return None
        
        # ================== TREND BELİRLEME ==================
        close = last_row['close']
        ema20 = last_row['ema20']
        ema50 = last_row['ema50']
        ema200 = last_row['ema200']
        
        trend_up = close > ema200 and ema20 > ema50
        trend_down = close < ema200 and ema20 < ema50

        # ================== DMI YÖN DOĞRULAMASI ==================
        # +DI > -DI yükseliş yönünü, -DI > +DI düşüş yönünü doğrular
        plus_di_confirm  = last_row['plus_di'] > last_row['minus_di']
        minus_di_confirm = last_row['minus_di'] > last_row['plus_di']
        
        # ================== MOMENTUM BELİRLEME ==================
        roc = last_row['roc']
        
        # Momentum daha güçlü olmalı
        strong_positive_momentum = roc > 2
        strong_negative_momentum = roc < -2
        
        # ================== SİNYAL OLUŞTURMA ==================
        direction = None
        reasons = []
        strength = 0
        
        # BUY Sinyali (DAHA SIKI ŞARTLAR)
        if trend_up and strong_positive_momentum and plus_di_confirm:
            direction = "BUY"
            
            # TREND PUANI (0-30)
            if close > ema20 > ema50 > ema200:  # Mükemmel sıralama
                strength += 30
                reasons.append("TREND_PERFECT")
            elif close > ema200:
                strength += 20
                reasons.append("TREND_UP")
            
            # MOMENTUM PUANI (0-25)
            if roc > 5:
                strength += 25
                reasons.append("MOMENTUM_STRONG")
            elif roc > 3:
                strength += 20
                reasons.append("MOMENTUM_GOOD")
            elif roc > 2:
                strength += 15
                reasons.append("MOMENTUM_POSITIVE")
            
            # ADX PUANI (0-20)
            if last_row['adx'] > 50:
                strength += 20
                reasons.append("ADX_VERY_STRONG")
            elif last_row['adx'] > 40:
                strength += 15
                reasons.append("ADX_STRONG")
            elif last_row['adx'] > 30:
                strength += 10
                reasons.append("ADX_MODERATE")
            
            # RSI PUANI (0-10)
            if 40 <= last_row['rsi'] <= 60:  # Optimal bölge
                strength += 10
                reasons.append("RSI_OPTIMAL")
            elif 30 < last_row['rsi'] < 70:
                strength += 5
                reasons.append("RSI_HEALTHY")
            
            # MACD PUANI (0-10)
            if not pd.isna(last_row.get('macd')) and not pd.isna(last_row.get('macd_signal')):
                macd_diff = last_row['macd'] - last_row['macd_signal']
                if macd_diff > 0 and prev_row['macd'] <= prev_row['macd_signal']:
                    strength += 10
                    reasons.append("MACD_CROSS_UP")
                elif macd_diff > 0:
                    strength += 5
                    reasons.append("MACD_BULLISH")
            
            # VOLUME PUANI (0-5)
            volume_ratio = last_row['volume'] / avg_volume
            if volume_ratio > 1.5:
                strength += 5
                reasons.append("VOLUME_HIGH")
            elif volume_ratio > 1.2:
                strength += 3
                reasons.append("VOLUME_ABOVE_AVG")
        
        # SELL Sinyali (DAHA SIKI ŞARTLAR)
        elif trend_down and strong_negative_momentum and minus_di_confirm:
            direction = "SELL"
            
            # TREND PUANI (0-30)
            if close < ema20 < ema50 < ema200:  # Mükemmel sıralama
                strength += 30
                reasons.append("TREND_PERFECT")
            elif close < ema200:
                strength += 20
                reasons.append("TREND_DOWN")
            
            # MOMENTUM PUANI (0-25)
            if roc < -5:
                strength += 25
                reasons.append("MOMENTUM_STRONG")
            elif roc < -3:
                strength += 20
                reasons.append("MOMENTUM_GOOD")
            elif roc < -2:
                strength += 15
                reasons.append("MOMENTUM_NEGATIVE")
            
            # ADX PUANI (0-20)
            if last_row['adx'] > 50:
                strength += 20
                reasons.append("ADX_VERY_STRONG")
            elif last_row['adx'] > 40:
                strength += 15
                reasons.append("ADX_STRONG")
            elif last_row['adx'] > 30:
                strength += 10
                reasons.append("ADX_MODERATE")
            
            # RSI PUANI (0-10)
            if 40 <= last_row['rsi'] <= 60:  # Optimal bölge
                strength += 10
                reasons.append("RSI_OPTIMAL")
            elif 30 < last_row['rsi'] < 70:
                strength += 5
                reasons.append("RSI_HEALTHY")
            
            # MACD PUANI (0-10)
            if not pd.isna(last_row.get('macd')) and not pd.isna(last_row.get('macd_signal')):
                macd_diff = last_row['macd'] - last_row['macd_signal']
                if macd_diff < 0 and prev_row['macd'] >= prev_row['macd_signal']:
                    strength += 10
                    reasons.append("MACD_CROSS_DOWN")
                elif macd_diff < 0:
                    strength += 5
                    reasons.append("MACD_BEARISH")
            
            # VOLUME PUANI (0-5)
            volume_ratio = last_row['volume'] / avg_volume
            if volume_ratio > 1.5:
                strength += 5
                reasons.append("VOLUME_HIGH")
            elif volume_ratio > 1.2:
                strength += 3
                reasons.append("VOLUME_ABOVE_AVG")
        
        # Sinyal yok
        else:
            logger.debug(f"ℹ️ {symbol} - {timeframe}: Sinyal yok (Trend: {trend_up}/{trend_down}, ROC: {roc:.2f})")
            return None
        
        # Gücü 0-100 arasında sınırla
        strength = max(0, min(100, strength))
        
        # Minimum güç kontrolü (en az 50 olmalı)
        if strength < 50:
            logger.debug(f"⚠️ {symbol} - {timeframe}: Sinyal gücü yetersiz ({strength}% < 50%)")
            return None
        
        # ================== ATR TABANLI STOP & TARGET HESAPLA ==================
        entry_price = float(last_row['close'])
        atr_value = float(last_row['atr'])
        
        atr_levels = calculate_atr_based_levels(entry_price, atr_value, direction, timeframe)
        
        # ================== SİNYAL DOKÜMANINI OLUŞTUR ==================
        signal = {
            "symbol": symbol,
            "timeframe": timeframe,
            "direction": direction,
            "strength": int(strength),
            "reason": reasons,
            "price": entry_price,
            "stop_loss": atr_levels["stop_loss"],
            "target_price": atr_levels["target_price"],
            "risk_reward": atr_levels["risk_reward"],
            "risk_amount": atr_levels["risk_amount"],
            "reward_amount": atr_levels["reward_amount"],
            "atr": float(atr_value),
            "rsi": float(last_row['rsi']),
            "adx": float(last_row['adx']),
            "roc": float(roc),
            "volume_ratio": float(volume_ratio),
            # Mumun kapanış zamanı — sinyalin üretildiği anki kapanmış mumun UTC zamanı
            "opened_at": last_row['close_time'].to_pydatetime() if isinstance(last_row.get('close_time'), pd.Timestamp) else datetime.now(timezone.utc)
        }
        
        # Log mesajı
        logger.info(
            f"✅ {symbol} - {timeframe} | {direction} | "
            f"Güç: {strength}% | "
            f"Entry: ${entry_price:.6f} | "
            f"Stop: ${atr_levels['stop_loss']:.6f} | "
            f"Target: ${atr_levels['target_price']:.6f} | "
            f"R:R {atr_levels['risk_reward']}"
        )
        
        return signal
        
    except Exception as e:
        logger.error(f"❌ {symbol} - {timeframe} sinyal oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_signal_strength_category(strength: int) -> str:
    """
    Sinyal gücünü kategorize eder.
    
    Args:
        strength: Sinyal gücü (0-100)
        
    Returns:
        "STRONG", "MODERATE" veya "WEAK"
    """
    if strength >= SIGNAL_STRENGTH_STRONG:
        return "STRONG"
    elif strength >= SIGNAL_STRENGTH_MODERATE:
        return "MODERATE"
    else:
        return "WEAK"


def filter_signals_by_strength(signals: List[Dict], min_strength: int = 50) -> List[Dict]:
    """
    Sinyalleri güce göre filtreler.
    
    Args:
        signals: Sinyal listesi
        min_strength: Minimum güç threshold'u
        
    Returns:
        Filtrelenmiş sinyal listesi
    """
    return [sig for sig in signals if sig.get('strength', 0) >= min_strength]


def get_top_signals(signals: List[Dict], limit: int = 10) -> List[Dict]:
    """
    En güçlü sinyalleri döndürür.
    
    Args:
        signals: Sinyal listesi
        limit: Döndürülecek maksimum sinyal sayısı
        
    Returns:
        Güce göre sıralanmış top N sinyal
    """
    return sorted(signals, key=lambda x: x.get('strength', 0), reverse=True)[:limit]