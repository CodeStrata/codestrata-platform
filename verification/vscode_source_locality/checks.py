"""Focused static checks for Slice 13.10 source locality."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_source_locality.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    INTENDED_VSCODE_VERSION,
    LOCALITY_PACKAGE,
    LOCALITY_POLICY_ID,
    LOCALITY_POLICY_VERSION,
    SRC_ROOT,
)
from verification.vscode_source_locality.models import CheckResult, Defect

_SKIP_DIR_NAMES = {"test", "node_modules", "__pycache__", "out"}


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def _iter_src_ts(monorepo: Path) -> list[Path]:
    root = monorepo / SRC_ROOT
    files: list[Path] = []
    for path in root.rglob("*.ts"):
        if any(part in _SKIP_DIR_NAMES for part in path.parts):
            continue
        if "/test/" in str(path).replace("\\", "/"):
            continue
        files.append(path)
    return files


def _concat_src(monorepo: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in _iter_src_ts(monorepo))


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{LOCALITY_PACKAGE}/policy.ts")
    results = _read(monorepo, f"{LOCALITY_PACKAGE}/results.ts")
    claims = _read(monorepo, f"{LOCALITY_PACKAGE}/claims.ts")
    diagnostics = _read(monorepo, f"{LOCALITY_PACKAGE}/diagnostics.ts")
    docs = _read(monorepo, "vscode-plugin/docs/source-locality.md")
    privacy = _read(monorepo, "vscode-plugin/PRIVACY.md")
    readme = _read(monorepo, "vscode-plugin/README.md")
    src_blob = _concat_src(monorepo)
    events = _read(monorepo, "vscode-plugin/src/telemetry/events.ts")
    analytics_schema = _read(
        monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts"
    )
    report_policy = _read(monorepo, "vscode-plugin/src/reportOpening/policy.ts")
    recovery_policy = _read(monorepo, "vscode-plugin/src/failureRecovery/policy.ts")

    network_needles = (
        'from "axios"',
        "from 'axios'",
        'from "openai"',
        'from "@aws-sdk',
        'from "aws-sdk"',
        'from "node:http"',
        'from "node:https"',
        'from "http"',
        'from "https"',
        "XMLHttpRequest",
        "WebSocket(",
        "net.connect",
        "tls.connect",
    )
    cloud_needles = (
        "codestrata_platform",
        'from "community_cloud',
        "from 'community_cloud",
        'import community_cloud',
        'from "@codestrata/',
        "from '@codestrata/",
    )
    data_lake_import_needles = (
        'from "data_lake',
        "from 'data_lake",
        "import data_lake",
        "community_data_lake",
    )
    write_needles = ("writeFileSync(", "writeFile(", "mkdirSync(")
    git_needles = ("git add", "git commit", "git push", "git tag", "git remote")
    overclaims = (
        "never leaves your machine",
        "source code never leaves",
        "all ai data always stays local",
        "ai assessment sends no data off machine",
    )

    has_network = any(n in src_blob for n in network_needles)
    has_cloud = any(n in src_blob for n in cloud_needles)
    has_data_lake_import = any(n in src_blob for n in data_lake_import_needles)
    has_write = any(n in src_blob for n in write_needles)
    has_git = any(n in src_blob.lower() for n in git_needles)
    has_machine = "vscode.env.machineId" in src_blob
    has_openai_env = "process.env.OPENAI_API_KEY" in src_blob
    has_aws_env = "process.env.AWS_SECRET_ACCESS_KEY" in src_blob
    has_fetch_call = bool(re.search(r"\bfetch\s*\(", src_blob))
    docs_blob = f"{docs}\n{privacy}\n{readme}".lower()
    has_overclaim = any(o in docs_blob for o in overclaims)
    ai_qualified = (
        "configured AI provider" in docs
        or "configured AI-provider" in docs
        or "configured ai provider" in docs.lower()
    )

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                LOCALITY_POLICY_ID in policy and LOCALITY_POLICY_VERSION in policy,
                f"{LOCALITY_POLICY_ID}:{LOCALITY_POLICY_VERSION}",
                "locality_policy",
            ),
            CheckResult(
                "policy:upload_forbidden",
                "extension_source_upload_allowed: false" in policy
                and "extension_report_upload_allowed: false" in policy
                and "extension_cloud_api_access_allowed: false" in policy,
                "upload/cloud forbidden",
                "locality_policy",
            ),
            CheckResult(
                "policy:ai_boundary",
                "extension_ai_provider_calls_allowed: false" in policy
                and "ai_assessment_engine_provider_flow_possible: true" in policy
                and "provider_credentials_extension_owned: false" in policy,
                "AI Engine-owned",
                "ai_provider_boundary",
            ),
            CheckResult(
                "fs:no_production_writes",
                not has_write,
                "no writeFile/mkdir in production src",
                "filesystem_write",
            ),
            CheckResult(
                "fs:config_detection_read",
                "codestrata.toml" in src_blob
                or "detectRepositoryInitState" in src_blob,
                "config metadata reads only",
                "filesystem_read",
            ),
            CheckResult(
                "artifacts:approved",
                "report.html" in results
                and "codestrata.toml" in results
                and "local_report_artifact" in results,
                "approved artifact classes",
                "generated_artifact",
            ),
            CheckResult(
                "process:spawn_local",
                'from "node:child_process"' in src_blob
                and "shell: false" in src_blob
                and "runCodestrataCli" in src_blob,
                "local spawn shell:false",
                "process_boundary",
            ),
            CheckResult(
                "standard:local_claim",
                "standard_assessment_local" in claims
                and "local child process" in docs.lower(),
                "standard assessment local",
                "standard_assessment",
            ),
            CheckResult(
                "ai:qualified_docs",
                ai_qualified and "Engine may send" in docs,
                "AI provider flow qualified",
                "ai_assessment",
            ),
            CheckResult(
                "ai:no_extension_sdk",
                not any(n in src_blob for n in ('from "openai"', 'from "@aws-sdk')),
                "no provider SDK imports",
                "ai_provider_boundary",
            ),
            CheckResult(
                "report:local_open",
                "local_only: true" in report_policy
                and "report_content_transmission_allowed: false" in report_policy,
                "report local only",
                "report_boundary",
            ),
            CheckResult(
                "discovery:no_upload",
                "discoverCodeStrataCli" in src_blob
                and "extension_source_upload_allowed: false" in policy,
                "discovery local probe",
                "discovery_boundary",
            ),
            CheckResult(
                "install:guidance_only",
                "automatic_installation_forbidden" in src_blob
                or "automaticInstallationAllowed" in src_blob
                or "Approach A" in _read(
                    monorepo, "vscode-plugin/src/cliInstallation/policy.ts"
                ),
                "install guidance only",
                "installation_boundary",
            ),
            CheckResult(
                "init:engine_owned",
                "planRepositoryInitialization" in src_blob
                and "source_file_mutation_allowed: false" in policy,
                "init Engine-owned",
                "initialization_boundary",
            ),
            CheckResult(
                "recovery:no_network",
                "telemetry_allowed: false" in recovery_policy
                and "analytics_allowed: false" in recovery_policy,
                "recovery no telemetry/analytics",
                "recovery_boundary",
            ),
            CheckResult(
                "telemetry:no_source_fields",
                "path" not in _read(
                    monorepo, "vscode-plugin/src/telemetry/events.ts"
                ).split("APPROVED_FIELD_NAMES")[1][:800]
                if "APPROVED_FIELD_NAMES" in events
                else "APPROVED_FIELD_NAMES" in events,
                "telemetry allowlist",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:forbidden_source",
                "installation_id" in analytics_schema.lower()
                or "FORBIDDEN_ANALYTICS" in analytics_schema,
                "analytics forbids identity/source",
                "analytics_boundary",
            ),
            CheckResult(
                "network:no_clients",
                not has_network and not has_fetch_call,
                "no network clients",
                "network_boundary",
            ),
            CheckResult(
                "cloud:no_client",
                not has_cloud and "extension_cloud_api_access_allowed: false" in policy,
                "no Community Cloud client",
                "cloud_boundary",
            ),
            CheckResult(
                "data_lake:no_client",
                not has_data_lake_import
                and "extension_data_lake_access_allowed: false" in policy,
                "no Data Lake client",
                "data_lake_boundary",
            ),
            CheckResult(
                "identity:no_machine",
                not has_machine
                and "machine_identity_allowed: false"
                in _read(
                    monorepo,
                    "vscode-plugin/src/telemetryConsentIntegration/policy.ts",
                ),
                "no machine identity",
                "identity_boundary",
            ),
            CheckResult(
                "credential:no_env_keys",
                not has_openai_env and not has_aws_env,
                "no provider env credential reads",
                "credential_boundary",
            ),
            CheckResult(
                "git:no_mutation",
                not has_git and "git_mutation_allowed: false" in policy,
                "no Git mutation",
                "git_boundary",
            ),
            CheckResult(
                "output:no_payload_dump",
                "TELEMETRY_CONSENT_MESSAGE" in src_blob
                and "eventToIntakeDict" in src_blob,
                "telemetry not dumped to users as payload",
                "output_boundary",
            ),
            CheckResult(
                "privacy:no_overclaim",
                not has_overclaim and ai_qualified,
                "no unqualified AI locality overclaim",
                "privacy_claim",
            ),
            CheckResult(
                "privacy:diagnostics",
                "localityDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy_claim",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/source-locality.md").is_file()
                and "does not upload" in docs.lower(),
                "docs present",
                "privacy_claim",
            ),
            CheckResult(
                "vscode:version",
                _pkg_version(monorepo) == INTENDED_VSCODE_VERSION,
                _pkg_version(monorepo),
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in _read(
                    monorepo, "vscode-plugin/src/extension.ts"
                ),
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "sourceLocality.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "prior:integration_policy_1_0",
                'TELEMETRY_INTEGRATION_POLICY_VERSION = "1.0"'
                in _read(
                    monorepo,
                    "vscode-plugin/src/telemetryConsentIntegration/policy.ts",
                ),
                "13.9 policy 1.0",
                "vscode_regression",
            ),
        ]
    )

    if has_network or has_fetch_call:
        defects.append(
            Defect("network defect", "extension", "no client", "network client")
        )
    if has_write:
        defects.append(
            Defect(
                "filesystem-write defect",
                "extension",
                "no production writes",
                "writeFile",
            )
        )
    if has_overclaim:
        defects.append(
            Defect(
                "output/privacy-claim defect",
                "docs",
                "qualified AI locality",
                "overclaim",
            )
        )

    _ = json.loads(_read(monorepo, "vscode-plugin/package.json"))
    return checks, defects
