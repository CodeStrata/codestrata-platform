# Repository initialization (Slice 13.4)

Policy: `community-vscode-repository-initialization-policy:1.0`

## Purpose

User-triggered **Initialize Repository** (`codestrata.init`)
coordinates a safe, deterministic initialization workflow. The **Engine CLI**
(`codestrata init`) is the sole authority that creates CodeStrata repository
configuration.

Initialization is **not** an assessment path.

## Sequence

1. Resolve an eligible local workspace folder (multi-root: user selects one).
2. Discover a compatible CodeStrata CLI (Slice 13.2).
3. If unavailable → Slice 13.3 installation guidance (no auto-resume of init).
4. Detect local initialization state.
5. If already validly initialized → return `already_initialized` (**no CLI**).
6. If invalid/partial existing config → fail closed; **preserve** the file.
7. Otherwise invoke Engine `init` **once** (`shell: false`, no `--force`).
8. Re-detect state and verify; return a bounded result.

## Engine authority

Engine `codestrata init` writes a minimal `codestrata.toml` (template includes
`[repository]` and related tables). It refuses an existing file unless
`--force` is passed. The extension **never** passes `--force` and does not
synthesize or repair configuration itself.

Workspace directories declared in the template (for example under
`.codestrata/`) are **not** created by Engine init — only the configuration
file is written.

## States

| State | Meaning |
| --- | --- |
| `not_initialized` | Expected config file absent |
| `initialized` | File present with structural `[repository]` marker |
| `invalid_configuration` | File present but structurally invalid |
| `partial_initialization` | Empty file (single-artifact partial) |
| `unknown` | Unreadable / unexpected I/O |

## Results

Typed statuses include `initialized`, `already_initialized`, `failed`,
`cancelled`, `cli_unavailable`, `workspace_unavailable`,
`invalid_existing_configuration`, `partial_existing_configuration`, and
`verification_failed` (CLI claimed success but state not initialized).

## Boundaries

- No assessment, AI provider execution, telemetry consent, analytics, or report open
- No source / package / build / `.git` mutation by the extension
- No network calls for initialization
- Diagnostics omit workspace/config/CLI paths, stdout/stderr, environment, credentials
- Recovery categories are bounded (`install_cli`, `inspect_existing_configuration`,
  `retry_initialization`, `select_workspace`, …); full recovery UX is [failure-recovery.md](./failure-recovery.md) (Slice 13.8)

## Related

- [community-workflow.md](./community-workflow.md)
- [cli-discovery.md](./cli-discovery.md)
- [cli-installation.md](./cli-installation.md)

Assessment execution is Slice **13.5** —
[assessment-execution.md](./assessment-execution.md). Progress/report/recovery
UX remain later slices.
