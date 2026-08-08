"""Password verification — scrypt preferred; raw compare as documented fallback."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64


def hash_password(password: str) -> str:
    """Create a Secrets Manager–ready scrypt verifier JSON string."""

    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    payload = {
        "algorithm": "scrypt",
        "hash_b64": base64.b64encode(derived).decode("ascii"),
        "n": SCRYPT_N,
        "p": SCRYPT_P,
        "r": SCRYPT_R,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def verify_password(*, submitted: str, stored_secret: str) -> bool:
    """Verify submitted password against Secrets Manager material.

    Supports scrypt JSON verifiers. If the secret is a raw password string,
    uses hmac.compare_digest (documented limitation — prefer scrypt).
    Never logs submitted or stored values.
    """

    if not submitted or not stored_secret:
        return False
    text = stored_secret.strip()
    if text.startswith("{") and '"algorithm"' in text:
        try:
            data: dict[str, Any] = json.loads(text)
        except json.JSONDecodeError:
            return False
        if data.get("algorithm") != "scrypt":
            return False
        try:
            salt = base64.b64decode(str(data["salt_b64"]))
            expected = base64.b64decode(str(data["hash_b64"]))
            n = int(data.get("n", SCRYPT_N))
            r = int(data.get("r", SCRYPT_R))
            p = int(data.get("p", SCRYPT_P))
        except (KeyError, TypeError, ValueError):
            return False
        try:
            actual = hashlib.scrypt(
                submitted.encode("utf-8"),
                salt=salt,
                n=n,
                r=r,
                p=p,
                dklen=len(expected) or SCRYPT_DKLEN,
            )
        except (ValueError, TypeError, OverflowError):
            return False
        return hmac.compare_digest(actual, expected)

    # Raw password in Secrets Manager — discouraged; constant-time compare.
    return hmac.compare_digest(
        submitted.encode("utf-8"),
        text.encode("utf-8"),
    )
