using backend_service.Models;
using Microsoft.Extensions.Options;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

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

        public async Task<List<Signal>> GetTopSignalsAsync()
        {
            // Sadece açık sinyalleri getir (tp_hit ve sl_hit her ikisi de null olmalı)
            var filter = Builders<Signal>.Filter.And(
                Builders<Signal>.Filter.Eq(s => s.TpHit, null),
                Builders<Signal>.Filter.Eq(s => s.SlHit, null)
            );
            return await _signalsCollection.Find(filter)
                .SortByDescending(s => s.Strength)
                .ThenByDescending(s => s.OpenedAt)
                .Limit(3)
                .ToListAsync();
        }

        public async Task<SignalPagedResponseDto> GetFilteredSignalsAsync(
            string timeframe,
            string? symbol = null,
            string? direction = null,
            int? minStrength = null,
            string? status = null,
            int page = 1,
            int pageSize = 25)
        {
            // Validate inputs
            if (page < 1) page = 1;
            if (pageSize < 1 || pageSize > 1000) pageSize = 25;

            // Determine freshness window based on timeframe and status
            // Closed signals: up to 7 days
            var cutoffDate = status == "closed"
                ? DateTime.UtcNow.AddDays(-7)
                : timeframe switch
                {
                    "15m" => DateTime.UtcNow.AddHours(-24),
                    "1h" => DateTime.UtcNow.AddDays(-3),
                    "4h" => DateTime.UtcNow.AddDays(-7),
                    "1d" => DateTime.UtcNow.AddDays(-30),
                    _ => DateTime.UtcNow.AddHours(-24)
                };

            // Build base filter
            var filterBuilder = Builders<Signal>.Filter;
            var filters = new List<FilterDefinition<Signal>>
            {
                filterBuilder.Eq(s => s.Timeframe, timeframe),
                filterBuilder.Gte(s => s.OpenedAt, cutoffDate)
            };

            // Add optional filters
            if (!string.IsNullOrEmpty(symbol))
            {
                filters.Add(filterBuilder.Regex(s => s.Symbol, new MongoDB.Bson.BsonRegularExpression(symbol, "i"))); // case-insensitive
            }

            if (!string.IsNullOrEmpty(direction))
            {
                filters.Add(filterBuilder.Eq(s => s.Direction, direction));
            }

            if (minStrength.HasValue)
            {
                filters.Add(filterBuilder.Gte(s => s.Strength, minStrength.Value));
            }

            if (status == "open")
            {
                filters.Add(filterBuilder.Eq(s => s.TpHit, null));
                filters.Add(filterBuilder.Eq(s => s.SlHit, null));
            }
            else if (status == "closed")
            {
                var tpClosed = filterBuilder.Ne(s => s.TpHit, null);
                var slClosed = filterBuilder.Ne(s => s.SlHit, null);
                filters.Add(filterBuilder.Or(tpClosed, slClosed));
            }

            var combinedFilter = filterBuilder.And(filters);

            // Get all matching signals
            var allSignals = await _signalsCollection
                .Find(combinedFilter)
                .ToListAsync();

            // Açık sinyaller: symbol başına yalnızca en son kayıt göster
            // Kapanmış sinyaller: tüm geçmiş kayıtları göster (her biri ayrı sinyal)
            List<Signal> latestPerSymbol;
            if (status == "closed")
            {
                latestPerSymbol = allSignals;
            }
            else
            {
                latestPerSymbol = allSignals
                    .GroupBy(s => s.Symbol)
                    .Select(g => g.OrderByDescending(s => s.OpenedAt).First())
                    .ToList();
            }

            // Sort: openedAt desc, then strength desc
            var sorted = latestPerSymbol
                .OrderByDescending(s => s.OpenedAt)
                .ThenByDescending(s => s.Strength)
                .ToList();

            // Calculate pagination
            var totalCount = sorted.Count;
            var totalPages = (int)Math.Ceiling(totalCount / (double)pageSize);
            var skipCount = (page - 1) * pageSize;

            // Apply pagination
            var paginatedItems = sorted
                .Skip(skipCount)
                .Take(pageSize)
                .ToList();

            return new SignalPagedResponseDto
            {
                Items = paginatedItems.Select(MapToDto).ToList(),
                Page = page,
                PageSize = pageSize,
                TotalCount = totalCount,
                TotalPages = totalPages,
                Timeframe = timeframe
            };
        }

        private SignalResponseDto MapToDto(Signal signal)
        {
            return new SignalResponseDto
            {
                Symbol = signal.Symbol,
                Timeframe = signal.Timeframe,
                Direction = signal.Direction,
                Strength = signal.Strength,
                Reason = signal.Reason,
                Price = signal.Price,
                FirstPrice = signal.FirstPrice,
                StopLoss = signal.StopLoss,
                TargetPrice = signal.TargetPrice,
                RiskReward = signal.RiskReward,
                RiskAmount = signal.RiskAmount,
                RewardAmount = signal.RewardAmount,
                Atr = signal.Atr,
                OpenedAt = signal.OpenedAt,
                CreatedAt = signal.CreatedAt,
                UpdatedAt = signal.UpdatedAt,
                TpHit = signal.TpHit,
                SlHit = signal.SlHit,
                OutcomePrice = signal.OutcomePrice
            };
        }
    }
}

