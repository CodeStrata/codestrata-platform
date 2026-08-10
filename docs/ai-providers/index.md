---
title: AI Providers
description: Optional AI enhancement for CodeStrata Engine using Bedrock, OpenAI, or OpenRouter.
---

# AI Providers

AI is an **optional capability** of CodeStrata Engine. Deterministic assessment
(`--no-ai`) is the **default** and does not require provider keys.

## When to use AI

Use `--with-ai` when you want optional enrichment (Modernization Advisor) on top
of deterministic findings.

```bash
codestrata assess --repo . --output reports --with-ai
```

Check configuration without assessing:

```bash
codestrata ai
codestrata ai --provider bedrock
codestrata ai --provider openai
codestrata ai --provider openrouter
codestrata ai doctor
```

Supported assess providers are **Amazon Bedrock**, **OpenAI**, and **OpenRouter**.
Organizational Platform connectivity is outside Community Edition documentation
scope.

## What AI enrichment sends

Modernization Advisor builds a **compact** enrichment context — not full source
dumps. The provider receives:

- repository metadata (display name / identity / file count)
- compact **finding summaries** (id, title, severity, category, short summary, evidence refs)
- compact **recommendation summaries** (id, title, priority, category, short summary)
- bounded technology and dependency summaries

It does **not** upload full repository source trees. Do not interpret this as
findings being omitted from the provider payload — finding and recommendation
**summaries** are included so the advisor can reference deterministic evidence.

Provider failure is **non-blocking**: deterministic assessment and reports still
write when enrichment fails (exit code remains 0). Fix provider config and retry
`--with-ai` when ready.

## Provider calls vs CodeStrata telemetry

Sending enrichment context to **your** configured AI provider (Bedrock / OpenAI /
OpenRouter) is separate from optional CodeStrata product telemetry. Provider
prompts and responses stay with that provider session and are **not** mirrored
into Community telemetry / Data Lake events. Opt-in telemetry, when enabled,
uses approved usage metadata abstractions — not raw prompts, responses, or API
keys.

Community Edition v0.2.0 keeps optional `ai_usage` analytics as a
**construction-only** capability (not emitted on every assess run). Live
assess-path `ai_usage` emission is deferred to a later Release Epic task and
must not create a second telemetry transport.

## Timeout and retries

`[ai.<provider>].timeout_seconds` is applied when constructing the assess
provider client (finite; default 60s).

Community assess performs **exactly one** provider attempt per enrichment run
(CR-1). `[ai.<provider>].max_retries` is retained for diagnostics/configuration
representation and is **not** applied as CodeStrata-level retries on the assess
path (no infinite retry; provider failure remains fail-soft).

## Install provider extras

```bash
# Amazon Bedrock
pip install 'codestrata[bedrock]'

# OpenAI (also covers OpenRouter HTTP client extra)
pip install 'codestrata[openai]'

# Both Bedrock and OpenAI extras
pip install 'codestrata[bedrock,openai]'
```

## Amazon Bedrock setup

Works on any machine using the **standard AWS credential provider chain**. No
repository-specific AWS profile is required.

1. Install the Bedrock extra (above).
2. Configure credentials on **this machine** (pick one):

```bash
# Named profile (recommended for SSO)
export AWS_PROFILE=<your-profile>
aws sso login --profile <your-profile>

# Or default chain / access keys
aws configure
# or:
export AWS_ACCESS_KEY_ID=…
export AWS_SECRET_ACCESS_KEY=…
```

3. Set a region (env preferred):

```bash
export AWS_REGION=us-east-1
```

4. Optional model / toml (no profile required):

```toml
[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"

# Optional region if AWS_REGION is unset:
[aws]
region = "us-east-1"
# Do not commit developer-specific profiles. Prefer AWS_PROFILE on each machine.
```

Environment overrides:

| Variable | Purpose |
| -------- | ------- |
| `AWS_PROFILE` | Named AWS profile (optional; omit to use the default chain) |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | Region |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Access keys (default chain) |
| `CODESTRATA_BEDROCK_MODEL_ID` | Model ID override |

Validate (doctor uses the same resolution as runtime):

```bash
codestrata ai doctor
codestrata assess --repo . --output reports --with-ai
```

### Clean-machine Community path

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[bedrock]'   # from engine/
export AWS_REGION=us-east-1
# optional: export AWS_PROFILE=<your-profile>
codestrata ai doctor
codestrata assess --repo . --output reports --with-ai
```

## OpenAI setup

1. Install the OpenAI extra (`codestrata[openai]`).
2. Export your API key (value stays in the environment — never in `codestrata.toml`):

```bash
export OPENAI_API_KEY=...   # do not commit
```

3. Select the OpenAI assess provider:

```toml
profile = "openai"

[ai]
provider = "openai"

[ai.openai]
api_key_env = "OPENAI_API_KEY"
answer_model = "gpt-4o-mini"
```

Environment overrides:

| Variable | Purpose |
| -------- | ------- |
| `OPENAI_API_KEY` | API key (referenced by name only in config) |
| `CODESTRATA_OPENAI_API_KEY_ENV` | Override which env var name to read |
| `CODESTRATA_OPENAI_MODEL_ID` | Model ID override |

Validate:

```bash
codestrata ai doctor
codestrata assess --repo . --output reports --with-ai
```

## OpenRouter setup

1. Install the OpenAI extra (shared HTTP client): `pip install 'codestrata[openai]'`.
2. Export your API key (value stays in the environment — never in `codestrata.toml`):

```bash
export OPENROUTER_API_KEY=...   # do not commit
```

3. Select the OpenRouter assess provider. **A model ID is required** (no product default):

```toml
[ai]
provider = "openrouter"

[ai.openrouter]
api_key_env = "OPENROUTER_API_KEY"
model = "openai/gpt-4o-mini"
```

Or pass `--model-id` / set `CODESTRATA_OPENROUTER_MODEL_ID`.

Environment overrides:

| Variable | Purpose |
| -------- | ------- |
| `OPENROUTER_API_KEY` | API key (referenced by name only in config) |
| `CODESTRATA_OPENROUTER_API_KEY_ENV` | Override which env var name to read |
| `CODESTRATA_OPENROUTER_MODEL_ID` | Model ID override (required if toml model unset) |

Validate:

```bash
codestrata ai --provider openrouter
codestrata ai doctor
codestrata assess --repo . --output reports --with-ai --model-id openai/gpt-4o-mini
```

## CLI discovery

| Command | Purpose |
| ------- | ------- |
| `codestrata ai` | Supported providers, current provider, Configured / Not Configured, required env vars, docs link |
| `codestrata ai doctor` | Checkmarks for Bedrock / OpenAI / OpenRouter / missing credentials / unsupported provider (never prints secrets) |
| `codestrata assess --help` | Documents `--with-ai` / `--no-ai` (default deterministic) |

## Troubleshooting

| Symptom | What to try |
| ------- | ----------- |
| `✗ AWS credentials missing` | Set `AWS_PROFILE` or default credentials; `export AWS_REGION=…`; remove stale `[aws].profile` from toml; re-run `codestrata ai doctor` |
| Doctor shows wrong profile | Prefer `AWS_PROFILE` over committing `[aws].profile`; doctor reports the same source runtime uses |
| `✗ OPENAI_API_KEY missing` | `export OPENAI_API_KEY=…` (or the name in `[ai.openai].api_key_env`) |
| `✗ OPENROUTER_API_KEY missing` | `export OPENROUTER_API_KEY=…` (or the name in `[ai.openrouter].api_key_env`) |
| OpenRouter model required | Set `--model-id`, `CODESTRATA_OPENROUTER_MODEL_ID`, or `[ai.openrouter].model` |
| `✗ Unsupported provider` | Set `[ai].provider` to `bedrock`, `openai`, or `openrouter` |
| Extra / import errors | `pip install 'codestrata[bedrock]'` or `'codestrata[openai]'` |
| Profile `local` rejects `--with-ai` | Use `--profile bedrock` / `openai` / appropriate profile, or omit `--with-ai` |
| AI enrichment skipped but reports written | Expected when credentials fail; exit code remains 0 — fix provider config and retry |

Fall back anytime:

```bash
codestrata assess --repo . --output reports --no-ai
```

## What AI is not

- Not the product name (“CodeStrata AI” is not used)
- Not required for Community Edition assessments
- Not a path to upload repository source from the VS Code extension
- Not a cross-provider fallback layer (invalid provider names error; no silent substitute)

Never put commercial Platform API keys in Engine AI configuration. Use only the
provider credentials documented above for Bedrock, OpenAI, or OpenRouter.
