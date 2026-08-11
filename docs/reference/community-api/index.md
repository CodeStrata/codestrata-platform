---
title: Community Cloud API
description: Observable request and response contracts for the CodeStrata Community Cloud API at api.codestrata.ai.
---

# Community Cloud API

Public production authority:

`https://api.codestrata.ai`

Developers can inspect CodeStrata network requests from CLI or VS Code and compare
them directly with the documented request and response contracts on this page.

The raw AWS `execute-api` hostname is an implementation detail and is **not** the
public API contract.

## Route groups (v0.2.0)

Derived from the runtime route inventory (18 routes). Architecture overview:
[Community Cloud Architecture](/architecture/community-cloud).

| Group | Routes | Auth |
| --- | --- | --- |
| Public Community | `GET /health`, `GET /community/status`, `GET /reports/{public_id}` | None |
| Authenticated ingestion | `POST /telemetry`, `/assessment-metadata`, `/cli-events`, `/extension-events`, `/ai-usage` | Community client credential + consent |
| Report publishing | `POST /reports/upload-intents`, `POST /reports`, `POST /reports/{public_id}/verification`, `DELETE /reports/{public_id}` | Community client credential + eligibility/confirm |
| Private Insights | `/insights/auth/*`, `/insights/api/*` (incl. validation-reports) | Insights operator session — **not** public Community API |

### Producer honesty (ingestion)

| Stream endpoint | Current assess-path status |
| --- | --- |
| `POST /api/v1/telemetry` | **ACTIVE** after explicit opt-in + credential |
| `POST /api/v1/assessment-metadata` | **NOT_EMITTED_BY_CURRENT_ASSESS_PATH** |
| `POST /api/v1/cli-events` | **NOT_EMITTED_BY_CURRENT_ASSESS_PATH** |
| `POST /api/v1/extension-events` | **CONTRACT_ONLY** |
| `POST /api/v1/ai-usage` | **DEFERRED** (not an AI provider proxy) |

Ingestion / publish failures do **not** fail local assessment. Payloads go to the
Community Data Lake (ingestion) or Report Artifact Store (publish) — never treat
the lake as report storage.

## Transparency

Community Cloud ingestion endpoints accept only privacy-safe metadata. CodeStrata
does **not** transmit:

- source code
- repository contents
- repository file paths
- assessment findings or evidence
- prompts or AI responses
- API keys or credentials
- exact model IDs where prohibited
- VS Code `machineId`

Telemetry and related events remain **consent-gated** and **off by default** for
product transmission.

## Authentication

Ingestion routes require Community client credentials (fingerprint-verified).
Never embed long-lived secrets in public repositories. Health is public.

## Endpoints

### Health

| Field | Value |
| --- | --- |
| Method | `GET` |
| URL | `https://api.codestrata.ai/api/v1/health` |
| Auth | none |
| Consent | n/a |

**Purpose:** Liveness and version probe.

**When called:** Operator smoke checks, deploy validation, client startup probes.

**Response `200` example:**

```json
{
  "api_version": "v1",
  "application_version": "0.2.0",
  "schema_version": "1.0",
  "service": "codestrata-community-cloud-api",
  "status": "ok"
}
```

### Community Status

| Field | Value |
| --- | --- |
| Method | `GET` |
| URL | `https://api.codestrata.ai/api/v1/community/status` |
| Auth | none (public read-only) |
| Consent | n/a |

**Purpose:** Safe public Community Edition metadata for website and operators.
Public GitHub metadata for `CodeStrata/codestrata-engine` drives repository
identity, URL, star count, and the published release version once available.

**Engine version source:** latest **published** GitHub Release tag for
`CodeStrata/codestrata-engine` (non-draft, non-prerelease), normalized
(`v0.2.0` → `0.2.0`). The installed package `codestrata.__version__` is an
internal consistency check only. Before a matching published GitHub Release
exists, the endpoint falls back to the runtime/package candidate version
(`version_source=release_candidate` for verification only — not exposed on the
public wire).

**GitHub repository / URL / stars:** fetched server-side from the public GitHub
repository API (`full_name`, `html_url`, `stargazers_count`) and cached
in-process with a bounded TTL (`Cache-Control: public, max-age=…`).
Browsers must not call GitHub directly and must never embed a GitHub token.

**Failure behavior:** if GitHub is temporarily unavailable, the endpoint still
returns `200` with last-known cached metadata when available; otherwise
`github_stars: null`, candidate `engine_version`, and `status: "degraded"`.

**Response `200` example:**

```json
{
  "cache_age_seconds": 12,
  "engine_version": "0.2.0",
  "github_repository": "CodeStrata/codestrata-engine",
  "github_stars": 1304,
  "github_stars_source": "live",
  "github_url": "https://github.com/CodeStrata/codestrata-engine",
  "schema_id": "community-status",
  "schema_version": "1.0",
  "status": "ok"
}
```

Does **not** expose AWS account IDs, Lambda versions, S3 bucket names, secrets,
GitHub credentials, or internal `version_source` classification.

Private Insights report-registry APIs are **not** part of the public Community
API surface.

### Telemetry

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/telemetry` |
| Auth | Community client credentials |
| Consent | required for product transmission |

**Purpose:** Anonymous technical product telemetry.

**Required headers:** `Content-Type: application/json`, `Accept: application/json`,
plus Community authentication headers required by the current client contract.

**Representative privacy-safe request:**

```json
{
  "schema_version": "1.0",
  "event_id": "01PLACEHOLDEREVENTID000000",
  "installation_id": "01PLACEHOLDERINSTALL0000",
  "occurred_at": "2026-08-09T20:00:00Z",
  "event_type": "feature_used",
  "client": {
    "name": "cli",
    "version": "0.2.0",
    "platform": "darwin"
  },
  "properties": {
    "feature": "assess",
    "operation": "run",
    "outcome": "success"
  }
}
```

**Does not include:** source, paths, findings, prompts, responses, secrets.

**Responses:** `202` accepted; `400` schema/privacy rejection; `401`/`403` auth;
`429` rate limited; `503` sink unavailable.

### Assessment metadata

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/assessment-metadata` |
| Auth | Community client credentials |
| Consent | required |

**Purpose:** Bounded assessment metadata (not findings/evidence/HTML).

**Does not include:** repository contents, findings, evidence, report HTML.

### CLI events

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/cli-events` |
| Auth | Community client credentials |
| Consent | required |

**Purpose:** Privacy-safe CLI lifecycle/adoption events.

### Extension events

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/extension-events` |
| Auth | Community client credentials |
| Consent | required (command-local in VS Code) |

**Purpose:** Privacy-safe VS Code extension events.

**Does not include:** `machineId`, workspace contents, source, findings.

### AI usage metadata

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/ai-usage` |
| Auth | Community client credentials |
| Consent | required |

**Purpose:** Privacy-safe AI usage metadata (provider family / coarse usage).

**Does not include:** prompts, responses, API keys, exact model IDs where prohibited.

**Not an AI proxy:** This Community Cloud route does **not** forward prompts to
Bedrock, OpenAI, or OpenRouter. Provider enrichment calls go **directly** from
the Engine to the configured provider. In v0.2.0, assess-path emission of
`ai_usage` remains **construction-only / deferred** — capacity exists; do not
assume every `--with-ai` run posts here. See [AI Providers](/ai-providers/) and
[Source Locality](/security/source-locality).

### Report publishing (Slice 17.16)

Report publishing is **explicit**. Telemetry opt-in is a prerequisite for
eligibility; it does **not** automatically publish detailed assessments.

Reports are stored in a **private Report Artifact Store**, not the Community
Data Lake. Public URLs are branded and opaque:

`https://reports.codestrata.ai/r/<public-report-id>`

Raw S3 URLs are never returned as public share links.

#### Upload intent

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/reports/upload-intents` |
| Auth | Community client credentials |
| Consent | telemetry opt-in required (client-enforced eligibility) |

**Purpose:** Create a short-lived staging upload session with server-chosen keys
and temporary PUT URLs (not public report URLs).

**Request example:**

```json
{
  "schema_version": "1.0",
  "report_type": "assessment",
  "logical_identity_type": "repository",
  "logical_identity_key": "github-example-org-example-repo",
  "artifacts": ["assessment.html", "assessment.json"],
  "private_repository_acknowledged": true,
  "confirm_public_publish": true
}
```

**Response `201` (shape):** `upload_id`, temporary `puts[].upload_url`,
`expires_in_seconds`. Staging URLs must not be shared as report links.

#### Publish (finalize)

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/reports` |
| Auth | Community client credentials |

**Request example:**

```json
{
  "schema_version": "1.0",
  "upload_id": "UPLOAD_ID_FROM_INTENT",
  "confirm_public_publish": true,
  "private_repository_acknowledged": true
}
```

**Response `201` example:**

```json
{
  "api_version": "v1",
  "public_id": "OPAQUE_PUBLIC_REPORT_ID",
  "public_url": "https://reports.codestrata.ai/r/OPAQUE_PUBLIC_REPORT_ID",
  "report_type": "assessment",
  "slot": "current",
  "status": "published",
  "retention": {
    "max_versions": 2,
    "note": "current+previous only; S3 versioning is ops recovery"
  }
}
```

Cloud retention mirrors local lifecycle: current + previous only per repository
(assessment) or portfolio (EIR). A third publish revokes the oldest public id.

#### Verification confirm (temporary validation registry)

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/reports/<public-id>/verification` |
| Auth | Community client credentials |

After an independent public GET of `https://reports.codestrata.ai/r/<id>`
succeeds, the Engine confirms verification so the **private** validation
registry can mark the entry verified. This registry is temporary internal
Community validation tooling — not public, not enumerable on
`reports.codestrata.ai`, and removable without changing opaque URL contracts.
Authenticated Insights operators browse it via
`GET /api/v1/insights/api/validation-reports`.

#### Public fetch

| Field | Value |
| --- | --- |
| Method | `GET` |
| URL | `https://api.codestrata.ai/api/v1/reports/<public-id>` |
| Auth | none (only after explicit publish) |

Also available via branded shell:

`https://reports.codestrata.ai/r/<public-id>`

Optional: `?format=json` for JSON download. Cache is bounded so revoke can take
effect (`Cache-Control: private, max-age=60, must-revalidate`).

Oversized HTML may be delivered via a temporary presigned redirect. Responses
still carry `X-CodeStrata-Public-Id` so clients can prove identity without
downloading the entire document.

#### Voluntary report feedback (not telemetry)

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `https://api.codestrata.ai/api/v1/reports/<public-id>/feedback` |
| Auth | none (published reports only) |

Body: `{ "useful": true }` or `{ "useful": false }`. Separate from telemetry
consent. No free text, repository paths, or source content. Also reachable via
the branded shell at `https://reports.codestrata.ai/r/<public-id>/feedback`.

#### Revoke

| Field | Value |
| --- | --- |
| Method | `DELETE` |
| URL | `https://api.codestrata.ai/api/v1/reports/<public-id>` |
| Auth | Community client credentials (owner) |

After revoke, public GET returns `404`. Local artifacts are untouched.

## Retry behavior

Clients use short timeouts and bounded retries (typically at most two attempts)
for transient network failures. Schema/auth rejections are not retried as success.

## Insights note

The Insights dashboard browser contract remains same-origin:

`https://insights.codestrata.ai/api/v1/...`

Insights administrative routes are **not** Community APIs and are not documented
here.

## Related

- [Telemetry](/reference/telemetry)
- [Privacy](/security/privacy)
- [CLI](/reference/cli)
- [VS Code](/extensions/vscode)
- [Community API overview](/reference/api)
