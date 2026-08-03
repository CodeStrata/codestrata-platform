"""Regenerate public OSS demonstration artifacts.

Usage (from repository root):

    PYTHONPATH=platform:platform/src:engine/src python -m \\
      codestrata_platform.intelligence_reporting.application.oss_demonstration
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.oss_demonstration.builder import (
    generate_oss_demonstration_artifacts,
)


def main() -> None:
    result = generate_oss_demonstration_artifacts(overwrite=True)
    assert result.write_result is not None
    assert result.export_bundle.document.export_metadata is not None
    print(f"report_id={result.report.report_id.value}")
    print(f"dataset_id={result.report.dataset.dataset_id.value}")
    print(f"export_id={result.export_bundle.document.export_metadata.export_id}")
    print(f"output={result.write_result.output_directory}")
    for artifact in result.write_result.artifacts:
        print(f"  {artifact.filename} sha256={artifact.sha256} bytes={artifact.byte_size}")


if __name__ == "__main__":
    main()
