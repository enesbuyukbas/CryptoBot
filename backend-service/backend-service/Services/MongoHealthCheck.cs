using backend_service.Models;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Options;
using MongoDB.Bson;
using MongoDB.Driver;

namespace backend_service.Services;

public sealed class MongoHealthCheck : IHealthCheck
{
    private readonly IMongoDatabase _database;

    public MongoHealthCheck(IOptions<MongoDBSettings> settings)
    {
        var client = new MongoClient(settings.Value.ConnectionString);
        _database = client.GetDatabase(settings.Value.DatabaseName);
    }

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await _database.RunCommandAsync<BsonDocument>(
                new BsonDocument("ping", 1),
                cancellationToken: cancellationToken);

            return HealthCheckResult.Healthy("MongoDB is reachable.");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("MongoDB is unreachable.", ex);
        }
    }
}
