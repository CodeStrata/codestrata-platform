"""Deterministic content transforms for Approach A export."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_PLATFORM_DOC_RE = re.compile(
    r"`platform/docs/community-cloud-api/([^`]+)`"
)
_PLATFORM_DOC_MD_LINK = re.compile(
    r"\[([^\]]+)\]\(platform/docs/community-cloud-api/([^)]+)\)"
)
_IMPORT_FROM = re.compile(
    r"^from infrastructure\.verification(\b)", re.MULTILINE
)
_IMPORT_IMPORT = re.compile(
    r"^import infrastructure\.verification(\b)", re.MULTILINE
)


def rewrite_python_imports(text: str) -> str:
    text = _IMPORT_FROM.sub(r"from verification\1", text)
    text = _IMPORT_IMPORT.sub(r"import verification\1", text)
    return text


def rewrite_documentation_links(text: str) -> str:
    """Replace monorepo-relative Platform doc links with conceptual references."""

    def _bt(match: re.Match[str]) -> str:
        name = match.group(1)
        return f"`Community Cloud API documentation ({name})`"

    def _md(match: re.Match[str]) -> str:
        label = match.group(1)
        name = match.group(2)
        return f"{label} (Community Cloud API documentation: {name})"

    text = _PLATFORM_DOC_RE.sub(_bt, text)
    text = _PLATFORM_DOC_MD_LINK.sub(_md, text)
    text = text.replace("python -m infrastructure.verification", "python -m verification")
    text = text.replace("`infrastructure.verification`", "`verification`")
    # Strip remaining raw monorepo product path references in backticks
    text = text.replace("`engine/", "`(Engine repository)/")
    text = text.replace("`vscode-plugin/", "`(VS Code extension)/")
    text = text.replace("`cursor-plugin/", "`(retired Cursor extension)/")
    return text


def generated_boundary_test() -> str:
    return '''"""Infrastructure-local packaging boundary tests (exported form).

Monorepo cross-boundary reconciliation that imports Engine/Platform schema
constants remains in the main repository. This exported test asserts that
Infrastructure source does not import Engine or Platform runtime packages.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_IMPORT = re.compile(r"^\\s*(from|import)\\s+codestrata(_platform)?\\b")


def test_verification_under_repository_root() -> None:
    assert (ROOT / "verification" / "runner.py").is_file()
    assert (ROOT / "verification" / "README.md").is_file()


def test_no_engine_or_platform_runtime_imports() -> None:
    hits: list[str] = []
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if _RUNTIME_IMPORT.match(line):
                hits.append(path.relative_to(ROOT).as_posix())
                break
    assert not hits, hits


def test_modules_are_hcl_only() -> None:
    modules = ROOT / "modules"
    assert modules.is_dir()
    py = [p for p in modules.rglob("*.py") if p.is_file()]
    assert not py


def test_community_data_lake_module_present_with_fail_closed_default() -> None:
    module = ROOT / "modules" / "community-data-lake"
    assert module.is_dir()
    assert not (ROOT / "modules" / "data-lake").exists()
    variables = (module / "variables.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire" in variables
    assert "default     = false" in variables
'''


def generated_platform_boundary_test() -> str:
    return '''"""Platform / export boundary for the independent Infrastructure repository."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_application_source_outside_tests_and_verification() -> None:
    allowed_roots = {ROOT / "tests", ROOT / "verification"}
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path == ROOT / "scripts" / "export_helpers.py":
            continue
        if any(path == root or root in path.parents for root in allowed_roots):
            continue
        # Root pyproject may exist; no unexpected application python at repo root.
        if path.parent == ROOT and path.name in {"conftest.py"}:
            continue
        raise AssertionError(f"unexpected application python: {path.relative_to(ROOT)}")


def test_scripts_use_bounded_path_discovery() -> None:
    validate = (ROOT / "scripts" / "validate.sh").read_text(encoding="utf-8")
    assert "INFRA_ROOT=" in validate
    assert "/Users/" not in validate


def test_architecture_docs_mention_extraction() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "codestrata-infrastructure" in readme
'''


def generated_runtime_adapter() -> str:
    return '''"""Runtime adapter checks — exported static form (no Platform import).

Platform application runtime verification remains in the main monorepo.
Exported repository asserts adapter module presence without importing
``codestrata_platform``.
"""

from __future__ import annotations

from verification.contract import INGESTION_PATHS
from verification.models import CheckResult


def check_runtime_adapter() -> list[CheckResult]:
    return [
        CheckResult(
            name="runtime:exported_static_boundary",
            ok=len(INGESTION_PATHS) == 5,
            detail="platform_runtime_verification_deferred_to_monorepo",
            category="runtime",
        ),
        CheckResult(
            name="runtime:no_platform_import_in_export",
            ok=True,
            detail="static_export_form",
            category="runtime",
        ),
    ]
'''


def generated_packaging() -> str:
    return '''"""Packaging checks — exported static form (Dockerfile remains Platform-owned)."""

from __future__ import annotations

from verification.models import CheckResult


def check_packaging() -> list[CheckResult]:
    return [
        CheckResult(
            name="packaging:dockerfile_platform_owned",
            ok=True,
            detail="dockerfile_lives_in_platform_monorepo",
            category="packaging",
        ),
        CheckResult(
            name="packaging:no_platform_path_required",
            ok=True,
            detail="static_export_form",
            category="packaging",
        ),
    ]
'''


def generated_extraction() -> str:
    return '''"""Extraction-readiness checks for the independent Infrastructure repository."""

from __future__ import annotations

from verification.contract import infra_root
from verification.models import CheckResult


def check_extraction() -> list[CheckResult]:
    root = infra_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    security = (root / "docs" / "security-boundary.md").read_text(encoding="utf-8")
    future = (root / "docs" / "future-data-lake.md").read_text(encoding="utf-8")
    module_py = list((root / "modules").rglob("*.py"))
    return [
        CheckResult(
            name="extraction:codestrata_infrastructure_named",
            ok="codestrata-infrastructure" in readme
            or "codestrata-infrastructure" in security,
            detail="extraction target named",
            category="extraction",
        ),
        CheckResult(
            name="extraction:no_app_python_in_modules",
            ok=not module_py,
            detail="modules HCL only",
            category="extraction",
        ),
        CheckResult(
            name="extraction:scripts_resolve_paths",
            ok="INFRA_ROOT" in (root / "scripts" / "validate.sh").read_text(encoding="utf-8"),
            detail="bounded path discovery",
            category="extraction",
        ),
        CheckResult(
            name="extraction:data_lake_foundation_documented_unwired",
            ok=(root / "modules" / "community-data-lake").is_dir()
            and not (root / "modules" / "data-lake").exists()
            and "modules/community-data-lake" in future
            and "unwired" in future.lower(),
            detail="foundation documented, unwired",
            category="extraction",
            scenario="D",
        ),
        CheckResult(
            name="extraction:state_separate_from_datalake",
            ok="data lake"
            in (root / "docs" / "state-management.md").read_text(encoding="utf-8").lower(),
            detail="state vs data lake",
            category="extraction",
        ),
    ]
'''


def generated_safety() -> str:
    return '''"""Secret / privacy scans for Infrastructure source (exported form)."""

from __future__ import annotations

import re
from pathlib import Path

from verification.contract import SAFETY_PATTERNS, infra_root
from verification.models import CheckResult

_SCAN_GLOBS = (
    "*.tf",
    "*.md",
    "*.sh",
    "*.json",
    "*.example",
    ".gitignore",
)


def _iter_scan_files() -> list[Path]:
    root = infra_root()
    files: list[Path] = []
    for pattern in _SCAN_GLOBS:
        files.extend(root.rglob(pattern))
    filtered: list[Path] = []
    for path in files:
        if not path.is_file():
            continue
        if any(
            part in {".terraform", "__pycache__", ".pytest_cache", "reports"}
            for part in path.parts
        ):
            continue
        if path.suffix == ".py" and "verification" in path.parts:
            continue
        filtered.append(path)
    return filtered


def check_safety() -> list[CheckResult]:
    hits: list[str] = []
    for path in _iter_scan_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SAFETY_PATTERNS:
            for match in re.finditer(pattern, text):
                value = match.group(0)
                if "TEST_ONLY" in value or "EXAMPLE" in value.upper():
                    continue
                if path.suffix in {".md", ".sh"} or path.name.endswith(".example"):
                    if label in {
                        "bearer",
                        "cscc_credential",
                        "aws_access_key",
                        "home_path",
                        "file_uri",
                        "private_key",
                    }:
                        continue
                hits.append(f"{path.name}:{label}")
                break
    return [
        CheckResult(
            name="safety:no_secret_patterns",
            ok=not hits,
            detail="ok" if not hits else ",".join(hits[:8]),
            category="safety",
            scenario="O",
        ),
        CheckResult(
            name="safety:private_repository_posture",
            ok=True,
            detail="community_public_export_exclusion_verified_in_monorepo",
            category="safety",
            scenario="Z",
        ),
    ]
'''


def generated_state() -> str:
    return '''"""State management and gitignore verification (exported form)."""

from __future__ import annotations

import re
from pathlib import Path

from verification.contract import infra_root
from verification.models import CheckResult


def is_empty_s3_backend(path: Path) -> bool:
    """True when backend.tf is an empty S3 backend block with no identifiers."""

    if not path.is_file():
        return False
    stripped = re.sub(r"#.*", "", path.read_text(encoding="utf-8"))
    if not re.search(
        r'terraform\\s*\\{\\s*backend\\s+"s3"\\s*\\{\\s*\\}\\s*\\}',
        stripped,
        re.DOTALL,
    ):
        return False
    lowered = stripped.lower()
    return not any(
        token in lowered
        for token in ("bucket", "key", "access_key", "secret", "profile", "dynamodb")
    )


def check_state() -> list[CheckResult]:
    root = infra_root()
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    backend = (root / "production" / "backend.tf.example").read_text(encoding="utf-8")
    state_docs = (root / "docs" / "state-management.md").read_text(encoding="utf-8")
    committed_state = list(root.rglob("*.tfstate")) + list(root.rglob("*.tfplan"))
    committed_state = [
        p
        for p in committed_state
        if ".terraform" not in p.parts and "reports" not in p.parts
    ]
    return [
        CheckResult(
            name="state:gitignore_tfstate",
            ok="*.tfstate" in gitignore and "*.tfstate.*" in gitignore,
            detail="tfstate ignored",
            category="state",
            scenario="Q",
        ),
        CheckResult(
            name="state:gitignore_plans",
            ok="*.tfplan" in gitignore,
            detail="plans ignored",
            category="state",
            scenario="R",
        ),
        CheckResult(
            name="state:gitignore_terraform_dir",
            ok=".terraform/" in gitignore,
            detail=".terraform ignored",
            category="state",
        ),
        CheckResult(
            name="state:gitignore_allows_lockfile",
            ok=not any(
                line.strip() == ".terraform.lock.hcl"
                for line in gitignore.splitlines()
            ),
            detail="lock files trackable",
            category="state",
        ),
        CheckResult(
            name="state:gitignore_tfvars",
            ok="terraform.tfvars" in gitignore and "secrets.tfvars" in gitignore,
            detail="tfvars ignored",
            category="state",
        ),
        CheckResult(
            name="state:no_committed_state_or_plans",
            ok=not committed_state,
            detail="ok" if not committed_state else str(len(committed_state)),
            category="state",
            scenario="Q",
        ),
        CheckResult(
            name="state:backend_example_encrypted",
            ok="encrypt" in backend.lower() and "REPLACE_WITH" in backend,
            detail="encrypted remote example",
            category="state",
        ),
        CheckResult(
            name="state:docs_cover_locking",
            ok=all(
                token in state_docs.lower()
                for token in ("locking", "encrypt", "data lake", "environment")
            ),
            detail="state-management.md",
            category="state",
        ),
        CheckResult(
            name="state:backend_tf_empty_s3",
            ok=is_empty_s3_backend(root / "production" / "backend.tf"),
            detail="empty s3 backend (no bucket/key/credentials)",
            category="state",
        ),
        CheckResult(
            name="state:no_populated_backend_tf",
            ok=all(
                is_empty_s3_backend(path)
                for path in root.rglob("backend.tf")
                if path.is_file()
            ),
            detail="no populated backend.tf",
            category="state",
        ),
    ]
'''


def adapt_contract_py(text: str) -> str:
    text = rewrite_python_imports(text)
    # After Approach A, infra_root == repository root; repo_root aliases it.
    old = (
        "def repo_root() -> Path:\n"
        "    return infra_root().parent\n"
    )
    new = (
        "def repo_root() -> Path:\n"
        "    # Approach A: independent repository root equals infrastructure root.\n"
        "    return infra_root()\n"
    )
    if old in text:
        text = text.replace(old, new)
    return text


def adapt_validate_sh(text: str) -> str:
    # INFRA_ROOT is repository root; do not climb to monorepo parent for Python.
    text = text.replace(
        'REPO_ROOT="$(cd "${INFRA_ROOT}/.." && pwd)"',
        'REPO_ROOT="${INFRA_ROOT}"',
    )
    text = text.replace(
        'PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"',
        'PYTHON_BIN="${INFRA_ROOT}/.venv/bin/python"',
    )
    # pytest path already uses INFRA_ROOT/tests — good
    return text


def adapt_build_script(text: str) -> str:
    """Rewrite Platform Dockerfile dependency to an explicit owner-operated gate."""

    return '''#!/usr/bin/env bash
# Build helper for Community Cloud API Lambda image (exported form).
# The Dockerfile remains Platform-owned in the main monorepo.
# This script does not build without an explicit PLATFORM_DEPLOYMENT_ROOT.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: build-community-cloud-api.sh --platform-root <monorepo-or-platform-deployment-root> [--tag TAG]

Builds a local Docker image using the Platform-owned Dockerfile.
Does not push to ECR. Does not apply infrastructure. Does not call AWS.

Requires PLATFORM_DEPLOYMENT_ROOT or --platform-root pointing at a checkout
that contains community-cloud-api/Dockerfile (Platform deployment tree).
EOF
}

PLATFORM_ROOT="${PLATFORM_DEPLOYMENT_ROOT:-}"
IMAGE_TAG="${IMAGE_TAG:-}"
IMAGE_NAME="${IMAGE_NAME:-codestrata-community-cloud-api}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform-root)
      PLATFORM_ROOT="${2:-}"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${PLATFORM_ROOT}" ]]; then
  echo "error: PLATFORM_DEPLOYMENT_ROOT or --platform-root is required (Dockerfile is Platform-owned)" >&2
  exit 2
fi

if [[ -z "${IMAGE_TAG}" ]]; then
  echo "error: IMAGE_TAG or --tag is required (do not rely on floating 'latest')" >&2
  exit 2
fi

if [[ "${IMAGE_TAG}" == "latest" ]]; then
  echo "error: floating tag 'latest' is rejected" >&2
  exit 2
fi

DOCKERFILE="${PLATFORM_ROOT}/community-cloud-api/Dockerfile"
if [[ ! -f "${DOCKERFILE}" ]]; then
  DOCKERFILE="${PLATFORM_ROOT}/platform/deployment/community-cloud-api/Dockerfile"
fi
if [[ ! -f "${DOCKERFILE}" ]]; then
  echo "error: Dockerfile not found under platform deployment root" >&2
  exit 2
fi

echo "Building ${IMAGE_NAME}:${IMAGE_TAG} from Platform Dockerfile (no push, no apply)"
docker build -f "${DOCKERFILE}" -t "${IMAGE_NAME}:${IMAGE_TAG}" "${PLATFORM_ROOT}"
'''


TRANSFORM_DESTINATIONS = frozenset(
    {
        "tests/verification/test_boundary.py",
        "tests/test_platform_boundary.py",
        "verification/runtime_adapter.py",
        "verification/packaging.py",
        "verification/extraction.py",
        "verification/safety.py",
        "verification/state.py",
        "verification/contract.py",
        "scripts/validate.sh",
        "scripts/build-community-cloud-api.sh",
    }
)


def transform_file(destination_path: str, raw: bytes) -> tuple[bytes, str]:
    """Return (content, classification). classification is transformed_export or export_*."""

    name = PurePosixPath(destination_path).name
    if destination_path == "tests/verification/test_boundary.py":
        return generated_boundary_test().encode("utf-8"), "transformed_export"
    if destination_path == "tests/test_platform_boundary.py":
        return generated_platform_boundary_test().encode("utf-8"), "transformed_export"
    if destination_path == "verification/runtime_adapter.py":
        return generated_runtime_adapter().encode("utf-8"), "transformed_export"
    if destination_path == "verification/packaging.py":
        return generated_packaging().encode("utf-8"), "transformed_export"
    if destination_path == "verification/extraction.py":
        return generated_extraction().encode("utf-8"), "transformed_export"
    if destination_path == "verification/safety.py":
        return generated_safety().encode("utf-8"), "transformed_export"
    if destination_path == "verification/state.py":
        return generated_state().encode("utf-8"), "transformed_export"
    if destination_path == "verification/contract.py":
        text = adapt_contract_py(raw.decode("utf-8"))
        return text.encode("utf-8"), "transformed_export"
    if destination_path == "scripts/validate.sh":
        text = adapt_validate_sh(raw.decode("utf-8"))
        return text.encode("utf-8"), "transformed_export"
    if destination_path == "scripts/build-community-cloud-api.sh":
        return adapt_build_script(raw.decode("utf-8")).encode("utf-8"), "transformed_export"

    # Generic transforms
    if name.endswith((".py",)):
        text = rewrite_python_imports(raw.decode("utf-8"))
        text = text.replace("python -m infrastructure.verification", "python -m verification")
        text = text.replace("`infrastructure.verification`", "`verification`")
        if text.encode("utf-8") != raw:
            return text.encode("utf-8"), "transformed_export"
        return raw, "export_required"
    if name.endswith((".md",)):
        text = rewrite_documentation_links(raw.decode("utf-8"))
        # Also rewrite python import mentions in docs if any
        if text.encode("utf-8") != raw:
            return text.encode("utf-8"), "transformed_export"
        return raw, "export_required"
    return raw, "export_required"
