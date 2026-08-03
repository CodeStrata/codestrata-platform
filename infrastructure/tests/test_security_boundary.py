"""Security / no-secrets scans for infrastructure/."""

from __future__ import annotations

import re
from pathlib import Path

INFRA = Path(__file__).resolve().parents[1]

# Real-looking secrets — not documentation placeholders.
AWS_ACCESS_KEY = re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")
# Real Authorization bearer values (not prose mentioning the Bearer scheme).
BEARER_VALUE = re.compile(
    r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9\-._~+/]{12,}"
)
CSCC_TOKEN = re.compile(r"cscc_v1_[A-Za-z0-9]{8,}")
PRIVATE_KEY = re.compile(r"BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY")
HOME_PATH = re.compile(r"(?i)/(?:Users|home)/[A-Za-z0-9._-]+/")
FILE_URI = re.compile("file" + "://" )

SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".zip"}
SKIP_DIR_NAMES = {".terraform", ".pytest_cache", "__pycache__"}
SKIP_RELATIVE_PREFIXES = ("tests/",)


def _iter_text_files():
    for path in INFRA.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        rel = path.relative_to(INFRA).as_posix()
        if rel.startswith(SKIP_RELATIVE_PREFIXES):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield path, text


def test_no_aws_access_keys() -> None:
    for path, text in _iter_text_files():
        # Allow documented placeholder account id 123456789012 in examples only.
        assert not AWS_ACCESS_KEY.search(text), path


def test_no_community_tokens_or_bearers() -> None:
    for path, text in _iter_text_files():
        assert not CSCC_TOKEN.search(text), path
        assert not BEARER_VALUE.search(text), path


def test_no_private_keys() -> None:
    for path, text in _iter_text_files():
        assert not PRIVATE_KEY.search(text), path


def test_no_home_or_file_uris() -> None:
    for path, text in _iter_text_files():
        assert not HOME_PATH.search(text), path
        assert not FILE_URI.search(text), path


def test_no_password_assignments() -> None:
    pattern = re.compile(r"(?i)(password|secret_access_key)\s*=\s*['\"][^'\"]{8,}")
    for path, text in _iter_text_files():
        assert not pattern.search(text), path


def test_policy_json_has_no_star_star() -> None:
    policy = (INFRA / "policies" / "lambda-execution-policy.json").read_text(
        encoding="utf-8"
    )
    assert '"Action": "*"' not in policy
    # Only the AWS-documented GetAuthorizationToken exception may use Resource *.
    assert policy.count('"Resource": "*"') == 1
    assert "EcrAuthorizationTokenDocumentedWildcard" in policy
