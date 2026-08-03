# Capability and Assessment-Head Comparison

Platform-only factual comparison across repositories by assessment head.

> Capability comparisons describe the assessed repository/head states within the
> selected dataset. They do not rank repositories, measure engineering-team
> performance, or establish organizational maturity.

## Purpose

For each assessment head, describe:

- which repositories were assessed
- activation versus coverage versus confidence (separate vocabularies)
- Finding / Recommendation / Priority Action counts
- highest calibrated Finding Severity
- comparable versus limited versus excluded repositories
- explicit limitations

## Activation vs coverage vs confidence

| Concept | Meaning |
| --- | --- |
| Activation | Whether the head was activated, available, disabled, or unavailable |
| Coverage | Canonical AssessmentCoverage status (complete / partial / …) |
| Confidence | Canonical Assessment-Head Confidence (high / moderate / limited / unavailable) |

These are never collapsed into a maturity, health, or readiness score.

## Priority Action ownership

Slice 6.5 uses **primary-head ownership**:

- A Priority Action is counted once under the canonical head of its primary
  supporting Recommendation (category → head).
- If no recommendation head is available, the first supporting Finding head is
  used.
- Cross-head PAs do not inflate every supported head.

## Denominators

Comparisons are repository-count based. Eligible repositories follow visibility
policy and head presence. Zero eligible repositories → empty comparison with
`denominator_unavailable` limitation (not a claim that capability is absent).

## Severity

Highest severity uses calibrated Finding Severity for Findings owned by the head.
No Findings → `highest_severity` unavailable/none. No average or weighted risk
score.

## Distribution vs trend

`AssessmentHeadDistribution` is a single-snapshot cross-repository distribution.
It is not a temporal trend and must not use improving/declining language.

## Visibility

Public OSS scope admits only explicit public repository IDs.

## Report identity follow-up

Capability comparison policy is stored on each comparison (`policy_id`) and is
**section-local**, matching Technology Distribution (Slice 6.4). Before final
export (Slices 6.10/6.11), report identity must include a policy-bundle of every
interpretation-policy version (technology + capability + later sections).

## Non-goals

No recurring patterns, modernization observations, final report confidence,
drill-downs, HTML, website export, OSS demonstration report, Precision/Recall,
or Community Edition exposure.
