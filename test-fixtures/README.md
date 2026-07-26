# Test fixtures (internal)

CodeStrata-owned language sample applications and golden sample reports used for
deterministic automated tests, local dogfood, and Community Engine export smoke.

**Not** part of the public `codestrata-examples` repository. Public examples are
real-world showcases under [`examples/`](../examples/).

```text
test-fixtures/
├── sample-js-app/
├── sample-python-app/
├── sample-java-app/
├── sample-php-app/
├── sample-csharp-app/
└── sample-reports/          # golden HTML/JSON from the samples above
```

## Assess a fixture

```bash
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
```

Default `codestrata.toml` points at `test-fixtures/sample-js-app`.

## Sample reports decision

Golden `sample-reports/` remain **internal** for CE documentation and
`tests/docs` validation. The public examples mirror instead ships curated
real-world `expected-results/` summaries — more representative of product
behavior than tiny synthetic apps.
