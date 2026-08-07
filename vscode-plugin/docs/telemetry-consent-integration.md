# Telemetry consent integration (Slice 13.9)

Policy: `community-vscode-telemetry-integration-policy:1.0`

Attaches Epic 13 Community workflow to the Slice 9.13 privacy-first telemetry
runtime (`community-vscode-telemetry-runtime-policy:1.0`). Does not redesign
runtime mechanics, event schemas, or analytics schemas.

## Eligible commands

| Command | Operation | Telemetry |
| --- | --- | --- |
| `codestrata.assess` | `run_assessment` | eligible |
| `codestrata.assessWithAi` | `run_assessment_with_ai` | eligible |

All other commands (init, install, doctor, open report, activation, recovery
actions themselves) are **ineligible**.

## Readiness before consent

1. Workspace eligibility
2. Repository initialization readiness
3. Compatible CLI discovery
4. Optional AI confirmation (AI command only)
5. **Command-local telemetry consent**
6. Consent-gated analytics construction
7. Progress lifecycle
8. One Engine assessment invocation

If AI confirmation is declined, consent is **not** shown.

## Consent rules

- Scope: **command-local** (one decision per eligible invocation)
- Default: **Deny** (dismissal = Deny)
- Never persisted; never reused across commands
- Non-interactive / CI: no prompt → `non_interactive_disabled`
- Deny / prompt failure: assessment still runs
- Allow: privacy projection mandatory; transport remains **unavailable** (no HTTP)
- Analytics constructs only when decision is `allowed_for_session`

## Recovery semantics

- Recovery UI itself does not prompt for telemetry
- **Run Assessment Again** starts a **new** `codestrata.assess` → **fresh** consent
- Open Report / Initialize / Install / Documentation → no telemetry

## Boundaries

- Report opening: no consent, no events
- Init / discovery / install guidance: no consent
- Activation: no consent, no events
- No `machineId`, no installation identity
- Engine and VS Code telemetry schemas remain independent

## Deferred

~~Authoritative source-local verification — Slice **13.10**~~ — [source-locality.md](./source-locality.md).  
~~Marketplace branding — Slice **13.12**~~ — [marketplace-branding.md](./marketplace-branding.md). ~~Marketplace documentation — Slice **13.13**~~ — [marketplace-documentation.md](./marketplace-documentation.md). Clean install validation — Slice **13.14**.

## Related

- [telemetry.md](./telemetry.md)
- [analytics.md](./analytics.md)
- [assessment-execution.md](./assessment-execution.md)
- [failure-recovery.md](./failure-recovery.md)
- [community-workflow.md](./community-workflow.md)
