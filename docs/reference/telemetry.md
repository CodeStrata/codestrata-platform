---
title: Telemetry
description: Canonical CodeStrata Community telemetry and assessment-intelligence policy — consent v2, privacy-safe aggregates, and separation from report publishing.
---

# Telemetry

Canonical Community Edition telemetry documentation for CodeStrata **v0.2.1**.

This page describes what the product **actually does today**. Runtime contracts and
clean-runner suites through Slice 20.11 are authoritative if wording ever conflicts.

Related:

- [Data Collection](/security/data-collection) — what can leave the machine
- [Collected Fields](/security/collected-fields) — field reference
- [Privacy](/security/privacy) — broader product privacy authority
- [Community Cloud API](/reference/community-api/) — request/response contracts

## Why CodeStrata has telemetry

Optional, privacy-preserving product telemetry helps understand which Community
Edition features are used, whether assessments succeed or fail at a coarse level,
and how to improve the Engine and VS Code experience — **without** collecting
repository source, finding prose, or report bodies.

With **v2 consent**, CodeStrata may also send **privacy-safe derived assessment
intelligence** (bounded aggregates and categorical characteristics). That is
**not** an upload of individual findings or assessment reports.

Telemetry is **not required** to run assessments or produce local reports.

## Consent contract (v0.2.1)

One Engine-owned preference under `CODESTRATA_HOME` applies to **CLI and VS Code**.

| State | Lifecycle usage telemetry | Assessment intelligence (`assessment_metadata` 1.1) |
| --- | --- | --- |
| Undecided (default) | Off | Off |
| Disabled | Off | Off |
| Legacy v1 Yes | On | Off |
| v2 Yes | On | On |

| Topic | Behavior |
| --- | --- |
| Default | **Disabled / undecided** — no Community collection |
| Silent enable | **Forbidden** — Cloud credentials or publish eligibility alone never enable collection |
| Local assessment | Always works with collection off |
| Local reports | Always generated under `.codestrata-artifacts/` with collection off |
| Report publishing | **Separate** explicit action — never caused by telemetry consent |

### Commands

```bash
codestrata telemetry status          # human-readable status
codestrata telemetry status --json   # machine-readable consent capabilities
codestrata telemetry enable          # persist v2 Yes (usage + assessment insights)
codestrata telemetry disable         # persist Disabled (future collection off)
```

`decline-upgrade` keeps legacy v1 lifecycle telemetry and declines broader
assessment insights (used by trusted frontends such as VS Code). Prefer
`enable` / `disable` / `status` for day-to-day use.

## Explicit opt-in

| Mechanism | Meaning |
| --- | --- |
| Interactive assess (TTY) | When preference is **undecided**, eligible interactive `assess` prompts once; default is **No** (`[y/N]`). Yes persists **v2**. |
| Legacy v1 upgrade prompt | Existing lifecycle-only users may be asked once before broader assessment insights; decline keeps v1 |
| CLI enable | `codestrata telemetry enable` → **v2 Yes** |
| VS Code | Same Engine preference — Allow persists v2; No Thanks disables |

After durable **v2 Yes**, the Engine may open product HTTP transport to
`https://api.codestrata.ai` **only when**
`CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL` is available. Without a Community
client credential, transport stays unavailable.

## `--telemetry-allow` is not consent

`codestrata assess … --telemetry-allow` is a **session/frontend bridge** only.

It does **not**:

- create consent for an undecided user
- override explicit **Disabled**
- rewrite the local preference file
- authorize automation to “force telemetry on”

Do not use `--telemetry-allow` as a consent bypass in CI. Prefer durable
`codestrata telemetry enable` when collection is intentionally desired.

`--telemetry-deny` remains a process-local deny for the current invocation
(**Not persisted** as durable preference).

**Precedence** for a single `assess` invocation: CLI flags → durable Engine
preference → interactive prompt (when eligible) → default off.

Public production authority is `https://api.codestrata.ai`. The raw AWS
`execute-api` hostname is an implementation detail and is **not** the public
product authority.

## Explicit opt-out

| Mechanism | Meaning |
| --- | --- |
| CLI disable | `codestrata telemetry disable` — persists Disabled |
| Interactive No / Enter / dismiss | Persists Disabled (or declines upgrade while keeping v1) |
| Default / undecided | Remains off — always safe |

Opt-out / disable stops **future** Community collection. It does **not**
automatically erase historical Data Lake events, revoke public reports, delete
local reports, or erase installation identity files. See
[Data Collection](/security/data-collection#opt-out-scope-telemetry).

## Interactive copy (semantics)

```text
Help improve CodeStrata?

Share anonymous usage and privacy-safe assessment insights.
Source code and repository identity stay local.
This does not publish reports.

Help improve CodeStrata? [y/N]:
```

Enter / empty → No (persisted). Y/yes → v2 Yes (persisted). Assessment continues
either way.

Legacy lifecycle-only users may see a shorter upgrade prompt for assessment
insights before v2 is enabled.

## What v2 may share

### Usage (lifecycle)

- CodeStrata client name / version / platform band
- Assessment lifecycle signals (invoked / completed / failed)
- Bounded duration / usage metadata
- Whether AI enrichment was used (boolean / mode where applicable)

### Assessment intelligence (privacy-safe derived metadata)

- Executed assessment heads
- Safe aggregate counts
- Aggregate finding patterns: approved rule ID + severity + category + count
- Head confidence levels (categorical)
- Approved categorical repository / technology characteristics
- Bounded failure category on failed assessments

## What Community collection does **not** share

Under telemetry and assessment-intelligence consent, CodeStrata does **not**
transmit:

- Source code or raw file contents
- Source snippets / evidence excerpts
- File paths
- Repository name, URL, or git remote
- Organization / user identity
- Credentials / secrets
- Finding titles, descriptions, or recommendation prose
- Exact internal package / dependency names
- Graph nodes, edges, symbols, or path identifiers
- Prompts / model responses
- Stack traces / exception strings
- Report ID / report URL

**Finding language:** CodeStrata does **not** send individual rich findings.
It may send **privacy-safe aggregates** only (approved rule ID, severity,
category, count).

**Scores:** The Engine does **not** emit a canonical overall numeric health score
or numeric per-head scores for this Community intelligence contract. Prefer
“assessment insights,” finding patterns, and head confidence — not “scores.”

**Graph / provider identity:** Graph telemetry is **not** part of the v0.2.1
Community intelligence contract. Specific AI provider identity is **not**
collected on the assess Community path (an `ai_used` boolean may apply).

## Pseudonymous installation identifier

CodeStrata may use a **random installation identifier** (UUID v4) so Insights
can distinguish first vs repeat assessments. It is **not** derived from machine
properties, user identity, or repository identity.

Prefer wording such as “privacy-preserving usage metrics” or “pseudonymous
installation identifier.” Do **not** claim absolute unlinkability / no
persistent identifier.

Insights must not show raw installation identifiers in user-facing responses.

## Non-interactive / CI behavior

Non-interactive, headless, quiet, or CI contexts **never prompt**.

| Consent state | Quiet / CI assess |
| --- | --- |
| v2 Yes | May send approved usage + assessment intelligence (with credential) |
| Legacy v1 Yes | Lifecycle usage only — no assessment intelligence |
| Undecided / Disabled | No Community collection |

`--quiet` / `--json-summary` suppress prompts; they do **not** by themselves
disable durable v2 consent.

### CI example

```bash
# Recommended default — no Community collection without durable consent
codestrata assess --repo . --no-ai --quiet

# After an explicit durable enable (v2), quiet assess may emit approved streams
codestrata telemetry enable
codestrata assess --repo . --no-ai --quiet

# Process-local deny for this invocation
codestrata assess --repo . --no-ai --quiet --telemetry-deny

# --telemetry-allow is a session bridge only (not consent; do not use as CI bypass)
# codestrata assess --repo . --no-ai --quiet --telemetry-allow
```

## Voluntary report feedback (not telemetry)

Published reports at `https://reports.codestrata.ai/r/<opaque-id>` may offer:

```text
Was this report useful?
[Yes] [No]
```

This is a **separate** voluntary action from telemetry consent.

## Authentication

Community ingest routes require authenticated Community client credentials
(fingerprint-verified). Health and Community Status are public.

Anonymous writes to ingest routes return `401`.

## Transport and production endpoint

Public production authority:

`https://api.codestrata.ai`

| Stream | Path | When emitted |
| --- | --- | --- |
| Usage telemetry | `POST /api/v1/telemetry` | After lifecycle-allowed consent (v1 or v2) + credential |
| Assessment intelligence | `POST /api/v1/assessment-metadata` | After **v2** consent + credential (schema **1.0** and **1.1**) |

| Topic | Behavior |
| --- | --- |
| Protocol | HTTPS |
| Consent | Required for product transmission |
| Auth | Community client credential |
| Privacy validation | Server rejects privacy-invalid / unknown fields |
| Failure isolation | Telemetry / amd failure must not fail assessment or remove local reports |
| Offline | Best-effort; no durable offline queue of rich assessment state |

## Insights relationship

Accepted privacy-safe events may land in the Community Data Lake and feed
bounded Insights aggregates. One assessment that emits both lifecycle telemetry
and assessment metadata is counted **once** for Total / Successful / Failed
authorities — not twice.

Insights does **not** display raw installation identifiers or report HTML/JSON
bodies.

## Report-publishing separation

**Telemetry / assessment-intelligence consent ≠ public report authorization.**

Users may:

- Insights consent Yes + Publish No
- Insights consent No + Publish Yes (when publish is otherwise permitted)

Publishing requires a separate explicit Publish/Share confirmation (for example
`codestrata report publish --confirm-public-publish`). Consent alone never
publishes a report.

## Legacy v1 users

Users who previously enabled lightweight lifecycle telemetry:

- Keep lifecycle telemetry until they upgrade or disable
- Are **asked** before broader assessment intelligence is enabled
- Are **not** silently upgraded to v2

If they decline broader v2: lifecycle telemetry may remain; assessment
intelligence stays off.

## VS Code and CLI share consent

VS Code and CLI share the **same** Engine-owned preference under
`CODESTRATA_HOME`.

- Consent carries across CLI and VS Code
- Disabling in one surface applies to the other
- Extension-local UX cache does **not** override Engine consent

## Related

- [Data Collection](/security/data-collection)
- [Collected Fields](/security/collected-fields)
- [Privacy](/security/privacy)
- [Retention and Deletion](/security/retention-and-deletion)
- [Community Cloud API](/reference/community-api/)
- [CLI Reference](/reference/cli)
- [VS Code](/extensions/vscode)
