using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using System.Text.Json.Serialization;

[BsonIgnoreExtraElements]
public class Signal
{
    [BsonId]
    public ObjectId Id { get; set; }

    [BsonElement("symbol")]
    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = default!;

    [BsonElement("timeframe")]
    [JsonPropertyName("timeframe")]
    public string Timeframe { get; set; } = default!;

    [BsonElement("direction")]
    [JsonPropertyName("direction")]
    public string Direction { get; set; } = default!;

    [BsonElement("strength")]
    [JsonPropertyName("strength")]
    public int Strength { get; set; }

    [BsonElement("reason")]
    [JsonPropertyName("reason")]
    public List<string> Reason { get; set; } = new();

    [BsonElement("price")]
    [JsonPropertyName("price")]
    public double Price { get; set; }

    [BsonElement("stop_loss")]
    [JsonPropertyName("stop_loss")]
    public double StopLoss { get; set; }

    [BsonElement("target_price")]
    [JsonPropertyName("target_price")]
    public double TargetPrice { get; set; }

    [BsonElement("risk_reward")]
    [JsonPropertyName("risk_reward")]
    public double RiskReward { get; set; }

    [BsonElement("risk_amount")]
    [JsonPropertyName("risk_amount")]
    public double RiskAmount { get; set; }

    [BsonElement("reward_amount")]
    [JsonPropertyName("reward_amount")]
    public double RewardAmount { get; set; }

    [BsonElement("atr")]
    [JsonPropertyName("atr")]
    public double Atr { get; set; }

    [BsonElement("opened_at")]
    [JsonPropertyName("opened_at")]
    public DateTime OpenedAt { get; set; }

    [BsonElement("created_at")]
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }

    [BsonElement("updated_at")]
    [JsonPropertyName("updated_at")]
    public DateTime UpdatedAt { get; set; }
}
