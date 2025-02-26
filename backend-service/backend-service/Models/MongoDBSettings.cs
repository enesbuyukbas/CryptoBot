namespace backend_service.Models
{
    public class MongoDBSettings
    {
        public string ConnectionString { get; set; } = null!;
        public string DatabaseName { get; set; } = null!;
        public string SignalsCollection { get; set; } = null!;
    }
}
