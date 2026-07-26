using Microsoft.AspNetCore.Mvc;
using SampleAspNet.Models;
using SampleAspNet.Services;

namespace SampleAspNet.Controllers;

[ApiController]
[Route("api/users")]
public sealed class UsersController : ControllerBase
{
    private readonly IUserService _users;

    public UsersController(IUserService users)
    {
        _users = users;
    }

    [HttpGet("{id}")]
    public ActionResult<User> Get(int id)
    {
        var user = _users.Find(id);
        if (user is null)
        {
            return NotFound();
        }
        return user;
    }
}
