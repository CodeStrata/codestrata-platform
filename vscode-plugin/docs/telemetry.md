# VS Code privacy-first telemetry (Slice 9.13)

**Policy:** `community-vscode-telemetry-runtime-policy:1.0`  
**Event schema:** `community-vscode-telemetry-event-schema:1.0`  
**Client:** `vscode_extension` (independently versioned from Engine `codestrata_cli`)

Community workflow orchestration (Slice 13.1) calls consent at one explicit
point for eligible assessment commands — after CLI discovery succeeds
(Slice 13.2; see [cli-discovery.md](cli-discovery.md) and
[community-workflow.md](community-workflow.md)). Discovery failures do not
prompt telemetry.

## Purpose

Command-scoped, privacy-first telemetry runtime for the CodeStrata VS Code
extension. Disabled by default. No HTTP. No persistence. No installation
identity.

## Session definition

One eligible **command invocation** = one telemetry session.

Not activation lifetime, workspace lifetime, or extension lifetime.

## Consent

| Decision | Meaning |
| -------- | ------- |
| `disabled_by_default` | No prompt / not allowed |
| `allowed_for_session` | Explicit Allow for this command |
| `denied_for_session` | Explicit Deny / dismiss |
| `non_interactive_disabled` | CI / headless / automation |

Never written to `globalState`, `workspaceState`, settings, or `secretStorage`.

## Eligible commands

- `codestrata.assess`
- `codestrata.assessWithAi`

Excluded: install, doctor, init, report/findings/recommendations UI, welcome,
docs, output, activation.

## Prompt UX

VS Code information message:

> Allow privacy-safe anonymous product telemetry for this CodeStrata command
> only? Nothing is saved.

Buttons: **Allow** / **Deny**. Default = Deny (dismiss counts as Deny).
Prompt failure = Deny. At most one prompt per command.

Non-interactive when `CI=true/1` or
`CODESTRATA_VSCODE_TELEMETRY_NON_INTERACTIVE=1`.

## Events

Bounded types: `feature_invoked`, `feature_completed`, `operation_failed`.

Safe fields only (no workspace, repository, document, path, Finding, Evidence,
prompt/response, credentials, provider/model/token/cost, CLI argv).

`ai_used` is boolean only.

## Privacy projection

Mandatory before transport. Rejects unknown/forbidden keys and unsafe values.
Never echoes rejected values.

## Transport

`UnavailableExtensionTelemetryTransport` by default:

- no HTTP
- no endpoint
- no auth
- no queue / retry
- deterministic `unavailable`

Capture transport is test-only.

## Isolation

`runCommandWithTelemetryIsolation` records invoke → primary → complete/fail.
Telemetry failures never change command results or replace command errors.

## Engine catalog relationship

The public Engine catalog
(`engine/docs/telemetry-event-catalog.json`) is a **conceptual** vocabulary
reference. Schemas are not identical:

| | Engine | VS Code |
| --- | --- | --- |
| Client | `codestrata_cli` | `vscode_extension` |
| Policy | Engine runtime 1.0 | VS Code runtime 1.0 |
| HTTP | Engine Slice 9.11 (explicit) | Deferred |

Platform extension-event mapping is deferred.

## Output channel

Never logs payloads, consent decisions with secrets, paths, workspace URIs,
endpoints, or credentials.

## Cursor extension (removed)

The former CodeStrata Cursor Extension product is **not** an active telemetry
emitter (removed in Epic 12). Cross-client verification (Slice 9.14) confirmed
it had no privacy-first telemetry runtime. Slice 12.4 retires
`cursor_extension` from active Community client vocabularies; historical
schema 1.0 records may still deserialize
(`community-retired-client-policy:1.0`).

## Cross-client verification

Shared privacy principles with the Engine CLI are verified by
[`../../verification/privacy_first_telemetry/README.md`](../../verification/privacy_first_telemetry/README.md)
(`cross-client-telemetry-privacy-verification` @ `1.0.0`). Schemas remain
independently versioned — this package does not merge runtimes.

Epic 9 completion (Slice 9.15):
[`../../verification/privacy_first_telemetry_completion/README.md`](../../verification/privacy_first_telemetry_completion/README.md).
Production collection is **not operational**. The former Cursor extension is
not an active telemetry emitter. Epic 10 Slice 10.1 defines an Engine-side
anonymous analytics **contract only** (no collection yet). Slice 10.2 adds
local anonymous installation identity (unused operationally; no transmission).
Slice 10.3 adds Engine-side local runtime analytics construction (no
transmission; not wired into the VS Code runtime). Slice 10.4 adds Engine-side
assessment analytics construction APIs (not wired into assess; VS Code unchanged).
Slice 10.5 adds Engine-side repository aggregate analytics construction APIs
(unwired; VS Code unchanged). Slice 10.6 adds Engine-side AI analytics
construction APIs (unwired from VS Code runtime). Slice 10.7 adds VS Code
anonymous analytics construction
([analytics.md](analytics.md)) — local, identity-free, unavailable sink;
not transmitted or persisted. Slice 10.8 owns full privacy verification.
Slice 10.9 completes Epic 10 verification
([`../../verification/anonymous_analytics_completion/`](../../verification/anonymous_analytics_completion/))
— analytics remain contracts-only and not operational in production.

## Epic 13 integration

See [telemetry-consent-integration.md](./telemetry-consent-integration.md) (Slice 13.9): readiness before consent; command-local Deny-default; transport unavailable.

## Related

- [../PRIVACY.md](../PRIVACY.md)
- [../README.md](../README.md)
- Engine: `engine/docs/telemetry-runtime.md`
- Engine analytics contract: `engine/docs/telemetry-anonymous-analytics.md`
- Verification: `verification/privacy_first_telemetry/README.md`
- Completion: `verification/privacy_first_telemetry_completion/README.md`
- Epic 10 completion: `verification/anonymous_analytics_completion/README.md`
