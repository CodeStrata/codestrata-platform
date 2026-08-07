# CodeStrata CLI installation guidance (Slice 13.3)

Policy: `community-vscode-cli-installation-policy:1.0`  
Approach: **guidance-only** (Approach A)

## Decision

Automatic package-manager installation is **forbidden**.

Evidence: the prior `installEngine` path spawned `uv` / `pipx` / `pip`, could
mutate `codestrata.engine.executable`, and performed network package installs
without a finalized security contract. Slice 13.3 replaces that with explicit
user-triggered guidance.

`codestrata.installEngine` is preserved as the public command ID and now opens
guidance only.

## What the extension will do

- Explain when discovery says the CLI is missing, invalid, mismatched, or unsupported
- Offer to **copy** a fixed trusted install command
- **Open a visible terminal** without executing commands
- **Open** the trusted Engine Quick Start documentation (HTTPS, fixed URL)
- **Refresh CLI detection** after the user installs elsewhere
- Open the executable setting editor (user-owned; never auto-overwrite)

## What the extension will not do

- Install, download, upgrade, or repair the CLI automatically
- Run package managers
- Use curl-pipe-shell or sudo
- Mutate PATH or shell profiles
- Overwrite `codestrata.engine.executable`
- Persist installation status
- Prompt telemetry or create analytics
- Auto-resume init/assessment after guidance

## Supported method catalog

| Method | Action |
| --- | --- |
| `documentation` | Open fixed Quick Start URL |
| `python_package` | Copy `python3 -m pip install "codestrata[mcp]"` (Windows: `py -3 …`) |
| `pipx` | Copy `pipx install "codestrata[mcp]"` |
| `uv_tool` | Copy `uv tool install "codestrata[mcp]"` |
| `terminal_guidance` | Open terminal (no auto-execute) |

Public package availability for clean installs is deferred to Slice **13.14**.
Exact version compatibility: [cli-compatibility.md](./cli-compatibility.md) (Slice **13.11**).

## Discovery mapping

| Discovery status | Guidance |
| --- | --- |
| `compatible` | `not_required` |
| `not_found` | install CLI |
| `invalid_configuration` / `not_executable` | correct setting (no silent replace) |
| `identity_mismatch` | replace non-CodeStrata executable |
| `incompatible` | install supported version |
| probe failures | retry discovery |

## Ordering when discovery fails

workspace → discovery → bounded readiness → optional guidance → **stop**  
(no consent, progress, init/assess, or report open)

## Related

- [cli-discovery.md](./cli-discovery.md)
- [community-workflow.md](./community-workflow.md)
- [repository-initialization.md](./repository-initialization.md)
- [assessment-execution.md](./assessment-execution.md)
