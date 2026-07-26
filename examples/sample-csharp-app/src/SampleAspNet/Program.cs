using Microsoft.EntityFrameworkCore;
using SampleAspNet.Data;
using SampleAspNet.Middleware;
using SampleAspNet.Repositories;
using SampleAspNet.Services;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddDbContext<AppDbContext>();
builder.Services.AddHostedService<HeartbeatHostedService>();
builder.Services.AddSingleton<ExternalBillingClient>();

var app = builder.Build();
app.UseMiddleware<RequestTimingMiddleware>();
app.MapControllers();
app.Run();
