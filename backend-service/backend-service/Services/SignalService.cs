using backend_service.Models;
using Microsoft.Extensions.Options;
using MongoDB.Driver;

namespace backend_service.Services
{
    public class SignalService
    {
        private readonly IMongoCollection<Signal> _signalsCollection;

        public SignalService(IOptions<MongoDBSettings> mongoDBSettings)
        {
            var client = new MongoClient(mongoDBSettings.Value.ConnectionString);
            var database = client.GetDatabase(mongoDBSettings.Value.DatabaseName);
            _signalsCollection = database.GetCollection<Signal>(mongoDBSettings.Value.SignalsCollection);
        }

        public async Task<List<Signal>> GetSignalsAsync() =>
            await _signalsCollection.Find(signal => true).ToListAsync();

        public async Task<List<Signal>> GetTopSignalsAsync() =>
            await _signalsCollection.Find(signal => true)
                .SortByDescending(s => s.Strength)
                .Limit(3)
                .ToListAsync();
    }
}
