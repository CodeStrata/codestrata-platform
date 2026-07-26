# Dependency Evidence Platform

Phase **4.4.2** — reusable declared-dependency evidence from repository manifests.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Manifest discovery & parsing | **Dependency Evidence** |
| Normalized declaration facts | **Dependency Evidence** |
| Engineering-role interpretation | Dependency Intelligence (later) |
| Vulnerability interpretation | Security Intelligence (later) |

Dependency Intelligence must not reparse manifests. It may receive only a thin
projection / fingerprint handoff.

## Supported sources

| Manifest | Ecosystem | Notes |
| -------- | --------- | ----- |
| `pom.xml` | Maven | Direct deps, dependencyManagement, plugins, profiles; local property resolution only |
| `build.gradle` | Gradle | Static string/map declarations; dynamic DSL → diagnostics |
| `build.gradle.kts` | Gradle | Static Kotlin DSL string declarations |
| `pyproject.toml` | Python | PEP 621 + Poetry tables |
| `requirements.txt` (+ `requirements*.txt`) | Python | Specifiers, extras, markers, local includes |
| `composer.json` | Composer | `require` / `require-dev` (Phase 5.17); platform `php`/`ext-*` skipped |
| `*.csproj` / `packages.config` / `Directory.Packages.props` | NuGet | PackageReference / packages.config / CPM PackageVersion (Phase 5.18) |

**Not supported yet:** npm/`package.json` lockfile resolution, registry calls.

## Declared vs resolved

This platform records **declared** dependencies only. It does not:

- resolve transitive graphs
- execute Maven/Gradle/Python
- fetch parent POMs or remote includes
- invent versions for unresolved expressions

### Version resolution status (schema 1.1.0)

Each declaration carries `version_resolution_status`:

| Status | Meaning |
| ------ | ------- |
| `resolved` | Supported local contract resolved the expression |
| `proven_unresolved` | Supported local contract inspected; still unresolved |
| `unsupported_resolution` | Mechanism outside inspected contract (diagnostic) |
| `not_applicable` | No version / version not required |

Maven local `pom.xml` properties are a supported contract. Gradle property
interpolation (`${…}`), ext/extra, version catalogs, and convention plugins are
**not** inspected; they produce `unsupported_constructs` /
`diagnostics` and partial coverage — not proven-unresolved facts.

## Configuration

```toml
[evidence.dependency]
enabled = false
```

## Artifact

`dependency-evidence.json` (`codestrata.dependency_evidence`, schema `1.1.0`).

## Explicit non-goals

DependencyRole classification, CVEs, licenses, scores, CTO report. Hygiene rules
consume this evidence in Phase 4.4.3+ and must not treat unsupported resolution
coverage as proven absence.
