# Grounded Repository Answering (Phase 5.6 / 5.8)

**Status:** Complete — provider-neutral grounded answers over `RepositoryRetriever`.
Deterministic extractive answering remains the default. Phase 5.8 adds optional
Bedrock and OpenAI answer providers (see [ai-providers.md](ai-providers.md)).

## Architecture

```text
RepositoryQuestion
        ↓
RepositoryRetriever
        ↓
RetrievalResult
        ↓
Grounding Context
        ↓
AnswerProvider
        ↓
Draft Grounded Answer
        ↓
Citation and Grounding Validation
        ↓
GroundedAnswerResult
```

`GroundedAnswerEngine` receives existing `RepositoryRetriever` and
`AnswerProvider` instances. It does **not** create databases, vector stores,
embeddings, projections, chunks, or production AI services.

## Contracts

| Contract | Schema |
| -------- | ------ |
| `GroundedAnswerRequest` | `grounded-answer-request` 1.0.0 |
| `GroundedAnswerResult` | `grounded-answer-result` 1.0.0 |
| `GroundedAnswer` | `grounded-answer` 1.0.0 |
| `AnswerStatement` | `answer-statement` 1.0.0 |
| `AnswerCitation` | `answer-citation` 1.0.0 |

Supporting types: `AnswerSection`, `AnswerEvidence`, `AnswerCoverage`,
`AnswerDiagnostic`, `AnswerLimitation`, `AnswerStatus`, `AnswerConfidence`,
`AnswerStyle`, `AnswerStatementType`.

Required request scope: `tenant_id` + `repository_id` (via `RetrievalScope`).
Cross-tenant / cross-repository answering is rejected by retrieval scope and
grounding validation.

## Answer styles

`concise` | `detailed` | `findings_summary` | `recommendation_summary` |
`architecture_explanation` | `evidence_only`

Styles organize output only. They do **not** change retrieval providers or
trigger hidden AI behavior.

## AnswerProvider abstraction

Protocol methods: `generate`, `health`, `capabilities`, `model_identity`.

Provider request carries normalized question, selected hits, citation labels,
style, and output constraints. It must **not** include DB connections,
embedding arrays, credentials, or unrelated repository data.

### DeterministicExtractiveAnswerProvider

Initial provider for unit/integration/dogfood validation:

- Selects relevant retrieved excerpts
- Preserves source sentences or bounded excerpts
- Attaches existing `SRC-*` citations to every factual statement
- Never invents facts outside retrieved content
- Stable / byte-identical for identical inputs
- Declares `is_production_model=false`, `is_generative_ai=false`,
  `supports_freeform_synthesis=false`, `supports_streaming=false`

**Deterministic extraction is not generative AI.** Production language quality
requires a future model provider that still obeys citation and grounding
contracts.

Reserved (unimplemented) providers: `bedrock`, `openai`, `anthropic`,
`local_model`. Selecting one raises an explicit configuration error — never a
silent fallback to deterministic extraction.

## Citation and grounding validation

When `require_citations=true`:

- Every factual statement needs ≥1 valid citation from the retrieval result
- Citation metadata must match the underlying `RetrievalHit`
- Labels preserve retrieval ordering; duplicates are deduplicated
- Limitation / insufficient-evidence statements may omit citations

Grounding (deterministic only):

- Normalized text containment **or** bounded token overlap (≥ 0.45)
- Scope checks: tenant, repository, optional scan / branch / commit
- Unsupported statements are excluded (never returned silently)
- Result becomes `PARTIAL` if some statements remain; otherwise
  `INSUFFICIENT_EVIDENCE` / `FAILED`

No semantic entailment, LLM judging, or model-based grounding.

## Insufficient evidence

Distinct diagnostics cover empty retrieval, low scores, ungroundable hits,
filter/budget exclusion, malformed content, and provider failure.

Default message:

> The indexed repository evidence is insufficient to answer this question.

The engine does not guess, use general programming knowledge, or infer
unsupported repository behavior.

## Statuses

| Status | Meaning |
| ------ | ------- |
| `SUCCESS` | Answer produced; factual statements grounded; citations OK |
| `PARTIAL` | ≥1 grounded statement; some coverage/statements excluded |
| `INSUFFICIENT_EVIDENCE` | Retrieval OK but cannot support an answer |
| `EMPTY` | No eligible retrieval hits |
| `FAILED` | Retrieval / provider / validation / orchestration failure |
| `DISABLED` | `knowledge.answering.enabled = false` |

## Confidence

Bands: `HIGH` | `MEDIUM` | `LOW` | `NONE` — from measurable factors only:

- Mean retrieval score of cited hits
- Number of supporting sources / independent documents
- Citation coverage of factual statements
- Grounding exclusions

Not probabilistic certainty.

Approximate rules:

- **HIGH** — mean score ≥ 0.55, ≥2 sources, full citation coverage, no
  grounding exclusions, ≥2 factual statements
- **MEDIUM** — mean score ≥ 0.25, meets `minimum_supporting_sources`,
  citation coverage ≥ 0.8
- **LOW** — ≥1 supporting source and some citation coverage
- **NONE** — otherwise / insufficient evidence

## Configuration

```toml
[knowledge.answering]
enabled = false
provider = "deterministic_extractive"
style = "concise"
max_answer_characters = 12000
max_statements = 20
minimum_supporting_sources = 1
require_citations = true
fail_on_insufficient_evidence = false
include_evidence = true
include_retrieval_context = false
include_diagnostics = true
write_answer_artifact = false
answer_filename = "repository-grounded-answer.json"

[knowledge.answering.deterministic_extractive]
max_excerpt_characters = 800
max_statements_per_source = 2
preserve_source_sentences = true
```

Independent of projection, chunking, embedding, indexing, vector_store, and
retrieval sections.

## Artifact

Optional `repository-grounded-answer.json` (when
`write_answer_artifact = true`): request summary, status, statements,
citations, confidence, coverage, diagnostics, provider identity, retrieval
fingerprint. Never embeddings, secrets, DB URLs, or hidden prompts.

## Future production providers

Bedrock / OpenAI / Anthropic / local models must:

1. Consume the same `AnswerProviderRequest`
2. Emit citation-bound statements using retrieval `SRC-*` labels
3. Pass identical citation + grounding validation
4. Never silently invent uncited facts

## Out of scope (Phase 5.6)

Production AI providers, Bedrock/OpenAI/Anthropic/local LLM calls, production
embeddings, hybrid retrieval, graph expansion, reranking, conversational
memory, MCP, AWS infrastructure.
