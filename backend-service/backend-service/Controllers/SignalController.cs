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
        public async Task<ActionResult<List<Signal>>> GetSignals()
        {
            var signals = await _signalService.GetSignalsAsync();
            return Ok(signals);
        }

        [HttpGet("top")]
        public async Task<ActionResult<List<Signal>>> GetTopSignals()
        {
            var topSignals = await _signalService.GetTopSignalsAsync();
            return Ok(topSignals);
        }
    }
}
