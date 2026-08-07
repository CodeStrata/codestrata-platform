# Infrastructure repository export (Slice 12.6)
#
# Authoritative command:
#   python scripts/export_infrastructure_repository.py \\
#     --destination <path-outside-monorepo> [--dry-run]
#
# Supporting package: scripts/repository_export/
# Contract: infrastructure/docs/repository-contract.md (Slice 12.5)
# Verification: verification/infrastructure_repository_exporter/ (Slice 12.6)
#
# Boundaries:
# - no Git operations
# - no AWS operations
# - no OpenTofu plan/apply/destroy
# - OpenTofu fmt/init/validate of exported trees is Slice 12.7
# - no remote repository creation
# - main monorepo remains authoritative pre-cutover
#
# Slice 12.7 verification:
#   PYTHONPATH=. .venv/bin/python -m verification.infrastructure_repository_export
