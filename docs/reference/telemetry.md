---
title: Telemetry
description: Canonical CodeStrata Community telemetry policy — default off, explicit consent, production transport, and separation from report publishing.
---

# Telemetry

Canonical Community Edition telemetry documentation for CodeStrata **v0.2.0**.

This page describes what the product **actually does today**. Runtime contracts and
Slice 18.1 inventories are authoritative if wording ever conflicts.

Related:

- [Data Collection](/security/data-collection) — what can leave the machine
- [Collected Fields](/security/collected-fields) — field reference (137 fields)
- [Privacy](/security/privacy) — broader product privacy authority
- [Community Cloud API](/reference/community-api/) — request/response contracts

## Why CodeStrata has telemetry

Optional, privacy-safe product telemetry helps understand which Community Edition
features are used, whether assessments succeed or fail at a coarse level, and how
to improve the Engine and VS Code experience — **without** collecting repository
source, findings, or report bodies.

Telemetry is **not required** to run assessments or produce local reports.

## Default posture

| Topic | Behavior |
| --- | --- |
| Default | **Disabled** (`disabled_by_default`) — no product transmission |
| Silent enable | **Forbidden** — Community Cloud, credentials, or publish eligibility alone never enable telemetry |
| Local assessment | Always works with telemetry off |
| Local reports | Always generated under `.codestrata-artifacts/` with telemetry off |

## Explicit opt-in

| Mechanism | Meaning |
| --- | --- |
| Interactive assess (TTY) | When preference is **undecided**, eligible interactive `assess` prompts once; default is **No** (`[y/N]`) |
| Persisted preference | Explicit Yes/No is stored locally under `CODESTRATA_HOME` and is **not** re-asked |
| CLI enable / disable | `codestrata telemetry enable` / `codestrata telemetry disable` |
| CLI allow flag | `codestrata assess … --telemetry-allow` (process override; does not rewrite preference) |
| VS Code | Native prompt on first undecided assessment; **Allow Anonymous Telemetry** / **No Thanks** / **Learn More** |

After explicit allow, the Engine may open product HTTP transport to
`https://api.codestrata.ai` **only when**
`CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL` is available. Without a Community
client credential, transport stays unavailable (no anonymous ingestion).

## Explicit opt-out

| Mechanism | Meaning |
| --- | --- |
| CLI disable | `codestrata telemetry disable` — persists explicit No |
| CLI deny flag | `codestrata assess … --telemetry-deny` |
| Interactive No / Enter / dismiss | Persists explicit No; assessment continues |
| Default / undecided | Remains off — always safe |

Opt-out stops **future** consent-governed telemetry. It does **not**
automatically erase historical Data Lake events, revoke public reports, delete
local reports, or erase installation identity files. See
[Data Collection](/security/data-collection#opt-out-scope-telemetry).

## Local preference storage

| Topic | Behavior |
| --- | --- |
| Default | **Not configured** / disabled — no silent telemetry |
| Persistence | Explicit Yes or No is stored locally (survives CLI restarts) |
| Re-prompt | Only when preference is undecided and the session is interactive |
| Status | `codestrata telemetry status` → Enabled / Disabled / Not configured |
| Contents | Anonymous usage and assessment metadata only — **no** source code, repository names, file paths, findings, or credentials |

`--telemetry-allow` / `--telemetry-deny` still win for the **current process**
without changing the stored preference.

## Interactive behavior

```text
Help improve CodeStrata by sharing anonymous usage and assessment metadata.
No source code, repository names, file paths, findings, or credentials are sent.

Share anonymous telemetry? [y/N]:
```

Enter / empty → No (persisted). Y/yes → Yes (persisted). Assessment continues
either way.

## Voluntary report feedback (not telemetry)

Published reports at `https://reports.codestrata.ai/r/<opaque-id>` may offer:

```text
Was this report useful?
[Yes] [No]
```

This is a **separate** voluntary action from telemetry consent. No free text,
no login, no repository identity. Aggregates appear in Insights as
**Community Sentiment** (explicit Yes/No only — never AI-inferred). No response
does not count as negative.

## Non-interactive / CI behavior

Non-interactive, headless, quiet, or CI contexts **never prompt**.

| Topic | Behavior |
| --- | --- |
| Prompt | Never |
| Decision | `non_interactive_disabled` unless an explicit supported allow flag is provided |
| Assessment | Continues normally |
| Local reports | Continues normally |
| Silent persistence | None |

### CI example

```bash
# Telemetry remains disabled (privacy-safe) — recommended default for CI
codestrata assess --repo . --no-ai --quiet

# Explicit allow for this process only (also requires Community credential for HTTP)
codestrata assess --repo . --no-ai --quiet --telemetry-allow

# Explicit deny for this process
codestrata assess --repo . --no-ai --quiet --telemetry-deny
```

## Authentication

Community ingest routes require authenticated Community client credentials
(fingerprint-verified). Health and Community Status are public.

Anonymous writes to ingest routes return `401`.

## Transport and production endpoint

Public production authority:

`https://api.codestrata.ai`

Primary product telemetry path:

`POST https://api.codestrata.ai/api/v1/telemetry`

| Topic | Behavior |
| --- | --- |
| Protocol | HTTPS |
| Consent | Required for product transmission |
| Auth | Community client credential |
| Privacy validation | Server rejects privacy-invalid payloads |
| Failure isolation | Telemetry failure must not fail assessment or remove local reports |
| Offline | Best-effort; no durable offline queue for product telemetry in v0.2.0 |

The raw AWS `execute-api` hostname is an implementation detail and is **not**
the public API authority.

## Failure isolation and offline behavior

- Telemetry is best-effort after opt-in
- Assessment and local report generation are independent of telemetry success
- Disabled / denied / non-interactive sessions keep HTTP transport unavailable

## Insights relationship

Accepted privacy-safe events may land in the Community Data Lake and feed
bounded Insights aggregates for authenticated operators. Insights does **not**
display raw installation identifiers or report HTML/JSON bodies.

## Report-publishing separation

**Telemetry opt-in ≠ public report authorization.**

Publishing Assessment or Engineering Intelligence reports requires a separate
explicit Publish/Share confirmation (for example
`codestrata report publish --confirm-public-publish`). Telemetry allow alone
never publishes a report.

## Production availability (v0.2.0)

Production Community telemetry is available when **all** of the following hold:

1. The user has an explicit Yes preference (persisted or process override) / `--telemetry-allow`
2. A valid Community client credential is available
3. Network transport to `api.codestrata.ai` is available

Only the product **`telemetry`** stream is classified as **ACTIVE** after
opt-in in the current Engine path. Other registered Community streams may exist
as API/Data Lake capacity without being emitted by the current assess path.
See the stream status table on [Data Collection](/security/data-collection).

## Installation / client identity

CodeStrata may use a **random installation identifier** (UUID v4) for analytics
continuity and aggregation. It is not derived from machine properties, user
identity, or repository identity.

| Topic | Detail |
| --- | --- |
| Type | Random UUID v4 |
| Local file | `~/.codestrata/anonymous-installation-identity.json` (when used) |
| Privacy-first assess | Does **not** require generating an installation id for normal transmission |
| Wire contracts | Some Community stream schemas may accept optional `installation_id` when present |
| Insights | Must not show raw installation ids in the UI |
| Wording | Prefer “random installation identifier” — do not claim absolute anonymity |


## VS Code

Eligible assessment commands may prompt when preference is **undecided**.
Discovery, install guidance, initialization, report open, doctor, and recovery
do not prompt. Explicit Allow / No Thanks is stored in extension `globalState`
(`codestrata.telemetryPreference`) and can be changed via **Telemetry Settings**.
Default remains disabled until decided.

Public extension distribution:
[CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
(`CodeStrataAI.codestrata-assessment`). Extension source remains private.

## Precedence (privacy-first)

1. Explicit CLI `--telemetry-allow` / `--telemetry-deny` (process override)
2. Persisted local preference (Yes / No)
3. Interactive prompt when undecided and interactive
4. Default disabled / non-interactive disabled

`codestrata telemetry enable|disable|status` manage the same local preference.

## Related

- [Data Collection](/security/data-collection)
- [Collected Fields](/security/collected-fields)
- [Privacy](/security/privacy)
- [Retention and Deletion](/security/retention-and-deletion)
- [Community Cloud API](/reference/community-api/)
- [CLI Reference](/reference/cli)
- [VS Code](/extensions/vscode)
