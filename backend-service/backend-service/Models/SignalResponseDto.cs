using System.Text.Json.Serialization;

namespace backend_service.Models
{
    public class SignalResponseDto
    {
        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = default!;

        [JsonPropertyName("timeframe")]
        public string Timeframe { get; set; } = default!;

        [JsonPropertyName("direction")]
        public string Direction { get; set; } = default!;

        [JsonPropertyName("strength")]
        public int Strength { get; set; }

        [JsonPropertyName("reason")]
        public List<string> Reason { get; set; } = new();

        [JsonPropertyName("price")]
        public double Price { get; set; }

        [JsonPropertyName("stopLoss")]
        public double StopLoss { get; set; }

        [JsonPropertyName("targetPrice")]
        public double TargetPrice { get; set; }

        [JsonPropertyName("riskReward")]
        public double RiskReward { get; set; }

        [JsonPropertyName("riskAmount")]
        public double RiskAmount { get; set; }

        [JsonPropertyName("rewardAmount")]
        public double RewardAmount { get; set; }

        [JsonPropertyName("atr")]
        public double Atr { get; set; }

        [JsonPropertyName("firstPrice")]
        public double? FirstPrice { get; set; }

        [JsonPropertyName("openedAt")]
        public DateTime OpenedAt { get; set; }

        [JsonPropertyName("createdAt")]
        public DateTime CreatedAt { get; set; }

        [JsonPropertyName("updatedAt")]
        public DateTime UpdatedAt { get; set; }

        [JsonPropertyName("tpHit")]
        public bool? TpHit { get; set; }

        [JsonPropertyName("slHit")]
        public bool? SlHit { get; set; }

        [JsonPropertyName("outcomePrice")]
        public double? OutcomePrice { get; set; }
    }
}
