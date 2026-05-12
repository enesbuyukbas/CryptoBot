import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from config import MONGODB_URI, SIGNAL_TTL_SECONDS, SIGNAL_MAX_AGE_SECONDS, OPEN_SIGNAL_RETENTION_SECONDS

logger = logging.getLogger(__name__)

# Thread-local storage for MongoDB connections
thread_local = threading.local()


def get_db():
    """
    Thread-safe MongoDB bağlantısı sağlar.
    Her thread için ayrı bir connection döndürür.
    
    Returns:
        MongoDB database instance
    """
    if not hasattr(thread_local, "db"):
        try:
            client = MongoClient(
                MONGODB_URI,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True,
                retryReads=True
            )
            thread_local.db = client["cryptoDB"]
            logger.info("✅ MongoDB bağlantısı kuruldu")
        except Exception as e:
            logger.error(f"❌ MongoDB bağlantı hatası: {e}")
            raise
    
    # Bağlantı kontrolü (ping)
    try:
        thread_local.db.client.admin.command('ping')
    except ConnectionFailure:
        logger.warning("⚠️ MongoDB bağlantısı koptu, yeniden bağlanılıyor...")
        client = MongoClient(
            MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            retryReads=True
        )
        thread_local.db = client["cryptoDB"]
    
    return thread_local.db


def init_indexes():
    """
    MongoDB koleksiyonlarını ve index'leri oluşturur.
    
    Koleksiyonlar:
    - signals: Sinyal verilerini saklar (TTL: 30 gün)
    """
    db = get_db()
    
    try:
        # ================== SIGNALS KOLEKSİYONU ==================
        if "signals" not in db.list_collection_names():
            db.create_collection("signals")
            logger.info("✅ 'signals' koleksiyonu oluşturuldu")
        
        # Index 1: symbol + timeframe + created_at (unique query için)
        db.signals.create_index(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("created_at", DESCENDING)],
            name="idx_symbol_timeframe_created"
        )
        
        # Index 2: created_at için TTL index (30 gün)
        db.signals.create_index(
            [("created_at", ASCENDING)],
            name="idx_ttl_created_at",
            expireAfterSeconds=SIGNAL_TTL_SECONDS
        )
        
        # Index 2b: expires_at için TTL index (expireAfterSeconds=0 — tarihe göre siler)
        db.signals.create_index(
            [("expires_at", ASCENDING)],
            name="idx_ttl_expires_at",
            expireAfterSeconds=0
        )
        
        # Index 3: Güce göre sıralama için
        db.signals.create_index(
            [("strength", DESCENDING)],
            name="idx_strength"
        )
        
        # Index 4: symbol + timeframe + direction (son sinyal sorgusu için)
        db.signals.create_index(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("direction", ASCENDING)],
            name="idx_symbol_timeframe_direction"
        )
        
        logger.info("✅ 'signals' koleksiyonu index'leri oluşturuldu")
        
    except Exception as e:
        logger.error(f"❌ Index oluşturma hatası: {e}")
        raise


def save_signal_if_new(signal: Dict) -> bool:
    """
    Sinyali MongoDB'ye kaydeder.
    Eğer aynı symbol + timeframe için son sinyal aynı direction'a sahipse:
        - Yeni kayıt açmaz, mevcut kaydı günceller
    Eğer direction değiştiyse:
        - Yeni kayıt ekler
    
    Args:
        signal: Sinyal dictionary
        
    Returns:
        True: Yeni kayıt eklendi veya güncellendi
        False: İşlem başarısız
        
    Signal Schema:
        {
            "_id": ObjectId,
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "direction": "BUY",
            "strength": 85,
            "reason": ["TREND_UP", "MOMENTUM_POSITIVE"],
            "price": 43250.5,          - güncel fiyat (her güncellemede değişir)
            "first_price": 43000.0,    - sinyalin ilk açıldığı fiyat (hiç değişmez)
            "opened_at": datetime,     - güncel mumun kapanış zamanı (UTC)
            "first_opened_at": datetime - sinyalin ilk açıldığı mumun kapanış zamanı (UTC, hiç değişmez)
            "created_at": datetime,    - DB'ye ilk yazıldığı an (UTC)
            "updated_at": datetime     - son güncellenme (UTC)
        }
    """
    if not signal:
        logger.warning("⚠️ Boş sinyal gönderildi")
        return False
    
    db = get_db()
    
    try:
        symbol = signal.get("symbol")
        timeframe = signal.get("timeframe")
        direction = signal.get("direction")
        
        if not symbol or not timeframe or not direction:
            logger.error(f"❌ Eksik sinyal alanları: {signal}")
            return False
        
        # ================== SON SİNYALİ BUL ==================
        last_signal = db.signals.find_one(
            {
                "symbol": symbol,
                "timeframe": timeframe
            },
            sort=[("created_at", DESCENDING)]
        )
        
        current_time = datetime.now(timezone.utc)
        
        # ================== AYNI DIRECTION İSE GÜNCELLE ==================
        if last_signal and last_signal.get("direction") == direction:
            # Kapatılmış sinyal ise (tp_hit veya sl_hit set edilmişse) yeni kayıt aç
            if last_signal.get("tp_hit") is not None or last_signal.get("sl_hit") is not None:
                logger.info(
                    f"🔁 {symbol} - {timeframe} | {direction} sinyali zaten kapandı "
                    f"(tp_hit={last_signal.get('tp_hit')}, sl_hit={last_signal.get('sl_hit')}) → yeni kayıt açılıyor"
                )
                last_signal = None  # aşağıdaki else bloğunu tetikler

        if last_signal and last_signal.get("direction") == direction:
            # Sinyal yaşını kontrol et
            max_age = SIGNAL_MAX_AGE_SECONDS.get(timeframe, 86400)
            signal_age = (current_time - last_signal["created_at"].replace(tzinfo=timezone.utc)).total_seconds()

            if signal_age > max_age:
                # Sinyal çok eski — aynı yönde olsa bile yeni kayıt aç
                logger.info(
                    f"⏰ {symbol} - {timeframe} | {direction} sinyali {signal_age/3600:.1f} saat önce açıldı, "
                    f"max_age={max_age/3600:.0f}h aşıldı → yeni kayıt açılıyor"
                )
                last_signal = None  # aşağıdaki else bloğunu tetikler

        if last_signal and last_signal.get("direction") == direction:
            # Mevcut kaydı güncelle
            # NOT: first_price ve first_opened_at HİÇBİR ZAMAN güncellenmez —
            # ilk sinyalin fiyatı ve zamanı korunur
            open_retention = OPEN_SIGNAL_RETENTION_SECONDS.get(timeframe, 30 * 86400)
            update_result = db.signals.update_one(
                {"_id": last_signal["_id"]},
                {
                    "$set": {
                        "strength": signal.get("strength"),
                        "price": signal.get("price"),
                        "reason": signal.get("reason"),
                        "opened_at": signal.get("opened_at"),
                        # stop_loss, target_price, risk_reward, risk_amount, reward_amount, atr
                        # ilk açılıştaki değerler korunur — fiyat değişse bile üzerine yazılmaz
                        "expires_at": current_time + timedelta(seconds=open_retention),
                        "updated_at": current_time
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"🔄 {symbol} - {timeframe} | {direction} sinyali güncellendi (Güç: {signal.get('strength')}%)")
                return True
            else:
                logger.debug(f"ℹ️ {symbol} - {timeframe} | {direction} değişiklik yok")
                return True
        
        # ================== FARKLI DIRECTION İSE YENİ KAYIT ==================
        else:
            open_retention = OPEN_SIGNAL_RETENTION_SECONDS.get(timeframe, 30 * 86400)
            signal_to_save = {
                "symbol": symbol,
                "timeframe": timeframe,
                "direction": direction,
                "strength": signal.get("strength"),
                "reason": signal.get("reason", []),
                "price": signal.get("price"),
                "stop_loss": signal.get("stop_loss"),
                "target_price": signal.get("target_price"),
                "risk_reward": signal.get("risk_reward"),
                "risk_amount": signal.get("risk_amount"),
                "reward_amount": signal.get("reward_amount"),
                "atr": signal.get("atr"),
                "opened_at": signal.get("opened_at", current_time),
                # İlk sinyal anındaki fiyat ve zaman — hiçbir zaman üzerine yazılmaz
                "first_price": signal.get("price"),
                "first_opened_at": signal.get("opened_at", current_time),
                # Sonuç takibi — her run'da check edilir, TP/SL geçildiyse set edilir
                "tp_hit": None,
                "sl_hit": None,
                "outcome_price": None,
                "outcome_checked_at": None,
                "expires_at": current_time + timedelta(seconds=open_retention),
                "created_at": current_time,
                "updated_at": current_time
            }
            
            result = db.signals.insert_one(signal_to_save)
            
            if result.inserted_id:
                logger.info(f"✅ {symbol} - {timeframe} | {direction} sinyali eklendi (Güç: {signal.get('strength')}%)")
                return True
            else:
                logger.error(f"❌ {symbol} - {timeframe} sinyal eklenemedi")
                return False
                
    except DuplicateKeyError:
        logger.warning(f"⚠️ {signal.get('symbol')} - {signal.get('timeframe')} zaten var (duplicate key)")
        return False
        
    except Exception as e:
        logger.error(f"❌ Sinyal kaydetme hatası ({signal.get('symbol')} - {signal.get('timeframe')}): {e}")
        import traceback
        traceback.print_exc()
        return False


def get_latest_signals(limit: int = 10, min_strength: int = 0) -> list:
    """
    En son sinyalleri getirir.
    
    Args:
        limit: Maksimum sinyal sayısı
        min_strength: Minimum güç seviyesi
        
    Returns:
        Sinyal listesi
    """
    db = get_db()
    
    try:
        query = {}
        if min_strength > 0:
            query["strength"] = {"$gte": min_strength}
        
        signals = list(
            db.signals.find(query)
            .sort([("created_at", DESCENDING)])
            .limit(limit)
        )
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ Sinyal listesi getirme hatası: {e}")
        return []


def get_top_signals_by_strength(limit: int = 10) -> list:
    """
    En güçlü sinyalleri getirir.
    
    Args:
        limit: Maksimum sinyal sayısı
        
    Returns:
        Güce göre sıralanmış sinyal listesi
    """
    db = get_db()
    
    try:
        signals = list(
            db.signals.find()
            .sort([("strength", DESCENDING), ("created_at", DESCENDING)])
            .limit(limit)
        )
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ Top sinyal listesi getirme hatası: {e}")
        return []