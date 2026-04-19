# CryptoBot - Kripto Teknik Analiz ve Ticaret Sinyali Platformu

Kripto para piyasalarında teknik analiz yaparak otomatik alım-satım sinyalleri üreten, üretilen sinyalleri görselleştiren ve yöneten kapsamlı bir platform.

## 📋 Proje Özeti

CryptoBot, Binance SPOT piyasasında teknik analiz göstergelerini kullanarak alım-satım sinyalleri üreten bir otomasyondur. Proje, üç ana bileşenden oluşmaktadır:

- **Backend API** (.NET 8 ile ASP.NET Core)
- **Analiz Botu** (Python ile Binance API entegrasyonu)
- **Web Arayüzü** (Angular 19 ile modern SPA)

---

## 🏗️ Proje Mimarisi

```
CryptoBot/
├── backend-service/          # .NET 8 ASP.NET Core API
│   ├── Controllers/          # API Endpoints
│   ├── Services/             # Business Logic
│   ├── Models/               # Veri Modelleri
│   ├── Properties/           # Launch Settings
│   └── bin/, obj/            # Build Output
├── bot-service/              # Python Analiz Botu
│   ├── main.py              # Ana giriş noktası
│   ├── config.py            # Konfigürasyon ayarları
│   ├── signals.py           # Sinyal üretme mantığı
│   ├── indicators.py        # Teknik analiz göstergeleri
│   ├── jobs.py              # Analiz işleri
│   ├── repository.py        # MongoDB operasyonları
│   ├── binance_client.py    # Binance API client
│   └── requirements.txt      # Python bağımlılıkları
├── frontend-service/         # Angular 19 Web Uygulaması
│   └── frontend/
│       ├── src/             # TypeScript/HTML kaynakları
│       ├── package.json     # Node.js bağımlılıkları
│       └── angular.json     # Angular konfigürasyonu
└── README.md
```

---

## 🔧 Teknik Stack

### Backend Service
- **Framework**: ASP.NET Core 8.0
- **Veritabanı**: MongoDB
- **İçerik Tipi**: RESTful API
- **İşletme Sistemi**: Cross-platform
- **Protokol**: HTTP/HTTPS

**Başlıca Bağımlılıklar**:
- MongoDB.Driver (C# MongoDB client)
- Microsoft.Extensions.Caching.Memory (Memory Caching)
- CORS Support (Angular uygulaması için)

### Bot Service
- **Dil**: Python 3.x
- **Pazar**: Binance SPOT
- **Veritabanı**: MongoDB
- **Komut Satırı**: argparse ile parametrize

**Başlıca Kütüphaneler**:
- `pymongo` (MongoDB işlemleri)
- `requests` (HTTP istekleri)
- `pandas` (Veri işleme)
- `numpy` (Sayısal hesaplamalar)
- `TA-Lib` (Teknik analiz göstergeleri)
- `python-dotenv` (Ortam değişkenleri)

### Frontend Service
- **Framework**: Angular 19
- **UI Framework**: Bootstrap 5
- **Dil**: TypeScript 5.7+
- **Build Tool**: Angular CLI 19
- **Dev Server**: ng serve

---

## 📊 Temel Özellikler

### 1. Teknik Analiz Göstergeleri

Bot aşağıdaki teknik analiz göstergelerini kullanarak sinyaller oluşturur:

| Gösterge | Parametre | Amaç |
|----------|-----------|------|
| **EMA** (Exponential Moving Average) | 20, 50, 200 | Trend tespiti |
| **RSI** (Relative Strength Index) | 14 | Aşırı alım/satım durumu |
| **ATR** (Average True Range) | 14 | Oynaklık ve stop-loss hesaplaması |
| **ADX** (Average Directional Index) | 14 (Strong Trend > 25) | Trend güçlülüğü |
| **MACD** | Fast:12, Slow:26, Signal:9 | Momentum ve crossover |
| **ROC** (Rate of Change) | 10 | Fiyat değişim hızı |

### 2. Sinyal Üretim

**Sinyal Kriterleri**:
- Çok zaman diliminde gösterge uyumsuzluğu analizi
- ATR tabanlı dinamik risk yönetimi
- Risk/Reward oranı hesaplaması
- Sinyal gücü puanlaması (0-100)

**Yönetilen Zaman Dilimleri**:
- `15m` (15 dakika) - Hızlı işlemler
- `1h` (1 saat) - Orta vadeli
- `4h` (4 saat) - Uzun vadeli
- `1d` (1 gün) - Çok uzun vadeli

### 3. Risk Yönetimi

Her timeframe için ATR tabanlı risk seviyeleri:

```python
TIMEFRAME_RISK_SETTINGS = {
    "15m": {"atr_sl": 1.5, "rr": 1.5},    # 1:1.5 risk/reward
    "1h":  {"atr_sl": 1.8, "rr": 1.8},    # 1:1.8 risk/reward
    "4h":  {"atr_sl": 2.0, "rr": 2.0},    # 1:2.0 risk/reward
    "1d":  {"atr_sl": 2.5, "rr": 2.0},    # 1:2.0 risk/reward
}
```

**Hesaplanan Seviyeler**:
- `stop_loss` - Stop-loss seviyesi (ATR tabanlı)
- `target_price` - Hedef fiyat (Risk/Reward oranı)
- `risk_reward` - Risk/Reward oranı
- `risk_amount` - Risk miktarı
- `reward_amount` - Beklenen kazanç

### 4. İzlenen Semboller

Binance SPOT piyasasında en çok işlem gören **200 sembol** izlenir.

---

## 🚀 Kurulum ve Çalışma

### Ön Koşullar

- .NET 8.0 SDK
- Python 3.8+
- Node.js 18+ ve npm
- MongoDB (yerel veya uzak)
- Binance API anahtarları (isteğe bağlı)
- Git

### 1. Backend Service Kurulumu

```bash
cd backend-service
dotnet restore
dotnet build
dotnet run
```

**Backend API** `http://localhost:5000` veya `https://localhost:5001` adresinde çalışır.

### 2. Bot Service Kurulumu

```bash
cd bot-service
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend Service Kurulumu

```bash
cd frontend-service/frontend
npm install
npm start
```

**Frontend** `http://localhost:4200` adresinde çalışır.

---

## 🔑 Ortam Değişkenleri

Bot service için `.env` dosyası oluşturun:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017

# Binance (İsteğe bağlı)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
SPOT_URL=https://api.binance.com

# MongoDB Veritabanı (varsayılan)
# DatabaseName=CryptoBot
# SignalsCollection=signals
```

**MongoDB Ayarları** (`appsettings.json`):
```json
"MongoDB": {
  "ConnectionString": "mongodb://localhost:27017",
  "DatabaseName": "CryptoBot",
  "SignalsCollection": "signals"
}
```

---

## 💻 Kullanım

### Bot Service Çalıştırma

Bot tek seferlik analiz yapar (sonsuz döngü yok). Cron veya Task Scheduler ile zamanlanması gerekir.

```bash
# Tüm zaman dilimlerini analiz et
python main.py --timeframe all

# Sadece 15 dakikalık zaman dilimi
python main.py --timeframe 15m

# Sadece 1 saatlik zaman dilimi
python main.py --timeframe 1h

# Sadece 4 saatlik zaman dilimi
python main.py --timeframe 4h

# Sadece 1 günlük zaman dilimi
python main.py --timeframe 1d
```

### Backend API Endpoints

#### Tüm Sinyalleri Getir
```
GET /api/signals
```

#### En İyi 3 Sinyali Getir
```
GET /api/signals/top
```

#### Filtrelenmiş Sinyalleri Getir (Pagination ile)
```
GET /api/signals/filtered?timeframe=15m&symbol=BTCUSDT&direction=BUY&minStrength=70&page=1&pageSize=25
```

**Query Parametreleri**:
- `timeframe` (gerekli): `15m`, `1h`, `4h`, `1d`
- `symbol` (isteğe bağlı): Sembol adı (örn: BTCUSDT)
- `direction` (isteğe bağlı): `BUY` veya `SELL`
- `minStrength` (isteğe bağlı): 0-100 arası minimum sinyal gücü
- `page` (varsayılan: 1): Sayfa numarası
- `pageSize` (varsayılan: 25): Sayfa başına öğe sayısı (max: 1000)

---

## 📡 Dış API Entegrasyonları

Backend, piyasa verileri için aşağıdaki external API'lerle entegre edilmiştir:

| API | Amaç | Base URL |
|-----|------|----------|
| **Alternative.me Fear & Greed** | Piyasa duygusunun tespiti | `https://api.alternative.me/` |
| **CoinGecko Global Data** | Pazar hacmi ve dominans | `https://api.coingecko.com/api/v3/` |
| **CoinGecko Altseason** | Alt coin sezonunun tespiti | `https://api.coingecko.com/api/v3/` |
| **CoinGecko Average RSI** | Ortalama RSI değerleri | `https://api.coingecko.com/api/v3/` |

---

## 🗄️ MongoDB Koleksiyonu

### Signals Koleksiyonu Şeması

```json
{
  "_id": ObjectId,
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "direction": "BUY",
  "strength": 85,
  "openedAt": ISODate("2026-04-19T10:30:00Z"),
  "entryPrice": 65000.50,
  "stopLoss": 64500.25,
  "targetPrice": 67000.75,
  "riskReward": 2.0,
  "indicators": {
    "ema20": 65100,
    "ema50": 65200,
    "rsi": 68,
    "atr": 250,
    "adx": 28,
    "macd": "POSITIVE"
  }
}
```

---

## 🔄 İş Akışı

```
┌─────────────────────┐
│  Bot Service        │
│  (Python)           │
├─────────────────────┤
│ 1. Binance Verileri │
│    İndir            │
│ 2. Teknik Analiz    │
│    Yap              │
│ 3. Sinyal Oluştur   │
│ 4. MongoDB'ye Kaydet│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  MongoDB            │
│  (Signals)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Backend Service    │
│  (.NET)             │
├─────────────────────┤
│ API Endpoints       │
│ CORS Enabled        │
│ Filtering/Sorting   │
│ Pagination          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Frontend           │
│  (Angular)          │
├─────────────────────┤
│ Sinyal Görünümü     │
│ Filtreleme          │
│ Detay İnceleme      │
└─────────────────────┘
```

---

## 📈 Sinyal Gücü Hesaplaması

Sinyal gücü (0-100) aşağıdaki faktörlere göre hesaplanır:

- **EMA Alignment**: Tüm EMA'lar aynı yönde mü?
- **RSI Durumu**: Aşırı alım/satım bölgesinde mi?
- **Trend Gücü**: ADX değeri (25+ güçlü trend)
- **Momentum**: MACD ve ROC uyumsuzluğu
- **Volatilite**: ATR normalleştirilmiş değeri

Daha yüksek puan = Daha güvenilir sinyal

---

## 🛠️ Geliştirme Notları

### Backend
- ASP.NET Core 8 MVC/API pattern
- Dependency Injection (DI) konfigürasyonu
- Memory Cache desteği
- CORS policy konfigürasyonu

### Bot
- Komut satırı argümanları ile parametrize
- Logging sistemi
- MongoDB indexleme
- TA-Lib teknik analiz

### Frontend
- Angular Standalone Components
- Proxy configuration (API çağrıları için)
- Bootstrap responsive design
- TypeScript strict mode

---

## 🐛 Troubleshooting

| Problem | Çözüm |
|---------|-------|
| MongoDB bağlantı hatası | MONGODB_URI ortam değişkenini kontrol edin |
| API CORS hatası | Backend'de CORS policy konfigürasyonunu doğrulayın |
| Bot çalışmıyor | Python bağımlılıklarını kontrol edin: `pip install -r requirements.txt` |
| Frontend API'yi çağıramıyor | proxy.conf.json konfigürasyonunu ve backend URL'sini kontrol edin |

---

## 📞 Katkıda Bulunma

Projede hata bulduysanız veya öneriniz varsa lütfen issue açınız veya pull request gönderin.

---

## 📜 Lisans

Bu proje özel amaçlar için geliştirilmiştir. Kullanım şartları için proje sahibine danışınız.

---

## ⚠️ Disclaimer

Bu tool, **eğitim ve araştırma amaçlıdır**. Finansal tavsiyeleri temsil etmez. Kripto para ticareti yüksek risklidir. Kendi risk yönetiminizi yapınız ve yatırım kararlarınızı uzmanlarla danışarak alınız.