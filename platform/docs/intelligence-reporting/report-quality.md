# Report Confidence and Dataset Limitations (Slice 6.8)

Platform-only derivation of commercial Engineering Intelligence Report confidence
and structured dataset limitations.

## Meaning of report confidence

Report confidence describes the **strength and comparability of the structured
assessment evidence supporting this report**. It is **not**:

- an accuracy percentage
- Precision or Recall
- a probability that the report is correct
- an average of repository confidence values
- repository health, maturity, readiness, risk, or business confidence
- Recommendation priority
- evidence completeness alone
- dataset size alone

> Report confidence describes the strength and comparability of the structured
> assessment evidence supporting this report. It is not an accuracy percentage,
> a repository score, or a guarantee that all technical conditions were detected.

> The selected dataset determines the scope of every observation. Results must
> not be generalized beyond that dataset without additional evidence.

## Weakest-material-support policy

Confidence uses **weakest material support with explicit caps**:

1. Source assessment-head confidence (canonical head confidence, not Finding confidence)
2. Dataset comparability
3. Dataset coverage status
4. Material section denominator availability
5. Sample size thresholds
6. Schema/methodology compatibility
7. Legacy / incomplete source presence

Ordinal confidence values are **never averaged**. Disabled and not-applicable
heads are not treated as failures. Non-material unavailable heads add
disclosures without necessarily capping the whole report.

## Material versus optional sections

Material by default:

- dataset / repository population
- Technology Distribution
- Capability Comparison
- Assessment-Head Distribution

Optional / dependent:

- Recurring Patterns
- Modernization Observations

An honestly empty recurring-pattern or modernization section does **not**
automatically reduce report confidence. Unavailable denominators for a populated
material section may cap confidence.

## Coverage and comparability

Coverage uses canonical Assessment Coverage statuses
(`complete` / `partial` / `insufficient_evidence` / `unavailable` / `disabled`).
Coverage is not inferred from Finding counts and area percentages are not
averaged across heads.

Comparability uses repository- and head-level comparability from dataset
ingestion/aggregation. Excluded repositories do not enter sample counts.

## Sample size

Sample size is explicit but is not statistical certainty:

- zero included repositories → unavailable
- one repository → limited/unavailable for cross-repository reports
- small samples under policy threshold → confidence cap
- larger samples do not automatically produce High

## Source diversity and selection bias

Diversity interpretation depends on report scope:

| Scope | Representation concentration |
| --- | --- |
| Public OSS / demonstration | Material limitation |
| Customer portfolio | Often informational (describes the portfolio) |
| Internal validation | Controlled-fixture presence must be explicit |

Public OSS and internal validation scopes require selection-bias disclosure:
the dataset is curated/validation-driven, not random, and must not be treated
as industry prevalence.

## Dataset limitations

`DatasetLimitation` objects use interpretation severity
(`material` / `moderate` / `minor` / `informational`) — not Finding Severity.

Categories include sample size, coverage, confidence, schema/methodology,
legacy sources, missing revisions, language/ecosystem representation,
controlled fixtures, selection bias, section support, and the mandatory
**non-temporal dataset** disclosure (cross-sectional snapshot; not a trend).

Section-local limitations remain on their sections. Report-level promotion
deduplicates equivalent structured subjects and does not concatenate prose.

## Interpretation policy bundle and report identity

`IntelligenceInterpretationPolicyBundle` folds technology, capability,
recurring-pattern, modernization, report-quality, repository-drilldown, and
website-export policy tokens plus catalog and statement-template versions into a
deterministic `interp-bundle:{sha256[:24]}`.

Report identity (`eir:{sha256[:24]}`) includes:

- dataset ID
- report schema version
- report scope
- assessment run identities
- report policy version
- interpretation-policy bundle ID (when present)

Same dataset + same bundle → same report ID. Changing any interpretation policy
component changes the bundle ID and therefore the report ID. Dataset IDs and
Engine entity IDs remain unchanged. Empty/absent bundle IDs preserve pre-6.8
identity material for deserialization compatibility. EIR schema remains **1.0**.

## APIs

```python
from codestrata_platform.intelligence_reporting.application.report_quality import (
    ReportQualityPolicy,
    build_report_quality,
    populate_report_quality,
)

result = build_report_quality(report, aggregation, policy=ReportQualityPolicy())
report = populate_report_quality(report, aggregation)
```

## Explicit non-goals

- Repository drill-downs (Slice 6.9)
- HTML / website export / OSS demonstration report
- Community Edition multi-repo reporting
- Engine analyzer/rule/Finding/Recommendation changes
- AI / LLM / RAG / Knowledge Graph inference
- Validation Precision/Recall as report confidence
- Maturity / health / readiness / ranking / composite scores

## Assessment age

Assessment-age evaluation is **deferred** when timestamps are not consistently
present (`assessment_age_policy = deferred_without_consistent_timestamps`).
When implemented later, tests must use a fixed reference time; wall-clock time
must not enter report identity.
