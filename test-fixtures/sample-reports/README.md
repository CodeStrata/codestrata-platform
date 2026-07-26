# Sample reports (Community Edition)

Deterministic HTML + JSON assessments generated from the bundled language
samples. Open `report.html` in a browser, or regenerate locally:

```bash
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
codestrata assess --repo test-fixtures/sample-python-app --output reports --no-ai
codestrata assess --repo test-fixtures/sample-java-app --output reports --no-ai
codestrata assess --repo test-fixtures/sample-php-app --output reports --no-ai
codestrata assess --repo test-fixtures/sample-csharp-app --output reports --no-ai
```

| Language | Directory | Source sample |
| -------- | --------- | ------------- |
| JavaScript | [javascript/](javascript/) | `test-fixtures/sample-js-app` |
| Python | [python/](python/) | `test-fixtures/sample-python-app` |
| Java | [java/](java/) | `test-fixtures/sample-java-app` |
| PHP | [php/](php/) | `test-fixtures/sample-php-app` |
| C# / .NET | [csharp/](csharp/) | `test-fixtures/sample-csharp-app` |

Each directory contains:

* `report.html` — HTML Report v2 (footer: Community Edition)
* `report.json` — assessment document
* `findings.json` — deterministic findings

Interpretation guide: [docs/report-interpretation.md](../../engine/docs/report-interpretation.md).
