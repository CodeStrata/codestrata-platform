---
title: CodeStrata Engine
description: Overview of CodeStrata Engine — local Engineering Assessments for Community Edition.
---

# CodeStrata Engine

**CodeStrata Engine** is the Community assessment engine. It runs locally,
produces Engineering Assessments, and does not require CodeStrata Platform.

## What it does

- Assess a local repository or GitHub URL
- Apply deterministic Engineering Intelligence (rules + evidence)
- Emit HTML and JSON reports
- Optionally enrich with AI using your provider credentials
- Optionally expose MCP tools when the `mcp` extra is installed

## What it is not

- Not CodeStrata Platform
- Not an IDE (use the VS Code extension as a thin client)
- Not “CodeStrata AI” — AI is an optional capability

## Docs in this portal

| Topic | Page |
| ----- | ---- |
| Installation | [Installation](./installation) |
| Doctor | [Doctor](./doctor) |
| Assessments | [Engineering Assessments](/assessments/) |
| CLI | [CLI Reference](/reference/cli) |
| Configuration | [Configuration](/reference/configuration) |

Engine-specific technical depth (architecture, contracts, contributor internals)
remains in the Engine repository under `docs/`. See the
[Migration Plan](/MIGRATION_PLAN) for ownership boundaries.
