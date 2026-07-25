# Phase 4.5.2 — Repository Security-Relevant Evidence Review

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-5-2/` (gitignored)  
**Schema:** `repository-sensitive-evidence` **1.0.0**  
**Artifact:** `repository-sensitive-evidence.json`  
(`codestrata.repository_sensitive_evidence`)

## Recommendation

**Accept Phase 4.5.2.** Platform evidence collects deterministic
repository-visible security-relevant artifact and configuration facts only.
No Security rules, Findings, severity, synthesis, or CTO report integration
were added. Evidence ownership remains platform-scoped
(`[evidence.repository_sensitive]`), not Security-owned.

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Artifact discovery / signatures / config literals | Platform `repository_sensitive` evidence |
| Security interpretation | Deferred (future Security rules) |
| Findings / severity / remediation | Not in this phase |

Collectors do not import `aimf.domain.security` and do not emit Findings.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Candidate artifacts | 1 (`.env.example`) |
| Content classification | `no_supported_sensitive_signature` |
| Configuration facts | 0 |
| Placeholder facts | 0 |
| Metadata-only binaries | 0 |
| Malformed / unsupported diagnostics | none |
| Production / test / unknown | 1 / 0 / 0 |
| Limitations | 10 (standard bounded set) |
| Repeat-run artifact | **byte-identical** |

Manual notes:

- `.env.example` is a template; filename discovery does not imply secrets.
- Commented `AIMF_GITHUB_TOKEN=` does not classify as credential entries.
- `/reports/` inventory noise is excluded by default ignore markers.
- No raw secret values, absolute paths, or PEM bodies in the artifact.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Status | `partially_succeeded` |
| Candidate artifacts | 0 |
| Configuration facts | 2 (`spring_datasource_password` in mysql/postgres profiles) |
| Value kind | `environment_reference` |
| Placeholder status | `environment_interpolation` (`${…:default}` style) |
| Metadata-only binaries | 0 |
| Diagnostics | `malformed_yaml` ×2 (`k8s/db.yml`, `k8s/petclinic.yml` ComposerError) |
| Production / test / unknown artifacts | 0 / 0 / 0 |
| Limitations | 10 |
| Repeat-run artifact | **byte-identical** |

Manual notes:

- Password literals are redacted (`[REDACTED]`); Spring interpolation defaults
  are not serialized in cleartext.
- Public certificates / private keys were not present as candidates.
- Malformed k8s YAML diagnostics are not Findings.

## Manual precision and leakage review

| Check | Result |
| ----- | ------ |
| Private-key classifications inspected | None observed in dogfood targets |
| Credential-entry classifications inspected | None overstated on CodeStrata `.env.example` |
| No raw sensitive values in artifacts/logs | Pass |
| Candidate filenames without content not overstated | Pass |
| Certificates not classified as private keys | N/A (none present) |
| Templates/examples distinguishable | Pass (`.env.example` → no supported signature) |
| Totals reconcile with coverage counters | Pass |

## Explicit non-claims

Artifacts do **not** claim:

- the repository is secure
- values are active secrets
- vulnerabilities exist or do not exist
- severity or remediation

## Explicit limitations (serialized)

Repository snapshot only; no Git history; no runtime environment; no secret
validity verification; no entropy analysis; no external credential validation;
no certificate trust/expiry validation; no keystore decryption; no arbitrary
source-code secret scanning; no vulnerability/compliance interpretation.

## Confirmation

- No Security rules executed by this evidence phase
- No shared Findings emitted by collectors
- No Security synthesis or report integration added
- Architecture / Technical Debt / Dependency gates unchanged in behavior
- No git commit created for this phase
