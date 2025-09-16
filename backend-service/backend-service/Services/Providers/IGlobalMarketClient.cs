using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    public interface IGlobalMarketClient
    {
        Task<MetricCard> GetGlobalMarketCapAsync(CancellationToken ct);
    }
}
