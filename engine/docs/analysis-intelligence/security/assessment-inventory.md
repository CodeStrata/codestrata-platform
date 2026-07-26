# Security Assessment Inventory (Phase 4.5.4)

Schema: `security-assessment` **1.3.0** (`security-assessment.json`).

Deterministic inventory projection over platform repository-sensitive evidence
and shared `security.*` Findings, plus Phase 4.5.5 deterministic synthesis.
**No** composite scores, CVE/OWASP fields, or CTO report integration.

## Contract

Consumes (does not re-collect or re-evaluate):

1. In-memory `AggregatedRepositorySensitiveEvidence`
2. Shared `Finding` objects already emitted by `security.core`

### Production-primary vs all findings

| Field | Scope |
| ----- | ----- |
| `finding_ids` / `finding_summaries` | **Production** source role only |
| `all_finding_ids` / `all_finding_summaries` | Production + test/fixture + unknown |

Unknown-role findings are never treated as production. Test and fixture share
the inventory `test` role.

### Inventories

- `evidence_summary` — bounded coverage counters (signatures ≠ Findings)
- `evidence_type_inventory` — artifact / configuration fact type counts
- `finding_inventory` — role-partitioned finding counts
- `rule_inventory` — every registered Security rule, including zero findings
- `category_inventory` / `severity_inventory` / `confidence_inventory`
- `hotspot_inventory` — path concentration (max 20); presentation order only
- `diagnostics_summary` — evidence / rule / assessment diagnostics (**not** Findings)

### Hotspot presentation ordering (not a priority score)

1. production finding count descending
2. total finding count descending
3. highest observed severity
4. normalized path ascending

Neutral wording only (`Security finding hotspot`). Does **not** assert risk,
vulnerability, or that a file is critical.

### Diagnostics separation

| Origin | Examples |
| ------ | -------- |
| Evidence | malformed YAML, unsupported binary, size limit |
| Rule | isolated evaluation failure |
| Assessment | inventory assembly notes |

Diagnostics never become Findings.

### Lifecycle / status precision

Status reflects collection and evaluation completeness, **not** finding
presence:

| Condition | Status |
| --------- | ------ |
| Pack / section disabled | `disabled` / `not_requested` |
| Rules on, evidence unavailable | `insufficient_evidence` |
| Evidence + rules succeeded (including zero findings) | `succeeded` |
| Evidence partially succeeded with usable facts | `partially_succeeded` |
| Some rules failed | `partially_succeeded` |
| All required rule evaluation failed | `failed` |

Zero findings must not be phrased as “passed,” “secure,” or “no vulnerabilities.”

### Traceability

Bounded edges: assessment → finding → evidence ID / hotspot. Cap follows
`MAX_TRACEABILITY_ENTRIES`. No raw values or absolute paths.

### Privacy

- no raw credential values
- no private-key content
- no absolute paths
- no redacted-preview reversal

## Configuration

```toml
[evidence.repository_sensitive]
enabled = false

[rules.security]
enabled = false

[assessment.sections.security]
enabled = false
```

No synthesis, scoring, threshold, or `report.sections.security` knobs in this
phase.

## Deferred

Presentation-only report adapter, CLI/MCP surfaces, CVE/SAST/DAST, certificate
trust, keystore decryption, and new scanning rules. Synthesis is documented in
[synthesis.md](synthesis.md).
