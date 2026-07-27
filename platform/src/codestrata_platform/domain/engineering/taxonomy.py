"""Technology taxonomy for deterministic CEIM normalization."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError

# Canonical technology keys → display name.
CANONICAL_TECHNOLOGIES: dict[str, str] = {
    "spring-boot": "Spring Boot",
    "spring-mvc": "Spring MVC",
    "spring-security": "Spring Security",
    "hibernate": "Hibernate",
    "postgresql": "PostgreSQL",
    "oracle": "Oracle",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue",
    "node": "Node",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "dotnet": ".NET",
    "java": "Java",
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "nginx": "Nginx",
    "terraform": "Terraform",
}

# Alias → canonical key.
_TECHNOLOGY_ALIASES: dict[str, str] = {
    "springboot": "spring-boot",
    "spring boot": "spring-boot",
    "spring-boot": "spring-boot",
    "springmvc": "spring-mvc",
    "spring mvc": "spring-mvc",
    "spring-mvc": "spring-mvc",
    "springsecurity": "spring-security",
    "spring security": "spring-security",
    "spring-security": "spring-security",
    "hibernate": "hibernate",
    "jpa": "hibernate",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pg": "postgresql",
    "oracle": "oracle",
    "oracle db": "oracle",
    "mysql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "kafka": "kafka",
    "apache kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "react": "react",
    "reactjs": "react",
    "angular": "angular",
    "vue": "vue",
    "vuejs": "vue",
    "node": "node",
    "nodejs": "node",
    "node.js": "node",
    "docker": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "dotnet": "dotnet",
    ".net": "dotnet",
    "aspnet": "dotnet",
    "java": "java",
    "python": "python",
    "typescript": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "elastic": "elasticsearch",
    "nginx": "nginx",
    "terraform": "terraform",
}


def normalize_technology_name(raw: str) -> tuple[str, str] | None:
    """Return ``(canonical_key, display_name)`` or ``None`` when unrecognized."""

    compact = " ".join(raw.strip().lower().replace("_", "-").split())
    if not compact:
        return None
    key = _TECHNOLOGY_ALIASES.get(compact)
    if key is None:
        dashed = compact.replace(" ", "-")
        key = _TECHNOLOGY_ALIASES.get(dashed)
    if key is None and compact in CANONICAL_TECHNOLOGIES:
        key = compact
    if key is None:
        return None
    return key, CANONICAL_TECHNOLOGIES[key]


@dataclass(frozen=True, slots=True)
class TechnologyTaxonomy:
    """Lookup table for known technology aliases."""

    entries: tuple[tuple[str, str], ...] = tuple(
        sorted((key, name) for key, name in CANONICAL_TECHNOLOGIES.items())
    )

    def resolve(self, raw: str) -> tuple[str, str] | None:
        return normalize_technology_name(raw)

    def require(self, raw: str) -> tuple[str, str]:
        resolved = self.resolve(raw)
        if resolved is None:
            raise InvalidValueError(
                f"Unrecognized technology: {raw!r}",
                reason_code="unknown_technology",
            )
        return resolved
