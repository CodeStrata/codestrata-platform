#!/usr/bin/env python3
"""One-shot generator for Epic 4 Slice 4.13 validation expansion."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
VAL = ROOT / "validation"

ACTIVE = (
    "local-cloud-signals",
    "local-security-hygiene",
    "local-ai-readiness",
    "local-ai-negative",
    "local-architecture-signals",
    "local-complexity-signals",
    "local-dependency-signals",
    "local-terraform-signals",
    "local-serverless-signals",
    "local-compose-managed",
    "local-library-npm",
    "local-cli-python",
    "local-sample-js",
    "local-sample-python",
    "local-sample-php",
    "local-sample-csharp",
    "local-sample-java",
    "local-typescript-app",
    "local-gradle-multimodule",
    "remote-java-spring-petclinic",
    "remote-python-fastapi",
    "remote-typescript-angular",
    "remote-php-bookstack",
    "remote-csharp-eshop",
)

SECURITY_NEG = {
    "required_findings": [],
    "forbidden_findings": [],
    "forbidden_rule_ids": [
        "security.private-key-material",
        "security.credential-literal",
        "security.placeholder-credential",
        "SEC002",
    ],
    "maximum_false_positive_count": 0,
    "forbidden_raw_values": [],
    "not_applicable_rule_ids": [
        "security.tls-verification-disabled",
        "security.hostname-verification-disabled",
        "security.authentication-disabled",
        "security.permissive-cors-origin",
        "security.debug-enabled",
    ],
}

ARCH_NEG = {
    "required_findings": [],
    "forbidden_findings": [],
    "allowed_findings": [
        {"rule_id": "ARCH004", "rationale": "Legacy missing-tests inventory signal; ambiguous"},
        {"rule_id": "ARCH005", "rationale": "Legacy test-structure inventory signal; ambiguous"},
        {"rule_id": "ARCH001", "rationale": "Legacy component inventory; ambiguous if present"},
        {"rule_id": "ARCH002", "rationale": "Legacy API inventory; ambiguous if present"},
        {"rule_id": "ARCH003", "rationale": "Legacy persistence inventory; ambiguous if present"},
        {"rule_id": "ARCH007", "rationale": "Legacy single-app inventory; ambiguous if present"},
    ],
    "forbidden_rule_ids": [
        "architecture.dependency-cycle",
        "architecture.invalid-dependency-direction",
        "architecture.layer-boundary-violation",
        "architecture.excessive-cross-module-coupling",
        "architecture.component-concentration",
        "architecture.framework-leakage",
        "architecture.enterprise-standard-mismatch",
    ],
    "maximum_false_positive_count": 0,
    "forbidden_unsupported_claims": [
        "microservices",
        "well-architected",
        "production-ready architecture",
        "loosely coupled",
        "scalable",
        "resilient",
    ],
}

TD_NEG = {
    "required_findings": [],
    "forbidden_findings": [],
    "allowed_findings": [],
    "forbidden_rule_ids": [
        "technical_debt.large-callable",
        "technical_debt.excessive-branching",
        "technical_debt.deep-nesting",
        "technical_debt.excessive-parameters",
        "technical_debt.oversized-type",
    ],
    "maximum_false_positive_count": 0,
    "forbidden_conclusions": [
        "low technical debt",
        "high technical debt",
        "rewrite required",
        "poor maintainability",
        "developer productivity",
        "financial debt",
        "delivery delay",
    ],
}

DEP_NEG = {
    "required_manifests": [],
    "required_findings": [],
    "forbidden_findings": [],
    "forbidden_rule_ids": [
        "dependency.unresolved-version",
        "dependency.mutable-version",
        "dependency.unbounded-requirement",
        "dependency.conflicting-exact-versions",
        "dependency.duplicate-declaration",
    ],
    "maximum_false_positive_count": 0,
    "forbidden_conclusions": [
        "dependencies are healthy",
        "secure supply chain",
        "no dependency risk",
        "dependencies are current",
        "licenses are compliant",
        "no vulnerabilities",
        "upgrade-ready",
        "safe dependency posture",
    ],
}

CLOUD_NEG = {
    "required_signal_families": [],
    "forbidden_signal_families": [
        {"family_id": "platform", "rationale": "No cloud provider artifacts"},
        {"family_id": "container", "rationale": "No Dockerfile/compose"},
        {"family_id": "orchestration", "rationale": "No Kubernetes/Helm"},
        {"family_id": "iac", "rationale": "No IaC"},
        {"family_id": "serverless", "rationale": "No serverless config"},
        {"family_id": "managed_service", "rationale": "No managed-service markers"},
        {"family_id": "deployment", "rationale": "No confirmed deployment pipelines"},
    ],
    "required_findings": [],
    "forbidden_rule_ids": [
        "cloud.cloud-001",
        "cloud.cloud-002",
        "cloud.cloud-010",
        "cloud.cloud-011",
        "cloud.cloud-020",
        "cloud.cloud-021",
        "cloud.cloud-030",
        "cloud.cloud-040",
        "cloud.cloud-050",
        "cloud.cloud-060",
        "cloud.cloud-061",
    ],
    "maximum_false_positive_count": 0,
    "forbidden_conclusions": [
        "cloud ready",
        "migration ready",
        "cloud native architecture",
        "production ready",
        "highly available",
        "secure cloud posture",
        "cost optimized",
        "operationally mature",
        "successfully deployed",
        "no cloud risks",
    ],
}

AI_NEG = {
    "required_signal_families": [],
    "forbidden_signal_families": [
        {"family_id": "api_boundary", "rationale": "Must not invent AI API-boundary signals"},
        {"family_id": "documentation", "rationale": "Must not invent AI documentation signals"},
        {"family_id": "data_retrieval", "rationale": "Must not invent RAG/data-retrieval readiness"},
        {"family_id": "ai_integration", "rationale": "Must not imply LLM/AI integration"},
        {"family_id": "tool_mcp", "rationale": "Must not imply MCP tools"},
        {"family_id": "workflow_agent", "rationale": "Must not invent agent workflows"},
        {"family_id": "observability_governance", "rationale": "Must not invent AI governance"},
    ],
    "required_signals": [],
    "forbidden_signals": [],
    "required_findings": [],
    "forbidden_findings": [],
    "forbidden_rule_ids": [
        "ai_readiness.ai-001",
        "ai_readiness.ai-002",
        "ai_readiness.ai-003",
        "ai_readiness.ai-010",
        "ai_readiness.ai-011",
        "ai_readiness.ai-020",
        "ai_readiness.ai-021",
        "ai_readiness.ai-022",
        "ai_readiness.ai-030",
        "ai_readiness.ai-031",
        "ai_readiness.ai-032",
        "ai_readiness.ai-040",
        "ai_readiness.ai-041",
        "ai_readiness.ai-050",
        "ai_readiness.ai-051",
        "ai_readiness.ai-060",
        "ai_readiness.ai-061",
    ],
    "required_recommendations": [],
    "forbidden_recommendations": [
        {"title_pattern": "(?i)deploy rag", "rationale": "no RAG deploy claim"},
        {"title_pattern": "(?i)autonomous agent", "rationale": "no autonomous agent claim"},
        {"title_pattern": "(?i)productionize ai", "rationale": "no productionize claim"},
        {"title_pattern": "(?i)responsible ai", "rationale": "no certification claim"},
        {"title_pattern": "(?i)ai ready", "rationale": "no readiness claim"},
    ],
    "maximum_false_positive_count": 0,
    "forbidden_conclusions": [
        "ai ready",
        "agent ready",
        "rag ready",
        "production ai ready",
        "mature ai platform",
        "strong ai foundation",
        "governed ai",
        "safe ai implementation",
        "high-quality data",
        "responsible ai compliant",
        "no ai readiness risks",
    ],
}

MOD_NEG = {
    "require_finding_backed_authority": True,
    "require_priority_action_backed_roadmap": True,
    "allow_legacy_recommendations": True,
    "maximum_false_positive_count": 0,
    "allowed_recommendations": [
        {"title_pattern": "(?i)before modernization", "rationale": "Phase-1 legacy testing rec; not PA-eligible"},
        {"title_pattern": "(?i)quality gates", "rationale": "Phase-1 legacy CI rec; not PA-eligible"},
    ],
    "forbidden_recommendations": [
        {"title_pattern": "(?i)become cloud native", "rationale": "Vague unsupported theme"},
        {"title_pattern": "(?i)rewrite (the |required|application)", "rationale": "No rewrite claim"},
        {"title_pattern": "(?i)^enable ai\\b|\\benable ai\\b", "rationale": "No enable-AI modernization claim"},
        {"title_pattern": "(?i)production readiness", "rationale": "No prod readiness"},
        {"title_pattern": "(?i)guaranteed", "rationale": "No guaranteed outcome"},
    ],
    "forbidden_priority_actions": [
        {"title_pattern": "(?i)cloud ready|ai ready|production ready", "rationale": "No invented readiness PAs"},
    ],
    "forbidden_roadmap_phases": ["optimize"],
    "forbidden_conclusions": [
        "modernization ready",
        "production ready",
        "transformation ready",
        "rewrite required",
        "guaranteed improvement",
        "exact ROI",
        "successful migration",
        "become cloud native",
        "enable AI",
        "transform the architecture",
        "security certification",
        "cloud ready",
        "ai ready",
    ],
}


def pack(section: dict, notes: str) -> dict:
    out = dict(section)
    out["evidence_notes"] = notes
    return out


def base_expectation(notes: str) -> dict:
    return {
        "schema_version": "1.2",
        "expect_ai_executed": False,
        "expected_artifacts": ["report.json"],
        "finding_count": {"minimum": 0},
        "technology_inventory": pack(
            {
                "required_languages": [],
                "forbidden_languages": [],
                "required_frameworks": [],
                "forbidden_frameworks": [],
                "required_build_systems": [],
                "forbidden_build_systems": [],
                "required_dependency_ecosystems": [],
                "forbidden_dependency_ecosystems": [],
                "allowed_ambiguous_facts": [],
            },
            notes,
        ),
        "security": pack(dict(SECURITY_NEG), f"Negative control. {notes}"),
        "architecture": pack(dict(ARCH_NEG), f"Negative control. {notes}"),
        "technical_debt": pack(dict(TD_NEG), f"Negative control. {notes}"),
        "dependency": pack(dict(DEP_NEG), f"Negative control. {notes}"),
        "cloud": pack(dict(CLOUD_NEG), f"Negative control. {notes}"),
        "ai_readiness": pack(dict(AI_NEG), f"Negative control. {notes}"),
        "modernization": pack(dict(MOD_NEG), f"Negative control. {notes}"),
        "notes": notes,
    }


REPOS = {
    "local-architecture-signals": {
        "toml": {
            "display_name": "Local architecture signals fixture",
            "source_type": "local",
            "local_path": "fixtures/architecture-signals",
            "assessment_config": "configs/local-architecture-signals.toml",
            "tags": ["local", "fixture", "architecture", "controlled", "fast", "set-4-13"],
            "languages": ["java"],
        },
        "expect": lambda: _arch_expectation(),
        "baseline_identity": "engine/validation/fixtures/architecture-signals",
    },
    "local-complexity-signals": {
        "toml": {
            "display_name": "Local complexity signals fixture",
            "source_type": "local",
            "local_path": "fixtures/complexity-signals",
            "assessment_config": "configs/local-complexity-signals.toml",
            "tags": ["local", "fixture", "technical-debt", "controlled", "fast", "set-4-13"],
            "languages": ["python"],
        },
        "expect": lambda: _complexity_expectation(),
        "baseline_identity": "engine/validation/fixtures/complexity-signals",
    },
    "local-dependency-signals": {
        "toml": {
            "display_name": "Local dependency signals fixture",
            "source_type": "local",
            "local_path": "fixtures/dependency-signals",
            "assessment_config": "configs/local-dependency-signals.toml",
            "tags": ["local", "fixture", "dependency", "controlled", "fast", "set-4-13"],
            "languages": ["java", "python"],
        },
        "expect": lambda: _dependency_expectation(),
        "baseline_identity": "engine/validation/fixtures/dependency-signals",
    },
    "local-sample-php": {
        "toml": {
            "display_name": "Local sample PHP (Laravel + PHPUnit)",
            "source_type": "local",
            "local_path": "../../test-fixtures/sample-php-app",
            "tags": ["local", "php", "composer", "laravel", "tests-present", "real-world", "fast", "set-4-13"],
            "languages": ["php"],
        },
        "expect": lambda: _sample_php_expectation(),
        "baseline_identity": "workspace test-fixtures/sample-php-app",
    },
    "local-sample-csharp": {
        "toml": {
            "display_name": "Local sample C# (ASP.NET + NuGet)",
            "source_type": "local",
            "local_path": "../../test-fixtures/sample-csharp-app",
            "tags": ["local", "csharp", "nuget", "aspnet", "tests-present", "real-world", "fast", "set-4-13"],
            "languages": ["csharp"],
        },
        "expect": lambda: _sample_csharp_expectation(),
        "baseline_identity": "workspace test-fixtures/sample-csharp-app",
    },
    "local-sample-java": {
        "toml": {
            "display_name": "Local sample Java (Maven + Spring Boot)",
            "source_type": "local",
            "local_path": "../../test-fixtures/sample-java-app",
            "tags": ["local", "java", "maven", "spring-boot", "tests-absent", "real-world", "fast", "set-4-13"],
            "languages": ["java"],
        },
        "expect": lambda: _sample_java_expectation(),
        "baseline_identity": "workspace test-fixtures/sample-java-app",
    },
    "local-terraform-signals": {
        "toml": {
            "display_name": "Local Terraform IaC signals fixture",
            "source_type": "local",
            "local_path": "fixtures/terraform-signals",
            "tags": ["local", "fixture", "cloud", "terraform", "controlled", "fast", "set-4-13"],
            "languages": ["hcl"],
        },
        "expect": lambda: _terraform_expectation(),
        "baseline_identity": "engine/validation/fixtures/terraform-signals",
    },
    "local-serverless-signals": {
        "toml": {
            "display_name": "Local serverless signals fixture",
            "source_type": "local",
            "local_path": "fixtures/serverless-signals",
            "tags": ["local", "fixture", "cloud", "serverless", "controlled", "fast", "set-4-13"],
            "languages": ["python"],
        },
        "expect": lambda: _serverless_expectation(),
        "baseline_identity": "engine/validation/fixtures/serverless-signals",
    },
    "local-typescript-app": {
        "toml": {
            "display_name": "Local TypeScript Express app fixture",
            "source_type": "local",
            "local_path": "fixtures/typescript-app",
            "tags": ["local", "typescript", "npm", "express", "tests-present", "controlled", "fast", "set-4-13"],
            "languages": ["typescript"],
        },
        "expect": lambda: _typescript_expectation(),
        "baseline_identity": "engine/validation/fixtures/typescript-app",
    },
    "local-gradle-multimodule": {
        "toml": {
            "display_name": "Local Gradle multi-module Java fixture",
            "source_type": "local",
            "local_path": "fixtures/gradle-multimodule",
            "tags": ["local", "java", "gradle", "multimodule", "controlled", "fast", "set-4-13"],
            "languages": ["java"],
        },
        "expect": lambda: _gradle_expectation(),
        "baseline_identity": "engine/validation/fixtures/gradle-multimodule",
    },
    "local-cli-python": {
        "toml": {
            "display_name": "Local Python CLI fixture",
            "source_type": "local",
            "local_path": "fixtures/cli-python",
            "tags": ["local", "python", "cli", "tests-absent", "controlled", "fast", "set-4-13"],
            "languages": ["python"],
        },
        "expect": lambda: _cli_python_expectation(),
        "baseline_identity": "engine/validation/fixtures/cli-python",
    },
    "local-library-npm": {
        "toml": {
            "display_name": "Local npm library fixture",
            "source_type": "local",
            "local_path": "fixtures/library-npm",
            "tags": ["local", "javascript", "npm", "library", "controlled", "fast", "set-4-13"],
            "languages": ["javascript"],
        },
        "expect": lambda: _library_npm_expectation(),
        "baseline_identity": "engine/validation/fixtures/library-npm",
    },
    "local-compose-managed": {
        "toml": {
            "display_name": "Local compose managed-services fixture",
            "source_type": "local",
            "local_path": "fixtures/compose-managed",
            "tags": ["local", "fixture", "cloud", "compose", "controlled", "fast", "set-4-13"],
            "languages": ["yaml"],
        },
        "expect": lambda: _compose_managed_expectation(),
        "baseline_identity": "engine/validation/fixtures/compose-managed",
    },
    "local-ai-negative": {
        "toml": {
            "display_name": "Local AI negative control fixture",
            "source_type": "local",
            "local_path": "fixtures/ai-negative",
            "tags": ["local", "fixture", "ai-readiness", "controlled", "fast", "set-4-13"],
            "languages": ["javascript"],
        },
        "expect": lambda: _ai_negative_expectation(),
        "baseline_identity": "engine/validation/fixtures/ai-negative",
    },
    "remote-python-fastapi": {
        "toml": {
            "display_name": "FastAPI full-stack template (Python)",
            "source_type": "remote",
            "remote_url": "https://github.com/fastapi/full-stack-fastapi-template.git",
            "pinned_ref": "c9e70d65c74f7adda417fc8de0757207ff77514c",
            "expected_commit": "c9e70d65c74f7adda417fc8de0757207ff77514c",
            "tags": ["remote", "python", "fastapi", "medium", "network", "real-world", "set-4-13"],
            "languages": ["python"],
        },
        "expect": lambda: _remote_fastapi_expectation(),
        "baseline_identity": "https://github.com/fastapi/full-stack-fastapi-template.git@c9e70d65c74f7adda417fc8de0757207ff77514c",
    },
    "remote-typescript-angular": {
        "toml": {
            "display_name": "Angular RealWorld example (TypeScript)",
            "source_type": "remote",
            "remote_url": "https://github.com/gothinkster/angular-realworld-example-app.git",
            "pinned_ref": "dd99ed2cf39c805d719f943c5d7061a5683d98a8",
            "expected_commit": "dd99ed2cf39c805d719f943c5d7061a5683d98a8",
            "tags": ["remote", "typescript", "angular", "medium", "network", "real-world", "set-4-13"],
            "languages": ["typescript"],
        },
        "expect": lambda: _remote_angular_expectation(),
        "baseline_identity": "https://github.com/gothinkster/angular-realworld-example-app.git@dd99ed2cf39c805d719f943c5d7061a5683d98a8",
    },
    "remote-php-bookstack": {
        "toml": {
            "display_name": "BookStack (PHP)",
            "source_type": "remote",
            "remote_url": "https://github.com/BookStackApp/BookStack.git",
            "pinned_ref": "4e406c41c4c8060a5795e74c66fb96362e54f400",
            "expected_commit": "4e406c41c4c8060a5795e74c66fb96362e54f400",
            "tags": ["remote", "php", "medium", "network", "real-world", "set-4-13"],
            "languages": ["php"],
        },
        "expect": lambda: _remote_bookstack_expectation(),
        "baseline_identity": "https://github.com/BookStackApp/BookStack.git@4e406c41c4c8060a5795e74c66fb96362e54f400",
    },
    "remote-csharp-eshop": {
        "toml": {
            "display_name": ".NET eShop (C#)",
            "source_type": "remote",
            "remote_url": "https://github.com/dotnet/eShop.git",
            "pinned_ref": "9b4f9434f46fdc5c1a6e9e936af2868340cdbc48",
            "expected_commit": "9b4f9434f46fdc5c1a6e9e936af2868340cdbc48",
            "tags": ["remote", "csharp", "slow", "network", "real-world", "set-4-13"],
            "languages": ["csharp"],
        },
        "expect": lambda: _remote_eshop_expectation(),
        "baseline_identity": "https://github.com/dotnet/eShop.git@9b4f9434f46fdc5c1a6e9e936af2868340cdbc48",
    },
}


def _arch_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-architecture-signals focus repository.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["Java"],
            "required_frameworks": [],
            "required_build_systems": [],
            "required_dependency_ecosystems": [],
            "expected_repository_facts": ["has_tests=True"],
            "allowed_ambiguous_facts": [],
        },
        "Controlled architecture-signals Java fixture with intentional cycle and layer skip.",
    )
    e["architecture"] = pack(
        {
            "required_findings": [
                {"rule_id": "architecture.dependency-cycle", "expected_count": 1, "rationale": "Intentional domain↔application cycle"},
                {"rule_id": "architecture.layer-boundary-violation", "path_pattern": "controller/", "expected_count": 1, "rationale": "Presentation→persistence skip"},
            ],
            "forbidden_findings": [],
            "allowed_findings": [
                {"rule_id": "architecture.invalid-dependency-direction", "rationale": "Allowed overlap with cycle/boundary"},
                {"rule_id": "ARCH001", "rationale": "legacy"},
            ],
            "forbidden_rule_ids": ["architecture.framework-leakage", "architecture.enterprise-standard-mismatch"],
            "maximum_false_positive_count": 0,
            "forbidden_unsupported_claims": ["microservices", "well-architected", "production-ready architecture"],
        },
        "Controlled architecture-signals fixture. Require cycle + layer-boundary-violation; forbid enterprise framework-leakage claims.",
    )
    for k, neg in (
        ("security", SECURITY_NEG),
        ("technical_debt", TD_NEG),
        ("dependency", DEP_NEG),
        ("cloud", CLOUD_NEG),
        ("ai_readiness", AI_NEG),
        ("modernization", MOD_NEG),
    ):
        e[k] = pack(dict(neg), f"Non-focus negative control for architecture fixture.")
    return e


def _complexity_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-complexity-signals focus repository.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {"required_languages": ["Python"], "allowed_ambiguous_facts": []},
        "Controlled complexity-signals Python fixture.",
    )
    e["technical_debt"] = pack(
        {
            "required_findings": [
                {"rule_id": "technical_debt.large-callable", "path_pattern": "above_threshold", "symbol_pattern": "large_above"},
                {"rule_id": "technical_debt.excessive-branching", "path_pattern": "above_threshold", "symbol_pattern": "branch_above"},
                {"rule_id": "technical_debt.deep-nesting", "path_pattern": "above_threshold", "symbol_pattern": "nest_above"},
                {"rule_id": "technical_debt.excessive-parameters", "path_pattern": "above_threshold", "symbol_pattern": "params_above"},
                {"rule_id": "technical_debt.oversized-type", "path_pattern": "oversized_type", "symbol_pattern": "OversizedType"},
            ],
            "forbidden_findings": [
                {"rule_id": "technical_debt.large-callable", "path_pattern": "below_threshold", "rationale": "below threshold must not match"},
                {"rule_id": "technical_debt.large-callable", "path_pattern": "equal_threshold", "rationale": "equal threshold must not match"},
                {"rule_id": "technical_debt.large-callable", "path_pattern": "tests/", "rationale": "test-only excluded"},
            ],
            "maximum_false_positive_count": 0,
            "forbidden_conclusions": TD_NEG["forbidden_conclusions"],
        },
        "Controlled complexity-signals fixture. Require all five TD rules on above-threshold production subjects.",
    )
    return e


def _dependency_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-dependency-signals focus repository.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {"required_languages": ["Java", "Python"], "required_dependency_ecosystems": ["maven", "pip"], "allowed_ambiguous_facts": []},
        "Controlled dependency-signals fixture with pom.xml and requirements.txt.",
    )
    e["dependency"] = pack(
        {
            "required_manifests": [
                {"path": "pom.xml", "ecosystem": "maven", "manifest_type": "pom.xml"},
                {"path": "requirements.txt", "ecosystem": "python", "manifest_type": "requirements.txt"},
            ],
            "required_findings": [
                {"rule_id": "dependency.unresolved-version", "path": "pom.xml", "dependency_pattern": "missing-prop-lib"},
                {"rule_id": "dependency.mutable-version", "path": "pom.xml", "dependency_pattern": "snapshot-lib"},
                {"rule_id": "dependency.unbounded-requirement", "path": "requirements.txt", "dependency_name": "unbounded-pkg"},
                {"rule_id": "dependency.conflicting-exact-versions", "path": "pom.xml", "dependency_pattern": "conflict-lib"},
                {"rule_id": "dependency.duplicate-declaration", "path": "pom.xml", "dependency_pattern": "dup-lib"},
            ],
            "forbidden_findings": [
                {"rule_id": "dependency.unresolved-version", "dependency_pattern": "known-lib", "rationale": "resolved property negative"},
            ],
            "maximum_false_positive_count": 0,
            "forbidden_conclusions": DEP_NEG["forbidden_conclusions"],
        },
        "Controlled dependency-signals fixture. Require all five dependency hygiene rules.",
    )
    return e


def _sample_php_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-sample-php workspace fixture.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["PHP"],
            "required_frameworks": ["Laravel"],
            "required_build_systems": ["Composer"],
            "required_dependency_ecosystems": ["composer"],
            "expected_repository_facts": ["has_tests=True"],
            "allowed_ambiguous_facts": [],
        },
        "sample-php-app: composer.json with Laravel; phpunit tests present.",
    )
    return e


def _sample_csharp_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-sample-csharp workspace fixture.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["C#"],
            "required_frameworks": ["ASP.NET"],
            "required_build_systems": ["NuGet"],
            "required_dependency_ecosystems": ["nuget"],
            "expected_repository_facts": ["has_tests=True"],
            "allowed_ambiguous_facts": [],
        },
        "sample-csharp-app: ASP.NET Web SDK + NuGet packages; xUnit tests present.",
    )
    return e


def _sample_java_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-sample-java workspace fixture.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["Java"],
            "required_frameworks": ["Spring Boot"],
            "required_build_systems": ["Maven"],
            "required_dependency_ecosystems": ["maven"],
            "expected_repository_facts": ["has_tests=False"],
            "forbidden_repository_facts": ["has_tests=True"],
            "allowed_ambiguous_facts": [],
        },
        "sample-java-app: pom.xml with Spring Boot; junit dependency in test scope but no test sources.",
    )
    return e


def _terraform_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-terraform-signals cloud/IaC focus.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {
            "forbidden_languages": ["JavaScript", "Python", "Java", "TypeScript"],
            "expected_application_indicators": [],
            "forbidden_application_indicators": ["web_application"],
            "allowed_ambiguous_facts": [],
        },
        "main.tf only — Terraform HCL with AWS provider and resource stubs. Do not invent language stacks.",
    )
    e["cloud"] = pack(
        {
            "required_signal_families": [{"family_id": "iac", "rationale": "Terraform main.tf present"}],
            "required_findings": [],
            "allowed_findings": [],
            "forbidden_rule_ids": [],
            "maximum_false_positive_count": 1,
            "forbidden_conclusions": CLOUD_NEG["forbidden_conclusions"],
        },
        "Terraform IaC stub. Require IaC family when product emits it; forbid inventing application language stacks.",
    )
    return e


def _serverless_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-serverless-signals cloud focus.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {"required_languages": ["Python"], "allowed_ambiguous_facts": []},
        "serverless.yml + handler.py stub naming a Lambda function.",
    )
    e["cloud"] = pack(
        {
            "required_signal_families": [{"family_id": "serverless", "rationale": "serverless.yml present"}],
            "required_signals": [{"family_id": "serverless", "signal_kind": "serverless_framework", "path": "serverless.yml"}],
            "required_findings": [],
            "maximum_false_positive_count": 1,
            "forbidden_conclusions": CLOUD_NEG["forbidden_conclusions"],
        },
        "Serverless framework stub. Require serverless family when product emits it.",
    )
    return e


def _typescript_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-typescript-app fixture.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["TypeScript"],
            "required_frameworks": ["Express"],
            "required_build_systems": ["npm"],
            "required_dependency_ecosystems": ["npm"],
            "required_testing": ["Jest"],
            "expected_repository_facts": ["has_tests=True"],
            "allowed_ambiguous_facts": [],
        },
        "TypeScript Express app with Jest tests in tests/index.test.ts.",
    )
    return e


def _gradle_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-gradle-multimodule fixture.")
    e["finding_count"] = {"minimum": 1}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["Java"],
            "required_build_systems": ["Gradle"],
            "required_dependency_ecosystems": ["gradle"],
            "allowed_ambiguous_facts": [],
        },
        "Gradle multi-module: settings.gradle includes app and lib modules.",
    )
    return e


def _cli_python_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-cli-python fixture.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["Python"],
            "forbidden_frameworks": ["Flask", "Django", "FastAPI"],
            "expected_repository_facts": ["has_tests=False"],
            "forbidden_repository_facts": ["has_tests=True"],
            "expected_application_indicators": [],
            "allowed_ambiguous_facts": [],
        },
        "argparse CLI only via pyproject.toml + src/cli_tool/main.py. No web frameworks.",
    )
    return e


def _library_npm_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-library-npm fixture.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {
            "required_languages": ["JavaScript"],
            "required_build_systems": ["npm"],
            "required_dependency_ecosystems": ["npm"],
            "forbidden_frameworks": ["Express"],
            "allowed_ambiguous_facts": [],
        },
        "npm library package with exports field; no Express dependency.",
    )
    return e


def _compose_managed_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-compose-managed cloud focus.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {
            "forbidden_languages": ["JavaScript", "Python", "Java"],
            "allowed_ambiguous_facts": [],
        },
        "docker-compose.yml with postgres and redis services only.",
    )
    e["cloud"] = pack(
        {
            "required_signal_families": [
                {"family_id": "container", "rationale": "docker-compose present"},
                {"family_id": "managed_service", "rationale": "postgres/redis services"},
            ],
            "required_signals": [{"family_id": "container", "signal_kind": "docker_compose", "path": "docker-compose.yml"}],
            "required_findings": [],
            "maximum_false_positive_count": 1,
            "forbidden_conclusions": CLOUD_NEG["forbidden_conclusions"],
        },
        "Compose managed-service stub. Require container/managed_service families when product emits them.",
    )
    return e


def _ai_negative_expectation() -> dict:
    e = base_expectation("Slice 4.13 — local-ai-negative negative control.")
    e["finding_count"] = {"minimum": 0}
    e["technology_inventory"] = pack(
        {
            "required_languages": [],
            "forbidden_libraries": ["OpenAI"],
            "allowed_ambiguous_facts": [],
        },
        "README prose mentions AI assistant; package.json lists agent-utils only. No openai import or mcp.json.",
    )
    e["ai_readiness"] = pack(
        {
            **AI_NEG,
            "forbidden_signals": [{"family_id": "ai_integration", "path_pattern": "README.md", "rationale": "prose only"}],
            "forbidden_findings": [{"rule_id": "ai_readiness.ai-030", "rationale": "no LLM SDK without import"}],
        },
        "Negative control: prose and dependency name alone must not invent AI integration findings.",
    )
    return e


def _remote_template(lang: str, ecosystem: str, framework: str | None, notes: str) -> dict:
    e = base_expectation(notes)
    e["finding_count"] = {"minimum": 1}
    inv = {
        "required_languages": [lang],
        "required_dependency_ecosystems": [ecosystem],
        "allowed_ambiguous_facts": [],
    }
    if framework:
        inv["required_frameworks"] = [framework]
    e["technology_inventory"] = pack(inv, f"Pinned remote repository inspected for intent. {notes}")
    e["modernization"] = pack(
        {
            **MOD_NEG,
            "forbidden_conclusions": MOD_NEG["forbidden_conclusions"] + ["production deployment", "enterprise ready"],
        },
        "Remote negative control: forbid unsupported modernization/production claims without finding backing.",
    )
    return e


def _remote_fastapi_expectation() -> dict:
    return _remote_template("Python", "pip", "FastAPI", "remote-python-fastapi pinned MIT template.")


def _remote_angular_expectation() -> dict:
    return _remote_template("TypeScript", "npm", "Angular", "remote-typescript-angular pinned MIT RealWorld app.")


def _remote_bookstack_expectation() -> dict:
    return _remote_template("PHP", "composer", "Laravel", "remote-php-bookstack pinned MIT BookStack.")


def _remote_eshop_expectation() -> dict:
    return _remote_template("C#", "nuget", "ASP.NET", "remote-csharp-eshop pinned MIT eShop.")


def write_toml(repo_id: str, meta: dict) -> None:
    lines = [
        f'repository_id = "{repo_id}"',
        f'display_name = "{meta["display_name"]}"',
        f'source_type = "{meta["source_type"]}"',
    ]
    if meta.get("local_path"):
        lines.append(f'local_path = "{meta["local_path"]}"')
    if meta.get("assessment_config"):
        lines.append(f'assessment_config = "{meta["assessment_config"]}"')
    if meta.get("remote_url"):
        lines.append(f'remote_url = "{meta["remote_url"]}"')
    if meta.get("pinned_ref"):
        lines.append(f'pinned_ref = "{meta["pinned_ref"]}"')
    if meta.get("expected_commit"):
        lines.append(f'expected_commit = "{meta["expected_commit"]}"')
    lines.append(f'expected_results_path = "expectations/{repo_id}.json"')
    lines.append("tags = [")
    for tag in meta["tags"]:
        lines.append(f'  "{tag}",')
    lines.append("]")
    lines.append("languages = [")
    for lang in meta["languages"]:
        lines.append(f'  "{lang}",')
    lines.append("]")
    lines.append(f'notes = """{meta.get("notes", meta["display_name"])}"""')
    lines.append("enabled = true")
    path = VAL / "repositories" / f"{repo_id}.toml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_baseline(repo_id: str, identity: str) -> None:
    payload = {
        "repository_id": repo_id,
        "schema_version": "1.2",
        "harness_verdict": "PASS",
        "pinned_source_identity": identity,
    }
    path = VAL / "baselines" / f"{repo_id}.summary.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_existing_tags() -> None:
    updates = {
        "local-sample-js": ["real-world", "fast", "set-4-13"],
        "local-sample-python": ["real-world", "fast", "set-4-13"],
        "remote-java-spring-petclinic": ["real-world", "medium", "set-4-13"],
        "local-cloud-signals": ["controlled", "fast", "set-4-13"],
        "local-security-hygiene": ["controlled", "fast", "set-4-13"],
        "local-ai-readiness": ["controlled", "fast", "set-4-13"],
    }
    for repo_id, new_tags in updates.items():
        path = VAL / "repositories" / f"{repo_id}.toml"
        text = path.read_text(encoding="utf-8")
        for tag in new_tags:
            if tag not in text:
                text = text.replace("tags = [", f'tags = [\n  "{tag}",', 1)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    for repo_id, spec in REPOS.items():
        meta = dict(spec["toml"])
        meta.setdefault("notes", meta["display_name"])
        write_toml(repo_id, meta)
        expect_path = VAL / "expectations" / f"{repo_id}.json"
        expect_path.write_text(json.dumps(spec["expect"](), indent=2) + "\n", encoding="utf-8")
        write_baseline(repo_id, spec["baseline_identity"])
    update_existing_tags()
    print(f"Generated {len(REPOS)} new repository artifacts")


if __name__ == "__main__":
    main()
