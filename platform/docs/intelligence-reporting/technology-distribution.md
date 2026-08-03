# Technology Distribution Insights

Platform-only descriptive inventory over `CrossRepositoryAggregation.technology_facts`.

> Technology distributions describe only the repositories with eligible
> Technology Inventory evidence in the selected dataset. They do not establish
> industry popularity, technology quality, support status, or modernization need.

## Purpose

Answer which languages, frameworks, build systems, runtimes, and ecosystems are
present in the assessed dataset — with explicit denominators and version states.

Does **not** claim modernity, support status, security posture, production usage,
standardization need, or industry popularity.

## Counting

| Metric | Meaning |
| --- | --- |
| `repository_count` | Distinct eligible repositories with the technology |
| `occurrence_count` | Fact rows (may exceed repository count) |
| `repository_ratio` | presence / technology-inventory denominator |

Repeated declarations in one repository do not inflate presence.

## Denominator

Uses the aggregation `technology_inventory_available` denominator when present.
Unavailable inventory repositories are listed, not treated as zero technologies.

Zero denominator → ratio unavailable (not 0%).

## Normalization

Versioned explicit alias catalog only (`technology-normalization-v1`).

No fuzzy matching, AI, or package registries. Java ≠ JavaScript; npm ≠ Node.js;
Docker ≠ Kubernetes; .NET ≠ ASP.NET Core.

## Versions

Preserves exact / unavailable / conflicting states from aggregation facts.

Cross-repository version diversity is **not** a conflict. Multiple versions in
one repository remain presence-once with version buckets; explicit conflict
markers are preserved.

## Visibility

Public OSS scope admits only explicit public repository IDs. No URL-based
visibility inference.

## Report integration

Populates `EngineeringIntelligenceReport.technology_distribution` only.
