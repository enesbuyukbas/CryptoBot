using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;

namespace backend_service.Services.Providers
{
    public interface IAltseasonClient
    {
        /// <summary>
        /// Top 50 altcoin'in son 90 günde BTC'den iyi performans gösterme oranını (0-100) hesaplar.
        /// </summary>
        Task<MetricCard> GetAltseasonAsync(CancellationToken ct);
    }
}
