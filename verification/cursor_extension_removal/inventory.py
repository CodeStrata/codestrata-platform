"""Pre-removal Cursor product inventory (discovered before Slice 12.1 delete)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Relative paths of tracked Cursor product files before removal (git ls-files).
TRACKED_CURSOR_RELATIVE_PATHS: tuple[str, ...] = (
    "cursor-plugin/.gitignore",
    "cursor-plugin/.vscodeignore",
    "cursor-plugin/CHANGELOG.md",
    "cursor-plugin/CI.md",
    "cursor-plugin/CODE_OF_CONDUCT.md",
    "cursor-plugin/COMPATIBILITY.md",
    "cursor-plugin/CONTRIBUTING.md",
    "cursor-plugin/EXTRACTION.md",
    "cursor-plugin/LICENSE",
    "cursor-plugin/MARKETPLACE.md",
    "cursor-plugin/PLACEHOLDER.md",
    "cursor-plugin/PRIVACY.md",
    "cursor-plugin/README.md",
    "cursor-plugin/RELEASE_CHECKLIST.md",
    "cursor-plugin/SECURITY.md",
    "cursor-plugin/SUPPORT.md",
    "cursor-plugin/media/SCREENSHOTS.md",
    "cursor-plugin/media/codestrata-activity.svg",
    "cursor-plugin/media/codestrata-icon.png",
    "cursor-plugin/media/marketplace-banner.png",
    "cursor-plugin/media/screenshot-activity.png",
    "cursor-plugin/media/screenshot-complete.png",
    "cursor-plugin/media/screenshot-findings.png",
    "cursor-plugin/media/screenshot-recommendations.png",
    "cursor-plugin/media/screenshot-report.png",
    "cursor-plugin/media/screenshot-running.png",
    "cursor-plugin/media/screenshot-welcome.png",
    "cursor-plugin/package-lock.json",
    "cursor-plugin/package.json",
    "cursor-plugin/src/config/settings.ts",
    "cursor-plugin/src/conversation/context.ts",
    "cursor-plugin/src/conversation/cursorRules.ts",
    "cursor-plugin/src/conversation/prompts.ts",
    "cursor-plugin/src/conversation/suggestedQuestions.ts",
    "cursor-plugin/src/engine/cliContract.ts",
    "cursor-plugin/src/engine/cliRunner.ts",
    "cursor-plugin/src/engine/compatibility.ts",
    "cursor-plugin/src/engine/discovery.ts",
    "cursor-plugin/src/engine/installer.ts",
    "cursor-plugin/src/extension.ts",
    "cursor-plugin/src/onboarding/firstRun.ts",
    "cursor-plugin/src/onboarding/state.ts",
    "cursor-plugin/src/test/extensionCore.test.ts",
    "cursor-plugin/src/test/runHostTests.ts",
    "cursor-plugin/src/test/suite/index.ts",
    "cursor-plugin/src/ui/output.ts",
    "cursor-plugin/src/ui/statusBar.ts",
    "cursor-plugin/src/views/statusTree.ts",
    "cursor-plugin/src/views/suggestedTree.ts",
    "cursor-plugin/tsconfig.json",
)

CURSOR_COMMANDS_PRE_REMOVAL: tuple[str, ...] = (
    "codestrata.assess",
    "codestrata.assessWithAi",
    "codestrata.refreshAssessment",
    "codestrata.clearAssessment",
    "codestrata.installEngine",
    "codestrata.checkEnvironment",
    "codestrata.showWelcome",
    "codestrata.missingAssessmentHelp",
    "codestrata.openHtmlReport",
    "codestrata.showFindings",
)

CURSOR_PACKAGE_NAME = "codestrata-cursor"
CURSOR_PACKAGE_VERSION = "0.2.0"
CURSOR_ACTIVATION = "onStartupFinished"


def build_inventory(monorepo: Path) -> dict[str, Any]:
    cursor = monorepo / "cursor-plugin"
    vscode = monorepo / "vscode-plugin"
    return {
        "cursor_directory_exists": cursor.exists(),
        "cursor_package_json_exists": (cursor / "package.json").is_file(),
        "cursor_src_exists": (cursor / "src").is_dir(),
        "cursor_test_exists": (cursor / "src" / "test").is_dir(),
        "cursor_telemetry_runtime_exists": (cursor / "src" / "telemetry").is_dir(),
        "cursor_analytics_runtime_exists": (
            (cursor / "src" / "analytics").is_dir()
            or (cursor / "src" / "telemetry" / "analytics").is_dir()
        ),
        "cursor_media_exists": (cursor / "media").is_dir(),
        "cursor_out_exists": (cursor / "out").is_dir(),
        "vscode_directory_exists": vscode.exists(),
        "vscode_package_json_exists": (vscode / "package.json").is_file(),
        "tracked_cursor_paths_pre_removal": list(TRACKED_CURSOR_RELATIVE_PATHS),
        "tracked_cursor_path_count": len(TRACKED_CURSOR_RELATIVE_PATHS),
    }
