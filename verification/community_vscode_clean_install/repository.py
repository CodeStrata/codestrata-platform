"""Re-export Slice 17.21 repository checks."""
from verification.community_vscode_clean_install.package import (  # noqa: F401
    check_activation,
    check_engine_discovery,
    check_install,
    check_package,
    check_profile,
)
from verification.community_vscode_clean_install.assessment import (  # noqa: F401
    check_api_authority,
    check_assessment,
    check_lifecycle,
    check_publishing,
    check_report,
    check_repository,
    check_telemetry,
)
from verification.community_vscode_clean_install.remaining import (  # noqa: F401
    check_docs,
    check_errors,
    check_export,
    check_no_ai,
    check_offline,
    check_performance,
    check_prior_slices,
    check_privacy,
    check_security,
    check_ux,
)
