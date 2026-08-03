# Recurring Evidence-Backed Patterns

Platform-only detection of deterministic conditions that recur across two or more
repositories in a selected assessment dataset.

> Recurring patterns describe repeated deterministic conditions within the
> selected assessed dataset. They do not establish industry prevalence,
> organizational maturity, business impact, or a required portfolio action.

## Purpose

Answer which rules, configuration conditions, dependency conditions, complexity
conditions, recommendation intents, or technology *conflicts* recur across
repositories — with explicit denominators, confidence, and provenance.

## Recurrence versus duplication

- One repository with many Findings for the same rule is **not** recurrence.
- Recurrence requires distinct repository presence.
- Within-repository Finding correlations (Slice 5.12) are not recurring patterns.

## Identity

Pattern ID: `pattern:{sha256[:24]}` from Slice 6.1
`build_pattern_id`, which currently includes:

- pattern type
- normalized subject
- rule IDs / assessment-head IDs
- **sorted repository IDs**
- policy version

Consequence: the pattern ID changes when repository membership changes.
Logical subject keys (for example `rule:{head}|{rule_id}`) are stable in
`normalized_subject`. A future migration may separate logical identity from
membership; this slice does not break the Slice 6.1 contract.

Never uses titles, statements, counts, severity, confidence, or AI similarity.

## TechnologyDistribution boundary

Ordinary technology prevalence belongs in `TechnologyDistribution`.
Recurring technology patterns are emitted only for **cross-repository conflicting
version declarations** under explicit policy.

## Priority Action / roadmap

Priority Action patterns are deferred: aggregated PA facts lack a stable
cross-repository action-intent identity (`action_id` is repository-local).
Roadmap patterns are deferred (phase alone is not a technical pattern).

## Modernization boundary

This slice does not create modernization observations or portfolio
Recommendations / Priority Actions.

## Confidence

Pattern confidence answers how strongly the dataset establishes recurrence.
It is not Finding Confidence, severity, prevalence, or final report confidence.

## Report identity follow-up

Pattern policy is section-local (`policy_token` / pattern `policy_version`).
Before Slices 6.10/6.11, fold all interpretation-policy versions into report
identity.
