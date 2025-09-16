using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    // BaseAddress: https://api.coingecko.com/api/v3/
    // Endpoint:    GET global
    public sealed class CoinGeckoGlobalClient : IGlobalMarketClient
    {
        private readonly HttpClient _http;
        public CoinGeckoGlobalClient(HttpClient http) => _http = http;

        public async Task<MetricCard> GetGlobalMarketCapAsync(CancellationToken ct)
        {
            using var doc = await _http.GetFromJsonAsync<JsonDocument>("global", ct);
            var root = doc!.RootElement.GetProperty("data");
            var totalUsd = root.GetProperty("total_market_cap").GetProperty("usd").GetDecimal();
            var chg24 = root.GetProperty("market_cap_change_percentage_24h_usd").GetDecimal();

            return new MetricCard
            {
                Key = "marketCap",
                Label = "Global Market Cap",
                Value = totalUsd,          // USD toplam piyasa değeri
                Unit  = "USD",
                Change24h = chg24,         // yüzde (örn. -1.23)
                UpdatedAt = DateTimeOffset.UtcNow
            };
        }
    }
}
