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

    [BsonElement("signal_time")]
    [JsonPropertyName("signal_time")]
    public string SignalTime { get; set; } = default!; // Python string kaydediyor

    [BsonElement("signal_type")]
    [JsonPropertyName("signal_type")]
    public string SignalType { get; set; } = default!;

    [BsonElement("price")]
    [JsonPropertyName("price")]
    public double Price { get; set; }

    // 🔽 Tabloya yeni eklenen alanlar
    [BsonElement("open")]
    [JsonPropertyName("open")]
    public double? Open { get; set; }

    [BsonElement("high")]
    [JsonPropertyName("high")]
    public double? High { get; set; }

    [BsonElement("low")]
    [JsonPropertyName("low")]
    public double? Low { get; set; }

    [BsonElement("close")]
    [JsonPropertyName("close")]
    public double? Close { get; set; }

    [BsonElement("atr")]
    [JsonPropertyName("atr")]
    public double? Atr { get; set; }

    [BsonElement("adx")]
    [JsonPropertyName("adx")]
    public double? Adx { get; set; }

    [BsonElement("roc")]
    [JsonPropertyName("roc")]
    public double? Roc { get; set; }

    [BsonElement("pullback_level")]
    [JsonPropertyName("pullback_level")]
    public double? PullbackLevel { get; set; }

    [BsonElement("target_price")]
    [JsonPropertyName("target_price")]
    public double? TargetPrice { get; set; }

    [BsonElement("strength")]
    [JsonPropertyName("strength")]
    public int Strength { get; set; }

    [BsonElement("indicators")]
    [JsonPropertyName("indicators")]
    public string? Indicators { get; set; }
}
