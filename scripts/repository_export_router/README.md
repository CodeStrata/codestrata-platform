# Repository export target router (Slice 12.8)
#
# Authoritative command:
#   python scripts/export_repository.py --target community|infrastructure \
#     --destination <path> [--dry-run]
#
# Compatibility wrappers:
#   scripts/export-public-repos.py  → community staging export
#   scripts/export_infrastructure_repository.py → infrastructure export
#
# Policies and manifests remain target-specific and are never merged.
#
# CI (Slice 12.9): .github/workflows/ci.yml jobs
#   community-export-verification
#   infrastructure-export-verification
# Boundary verifier: python -m verification.ci_release_boundaries
