using Microsoft.EntityFrameworkCore;
using SampleAspNet.Models;

namespace SampleAspNet.Data;

public sealed class AppDbContext : DbContext
{
    public DbSet<User> Users => Set<User>();

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        optionsBuilder.UseSqlServer("Server=(localdb)\\mssqllocaldb;Database=SampleAspNet;");
    }
}
