"""Network-dependent showcase fetch tests (opt-in; not part of default CI).

Run explicitly:

    pytest -m network tests/examples/test_showcase_network.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "examples" / "real-world" / "scripts"


def _load_module():
    path = SCRIPTS / "fetch_example.py"
    name = "fetch_example_network"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.network
def test_fetch_spring_petclinic_pinned_sha(tmp_path: Path):
    fetch_mod = _load_module()
    result = fetch_mod.fetch_example(
        "spring-petclinic",
        repo_root=tmp_path,
        examples_root=REPO_ROOT / "examples",
        force=True,
    )
    assert result["commit_sha"] == "f182358d02e4a68e52bdbabf55ca7800288511e7"
    provenance = Path(result["provenance"])
    assert provenance.is_file()
