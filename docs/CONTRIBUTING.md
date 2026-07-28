# Contributing to CodeStrata Docs

Thank you for contributing to the public documentation portal.

## Principles

1. Use product names correctly: **CodeStrata**, **CodeStrata Engine**,
   **CodeStrata Platform**, **Engineering Intelligence**, **Engineering Assessment**,
   **Community Edition**.
2. Do not use “CodeStrata AI” as a product name. AI is a capability.
3. Do not present Platform features as Community capabilities.
4. Document only working Community commands.
5. Prefer concise, journey-oriented pages over dumping internal Markdown.
6. **Documentation visibility:** every new document must declare or clearly imply
   whether it is (a) public Community documentation, (b) public contributor
   documentation, or (c) private Platform/internal documentation. Prefer an HTML
   comment marker such as
   `<!-- documentation-visibility: public-community -->`
   (also `public-contributor`, `public-contract`, or `private-internal`).
   Do not publish private classification inventories in public repositories.

## Setup

```bash
npm install
npm run dev
```

## Before you open a PR

```bash
npm test
```

## Structure

- Journeys and product pages: section folders under this repository
- Theme / tokens: `.vitepress/`
- Do not import monorepo `governance/` or `platform/` at build time

## Link policy

Prefer public URLs (`docs.codestrata.ai`, `codestrata.ai`, public GitHub).
Avoid private monorepo paths and localhost links in published content.
