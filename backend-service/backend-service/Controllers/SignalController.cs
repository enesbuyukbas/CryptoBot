using backend_service.Models;
using backend_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace backend_service.Controllers
{
    [ApiController]
    [Route("api/signals")]
    public class SignalController : ControllerBase
    {
        private readonly SignalService _signalService;

        public SignalController(SignalService signalService)
        {
            _signalService = signalService;
        }

        [HttpGet]
        public async Task<ActionResult<List<SignalResponseDto>>> GetSignals()
        {
            var signals = await _signalService.GetSignalsAsync();
            var dtos = signals.Select(MapToDto).ToList();
            return Ok(dtos);
        }

        [HttpGet("top")]
        public async Task<ActionResult<List<SignalResponseDto>>> GetTopSignals()
        {
            var topSignals = await _signalService.GetTopSignalsAsync();
            var dtos = topSignals.Select(MapToDto).ToList();
            return Ok(dtos);
        }

        [HttpGet("filtered")]
        public async Task<ActionResult<SignalPagedResponseDto>> GetFilteredSignals(
            [FromQuery] string timeframe = "15m",
            [FromQuery] string? symbol = null,
            [FromQuery] string? direction = null,
            [FromQuery] int? minStrength = null,
            [FromQuery] string? status = null,
            [FromQuery] int page = 1,
            [FromQuery] int pageSize = 25)
        {
            // Validate timeframe
            var validTimeframes = new[] { "15m", "1h", "4h", "1d" };
            if (!validTimeframes.Contains(timeframe))
            {
                return BadRequest(new { error = "Invalid timeframe. Must be: 15m, 1h, 4h, or 1d" });
            }

            var result = await _signalService.GetFilteredSignalsAsync(
                timeframe, symbol, direction, minStrength, status, page, pageSize);

            return Ok(result);
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
