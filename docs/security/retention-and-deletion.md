---
title: Retention and Deletion
description: Canonical CodeStrata Community retention, opt-out, revoke, and deletion capability documentation for v0.2.0.
---

# Retention and Deletion

Canonical Community Edition page for **how long data is kept**, **what opt-out
changes**, and **what users can delete or revoke today**.

This page is **product** retention/deletion transparency — not the corporate
legal notice at [codestrata.ai/privacy](https://codestrata.ai/privacy).

Authority: Slice 18.1 retention / opt-out / destination registers, Epic 17
report retention policy, Data Lake and Report Artifact Store lifecycle
configuration, and current Community Cloud revoke runtime.

Related:

- [Privacy](/security/privacy) — overall product privacy commitments
- [Data Collection](/security/data-collection) — what can leave the machine
- [Telemetry](/reference/telemetry) — consent and transport behavior
- [Collected Fields](/security/collected-fields) — field inventory
- [Community Cloud API](/reference/community-api/) — publish / revoke contracts

## Document roles

| Page | Role |
| --- | --- |
| [Privacy](/security/privacy) | Overall behavioral commitments and boundaries |
| [Data Collection](/security/data-collection) | Exact streams / field categories |
| [Telemetry](/reference/telemetry) | Consent / runtime transport behavior |
| **This page** | Storage duration, opt-out scope, revoke, deletion capabilities |

Do not invent product capabilities that are not implemented.

## Local data ownership

Local products live under your filesystem:

```text
.codestrata-artifacts/
  assessments/<repository-id>/
    current/
    previous/
  intelligence/<portfolio-id>/
    current/
    previous/
```

| Topic | Behavior |
| --- | --- |
| Control | Local artifacts are under **your** filesystem control |
| Product-visible versions | **current + previous** only |
| Failed generations | Do **not** promote into `current` / `previous` |
| Local deletion | User-controlled (delete files/directories yourself) |
| Cloud coupling | Local deletion does **not** erase historical Community Data Lake events |
| Public reports | Local deletion does **not** revoke a public report unless you invoke revoke |

CodeStrata Cloud does **not** remotely delete your local `.codestrata-artifacts/`
tree.

`assessment_run_id` and similar run identifiers are **metadata** on artifacts —
not a separate top-level product storage identity beyond the
`repository-id` / `portfolio-id` + current/previous slots.

## Local Assessment retention

| Class | Retention |
| --- | --- |
| Local Assessment | **current + previous** only |

Older successful generations are rotated out of product-visible slots when a new
assessment promotes. This is **not** the Community Data Lake 365-day window.

## Local Engineering Intelligence (EIR) retention

| Class | Retention |
| --- | --- |
| Local EIR | **current + previous** only |

Same product-visible slot model as assessments, under
`.codestrata-artifacts/intelligence/<portfolio-id>/`.

## Published report retention

Published Assessment and EIR packages live in the **Report Artifact Store**
(private object storage), exposed publicly only via opaque URLs on
`https://reports.codestrata.ai/r/<id>`.

| Class | Product-visible retention |
| --- | --- |
| Published Assessment | **current + previous** (application-enforced) |
| Published EIR | **current + previous** (application-enforced) |

When a **third** successfully published logical version arrives:

1. Newest becomes **current**
2. Former current becomes **previous**
3. Oldest is retired / made inaccessible as a public product version

Retired public URLs are **intentionally disposable**: opening a previously
returned `https://reports.codestrata.ai/r/<id>` for a version that is no longer
**current** or **previous** returns **404**. That is retention policy, not a
routing failure. A successful publish response alone does not prove an older
URL remains reachable.

**S3 object versioning** (when enabled) is **operational recovery history**.
It is **not** the same as product-visible public report history
(`current` + `previous`).

Abandoned staging uploads expire on a short operational schedule (about
**2 days** in current Report Artifact Store lifecycle configuration).

## Report revocation

Authenticated revoke:

`DELETE https://api.codestrata.ai/api/v1/reports/<public-id>`

(requires Community client credentials / owner principal)

After revoke, public fetch of that opaque id returns **404** (product access
withdrawn). There is **no** end-user CLI `report revoke` command in the current
Engine surface — use the authenticated Community API revoke path documented in
[Community Cloud API](/reference/community-api/).

Revoke does **not**:

- Delete local Assessment artifacts
- Delete local EIR artifacts
- Delete historical Community Data Lake telemetry
- Delete unrelated current/previous published reports for other identities

Revoke withdraws **product public access** for that public id. Do not read it as
a promise of total backend erasure of every operational copy or versioned
recovery object.

## Telemetry / Data Lake retention

The Community Data Lake is **append-oriented**. It is **not** a current/previous
product slot model.

| Prefix / class | Current configured retention | Evidence |
| --- | --- | --- |
| Data Lake `raw/` (accepted events) | About **365 days** | Data Lake lifecycle `accepted_retention_days` default |
| Data Lake `quarantine/` | About **90 days** | Data Lake lifecycle `quarantine_retention_days` default |
| Data Lake `identity/` | **Indefinite** by current intentional design | No object-expiration rule on `identity/` (Epic 17.22 / 18.1) |

These values are **telemetry / lake** retention — not local report retention and
not published report current/previous retention.

### Identity retention rationale

Identity objects support:

- Deduplication
- Aggregation correctness
- Installation continuity for privacy-safe analytics

Automatic **self-service deletion** of Data Lake identity objects is **not**
currently implemented. Prefer wording such as “random installation identifier”
/ “privacy-safe client installation identifier” — do not claim “anonymous
forever.”

### Quarantine semantics

Live Community ingest may **reject** invalid or privacy-invalid HTTP requests
**before** accepted persistence (for example schema / privacy validation
failures returning client errors).

**Quarantine** retention (~90 days) applies where quarantine objects are
written under the Data Lake quarantine prefix. Do **not** assume every rejected
HTTP request is stored as a quarantine object.

## Opt-out (telemetry)

Current privacy-first opt-out:

```bash
codestrata assess … --telemetry-deny
```

(or interactive Deny / remaining at the disabled default)

| Topic | Behavior |
| --- | --- |
| Effect | Stops **future** consent-governed telemetry according to preference / process flags |
| Persistence | Explicit Yes/No is stored locally; `--telemetry-deny` is a process override |
| Scope | Local preference under `CODESTRATA_HOME` (CLI) / extension `globalState` (VS Code) |

Opt-out does **not** automatically:

- Delete historical Data Lake events
- Erase identity records
- Delete local reports under `.codestrata-artifacts/`
- Revoke public reports
- Delete Report Artifact Store data already published

## Historical telemetry after opt-out

Events already accepted into the Community Data Lake **before** opt-out remain
subject to **Data Lake lifecycle** (raw ~365 days; quarantine ~90 days where
present; identity indefinite by current design).

There is **no** end-user self-service historical telemetry deletion API in
v0.2.0. This page does not invent one.

## Telemetry consent vs report publish

| Decision | Authorizes |
| --- | --- |
| Telemetry opt-in (`--telemetry-allow` / interactive allow) | Privacy-safe Community ingest eligibility for that process/command |
| Explicit Publish/Share (`codestrata report publish --confirm-public-publish`) | Uploading selected Assessment/EIR artifacts to the Report Artifact Store |

These are **different** consent decisions.

Opting out of telemetry later does **not** automatically revoke an already
published report. Report revoke is a **separate** authenticated action.

## Data destination retention matrix

Conceptual service names only (no internal bucket identifiers required for
transparency).

| Data class | Location | Created when | Retention | User action | Public? | Deletion / revoke |
| --- | --- | --- | --- | --- | --- | --- |
| Local Assessment | `.codestrata-artifacts/assessments/…` | Successful assessment | current + previous | Delete local files | No | User-controlled local delete |
| Local EIR | `.codestrata-artifacts/intelligence/…` | Successful EIR generation | current + previous | Delete local files | No | User-controlled local delete |
| Data Lake raw | Community Data Lake `raw/` | Accepted privacy-safe ingest after opt-in + auth | ~365 days | Opt-out stops future only | No | No self-service wipe |
| Data Lake quarantine | Community Data Lake `quarantine/` | When quarantine objects are written | ~90 days | n/a | No | Lifecycle expiration |
| Identity | Community Data Lake `identity/` | Identity/dedup path when used | Indefinite (intentional) | n/a | No | No self-service deletion |
| Published Assessment | Report Artifact Store + opaque URL | Explicit publish | current + previous | Authenticated revoke | Opaque URL | Revoke → public 404 |
| Published EIR | Report Artifact Store + opaque URL | Explicit publish | current + previous | Authenticated revoke | Opaque URL | Revoke → public 404 |
| Secrets / credentials | Operator secret store | Operational provisioning | Operator rotation lifecycle | n/a (operators) | No | Operator rotation/deletion |
| Validation evidence | Local/CI validation suites | Verification runs | Separate from product current/previous | Operator/CI cleanup | No | Not product report retention |

## Deletion capability matrix

| Capability | Status (v0.2.0) |
| --- | --- |
| Delete local artifacts | **Supported** — user deletes under `.codestrata-artifacts/` |
| Revoke public report | **Supported** — authenticated `DELETE /api/v1/reports/<public-id>` |
| Opt out of future telemetry | **Supported** — `--telemetry-deny` / deny / default off |
| Self-service delete historical Data Lake events | **Not implemented** |
| Self-service delete Data Lake identity objects | **Not implemented** |
| Secrets rotation / deletion | **Operator-managed** (not end-user telemetry control) |

“Not implemented” here is an honest capability statement — not a product defect
unless a release promise claimed otherwise.

## Secrets / credential privacy boundary

Relevant for privacy transparency only:

- Community authentication secrets are **operational credentials**, not telemetry payloads
- Insights dashboard password verifier is stored as an operational secret
- Provider API keys are **not** Community telemetry and are not written into local Assessment/EIR report bodies
- Rotation / deletion of secrets is **operator security** behavior

This page does not publish secret names, ARNs, or values.

## AI provider retention boundary

AI provider requests are **separate** from CodeStrata Community telemetry.

Retention of prompts/context at third-party AI providers is governed by
**provider / account terms and configuration**, not by Community Data Lake
retention. This page does **not** speculate about provider retention periods.

Details: [AI Providers](/ai-providers/) (Slice 18.4 expands provider data-flow
documentation).

## Never-collected regression (telemetry)

Community telemetry still does **not** collect repository source, report
HTML/JSON bodies, AI prompts/responses **through telemetry**, or credentials as
telemetry. See [Data Collection](/security/data-collection) and
[Privacy](/security/privacy).

## Production availability note

Retention values above describe **current configured** Community production
posture for v0.2.0. Runtime contracts and infrastructure remain authoritative if
wording ever conflicts.
