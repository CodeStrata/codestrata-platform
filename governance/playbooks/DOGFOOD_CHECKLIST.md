# Dogfood Checklist

**Status:** Foundation  
**Authority:** Playbook

## Objective

Exercise CodeStrata as a new user would, and capture friction without expanding
scope into feature work unless defects are confirmed.

## Scope

Engine CLI flows and Platform API flows as applicable to the milestone.

## Engine path (Community)

- [ ] Install / editable install succeeds
- [ ] `codestrata init`
- [ ] `codestrata doctor`
- [ ] `codestrata assess --repo <sample> --output reports --no-ai`
- [ ] Open HTML report; skim Findings / Recommendations / Evidence
- [ ] (Optional) `--with-ai` only when credentials available

## Platform path (Commercial)

- [ ] Health / ready probes
- [ ] Ingest assessment artifacts (test harness or API)
- [ ] Engineering Snapshot / Knowledge Graph / Retrieval / Ask
- [ ] Portfolio / Executive Intelligence paths when in scope
- [ ] Cross-tenant denial behavior still correct

## Record

| Observation | Severity | Action |
| ----------- | -------- | ------ |
| <!-- TODO: fill during dogfood --> | | |

## Rules

1. Fix only **confirmed** product-experience or defect issues in dogfood phases.
2. Do not start documentation portal work from dogfood notes alone.

## References

- [CUSTOMER_DEMO_CHECKLIST.md](CUSTOMER_DEMO_CHECKLIST.md)
- [TESTING_STANDARDS.md](../standards/TESTING_STANDARDS.md)
