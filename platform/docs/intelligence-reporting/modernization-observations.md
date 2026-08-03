# Evidence-Backed Portfolio Modernization Observations

Platform-only synthesis of repeated deterministic repository-level actions into
bounded `ModernizationObservation` objects.

> Modernization observations summarize repeated deterministic repository-level
> actions within the selected assessed dataset. They are not portfolio
> Recommendations, delivery commitments, ROI claims, or transformation plans.

## Purpose

Answer which deterministic modernization actions recur across repositories,
with Recommendation → Finding → Evidence provenance, denominators, and
confidence.

## Authority

An observation requires deterministic action support — typically equivalent
Recommendations in at least two repositories. Recurring Finding patterns may
support an observation only through a reviewed pattern→action catalog and never
alone.

## Action identity

```
modernization-action:{provider-or-none}:{category}:{head}
```

Never uses title, summary, priority, count, or AI similarity.

## Observation identity

`obs:{sha256[:24]}` from Slice 6.1 `build_observation_id`, which currently
includes repository IDs and Recommendation/PA ID membership. Logical
`normalized_subject` is the stable action identity. Future migration may
separate logical identity from membership (same follow-up as recurring patterns).

## Boundaries

| Source | Role |
| --- | --- |
| TechnologyDistribution | Descriptive prevalence only — not observation authority |
| CapabilityComparison | Denominator/limitation context only |
| Recurring patterns | Support via reviewed catalog when Recommendations exist |
| Engine Recommendations/PAs/roadmaps | Canonical action authority |

## Non-goals

No portfolio Recommendation/PA/roadmap, ROI, cost, staffing, timeline, urgency
score, implementation plan, HTML, website export, or OSS report.
