---
title: Community Data Lake
description: Append-oriented privacy-safe Community analytics store — raw, quarantine, identity, retention, and separation from report storage.
---

# Community Data Lake

Canonical architecture for the **Community Data Lake** — the private,
append-oriented analytics store behind optional Community telemetry / metadata
ingestion and Insights aggregates.

Related:

- [Community Cloud Architecture](/architecture/community-cloud)
- [Insights](/architecture/insights)
- [Data Collection](/security/data-collection)
- [Retention and Deletion](/security/retention-and-deletion)
- [Telemetry](/reference/telemetry)

## What it is

| Topic | Posture |
| --- | --- |
| Role | Append-oriented privacy-safe event / metadata store for Community Insights |
| Access | **Private** object storage (no public listing / public anonymous lake access) |
| Encryption | Server-side encrypted private bucket posture |
| Versioning | Enabled for operational recovery |
| Orientation | **Not** a current/previous product slot model |

**Community Data Lake ≠ Report Artifact Store.** Report HTML/JSON bodies are not
lake objects.

## Prefix classes

| Prefix / class | Purpose | Retention (configured) |
| --- | --- | --- |
| `raw/` | Accepted privacy-safe events | ~**365 days** |
| `quarantine/` | Quarantine objects when written | ~**90 days** |
| `identity/` | Dedup / aggregation continuity objects | **Indefinite** by current intentional design |

Partitioning (accepted events) follows stream / schema / date layout under
`raw/` (Hive-style stream and date prefixes). Exact key formats are
implementation detail; public docs do not require internal bucket names.

## What belongs here

Privacy-safe Community event streams / metadata, including capacity for:

- `telemetry`
- `assessment_metadata`
- `cli_event`
- `extension_event`
- `ai_usage`
- quarantine / identity classes as designed

**Producer honesty (v0.2.1 assess path):** product **`telemetry`** is **ACTIVE**
after lifecycle-allowed consent + credential; **`assessment_metadata`** is
**ACTIVE_WITH_V2_CONSENT** (schemas 1.0 + 1.1). Other streams may have API/lake
capacity without current assess emission. See
[Data Collection](/security/data-collection).

Lake objects are **derived metadata**, not source repositories. Accepted amd
records use server `accepted_at` / day partition — clients do not need to send
execution timestamps for assessment intelligence.

## What does NOT belong here

- `assessment.html` / full `assessment.json`
- `heads/*.json` payloads
- EIR HTML/JSON bodies
- Public report bodies
- Repository source code
- AI prompts / responses
- Credentials / API keys

Those boundaries align with Slice 18.1/18.2 never-collected and destination
registers.

## Quarantine / reject-before-persist

Live ingestion may **reject** invalid or privacy-invalid HTTP requests **before**
accepted persistence (client error responses).

Quarantine retention applies where quarantine objects are written. Do **not**
assume every rejected HTTP event is stored as a quarantine object.

## Identity layer

| Topic | Behavior |
| --- | --- |
| Purpose | Deduplication, aggregation correctness, installation continuity |
| Identifier style | Privacy-safe / random installation identifier when present |
| Retention | Indefinite by current intentional design |
| Insights UI | Must **not** show raw installation IDs |
| Self-service deletion | Not implemented in v0.2.0 |

Public examples must not use real installation identifiers.

## Writer / reader separation

| Role | Intent |
| --- | --- |
| Ingestion writer | Bounded write into designed lake prefixes |
| Insights reader | Bounded read of accepted `raw/` for aggregates |
| Public clients | No direct lake access |

No public documentation of policy ARNs or account IDs is required for this
transparency page.
