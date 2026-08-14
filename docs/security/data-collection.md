---
title: Data Collection
description: What CodeStrata Community Edition can send off your machine — stream status, destinations, never-collected guarantees, and field inventory.
---

# Data Collection

Canonical answer to:

**What exactly can CodeStrata send off my machine?**

Authority: Slice 18.1 machine-readable inventories + Community Cloud runtime
schemas. Documentation is not authority when it conflicts with runtime.

Related:

- [Telemetry](/reference/telemetry) — consent and transport behavior
- [Collected Fields](/security/collected-fields) — full 137-field reference
- [Privacy](/security/privacy) — product privacy authority
- [Retention and Deletion](/security/retention-and-deletion) — retention / opt-out / revoke
- [Community Cloud API](/reference/community-api/)

## Short answer

By default, CodeStrata sends **nothing** off your machine for Community product
telemetry.

After **explicit opt-in** and with a Community client credential, the Engine may
send **privacy-safe metadata** to `https://api.codestrata.ai`. It does **not**
send repository source, full Assessment/EIR report bodies, findings evidence, or
credentials through Community telemetry.

Separately, if you configure optional AI enrichment, your chosen provider may
receive bounded enrichment context — that is **not** Community telemetry
(see [AI Providers](/ai-providers/)).

## Stream status (v0.2.1 honesty)

Community Cloud registers five ingest streams. **Do not assume all five are
actively emitted** by the current Engine assess path.

| Stream | Endpoint | Producer status (v0.2.1) | Consent | Destination | Insights use |
| --- | --- | --- | --- | --- | --- |
| `telemetry` | `POST /api/v1/telemetry` | **ACTIVE** after lifecycle-allowed consent (v1 or v2) + credential | Required | Community Data Lake `raw/` | activity / adoption aggregates |
| `assessment_metadata` | `POST /api/v1/assessment-metadata` | **ACTIVE_WITH_V2_CONSENT** after durable v2 Yes + credential (schemas 1.0 + 1.1) | Required (v2) | Community Data Lake `raw/` | assessments / coverage / technology (no double-count with lifecycle) |
| `cli_event` | `POST /api/v1/cli-events` | **NOT_EMITTED_BY_CURRENT_ASSESS_PATH** (API + lake capacity exist) | Required | Community Data Lake `raw/` | activity / adoption |
| `extension_event` | `POST /api/v1/extension-events` | **CONTRACT_ONLY** (no fabricated producer traffic) | Required | Community Data Lake `raw/` | adoption (when present) |
| `ai_usage` | `POST /api/v1/ai-usage` | **DEFERRED** on assess path (construction-only; no prompts/responses) | Required | Community Data Lake `raw/` | AI aggregates (when present) |

Report publish routes (`/api/v1/reports…`) are **not telemetry**. They require
separate explicit Publish/Share confirmation.

## What each ACTIVE / capacity stream is for

### `telemetry` (ACTIVE after opt-in)

Purpose: bounded anonymous product signals (client name/version/platform bands,
event type, optional coarse properties).

Producer: Engine / CLI product HTTP transport after allow + credential.

### `assessment_metadata` (ACTIVE with v2 consent)

Purpose: privacy-safe derived assessment intelligence — executed heads, aggregate
counts, approved rule/severity/category patterns, head confidence, bounded
failure category, and categorical repository characteristics.

**Not** full `assessment.json`, `assessment.html`, `heads/*.json`, finding prose,
source, paths, repository identity, graph data, or report IDs/URLs.

### `cli_event` / `extension_event` / `ai_usage`

Purpose: privacy-safe CLI / extension / AI **usage metadata** contracts.
`extension_event` remains contract-only. `ai_usage` assess-path emission is
deferred for v0.2.0 and never includes prompts or responses via telemetry.

## Field categories

Full field inventory (137 fields across ingest + report-publish request models):

→ [Collected Fields](/security/collected-fields)

Fields are grouped by API event. Report-publish fields describe explicit publish
packages — not automatic telemetry.

## What CodeStrata does not collect (telemetry)

These guarantees apply to **Community telemetry / Community ingest streams** and
are runtime-backed (Slice 18.1 never-collected register).

CodeStrata Community telemetry does **not** collect:

- Repository source code
- File contents
- Full local `assessment.html`
- Full local `assessment.json`
- Detailed `heads/*.json` payloads
- Complete findings / evidence payloads
- Engineering Intelligence HTML/JSON bodies
- Credentials / API keys
- Git credential userinfo
- AI prompts **through telemetry**
- AI responses **through telemetry**
- Local absolute paths where label validators prohibit them
- Raw S3 / object paths (public report URLs are opaque)
- Raw machine identifiers (MAC / hardware serials) — installation identity is a
  **random UUID v4**, not derived from machine properties

### Careful wording about AI

**“Not collected by CodeStrata telemetry”** is different from **“never sent to
an AI provider.”**

If you enable optional AI enrichment, bounded context may go **directly** to
your configured provider (Bedrock / OpenAI / OpenRouter). That provider path is
documented under [AI Providers](/ai-providers/) and is outside Community
telemetry.

## Consent vs publish

| Action | Authorizes |
| --- | --- |
| Telemetry opt-in | Privacy-safe Community ingest eligibility for that process/command |
| Explicit Publish/Share | Uploading selected Assessment/EIR artifacts to the Report Artifact Store |

Telemetry opt-in alone **never** publishes a report.

## Installation / client identity

See [Telemetry — Pseudonymous installation identifier](/reference/telemetry#pseudonymous-installation-identifier).

Summary: random UUID v4 installation identifier may exist locally for analytics
continuity (first vs repeat); Insights must not show raw ids.

## Data destinations

```text
Developer machine
    ↓ explicit telemetry opt-in (+ credential)
https://api.codestrata.ai
    ↓ auth + privacy validation
Community Data Lake  (append-oriented privacy-safe events)
    ↓ bounded aggregation
Insights (authenticated operators)
```

Separately:

```text
Developer machine
    ↓ explicit Publish/Share confirmation
Report Artifact Store
    ↓ opaque public id
https://reports.codestrata.ai/r/<id>
```

| Store | Purpose |
| --- | --- |
| Local `.codestrata-artifacts/` | Assessment / EIR products (current + previous) |
| Community Data Lake | Privacy-safe event streams for Insights |
| Report Artifact Store | Explicitly published report packages |
| AWS Secrets Manager | Operator/runtime secrets (not telemetry payloads) |

**Community Data Lake ≠ Report Artifact Store.** Report HTML/JSON is not
telemetry.

## Telemetry retention (this page’s scope)

| Class | Duration / semantics |
| --- | --- |
| Data Lake `raw/` | About **365 days** |
| Data Lake `quarantine/` | About **90 days** |
| Data Lake `identity/` | **Indefinite** by current intentional design (anonymous dedup) |

Broader cross-system retention (published reports, local slots, secrets) is
covered on [Privacy](/security/privacy) and later Transparency slices. This page
does **not** invent automatic identity deletion.

## Opt-out scope (telemetry)

Opt-out / deny stops **future** consent-governed telemetry for that
process/command.

It does **not** automatically:

- Delete historical Data Lake events
- Revoke public reports
- Delete local reports under `.codestrata-artifacts/`
- Erase installation identity files

Full retention / deletion matrix: [Retention and Deletion](/security/retention-and-deletion).

## Sanitized request example (product telemetry)

Synthetic values only — validate against Community telemetry schema concepts:

```json
{
  "schema_version": "1.0",
  "event_id": "00000000-0000-4000-8000-000000000001",
  "event_type": "feature_completed",
  "client": {
    "name": "codestrata_cli",
    "version": "0.2.0",
    "platform": "macos"
  },
  "properties": {
    "feature": "assess",
    "operation": "run",
    "outcome": "succeeded",
    "duration_bucket": "30s_to_2m"
  }
}
```

### Sanitized response example

```json
{
  "status": "accepted",
  "safe_event_reference": "evt_synth_0001",
  "retry_status": "first_seen",
  "schema_version": "1.0"
}
```

Notes for network inspectors:

- Production host is `api.codestrata.ai`
- Ingest requires authentication headers (never paste real credentials into docs)
- Optional `installation_id` may appear on some schemas; examples omit it unless
  illustrating the optional field
- Rejected privacy-invalid bodies do not become accepted lake objects
- Successful acknowledgements do not echo installation IDs, fingerprints, or
  raw storage paths

## Production availability checklist

Telemetry leaves the machine only when:

1. Explicit opt-in for the process/command
2. Valid Community client credential
3. Reachable `https://api.codestrata.ai`

Otherwise assessment and local reports still work offline / with telemetry off.
