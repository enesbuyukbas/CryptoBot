using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace backend_service.Models
{
    public class Signal
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public required string Id { get; set; }

        [BsonElement("symbol")]  // ✅ MongoDB'deki "symbol" ile eşleşmeli
        public required string Symbol { get; set; }

        [BsonElement("signalType")]  // ✅ MongoDB'deki "signal_type" ile eşleşmeli
        public required string SignalType { get; set; }

        [BsonElement("price")]
        public double Price { get; set; }

        [BsonElement("pullback_level")]
        public double PullbackLevel { get; set; }

        [BsonElement("target_price")]
        public double TargetPrice { get; set; }

        [BsonElement("strength")]
        public int Strength { get; set; }

        [BsonElement("indicators")]
        public required string Indicators { get; set; }

        [BsonElement("signal_time")]
        public required string SignalTime { get; set; }
    }
}
