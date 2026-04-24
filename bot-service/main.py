#!/usr/bin/env python3
"""
Kripto Teknik Analiz Botu - Ana Giriş Noktası

Kullanım:
    python main.py --timeframe 15m
    python main.py --timeframe 1h
    python main.py --timeframe 4h
    python main.py --timeframe 1d
    python main.py --timeframe all
"""

import sys
import logging
import argparse
from datetime import datetime

from config import TIMEFRAMES
from repository import init_indexes, get_top_signals_by_strength
from jobs import run_job_for_timeframe, run_job_for_all_timeframes, check_signal_outcomes

logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Komut satırı argümanlarını parse eder.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Kripto Teknik Analiz Botu - Binance SPOT Sinyal Üretici',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py --timeframe 15m    # Sadece 15 dakikalık timeframe
  python main.py --timeframe 1h     # Sadece 1 saatlik timeframe
  python main.py --timeframe all    # Tüm timeframe'ler (15m, 1h, 4h, 1d)
  
Not:
  - Program bir kere çalışır ve sonlanır (sonsuz döngü yok)
  - Zamanlamayı cron veya benzeri araçlarla yapın
  - MongoDB URI'yi .env dosyasında tanımlayın
        """
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        required=True,
        choices=['15m', '1h', '4h', '1d', 'all'],
        help='İşlenecek timeframe (15m, 1h, 4h, 1d veya all)'
    )
    
    parser.add_argument(
        '--show-top',
        type=int,
        default=10,
        help='İşlem sonunda en güçlü N sinyali göster (varsayılan: 10)'
    )
    
    return parser.parse_args()


def show_top_signals(limit: int = 10):
    """
    En güçlü sinyalleri ekrana yazdırır.
    
    Args:
        limit: Gösterilecek maksimum sinyal sayısı
    """
    try:
        top_signals = get_top_signals_by_strength(limit=limit)
        
        if not top_signals:
            logger.info("Henüz sinyal bulunamadı")
            return

        logger.info(f"Top {len(top_signals)} sinyal:")
        for i, sig in enumerate(top_signals, 1):
            symbol = sig.get('symbol', 'N/A')
            timeframe = sig.get('timeframe', 'N/A')
            direction = sig.get('direction', 'N/A')
            strength = sig.get('strength', 0)
            price = sig.get('price', 0)
            reasons = ', '.join(sig.get('reason', []))
            logger.info(f"  {i}. {symbol} {timeframe} {direction} {strength}% ${price:.4f} | {reasons}")
        
    except Exception as e:
        logger.error(f"❌ Top sinyal gösterme hatası: {e}")


def main():
    """
    Ana program giriş noktası.
    """
    # Başlangıç zamanı
    start_time = datetime.now()
    
    logger.info(f"▶ Bot başlıyor | {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Argümanları parse et
    try:
        args = parse_arguments()
    except SystemExit:
        return 1
    
    # MongoDB index'lerini oluştur
    try:
        logger.info("🔧 MongoDB index'leri kontrol ediliyor...")
        init_indexes()
        logger.info("✅ MongoDB hazır\n")
    except Exception as e:
        logger.error(f"❌ MongoDB başlatma hatası: {e}")
        return 1
    
    # İşlemi başlat
    try:
        if args.timeframe == 'all':
            # Tüm timeframe'ler için çalıştır
            stats = run_job_for_all_timeframes(TIMEFRAMES)
        else:
            # Tek timeframe için çalıştır
            stats = run_job_for_timeframe(args.timeframe)
        
        # En güçlü sinyalleri göster
        if args.show_top > 0:
            show_top_signals(limit=args.show_top)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Program kullanıcı tarafından durduruldu (Ctrl+C)")
        return 130
    
    except Exception as e:
        logger.error(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Bitiş zamanı ve özet
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"✔ Tamamlandı | süre={duration:.1f}s")
    
    return 0


def handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.
    EventBridge payload: {"timeframe": "1h"}
    """
    start_time = datetime.now()
    timeframe = event.get("timeframe", "").strip()

    valid = {"15m", "1h", "4h", "1d", "all"}
    if timeframe not in valid:
        logger.error(f"Geçersiz timeframe: '{timeframe}'. Beklenen: {valid}")
        return {"status": "error", "message": f"Invalid timeframe: {timeframe}"}

    logger.info(f"▶ Lambda başlıyor | timeframe={timeframe}")

    try:
        init_indexes()
    except Exception as e:
        logger.error(f"MongoDB başlatma hatası: {e}")
        return {"status": "error", "message": str(e)}

    try:
        if timeframe == "all":
            from config import TIMEFRAMES
            stats = run_job_for_all_timeframes(TIMEFRAMES)
        else:
            check_signal_outcomes()          # açık sinyallerin TP/SL durumunu güncelle
            stats = run_job_for_timeframe(timeframe)
    except Exception as e:
        logger.error(f"İşlem hatası: {e}")
        return {"status": "error", "message": str(e)}

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"✔ Tamamlandı | süre={duration:.1f}s")
    return {"status": "ok", "timeframe": timeframe, "duration_seconds": round(duration, 1)}


if __name__ == "__main__":
    sys.exit(main())