# Production AI Providers (Phase 5.8)

**Status:** Complete — Bedrock and OpenAI embedding + grounded-answer providers.

Deterministic providers remain the default. Production providers are selected
independently and never silently fall back.

## Independent configuration

```toml
[ai]
embedding_provider = "bedrock"   # deterministic | bedrock | openai
answer_provider = "openai"       # deterministic_extractive | bedrock | openai

[ai.bedrock]
region = "us-east-1"
embedding_model = "amazon.titan-embed-text-v2:0"
answer_model = "amazon.nova-lite-v1:0"
timeout_seconds = 60
max_retries = 3

[ai.openai]
api_key_env = "OPENAI_API_KEY"
base_url = ""
embedding_model = "text-embedding-3-small"
answer_model = "gpt-4o-mini"
embedding_dimensions = 0
timeout_seconds = 60
max_retries = 3
```

Credentials are required only for **selected** providers at runtime. Unused
provider sections do not need secrets. API keys are read from environment
variables named by `api_key_env` and are never logged.

Optional installs:

* `pip install 'codestrata[bedrock]'`
* `pip install 'codestrata[openai]'`

## Registry and factories

`AIProviderRegistry` (`codestrata.ai.providers.registry`) registers:

| Kind | Names |
| ---- | ----- |
| Embedding | `deterministic`, `bedrock`, `openai` |
| Answer | `deterministic_extractive`, `bedrock`, `openai` |

`create_embedding_provider` / `create_answer_provider` resolve through the
registry. Prefer `[ai].embedding_provider` / `[ai].answer_provider` when
`CodestrataSettings` is supplied (MCP and CLI do this).

### Adding another provider later

1. Implement `EmbeddingProvider` and/or `AnswerProvider`
2. Register a factory on `AIProviderRegistry`
3. Add `[ai.<name>]` settings and allowlist the name in `AiSettings`
4. Do **not** add silent fallback to another provider

Do not add Anthropic, Azure OpenAI, Gemini, Ollama, or vLLM in this phase.

## Prompts

Shared versioned prompt resources live at:

```text
codestrata/application/knowledge/answering/prompts/
  grounded-repository-answer/1.0.0/
    system.md
    user.md
    repair.md
    metadata.json
    response_schema.json
```

Python loads and renders these files only; production prompt text is not
embedded in Python modules. Bedrock and OpenAI use the same resources.
`prompt_version` appears in answer-provider diagnostics.

## Index compatibility

Indexed vectors stamp:

* `embedding_provider`
* `embedding_model` / `embedding_model_version`
* `embedding_dimension`
* `embedding_config_fingerprint`
* `vector_record_schema_version`

Retrieval rejects incompatible fingerprints with a clear reindex message.
No silent querying of mismatched vectors.

## CLI

```bash
codestrata ai providers
codestrata ai config --config codestrata.toml
codestrata ai health --config codestrata.toml
codestrata ai health --live --config codestrata.toml
```

## MCP

`compose_repository_intelligence` builds providers via the same factories.
`repository_health` reports selected embedding/answer providers, models,
configuration health, and deterministic vs production mode.

## Non-goals

Anthropic, Azure OpenAI, Gemini, Ollama, vLLM, hybrid retrieval, reranking,
graph retrieval, conversation memory, agents, UI, REST API, repository
mutation, provider fallback, AWS infrastructure provisioning, report redesign.
