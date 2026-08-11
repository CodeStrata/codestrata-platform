---
title: AI Providers
description: Optional AI enrichment for CodeStrata Engine — what leaves your machine, provider-specific flows, and honest live-verification status.
---

# AI Providers

Canonical Community Edition documentation for **optional** AI enrichment
(Modernization Advisor) on top of deterministic Engineering Assessments.

For the broader “what stays local vs leaves” map across Assessment, Telemetry,
Publishing, and Insights, see [Source Locality](/security/source-locality).

## Skeptical engineering checklist

| Question | Short answer (v0.2.0) |
| --- | --- |
| Is AI required? | **No** — default is `--no-ai` |
| Which providers are supported? | Amazon Bedrock, OpenAI, OpenRouter |
| What leaves the machine for AI? | Bounded assessment-derived enrichment context / prompts to the **chosen provider** |
| Full source tree uploaded? | **No** |
| Bounded evidence path/excerpt clips? | **May be included** in compact context |
| Which provider was live E2E proven in release-candidate validation? | **Bedrock** (`passed_live`) |
| OpenAI / OpenRouter live E2E? | Structural/implementation validated; live E2E **OWNER_CREDENTIAL_REQUIRED** |
| If AI fails? | Assessment continues; deterministic reports still write (fail-soft) |
| Are prompts/responses CodeStrata telemetry? | **No** |
| Does AI create/delete findings? | **No** — deterministic finding IDs remain provider-independent |
| Where do credentials live? | Provider env / AWS chain — not in reports, telemetry, or public URLs |
| Provider retention? | Governed by provider/account terms — not CodeStrata Data Lake retention |

## Is AI required? (`--no-ai`)

AI is an **optional capability**. Deterministic assessment is the **default**.

```bash
# Default / explicit deterministic path
codestrata assess --repo . --no-ai

# Optional enrichment
codestrata assess --repo . --with-ai
```

| Claim | Status |
| --- | --- |
| Deterministic assessment only with `--no-ai` | Yes |
| No AI provider invocation | Yes |
| No AI-provider credential required | Yes |
| Local HTML/JSON reports remain valid | Yes |
| Deterministic evidence remains available | Yes |

Provider selection for `--with-ai` comes from Engine configuration
(`[ai].provider`, default `bedrock`) and environment — not from inventing
extra CLI provider switches beyond `--with-ai` / `--model-id`.

## Deterministic vs AI output

| Layer | Role |
| --- | --- |
| **Deterministic** | Findings, evidence, base assessment facts produced by the Engine |
| **AI-enriched** | Advisor narrative / explanation / prioritization **on top of** allowlisted finding and recommendation IDs |

AI providers do **not** determine whether a finding exists. Epic 17.20 validation
requires identical deterministic finding ID sets for `--no-ai` vs Bedrock when
both runs are available. Advisor narrative may differ; finding identity must not.

## What AI enrichment sends

When `--with-ai` is enabled and a provider is configured, Modernization Advisor
builds a **compact, budgeted, secret-redacted** enrichment context and sends it
**directly** to the selected provider.

Included categories (current Engine builders):

- Repository metadata (display name / identity key / file count)
- Technology summaries (name, category, version — capped)
- Dependency summaries (ecosystem, name, namespace, version, scope — capped)
- Finding summaries (id, rule_id, title, severity, category, clipped summary, evidence refs)
- Recommendation summaries (id, title, priority, category, clipped summary, related finding ids, action titles)
- Allowlists of permitted finding / recommendation IDs
- Truncation notes when budget caps are hit
- Provider prompt wrapper (persona / schema instructions)

Evidence refs may include bounded **path or excerpt clips** (short character
caps). That is **not** a full file or repository upload — but it is also **not**
a claim that “no source-derived text ever leaves.”

It does **not** upload full repository source trees or full graph dumps.

## What is not sent to AI providers

Verified for current v0.2.0 enrichment builders (distinct from the Community
telemetry never-collected list):

- Full repository checkout / entire source tree
- Full source files as wire bodies
- Absolute filesystem paths (validators reject common absolute-path forms)
- Local / provider credentials and API key values
- Community auth tokens / client credentials
- Community telemetry history
- Public report URLs as enrichment payload
- Secrets Manager values
- Unrelated local files outside the compact assessment-derived context
- Full local `assessment.html` / `assessment.json` report bodies as the provider wire payload

## Provider calls vs CodeStrata telemetry

| Path | What it is |
| --- | --- |
| AI provider request/response | Direct call to Bedrock / OpenAI / OpenRouter with enrichment context |
| Community telemetry | Optional privacy-safe events to `api.codestrata.ai` after separate opt-in |

**AI prompts and responses are not sent through CodeStrata Community telemetry.**

That does **not** mean the provider itself never receives prompt/context — it
does, when you enable `--with-ai`.

Community API `POST /api/v1/ai-usage` is a **usage-metadata** ingest contract for
Community Cloud. It is **not** an AI proxy. Assess-path `ai_usage` emission
remains **construction-only / deferred** in v0.2.0 — do not claim every AI
request is recorded in CodeStrata telemetry.

## Three outbound paths (do not conflate)

| Path | Data | Destination |
| --- | --- | --- |
| AI enrichment | Assessment-derived compact context | Chosen provider |
| Telemetry | Privacy-safe events | Community Data Lake via `api.codestrata.ai` |
| Report publishing | Explicit report package | Report Artifact Store → opaque public URL |

Diagrams: [Source Locality](/security/source-locality#data-flow-diagrams).

## Provider-specific status

| Provider | Live E2E status | Notes |
| --- | --- | --- |
| **Bedrock** | `passed_live` / LIVE E2E PROVEN | Release-candidate validation proven |
| **OpenAI** | Implementation validated; live E2E **OWNER_CREDENTIAL_REQUIRED** | Not an implementation failure statement — owner API key was not supplied for live E2E |
| **OpenRouter** | Implementation validated; live E2E **OWNER_CREDENTIAL_REQUIRED** | Distinct integration — **not** an alias for OpenAI; **not** the Bedrock test path |
| **no-AI** | Supported / proven | Default deterministic path |

There is **no** silent cross-provider fallback.

### Amazon Bedrock

| Topic | Behavior |
| --- | --- |
| Path | AWS SDK Bedrock Runtime (`invoke` / Converse-style adapter) |
| Credentials | AWS SDK default credential chain / profile / role — no static CodeStrata-managed key architecture |
| Destination | AWS Bedrock in the configured region |
| Request data | Compact enrichment context (above) |
| Response use | Advisor enrichment narrative / structured advisor result |
| Timeout | Finite `timeout_seconds` (default 60s) wired into the client |
| Retry | **Single attempt** (`maximum_attempts=1`, CR-1 intentional) |
| Failure | Non-blocking; deterministic reports still write |
| E2E | Live proven |

Do not publish AWS account IDs in docs examples.

### OpenAI

| Topic | Behavior |
| --- | --- |
| Path | Direct OpenAI Chat Completions / Responses-compatible client path |
| Credentials | Env var named by config (default `OPENAI_API_KEY`) — value never in `codestrata.toml` |
| Destination | OpenAI API (or configured base URL) |
| Request / response / timeout / single-attempt / fail-soft | Same enrichment contract as other assess providers |
| E2E | Live provider E2E not completed in RC validation because owner API key was not supplied |

### OpenRouter

| Topic | Behavior |
| --- | --- |
| Path | OpenRouter Chat Completions API (distinct provider integration) |
| Credentials | Env var named by config (default `OPENROUTER_API_KEY`) |
| Model | Explicit model ID required (no product default) |
| Not | Not OpenAI alias; not Bedrock routing |
| E2E | OWNER_CREDENTIAL_REQUIRED (same honesty standard as OpenAI) |

## Timeout and retries

`[ai.<provider>].timeout_seconds` is applied when constructing the assess
provider client (finite; default **60s**).

Community assess performs **exactly one** provider attempt per enrichment run
(CR-1). `[ai.<provider>].max_retries` may appear in configuration diagnostics
but is **not** applied as CodeStrata-level multi-attempt retries on the assess
path. This avoids unexpected repeated external provider calls.

## Provider failure behavior

If the provider is unavailable, times out, returns malformed output, or has
invalid credentials:

- Deterministic assessment and local HTML/JSON reports remain viable
- Enrichment is skipped / status recorded without fabricating advisor success
- CLI typically still exits **0** when reports are written
- There is **no** silent fallback to another provider

Fix provider configuration and retry `--with-ai` when ready.

## Credential handling

| Provider | Credential class |
| --- | --- |
| Bedrock | AWS SDK credential chain / profile / role |
| OpenAI | Secure API key via environment |
| OpenRouter | Secure API key via environment |

CodeStrata does **not** place provider credentials into:

- Assessment Reports / EIR bodies
- Community telemetry payloads
- Public report URLs
- Generated artifact manifests as secret values

Successful enrichment may record **provider name / model metadata / token or
latency metadata** in advisor execution artifacts — not API keys or AWS secrets.

## Model metadata

Local configuration may name an exact model ID for the provider call.

Public Community telemetry / Insights classification prefers privacy-safe model
family / classification abstractions where telemetry exists. Do not treat
telemetry docs as a place to republish every exact model identifier.

Exact model IDs in **local** `codestrata.toml` / env overrides are operator
configuration, not Community Data Lake contracts.

## Third-party provider retention

Data sent to a third-party provider (or AWS Bedrock under your account) is
governed by **that provider/account’s terms, configuration, and policies**.

CodeStrata Community Data Lake retention does **not** control third-party
provider retention. This page does not invent provider retention guarantees.

## Engineering Intelligence (EIR) AI boundary

Validated v0.2.0 Engineering Intelligence reporting does **not** use AI-provider
enrichment. EIR is composed from assessment products / deterministic synthesis —
not an AI-generated substitute for findings.

Advisor enrichment attaches to Assessment flows (`--with-ai`), not to EIR
generation.

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

Works on any machine using the **standard AWS credential provider chain**.

1. Install the Bedrock extra (above).
2. Configure credentials on **this machine** (pick one):

```bash
# Named profile (recommended for SSO)
export AWS_PROFILE=<your-profile>
aws sso login --profile <your-profile>

# Or default chain / access keys
aws configure
```

3. Set a region (env preferred):

```bash
export AWS_REGION=us-east-1
```

4. Optional model / toml:

```toml
[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"

[aws]
region = "us-east-1"
```

| Variable | Purpose |
| -------- | ------- |
| `AWS_PROFILE` | Named AWS profile (optional) |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | Region |
| `CODESTRATA_BEDROCK_MODEL_ID` | Model ID override |

```bash
codestrata ai doctor
codestrata assess --repo . --with-ai
```

## OpenAI setup

```bash
export OPENAI_API_KEY=...   # do not commit
```

```toml
[ai]
provider = "openai"

[ai.openai]
api_key_env = "OPENAI_API_KEY"
answer_model = "gpt-4o-mini"
```

```bash
codestrata ai doctor
codestrata assess --repo . --with-ai
```

## OpenRouter setup

```bash
export OPENROUTER_API_KEY=...   # do not commit
```

```toml
[ai]
provider = "openrouter"

[ai.openrouter]
api_key_env = "OPENROUTER_API_KEY"
model = "openai/gpt-4o-mini"
```

A model ID is **required** (no product default). Or pass `--model-id` /
`CODESTRATA_OPENROUTER_MODEL_ID`.

```bash
codestrata ai --provider openrouter
codestrata ai doctor
codestrata assess --repo . --with-ai --model-id openai/gpt-4o-mini
```

## CLI discovery

| Command | Purpose |
| ------- | ------- |
| `codestrata ai` | Supported providers, current provider, Configured / Not Configured |
| `codestrata ai doctor` | Credential/config checks (never prints secrets) |
| `codestrata assess --help` | Documents `--with-ai` / `--no-ai` (default deterministic) |

## VS Code

The VS Code extension runs local Engine assessments. Provider credentials are
**not** stored in the extension. There is **no** separate Marketplace-live
provider-selection control panel beyond Engine configuration for Community
v0.2.0 — AI support is through the Engine (`--with-ai` / config) where used.

Default assessment posture remains local / deterministic unless the user
explicitly chooses an AI-enhanced Engine path.

See [VS Code](/extensions/vscode) and [Source Locality](/security/source-locality).

## Troubleshooting

| Symptom | What to try |
| ------- | ----------- |
| AWS credentials missing | Set `AWS_PROFILE` or default credentials; `export AWS_REGION=…`; re-run `codestrata ai doctor` |
| `OPENAI_API_KEY` / `OPENROUTER_API_KEY` missing | Export the env var named in config |
| OpenRouter model required | Set `--model-id`, env override, or `[ai.openrouter].model` |
| Unsupported provider | Set `[ai].provider` to `bedrock`, `openai`, or `openrouter` |
| AI enrichment skipped but reports written | Expected fail-soft; exit code may remain 0 — fix provider config and retry |

Fall back anytime:

```bash
codestrata assess --repo . --no-ai
```

## What AI is not

- Not required for Community Edition assessments
- Not a path for the VS Code extension to upload repository source trees
- Not a cross-provider fallback layer
- Not CodeStrata Community telemetry
- Not an EIR generator in the validated v0.2.0 path

## Related

- [Source Locality](/security/source-locality)
- [Privacy](/security/privacy)
- [Telemetry](/reference/telemetry)
- [Data Collection](/security/data-collection)
- [Retention and Deletion](/security/retention-and-deletion)
- [Community Cloud API](/reference/community-api/)
