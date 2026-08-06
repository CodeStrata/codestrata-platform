# Anonymous Analytics Privacy Verification (Slice 10.8)

Verification-only package for Epic 10 Slice **10.8**. Proves all Epic 10
anonymous analytics contracts satisfy the intended privacy guarantees.

This package does **not**:

- enable analytics collection or transmission
- add HTTP analytics transport to VS Code
- add Community Cloud / Data Lake analytics processors
- merge Engine and VS Code analytics schemas
- modify Cursor
- start Slice 10.9

## Run

From the monorepo root:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m verification.anonymous_analytics_privacy
```

Optional:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m verification.anonymous_analytics_privacy \
  --monorepo-root . \
  --output-dir reports/verification/sv10-8
```

Pytest:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m pytest tests/verification/anonymous_analytics_privacy -q
```

Recommended adjacent suites:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m pytest engine/tests/telemetry -q
cd vscode-plugin && npm test
```

## Output

```
reports/verification/sv10-8/
├── anonymous-analytics-privacy-verification.json
└── anonymous-analytics-privacy-verification.md
```

Reports are gitignored under `reports/`.

## Contract

| Field | Value |
| ----- | ----- |
| schema_name | `anonymous-analytics-privacy-verification` |
| schema_version | `1.0.0` |
| Engine base | `community-anonymous-analytics-*:1.0` |
| Identity | `community-anonymous-installation-identity-*:1.0` |
| Runtime / assessment / repository / AI | independent `*:1.0` policies |
| VS Code | `community-vscode-anonymous-analytics-*:1.0` |

## Scope

- base analytics contract
- anonymous installation identity (Engine-only)
- runtime / assessment / repository aggregate / AI analytics
- VS Code analytics (consent-gated, identity-free, unavailable sink)
- consent / persistence / transport / isolation
- forbidden-category matrix
- documentation and package boundaries

## Intentional Engine / VS Code differences

| Topic | Engine | VS Code |
| ----- | ------ | ------- |
| Wiring | Construction APIs only (unwired) | Consent-gated local construction |
| Identity | Local envelope may include UUID | Identity-free |
| Sink | No analytics HTTP | Unavailable sink |
| AI detail | Provider/model families | Boolean `ai_used` only |

## Limitations

- Bounded exact language counts remain an intentional privacy limitation
- Full VS Code extension-host UI automation is not required for this slice
- Slice 10.9 owns Epic 10 completion verification

## Slice 10.9

Epic 10 completion verification lives in
[`../anonymous_analytics_completion/README.md`](../anonymous_analytics_completion/README.md).
It re-runs this Slice 10.8 verification live and does not trust a stale report.
Analytics remain contracts-only and not operational in production.

## Related

- Engine: `engine/docs/telemetry-anonymous-analytics.md`
- VS Code: `vscode-plugin/docs/analytics.md`
- Epic 9 cross-client: `verification/privacy_first_telemetry/`
