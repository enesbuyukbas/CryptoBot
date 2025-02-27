using backend_service.Models;
using backend_service.Services;

var builder = WebApplication.CreateBuilder(args);

// CORS 
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAngularApp",
        policy => policy
            .WithOrigins("http://localhost:4200") //  Angular'ýn çalýþtýðý port
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials()); // Eðer kimlik doðrulama gerekiyorsa
});

// MongoDB Ayarlarýný Konfigürasyon Dosyasýndan Yükle
builder.Services.Configure<MongoDBSettings>(
    builder.Configuration.GetSection("MongoDB"));

builder.Services.AddSingleton<SignalService>(); // SignalService'i servislere ekle

// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseCors("AllowAngularApp"); // CORS Politikasýný Etkinleþtir

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
