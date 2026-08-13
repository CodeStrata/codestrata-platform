---
title: Privacy
description: Canonical Community Edition and CodeStrata Engine privacy authority — local assessments, telemetry, Data Lake, published reports, and AI providers.
---

# Privacy

This page is the **canonical Community / Engine product privacy authority** for
CodeStrata Community Edition (Engine CLI, VS Code extension clients, Community
Cloud API, Data Lake, and published reports).

## Corporate website privacy vs this page

| Surface | What it covers |
| --- | --- |
| [codestrata.ai/privacy](https://codestrata.ai/privacy) | Corporate website / legal privacy notice for the marketing site and related web properties |
| **This page** (`docs.codestrata.ai/security/privacy`) | Product privacy for **local Engineering Assessments**, optional Community telemetry, Community Data Lake streams, explicit report publishing, and optional AI enrichment |

Claims on this page describe Community Edition runtime behavior. They do not
replace the corporate legal notice, and the corporate notice does not define
Engine assessment or telemetry contracts.

## Local assessment privacy

Engineering Assessments run **locally by default** on your machine (or CI you
control). Deterministic assessment (`--no-ai`) does not call AI providers.

Successful runs write inspectable artifacts under:

```text
.codestrata-artifacts/assessments/<repository_id>/current/
.codestrata-artifacts/assessments/<repository_id>/previous/
```

Typical files in a slot:

- `assessment.json` — machine-readable assessment artifact
- `assessment.html` — interactive HTML report
- `heads/` — per-head assessment artifacts

Each run carries an `assessment_run_id`. Logical identity uses a
`repository_id` (for example `github-<owner>-<repo>` or `local-<safe-name>`).
Portfolio Engineering Intelligence artifacts use a parallel layout:

```text
.codestrata-artifacts/intelligence/<portfolio_id>/current/
.codestrata-artifacts/intelligence/<portfolio_id>/previous/
```

**Ownership:** local artifacts are under your filesystem control. Product-visible
retention is **current + previous** only. Failed generations do not promote.
Deleting local files is user-controlled and does **not** automatically erase
historical Community Data Lake events or revoke a public report.

**Source locality:** writing `assessment.json` / `assessment.html` does **not**
automatically become Community Cloud telemetry, Data Lake events, or a public
published report. IDE extensions invoke the Engine locally and do not store AI
provider credentials in the extension for Community assessment flows.

Canonical retention detail: [Retention and Deletion](/security/retention-and-deletion).


## Telemetry

Anonymous product telemetry is **disabled by default**. Transmission requires
**explicit consent**. Consent authorizes privacy-safe transmission *eligibility*;
it is **not** permission to publish reports, and it is **not** required for
voluntary public-report Yes/No feedback.

### Privacy-first product consent (authoritative for `assess`)

| Topic | Detail |
| --- | --- |
| Default | `disabled_by_default` — transmission unauthorized |
| Opt in (interactive) | When preference is undecided, eligible interactive assess may prompt; default **No** (`[y/N]`). Yes persists **v2** (usage + assessment insights). |
| Opt in (explicit) | `codestrata telemetry enable` → **v2 Yes** |
| Opt out (explicit) | `codestrata telemetry disable` |
| Session bridge | `codestrata assess --telemetry-allow` is **not** consent — it cannot invent Yes or override Disabled |
| Non-interactive / CI | Never prompts; undecided/disabled stay off; durable v2 may emit without prompting |
| Persistence | Engine-owned preference under `CODESTRATA_HOME` (shared by CLI and VS Code) |

After durable **v2 Yes**, production Community HTTP transport targets
`https://api.codestrata.ai` when `CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL` is set;
otherwise transport stays unavailable. Disabled / undecided sessions never open
HTTP transport for Community collection.

**Legacy v1:** users who previously enabled lifecycle-only telemetry keep that
scope until they accept a one-time upgrade prompt (or run `telemetry enable`).
Decline keeps lifecycle on and assessment intelligence off — never a silent v2
upgrade.

Consent authorizes privacy-safe transmission eligibility. It is **not**
permission to publish reports.

Telemetry / assessment-intelligence failures must not fail assessment or remove
local reports.

### Preference CLI

| Topic | Command |
| --- | --- |
| Status | `codestrata telemetry status` / `status --json` |
| Enable | `codestrata telemetry enable` → **v2 Yes** |
| Disable | `codestrata telemetry disable` |
| Session bridge | `codestrata assess --telemetry-allow` / `--telemetry-deny` (not consent) |

See [Telemetry](/reference/telemetry).

### Voluntary report feedback (separate from telemetry)

Public reports may collect optional **Was this report useful? Yes/No** feedback.
Clicking Yes or No is consent for that feedback event only. No free text, no
login, no repository identity. Insights **Community Sentiment** aggregates only
explicit Yes/No responses. No response does not count as negative.

### Collected when transmission is authorized and transport is wired

Bounded privacy-preserving product signals (usage lifecycle) and, with **v2**
consent, privacy-safe derived assessment intelligence. See
[Telemetry](/reference/telemetry) and
[Community Cloud API](/reference/community-api/).

## Assessment metadata

With **durable v2 consent** and authentication, Community Cloud may accept
**privacy-safe assessment intelligence** — bounded aggregates and closed enums —
via `POST /api/v1/assessment-metadata` (schemas **1.0** and **1.1**).

Distinguish these surfaces carefully:

| Artifact | Where it lives | Contents (summary) |
| --- | --- | --- |
| Local `assessment.json` / `assessment.html` | `.codestrata-artifacts/…` on disk | Full local assessment report artifacts |
| `assessment_metadata` | Community Data Lake stream (v2 consent-gated) | Privacy-safe aggregates / enums — **not** full `assessment.json` or finding prose |
| Published reports | Report Artifact Store + `reports.codestrata.ai` | Explicitly published HTML/JSON for opaque public URLs |
| EIR | Local `intelligence/<portfolio_id>/…` and/or published portfolio reports | Engineering Intelligence report packages — separate from telemetry |

Assessment metadata is **not** a substitute for local reports and is **not** a
public report publish.

## Never collected through Community telemetry

Community product telemetry and assessment-intelligence streams do **not**
collect:

- Source code or repository file contents
- Source snippets / evidence excerpts
- Full `assessment.html` or full `assessment.json`
- Detailed `heads/*.json` payloads as telemetry bodies
- Finding titles, descriptions, recommendation prose, or EIR content bodies
- File paths, repository name/URL/remote
- Credentials, secrets, tokens, or API keys
- Git credential userinfo / similar personal identity fields
- Graph nodes/edges/symbols
- Stack traces / exception strings
- Report ID / report URL
- AI prompts or AI responses **through Community telemetry**

AI enrichment (when enabled) is a **separate** provider path — see
[AI Providers](/ai-providers/). “Not collected by telemetry” does not mean
“never sent to an AI provider.”

Full Data Collection page: [Data Collection](/security/data-collection).

**Installation identifier:** CodeStrata may use a **random (pseudonymous)
installation UUID** so Insights can distinguish first vs repeat assessments. It
is not derived from machine, user, or repository identity. Prefer
“pseudonymous installation identifier” — do not claim absolute anonymity.
Insights must not show raw installation IDs in the UI.

Observable request/response contracts (including fields intentionally not
transmitted) are documented at [Community Cloud API](/reference/community-api/).
Telemetry-related ingest routes require authentication and client-enforced
consent. Anonymous writes return `401`.

## Community Data Lake

The Community Data Lake accepts privacy-safe event streams, including:

- `telemetry`
- `assessment_metadata`
- `cli_event`
- `extension_event`
- `ai_usage`

**Runtime wiring today:** with lifecycle-allowed consent, product **`telemetry`**
is live-wired; with **v2** consent, **`assessment_metadata`** (1.0/1.1) is also
live-wired. `cli_event` / `extension_event` / `ai_usage` retain API/Data Lake
capacity but are not emitted by the current assess path (contract-only /
deferred as documented on [Data Collection](/security/data-collection)).

One assessment that emits both lifecycle telemetry and assessment metadata is
counted **once** in Insights Total/Successful/Failed authorities.

The Data Lake is **not** the Report Artifact Store. It does **not** store
`assessment.html`, full `assessment.json`, EIR report bodies, or public report
HTML as Data Lake objects.

## Published reports

Publishing a detailed Assessment or Engineering Intelligence report requires an
**explicit** publish/share action (for example
`codestrata report publish --confirm-public-publish`). Telemetry opt-in alone
**never** publishes a report.

Published reports:

- Use opaque URLs: `https://reports.codestrata.ai/r/<id>`
- Are viewable by **anyone with the URL** (no public directory / listing)
- Live in a **private Report Artifact Store**, separate from the Community Data Lake
- Follow **current / previous** retention per repository (assessment) or portfolio (EIR)
- Support authenticated **revoke** via
  `DELETE /api/v1/reports/<public-id>` (public GET becomes **404**; local
  artifacts are untouched). There is no Engine CLI `report revoke` command in
  the current surface — see [Community Cloud API](/reference/community-api/)
  and [Retention and Deletion](/security/retention-and-deletion)

Local reports remain authoritative on disk whether or not you publish.


## AI providers

AI enrichment is **optional**. Deterministic assessment (`--no-ai`) is the
default and does not call providers.

With `--with-ai`, the Engine may send a **compact enrichment context** to **your**
configured provider (Bedrock, OpenAI, or OpenRouter). That path is **not**
Community telemetry and does **not** upload full repository source trees.
Bounded evidence path/excerpt clips may be included in the compact context.

Provider prompts/responses are **not** mirrored into Community telemetry.
Assess-path `ai_usage` emission remains deferred/construction-only in v0.2.0.

Canonical detail:

- [AI Providers](/ai-providers/)
- [Source Locality](/security/source-locality)

## Retention (separate systems)

Canonical detail: [Retention and Deletion](/security/retention-and-deletion).

| System | Retention posture |
| --- | --- |
| Local assessment / intelligence artifacts | **current + previous** per logical identity |
| Community Data Lake `raw/` | About **365 days** (configured Data Lake lifecycle default) |
| Community Data Lake `quarantine/` | About **90 days** (where quarantine objects exist) |
| Community Data Lake `identity/` | **Indefinite** by current intentional design (dedup / aggregation) |
| Report Artifact Store (published) | Application-enforced **current + previous** |

The Data Lake is **not** a current/previous product model. Local reports are
**not** retained for 365 days by product policy — only current + previous.

Opting out of telemetry does **not** erase historical Data Lake events and does
**not** automatically revoke already-published reports.

## Opt-out and deletion

Canonical detail: [Retention and Deletion](/security/retention-and-deletion).

- `--telemetry-deny`, interactive No, or `codestrata telemetry disable` stops
  **future** product transmission (explicit No is stored locally; process flags
  override without rewriting preference when used).
- Opt-out does **not** auto-delete historical Community Data Lake events.
- Opt-out does **not** auto-revoke published report URLs.
- Opt-out does **not** erase Data Lake identity objects (no self-service identity
  deletion API today).
- Revoke a published report with authenticated
  `DELETE https://api.codestrata.ai/api/v1/reports/<public-id>` when you intend
  to withdraw a public link.
- Delete local artifacts yourself under `.codestrata-artifacts/` when you intend
  local removal.

## Document map

| Concern | Canonical page |
| --- | --- |
| Overall privacy commitments | This page |
| What stays local vs leaves | [Source Locality](/security/source-locality) |
| Exact collected streams/fields | [Data Collection](/security/data-collection) / [Collected Fields](/security/collected-fields) |
| Consent / transport | [Telemetry](/reference/telemetry) |
| Retention / opt-out / revoke / deletion capabilities | [Retention and Deletion](/security/retention-and-deletion) |
| AI provider data flow | [AI Providers](/ai-providers/) |
| Community Cloud architecture | [Community Cloud](/architecture/community-cloud) |
| Data Lake / Insights | [Data Lake](/architecture/data-lake) · [Insights](/architecture/insights) |

## Contact

Use the process in [Responsible Disclosure](./disclosure) / `SECURITY.md`.
Do not open public issues containing secrets or private repository details.
