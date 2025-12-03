import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from config import MAX_WORKERS
from binance_client import get_spot_symbols, fetch_klines
from indicators import add_indicators
from signals import generate_signal
from repository import save_signal_if_new
from config import MAX_WORKERS, CANDLE_LIMIT

logger = logging.getLogger(__name__)


def process_single_symbol(symbol: str, timeframe: str) -> bool:
    """
    Tek bir sembol için işlem yapar.
    
    İşlem Adımları:
    1. Binance'ten 200 mum verisi çek
    2. İndikatörleri hesapla
    3. Sinyal üret
    4. Sinyal varsa MongoDB'ye kaydet
    
    Args:
        symbol: Trading sembolü (örn: "BTCUSDT")
        timeframe: Zaman dilimi (örn: "15m")
        
    Returns:
        True: İşlem başarılı
        False: İşlem başarısız
    """
    try:
        # 1. Veri çek
        df = fetch_klines(symbol, timeframe, limit=CANDLE_LIMIT)
        
        if df is None or len(df) < 200:
            logger.debug(f"⚠️ {symbol} - {timeframe}: Yetersiz veri ({len(df) if df is not None else 0}/200)")
            return False
        
        # 2. İndikatörleri hesapla
        df = add_indicators(df)
        
        if df is None:
            logger.warning(f"⚠️ {symbol} - {timeframe}: İndikatör hesaplama başarısız")
            return False
        
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
                return True
            else:
                logger.warning(f"⚠️ {symbol} - {timeframe}: Sinyal kaydedilemedi")
                return False
        else:
            logger.debug(f"ℹ️ {symbol} - {timeframe}: Sinyal yok")
            return True  # Sinyal yoksa da başarılı sayılır
            
    except Exception as e:
        logger.error(f"❌ {symbol} - {timeframe} işlem hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


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
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 {timeframe.upper()} için işlem başlatılıyor...")
    logger.info(f"{'='*60}")
    
    # 1. Sembolleri al
    symbols = get_spot_symbols(limit=200)
    
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
                if result:
                    successful += 1
                    # Sinyal olup olmadığını kontrol et (log'dan anlayabiliriz)
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"❌ {symbol} - {timeframe} future hatası: {e}")
    
    # 3. İstatistikleri raporla
    logger.info(f"\n{'='*60}")
    logger.info(f"📈 {timeframe.upper()} İSTATİSTİKLERİ:")
    logger.info(f"   Toplam Sembol: {len(symbols)}")
    logger.info(f"   ✅ Başarılı: {successful}")
    logger.info(f"   ❌ Başarısız: {failed}")
    logger.info(f"{'='*60}\n")
    
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
    logger.info(f"\n{'#'*60}")
    logger.info(f"🚀 TÜM TIMEFRAME'LER İÇİN İŞLEM BAŞLATILIYOR")
    logger.info(f"   Timeframes: {', '.join(timeframes)}")
    logger.info(f"{'#'*60}\n")
    
    all_stats = {}
    
    for tf in timeframes:
        stats = run_job_for_timeframe(tf)
        all_stats[tf] = stats
    
    # Genel rapor
    logger.info(f"\n{'#'*60}")
    logger.info(f"📊 GENEL ÖZET:")
    total_processed = sum(s['total'] for s in all_stats.values())
    total_successful = sum(s['successful'] for s in all_stats.values())
    total_failed = sum(s['failed'] for s in all_stats.values())
    
    logger.info(f"   Toplam İşlem: {total_processed}")
    logger.info(f"   ✅ Başarılı: {total_successful}")
    logger.info(f"   ❌ Başarısız: {total_failed}")
    
    for tf, stats in all_stats.items():
        logger.info(f"   {tf}: {stats['successful']}/{stats['total']}")
    
    logger.info(f"{'#'*60}\n")
    
    return all_stats