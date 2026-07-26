# Sample reports (Community Edition)

Deterministic HTML + JSON assessments generated from the bundled language
samples. Open `report.html` in a browser, or regenerate locally:

```bash
codestrata assess --repo examples/sample-js-app --output reports --no-ai
codestrata assess --repo examples/sample-python-app --output reports --no-ai
codestrata assess --repo examples/sample-java-app --output reports --no-ai
codestrata assess --repo examples/sample-php-app --output reports --no-ai
codestrata assess --repo examples/sample-csharp-app --output reports --no-ai
```

| Language | Directory | Source sample |
| -------- | --------- | ------------- |
| JavaScript | [javascript/](javascript/) | `examples/sample-js-app` |
| Python | [python/](python/) | `examples/sample-python-app` |
| Java | [java/](java/) | `examples/sample-java-app` |
| PHP | [php/](php/) | `examples/sample-php-app` |
| C# / .NET | [csharp/](csharp/) | `examples/sample-csharp-app` |

Each directory contains:

* `report.html` — HTML Report v2 (footer: Community Edition)
* `report.json` — assessment document
* `findings.json` — deterministic findings

Interpretation guide: [docs/report-interpretation.md](../../engine/docs/report-interpretation.md).
