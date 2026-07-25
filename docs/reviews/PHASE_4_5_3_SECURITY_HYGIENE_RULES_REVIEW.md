# Phase 4.5.3 — Security Hygiene Rules Review

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-5-3/` (gitignored)  
**Pack:** `security.core` **1.0.0**  
**Assessment schema:** `security-assessment` **1.1.0**  
**Evidence schema:** `repository-sensitive-evidence` **1.1.0**

## Recommendation

**Accept Phase 4.5.3.** Security hygiene rules consume only typed
repository-sensitive evidence, emit shared Findings, and assemble
`security-assessment.json` without inventory, synthesis, or report integration.
Repeated artifacts are byte-identical. Zero findings does **not** imply the
repository is secure.

## Rule-pack contract

| Gate | Default |
| ---- | ------- |
| `evidence.repository_sensitive.enabled` | false |
| `rules.security.enabled` | false |
| `assessment.sections.security.enabled` | false |

Rules never invoke evidence collectors. Evidence may run without rules.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Rules executed | 8 |
| Findings | **0** |
| Evidence | 1 artifact (`.env.example`, no sensitive signature), 0 config facts |
| Evidence diagnostics | none |
| Limitations | 9 (hygiene-only + no SAST/CVE/git-history/…) |
| Repeat-run artifact | **byte-identical** |

Manual: no private-key or credential findings; template `.env.example` not
overstated.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Rules executed | 8 |
| Findings | **0** |
| Evidence | 2 password facts (`environment_reference` / interpolation) |
| Evidence diagnostics | `malformed_yaml` ×2 (k8s YAML) — **not** Findings |
| Limitations | 9 |
| Repeat-run artifact | **byte-identical** |

Manual: Spring `${VAR:default}` passwords correctly excluded from
`security.credential-literal`; no raw values in assessment or evidence
artifacts.

## Manual precision and leakage review

| Check | Result |
| ----- | ------ |
| Every finding inspected | N/A (zero findings on both targets) |
| Env references not treated as literals | Pass |
| Public cert ≠ private key | N/A / Pass (no false private-key findings) |
| No raw sensitive values | Pass |
| Malformed YAML remains diagnostic only | Pass |
| Zero findings ≠ “secure” | Pass (limitation text states this) |

## Explicit limitations

No source-code secret regex, entropy, git history, secret validity, certificate
trust/expiry, keystore inspection, CVEs, SAST/DAST, inventories, synthesis,
scores, or CTO report integration.

## Confirmation

- No inventory / hotspots / themes / conclusions / recommendations added
- No report section / CLI / MCP / IntelligencePack abstraction
- No git commit
