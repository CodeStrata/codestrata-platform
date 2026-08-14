"""Slice 20.12 — semantic claim guards for transparency documentation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

TELEMETRY = (ROOT / "docs/reference/telemetry.md").read_text(encoding="utf-8")
DATA_COLLECTION = (ROOT / "docs/security/data-collection.md").read_text(encoding="utf-8")
PRIVACY = (ROOT / "docs/security/privacy.md").read_text(encoding="utf-8")
CLI = (ROOT / "docs/reference/cli.md").read_text(encoding="utf-8")
VSCODE = (ROOT / "docs/extensions/vscode.md").read_text(encoding="utf-8")
ENGINE_PRIVACY = (ROOT / "engine/PRIVACY.md").read_text(encoding="utf-8")
VSCODE_PRIVACY = (ROOT / "vscode-plugin/PRIVACY.md").read_text(encoding="utf-8")
VSCODE_README = (ROOT / "vscode-plugin/README.md").read_text(encoding="utf-8")


def test_no_numeric_scores_promise() -> None:
    low = TELEMETRY.lower()
    assert "numeric" in low and "score" in low and "not" in low
    assert "canonical overall numeric health score" in low


def test_no_graph_telemetry_claim() -> None:
    assert "graph telemetry is **not**" in TELEMETRY.lower() or "no graph telemetry" in TELEMETRY.lower()
    assert "graph telemetry is collected" not in TELEMETRY.lower()
    assert "code graph uploaded" not in TELEMETRY.lower()


def test_source_code_stays_local() -> None:
    for text in (TELEMETRY, PRIVACY, ENGINE_PRIVACY, VSCODE_PRIVACY, VSCODE_README):
        low = text.lower()
        assert "source code" in low
        assert "stay local" in low or "stays local" in low or "remain local" in low or "does **not**" in low


def test_report_publish_separate() -> None:
    for text in (TELEMETRY, CLI, VSCODE, ENGINE_PRIVACY):
        low = text.lower()
        assert "publish" in low
        assert "not" in low


def test_vscode_cli_same_consent() -> None:
    for text in (TELEMETRY, VSCODE, VSCODE_PRIVACY, VSCODE_README):
        low = text.lower()
        assert "share" in low or "same" in low
        assert "engine" in low


def test_telemetry_allow_is_not_consent() -> None:
    for text in (TELEMETRY, CLI, PRIVACY, ENGINE_PRIVACY):
        assert "--telemetry-allow" in text
        low = text.lower()
        assert "not" in low and ("consent" in low or "bridge" in low)


def test_legacy_v1_not_silently_expanded() -> None:
    for text in (TELEMETRY, PRIVACY, ENGINE_PRIVACY):
        low = text.lower()
        assert "silent" in low or "silently" in low
        assert "v2" in low or "upgrade" in low or "assessment intelligence" in low


def test_amd_active_with_v2_documented() -> None:
    assert "ACTIVE_WITH_V2_CONSENT" in DATA_COLLECTION
    assert "assessment_metadata" in DATA_COLLECTION
    assert "ACTIVE_WITH_V2_CONSENT" in TELEMETRY or "v2" in TELEMETRY.lower()


def test_pseudonymous_not_absolute_anonymity() -> None:
    low = TELEMETRY.lower()
    assert "pseudonymous" in low or "random installation identifier" in low
    assert "completely anonymous" not in low
    assert "absolutely unlinkable" not in low
