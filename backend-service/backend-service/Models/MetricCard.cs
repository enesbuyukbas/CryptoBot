using System.Text.Json.Serialization;

namespace backend_service.Models
{
    public sealed class MetricCard
    {
        [JsonPropertyName("key")]
        public required string Key { get; init; }

        [JsonPropertyName("label")]
        public required string Label { get; init; }

        [JsonPropertyName("value")]
        public required decimal Value { get; init; }

        [JsonPropertyName("unit")]
        public string? Unit { get; init; }

        [JsonPropertyName("change24h")]
        public decimal? Change24h { get; init; }

        [JsonPropertyName("updatedAt")]
        public DateTimeOffset UpdatedAt { get; init; }
    }
}
