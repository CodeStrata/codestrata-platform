# Acceptance Notes — Security Context Classification

**Branch:** `feature/security-context-classification`  
**Nature:** Precision layer for security findings (no detector removal)

## Problem

VS Code precision audit (86 secret-related findings):

| Classification | Count |
| --- | ---: |
| REAL / LIKELY | 0 |
| FALSE_POSITIVE | 71 |
| TEST_FIXTURE | 12 |
| MOCK_CREDENTIAL | 3 |

Detectors recalled secret-like patterns, but reporting lacked repository context.

## Solution

Introduce `SecurityEvidenceContext` between detection and presentation:

- Classify path + value (CI expressions, schema metadata, lockfiles, tests, mocks, production)
- Demote severity/confidence for non-actionable contexts
- Keep all matches (recall preserved)
- Leadership surfaces skip informational / non-actionable context findings

## Expected precision improvements (VS Code profile)

| Pattern | Before | After (reporting) |
| --- | --- | --- |
| `${{ secrets.* }}` in workflows | HIGH credential-literal | INFORMATIONAL / CI expression |
| package.json `apiKey` schema fields | HIGH | INFORMATIONAL / configuration schema |
| package-lock `@octokit/auth-token` | HIGH | INFORMATIONAL / dependency metadata |
| Fixture `$(github-distro-mixin-password)` | HIGH | INFORMATIONAL / CI expression or fixture |
| SEC* in secretFilter / env tests | HIGH/CRITICAL | INFO / mock or test |
| Production literal credentials | HIGH/CRITICAL | Unchanged |

## Validation results (concrete)

### 1. Microsoft VS Code (`validation/typescript-vscode.toml`)

| Metric | Before `20260729-082446` | Mid `20260730-061625` | After `20260730-062724` |
| --- | ---: | ---: | ---: |
| `security.credential-literal` matches | 80 | 80 | 80 |
| Security findings (all summaries) | 81 | 81 | 81 |
| HIGH+CRITICAL (all) | 80 | 39 | **0** |
| credential-literal HIGH | 80 | 39 | **0** |
| credential-literal INFORMATIONAL | 0 | 41 | **80** |

**After demotion breakdown** (`security-assessment.json` all_finding_summaries, by Context label):

| Context | Severity | Count |
| --- | --- | ---: |
| CI secret reference | informational | 48 |
| Configuration schema | informational | 27 |
| Dependency metadata | informational | 5 |
| production (`security.debug-enabled`) | medium | 1 |

- **Recall:** credential-literal match count still **80** (unchanged vs before).
- **Precision:** HIGH+CRITICAL for credential-literal **0** (expect near 0; no SEC* leftovers in security-assessment all summaries — SEC* appear only on the broader `findings.json` surface).
- Audit baseline (`_audit_vscode_secret_findings.json`): 86 secret findings, 86 HIGH+CRITICAL → now 0 HIGH+CRITICAL on secret-like security-assessment findings.

### 2. Spring PetClinic (`validation/java-spring-petclinic.toml`)

Prior run `20260730-061646`:

| Metric | Value |
| --- | ---: |
| Security findings (all / primary) | 0 / 0 |
| HIGH+CRITICAL | **0** |

No regression: still zero security HIGH.

### 3. CodeStrata self (`validation/reports/codestrata-self/.../20260730-061659`)

Prior run (not re-run):

| Metric | Value |
| --- | ---: |
| Security findings (all / primary) | 43 / 19 |
| HIGH+CRITICAL | **17** |
| INFORMATIONAL | 23 |
| Context mix | Production source 17, Documentation 23, production 2, unknown 1 |

Self-repo keeps production HIGH where appropriate; documentation demoted to informational.

## Verify checklist

- Production detections remain high/critical when truly production
- Leadership report emphasizes actionable findings
- Detector match counts are not reduced (demotion only)

## Audit reference

`docs/internal/security-detector-precision-audit-vscode.md`  
Precision helper: `docs/internal/_precision_vscode_security_context.py` (points at `20260730-062724`)
