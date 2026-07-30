# Security Detector Precision Audit — Microsoft VS Code

**Assessment:** typescript-vscode / 20260729-082446
**Repository:** microsoft/vscode (validation/repos/vscode)
**Scope:** Secret-related findings only (SEC001–SEC004, security.credential-literal)
**Nature:** Investigation only — no code, rule, or suppression changes

## 1. Executive Summary

- 86 secret-related findings reviewed
- 0 REAL_SECURITY_ISSUE / 0 LIKELY_SECURITY_ISSUE
- Precision against "real credential" definition ≈ 0% true positives for live secrets; high rate of intentional test/mock and configuration-metadata FPs
- Primary FP drivers: GitHub Actions secret *expressions*, package.json contribution-point schema fields named apiKey, package-lock dependency names containing "token", Azure pipeline fixture password macros
- Static SEC* rules correctly hit intentional secret-filter / env test fixtures (MOCK/TEST_FIXTURE) — good recall for patterns, wrong severity framing if treated as production breaches

## 2. Findings Statistics

### By classification

| Classification | Count | % of secret findings |
|---|---:|---:|
| REAL_SECURITY_ISSUE | 0 | 0.0% |
| LIKELY_SECURITY_ISSUE | 0 | 0.0% |
| TEST_FIXTURE | 12 | 14.0% |
| MOCK_CREDENTIAL | 3 | 3.5% |
| FALSE_POSITIVE | 71 | 82.6% |
| **Total** | **86** | **100%** |

### By rule

| Rule ID | Count | Classifications |
|---|---:|---|
| `security.credential-literal` | 80 | FALSE_POSITIVE=71, TEST_FIXTURE=9 |
| `SEC003` | 3 | MOCK_CREDENTIAL=2, TEST_FIXTURE=1 |
| `SEC001` | 1 | TEST_FIXTURE=1 |
| `SEC002` | 1 | TEST_FIXTURE=1 |
| `SEC004` | 1 | MOCK_CREDENTIAL=1 |

### By path category

| Path / context category | Count |
|---|---:|
| CI workflow (.github) | 39 |
| Extension package.json schema | 27 |
| Test fixture | 9 |
| Unit/integration test | 6 |
| package-lock metadata | 5 |

### Precision notes

**Definition used here:** a true positive is a finding classified as `REAL_SECURITY_ISSUE` or `LIKELY_SECURITY_ISSUE` among the 86 secret-related findings.

| Metric | Value |
|---|---|
| Secret-related findings (N) | 86 |
| True positives (REAL + LIKELY) | 0 |
| False positives / non-breach classes | 86 |
| Precision (TP / N) | **0.0%** (0/86) |
| Recall note | SEC* patterns fired on intentional unit-test / fixture secret strings (expected for a secret-filter test suite); not counted as TPs under the live-credential definition |

Interpretation: against a “live committed credential” definition, detector precision on this assessment is effectively **0%**. Most volume is `security.credential-literal` over CI expressions, schema metadata, and lockfile rows. The six SEC* hits are pattern-correct on MOCK/TEST_FIXTURE inputs.

## 3. Classification table for every finding

Sorted by classification, then rule ID, then path. Snippets are short/redacted as in the classified JSON.

| # | Rule ID | Secret type | File | Line | Classification | Context | Why detected | Real credential? |
|---:|---|---|---|---:|---|---|---|---|
| 1 | `SEC001` | Sensitive config file (.env) | `extensions/copilot/test/simulation/fixtures/multiFileEdit/issue-9647/.env` | 1 | TEST_FIXTURE | test · role=test · `Repository contains sensitive file: ext…` | SEC001: Sensitive config file (.env) pattern match | No — test fixture |
| 2 | `SEC002` | private-key | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | 76 | TEST_FIXTURE | test · role=test · `-----BEGIN RSA PRIVATE KEY-----` | SEC002: private-key pattern match | No — test fixture |
| 3 | `SEC003` | Google API key | `src/vs/platform/terminal/test/node/terminalEnvironment.test.ts` | 336 | TEST_FIXTURE | test · role=test · `AIz***wQe` | SEC003: Google API key pattern match | No — test fixture |
| 4 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[18]_${{ if ne(parameters_vscode_quality, ` | No — test fixture |
| 5 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[11]_env_github_token` | No — test fixture |
| 6 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[18]_${{ if ne(parameters_vscode_quality, ` | No — test fixture |
| 7 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[18]_${{ if ne(parameters_vscode_quality, ` | No — test fixture |
| 8 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[10]_env_github_token` | No — test fixture |
| 9 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[21]_${{ if and(ne(parameters_vscode_cibuild, true), ne(paramete…` | No — test fixture |
| 10 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[19]_${{ else }}[0]_env_github_token` | No — test fixture |
| 11 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[13]_env_github_token` | No — test fixture |
| 12 | `security.credential-literal` | Pipeline password macro | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | 121 | TEST_FIXTURE | test_fixture · role=test · `$(github-distro-mixin-password)` | credential-literal on key `steps[18]_${{ if ne(parameters_vscode_quality, ` | No — test fixture |
| 13 | `SEC003` | GitHub token | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | 11 | MOCK_CREDENTIAL | test · role=test · `ghp***234` | SEC003: GitHub token pattern match | No — mock/example |
| 14 | `SEC003` | AWS access key | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | 48 | MOCK_CREDENTIAL | test · role=test · `AKI***PLE` | SEC003: AWS access key pattern match | No — mock/example |
| 15 | `SEC004` | Hardcoded credential | `src/vs/platform/terminal/test/node/terminalEnvironment.test.ts` | 302 | MOCK_CREDENTIAL | test · role=test · `CLIENT_SECRET=cli***lue` | SEC004: Hardcoded credential pattern match | No — mock/example |
| 16 | `security.credential-literal` | GHA secrets expression | `.github/workflows/chat-perf.yml` | 133 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_leak_check_steps[3]_env_github_token` | No — FP |
| 17 | `security.credential-literal` | GHA secrets expression | `.github/workflows/chat-perf.yml` | 133 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_setup_steps[4]_env_github_token` | No — FP |
| 18 | `security.credential-literal` | GHA secrets expression | `.github/workflows/chat-perf.yml` | 133 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_chat_perf_steps[3]_env_github_token` | No — FP |
| 19 | `security.credential-literal` | GHA permissions.id-token | `.github/workflows/component-fixtures.yml` | 17 | FALSE_POSITIVE | ci_workflow · role=production · `write` | credential-literal on key `permissions_id_token` | No — FP |
| 20 | `security.credential-literal` | GHA secrets expression | `.github/workflows/component-fixtures.yml` | 54 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_screenshots_steps[3]_env_github_token` | No — FP |
| 21 | `security.credential-literal` | GHA OIDC/token expression | `.github/workflows/component-fixtures.yml` | 209 | FALSE_POSITIVE | ci_workflow · role=production · `${{ steps.oidc.outputs.token }}` | credential-literal on key `jobs_screenshots_steps[19]_env_screenshot_service_token` | No — FP |
| 22 | `security.credential-literal` | GHA secrets expression | `.github/workflows/copilot-setup-steps.yml` | 75 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_copilot_setup_steps_steps[5]_env_github_token` | No — FP |
| 23 | `security.credential-literal` | GHA secrets expression | `.github/workflows/copilot-setup-steps.yml` | 75 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_copilot_setup_steps_steps[10]_env_github_token` | No — FP |
| 24 | `security.credential-literal` | GHA secrets expression | `.github/workflows/copilot-setup-steps.yml` | 75 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_copilot_setup_steps_steps[9]_env_github_token` | No — FP |
| 25 | `security.credential-literal` | GHA secrets expression | `.github/workflows/copilot-setup-steps.yml` | 75 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_copilot_setup_steps_steps[4]_env_github_token` | No — FP |
| 26 | `security.credential-literal` | GHA permissions.id-token | `.github/workflows/css-order-scan.yml` | 11 | FALSE_POSITIVE | ci_workflow · role=production · `write` | credential-literal on key `permissions_id_token` | No — FP |
| 27 | `security.credential-literal` | GHA secrets expression | `.github/workflows/css-order-scan.yml` | 45 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_scan_steps[3]_env_github_token` | No — FP |
| 28 | `security.credential-literal` | GHA OIDC/token expression | `.github/workflows/css-order-scan.yml` | 201 | FALSE_POSITIVE | ci_workflow · role=production · `${{ steps.oidc.outputs.token }}` | credential-literal on key `jobs_scan_steps[15]_env_screenshot_service_token` | No — FP |
| 29 | `security.credential-literal` | GHA secrets expression | `.github/workflows/monaco-editor.yml` | 20 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_main_env_github_token` | No — FP |
| 30 | `security.credential-literal` | GHA secrets expression | `.github/workflows/no-engineering-system-changes.yml` | 123 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_main_steps[2]_env_gh_token` | No — FP |
| 31 | `security.credential-literal` | GHA secrets expression | `.github/workflows/no-engineering-system-changes.yml` | 123 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_main_steps[3]_env_gh_token` | No — FP |
| 32 | `security.credential-literal` | GHA secrets expression | `.github/workflows/no-engineering-system-changes.yml` | 168 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_main_steps[6]_env_github_token` | No — FP |
| 33 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-darwin-test.yml` | 70 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_macos_test_steps[3]_env_github_token` | No — FP |
| 34 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-darwin-test.yml` | 70 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_macos_test_steps[7]_env_github_token` | No — FP |
| 35 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-darwin-test.yml` | 70 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_macos_test_steps[9]_env_github_token` | No — FP |
| 36 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-linux-test.yml` | 86 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_linux_test_steps[4]_env_github_token` | No — FP |
| 37 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-linux-test.yml` | 86 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_linux_test_steps[5]_env_github_token` | No — FP |
| 38 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-linux-test.yml` | 86 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_linux_test_steps[14]_env_github_token` | No — FP |
| 39 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-linux-test.yml` | 86 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_linux_test_steps[9]_env_github_token` | No — FP |
| 40 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_compile_steps[4]_env_github_token` | No — FP |
| 41 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_windows_steps[3]_env_github_token` | No — FP |
| 42 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_macos_steps[3]_env_github_token` | No — FP |
| 43 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_linux_steps[4]_env_github_token` | No — FP |
| 44 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_compile_steps[8]_env_github_token` | No — FP |
| 45 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-node-modules.yml` | 50 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.VSCODE_OSS }}` | credential-literal on key `jobs_linux_steps[3]_env_github_token` | No — FP |
| 46 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-win32-test.yml` | 80 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_windows_test_steps[9]_env_github_token` | No — FP |
| 47 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-win32-test.yml` | 80 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_windows_test_steps[3]_env_github_token` | No — FP |
| 48 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr-win32-test.yml` | 80 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_windows_test_steps[7]_env_github_token` | No — FP |
| 49 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr.yml` | 61 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_compile_steps[8]_env_github_token` | No — FP |
| 50 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr.yml` | 61 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_compile_steps[9]_env_github_token` | No — FP |
| 51 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr.yml` | 61 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_compile_steps[4]_env_github_token` | No — FP |
| 52 | `security.credential-literal` | GHA secrets expression | `.github/workflows/pr.yml` | 238 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_copilot_check_test_cache_steps[6]_env_gh_token` | No — FP |
| 53 | `security.credential-literal` | GHA secrets expression | `.github/workflows/sessions-e2e.yml` | 43 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_sessions_e2e_steps[3]_env_github_token` | No — FP |
| 54 | `security.credential-literal` | GHA secrets expression | `.github/workflows/telemetry.yml` | 21 | FALSE_POSITIVE | ci_workflow · role=production · `${{ secrets.GITHUB_TOKEN }}` | credential-literal on key `jobs_check_metadata_steps[2]_env_github_token` | No — FP |
| 55 | `security.credential-literal` | Lockfile package metadata | `extensions/configuration-editing/package-lock.json` | 23 | FALSE_POSITIVE | lockfile_dependency_metadata · role=production · `>= 18` | credential-literal on key `packages_node_modules_@octokit_auth_token_engines_node` | No — FP |
| 56 | `security.credential-literal` | Lockfile package metadata | `extensions/configuration-editing/package-lock.json` | 23 | FALSE_POSITIVE | lockfile_dependency_metadata · role=production · `^5.0.0` | credential-literal on key `packages_node_modules_@octokit_core_dependencies_@octokit_auth_token` | No — FP |
| 57 | `security.credential-literal` | Lockfile package metadata | `extensions/configuration-editing/package-lock.json` | 23 | FALSE_POSITIVE | lockfile_dependency_metadata · role=production · `sha512-JcQDs***y44Mpw==` | credential-literal on key `packages_node_modules_@octokit_auth_token_integrity` | No — FP |
| 58 | `security.credential-literal` | Lockfile package metadata | `extensions/configuration-editing/package-lock.json` | 23 | FALSE_POSITIVE | lockfile_dependency_metadata · role=production · `MIT` | credential-literal on key `packages_node_modules_@octokit_auth_token_license` | No — FP |
| 59 | `security.credential-literal` | Lockfile package metadata | `extensions/configuration-editing/package-lock.json` | 23 | FALSE_POSITIVE | lockfile_dependency_metadata · role=production · `5.1.2` | credential-literal on key `packages_node_modules_@octokit_auth_token_version` | No — FP |
| 60 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1754 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[3]_configuration_properties_ap…` | No — FP |
| 61 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1756 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for Anthropic` | credential-literal on key `contributes_languagemodelchatproviders[3]_configuration_properties_ap…` | No — FP |
| 62 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1757 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[3]_configuration_properties_ap…` | No — FP |
| 63 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1772 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[4]_configuration_properties_ap…` | No — FP |
| 64 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1774 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for xAI` | credential-literal on key `contributes_languagemodelchatproviders[4]_configuration_properties_ap…` | No — FP |
| 65 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1775 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[4]_configuration_properties_ap…` | No — FP |
| 66 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1790 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[5]_configuration_properties_ap…` | No — FP |
| 67 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1792 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for Google Gemini` | credential-literal on key `contributes_languagemodelchatproviders[5]_configuration_properties_ap…` | No — FP |
| 68 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1793 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[5]_configuration_properties_ap…` | No — FP |
| 69 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1808 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[6]_configuration_properties_ap…` | No — FP |
| 70 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1810 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for OpenRouter` | credential-literal on key `contributes_languagemodelchatproviders[6]_configuration_properties_ap…` | No — FP |
| 71 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1811 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[6]_configuration_properties_ap…` | No — FP |
| 72 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1826 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[7]_configuration_properties_ap…` | No — FP |
| 73 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1828 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for OpenAI` | credential-literal on key `contributes_languagemodelchatproviders[7]_configuration_properties_ap…` | No — FP |
| 74 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1829 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[7]_configuration_properties_ap…` | No — FP |
| 75 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 1871 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[9]_configuration_properties_ap…` | No — FP |
| 76 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 1873 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for the models` | credential-literal on key `contributes_languagemodelchatproviders[9]_configuration_properties_ap…` | No — FP |
| 77 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 1874 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[9]_configuration_properties_ap…` | No — FP |
| 78 | `security.credential-literal` | Schema apiKey deprecation | `extensions/copilot/package.json` | 1875 | FALSE_POSITIVE | extension_manifest_schema · role=production · `**Deprecated.** Use the `customendpoint…` | credential-literal on key `contributes_languagemodelchatproviders[9]_configuration_properties_ap…` | No — FP |
| 79 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 2016 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[10]_configuration_properties_a…` | No — FP |
| 80 | `security.credential-literal` | Schema apiKey minLength | `extensions/copilot/package.json` | 2018 | FALSE_POSITIVE | extension_manifest_schema · role=production · `1` | credential-literal on key `contributes_languagemodelchatproviders[10]_configuration_properties_a…` | No — FP |
| 81 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 2019 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for the models` | credential-literal on key `contributes_languagemodelchatproviders[10]_configuration_properties_a…` | No — FP |
| 82 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 2020 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[10]_configuration_properties_a…` | No — FP |
| 83 | `security.credential-literal` | Schema apiKey type | `extensions/copilot/package.json` | 2227 | FALSE_POSITIVE | extension_manifest_schema · role=production · `string` | credential-literal on key `contributes_languagemodelchatproviders[11]_configuration_properties_a…` | No — FP |
| 84 | `security.credential-literal` | Schema apiKey description | `extensions/copilot/package.json` | 2229 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API key for the models. If not set then…` | credential-literal on key `contributes_languagemodelchatproviders[11]_configuration_properties_a…` | No — FP |
| 85 | `security.credential-literal` | Schema apiKey title | `extensions/copilot/package.json` | 2230 | FALSE_POSITIVE | extension_manifest_schema · role=production · `API Key` | credential-literal on key `contributes_languagemodelchatproviders[11]_configuration_properties_a…` | No — FP |
| 86 | `security.credential-literal` | npm script (get_token) | `extensions/copilot/package.json` | 7140 | FALSE_POSITIVE | extension_manifest_schema · role=production · `tsx script/setup/getToken.mts` | credential-literal on key `scripts_get_token` | No — FP |

### Pattern groups

Compact summary of large FP / fixture clusters from the classified JSON (`pattern_groups`):

| Pattern group | Count | Classification | Rule | Example path | Example value (redacted) |
|---|---:|---|---|---|---|
| gha_secrets_github_token_expression | 35 | FALSE_POSITIVE | `security.credential-literal` | `.github/workflows/pr-node-modules.yml` | `${{ secrets.VSCODE_OSS }}` |
| azure_pipelines_mixin_password_var_in_fixture | 9 | TEST_FIXTURE | `security.credential-literal` | `extensions/copilot/test/simulation/fixtures/codeMapper/product-build-linux.yml` | `$(github-distro-mixin-password)` |
| package_json_apikey_schema_description | 8 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `API key for Anthropic` |
| package_json_apikey_schema_title | 8 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `API Key` |
| package_json_apikey_schema_type | 8 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `string` |
| packagelock_octokit_auth_token_metadata | 5 | FALSE_POSITIVE | `security.credential-literal` | `extensions/configuration-editing/package-lock.json` | `>= 18` |
| gha_oidc_step_output_token_expression | 2 | FALSE_POSITIVE | `security.credential-literal` | `.github/workflows/css-order-scan.yml` | `${{ steps.oidc.outputs.token }}` |
| gha_permissions_id_token_keyword | 2 | FALSE_POSITIVE | `security.credential-literal` | `.github/workflows/css-order-scan.yml` | `write` |
| SEC001::Sensitive configuration file committed | 1 | TEST_FIXTURE | `SEC001` | `extensions/copilot/test/simulation/fixtures/multiFileEdit/issue-9647/.env` | `Repository contains sensitive file: extensions/co…` |
| SEC002::Private key material detected | 1 | TEST_FIXTURE | `SEC002` | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | `-----BEGIN RSA PRIVATE KEY-----` |
| SEC003::AWS access key detected | 1 | MOCK_CREDENTIAL | `SEC003` | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | `AKI***PLE` |
| SEC003::GitHub token detected | 1 | MOCK_CREDENTIAL | `SEC003` | `extensions/copilot/src/extension/chronicle/common/test/secretFilter.spec.ts` | `ghp***234` |
| SEC003::Google API key detected | 1 | TEST_FIXTURE | `SEC003` | `src/vs/platform/terminal/test/node/terminalEnvironment.test.ts` | `AIz***wQe` |
| SEC004::Possible hardcoded credential | 1 | MOCK_CREDENTIAL | `SEC004` | `src/vs/platform/terminal/test/node/terminalEnvironment.test.ts` | `CLIENT_SECRET=cli***lue` |
| package_json_apikey_schema_deprecation | 1 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `**Deprecated.** Use the `customendpoint` provider…` |
| package_json_apikey_schema_minlength | 1 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `1` |
| package_json_npm_script_get_token | 1 | FALSE_POSITIVE | `security.credential-literal` | `extensions/copilot/package.json` | `tsx script/setup/getToken.mts` |

**Cluster takeaways**

- **GHA `${{ secrets.* }}` (35)** and **OIDC step-output tokens (2)** plus **`permissions.id-token` (2)** dominate `security.credential-literal` FPs in `.github/workflows`.
- **package.json apiKey contribution schema (≈26)** — title/description/type/minLength/deprecation fields describe UI settings named `apiKey`, not secret values.
- **package-lock `@octokit/auth-token` metadata (5)** — dependency *name* contains `token`; engines/integrity rows are not credentials.
- **Azure `$(github-distro-mixin-password)` in copilot fixtures (9)** — TEST_FIXTURE pipeline macros under simulation fixtures.
- **SEC001–SEC004 (6)** — MOCK/TEST_FIXTURE hits in secretFilter / terminalEnvironment tests and an empty fixture `.env`.

## 4. Root cause analysis of false positives

Investigation-only analysis of detector behavior implications (no implementation changes).

### 4.1 GitHub Actions secret and OIDC *expressions*

- **What fired:** `security.credential-literal` on workflow YAML keys whose *values* are `${{ secrets.… }}`, `${{ steps.oidc.outputs.token }}`, or related permission keywords (`id-token: write`).
- **Why:** Key names such as `github_token` / `token` plus secret-shaped *identifiers* satisfy credential-literal heuristics even when the value is a runtime expression resolved by Actions, not a committed secret.
- **Implication:** Expression-shaped values (`${{ … }}`) and OIDC wiring are configuration *references*, not literals. Treating them as credential material inflates FP volume (~45% of all secret findings in this assessment).

### 4.2 package.json contribution-point schema fields named `apiKey`

- **What fired:** Nested `contributes.languageModelChatProviders…configuration.properties.apiKey` schema nodes (`title`, `description`, `type`, `minLength`, deprecation markdown).
- **Why:** The property *name* `apiKey` (and titles like “API Key”) match credential key heuristics; sibling schema metadata values (`string`, `1`, descriptive prose) are then reported as credential literals.
- **Implication:** JSON Schema / VS Code contribution metadata describes *where a user may later supply* a key — not a stored secret. Name/description matching without value-shape checks produces systematic FPs in extension manifests.

### 4.3 package-lock dependency names containing `token`

- **What fired:** Lockfile rows for packages such as `@octokit/auth-token` (e.g. engines constraints).
- **Why:** Substring `token` / `auth-token` in package identity paths triggers credential-literal association with adjacent non-secret fields.
- **Implication:** Lockfiles are high-noise for name-based detectors; integrity hashes and engine ranges are never live credentials.

### 4.4 Azure Pipelines-style password macros in fixtures

- **What fired:** `$(github-distro-mixin-password)` under `extensions/copilot/test/simulation/fixtures/…`.
- **Why:** Password-like variable *names* inside YAML match credential patterns; values are shell/pipeline macros, not plaintext secrets.
- **Implication:** Macro/`$(…)` forms resemble GHA expressions — same class of “reference vs literal” confusion. Path under `**/test/**` / `fixtures` further indicates non-production evidence role (here classified TEST_FIXTURE).

### 4.5 Intentional SEC* hits on secret-filter and env sanitization tests

- **What fired:** SEC001 (empty fixture `.env`), SEC002 (fake PEM), SEC003 (AWS EXAMPLE key, synthetic `ghp_…`, Google sample key), SEC004 (`CLIENT_SECRET=…` test env).
- **Why:** Static pattern packs correctly recognize well-known secret shapes used as *positive test inputs* for redaction/sanitization.
- **Implication:** High pattern recall is desirable, but severity/labeling that implies a production breach is misleading. Evidence role (`test`) and well-known example corpora (AKIA…EXAMPLE, Google sample keys) should gate presentation.

### 4.6 Dual reporting: SEC* vs `security.credential-literal`

- **Observation:** Content-scan SEC* findings (6) come from `findings.json`; the bulk of credential-literal findings (80) come from repository-sensitive / configuration-fact assessment. Notes in the classified JSON also record count mismatches between findings.json credential-literal and security-assessment credential-literal streams.
- **Implication:** Without consolidation, the same conceptual “credential” theme can appear under different rule IDs and analyzers, complicating precision metrics and triage. Zero-match rules `security.placeholder-credential` and `security.private-key-material` ran but did not fire — overlapping concerns with SEC002 / example-key handling.

### 4.7 Evidence role and empty dotenv fixtures

- **What fired:** SEC001 on an empty `.env` under multiFileEdit simulation fixtures.
- **Why:** Sensitive *filename* heuristics treat committed `.env` as high risk regardless of emptiness or fixture path.
- **Implication:** Distinguishing empty vs populated dotenv, and test vs production artifact role, would reframe severity without requiring silence of all `.env` detections.

## 5. Precision improvement recommendations

Numbered recommendations for future detector work. **Do not implement as part of this investigation.**

1. **Exclude or down-rank GitHub Actions `${{ secrets.* }}` and OIDC expressions** — Values matching `${{ secrets.… }}`, `${{ steps.*.outputs.token }}`, and similar Actions expression forms are secret *references*, not committed literals; apply the same caution to `permissions.id-token` keyword rows.
2. **Exclude JSON schema property *names*/descriptions for `apiKey` contribution points** — Do not treat VS Code `contributes.*.configuration.properties.apiKey` title/description/type/minLength/deprecation metadata as credential values.
3. **Exclude lockfile package name/integrity rows for `*-token` packages** — Ignore npm/yarn/pnpm lockfile dependency identity and non-secret fields when the only signal is a package name containing `token` / `auth-token`.
4. **Treat paths under `**/test/**`, `**/*.spec.ts`, fixtures as test context** — Use path and source-role signals to lower severity or relabel (MOCK/TEST_FIXTURE), not to silence without review.
5. **Distinguish empty `.env` fixtures from populated dotenv** — Filename-only SEC001-style hits on empty or whitespace-only dotenv under fixtures should not share severity with populated production `.env` commits.
6. **Placeholder/example AWS keys (`AKIA…EXAMPLE`) and well-known Google sample keys** — Maintain an allowlist / known-example corpus so documentation and unit-test strings are labeled mock/example rather than live AWS/Google credentials.
7. **Shell macro credentials like `$(github-distro-mixin-password)`** — Treat `$(…)` pipeline/shell macros analogously to GHA expressions (references), especially under fixture trees.
8. **Dual reporting SEC* vs `security.credential-literal` consolidation** — Deduplicate or cross-link overlapping secret themes across content-scan and repository-sensitive analyzers before scoring precision.
9. **Evidence role (test vs production) should gate finding severity** — Propagate `source_role` / artifact classification into severity and customer-facing wording so intentional test secrets are not framed as production breaches.

## Appendix

### Assessment artifact paths

| Artifact | Path |
|---|---|
| Assessment ID | `typescript-vscode/vscode/20260729-082446` |
| Assessment directory | `validation/reports/typescript-vscode/vscode/20260729-082446` |
| Repository clone | `validation/repos/vscode` |
| Repository (GitHub) | `microsoft/vscode` |
| This report | `docs/internal/security-detector-precision-audit-vscode.md` |

### Rules with zero matches

From repository-sensitive evidence summary (executed, not matched):

- `security.placeholder-credential`
- `security.private-key-material`

Note: Static SEC002 private-key finding (when present) comes from the content-scan pack (`findings.json`), not from `security.private-key-material` repository-sensitive signatures.

### Intermediate data

- Classified findings JSON: `docs/internal/_audit_vscode_secret_findings.json`
- Total secret-related findings in JSON: 86
- Classification counts (JSON): `{"FALSE_POSITIVE": 71, "TEST_FIXTURE": 12, "MOCK_CREDENTIAL": 3}`
- Rule counts (JSON): `{"security.credential-literal": 80, "SEC003": 3, "SEC001": 1, "SEC002": 1, "SEC004": 1}`

### Scope exclusions (from classification notes)

- SEC005/SEC006 excluded: crypto/exec rules are not secret/credential findings
- `security.assessment` debug-enabled findings excluded: True
- findings.json credential-literal count: 1
- security-assessment credential-literal count: 80

