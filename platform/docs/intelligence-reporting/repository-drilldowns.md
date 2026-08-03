# Repository Drill-Downs (Slice 6.9)

Platform-only bounded navigation from portfolio Engineering Intelligence into
one repository’s supporting assessment results.

> Repository drill-downs provide bounded navigation from portfolio intelligence
> to the canonical repository assessment. They do not replace the complete
> assessment report and do not score or rank repositories.

## Purpose

A `RepositoryIntelligenceDrilldown` answers:

- Which exact repository assessment supports the portfolio report?
- Which technologies were observed (safe names/categories/versions only)?
- What was the state of each assessed capability?
- Which recurring patterns and modernization observations include this repository?
- Which Findings, Recommendations, Priority Actions, and roadmap initiatives
  support those portfolio-level results (bounded subset)?
- What confidence, coverage, and limitations apply to this repository?
- Where can an authorized reader resolve the canonical single-repository report?

## Not a replacement assessment

Drill-downs are **not**:

- a second assessment renderer
- a repository scorecard, maturity score, or ranking
- an executive narrative or source-code browser
- a full Evidence dump
- a portfolio Recommendation or new modernization roadmap

The canonical Engine assessment report remains the source of truth for complete
Findings, Recommendations, Priority Actions, roadmaps, and Evidence.

## Bounded entity references

`SafeEntityRef` carries IDs and safe labels only — no snippets, paths, raw
Evidence, or private URLs. Selection is deterministic (calibrated severity /
priority, then confidence, then stable IDs). Policy limits are explicit;
truncation emits limitations such as `finding_refs_truncated:20/63`.

## Technology summary

Repository-local technology lines are derived from aggregation facts
(`category:name@version`). No modern/outdated/supported claims and no manifest
or path exposure.

## Capability snapshots

`RepositoryCapabilitySnapshot` values from Capability Comparison are reused.
Activation, coverage, confidence, counts, and highest calibrated severity are
preserved. Missing, disabled, unavailable, and legacy states remain distinct.
Zero Findings do **not** imply a healthy repository.

## Pattern and observation membership

Drill-downs list `pattern_id` / `observation_id` values where the repository is
a member. Full pattern/observation objects are not duplicated.

## Confidence and limitations

Drill-down confidence is the weakest material assessment-head confidence among
represented heads — never an average, percentage, or Precision/Recall value.
Limitations cover truncation, legacy/incomplete sources, missing revisions,
visibility, non-temporal snapshot scope, and the requirement to open the
canonical assessment for full Evidence.

## Visibility and anonymization

| Scope | Display behavior |
| --- | --- |
| Public OSS | Public names only when publication is permitted; otherwise stable alias |
| Customer private | Internal display names allowed inside customer-private scope |
| Anonymized | Stable `repository-{sha8}` alias only |
| Internal mixed | Explicit policy; no private identity in public-safe fields |

Website-export eligibility remains a **precheck** (`public_export_eligible`,
`requires_anonymization`, blocking reasons). No HTML export is generated here.

## Canonical assessment reference

Every drill-down carries an opaque logical `canonical_assessment_report_ref`
(and digest). Local paths, signed URLs, and private object-store URLs are
rejected.

## Policy and report identity

`RepositoryDrilldownPolicy` contributes a deterministic token to
`IntelligenceInterpretationPolicyBundle`. Changing the drill-down policy changes
the bundle ID and therefore the report ID. Dataset IDs and Engine entity IDs are
unchanged.

## APIs

```python
from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
    RepositoryDrilldownPolicy,
    build_repository_drilldowns,
    populate_report_repository_drilldowns,
)

result = build_repository_drilldowns(report, aggregation)
report = populate_report_repository_drilldowns(report, aggregation)
```

Recommended populate order after Slice 6.8:

1. technology → capability → patterns → modernization  
2. report quality (include drill-down policy token in the bundle)  
3. repository drill-downs

## Explicit non-goals

- HTML / website export / OSS demonstration report
- Community Edition multi-repo drill-downs
- Engine analyzer/rule/Finding/Recommendation changes
- AI / RAG / Knowledge Graph / source rescans
- Maturity / health / readiness / ranking scores
