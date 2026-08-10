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

**Source locality:** local artifacts stay on disk you control. Writing
`assessment.json` / `assessment.html` does **not** automatically become
Community Cloud telemetry, Data Lake events, or a public published report.
IDE extensions invoke the Engine locally and do not store AI provider
credentials in the extension for Community assessment flows.

## Telemetry

Anonymous product telemetry is **disabled by default**. Transmission requires
**explicit process/command consent**. Consent authorizes privacy-safe
transmission *eligibility*; it is **not** permission to publish reports.

### Privacy-first product consent (authoritative for `assess`)

| Topic | Detail |
| --- | --- |
| Default | `disabled_by_default` — transmission unauthorized |
| Opt in (interactive) | Eligible interactive assess may prompt once; default **No** (`[y/N]`) |
| Opt in (explicit) | `codestrata assess --telemetry-allow` |
| Opt out (explicit) | `codestrata assess --telemetry-deny` |
| Non-interactive / CI | Never prompts; decision is `non_interactive_disabled` |
| Persistence | **Not persisted** — process/command local only |

After explicit opt-in (`--telemetry-allow` or interactive Yes), the CLI may
resolve the production Community HTTP transport to `https://api.codestrata.ai`
when `CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL` is set. Without a credential,
transport stays unavailable (no anonymous ingestion). Disabled, denied, and
non-interactive sessions never open HTTP transport.

Telemetry failures must not fail assessment or remove local reports.

### Legacy preference CLI (compatibility only)

| Topic | Detail |
| --- | --- |
| Opt in | `codestrata telemetry enable` |
| Opt out | `codestrata telemetry disable` or `CODESTRATA_TELEMETRY=0` |
| Inspect | `codestrata telemetry show` / `codestrata telemetry status` |
| Reset id | `codestrata telemetry reset` |

Legacy `~/.codestrata/telemetry.json` preferences and
`codestrata telemetry enable|disable` are **compatibility-only**. They do
**not** authorize the privacy-first assess runtime.

### Collected when transmission is authorized and transport is wired

Bounded anonymous product signals only (for example version, OS/Python bands,
command name, domain/language categories, size/duration bands, AI enabled/used
flags, success/failure, timestamps). See [Telemetry](/reference/telemetry) and
[Community Cloud API](/reference/community-api/).

## Assessment metadata

When consent and authentication allow it, Community Cloud may accept
**privacy-safe assessment metadata** — bounded counts and closed enums — via
`POST /api/v1/assessment-metadata`.

Distinguish these surfaces carefully:

| Artifact | Where it lives | Contents (summary) |
| --- | --- | --- |
| Local `assessment.json` / `assessment.html` | `.codestrata-artifacts/…` on disk | Full local assessment report artifacts |
| `assessment_metadata` | Community Data Lake stream (consent-gated) | Privacy-safe aggregates / enums — **not** full `assessment.json` |
| Published reports | Report Artifact Store + `reports.codestrata.ai` | Explicitly published HTML/JSON for opaque public URLs |
| EIR | Local `intelligence/<portfolio_id>/…` and/or published portfolio reports | Engineering Intelligence report packages — separate from telemetry |

Assessment metadata is **not** a substitute for local reports and is **not** a
public report publish.

## Never collected through Community telemetry

Community product telemetry and related Community ingest streams do **not**
collect:

- Source code or repository file contents
- Full `assessment.html` or full `assessment.json`
- Findings, evidence, recommendations, or EIR content bodies
- Absolute filesystem paths
- Credentials, secrets, tokens, or API keys
- Git user identity (name/email) or similar personal identity fields
- AI prompts or AI responses

**`installation_id` nuance:** the privacy-first assess runtime does **not**
generate or require an installation id for normal product transmission. Some
Community API stream contracts may accept an `installation_id` when present
(for analytics deduplication). Presence on a wire example does not mean the
assess runtime invents one by default.

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

**Runtime wiring today:** the Engine product HTTP path for opt-in **telemetry**
ingest is the live-wired Community product transmission path. Other streams
have API/Data Lake contract and capacity; their Engine/client producers may be
deferred or unavailable on the assess path.

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
- Support authenticated **revoke** (public GET becomes unavailable; local artifacts are untouched)

Local reports remain authoritative on disk whether or not you publish.

## AI providers

AI enrichment is **optional**. Deterministic assessment (`--no-ai`) is the
default and does not call providers.

With `--with-ai`, the Engine may send a **compact enrichment context** to **your**
configured provider (Bedrock, OpenAI, or OpenRouter), including:

- Repository metadata (display name / identity / file count)
- Compact finding and recommendation summaries
- Evidence refs / path clips (bounded)
- Dependency / technology names and related compact summaries

This is **not** “never sends anything derived from the repository.” It does
**not** upload full repository source trees. Do not interpret compact summaries
as omitting findings from the provider payload.

Provider prompts and responses stay with that provider session and are **not**
mirrored into Community telemetry / Data Lake events. Optional `ai_usage`
analytics remain **construction-only / deferred** on the assess emission path —
not a second live telemetry transport.

Details: [AI Providers](/ai-providers/).

## Retention (separate systems)

| System | Retention posture |
| --- | --- |
| Local assessment / intelligence artifacts | **2 versions** (`current` + `previous`) per logical identity |
| Community Data Lake `raw/` | About **365 days** (provisional / review-required default) |
| Community Data Lake `quarantine/` | About **90 days** (provisional / review-required default) |
| Report Artifact Store (published) | Application-enforced **current + previous** (mirrors local product retention) |

Opting out of telemetry does **not** erase historical Data Lake events and does
**not** automatically revoke already-published reports.

## Opt-out and deletion

- `--telemetry-deny`, legacy disable, or leaving telemetry off stops **future**
  product transmission for that process/command posture.
- Opt-out does **not** auto-delete historical Community Data Lake events.
- Opt-out does **not** auto-revoke published report URLs.
- Revoke published reports with the authenticated report revoke API / CLI flow
  when you intend to withdraw a public link.

## Contact

Use the process in [Responsible Disclosure](./disclosure) / `SECURITY.md`.
Do not open public issues containing secrets or private repository details.
