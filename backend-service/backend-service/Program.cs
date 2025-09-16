using backend_service.Models;
using backend_service.Services;
using backend_service.Services.Providers;   // Provider DI
using Microsoft.Extensions.Caching.Memory;  // MemoryCache DI

var builder = WebApplication.CreateBuilder(args);

// CORS 
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAngularApp",
        policy => policy
            .WithOrigins("http://localhost:4200") //  Angular'�n �al��t��� port
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials()); // E�er kimlik do�rulama gerekiyorsa
});

// MongoDB Ayarlar�n� Konfig�rasyon Dosyas�ndan Y�kle
builder.Services.Configure<MongoDBSettings>(
    builder.Configuration.GetSection("MongoDB"));

builder.Services.AddSingleton<SignalService>(); // SignalService'i servislere ekle



//Fear & Greed provider'ı için HttpClient DI
builder.Services.AddHttpClient<IFngClient, AlternativeMeFngClient>(c =>
{
    c.BaseAddress = new Uri("https://api.alternative.me/");
    c.Timeout = TimeSpan.FromSeconds(10);
});

//Market Cap için CoinGecko client DI
builder.Services.AddHttpClient<IGlobalMarketClient, CoinGeckoGlobalClient>(c =>
{
    c.BaseAddress = new Uri("https://api.coingecko.com/api/v3/");
    c.Timeout = TimeSpan.FromSeconds(10);
});

//Altseason provider'ı için HttpClient DI
builder.Services.AddHttpClient<IAltseasonClient, CoingeckoAltseasonClient>(c =>
{
    c.BaseAddress = new Uri("https://api.coingecko.com/api/v3/");
    c.Timeout = TimeSpan.FromSeconds(30);
    c.DefaultRequestHeaders.UserAgent.ParseAdd("CryptoBot/1.0 (+https://localhost)");
});


builder.Services.AddMemoryCache(); // MemoryCache servisi DI
// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseCors("AllowAngularApp"); // CORS Politikas�n� Etkinle�tir

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
