# AI usage ingestion (Slice 7.11)

Platform-owned privacy-first endpoint for bounded operational classifications of
AI-assisted CodeStrata operations.

## Endpoint

`POST /api/v1/ai-usage`

Route identity: `ai_usage.ingest`

Production Community Cloud routes after this slice:

- `GET /api/v1/health`
- `POST /api/v1/telemetry`
- `POST /api/v1/assessment-metadata`
- `POST /api/v1/cli-events`
- `POST /api/v1/extension-events`
- `POST /api/v1/ai-usage`

Single-event ingestion only. No `/ai`, `/llm-usage`, `/model-usage`,
`/events/ai`, or `/ai-usage/batch` aliases.

## Privacy statements

The AI Usage endpoint accepts only bounded operational classifications. It does
not accept prompts, model responses, source code, repository content, retrieved
documents, tool inputs or outputs, credentials, provider response bodies, exact
token counts, or exact customer cost.

AI usage metadata must not be used to reconstruct model conversations,
repository content, or customer intellectual property.

Do not send AI usage through `POST /telemetry`. Assessment metadata may contain
only `ai_used`. CLI/extension events may contain only `ai_requested`.

## Schema, policy, and catalogs

| Constant | Value |
| --- | --- |
| Community Cloud API contract | `1.0` (unchanged) |
| Prior endpoint schemas/policies | `1.0` (unchanged) |
| **AI usage schema** | `1.0` |
| **AI usage policy** | `community-ai-usage-policy:1.0` |
| **Capability catalog** | `ai-capability-catalog:1.0` |
| **Provider family catalog** | `ai-provider-family-catalog:1.0` |
| **Model family catalog** | `ai-model-family-catalog:1.0` |

Logging policy remains `community-logging-policy:1.0` with additive
`ai_usage_*` events and safe fields (`canonical_capability`, `outcome`,
schema/policy versions). Provider/model/token fields are **not** logged by
default.

## Reviewed catalogs (actual integrations only)

### Capability

- `modernization_advisor` (Community assess `--with-ai` / Modernization Advisor)

Invented capabilities such as free-form “code assistance” are rejected.

### Provider family

- `openai` (includes Azure-compatible OpenAI `base_url` endpoints)
- `aws_bedrock` (alias `bedrock`)
- `unavailable`

Anthropic, OpenRouter, and native Azure providers are **not** accepted until
implemented in product code.

### Model family

- `gpt_family`
- `amazon_nova_family`
- `other_supported`
- `unavailable`

Raw model IDs (`gpt-4o-mini`, `amazon.nova-lite-v1:0`) are rejected.

## Request envelope

Required: `schema_version`, `event_id`, `client`, `usage`, `context`.

Optional: `installation_id`.

### Client

`codestrata_cli` | `vscode_extension` | `cursor_extension` with bounded
version/platform.

### Usage

- `capability`, `execution_mode` (`deterministic_with_ai` | `unavailable`)
- `provider_ownership` (`customer_managed` | `codestrata_managed` | `unavailable`)
- `provider_family`, `model_family`
- `outcome`, `duration_bucket`, token buckets, tool/rag/graph usage states
- `failure_category` required when `outcome=failed`; forbidden on success

Token buckets are coarse ranges only. Exact counts and cost are forbidden.
Total cannot be `none` when input/output show usage; consistency across ranges
is coarse by design (no numeric reconstruction).

### Context

- single `assessment_head` (canonical Community Cloud head or `unavailable`)
- `invocation_source`, `offline_mode`, `user_initiated`
- `data_scope` / `output_usage` classify broad categories only — never content

## Event identity

Source type: `ai_usage_submitted`.

Retry: 202 / 200 exact retry / 409 conflict / 503 unavailable.

Shared identity ports; separate `AiUsageSink`. No exactly-once guarantee.

## Defaults

Default sink/store unavailable → **503**. Independent injectable
`ai_usage_sink` on `create_community_cloud_app()`.

## Auth / persistence / emitter

Unauthenticated. No production persistence. Client emission is **not** wired.
Engine AI providers, prompts, RAG, and KG are unchanged.
