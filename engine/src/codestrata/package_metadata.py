"""Installed package metadata helpers for CLI product identity commands.

Version and project URLs are read from package metadata when available.
Fallbacks mirror ``pyproject.toml`` / ``codestrata.__version__`` for source-tree
execution when the distribution is not installed.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as package_metadata
from importlib.metadata import version as package_version

PACKAGE_NAME = "codestrata"
PRODUCT_NAME = "CodeStrata"

# Fallbacks must stay aligned with pyproject.toml / codestrata.__version__.
_FALLBACK_SUMMARY = (
    "CodeStrata: deterministic assessment, knowledge, and modernization "
    "tooling for legacy enterprise applications."
)
_FALLBACK_HOMEPAGE = "https://github.com/sknampally/codestrata"
_FALLBACK_REPOSITORY = "https://github.com/sknampally/codestrata"


@dataclass(frozen=True, slots=True)
class PackageAboutInfo:
    """Verified product identity fields for ``codestrata about``."""

    version: str
    summary: str
    website: str
    github: str


def get_package_version() -> str:
    """Return the installed ``codestrata`` distribution version."""

    try:
        return package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        from codestrata import __version__

        return __version__


def _project_urls() -> dict[str, str]:
    try:
        meta = package_metadata(PACKAGE_NAME)
    except PackageNotFoundError:
        return {
            "Homepage": _FALLBACK_HOMEPAGE,
            "Repository": _FALLBACK_REPOSITORY,
        }

    urls: dict[str, str] = {}
    for item in meta.get_all("Project-URL") or []:
        name, _, value = item.partition(",")
        key = name.strip()
        url = value.strip()
        if key and url:
            urls[key] = url

    homepage = (meta.get("Home-page") or "").strip()
    if homepage and homepage.upper() != "UNKNOWN" and "Homepage" not in urls:
        urls["Homepage"] = homepage

    if "Homepage" not in urls:
        urls["Homepage"] = _FALLBACK_HOMEPAGE
    if "Repository" not in urls:
        urls["Repository"] = urls.get("Homepage", _FALLBACK_REPOSITORY)
    return urls


def _package_summary() -> str:
    try:
        meta = package_metadata(PACKAGE_NAME)
    except PackageNotFoundError:
        return _FALLBACK_SUMMARY

    summary = (meta.get("Summary") or "").strip()
    return summary or _FALLBACK_SUMMARY


def get_about_info() -> PackageAboutInfo:
    """Return verified about-page fields from package metadata."""

    urls = _project_urls()
    return PackageAboutInfo(
        version=get_package_version(),
        summary=_package_summary(),
        website=urls["Homepage"],
        github=urls["Repository"],
    )


def format_version_line() -> str:
    """Return the short product version line (``CodeStrata X.Y.Z``)."""

    return f"{PRODUCT_NAME} {get_package_version()}"


def format_version_details() -> str:
    """Return version details for ``codestrata version`` (CLI / Engine / Report / AI)."""

    from codestrata.config.settings import DEFAULT_BEDROCK_MODEL_ID
    from codestrata.extensions.version import EXTENSION_API_VERSION
    from codestrata.reporting.contract.constants import REPORT_HTML_VERSION

    try:
        from codestrata.config.settings import CodestrataSettings

        settings = CodestrataSettings.model_validate(
            {"repository": {"path": "."}, "ai": {}}
        )
        ai_provider = settings.ai.provider
        if ai_provider == "openai":
            ai_model = settings.ai.openai.answer_model or "gpt-4o-mini"
        else:
            ai_model = settings.ai.bedrock.model_id or DEFAULT_BEDROCK_MODEL_ID
    except Exception:  # noqa: BLE001 - metadata must not fail
        ai_provider = "bedrock"
        ai_model = DEFAULT_BEDROCK_MODEL_ID

    return "\n".join(
        (
            format_version_line(),
            f"CLI: {get_package_version()}",
            f"Engine: {get_package_version()}",
            f"Extension API: {EXTENSION_API_VERSION}",
            f"Report HTML: {REPORT_HTML_VERSION}",
            f"AI provider (default): {ai_provider}",
            f"AI model (default): {ai_model}",
            f"Python: {platform.python_version()}",
            f"Platform: {platform.system()}",
        )
    )


def format_about() -> str:
    """Return concise about text for ``codestrata about``."""

    info = get_about_info()
    return "\n".join(
        (
            f"{PRODUCT_NAME} {info.version}",
            "",
            info.summary,
            "",
            f"Website: {info.website}",
            f"GitHub: {info.github}",
        )
    )

