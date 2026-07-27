using SampleAspNet.Data;
using SampleAspNet.Models;

namespace SampleAspNet.Repositories;

public interface IUserRepository
{
    User? GetById(int id);
}

public sealed class UserRepository : IUserRepository
{
    private readonly AppDbContext _db;

    public UserRepository(AppDbContext db)
    {
        _db = db;
    }

    public User? GetById(int id)
    {
        return _db.Users.FirstOrDefault(user => user.Id == id);
    }
}
