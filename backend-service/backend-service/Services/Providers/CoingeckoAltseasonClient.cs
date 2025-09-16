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
    public sealed class CoingeckoAltseasonClient : IAltseasonClient
    {
        private readonly HttpClient _http;

        // BTC, stable ve wrapped/pegged filtreleri
        private static readonly HashSet<string> Excludes = new(StringComparer.OrdinalIgnoreCase)
        {
            "bitcoin","btc","wbtc","wrapped-bitcoin",
            "tether","usdt","usd-coin","usdc","binance-usd","busd","true-usd","tusd",
            "dai","frax","usdd","lusd","usde","susd",
            "steth","rocket-pool-eth","reth","cbeth","weth","wrapped-ether",
            "pyusd","fdusd","gusd","eurs","eurt"
        };

        // ENV ile dev/prod ayarlanabilir
        private static int TAKE => TryGetInt("ALTSEASON_TAKE", 50);               // Top kaç altcoin? (prod: 50)
        private static int DELAY_MS => TryGetInt("ALTSEASON_DELAY_MS", 1200);     // Her coin çağrısı arası bekleme (ms)
        private static int MAX_RETRY => TryGetInt("ALTSEASON_MAX_RETRY", 5);      // 429 için max tekrar

        public CoingeckoAltseasonClient(HttpClient http) => _http = http;

        public async Task<MetricCard> GetAltseasonAsync(CancellationToken ct)
        {
            try
            {
                // 1) Top X altcoin’i topla (BTC/stable/pegged hariç) — sayfalı
                var coins = await GetTopAltcoinsAsync(ct, TAKE);

                var passed = 0;
                var total  = 0;

                // 2) Her coin için 90 günlük BTC karşısı performans
                foreach (var c in coins)
                {
                    if (total > 0)
                        await Task.Delay(DELAY_MS, ct); // nazik gecikme (rate-limit’e takılmamak için)

                    using var doc = await GetJsonWithRetryAsync(
                        $"coins/{c}/market_chart?vs_currency=btc&days=90&interval=daily", ct);

                    var prices = doc.RootElement.GetProperty("prices").EnumerateArray()
                        .Select(p => p[1].GetDecimal()).ToList();

                    if (prices.Count >= 2)
                    {
                        var first = prices.First();
                        var last  = prices.Last();
                        if (first > 0 && (last / first) > 1.0m)
                            passed++;
                        total++;
                    }
                }

                if (total == 0)
                    throw new InvalidOperationException("Altseason hesaplaması için yeterli veri yok.");

                var score = Math.Round(passed * 100.0m / total, 2);

                return new MetricCard
                {
                    Key = "altseason",
                    Label = "Altcoin Season Index",
                    Value = (decimal)score,
                    Unit = "",
                    Change24h = null,
                    UpdatedAt = DateTimeOffset.UtcNow
                };
            }
            catch (HttpRequestException ex) when ((ex.StatusCode ?? 0) == HttpStatusCode.TooManyRequests)
            {
                // 3) Fallback: tek çağrıda yaklaşık 30 günlük skor (markets endpoint)
                var (score30d, updatedAt) = await ComputeApprox30dAsync(ct);

                return new MetricCard
                {
                    Key = "altseason",
                    Label = "Altcoin Season Index (approx 30d)",
                    Value = (decimal)score30d,
                    Unit = "",
                    Change24h = null,
                    UpdatedAt = updatedAt
                };
            }
        }

        // Top altcoinleri getir (BTC/stable dışı) — sayfa sayfa topla
        private async Task<List<string>> GetTopAltcoinsAsync(CancellationToken ct, int need)
        {
            var ids = new List<string>();
            int page = 1;

            while (ids.Count < need && page <= 5) // güvenlik: 5 sayfa (5*60=300 coin)
            {
                using var marketsDoc = await GetJsonWithRetryAsync(
                    $"coins/markets?vs_currency=usd&order=market_cap_desc&per_page=60&page={page}&sparkline=false", ct);

                var batch = marketsDoc.RootElement.EnumerateArray()
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
                    if (!ids.Contains(id))
                        ids.Add(id);
                    if (ids.Count >= need) break;
                }

                if (batch.Count == 0) break; // sayfa boşsa dur
                page++;
            }

            if (ids.Count < Math.Min(need, 20)) // en az 20 bulunmalı
                throw new InvalidOperationException("Yeterli altcoin bulunamadı.");

            // Tam olarak 'need' kadar kes
            return ids.Take(need).ToList();
        }

        // 429 için retry/backoff’lu JSON çağrısı (Retry-After destekli)
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

        // Fallback: tek çağrıda yaklaşık 30g sonuç (vs_currency=btc + price_change_percentage=30d)
        private async Task<(decimal score, DateTimeOffset at)> ComputeApprox30dAsync(CancellationToken ct)
        {
            using var doc = await GetJsonWithRetryAsync(
                "coins/markets?vs_currency=btc&order=market_cap_desc&per_page=100&page=1"
                + "&sparkline=false&price_change_percentage=30d", ct);

            var coins = doc.RootElement.EnumerateArray()
                .Select(x => new
                {
                    id = x.GetProperty("id").GetString()!,
                    symbol = x.GetProperty("symbol").GetString()!,
                    name = x.GetProperty("name").GetString()!,
                    pct30 = x.TryGetProperty("price_change_percentage_30d_in_currency", out var p)
                        ? (decimal?)p.GetDecimal() : null
                })
                .Where(x => !Excludes.Contains(x.id) && !Excludes.Contains(x.symbol) && !Excludes.Contains(x.name))
                .Take(TAKE) // aynı TAKE ile tutarlı ol
                .Where(x => x.pct30.HasValue)
                .ToList();

            var total = coins.Count;
            var passed = coins.Count(x => x.pct30!.Value > 0);

            var score = total == 0 ? 0m : Math.Round(passed * 100.0m / total, 2);
            return (score, DateTimeOffset.UtcNow);
        }

        private static int TryGetInt(string key, int dflt)
            => int.TryParse(Environment.GetEnvironmentVariable(key), out var v) ? v : dflt;
    }
}
