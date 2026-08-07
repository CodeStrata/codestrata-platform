# Privacy Policy (CodeStrata Community Edition)

**Product:** CodeStrata Engine (Community Edition) and related Community clients  
**Telemetry schema:** `1.0.0` (legacy `TelemetryService`)  
**Runtime policy:** `community-telemetry-runtime-policy:1.0` (Slice 9.1 foundation; no transmission)  
**Session consent policy:** `community-telemetry-session-consent-policy:1.0` (process-local)  
**Interactive prompt policy:** `community-telemetry-interactive-consent-policy:1.0` (default No; not saved)  
**Non-interactive policy:** `community-telemetry-non-interactive-policy:1.0` (CI/pipes never prompt)  
**CLI consent policy:** `community-telemetry-cli-consent-policy:1.0` (assess `--telemetry-allow` / `--telemetry-deny`)  
**Status policy:** `community-telemetry-status-policy:1.0` (`codestrata telemetry status`)  
**Public catalog policy:** `community-telemetry-public-catalog-policy:1.0`  
**Catalog schema:** `privacy-first-telemetry-catalog` `1.0.0`  
**Preview policy:** `community-telemetry-preview-policy:1.0`  
**Preview schema:** `privacy-first-telemetry-preview` `1.0.0`  
**Pre-transport privacy policy:** `community-telemetry-pre-transport-privacy-policy:1.0`  
**Transport policy:** `community-telemetry-transport-policy:1.0` (HTTP explicit; unavailable by default)  
**Assessment isolation policy:** `community-telemetry-assessment-isolation-policy:1.0`  
**Default:** Anonymous telemetry is **disabled**

> Slice 9.1–9.15: Epic 9 privacy-first telemetry is **complete** for v0.2.0.
> Engine-local telemetry **runtime** is disabled by default and
> does not transmit or generate installation IDs on normal product paths.
> Eligible interactive `assess` may prompt once for process-local consent
> (default No; not persisted). CI, automation, pipes, quiet, and machine-readable
> modes never prompt. Explicit `--telemetry-allow` / `--telemetry-deny` on
> `assess` set process-local consent without prompting and without persisting.
> The public event-and-field catalog lists every privacy-safe event and field
> the runtime may accept or project (`docs/telemetry-event-catalog.md`,
> `docs/telemetry-event-catalog.json`). `codestrata telemetry preview` shows an
> illustrative privacy-safe event locally without transmission
> (`docs/telemetry-preview.md`). Every transport-bound event must pass the
> pre-transport privacy gate (`docs/telemetry-pre-transport-privacy.md`). An
> explicit fail-silent HTTP transport exists but is not activated by default
> (`docs/telemetry-transport.md`). Assessment results remain authoritative when
> telemetry fails (`docs/telemetry-assessment-isolation.md`). VS Code has a
> command-local runtime with unavailable transport only. The former Cursor
> extension is not an active telemetry emitter (product removed in Epic 12).
> Slice 12.4 retires `cursor_extension` from active Community client
> vocabularies; historical records may still deserialize under
> `community-retired-client-policy:1.0`.
> Production collection is **not operational**. Cross-client and completion
> verification: `verification/privacy_first_telemetry/`,
> `verification/privacy_first_telemetry_completion/`.
> **Epic 10 Slice 10.1** adds the anonymous analytics **contract only**
> (`docs/telemetry-anonymous-analytics.md`) — no collection, persistence, or
> transmission. **Slice 10.2** adds local anonymous installation identity
> (`docs/telemetry-installation-identity.md`). **Slice 10.3** adds local
> runtime analytics construction (`docs/telemetry-runtime-analytics.md`) —
> no transmission; analytics payloads are not persisted. **Slice 10.4** adds
> assessment analytics construction APIs
> (`docs/telemetry-assessment-analytics.md`) — not wired into assess; no
> transmission or analytics persistence. **Slice 10.5** adds repository
> aggregate analytics construction APIs
> (`docs/telemetry-repository-aggregate-analytics.md`) — unwired; no
> transmission. **Slice 10.6** adds AI analytics construction APIs
> (`docs/telemetry-ai-analytics.md`) — unwired; no transmission or analytics
> persistence. **Slice 10.8** verifies Epic 10 privacy guarantees (`../verification/anonymous_analytics_privacy/`).
> **Slice 10.9** verifies Epic 10 completion (`../verification/anonymous_analytics_completion/`) —
> contracts-only; production analytics collection remains not operational.
> See `docs/telemetry-runtime.md`,
> `docs/telemetry-disabled-default.md`, `docs/telemetry-session-consent.md`,
> `docs/telemetry-interactive-consent.md`,
> `docs/telemetry-non-interactive.md`,
> `docs/telemetry-cli-consent-flags.md`, and `docs/telemetry-status.md`. The
> sections below describe the existing opt-in `TelemetryService` / CLI
> telemetry preference commands (legacy; separate from the privacy-first catalog).

## What we collect (only if you opt in)

When you explicitly enable anonymous telemetry, CodeStrata may send:

- A random installation ID (UUID v4)
- CodeStrata version, OS family, and Python version
- Command name (for example `assess`, `open`)
- Enabled assessment domain categories (not findings)
- Language categories (for example `python`, `java`) — never filenames
- Repository size **band** and duration **band** (never exact counts)
- Whether optional AI was enabled/used (never prompts or responses)
- Success or failure flags
- Event timestamps

Events are versioned (`schema_version: 1.0.0`). Inspect any payload with:

```bash
codestrata telemetry show
```

## What we never collect

- Source code
- Repository names or URLs
- Git remotes
- File names or filesystem paths
- Findings, recommendations, or report contents
- AI prompts or AI responses
- Credentials, secrets, tokens, or API keys
- Hostname, username, email, or Git identity

## Opt-in process

Telemetry is **off by default**. On first interactive run you may see:

```text
Enable anonymous telemetry? [y/N]
```

The default answer is **No**. After you choose, CodeStrata will not ask again
until you reset.

You can also enable explicitly:

```bash
codestrata telemetry enable
```

## Disable instructions

```bash
codestrata telemetry disable
```

Environment override (forces off):

```bash
export CODESTRATA_TELEMETRY=0
```

## Reset instructions

Resets the anonymous installation ID, preferences, and local event queue
(telemetry returns to disabled; you may be asked again):

```bash
codestrata telemetry reset
```

State is stored under `~/.codestrata/` (override with `CODESTRATA_HOME` for
tests).

## Local queue

If a telemetry endpoint is unavailable, events are queued locally and retried
later. Queuing **never blocks** assessments.

Optional endpoint:

```bash
export CODESTRATA_TELEMETRY_ENDPOINT=https://example.invalid/v1/telemetry
```

When unset, events remain local-only (inspectable via `telemetry show` /
queue files under `~/.codestrata/`).

## Status

```bash
codestrata telemetry status
```

## Contact

Report privacy concerns privately using the process in `SECURITY.md` (GitHub
Security Advisories when enabled). Do not open public issues that include
secrets or private repository details.

## Related documentation

- `docs/telemetry.md` (Engine)
- `docs/ai-provider-security-boundaries.md` (Epic 11 provider privacy / failure isolation)
- `https://docs.codestrata.ai/security/privacy`
- Telemetry JSON Schema: `schemas/telemetry/codestrata.io/v1.0/TelemetryEvent.json`
