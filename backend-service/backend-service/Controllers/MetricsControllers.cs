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
        private readonly IGlobalMarketClient _global;
        private readonly IAltseasonClient _altseason;
        private readonly IMemoryCache _cache;


        private static readonly TimeSpan TtlFng = TimeSpan.FromSeconds(90);
        private static readonly TimeSpan TtlMcap = TimeSpan.FromMinutes(90);
        private static readonly TimeSpan TtlAltseason = TimeSpan.FromHours(6);

        public MetricsController(IFngClient fng, IGlobalMarketClient global, IAltseasonClient altseason, IMemoryCache cache)
        {
            _fng = fng;
            _global = global;
            _altseason = altseason;
            _cache = cache;
        }

        [HttpGet("fng")]
        public async Task<ActionResult<MetricCard>> GetFng(CancellationToken ct)
        {
            var dto = await _cache.GetOrCreateAsync("metric:fng", async e =>
            {
                e.AbsoluteExpirationRelativeToNow = TtlFng;
                return await _fng.GetAsync(ct);
            });

            return Ok(dto);
        }

        [HttpGet("market-cap")]
        public async Task<ActionResult<MetricCard>> GetMarketCap(CancellationToken ct)
        {
            var dto = await _cache.GetOrCreateAsync("metric:marketcap", async e =>
            {
                e.AbsoluteExpirationRelativeToNow = TtlMcap;
                return await _global.GetGlobalMarketCapAsync(ct);
            });
            return Ok(dto);
        }

        [HttpGet("altseason")]
        public async Task<ActionResult<MetricCard>> GetAltseason(CancellationToken ct)
        {
            var dto = await _cache.GetOrCreateAsync("metric:altseason", async e =>
            {
                e.AbsoluteExpirationRelativeToNow = TtlAltseason;
                return await _altseason.GetAltseasonAsync(ct);
            });
            return Ok(dto);
        }
    }
}
