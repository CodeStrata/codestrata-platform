using SampleAspNet.Models;
using Xunit;

namespace SampleAspNet.Tests;

public sealed class UserTests
{
    [Fact]
    public void User_defaults_email_to_empty()
    {
        var user = new User();
        Assert.Equal(string.Empty, user.Email);
    }
}
