using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    // BaseAddress: https://api.alternative.me/
    // Endpoint:    GET fng/
    public sealed class AlternativeMeFngClient : IFngClient
    {
        private readonly HttpClient _http;
        public AlternativeMeFngClient(HttpClient http) => _http = http;

        public async Task<MetricCard> GetAsync(CancellationToken ct)
        {
            using var doc = await _http.GetFromJsonAsync<JsonDocument>("fng/", ct);
            var data0 = doc!.RootElement.GetProperty("data")[0];

            var valueStr = data0.GetProperty("value").GetString()!;
            var value = decimal.Parse(valueStr);

            return new MetricCard
            {
                Key = "fng",
                Label = "Fear & Greed",
                Value = value, // 0–100
                Unit = "",
                UpdatedAt = DateTimeOffset.UtcNow
            };
        }
    }
}
