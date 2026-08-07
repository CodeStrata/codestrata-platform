"""Slice 12.5 / 12.6 export policy constants."""

from __future__ import annotations

REPOSITORY_NAME = "codestrata-infrastructure"
REPOSITORY_VISIBILITY = "private"
TARGET = "infrastructure"

SOURCE_LAYOUT_VERSION = "1.0.0"
DESTINATION_LAYOUT_VERSION = "approach_a_1.0.0"

POLICY_ID = "community-infrastructure-repository-policy"
POLICY_VERSION = "1.0"

MANIFEST_SCHEMA_NAME = "infrastructure-repository-export-manifest"
MANIFEST_SCHEMA_VERSION = "1.0.0"

SOURCE_AUTHORITY = (
    "pre_cutover_main_monorepo_authoritative;"
    "post_cutover_infrastructure_repository_authoritative;"
    "dual_authoring_forbidden;"
    "export_one_way"
)

VALIDATION_ROOTS = (
    "modules/community-cloud-api",
    "modules/community-data-lake",
    "production",
)

VALIDATION_COMMANDS = (
    "tofu fmt -check -recursive",
    "tofu init -backend=false -input=false",
    "tofu validate",
)

# Relative to monorepo root — directory prefixes end with /
REQUIRED_SOURCE_PREFIXES = (
    "infrastructure/modules/",
    "infrastructure/production/",
    "infrastructure/tests/",
    "infrastructure/verification/",
    "infrastructure/docs/",
    "infrastructure/policies/",
    "infrastructure/scripts/",
)

REQUIRED_SOURCE_FILES = (
    "infrastructure/README.md",
)

# Copied into destination root (Approach A omits monorepo package marker).
OPTIONAL_SOURCE_FILES = (
    "infrastructure/production/backend.tf.example",
    "infrastructure/production/terraform.tfvars.example",
)

# Destination artifact names (not part of managed content checksum set for self-hash).
# Never include absolute paths, usernames, hostnames, or timestamps in manifests.
MANIFEST_FORBIDDEN_FIELDS = ("timestamp", "created_at", "absolute_path")
MANIFEST_FILENAME = "export-manifest.json"
INVENTORY_FILENAME = "export-inventory.json"
CHECKSUMS_FILENAME = "SHA256SUMS"

ARTIFACT_FILENAMES = frozenset(
    {MANIFEST_FILENAME, INVENTORY_FILENAME, CHECKSUMS_FILENAME}
)

MODE_FILE = 0o644
MODE_EXECUTABLE = 0o755

EXECUTABLE_SUFFIXES = (".sh",)
EXECUTABLE_NAMES = frozenset({"validate.sh", "build-community-cloud-api.sh", "plan-production.sh", "smoke-health.sh"})
