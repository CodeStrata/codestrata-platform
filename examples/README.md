# Examples

Language sample repositories for CodeStrata onboarding, docs, and dogfood.

| Sample | Language | Assess |
| ------ | -------- | ------ |
| [`sample-js-app`](sample-js-app/) | JavaScript | `codestrata assess --repo examples/sample-js-app --output reports` |
| [`sample-python-app`](sample-python-app/) | Python | `codestrata assess --repo examples/sample-python-app --output reports` |
| [`sample-java-app`](sample-java-app/) | Java | `codestrata assess --repo examples/sample-java-app --output reports` |
| [`sample-php-app`](sample-php-app/) | PHP | `codestrata assess --repo examples/sample-php-app --output reports` |
| [`sample-csharp-app`](sample-csharp-app/) | C# / .NET | `codestrata assess --repo examples/sample-csharp-app --output reports` |

Golden HTML/JSON reports: [sample-reports/README.md](sample-reports/README.md).

Default `codestrata.toml` points at `sample-js-app`:

```bash
codestrata config validate --config codestrata.toml
codestrata assess --config codestrata.toml --output reports --no-ai
# Optional: --profile local|community|enterprise|bedrock|openai
```

## Expected artifacts (deterministic)

* Exit code `0`
* `reports/<name>/<YYYYMMDD-HHMMSS>/report.html`
* `report.json`, `findings.json`, `recommendations.json`, `graphs/`
* No `ai-enrichment.json` unless `--with-ai` succeeded

## Private GitHub HTTPS clones

Set a token in `.env` (never commit secrets) and reference it from
`codestrata.toml`:

```toml
[repository.authentication]
type = "github_token"
token_env = "CODESTRATA_GITHUB_TOKEN"
```

## AI mode (optional)

Requires AWS credentials and Bedrock configuration:

```bash
aws sso login --profile <profile-name>
codestrata assess --config codestrata.toml --output reports --with-ai
```

See [docs/configuration-profiles.md](../engine/docs/configuration-profiles.md) and
[docs/tutorial.md](../engine/docs/tutorial.md).
