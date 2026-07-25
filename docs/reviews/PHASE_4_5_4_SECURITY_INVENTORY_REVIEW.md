# Phase 4.5.4 — Security Assessment Inventory Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-5-4/` (gitignored)  
**Pack:** `security.core` **1.0.0** (unchanged)  
**Assessment schema:** `security-assessment` **1.2.0**  
**Evidence schema:** `repository-sensitive-evidence` **1.1.0** (unchanged)

## Recommendation

**Accept Phase 4.5.4.** Security assessment organizes in-memory
repository-sensitive evidence and shared hygiene Findings into deterministic
inventories, hotspots, diagnostics, limitations, and bounded traceability.
No synthesis, conclusions, recommendations, scores, or report integration.
Repeated artifacts are byte-identical. Zero findings does **not** imply either
repository is secure.

## Production-primary contract

| Field | Behavior |
| ----- | -------- |
| `finding_ids` / `finding_summaries` | Production source role only |
| `all_finding_ids` / `all_finding_summaries` | All roles including unknown |
| Unknown role | Explicit; never promoted to production |

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Evidence status | `succeeded` |
| Rules registered / executed | 8 / 8 |
| Production findings | **0** |
| All findings | **0** |
| Findings by source role | production 0 / test 0 / unknown 0 |
| Findings by rule | all eight rules at 0 |
| Category / severity inventories | empty (no findings) |
| Hotspot count | 0 |
| Evidence diagnostics | 0 |
| Rule diagnostics | 0 |
| Limitations | 10 |
| Repeat-run artifact | **byte-identical** (`sha256 e6aa5446…`) |
| Schema | `security-assessment` **1.2.0** |

Manual: complete zero-count rule inventory retained; evidence coverage retained;
no claim that CodeStrata is secure.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `partially_succeeded` (evidence partial) |
| Evidence status | `partially_succeeded` |
| Rules registered / executed | 8 / 8 |
| Production findings | **0** |
| All findings | **0** |
| Findings by source role | production 0 / test 0 / unknown 0 |
| Findings by rule | all eight rules at 0 |
| Hotspot count | 0 |
| Evidence diagnostics | **2** (`malformed_yaml`) — **not** Findings |
| Rule diagnostics | 0 |
| Limitations | 10 |
| Repeat-run artifact | **byte-identical** (`sha256 6c277c41…`) |

Manual: Spring `${VAR:default}` passwords remain non-literal; malformed YAML
stays in evidence diagnostics; status correctly reflects partial evidence
rather than “failed because zero findings.”

## Synthetic precision scenarios (unit tests)

Covered in `tests/application/security/assessment/test_security_inventory.py`:

- production / test / unknown finding partitions
- multi-finding and mixed-rule hotspot ranking (production first; max 20)
- partially_succeeded from evidence and from isolated rule failure
- failed when all rules fail
- succeeded with zero findings
- no raw private-key / absolute-path leakage
- shuffled Finding input → byte-identical serialization

## Manual reconciliation and leakage review

| Check | Result |
| ----- | ------ |
| Count reconciliation (dogfood) | Pass (all zeros + 8×0 rule inventory) |
| Production-primary separation | Pass (synthetic) |
| Hotspot inspection | Pass (synthetic multi-path; dogfood empty) |
| No raw sensitive material | Pass |
| Diagnostics ≠ Findings | Pass (Petclinic malformed YAML) |
| Zero-result wording bounded | Pass (limitations + hotspot note) |
| Evidence schema still 1.1.0 | Pass |
| Pack / rule behavior unchanged | Pass (`security.core` 1.0.0) |

## Explicit limitations / deferred

No synthesis, conclusions, recommendations, scores, CTO report, CLI/MCP,
CVE/OWASP, SAST/DAST, secret validity, certificate trust, keystore decryption,
Git history, entropy analysis, or new scanners.

## Confirmation

- Additive schema only: **1.1.0 → 1.2.0**
- No second Security finding model
- No re-collection / re-parse / re-run of rules during inventory
- Architecture / Technical Debt / Dependency behavior untouched
- No git commit
