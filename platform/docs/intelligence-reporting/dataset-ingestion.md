# Canonical Assessment Dataset Ingestion

Platform-only application flow that turns multiple Engine assessment `report.json`
documents into one deterministic `IntelligenceDataset`.

> Dataset ingestion preserves canonical Engine assessment identities and
> relationships. It does not rerun analysis, infer missing relationships, or
> create portfolio conclusions.

## Source of truth

The complete Engine assessment report document (schema **1.2**) is authoritative.

The normalized assessment snapshot is a bounded projection:

- IDs, head states, coverage/confidence maps, and safe entity references
- `canonical_report_reference` + `canonical_report_digest`
- no source bodies, snippets, HTML, absolute paths, or secrets

Full report artifacts may remain in Platform artifact storage separately.

## Flow

```
Assessment report sources
→ schema / safety validation
→ ReportJsonParser + traceability validation
→ NormalizedAssessmentSnapshot
→ selection / dedupe (one assessment per repository)
→ comparability evaluation
→ IntelligenceDataset
```

No technology distribution, capability comparison, recurring patterns, or
modernization observations are calculated in this slice.

## Selection policy

`IntelligenceDatasetSelectionPolicy` prefers **explicit assessment-run selection**.

- One included canonical assessment per repository
- Exact duplicate digests are deduped
- Same assessment/run with conflicting digests fails closed
- Same repository with different runs requires `selected_assessment_runs`
- Timestamps are metadata only — never identity

Dataset identity includes the policy token (`policy_id:policy_version`).

## Report digest

`sha256` of stable canonical JSON (`sort_keys=True`). Same report → same digest;
material content changes → different digest.

## Schema compatibility

| Schema | Behavior |
| --- | --- |
| `1.2` complete | Fully comparable candidate |
| `1.0` / `1.1` / incomplete | Legacy/limited; may be included with limitations |
| Future major (`2.x`) | Rejected |

Missing canonical sections produce limitations — Priority Actions, evidence, and
correlations are never fabricated.

## Traceability

Reuses Engine/Platform `ReportJsonParser` + `validate_canonical_assessment`.
Unresolved Evidence → Finding → Recommendation → PA → Roadmap chains fail closed
for complete reports.

## Comparability

`AssessmentComparability` records comparable / partially comparable /
not comparable / unavailable status, schema versions, and per-head compatibility.
A missing head does not invalidate unrelated head comparisons.

## Visibility and website precheck

Visibility is explicit (`public`, `customer_private`, `internal`, `anonymized`).
URL shape is never used to infer visibility.

`WebsiteExportEligibility` is a **precheck only** — no HTML/JSON website export.

## Safety validation

Ingestion rejects absolute paths, `file://` URIs, and secret-shaped customer
fields (`title`, `summary`, `description`, `rationale`, `display_name`,
`repository_url`, `source_reference`).

The Platform privacy gate is **fail-closed**. It does **not**:

- trust text because it originated from Engine
- allow repository-name or Known Issues bypasses
- accept PEM begin fences or credential assignment values

Engine must emit customer-safe descriptive text (see Engine
`customer_safe_text` / redaction). Recognized redacted placeholders such as
`[REDACTED]` / `<redacted>` are allowed as assignment RHS; raw credentials and
PEM markers are not.

Descriptive prose about credential findings (for example “hardcoded credential
detected”, “value redacted”) is not itself a secret and must pass when no
secret *value* is embedded.

Cross-schema compatibility (assessment 1.2 ↔ EI ingestion ↔ EIR 1.0 ↔ website
export 1.0) is verified by System Verification **SV.14**
(`platform/verification/cross_schema_compatibility/`).

## Platform-only boundary

- Engine remains single-repository and does not ingest commercial datasets
- Community CLI has no intelligence-dataset commands
- Public export excludes `platform/**`

