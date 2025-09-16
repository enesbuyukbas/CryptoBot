using System;
using System.Threading;
using System.Threading.Tasks;
using backend_service.Models;
using backend_service.Services.Providers;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Caching.Memory;

namespace backend_service.Controllers
{
    [ApiController]
    [Route("api/metrics")]
    public sealed class MetricsController : ControllerBase
    {
        private readonly IFngClient _fng;
        private readonly IMemoryCache _cache;
        private readonly IGlobalMarketClient _global;
        private static readonly TimeSpan Ttl = TimeSpan.FromSeconds(90);

        public MetricsController(IFngClient fng, IGlobalMarketClient global, IMemoryCache cache)
        {
            _fng = fng;
            _cache = cache;
            _global = global;
        }

        [HttpGet("fng")]
        public async Task<ActionResult<MetricCard>> GetFng(CancellationToken ct)
        {
            var dto = await _cache.GetOrCreateAsync("metric:fng", async e =>
            {
                e.AbsoluteExpirationRelativeToNow = Ttl;
                return await _fng.GetAsync(ct);
            });

            return Ok(dto);
        }

        [HttpGet("market-cap")]
        public async Task<ActionResult<MetricCard>> GetMarketCap(CancellationToken ct)
        {
            var dto = await _cache.GetOrCreateAsync("metric:marketcap", async e =>
            {
                e.AbsoluteExpirationRelativeToNow = Ttl;
                return await _global.GetGlobalMarketCapAsync(ct);
            });
            return Ok(dto);
        }
    }
}
