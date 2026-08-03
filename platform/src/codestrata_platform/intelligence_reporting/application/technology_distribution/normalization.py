"""Deterministic technology-name normalization (no fuzzy / AI / registry)."""

from __future__ import annotations

import re

from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text

NORMALIZATION_POLICY_VERSION = "technology-normalization-v1"

# Explicit reviewed aliases only. Unknown names are preserved after light cleanup.
_ALIAS_CATALOG: dict[str, str] = {
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "java": "Java",
    "kotlin": "Kotlin",
    "csharp": "C#",
    "c#": "C#",
    "c-sharp": "C#",
    "dotnet": ".NET",
    ".net": ".NET",
    "net": ".NET",
    "aspnet": "ASP.NET Core",
    "aspnetcore": "ASP.NET Core",
    "asp.net": "ASP.NET Core",
    "asp.net core": "ASP.NET Core",
    "spring": "Spring",
    "springboot": "Spring Boot",
    "spring-boot": "Spring Boot",
    "spring boot": "Spring Boot",
    "maven": "Maven",
    "gradle": "Gradle",
    "npm": "npm",
    "pip": "pip",
    "nuget": "NuGet",
    "composer": "Composer",
    "docker": "Docker",
    "docker-compose": "Docker Compose",
    "docker compose": "Docker Compose",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "helm": "Helm",
    "terraform": "Terraform",
    "openai": "OpenAI",
    "openai sdk": "OpenAI SDK",
    "mcp": "MCP",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "django": "Django",
    "react": "React",
    "angular": "Angular",
    "php": "PHP",
    "ruby": "Ruby",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
}

_PUNCT_RE = re.compile(r"[\s_\-/]+")


def canonicalize_alias_key(name: str) -> str:
    text = name.strip().lower()
    text = text.replace(".", ".")  # keep dots for node.js keys
    text = _PUNCT_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Also provide compacted form without spaces for catalog lookup.
    return text


def normalize_technology_name(name: str) -> tuple[str, bool]:
    """Return (normalized_display_name, alias_applied).

    No fuzzy matching. Distinct technologies remain distinct.
    """

    cleaned = reject_unsafe_text(str(name).strip(), label="technology_name")
    key = canonicalize_alias_key(cleaned)
    compact = key.replace(" ", "").replace(".", "")
    if key in _ALIAS_CATALOG:
        return _ALIAS_CATALOG[key], True
    if compact in {k.replace(" ", "").replace(".", "") for k in _ALIAS_CATALOG}:
        for alias_key, value in _ALIAS_CATALOG.items():
            if alias_key.replace(" ", "").replace(".", "") == compact:
                return value, True
    # Preserve original casing lightly title-cased only when all-lower/upper.
    if cleaned.islower() or cleaned.isupper():
        return cleaned[:1].upper() + cleaned[1:], False
    return cleaned, False


def technology_id(*, category: str, normalized_name: str) -> str:
    cat = canonicalize_alias_key(category).replace(" ", "_")
    name = canonicalize_alias_key(normalized_name).replace(" ", "-")
    return f"technology:{cat}:{name}"
