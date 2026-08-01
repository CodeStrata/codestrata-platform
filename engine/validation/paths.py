"""Path helpers for the validation harness."""

from __future__ import annotations

from pathlib import Path

VALIDATION_ROOT = Path(__file__).resolve().parent
ENGINE_ROOT = VALIDATION_ROOT.parent
WORKSPACE_ROOT = ENGINE_ROOT.parent
REPOSITORIES_DIR = VALIDATION_ROOT / "repositories"
EXPECTATIONS_DIR = VALIDATION_ROOT / "expectations"
RESULTS_DIR = VALIDATION_ROOT / "results"
SCHEMAS_DIR = VALIDATION_ROOT / "schemas"


def resolve_local_path(relative: str, *, validation_root: Path = VALIDATION_ROOT) -> Path:
    """Resolve a repository-relative local path under the validation root.

    Absolute paths are rejected for committed definitions; callers that need a
    temporary absolute path (e.g. after cloning) pass an already-resolved Path
    outside this helper.
    """

    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(
            f"local_path must be relative to the validation root, got absolute path: {relative!r}"
        )
    resolved = (validation_root / candidate).resolve()
    # Allow fixtures outside validation_root (e.g. ../../test-fixtures/...) but
    # still require the relative form in the definition.
    return resolved
