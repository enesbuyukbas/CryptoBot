using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    /// <summary>
    /// Top 50 altcoin'in BTC karsisindaki 30 gunluk performansini TEK CoinGecko cagriyla hesaplar.
    /// coins/markets endpoint'i price_change_percentage=30d parametresiyle kullanilir.
    /// Toplam API cagrisi: 1 (rate-limit dostu).
    /// </summary>
    public sealed class CoingeckoAltseasonClient : IAltseasonClient
    {
        private readonly HttpClient _http;

        private static readonly HashSet<string> Excludes = new(StringComparer.OrdinalIgnoreCase)
        {
            "bitcoin","btc","wbtc","wrapped-bitcoin",
            "tether","usdt","usd-coin","usdc","binance-usd","busd","true-usd","tusd",
            "dai","frax","usdd","lusd","usde","susd",
            "steth","rocket-pool-eth","reth","cbeth","weth","wrapped-ether",
            "pyusd","fdusd","gusd","eurs","eurt"
        };

        private static int TAKE => TryGetInt("ALTSEASON_TAKE", 50);
        private static int MAX_RETRY => TryGetInt("ALTSEASON_MAX_RETRY", 3);

        public CoingeckoAltseasonClient(HttpClient http) => _http = http;

        public async Task<MetricCard> GetAltseasonAsync(CancellationToken ct)
        {
            // Tek cagrida top 100 coin'i BTC bazinda al, 30 gunluk degisim yuzdesiyle
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
                .Take(TAKE)
                .Where(x => x.pct30.HasValue)
                .ToList();

            var total = coins.Count;
            var passed = coins.Count(x => x.pct30!.Value > 0);

            if (total == 0)
                throw new InvalidOperationException("Altseason hesaplamasi icin yeterli veri yok.");

            var score = Math.Round(passed * 100.0m / total, 2);

            return new MetricCard
            {
                Key = "altseason",
                Label = "Altcoin Season Index",
                Value = score,
                Unit = "",
                Change24h = null,
                UpdatedAt = DateTimeOffset.UtcNow
            };
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
                    if (attempt >= MAX_RETRY)
                        throw new HttpRequestException("Too Many Requests (429)", null, resp.StatusCode);

                    var retryAfter = resp.Headers.RetryAfter?.Delta
                                     ?? TimeSpan.FromSeconds(Math.Min(30, 3 * attempt));
                    await Task.Delay(retryAfter, ct);
                    continue;
                }

                resp.EnsureSuccessStatusCode();

                await using var stream = await resp.Content.ReadAsStreamAsync(ct);
                return await JsonDocument.ParseAsync(stream, cancellationToken: ct);
            }
        }

        private static int TryGetInt(string key, int dflt)
            => int.TryParse(Environment.GetEnvironmentVariable(key), out var v) ? v : dflt;
    }
}
