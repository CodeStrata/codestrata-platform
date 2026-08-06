# Cross-Client Telemetry Privacy Verification (Slice 9.14)

Verification-only package for Epic 9 Slice **9.14**. Proves the Engine CLI and
VS Code privacy-first telemetry runtimes follow the same product principles
while remaining **independently versioned**.

This package does **not**:

- create a shared runtime schema
- enable production telemetry
- add HTTP to VS Code
- modify Cursor
- change Community Cloud or Data Lake product behavior

## Run

From the monorepo root (with `.venv` and `PYTHONPATH` including Engine):

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m verification.privacy_first_telemetry
```

Optional:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m verification.privacy_first_telemetry \
  --monorepo-root . \
  --output-dir reports/verification/sv9-14
```

Pytest:

```bash
PYTHONPATH=engine/src:. .venv/bin/python -m pytest tests/verification/privacy_first_telemetry -q
```

VS Code unit tests (separate; recommended alongside this suite):

```bash
cd vscode-plugin && npm test
```

## Output

```
reports/verification/sv9-14/
├── cross-client-telemetry-privacy-verification.json
└── cross-client-telemetry-privacy-verification.md
```

Reports are gitignored under `reports/`.

## Contract

| Field | Value |
| ----- | ----- |
| schema_name | `cross-client-telemetry-privacy-verification` |
| schema_version | `1.0.0` |
| Engine runtime | `community-telemetry-runtime-policy:1.0` |
| Engine events | `community-telemetry-runtime-event:1.0` |
| VS Code runtime | `community-vscode-telemetry-runtime-policy:1.0` |
| VS Code events | `community-vscode-telemetry-event-schema:1.0` |

## Shared principles (verification metadata)

Disabled by default · explicit session/command consent · no persistence · no
prior reuse · no installation identity · typed events · mandatory privacy
projection · forbidden repository/path/source/Finding/Evidence/prompt/credential
data · deterministic preview · unavailable default transport · fail-silent
isolation · no queue/retry · no payload logging · no Platform/Data Lake runtime
dependency.

## Intentional differences

| Topic | Engine | VS Code |
| ----- | ------ | ------ |
| Session | one CLI process | one command invocation |
| Client | `codestrata_cli` | `vscode_extension` |
| Events | includes `application_*` | feature/operation only |
| Transport | explicit HTTP exists (non-default) | unavailable only |
| Consent UX | CLI prompt / flags | native Allow/Deny |

## Confirmations

- Slice 9.15 completion: [`../privacy_first_telemetry_completion/README.md`](../privacy_first_telemetry_completion/README.md)
- No shared runtime schema
- Cursor unchanged
- Assessment schema remains 1.2
- Production collection is not operational
- Epic 10 is not started

## Related

- Engine: `engine/docs/telemetry.md`, `telemetry-event-catalog.md`, `telemetry-preview.md`, `telemetry-assessment-isolation.md`
- VS Code: `vscode-plugin/docs/telemetry.md`, `PRIVACY.md`
- Architecture: `ARCHITECTURE.md`
- Completion: [`../privacy_first_telemetry_completion/README.md`](../privacy_first_telemetry_completion/README.md)
