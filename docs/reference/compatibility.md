---
title: Compatibility
description: Compatibility expectations for CodeStrata Engine and IDE extensions.
---

# Compatibility

| Component | Expectation |
| --------- | ----------- |
| Engine | Python 3.12+ |
| VS Code Extension | Requires compatible Engine on PATH or configured path |
| Cursor Extension | Cursor / VS Code API compatibility; requires Engine |

Always run `codestrata version` and `codestrata doctor` when diagnosing
extension discovery issues.
