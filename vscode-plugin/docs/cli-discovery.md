# CodeStrata CLI discovery (Slice 13.2)

Policy: `community-vscode-cli-discovery-policy:1.0`

## Purpose

Detect and validate a local CodeStrata Engine CLI before initialization or
assessment. This slice does **not** install, download, upgrade, or repair the CLI.

## Candidate sources

| Source | Meaning |
| --- | --- |
| `explicit_configuration` | Non-default `codestrata.engine.executable` |
| `development_environment` | Workspace `.venv` or active `VIRTUAL_ENV` / `CONDA_PREFIX` (existing product contract) |
| `process_path` | Direct spawn of `codestrata` via PATH |
| `unavailable` | No candidate |

No arbitrary filesystem crawl (`/opt`, Downloads, home recursion, `node_modules`).

## Precedence

1. **Explicit configuration** — if set to a non-default value, it is the only
   candidate. Invalid explicit configuration **fails closed** (no silent PATH
   fallback).
2. Development environment candidates (existing contract).
3. PATH (`codestrata`).
4. Unavailable.

## Probe

- Command: `codestrata version` (Engine metadata; not `assess` / `init` / `doctor`)
- `shell: false`, structured args
- Timeout: 5 seconds
- Bounded stdout/stderr
- Minimal inherited environment (PATH/PATHEXT/etc.); no mutation of `process.env`

## Identity and version

- First line must match `CodeStrata <semver>`
- Bare `0.2.0` or `codestrata-compatible 0.2.0` is rejected
- Contradictory version lines are rejected

## Provisional compatibility (extension 0.2.0)

- CLI **major must be 0**
- CLI must be a supported **0.2.x** release (see [cli-compatibility.md](./cli-compatibility.md))
- CLI **1.x is incompatible**

## Workflow ordering

1. Workspace validation
2. CLI discovery (readiness probes; not product invocations)
3. Command-local telemetry consent (eligible assessment commands only)
4. Progress
5. One product CLI invocation (`init` / `assess`)
6. Result / report handling

If discovery fails: no product CLI, no telemetry prompt, no report open.

## Activation

Activation does **not** probe the CLI. First-run welcome asks **Get Started**
before discovery.

## Privacy

Stable diagnostics include source category, status, identity boolean, version
major/minor/patch, and limitation codes. They do **not** include executable path,
PATH, environment, stdout/stderr, or workspace paths.

## Deferred

- ~~Slice 13.3 — installation / download / upgrade~~ — guidance-only
  ([cli-installation.md](./cli-installation.md)); no automatic install
- ~~Slice 13.4 — repository initialization~~ —
  [repository-initialization.md](./repository-initialization.md)
- ~~Slice 13.5 — assessment execution~~ —
  [assessment-execution.md](./assessment-execution.md)
- Slice 13.11 — [cli-compatibility.md](./cli-compatibility.md) (complete)
- Slice 13.14 — clean-install package validation
