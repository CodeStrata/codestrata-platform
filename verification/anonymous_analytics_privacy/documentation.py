"""Documentation consistency checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.models import CheckResult, Defect


_REQUIRED_DOC_SNIPPETS: dict[str, tuple[str, ...]] = {
    "engine/docs/telemetry-anonymous-analytics.md": (
        "no collection",
        "installation_id",
    ),
    "engine/docs/telemetry-installation-identity.md": (
        "UUID",
        "machine",
    ),
    "engine/docs/telemetry-ai-analytics.md": (
        "construction",
        "model family",
        "OpenRouter",
    ),
    "engine/docs/telemetry-repository-aggregate-analytics.md": (
        "10",
        "language",
    ),
    "vscode-plugin/docs/analytics.md": (
        "identity-free",
        "unavailable",
        "allowed_for_session",
        "not transmitted",
    ),
    "vscode-plugin/docs/telemetry.md": (
        "Slice 10.7",
        "analytics.md",
    ),
}


_FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "analytics is collected in production",
    "analytics are transmitted",
    "analytics is transmitted to Community Cloud",
    "OpenRouter is supported for analytics",
)


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for rel, needles in _REQUIRED_DOC_SNIPPETS.items():
        path = monorepo / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and all(n.lower() in text.lower() for n in needles)
        checks.append(
            CheckResult(
                name=f"docs:present:{rel}",
                ok=ok,
                detail=rel,
                category="documentation",
                contract="docs",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "documentation defect",
                    rel,
                    "required snippets present",
                    "missing file or snippets",
                )
            )

    for rel in (
        "engine/docs/telemetry-anonymous-analytics.md",
        "engine/docs/telemetry-ai-analytics.md",
        "vscode-plugin/docs/analytics.md",
        "engine/PRIVACY.md",
        "vscode-plugin/PRIVACY.md",
    ):
        path = monorepo / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for claim in _FORBIDDEN_DOC_CLAIMS:
            bad = claim in text
            checks.append(
                CheckResult(
                    name=f"docs:no_false_claim:{rel}:{claim[:24]}",
                    ok=not bad,
                    category="documentation",
                    contract="docs",
                )
            )
            if bad:
                defects.append(
                    Defect(
                        "documentation defect",
                        rel,
                        "no production transmission claim",
                        claim,
                    )
                )

    # Exact-count limitation documented.
    repo_doc = monorepo / "engine/docs/telemetry-repository-aggregate-analytics.md"
    repo_text = repo_doc.read_text(encoding="utf-8") if repo_doc.is_file() else ""
    checks.append(
        CheckResult(
            name="docs:exact_count_limitation",
            ok="limitation" in repo_text.lower() and "count" in repo_text.lower(),
            category="documentation",
            contract="repository_aggregates",
        )
    )

    for item in checks:
        if not item.ok and all(d.component != item.name for d in defects):
            if item.name.startswith("docs:exact"):
                defects.append(
                    Defect("documentation defect", item.name, "pass", "fail")
                )
    return checks, defects
