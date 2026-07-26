# C# / .NET language evidence provider

Provider ID: `language.csharp.core`

Collects C# source-file, `using` import, architecture unit/layer, and framework-usage
facts using the shared architecture view builder. NuGet package declarations are
collected by Dependency Evidence (`dependency.nuget.manifest`), not this provider.

## Related providers

| Provider ID | Role |
| --- | --- |
| `language.csharp.core` | Architecture / import / framework hits |
| `language.csharp.complexity` | Structural complexity (brace-scan; Phase 5.18) |
| `dependency.nuget.manifest` | NuGet declared dependencies |

## Applicability

Applicable when repository paths include at least one `.cs` source file.

## Supported frameworks (detection / framework hits)

- ASP.NET Core / Web API
- ASP.NET MVC
- Blazor
- Entity Framework / EF Core
- WCF
- DI registrations (`AddScoped` / `AddTransient` / `AddSingleton`)
- Hosted / background services

## Build / dependency manifests

- `*.sln`, `*.csproj` / `*.fsproj`, `global.json`, `Directory.Build.props`
- `Directory.Packages.props`, `packages.config`, `packages.lock.json`

## Complexity (Phase 5.18)

C# complexity uses the same shared `File` / `Type` / `Callable` evidence models as
Java/Python/PHP. Extraction is a brace-aware structural scan (not Roslyn / not a
certified cyclomatic product metric). `struct` / `record` map to the existing
`CLASS` type kind.

```toml
[evidence.complexity]
enabled = true

[evidence.complexity.csharp]
enabled = true

[rules.technical_debt]
enabled = true
```

## Dependency hygiene (Phase 5.18)

The Dependency Intelligence pack includes `csharp` in `supported_languages`.
NuGet declarations participate in shared hygiene rules (duplicates, unbounded `*`
/ floating versions). Ordinary pinned NuGet versions are not mutable findings.

```toml
[evidence.dependency]
enabled = true

[evidence.dependency.nuget]
enabled = true

[rules.dependency]
enabled = true
```

## Limitations

- No Roslyn AST; regex/`using` imports and brace-scan complexity only
- `bin/` / `obj/` / `packages/` trees are ignored by default
- Closures / local functions are not extracted for complexity
- Central Package Management versionless PackageReference resolution is partial
- F# / VB language providers are not first-class (project files may still surface NuGet facts)
