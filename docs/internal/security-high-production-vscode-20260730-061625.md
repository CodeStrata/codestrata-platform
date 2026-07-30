# HIGH production / undemoted security findings — VS Code

**Assessment:** `validation/reports/typescript-vscode/vscode/20260730-061625/`
**Generated:** analysis only (print/append); no classifier code changes

## 1. Artifact files

- `ai-readiness-assessment.json` (83565 bytes)
- `architecture-assessment.json` (14023 bytes)
- `architecture_conclusions.json` (6862 bytes)
- `cloud-assessment.json` (44924 bytes)
- `dependency-assessment.json` (62259 bytes)
- `dependency-evidence.json` (68259 bytes)
- `findings.json` (213996 bytes)
- `recommendations.json` (17732 bytes)
- `report.html` (376482 bytes)
- `report.json` (1017135 bytes)
- `repository-ai-readiness-evidence.json` (1021538 bytes)
- `repository-cloud-evidence.json` (46424 bytes)
- `repository-sensitive-evidence.json` (321232 bytes)
- `repository-testing-evidence.json` (2543627 bytes)
- `scan-boundary-diagnostics.json` (1170 bytes)
- `security-assessment.json` (360815 bytes)
- `technical-debt-assessment.json` (112189 bytes)
- `testing-assessment.json` (41665 bytes)
- `graphs/` (assessment-graph, repository-graph, …)

## 2. Grouped counts — HIGH + production / no demotion

From `security-assessment.json` all_finding_summaries: **39** HIGH findings, all labeled `Production source`.

| Path prefix | Count |
|---|---:|
| `.github/` | 39 |

### By audit FP pattern (resolved via value fingerprint)

| Pattern | Count |
|---|---:|
| `gha_secrets_expression` | 35 |
| `gha_permissions_id_token_keyword` | 2 |
| `gha_oidc_step_output_token_expression` | 2 |

### Resolved values (fingerprinted; artifact preview is `[REDACTED]`)

| Value | Count |
|---|---:|
| `${{ secrets.GITHUB_TOKEN }}` | 29 |
| `${{ secrets.VSCODE_OSS }}` | 6 |
| `write` | 2 |
| `${{ steps.oidc.outputs.token }}` | 2 |

### Additional HIGH/CRITICAL from `findings.json` (non-credential-literal, production context)

Count: **2**
- **critical** `SEC002` path=`src/vs/platform/agentHost/node/sshRemoteAgentHostService.ts` ctx=`production` (path-production) preview=`Private key material detected in src/vs/platform/agentHost/node/sshRemoteAgentHo`
- **high** `SEC004` path=`extensions/copilot/src/extension/prompts/node/inline/pythonCookbookData.ts` ctx=`production` (path-production) preview=`Possible hardcoded credential in extensions/copilot/src/extension/prompts/node/i`

## 3. Sample rows (all 39 HIGH credential-literal)

### `.github/` (n=39)

- **path:** `.github/workflows/chat-perf.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_chat_perf_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/chat-perf.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_leak_check_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/chat-perf.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_setup_steps[4]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/component-fixtures.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_screenshots_steps[19]_env_screenshot_service_token`
  - preview: `${{ steps.oidc.outputs.token }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_oidc_step_output_token_expression`
- **path:** `.github/workflows/component-fixtures.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_screenshots_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/component-fixtures.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `permissions_id_token`
  - preview: `write` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_permissions_id_token_keyword`
- **path:** `.github/workflows/copilot-setup-steps.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_copilot_setup_steps_steps[10]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/copilot-setup-steps.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_copilot_setup_steps_steps[4]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/copilot-setup-steps.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_copilot_setup_steps_steps[5]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/copilot-setup-steps.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_copilot_setup_steps_steps[9]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/css-order-scan.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_scan_steps[15]_env_screenshot_service_token`
  - preview: `${{ steps.oidc.outputs.token }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_oidc_step_output_token_expression`
- **path:** `.github/workflows/css-order-scan.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_scan_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/css-order-scan.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `permissions_id_token`
  - preview: `write` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_permissions_id_token_keyword`
- **path:** `.github/workflows/monaco-editor.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_main_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/no-engineering-system-changes.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_main_steps[2]_env_gh_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/no-engineering-system-changes.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_main_steps[3]_env_gh_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/no-engineering-system-changes.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_main_steps[6]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-darwin-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_macos_test_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-darwin-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_macos_test_steps[7]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-darwin-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_macos_test_steps[9]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-linux-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_test_steps[14]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-linux-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_test_steps[4]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-linux-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_test_steps[5]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-linux-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_test_steps[9]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_compile_steps[4]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_compile_steps[8]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_steps[3]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_linux_steps[4]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_macos_steps[3]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-node-modules.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_windows_steps[3]_env_github_token`
  - preview: `${{ secrets.VSCODE_OSS }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-win32-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_windows_test_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-win32-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_windows_test_steps[7]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr-win32-test.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_windows_test_steps[9]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_compile_steps[4]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_compile_steps[8]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_compile_steps[9]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/pr.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_copilot_check_test_cache_steps[6]_env_gh_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/sessions-e2e.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_sessions_e2e_steps[3]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`
- **path:** `.github/workflows/telemetry.yml`
  - rule_id: `security.credential-literal`
  - normalized_key: `jobs_check_metadata_steps[2]_env_github_token`
  - preview: `${{ secrets.GITHUB_TOKEN }}` (artifact redacted_preview=`[REDACTED]`)
  - security_context: `production` / Production source
  - audit_pattern: `gha_secrets_expression`

## 4. Compare to audit (`security-detector-precision-audit-vscode.md`)

Credential-literal demotion status on this assessment:

| Path category | Severity | Context label | Count | vs audit FP |
|---|---|---|---:|---|
| `.github/` | high | Production source | 39 | STILL HIGH (FP) |
| `package.json` | informational | Configuration schema | 27 | demoted OK |
| `extensions/` | informational | Test fixture | 9 | demoted OK |
| `package-lock/` | informational | Dependency metadata | 5 | demoted OK |

### FP patterns still HIGH

- **GHA secrets expressions** (`${{ secrets.GITHUB_TOKEN }}`, `${{ secrets.VSCODE_OSS }}`) — 35 findings — still HIGH / production
- **GHA OIDC step output** (`${{ steps.oidc.outputs.token }}`) — 2 — still HIGH / production
- **GHA permissions.id-token** (`write`) — 2 — still HIGH / production (classifier has a rule, but value arrives as `[REDACTED]`)

### FP patterns no longer HIGH (demoted)

- Extension **package.json apiKey schema** (27) → informational / Configuration schema
- **package-lock** auth-token metadata (5) → informational / Dependency metadata
- Azure pipeline fixture macros / test fixtures (9) → informational / Test fixture
- SEC* mock/test hits in findings.json → low/informational with test/test_fixture context (except new SEC002/SEC004 below)

### Not in original audit table (new production-context hits)

- `SEC002` CRITICAL on `sshRemoteAgentHostService.ts` (OPENSSH PEM marker in production path)
- `SEC004` HIGH on `pythonCookbookData.ts` (`password=hun***er2` cookbook/prompt corpus)

## 5. Top classifier improvements (suggest only)

Root cause for the 39 remaining HIGHs: `security.credential-literal` calls `classify_security_context(..., value=item.redacted_preview)` where preview is always `[REDACTED]`, so existing CI-expression / id-token heuristics never match.

1. **Pass pre-redaction literal (or expression-preserving preview) into the classifier** for credential-literal — already-specified `ci_expression` path. Would demote ~37 expression FPs immediately without touching production secret literals (expressions are not secrets).
2. **Keep / fix `permissions.id-token` demotion when value is a permission keyword** (`write`/`read`/`none`) — rule exists but fails because value is redacted; fix via (1) or key+short-permission heuristic. Demotes 2 more.
3. **Optional:** treat cookbook/prompt corpora and PEM *header-only* matches in SSH client code as non-production or documentation/sample when clearly not key material (less clearly specified than CI/schema/lockfile — do not ship without acceptance criteria).

**Not implementing here:** (1) and (2) are clearly safe and match acceptance docs, but this note is analysis-only per request scope; wire-up is a one-field plumbing fix in `rules.py` / evidence collection.

