# Rule Platform Migration (Phase 4.1.1)

Public product: **CodeStrata**. Internals remain `codestrata`.

## Current architecture

```text
Assessment
    │
    ├── Legacy RuleEngine  →  Finding   (production path for codestrata assess)
    └── Shared Rule Platform → Finding  (Phase 4.1 infrastructure; opt-in)
```

Assessment continues to call `RuleEngine` directly. Behaviour, finding IDs,
reports, and recommendations are unchanged.

## Target architecture

```text
Assessment
        │
        ▼
RuleExecutionFacade
        │
        ├── LegacyRuleAdapter  (wraps existing Rule objects)
        │
        └── SharedRuleExecutor (native SharedRule packs)
                │
                ▼
        Existing Finding / Recommendation models
```

## Compatibility layer (4.1.1)

| Component | Role |
| --------- | ---- |
| `LegacyRuleAdapter` | Exposes SharedRule metadata/applicability; `evaluate_legacy` passthrough preserves Findings |
| `RuleExecutionFacade` | Strategic entry: `evaluate` (= RuleEngine), `evaluate_adapted`, `execute_shared` |
| `rule_execution_context_from_legacy` | Attaches `RuleContext` onto `RuleExecutionContext` |

Guarantee for adapted legacy rules:

Same repository → same legacy rule → same finding ID, severity, title,
description, evidence, metadata → same recommendations → same report inputs.

## Migration strategy

```text
Legacy Rule
    → Adapter (LegacyRuleAdapter)
    → SharedRule registration (optional)
    → Native SharedRule rewrite (future pack milestones)
```

Recommended steps per rule (no bulk migration in 4.1.1):

1. Keep the production RuleEngine path.
2. Add compatibility tests: `RuleEngine.evaluate` vs
   `RuleExecutionFacade.evaluate_adapted`.
3. Optionally register adapters on the shared registry for inspection only.
4. When rewriting as a native SharedRule, freeze finding identity fixtures first.
5. Switch assessment to the facade only when adapted and native packs produce
   equivalent findings under the same tests.

## Deprecation plan

- **Now:** Dual stacks; RuleEngine remains operational; facade is additive.
- **Next (pack milestones):** New rules are SharedRules only, executed via the
  facade.
- **Later:** Assessment may call `RuleExecutionFacade.evaluate` once parity is
  proven; legacy Rule classes remain until each is rewritten or retired.
- **Do not** remove RuleEngine or rewrite all builtins in this milestone.

## Strategic direction

The Shared Rule Platform is the **strategic execution architecture** for
Analysis Intelligence. The RuleEngine remains the **production assessment**
path until an explicit, tested cutover.
