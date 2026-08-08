# Community Insights Event Coverage (Slice 15.3)

Authoritative **data coverage** contract for Community Insights Dashboard metrics.
Baselines: `community-data-lake-policy:1.0`, `community-analytics-partition-policy:1.0`.

## Decision summary

| Topic | Result |
| --- | --- |
| Path redesign | **Not required** (15.2 stands) |
| Schema activation in 15.3 | **Forbidden** |
| Most metrics | Supported from existing fields |
| Named package ecosystems | Deferred additive change (`CR-15.3-001`) |
| OpenRouter provider family | Deferred catalog entry (`CR-15.3-002`) |
| AI model adoption | **Outcome C** — `model_family` only; exact `model_id` forbidden |
| Validation dataset growth | **external_metric_source** (`validation/repository-catalog/`) |
| Privacy vs dashboard | Privacy wins |

## Installation identity

- Field: `payload.installation_id` (optional on all five streams)
- Engine: UUID v4 in `~/.codestrata/anonymous-installation-identity.json`
- VS Code Epic 10: identity-free locally
- Do **not** count installations as raw event counts
- Do **not** redesign identity in 15.3

## Assessment success / failure

Authoritative: `payload.assessment.assessment_status` and `payload.execution.result`.  
**Not** authoritative: `open_report`, missing report artifact flags.

## VS Code usage

Stream `extension_event`. Usage operations: `assess`, `assess_with_ai`.  
`activate` alone does **not** count as usage.

## Change register

Machine-readable future changes only — **not** activated in runtime in 15.3.
Owned for implementation/hardening by Slice **15.4**.

**Policy:** `community-insights-event-coverage-policy:1.0`
