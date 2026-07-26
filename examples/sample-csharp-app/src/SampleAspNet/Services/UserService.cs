using SampleAspNet.Models;
using SampleAspNet.Repositories;

namespace SampleAspNet.Services;

public interface IUserService
{
    User? Find(int id);
}

public sealed class UserService : IUserService
{
    private readonly IUserRepository _repository;

    public UserService(IUserRepository repository)
    {
        _repository = repository;
    }

    public User? Find(int id)
    {
        return _repository.GetById(id);
    }
}

public sealed class HeartbeatHostedService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
        }
    }
}

public sealed class ExternalBillingClient
{
    public Task ChargeAsync(string customerId)
    {
        return Task.CompletedTask;
    }
}
