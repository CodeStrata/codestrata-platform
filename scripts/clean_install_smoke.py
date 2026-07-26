#!/usr/bin/env python3
"""Clean-install smoke test for CodeStrata packaging (Phase 5.14).

Builds a wheel, installs it into a fresh virtualenv, and runs deterministic
onboard against a tiny sample repository with no cloud credentials.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "release-readiness"
DIST = ROOT / "dist"

SMOKE_CONFIG = """\
[repository]
path = "{repository}"

[workspace]
directory = ".codestrata/workspace"
clean_before_clone = true

[knowledge]
directory = ".codestrata/knowledge"
enabled = true

[knowledge.projection]
enabled = true

[knowledge.chunking]
enabled = true

[knowledge.embedding]
enabled = true
provider = "deterministic"
model = "deterministic-test-embedding"
dimension = 384

[knowledge.indexing]
enabled = true

[knowledge.retrieval]
enabled = true

[knowledge.answering]
enabled = true
provider = "deterministic_extractive"

[knowledge.vector_store]
provider = "memory"

[mcp]
enabled = true
transport = "stdio"

[ai]
embedding_provider = "deterministic"
answer_provider = "deterministic_extractive"

[static_analysis]
enabled = false

[report]
title = "CodeStrata Smoke Assessment"

[report.sections.roadmap]
enabled = true
"""


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def _write_sample_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text(
        "# smoke-sample\n\nMinimal repository for clean-install smoke.\n",
        encoding="utf-8",
    )
    (path / "package.json").write_text(
        json.dumps(
            {"name": "smoke-sample", "version": "0.0.1", "private": True},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    src = path / "src"
    src.mkdir(exist_ok=True)
    (src / "index.js").write_text("console.log('smoke');\n", encoding="utf-8")


def main() -> int:
    output = Path(os.environ.get("CODESTRATA_RELEASE_OUTPUT", str(DEFAULT_OUTPUT)))
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "clean-install-smoke.json"
    steps: list[dict[str, object]] = []
    result: dict[str, object] = {"ok": False, "detail": "not started", "steps": steps}

    try:
        try:
            import build  # noqa: F401
        except ImportError:
            proc = _run([sys.executable, "-m", "pip", "install", "build"])
            if proc.returncode != 0:
                result["detail"] = "failed to install build"
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

        if DIST.exists():
            shutil.rmtree(DIST)
        build_proc = _run([sys.executable, "-m", "build", "--outdir", str(DIST)], cwd=ROOT)
        steps.append(
            {
                "name": "build",
                "ok": build_proc.returncode == 0,
                "stderr": build_proc.stderr[-2000:],
            }
        )
        if build_proc.returncode != 0:
            result["detail"] = "package build failed"
            print(build_proc.stderr, file=sys.stderr)
            summary_path.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return 1

        wheels = sorted(DIST.glob("*.whl"))
        if not wheels:
            result["detail"] = "no wheel produced"
            summary_path.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return 1
        wheel = wheels[-1]
        result["wheel"] = wheel.name

        with tempfile.TemporaryDirectory(prefix="codestrata-clean-install-") as tmp:
            tmp_path = Path(tmp)
            venv_dir = tmp_path / "venv"
            sample = tmp_path / "sample"
            config = tmp_path / "codestrata.toml"
            reports = tmp_path / "reports"
            _write_sample_repo(sample)
            config.write_text(SMOKE_CONFIG.format(repository=sample.as_posix()), encoding="utf-8")

            venv.create(venv_dir, with_pip=True, clear=True)
            python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            codestrata_bin = venv_dir / (
                "Scripts/codestrata.exe" if sys.platform == "win32" else "bin/codestrata"
            )

            clean_env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith(("AWS_", "OPENAI_", "BEDROCK_", "CODESTRATA_DATABASE"))
            }
            clean_env["PATH"] = str(python.parent) + os.pathsep + clean_env.get("PATH", "")

            install = _run(
                [str(python), "-m", "pip", "install", str(wheel), "mcp>=1.27,<2"],
                env=clean_env,
            )
            steps.append(
                {
                    "name": "install_wheel",
                    "ok": install.returncode == 0,
                    "wheel": wheel.name,
                    "stderr": install.stderr[-2000:],
                }
            )
            if install.returncode != 0:
                result["detail"] = "wheel install failed"
                print(install.stderr, file=sys.stderr)
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

            import_ok = _run(
                [
                    str(python),
                    "-c",
                    (
                        "import codestrata; "
                        "import importlib.util; "
                        "assert importlib.util.find_spec('aimf') is None; "
                        "print(codestrata.__version__)"
                    ),
                ],
                env=clean_env,
            )
            steps.append(
                {
                    "name": "import_codestrata_not_aimf",
                    "ok": import_ok.returncode == 0,
                    "stdout": import_ok.stdout[-500:],
                    "stderr": import_ok.stderr[-500:],
                }
            )
            if import_ok.returncode != 0:
                result["detail"] = "import codestrata failed or aimf still importable"
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

            aimf_bin = venv_dir / ("Scripts/aimf.exe" if sys.platform == "win32" else "bin/aimf")
            steps.append(
                {
                    "name": "aimf_cli_absent",
                    "ok": not aimf_bin.exists(),
                    "path": str(aimf_bin),
                }
            )
            if aimf_bin.exists():
                result["detail"] = "legacy aimf CLI entry point still installed"
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

            command_steps: list[tuple[list[str], str]] = [
                ([str(codestrata_bin), "--help"], "codestrata_help"),
                ([str(codestrata_bin), "version"], "codestrata_version"),
                ([str(codestrata_bin), "onboard", "--help"], "onboard_help"),
                ([str(codestrata_bin), "report", "validate", "--help"], "report_validate_help"),
                ([str(codestrata_bin), "acceptance", "run", "--help"], "acceptance_run_help"),
                ([str(codestrata_bin), "mcp", "health", "--config", str(config)], "mcp_health"),
                (
                    [
                        str(codestrata_bin),
                        "onboard",
                        str(sample),
                        "--config",
                        str(config),
                        "--output",
                        str(reports),
                        "--provider",
                        "deterministic",
                    ],
                    "onboard_sample",
                ),
            ]
            report_json: Path | None = None
            for command, name in command_steps:
                proc = _run(command, env=clean_env, cwd=tmp_path)
                ok = proc.returncode == 0
                steps.append(
                    {
                        "name": name,
                        "ok": ok,
                        "returncode": proc.returncode,
                        "stdout": proc.stdout[-1500:],
                        "stderr": proc.stderr[-1500:],
                    }
                )
                if not ok:
                    result["detail"] = f"step failed: {name}"
                    print(proc.stdout)
                    print(proc.stderr, file=sys.stderr)
                    summary_path.write_text(
                        json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    return 1
                if name == "onboard_sample":
                    candidates = sorted(reports.rglob("report.json"))
                    report_json = candidates[-1] if candidates else None

            if report_json is None:
                result["detail"] = "onboard did not produce report.json"
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

            validate = _run(
                [str(codestrata_bin), "report", "validate", str(report_json)],
                env=clean_env,
            )
            steps.append(
                {
                    "name": "report_validate",
                    "ok": validate.returncode == 0,
                    "report": str(report_json),
                    "stdout": validate.stdout[-1500:],
                    "stderr": validate.stderr[-1500:],
                }
            )
            if validate.returncode != 0:
                result["detail"] = "report validate failed"
                summary_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return 1

        failed = [step["name"] for step in steps if not step.get("ok")]
        result["ok"] = not failed
        result["detail"] = "pass" if result["ok"] else f"failed steps: {failed}"
        summary_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"clean-install smoke: {'PASS' if result['ok'] else 'FAIL'}")
        print(f"summary: {summary_path}")
        return 0 if result["ok"] else 1
    except Exception as error:  # noqa: BLE001
        result["detail"] = str(error)
        summary_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"clean-install smoke failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
