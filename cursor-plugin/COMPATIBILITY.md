# Compatibility

| Component | Supported range |
| --------- | --------------- |
| CodeStrata Cursor Extension | **0.2.x** |
| CodeStrata Engine | `>=0.1.0 <2.0.0` |
| Report schema | `1.x` (current **1.2**) |
| VS Code API (`engines.vscode`) | `^1.85.0` |

## Cursor versions

This extension targets **Cursor builds that expose the VS Code extension API** declared above.

Cursor compatibility depends on the VS Code APIs exposed by the installed Cursor release.
This package does **not** claim compatibility with specific Cursor marketing version numbers
that were not validated in a live Cursor IDE during packaging.

Automated tests use a **VS Code Extension Host** with Cursor-compatible APIs.

## Node (CI / packaging)

| Tooling | Recommendation |
| ------- | -------------- |
| Node.js | **20.x or 22.x** |
| `@vscode/test-electron` | Prefer **Node 22+** when running `npm run test:host` |

## Edition

Community Edition only. Platform / Portfolio / Executive Intelligence are out of scope.
