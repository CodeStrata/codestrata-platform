# Cross-Repository Aggregation Foundation

Platform-only factual aggregation over one `IntelligenceDataset`.

> This aggregation layer produces factual cross-repository inputs. It does not
> create recurring-pattern conclusions, portfolio recommendations, or industry
> benchmarks.

## Purpose

`aggregate_intelligence_dataset(...)` reads included normalized assessment
snapshots and their canonical Engine report documents, then builds
`CrossRepositoryAggregation`:

- repository / assessment indexes
- technology, head, finding, recommendation, PA, roadmap, correlation facts
- coverage / confidence facts (preserved, not recomputed)
- explicit denominators
- repository population counts
- diagnostics

It does **not** produce capability comparison
presentation, modernization observations, drill-downs, HTML,
or OSS demonstration reports. Recurring-pattern detection is Slice 6.6
(see [recurring-patterns.md](./recurring-patterns.md)).

## Counting rules

| Count | Meaning |
| --- | --- |
| `repository_count` | Distinct included repositories |
| `occurrence_count` | Entity rows (may exceed repository count) |
| repository presence | Distinct repos contributing to an observation |

Never divide entity count by repository count and call it repository prevalence
without an explicit repository-presence numerator. Never average percentages or
confidence levels.

## Denominators

`AggregationDenominator` scopes include all-included, comparable-only, and
per-head available/activated/evaluated sets. Zero denominators are
**unavailable** — not artificial 0% / 100%.

## Composite identity

Entity IDs are unique within a source assessment. Cross-repository identity is:

`(repository_id, assessment_id, entity_type, entity_id)`

Same entity IDs from different repositories remain distinct. Engine IDs are never
regenerated or merged.

## Legacy / incomplete

Policy:

- `exclude` — omit from aggregation facts
- `limited` — include with `legacy_limited` markers; missing collections are not zero
- `reject` — fail closed

## Visibility

Explicit only. Public OSS scope rejects non-public inputs. Private display names
and unpublished source refs stay out of public-safe outputs.

## Determinism

Same dataset digests + policy → same `aggregation:{sha256[:24]}`, ordered facts,
counts, denominators, and diagnostics.
