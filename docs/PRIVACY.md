# Privacy

## Documentation website

The CodeStrata documentation portal is a static site:

- No account or login
- No cookies required for reading docs
- No analytics by default

## Community Engine telemetry

Anonymous telemetry for CodeStrata Engine is **disabled by default** and requires
**explicit opt-in**. See [Security → Privacy](/security/privacy) and the Engine
`PRIVACY.md` / `docs/telemetry.md` files.

Commands:

```bash
codestrata telemetry status
codestrata telemetry enable
codestrata telemetry disable
codestrata telemetry reset
codestrata telemetry show
```

## Local tools

CodeStrata Engine and IDE extensions process repositories under your control.
This documentation site does not receive your source code.

Do not paste secrets, private keys, or private repository URLs into public issues
or documentation PRs.
