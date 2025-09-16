using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    public sealed class CoingeckoAverageRsiClient : IAverageRsiClient
    {
        private readonly HttpClient _http;

        // Basit filtre (BTC, stable/pegged, wrapped)
        private static readonly HashSet<string> Excludes = new(StringComparer.OrdinalIgnoreCase)
        {
            "bitcoin","btc","wbtc","wrapped-bitcoin",
            "tether","usdt","usd-coin","usdc","binance-usd","busd","true-usd","tusd",
            "dai","frax","usdd","lusd","usde","susd",
            "steth","rocket-pool-eth","reth","cbeth","weth","wrapped-ether",
            "pyusd","fdusd","gusd","eurs","eurt"
        };

        // ENV ile ayarlanabilir
        private static int TAKE => TryGetInt("AVGRSI_TAKE", 10);            // kaç coin? (prod: 10)
        private static int DELAY_MS => TryGetInt("AVGRSI_DELAY_MS", 800);   // her çağrı arası bekleme
        private static int MAX_RETRY => TryGetInt("AVGRSI_MAX_RETRY", 5);   // 429 max retry
        private const int RSI_PERIOD = 14;
        // CoinGecko OHLC: /coins/{id}/ohlc?vs_currency=usd&days=...  (1,7,14,30,90,180,365,max)
        private const int DAYS = 90; // RSI için yeterli

        public CoingeckoAverageRsiClient(HttpClient http) => _http = http;

        private async Task<MetricCard> BuildFallbackRsiAsync(CancellationToken ct)
        {
            var now = DateTimeOffset.UtcNow;
            var ids = new[] { "bitcoin", "ethereum" };
            var rsis = new List<decimal>();

            foreach (var id in ids)
            {
                using var doc = await GetJsonWithRetryAsync(
                    $"coins/{id}/ohlc?vs_currency=usd&days={DAYS}", ct);

                var closes = doc.RootElement.EnumerateArray()
                    .Select(arr => arr[4].GetDecimal())
                    .ToList();

                var rsi = ComputeRsi(closes, RSI_PERIOD);
                if (rsi.HasValue) rsis.Add(rsi.Value);
            }

            var avg = rsis.Count > 0 ? Math.Round(rsis.Average(), 2) : 0m;

            return new MetricCard
            {
                Key = "avgRsi",
                Label = "Average Crypto RSI (BTC+ETH, 14D approx)",
                Value = avg,
                Unit = "",
                Change24h = null,
                UpdatedAt = now
            };
        }


        public async Task<MetricCard> GetAverageRsiAsync(CancellationToken ct)
        {
            try
            {
                // 1) Top N coin (BTC/stable hariç)
                var coinIds = await GetTopAltcoinsAsync(ct, TAKE);

                // 2) Her coin için OHLC al, kapanış serisinden RSI(14) hesapla
                var rsis = new List<decimal>();
                var idx = 0;
                foreach (var id in coinIds)
                {
                    if (idx++ > 0) await Task.Delay(DELAY_MS, ct);

                    using var doc = await GetJsonWithRetryAsync(
                        $"coins/{id}/ohlc?vs_currency=usd&days={DAYS}", ct);

                    var closes = doc.RootElement.EnumerateArray()
                        .Select(arr => arr[4].GetDecimal()) // [t, open, high, low, close]
                        .ToList();

                    var rsi = ComputeRsi(closes, RSI_PERIOD);
                    if (rsi.HasValue) rsis.Add(rsi.Value);
                }

                if (rsis.Count == 0)
                    throw new InvalidOperationException("RSI hesaplamak için yeterli veri yok.");

                var avg = Math.Round(rsis.Average(), 2);

                return new MetricCard
                {
                    Key = "avgRsi",
                    Label = $"Average Crypto RSI (Top {rsis.Count}, 14D)",
                    Value = avg,
                    Unit = "",
                    Change24h = null,
                    UpdatedAt = DateTimeOffset.UtcNow
                };
            }
            catch (HttpRequestException ex)
            {
                // Bazı .NET sürümlerinde ex.StatusCode null olabiliyor → içerde kontrol et
                if (ex.StatusCode == HttpStatusCode.TooManyRequests)
                {
                    // Fallback: BTC+ETH ile hızlı approx
                    return await BuildFallbackRsiAsync(ct);
                }
                // Diğer network hataları: aynen yeniden fırlat (500 görürsün)
                throw;
            }
        }

        // ----- yardımcılar -----

        private async Task<List<string>> GetTopAltcoinsAsync(CancellationToken ct, int need)
        {
            var ids = new List<string>();
            int page = 1;
            while (ids.Count < need && page <= 5)
            {
                using var doc = await GetJsonWithRetryAsync(
                    $"coins/markets?vs_currency=usd&order=market_cap_desc&per_page=60&page={page}&sparkline=false", ct);

                var batch = doc.RootElement.EnumerateArray()
                    .Select(x => new
                    {
                        id = x.GetProperty("id").GetString()!,
                        symbol = x.GetProperty("symbol").GetString()!,
                        name = x.GetProperty("name").GetString()!
                    })
                    .Where(x => !Excludes.Contains(x.id) && !Excludes.Contains(x.symbol) && !Excludes.Contains(x.name))
                    .Select(x => x.id)
                    .ToList();

                foreach (var id in batch)
                {
                    if (!ids.Contains(id)) ids.Add(id);
                    if (ids.Count >= need) break;
                }

                if (batch.Count == 0) break;
                page++;
            }

            if (ids.Count < Math.Min(need, 5))
                throw new InvalidOperationException("Yeterli altcoin bulunamadı.");

            return ids.Take(need).ToList();
        }

        private async Task<JsonDocument> GetJsonWithRetryAsync(string url, CancellationToken ct)
        {
            var attempt = 0;
            while (true)
            {
                attempt++;
                using var resp = await _http.GetAsync(url, ct);
                if (resp.StatusCode == (HttpStatusCode)429)
                {
                    var retryAfter = resp.Headers.RetryAfter?.Delta
                                     ?? TimeSpan.FromSeconds(Math.Min(10, 2 * attempt));
                    await Task.Delay(retryAfter, ct);
                    if (attempt < MAX_RETRY) continue;

                    throw new HttpRequestException("Too Many Requests (429)", null, resp.StatusCode);
                }

                resp.EnsureSuccessStatusCode();
                await using var stream = await resp.Content.ReadAsStreamAsync(ct);
                return await JsonDocument.ParseAsync(stream, cancellationToken: ct);
            }
        }

        // Wilder's RSI (close[]; period) — DOĞRU SÜZDÜRME
        private static decimal? ComputeRsi(IReadOnlyList<decimal> closes, int period)
        {
            if (closes == null || closes.Count <= period) return null;

            // 1) İlk 14 farklardan ilk ortalamalar
            decimal gain = 0, loss = 0;
            for (int i = 1; i <= period; i++)
            {
                var diff = closes[i] - closes[i - 1];
                if (diff > 0) gain += diff;
                else loss -= diff; // negatif farkın mutlağı
            }
            decimal avgGain = gain / period;
            decimal avgLoss = loss / period;

            // 2) Kalan mumlarda Wilder smoothing
            for (int i = period + 1; i < closes.Count; i++)
            {
                var diff = closes[i] - closes[i - 1];
                var up = diff > 0 ? diff : 0m;
                var down = diff < 0 ? -diff : 0m;

                // Wilder: (öncekilerin toplamı * (period-1) + yeni) / period
                avgGain = ((avgGain * (period - 1)) + up) / period;
                avgLoss = ((avgLoss * (period - 1)) + down) / period;
            }

            if (avgGain == 0 && avgLoss == 0) return 50m;
            if (avgLoss == 0) return 100m;

            var rs = avgGain / avgLoss;
            var rsi = 100m - (100m / (1 + rs));
            return Math.Round(rsi, 2);
        }

        private static int TryGetInt(string key, int dflt)
            => int.TryParse(Environment.GetEnvironmentVariable(key), out var v) ? v : dflt;
    }
}
