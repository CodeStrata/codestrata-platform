---
title: Insights Architecture
description: Authenticated Insights dashboard over Community Data Lake aggregates — privacy model, metric families, and bounded reader.
---

# Insights Architecture

Canonical architecture for **CodeStrata Insights**
(`https://insights.codestrata.ai`) — an authenticated operator dashboard over
**bounded aggregates** from the Community Data Lake.

Related:

- [Community Cloud Architecture](/architecture/community-cloud)
- [Data Lake](/architecture/data-lake)
- [Community Cloud API](/reference/community-api/)
- [Privacy](/security/privacy)
- [Source Locality](/security/source-locality)

## High-level path

```text
insights.codestrata.ai
  → authenticated UI
  → same-origin / private Insights API routes
  → Community Cloud API (private Insights group)
  → aggregation service
  → bounded Data Lake reader (raw/)
```

## Community Sentiment

Insights metric **Community Sentiment** is based only on explicit voluntary
Yes/No usefulness feedback from public reports. Zero responses displays
**No responses yet** (never `0% Positive`). No AI sentiment inference.

## Authentication

Insights routes are **private** (not public Community API):

- `POST /api/v1/insights/auth/login`
- `POST /api/v1/insights/auth/logout`
- `GET /api/v1/insights/auth/session`
- `GET /api/v1/insights/api/overview`
- `GET /api/v1/insights/api/published-reports`
- `GET /api/v1/insights/api/validation-reports`

Operator authentication uses a password verifier / session model stored as
operational secrets — not end-user telemetry consent.

## Metric families (lake-backed inventory)

Slice 18.1 Insights inventory metric families:

| Family | Nature |
| --- | --- |
| Activity | Aggregate activity signals |
| Adoption | Aggregate adoption signals |
| Assessments | Aggregate assessment metadata signals (when present in lake) |
| Coverage | Aggregate coverage signals |
| Technology | Aggregate technology signals |
| AI | Aggregate AI usage metadata (when present; assess-path `ai_usage` emission is deferred in v0.2.0) |

All are **aggregates**, not raw event browsers. Input streams are privacy-safe
lake events/metadata — not report bodies.

A dashboard **Validation** section (if present) is an operator/external
validation-dataset surface — **not** an additional 18.1 lake metric family in
the inventory register. Do not treat it as a seventh lake stream family.

Category-level note: Activity / Assessments / Adoption / Coverage / Technology /
AI / Validation (UI) may appear together in operator UX copy; only the six
lake-backed families above are inventory metric families.

## Bounded reader / query budget

Insights uses a **bounded** Data Lake reader (list/get budgets and time-window
scoping). When a query approaches budget limits, Insights surfaces a graceful
limitation status rather than unbounded lake scans.

Rationale: reliability, cost control, and privacy-safe operator UX — not raw
event archaeology.

## Insights privacy model

Insights does **not** expose:

- Raw installation IDs
- Raw event payloads as a browse UI
- Repository source code
- Assessment / EIR report bodies
- Raw object-store keys
- Credentials

The **Validation Reports** Insights page (route `/published-reports`) is a
**temporary internal** metadata index over the private Community validation
registry — successfully published reports that passed independent public GET
verification. It is not a Data Lake event browser, not a dump of local
`.codestrata-artifacts/`, and not a permanent Community product capability.
Opaque public URLs remain `https://reports.codestrata.ai/r/<id>` only;
`reports.codestrata.ai` is not enumerable.

The local release file
`.codestrata-artifacts/validation/suites/release-v0.2.0/public-report-urls.json`
is an export/snapshot for deterministic release evidence — the authoritative
production copy is the private AWS validation registry.

## Failure isolation

Insights unavailability does **not** block local assessment, telemetry opt-in
transport design, or local report generation. Empty/partial streams and query
budget limits produce limitations, not a requirement to fail Engine assess.
