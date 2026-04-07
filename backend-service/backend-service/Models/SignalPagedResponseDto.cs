using System.Text.Json.Serialization;

namespace backend_service.Models
{
    public class SignalPagedResponseDto
    {
        [JsonPropertyName("items")]
        public List<SignalResponseDto> Items { get; set; } = new();

        [JsonPropertyName("page")]
        public int Page { get; set; }

        [JsonPropertyName("pageSize")]
        public int PageSize { get; set; }

        [JsonPropertyName("totalCount")]
        public int TotalCount { get; set; }

        [JsonPropertyName("totalPages")]
        public int TotalPages { get; set; }

        [JsonPropertyName("timeframe")]
        public string Timeframe { get; set; } = default!;
    }
}
