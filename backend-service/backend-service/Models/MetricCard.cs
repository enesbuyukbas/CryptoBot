namespace backend_service.Models
{
    public sealed class MetricCard
    {
        public required string Key { get; init; }      // "fng", "marketCap", "altseason", "avgRsi"
        public required string Label { get; init; }    // "Fear & Greed" vs.
        public required decimal Value { get; init; }   // sayısal değer
        public string? Unit { get; init; }             // "", "%", "USD"
        public decimal? Change24h { get; init; }       // opsiyonel
        public DateTimeOffset UpdatedAt { get; init; } // UTC
    }
}
