# Contributing

Thank you for contributing to the **CodeStrata Cursor Extension** (Community Edition).

## Scope

This extension is a **thin client** of **CodeStrata Engine**:

- Use public Engine CLI contracts and public report JSON only
- Do not duplicate Engineering Intelligence
- Do not add CodeStrata Platform dependencies
- Preserve Community Edition naming (never “CodeStrata AI” or “Enterprise Edition” as product names)

## Development

```bash
npm install
npm test
npm run test:host
npm run package:dry
```

Supported Node: **20.x or 22.x** (host tests via `@vscode/test-electron` work best on Node 22+).

## Conduct & security

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [PRIVACY.md](PRIVACY.md)

## Engine docs

Do not duplicate Engine documentation. Link to:

https://github.com/sknampally/codestrata-engine/blob/main/docs/quick-start.md
