# Configuration and execution profiles (Phase 5.20)

CodeStrata uses named **execution profiles** to apply secure defaults without
duplicating the rest of the configuration model. Profiles only supply defaults;
they do not replace `codestrata.toml`.

## Profiles

| Profile | Intent | Secure defaults |
| ------- | ------ | --------------- |
| `community` | Community edition (default) | Enterprise KG off; deterministic knowledge AI |
| `local` | No external LLM | Deterministic embedding/answer providers |
| `enterprise` | Enterprise Knowledge Graph | `[enterprise].enabled = true`; deterministic AI |
| `bedrock` | AWS Bedrock providers | Assessment + knowledge via Bedrock; region required |
| `openai` | OpenAI knowledge providers | `embedding_provider` / `answer_provider` = `openai`; API key via env name |

Community vs Enterprise remains **configuration-driven** via
`[enterprise].enabled` (see
[community-enterprise-boundary.md](assessment-framework/community-enterprise-boundary.md)).
The `enterprise` profile turns that gate on by default; `community` / `local` /
`bedrock` / `openai` leave it off unless the TOML explicitly enables it.

## Precedence

```text
CLI (--profile)
  > environment (CODESTRATA_PROFILE and related overlays)
  > codestrata.toml (including profile = "..." or [execution].profile)
  > profile defaults
```

Related environment overlays (also env > TOML):

| Variable | Effect |
| -------- | ------ |
| `CODESTRATA_PROFILE` | Active execution profile |
| `AWS_PROFILE` | AWS session profile (resolved at use time; env > TOML) |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | AWS region (resolved at use time; env > TOML) |
| `CODESTRATA_BEDROCK_MODEL_ID` | `[ai.bedrock].model_id` |
| `CODESTRATA_OPENAI_API_KEY_ENV` | `[ai.openai].api_key_env` (name only) |

OpenAI secrets are **never** stored in TOML. Configure only the environment
variable *name* (`api_key_env = "OPENAI_API_KEY"`) and set the value in the
process environment or `.env`.

## TOML examples

```toml
# Default when omitted: community
profile = "local"

[repository]
path = "examples/sample-js-app"
```

```toml
profile = "bedrock"

[aws]
profile = "codestrata"
region = "us-east-1"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
```

```toml
profile = "openai"

[ai.openai]
api_key_env = "OPENAI_API_KEY"
embedding_model = "text-embedding-3-small"
answer_model = "gpt-4o-mini"
```

```toml
profile = "enterprise"

# enterprise.enabled defaults to true under this profile
```

Alias form (equivalent):

```toml
[execution]
profile = "community"
```

## CLI

```bash
# Active profile + source
codestrata config profile --config codestrata.toml

# Effective non-secret settings
codestrata config effective --config codestrata.toml
codestrata config show --config codestrata.toml   # alias

# Validate profile compatibility (add --strict for credential presence)
codestrata config validate --config codestrata.toml
codestrata config validate --config codestrata.toml --profile bedrock --strict

# Assess with an explicit profile
codestrata assess --config codestrata.toml --profile local --output reports
```

## Validation behavior

Hard errors (fail load / `config validate`):

* Unknown profile name
* `local` with non-deterministic knowledge providers
* `enterprise` profile with `[enterprise].enabled = false`
* `bedrock` profile without a resolvable AWS region
* `openai` profile without OpenAI embedding/answer providers or `api_key_env`

Warnings (reported, non-fatal):

* `community` with external AI providers (prefer `bedrock` / `openai` profiles)
* `community` with `[enterprise].enabled = true` (prefer `profile = "enterprise"`)
* `--strict` Bedrock credential hints when no profile/access key is visible

`local` + `assess --with-ai` is rejected at assessment time.

## Secrets

Effective dumps and MCP health:

* Show `api_key_env` **name** and `api_key_present` boolean — never the key
* Redact database URLs / connection strings
* AWS uses the default credentials chain; only profile/region names are shown

## Backward compatibility

Existing `codestrata.toml` files without `profile` load as **`community`**,
matching prior secure defaults (`enterprise.enabled = false`, deterministic
knowledge providers, Bedrock-named assessment provider). Explicit TOML keys
continue to override profile defaults.

## Related

* [runtime.md](runtime.md)
* [runtime-performance.md](runtime-performance.md)
* [ai-enrichment.md](ai-enrichment.md)
* [cli-reference.md](cli-reference.md)
* [troubleshooting.md](troubleshooting.md)
* [assessment-framework/community-enterprise-boundary.md](assessment-framework/community-enterprise-boundary.md)
