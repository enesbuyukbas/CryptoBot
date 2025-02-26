using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace backend_service.Models
{
    public class Signal
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; }
        public string Symbol { get; set; }
        public string SignalType { get; set; }
        public int Strength { get; set; }
        public double Price { get; set; }
        public double Open { get; set; }
        public double High { get; set; }
        public double Low { get; set; }
        public double Close { get; set; }
        public bool C20 { get; set; }
        public bool C10 { get; set; }
        public bool M2 { get; set; }
        public bool M3 { get; set; }
        public bool M4 { get; set; }
        public bool M5 { get; set; }
        public bool MA20 { get; set; }
        public bool MA50 { get; set; }
        public bool MA200 { get; set; }
        public double ATR { get; set; }
        public double ADX { get; set; }
        public double ROC { get; set; }
        public double StopLoss { get; set; }
        public double TargetPrice { get; set; }
    }
}
