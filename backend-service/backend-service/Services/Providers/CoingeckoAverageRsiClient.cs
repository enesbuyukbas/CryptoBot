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
    /// BTC + ETH OHLC verisinden Wilder RSI(14) ortalamasini hesaplar.
    /// Toplam API cagrisi: 2 (rate-limit dostu).
    /// </summary>
    public sealed class CoingeckoAverageRsiClient : IAverageRsiClient
    {
        private readonly HttpClient _http;

        private static int MAX_RETRY => TryGetInt("AVGRSI_MAX_RETRY", 3);
        private const int RSI_PERIOD = 14;
        private const int DAYS = 90;

        public CoingeckoAverageRsiClient(HttpClient http) => _http = http;

        public async Task<MetricCard> GetAverageRsiAsync(CancellationToken ct)
        {
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

            if (rsis.Count == 0)
                throw new InvalidOperationException("RSI hesaplamak icin yeterli veri yok.");

            var avg = Math.Round(rsis.Average(), 2);

            return new MetricCard
            {
                Key = "avgRsi",
                Label = "Average Crypto RSI (BTC+ETH, 14D)",
                Value = avg,
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

        private static decimal? ComputeRsi(IReadOnlyList<decimal> closes, int period)
        {
            if (closes == null || closes.Count <= period) return null;

            decimal gain = 0, loss = 0;
            for (int i = 1; i <= period; i++)
            {
                var diff = closes[i] - closes[i - 1];
                if (diff > 0) gain += diff;
                else loss -= diff;
            }
            decimal avgGain = gain / period;
            decimal avgLoss = loss / period;

            for (int i = period + 1; i < closes.Count; i++)
            {
                var diff = closes[i] - closes[i - 1];
                var up = diff > 0 ? diff : 0m;
                var down = diff < 0 ? -diff : 0m;

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
