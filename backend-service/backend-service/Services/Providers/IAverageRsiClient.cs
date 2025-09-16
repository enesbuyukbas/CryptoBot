using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    public interface IAverageRsiClient
    {
        /// <summary>
        /// Top N coin (BTC/stable hariç) için günlük 14-periyot RSI ortalamasını hesaplar.
        /// 429 durumunda BTC+ETH fallback ortalamasını döner.
        /// </summary>
        Task<MetricCard> GetAverageRsiAsync(CancellationToken ct);
    }
}
