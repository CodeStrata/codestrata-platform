using System.Diagnostics;

namespace SampleAspNet.Middleware;

public sealed class RequestTimingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestTimingMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var timer = Stopwatch.StartNew();
        await _next(context);
        timer.Stop();
        context.Response.Headers["X-Elapsed-Ms"] = timer.ElapsedMilliseconds.ToString();
    }
}
