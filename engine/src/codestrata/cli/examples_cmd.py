"""List official sample repositories and documentation links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import typer


@dataclass(frozen=True, slots=True)
class ExampleEntry:
    name: str
    kind: str
    location: str
    notes: str


OFFICIAL_EXAMPLES: tuple[ExampleEntry, ...] = (
    ExampleEntry(
        name="sample-js-app",
        kind="test-fixture",
        location="test-fixtures/sample-js-app",
        notes="Bundled with Engine for offline quick start",
    ),
    ExampleEntry(
        name="sample-python-app",
        kind="test-fixture",
        location="test-fixtures/sample-python-app",
        notes="Python language sample (monorepo / fixture pack)",
    ),
    ExampleEntry(
        name="sample-java-app",
        kind="test-fixture",
        location="test-fixtures/sample-java-app",
        notes="Java / Maven language sample",
    ),
    ExampleEntry(
        name="sample-php-app",
        kind="test-fixture",
        location="test-fixtures/sample-php-app",
        notes="PHP language sample",
    ),
    ExampleEntry(
        name="sample-csharp-app",
        kind="test-fixture",
        location="test-fixtures/sample-csharp-app",
        notes="C# / .NET language sample",
    ),
    ExampleEntry(
        name="codestrata-examples",
        kind="showcase",
        location="https://github.com/sknampally/codestrata-examples",
        notes="Pinned real-world showcases (Spring PetClinic, eShop, Laravel)",
    ),
)

DOC_LINKS: tuple[tuple[str, str], ...] = (
    ("Quick start", "docs/quick-start.md"),
    ("CLI reference", "docs/cli-reference.md"),
    ("Installation", "docs/installation.md"),
    ("CI sample workflow", "examples/github-actions/codestrata-assess.yml"),
    ("Troubleshooting", "docs/troubleshooting.md"),
    ("Community edition", "docs/community-edition.md"),
)


def format_examples(*, json_output: bool = False) -> str:
    """Render official examples and documentation links."""

    if json_output:
        import json

        payload = {
            "examples": [
                {
                    "name": item.name,
                    "kind": item.kind,
                    "location": item.location,
                    "notes": item.notes,
                }
                for item in OFFICIAL_EXAMPLES
            ],
            "documentation": [{"title": title, "path": path} for title, path in DOC_LINKS],
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        "Official samples and documentation",
        "",
        "Samples:",
    ]
    for item in OFFICIAL_EXAMPLES:
        lines.append(f"  - {item.name} ({item.kind})")
        lines.append(f"      {item.location}")
        lines.append(f"      {item.notes}")
    lines.append("")
    lines.append("Documentation:")
    for title, path in DOC_LINKS:
        lines.append(f"  - {title}: {path}")
    lines.append("")
    lines.append("Try:")
    lines.append(
        "  codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai"
    )
    return "\n".join(lines)


def register_examples_command(app: typer.Typer) -> None:
    """Register ``codestrata examples``."""

    @app.command("examples")
    def examples_command(
        json_output: Annotated[
            bool,
            typer.Option("--json", help="Emit machine-readable JSON."),
        ] = False,
    ) -> None:
        """List official sample repositories and documentation links."""

        typer.echo(format_examples(json_output=json_output))


__all__ = [
    "DOC_LINKS",
    "OFFICIAL_EXAMPLES",
    "ExampleEntry",
    "format_examples",
    "register_examples_command",
]
