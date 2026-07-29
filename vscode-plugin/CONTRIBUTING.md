# Contributing

Thank you for contributing to the **CodeStrata VS Code Extension** (Community Edition).

## Scope

This extension is a **thin client** of **CodeStrata Engine**. Contributions should:

- Use public Engine CLI contracts and public report JSON only
- Avoid duplicating Engineering Intelligence
- Avoid CodeStrata Platform API dependencies
- Preserve Community Edition naming (never “CodeStrata AI” or “Enterprise Edition” as product names)

## Development

```bash
npm install
npm test
npm run test:host
npm run package:dry
```

Press **F5** in VS Code to launch an Extension Development Host.

## Design

Branding follows the CodeStrata Design System (amber strata accents, dark-first).  
Command and UI copy should say **Engineering Assessment** and **CodeStrata Engine**.

## Conduct & security

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [PRIVACY.md](PRIVACY.md)
- [SUPPORT.md](SUPPORT.md)

## Engine docs

Do not duplicate Engine documentation. Link to the Engine Quick Start and related docs instead:

https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md
