# Privacy

## Documentation site

- No account required
- No cookies required for reading docs
- Documentation site analytics remain off unless separately reviewed

## CodeStrata Engine (Community)

Anonymous product telemetry is **disabled by default** and requires **explicit
opt-in**.

| Topic | Detail |
| --- | --- |
| Opt in | First-run prompt (default **No**) or `codestrata telemetry enable` |
| Opt out | `codestrata telemetry disable` or `CODESTRATA_TELEMETRY=0` |
| Inspect | `codestrata telemetry show` |
| Reset id | `codestrata telemetry reset` |

### Collected when enabled

Installation id (UUID v4), CodeStrata version, OS, Python version, command name,
assessment domain categories, language categories, size/duration bands, AI
enabled/used flags, success/failure, timestamps.

### Never collected

Source code, repository names/URLs, file names/paths, findings, recommendations,
reports, prompts, AI responses, credentials, hostname, username, or email.

Full policy: repository [`PRIVACY.md`](https://github.com/CodeStrata/codestrata-engine/blob/main/PRIVACY.md)
and Engine docs [`telemetry.md`](https://github.com/CodeStrata/codestrata-engine/blob/main/docs/telemetry.md).

## Local assessment

CodeStrata Engine processes repositories on your machine (or CI you control).
IDE extensions invoke the Engine locally and do not store provider credentials in
the extension for Community assessment flows.

## Contact

Use the process in [Responsible Disclosure](./disclosure) / `SECURITY.md`.
Do not open public issues containing secrets.
