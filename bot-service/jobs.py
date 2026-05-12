import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import List

from config import MAX_WORKERS, CANDLE_LIMIT, SPOT_URL, REQUEST_TIMEOUT, CLOSED_SIGNAL_RETENTION_SECONDS
from binance_client import get_spot_symbols, fetch_klines
from indicators import add_indicators
from signals import generate_signal
from repository import save_signal_if_new, get_db

logger = logging.getLogger(__name__)


def process_single_symbol(symbol: str, timeframe: str) -> str:
    """
    Tek bir sembol için işlem yapar.
    
    Returns:
        "signal"   : Sinyal üretildi ve kaydedildi
        "no_signal": Sinyal üretilemedi (kriter sağlanamadı veya veri yok)
        "error"    : İşlem sırasında hata oluştu
    """
    try:
        # 1. Veri çek
        df = fetch_klines(symbol, timeframe, limit=CANDLE_LIMIT)
        
        if df is None or len(df) < 200:
            logger.debug(f"⚠️ {symbol} - {timeframe}: Yetersiz veri ({len(df) if df is not None else 0}/200)")
            return "no_signal"
        
        # 2. İndikatörleri hesapla
        df = add_indicators(df)
        
        if df is None:
            logger.warning(f"⚠️ {symbol} - {timeframe}: İndikatör hesaplama başarısız")
            return "error"
        
        # 3. Sinyal üret
        signal = generate_signal(df, symbol, timeframe)
        
        # 4. Sinyal varsa kaydet
        if signal:
            success = save_signal_if_new(signal)
            if success:
                logger.info(
                    f"✅ {symbol} - {timeframe} | "
                    f"{signal['direction']} | "
                    f"Güç: {signal['strength']}% | "
                    f"Fiyat: ${signal['price']:.4f}"
                )
                return "signal"
            else:
                logger.warning(f"⚠️ {symbol} - {timeframe}: Sinyal kaydedilemedi")
                return "error"
        else:
            logger.debug(f"ℹ️ {symbol} - {timeframe}: Sinyal yok")
            return "no_signal"
            
    except Exception as e:
        logger.error(f"❌ {symbol} - {timeframe} işlem hatası: {e}")
        import traceback
        traceback.print_exc()
        return "error"


def run_job_for_timeframe(timeframe: str) -> dict:
    """
    Belirtilen timeframe için tüm sembolleri işler.
    
    İşlem Adımları:
    1. Top 200 sembolü al
    2. Her sembol için paralel işlem yap
    3. Sonuçları topla ve raporla
    
    Args:
        timeframe: Zaman dilimi (örn: "15m", "1h", "4h", "1d")
        
    Returns:
        İstatistik dictionary:
        {
            "timeframe": "15m",
            "total": 200,
            "successful": 185,
            "failed": 15,
            "signals_found": 42
        }
    """
    logger.info(f"▶ {timeframe.upper()} işlem başlıyor")

    # 1. Sembolleri al
    symbols = get_spot_symbols()
    
    if not symbols:
        logger.error(f"❌ {timeframe}: Sembol listesi alınamadı")
        return {
            "timeframe": timeframe,
            "total": 0,
            "successful": 0,
            "failed": 0,
            "signals_found": 0
        }
    
    logger.info(f"📊 {len(symbols)} sembol işlenecek")
    
    # 2. Paralel işleme
    successful = 0
    failed = 0
    signals_found = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Future'ları oluştur
        futures = {
            executor.submit(process_single_symbol, symbol, timeframe): symbol
            for symbol in symbols
        }
        
        # Sonuçları topla
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result(timeout=30)
                if result == "signal":
                    successful += 1
                    signals_found += 1
                elif result == "no_signal":
                    successful += 1
                else:  # "error"
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"❌ {symbol} - {timeframe} future hatası: {e}")
    
    # 3. İstatistikleri raporla
    logger.info(f"✔ {timeframe.upper()} tamamlandı | sembol={len(symbols)} başarılı={successful} başarısız={failed} sinyal={signals_found}")
    
    return {
        "timeframe": timeframe,
        "total": len(symbols),
        "successful": successful,
        "failed": failed,
        "signals_found": signals_found
    }


def run_job_for_all_timeframes(timeframes: List[str]) -> dict:
    """
    Tüm timeframe'ler için sırayla işlem yapar.
    
    Args:
        timeframes: Timeframe listesi (örn: ["15m", "1h", "4h", "1d"])
        
    Returns:
        Tüm timeframe'lerin istatistikleri
    """
    logger.info(f"▶ Run başlıyor | timeframes={', '.join(timeframes)}")

    # Tüm timeframe'lerden önce açık sinyallerin TP/SL durumunu bir kez kontrol et
    check_signal_outcomes()

    all_stats = {}

    for tf in timeframes:
        stats = run_job_for_timeframe(tf)
        all_stats[tf] = stats
    
    # Genel rapor
    total_processed = sum(s['total'] for s in all_stats.values())
    total_successful = sum(s['successful'] for s in all_stats.values())
    total_failed = sum(s['failed'] for s in all_stats.values())
    tf_summary = ' | '.join(f"{tf}:{s['signals_found']}sig" for tf, s in all_stats.items())
    logger.info(f"✔ Run tamamlandı | işlenen={total_processed} başarılı={total_successful} başarısız={total_failed} | {tf_summary}")
    
    return all_stats


# ================== TP/SL SONUÇ TAKİBİ ==================

def check_signal_outcomes() -> dict:
    """
    Açık sinyallerin TP/SL durumunu kontrol eder.
    Her bot çalışmasında bir kez çağrılmalıdır.

    - tp_hit / sl_hit henüz set edilmemiş sinyalleri sorgular
    - Binance toplu fiyat endpoint'i ile tek istekte tüm fiyatları çeker
    - TP öncelikli elif mantığıyla tp_hit ve sl_hit'in aynı anda True olması engellenir

    Returns:
        {"checked": int, "tp_hits": int, "sl_hits": int, "still_open": int}
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    open_signals = list(db.signals.find({
        "tp_hit": None,
        "sl_hit": None,
        "target_price": {"$ne": None},
        "stop_loss": {"$ne": None}
    }))

    if not open_signals:
        logger.info("📊 Outcome check: Açık sinyal yok")
        return {"checked": 0, "tp_hits": 0, "sl_hits": 0, "still_open": 0}

    unique_symbols = list({s["symbol"] for s in open_signals})
    logger.info(f"📊 Outcome check: {len(open_signals)} açık sinyal | {len(unique_symbols)} benzersiz sembol")

    # Parametre göndermeden tüm fiyatları çek — Binance tüm sembolleri döner
    response = None
    price_map: dict = {}
    try:
        response = requests.get(
            f"{SPOT_URL}/api/v3/ticker/price",
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        price_map = {
            item["symbol"]: float(item["price"])
            for item in response.json()
            if "symbol" in item and "price" in item
        }
        logger.info(f"📊 Outcome check: {len(price_map)} fiyat çekildi")
    except Exception as e:
        status = response.status_code if response is not None else "N/A"
        body = response.text[:500] if response is not None else ""
        logger.error(f"❌ Toplu fiyat çekme hatası: {e} | status={status} | body={body}")
        return {"checked": 0, "tp_hits": 0, "sl_hits": 0, "still_open": 0}

    checked = tp_hits = sl_hits = still_open = 0

    for signal in open_signals:
        symbol = signal.get("symbol")
        current_price = price_map.get(symbol)

        if current_price is None:
            logger.warning(f"⚠️ {symbol} için fiyat bulunamadı, atlanıyor")
            continue

        checked += 1
        direction = signal["direction"]
        tp = signal["target_price"]
        sl = signal["stop_loss"]

        # TP öncelikli — elif kullanarak tp_hit ve sl_hit'in aynı anda True olması engellenir
        if direction == "BUY":
            if current_price >= tp:
                tp_hit, sl_hit = True, False
            elif current_price <= sl:
                tp_hit, sl_hit = False, True
            else:
                tp_hit, sl_hit = False, False
        elif direction == "SELL":
            if current_price <= tp:
                tp_hit, sl_hit = True, False
            elif current_price >= sl:
                tp_hit, sl_hit = False, True
            else:
                tp_hit, sl_hit = False, False
        else:
            continue

        if tp_hit or sl_hit:
            closed_retention = CLOSED_SIGNAL_RETENTION_SECONDS.get(signal["timeframe"], 30 * 86400)
            db.signals.update_one(
                {"_id": signal["_id"]},
                {"$set": {
                    "tp_hit": tp_hit,
                    "sl_hit": sl_hit,
                    "outcome_price": current_price,
                    "outcome_checked_at": now,
                    "expires_at": now + timedelta(seconds=closed_retention)
                }}
            )
            if tp_hit:
                tp_hits += 1
                logger.info(f"✅ TP | {symbol} - {signal['timeframe']} | {direction} | ${current_price:.4f}")
            else:
                sl_hits += 1
                logger.info(f"❌ SL | {symbol} - {signal['timeframe']} | {direction} | ${current_price:.4f}")
        else:
            still_open += 1
            db.signals.update_one(
                {"_id": signal["_id"]},
                {"$set": {"outcome_checked_at": now}}
            )

    logger.info(
        f"📊 Outcome check: {checked} kontrol | "
        f"✅ TP: {tp_hits} | ❌ SL: {sl_hits} | ⏳ Açık: {still_open}"
    )
    return {"checked": checked, "tp_hits": tp_hits, "sl_hits": sl_hits, "still_open": still_open}