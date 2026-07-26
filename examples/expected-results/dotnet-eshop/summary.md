# .NET eShop — curated showcase summary

> Bounded artifact. Upstream source is fetched on demand; not vendored here.

## Repository identity

| Field | Value |
| ----- | ----- |
| Example ID | `dotnet-eshop` |
| Upstream | https://github.com/dotnet/eShop |
| Pinned revision | `9b4f9434f46fdc5c1a6e9e936af2868340cdbc48` |
| License | MIT |
| Profile | `community` / `--no-ai` |

## Detected technologies

C# / .NET Aspire-oriented microservices reference application (details refreshed
via `python scripts/run_showcase.py dotnet-eshop`).

## Architecture summary

Multi-project .NET reference eShop with Aspire orchestration samples. CodeStrata
assesses source statically; Docker/Aspire runtime is not executed.

## Assessment coverage

Baseline assess: language/.NET project detection, architecture and dependency
signals, HTML/JSON reports.

## Finding counts / top findings / recommendations

See `summary.json` (may remain pending until a maintainer live refresh).

## Assessment duration

`runtime_category: slow` — allow 10+ minutes on typical developer hardware.

## Known false positives

None curated yet.

## Known unsupported areas

* Aspire/Docker orchestration not executed.
* Larger tree may hit runtime limits depending on host configuration.
