# VS Code anonymous analytics (Epic 10 Slice 10.7)

**Policy:** `community-vscode-anonymous-analytics-policy:1.0`  
**Schema:** `community-vscode-anonymous-analytics-schema:1.0`  
**Status:** Local construction only — **not transmitted**, **not persisted**,
unavailable sink default

## Purpose

Construct privacy-safe VS Code extension usage analytics for eligible assess
commands, building on the Slice 9.13 command-local telemetry consent model
without weakening it.

```text
Eligible VS Code command
        │
        ▼
Existing command-local consent
        │
        ▼
Existing typed privacy-first telemetry event
        │
        ▼
Mandatory privacy projection
        │
        ▼
VS Code analytics aggregate input
        │
        ▼
VS Code analytics event
        │
        ▼
Local preview / validation
        │
        ▼
Unavailable analytics sink
        │
        ▼
(Not persisted / not transmitted)
```

## Product-path decision

**Construction APIs + controlled integration through
`runCommandWithTelemetryIsolation`, with unavailable sink only.**

When an eligible assess command runs:

1. command-local consent (Slice 9.13) is evaluated
2. telemetry events are recorded as before
3. if consent is `allowed_for_session`, analytics events are constructed locally
4. analytics are delivered only to the unavailable sink (or test capture sink)
5. primary command result remains authoritative

This does **not** mean VS Code analytics are collected in production.
There is no HTTP transport, queue, retry, worker, or persistence.

## Exact collected fields

| Field | Meaning |
| ----- | ------- |
| `client_name` | Always `vscode_extension` |
| `editor` | Always `vscode` |
| `extension_version` | Package version (semver-like, max 32) |
| `release_adoption` | `stable` / `prerelease` / `development` / `unknown` |
| `operation_category` | `assess` or `assess_with_ai` |
| `lifecycle` | `feature_invoked` / `feature_completed` / `operation_failed` |
| `outcome` | Command execution only: `success` / `failure` / `cancelled` |
| `duration_bucket` | Coarse bucket only (optional) |
| `ai_used` | Boolean only |
| `failure_category` | Optional bounded category on non-success |
| schema/policy/runtime version tokens | Contract versions |

## Eligible / excluded commands

Eligible (mapped to bounded categories):

- `codestrata.assess` → `assess` (`ai_used=false`)
- `codestrata.assessWithAi` → `assess_with_ai` (`ai_used=true`)

Excluded (no analytics): install, doctor, init, open report, findings /
recommendations UI, welcome, docs, output, activation, compatibility-only flows.

Raw command IDs are **not** serialized.

## Consent relationship

Reuses Slice 9.13 command-local consent. **No second analytics prompt.**

| Decision | Analytics construction |
| -------- | ---------------------- |
| `disabled_by_default` | No |
| `denied_for_session` | No |
| `non_interactive_disabled` | No |
| `allowed_for_session` | Yes (local only) |

Consent does not enable transport. Consent is not persisted.

## Identity

Slice 10.7 events are **identity-free**.

- no installation ID generation
- no `vscode.env.machineId`
- no `telemetrySessionId`
- no Engine `anonymous-installation-identity.json` reads
- no workspace / repository / document identity

Cross-client installation continuity requires a future explicit contract and is
**not** implemented here.

## Release adoption

Classified from the injected extension version only (no Marketplace / network):

| Category | Rule |
| -------- | ---- |
| `development` | `0.x` or contains `dev` |
| `prerelease` | pre-release label (`alpha` / `beta` / `rc` / `pre` / other `-` labels) |
| `stable` | otherwise valid semver-like |
| `unknown` | classification unavailable |

Current package version `0.2.0` classifies as `development`.

## Duration / AI / provider

- Duration: coarse buckets only (`lt_1s` … `gt_5m`, `unknown`). No exact ms.
- AI: boolean only. No provider family, model family, tokens, or cost.
- Provider/model analytics remain Engine Slice 10.6 only.

## Sink / transport

Default: `UnavailableVsCodeAnalyticsSink` → deterministic `unavailable`.

- no HTTP / endpoint / credentials
- no filesystem / queue / retry / worker / background task
- capture sink is test-only

Platform extension-event mapping is deferred.

## Privacy guarantees

Rejected (typed allowlists + structural checks):

- installation / machine / session IDs
- workspace / repository / document / path / URI
- argv / stdout / stderr / output text
- Finding / Evidence / Recommendation / source
- prompt / response / credentials
- provider / model / token / cost
- timestamps / exact duration

Analytics never writes payloads to the output channel.

## Engine relationship

Conceptual shared vocabulary only. Schemas are **not** identical:

| | Engine | VS Code |
| --- | --- | --- |
| Owner | Python | TypeScript |
| Schema token | Engine analytics 1.0 | VS Code analytics 1.0 |
| Identity | May use local installation identity | Identity-free (10.7) |
| Provider/model | Slice 10.6 | Not collected |
| HTTP | Deferred / separate | Unavailable |

No Engine Python imports at runtime.

## Cursor / Platform / Data Lake

- Former Cursor extension product removed (Epic 12); not an active analytics emitter
- Slice 12.4: `cursor_extension` is a retired historical client value only
  (`community-retired-client-policy:1.0`) — not accepted for current ingestion
  or active storage projection
- Community Cloud / Data Lake production ingestion remains fail-closed / unwired
- No Platform DTO / event_id / HTTP mapping

## Package surface

No new commands, settings, activation events, status-bar contributions, endpoint
settings, token settings, or identity settings.

## Slice 10.8

Full privacy verification across Epic 10 is provided by Slice 10.8 ([`../../verification/anonymous_analytics_privacy/`](../../verification/anonymous_analytics_privacy/)).

## Slice 10.9

Epic 10 completion verification is provided by Slice 10.9
([`../../verification/anonymous_analytics_completion/`](../../verification/anonymous_analytics_completion/)).
Analytics remain contracts-only and not operational in production.

## Related

- [telemetry.md](telemetry.md)
- [../PRIVACY.md](../PRIVACY.md)
- [../README.md](../README.md)
- Engine analytics contract: `engine/docs/telemetry-anonymous-analytics.md`
- Engine AI analytics: `engine/docs/telemetry-ai-analytics.md`
