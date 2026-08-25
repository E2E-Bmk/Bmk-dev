"""Shared fixtures, helpers, and constants for authlib JOSE oracle tests."""

from __future__ import annotations

import base64
import copy
import json
import os
import subprocess
import sys

import pytest

from authlib.jose import (
    ECKey,
    JsonWebEncryption,
    JsonWebKey,
    JsonWebSignature,
    JsonWebToken,
    KeySet,
    OctKey,
    OKPKey,
    RSAKey,
)

# Anti-memorization: oracle-specific labels and payloads (not upstream test literals).
ORACLE_KID_ALPHA = "oracle-kid-alpha-7f3a"
ORACLE_KID_BETA = "oracle-kid-beta-9c21"
PAYLOAD_ALPHA = b"oracle-payload-alpha-42"
PAYLOAD_BETA = b"oracle-payload-beta-17"
SYMMETRIC_SECRET = "oracle-symmetric-secret-8k2m"


def b64url_to_int(value: str | bytes) -> int:
    raw = value.encode("ascii") if isinstance(value, str) else value
    raw += b"=" * (-len(raw) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(raw), "big")


def run_python_snippet(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
        check=False,
    )


@pytest.fixture(scope="session")
def oct_key_256():
    return OctKey.generate_key(256, options={"kid": ORACLE_KID_ALPHA}, is_private=True)


@pytest.fixture(scope="session")
def rsa_private_key():
    return RSAKey.generate_key(2048, options={"kid": ORACLE_KID_ALPHA}, is_private=True)


@pytest.fixture(scope="session")
def rsa_public_key(rsa_private_key):
    return RSAKey.import_key(rsa_private_key.as_dict(is_private=False))


@pytest.fixture(scope="session")
def ec_private_key():
    return ECKey.generate_key("P-256", options={"kid": ORACLE_KID_BETA}, is_private=True)


@pytest.fixture(scope="session")
def ec_public_key(ec_private_key):
    return ECKey.import_key(ec_private_key.as_dict(is_private=False))


@pytest.fixture(scope="session")
def okp_x25519_key():
    return OKPKey.generate_key("X25519", is_private=True)


@pytest.fixture(scope="session")
def key_set_single(oct_key_256):
    return KeySet([oct_key_256])


@pytest.fixture(scope="session")
def jws_processor():
    return JsonWebSignature()


@pytest.fixture(scope="session")
def jwe_processor():
    return JsonWebEncryption()


@pytest.fixture(scope="session")
def jwt_processor_hs256():
    return JsonWebToken(["HS256"])


def make_jwks_pair() -> tuple[dict, dict]:
    """Build matching private and public JWKS views of the same two oct keys."""
    key_a = OctKey.generate_key(256, options={"kid": "jwks-alpha"}, is_private=True)
    key_b = OctKey.generate_key(256, options={"kid": "jwks-beta"}, is_private=True)
    keys = [key_a, key_b]
    private = {"keys": [k.as_dict(is_private=True) for k in keys]}
    public = {"keys": [k.as_dict(is_private=False) for k in keys]}
    return private, public


@pytest.fixture(scope="session")
def oct_key_128():
    """128-bit oct key for dir/A128GCM JWE workflows."""
    return OctKey.generate_key(128, options={"kid": ORACLE_KID_BETA}, is_private=True)


def deep_copy_mapping(value):
    return copy.deepcopy(value)
