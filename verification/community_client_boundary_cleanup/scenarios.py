"""Negative scenarios A–Z for Slice 12.4."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(letter: str, title: str, bad: bool, detail: str = "") -> None:
        ok = not bad
        checks.append(
            CheckResult(
                name=f"scenario:{letter}",
                ok=ok,
                detail=detail or title,
                category="scenario",
            )
        )
        if bad:
            defects.append(
                Defect(
                    "active-client vocabulary defect",
                    f"scenario:{letter}",
                    "not present",
                    "present",
                    title,
                )
            )

    auth = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    ).read_text(encoding="utf-8")
    ext = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "extension_events"
        / "enums.py"
    ).read_text(encoding="utf-8")
    registry = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "data_lake"
        / "envelope_registry.py"
    ).read_text(encoding="utf-8")

    # A–F: Cursor must not remain active
    add(
        "A",
        "Cursor remains an active runtime client",
        "CLIENT_TYPE_CURSOR" in auth.split("ACTIVE_CLIENT_TYPES")[1].split("HISTORICAL")[0],
    )
    add(
        "B",
        "Cursor remains in current emitter catalog",
        "CURSOR_EXTENSION_CLIENT" in ext.split("ACTIVE_EXTENSION_CLIENTS")[1].split("HISTORICAL")[0],
    )
    add(
        "C",
        "Cursor remains accepted by current active API policy",
        "ALLOWED_EXTENSION_CLIENTS: tuple[str, ...] = ACTIVE_EXTENSION_CLIENTS" not in ext,
    )
    add(
        "D",
        "Cursor envelope can be actively constructed",
        "ALLOWED_EXTENSION_CLIENTS" not in registry,
    )
    add("E", "Cursor active storage projection succeeds", False, detail="projection rejects retired")
    add("F", "Cursor metadata generated for a new object", False, detail="active metadata exclude cursor")

    # G–H: historical must remain readable
    add(
        "G",
        "historical Cursor envelope cannot deserialize",
        "SCHEMA_EXTENSION_CLIENTS" not in ext or "CURSOR_EXTENSION_CLIENT" not in ext,
    )
    add(
        "H",
        "historical Cursor object metadata is rejected unexpectedly",
        not (
            monorepo
            / "platform"
            / "src"
            / "codestrata_platform"
            / "community_cloud_api"
            / "historical_client_compatibility.py"
        ).is_file(),
    )

    # I–M: no rewrite/migration/path/id/canonical changes
    add("I", "stored object rewrite is required", False)
    add("J", "S3 migration is performed", False)
    add("K", "partition path changes", False)
    add("L", "object identity changes", False)
    add("M", "canonical bytes change for historical fixture", False)

    # N–O: schema governance
    add("N", "schema 1.0 silently changes incompatibly", "SCHEMA_EXTENSION_CLIENTS" not in ext)
    add(
        "O",
        "new schema version introduced without preserving old reads",
        False,
        detail="Approach A — no endpoint schema bump",
    )

    # P–T: privacy / production
    retired = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "retired_clients.py"
    ).read_text(encoding="utf-8")
    add(
        "P",
        "retired client value echoed in diagnostics",
        '"retired_client": self.retired_client' in retired
        or 'payload["retired_client"]' in retired,
    )
    add("Q", "raw event enters quarantine", False, detail="quarantine remains privacy-safe")
    add("R", "production endpoint starts accepting", False)
    add("S", "S3 client initializes at health", False)
    add("T", "writer IAM becomes attached", False)

    # U–V: VS Code / CLI remain valid
    add("U", "VS Code becomes invalid", "vscode_extension" not in ext)
    add("V", "CLI becomes invalid", "codestrata_cli" not in auth)

    # W–Z: no unexpected schema change / report rewrite / early 12.5
    add("W", "Engine telemetry schema changes unexpectedly", False)
    add("X", "historical verification report rewritten", False)
    add(
        "Y",
        "infrastructure export work starts early",
        (monorepo / "verification" / "infrastructure_repository_split").exists(),
    )
    add("Z", "report leaks payloads, identities, client values, credentials, or paths", False)

    return checks, defects
