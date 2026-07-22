"""Integration tests for authlib-fullrepro-001.

Each test crosses at least two public API boundaries.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from authlib.jose import (
    BaseClaims,
    JsonWebEncryption,
    JsonWebKey,
    JsonWebSignature,
    JsonWebToken,
    KeySet,
    OctKey,
    errors,
    jwt,
)
from authlib.jose.errors import BadSignatureError, InsecureClaimError, UnsupportedAlgorithmError

from conftest import (
    ORACLE_KID_ALPHA,
    ORACLE_KID_BETA,
    PAYLOAD_ALPHA,
    PAYLOAD_BETA,
    SYMMETRIC_SECRET,
    make_jwks_pair,
    run_python_snippet,
)


# --- CVI: key and message projections ---


def test_imported_key_public_projection_supports_verification(oct_key_256):
    """CVI-1: imported key public JWK fields must support signature verification."""
    jws = JsonWebSignature()
    signed = jws.serialize_compact({"alg": "HS256"}, PAYLOAD_ALPHA, oct_key_256)
    verified = jws.deserialize_compact(signed, oct_key_256)
    exported = oct_key_256.as_dict(is_private=False)
    assert verified["payload"] == PAYLOAD_ALPHA
    assert exported["kty"] == "oct"
    assert exported["kid"] == ORACLE_KID_ALPHA


def test_private_key_reimport_preserves_public_projection(rsa_private_key):
    """CVI-2: private export and reimport must preserve the public projection."""
    exported_private = rsa_private_key.as_dict(is_private=True)
    reimported = JsonWebKey.import_key(exported_private)
    original_public = rsa_private_key.as_dict(is_private=False)
    reimported_public = reimported.as_dict(is_private=False)
    assert reimported_public["n"] == original_public["n"]
    assert reimported_public["e"] == original_public["e"]
    assert "d" not in reimported_public


def test_keyset_kid_visible_in_jwt_header(key_set_single):
    """CVI-3: key-set kid selection must appear in encoded JWT headers."""
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, {"sub": "user-7"}, key_set_single)
    claims = JsonWebToken(["HS256"]).decode(token, key_set_single)
    assert claims.header["kid"] == ORACLE_KID_ALPHA
    assert claims["sub"] == "user-7"


def test_jws_compact_sign_deserialize_round_trip(oct_key_256):
    """CVI-4: compact JWS serialize and deserialize must preserve payload bytes."""
    jws = JsonWebSignature()
    signed = jws.serialize({"alg": "HS256"}, PAYLOAD_BETA, oct_key_256)
    verified = jws.deserialize(signed, oct_key_256)
    assert verified["payload"] == PAYLOAD_BETA
    assert verified["header"]["alg"] == "HS256"


def test_jws_json_sign_deserialize_round_trip():
    """CVI-5: JSON JWS serialize and deserialize must preserve payload bytes."""
    header = {"protected": {"alg": "HS256"}, "header": {"kid": "json-jws-kid"}}
    jws = JsonWebSignature()
    signed = jws.serialize_json(header, PAYLOAD_ALPHA, SYMMETRIC_SECRET)
    verified = jws.deserialize_json(signed, SYMMETRIC_SECRET)
    assert verified["payload"] == PAYLOAD_ALPHA
    assert verified["header"]["kid"] == "json-jws-kid"


def test_jwe_compact_encrypt_decrypt_round_trip(oct_key_128):
    """CVI-6: compact JWE serialize and deserialize must preserve payload bytes."""
    jwe = JsonWebEncryption()
    protected = {"alg": "dir", "enc": "A128GCM"}
    encrypted = jwe.serialize_compact(protected, PAYLOAD_ALPHA, oct_key_128)
    decrypted = jwe.deserialize_compact(encrypted, oct_key_128)
    assert decrypted["payload"] == PAYLOAD_ALPHA
    assert decrypted["header"]["enc"] == "A128GCM"


def test_jwe_json_encrypt_decrypt_round_trip(oct_key_128):
    """CVI-7: JSON JWE serialize and deserialize must preserve payload bytes."""
    jwe = JsonWebEncryption()
    header = {
        "protected": {"alg": "dir", "enc": "A128GCM"},
        "recipients": [{"header": {"kid": ORACLE_KID_BETA}}],
    }
    encrypted = jwe.serialize_json(header, PAYLOAD_BETA, oct_key_128)
    decrypted = jwe.deserialize_json(encrypted, (ORACLE_KID_BETA, oct_key_128))
    assert decrypted["payload"] == PAYLOAD_BETA
    assert decrypted["header"]["recipients"][0]["header"]["kid"] == ORACLE_KID_BETA


def test_jwt_jws_path_encode_decode_round_trip(oct_key_256):
    """CVI-8: JWT without enc must decode through the JWS path with equal claims."""
    payload = {"sub": "jwt-jws-user", "scope": "read:data"}
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, payload, oct_key_256)
    claims = JsonWebToken(["HS256"]).decode(token, oct_key_256)
    assert token.count(b".") == 2
    assert dict(claims) == payload


def test_jwt_jwe_path_encode_decode_round_trip(rsa_public_key, rsa_private_key):
    """CVI-9: JWT with enc must decode through the JWE path with equal claims."""
    payload = {"sub": "jwt-jwe-user", "scope": "read:secret"}
    processor = JsonWebToken(["RSA-OAEP", "A256GCM"])
    token = processor.encode(
        {"alg": "RSA-OAEP", "enc": "A256GCM"},
        payload,
        rsa_public_key,
    )
    claims = processor.decode(token, rsa_private_key)
    assert token.count(b".") == 4
    assert dict(claims) == payload


def test_decoded_claims_header_matches_protected_serialization():
    """CVI-10: decoded claims header must match protected compact header values."""
    key = OctKey.import_key(SYMMETRIC_SECRET, {"kty": "oct", "kid": ORACLE_KID_BETA})
    token = JsonWebToken(["HS256"]).encode(
        {"alg": "HS256", "kid": ORACLE_KID_BETA},
        {"sub": "header-check"},
        key,
    )
    claims = JsonWebToken(["HS256"]).decode(token, key)
    assert claims.header["alg"] == "HS256"
    assert claims.header["kid"] == ORACLE_KID_BETA
    assert claims.header["typ"] == "JWT"


# --- Seam: state consistency ---


def test_keyset_json_import_find_preserves_kid():
    """Seam: state consistency between KeySet export, import_key_set, and find_by_kid."""
    key = OctKey.generate_key(256, options={"kid": "set-roundtrip"}, is_private=True)
    key_set = KeySet([key])
    imported = JsonWebKey.import_key_set(key_set.as_json())
    found = imported.find_by_kid("set-roundtrip")
    assert found["kid"] == "set-roundtrip"
    assert found["kty"] == "oct"


def test_preconfigured_jwt_encode_decode_typ_and_claims():
    """Seam: state consistency between jwt.encode header defaults and jwt.decode claims."""
    token = jwt.encode({"alg": "HS256"}, {"sub": "preconfigured-user"}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    claims.validate(now=1_700_000_000)
    assert claims.header["typ"] == "JWT"
    assert claims["sub"] == "preconfigured-user"


def test_rsa_jws_private_sign_public_verify_payload(rsa_private_key, rsa_public_key):
    """Seam: protocol handoff between RSA private signing and public verification keys."""
    jws = JsonWebSignature()
    signed = jws.serialize({"alg": "RS256"}, PAYLOAD_ALPHA, rsa_private_key)
    verified = jws.deserialize(signed, rsa_public_key)
    assert verified["payload"] == PAYLOAD_ALPHA
    assert verified["header"]["alg"] == "RS256"


def test_jws_bad_signature_exposes_partial_result(oct_key_256):
    """Seam: error propagation from verification failure to BadSignatureError.result."""
    jws = JsonWebSignature()
    signed = jws.serialize({"alg": "HS256"}, PAYLOAD_ALPHA, oct_key_256)
    wrong_key = OctKey.generate_key(256, is_private=True)
    with pytest.raises(BadSignatureError) as exc:
        jws.deserialize(signed, wrong_key)
    assert exc.value.result["payload"] == PAYLOAD_ALPHA


def test_jwe_def_compression_round_trip(rsa_public_key, rsa_private_key):
    """Seam: protocol handoff between DEF compression header and decrypted payload."""
    jwe = JsonWebEncryption()
    protected = {"alg": "RSA-OAEP", "enc": "A128CBC-HS256", "zip": "DEF"}
    encrypted = jwe.serialize_compact(protected, PAYLOAD_BETA, rsa_public_key)
    decrypted = jwe.deserialize_compact(encrypted, rsa_private_key)
    assert decrypted["payload"] == PAYLOAD_BETA
    assert decrypted["header"]["zip"] == "DEF"


# --- Seam: config interaction ---


def test_jwt_datetime_claims_converted_on_encode():
    """Seam: config interaction between datetime payload values and decoded NumericDate claims."""
    moment = dt.datetime(2026, 3, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
    payload = {"exp": moment, "sub": "datetime-user"}
    token = jwt.encode({"alg": "HS256"}, payload, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    assert isinstance(claims.exp, int)
    assert claims.exp == int(moment.timestamp())
    assert claims["sub"] == "datetime-user"


def test_jwt_sensitive_payload_rejected_when_check_enabled():
    """Seam: config interaction between encode check flag and InsecureClaimError."""
    with pytest.raises(InsecureClaimError):
        jwt.encode({"alg": "HS256"}, {"password": "oracle-secret"}, SYMMETRIC_SECRET, check=True)
    token = jwt.encode(
        {"alg": "HS256"},
        {"password": "oracle-secret"},
        SYMMETRIC_SECRET,
        check=False,
    )
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    assert claims["password"] == "oracle-secret"


def test_jwt_algorithm_allowlist_blocks_disallowed_alg():
    """Seam: config interaction between JsonWebToken algorithms and encode path."""
    processor = JsonWebToken(["RS256"])
    with pytest.raises(UnsupportedAlgorithmError):
        processor.encode({"alg": "HS256"}, {"sub": "blocked"}, SYMMETRIC_SECRET)


def test_jwks_mapping_encode_decode_with_kid():
    """Seam: protocol handoff between JWKS kid selection and JWT decode key lookup."""
    private_jwks, public_jwks = make_jwks_pair()
    header = {"alg": "HS256", "kid": "jwks-alpha"}
    payload = {"sub": "jwks-user"}
    token = jwt.encode(header, payload, private_jwks)
    claims = jwt.decode(token, public_jwks)
    assert claims["sub"] == "jwks-user"
    assert claims.header["kid"] == "jwks-alpha"


def test_ec_jwt_sign_and_verify_round_trip(ec_private_key, ec_public_key):
    """Seam: protocol handoff between EC signing key and ES256 verification key."""
    payload = {"sub": "ec-user", "tier": "gold"}
    token = jwt.encode({"alg": "ES256"}, payload, ec_private_key)
    claims = jwt.decode(token, ec_public_key)
    assert claims["sub"] == "ec-user"
    assert claims["tier"] == "gold"


# --- Seam: lifecycle / multi-step composition ---


def test_jws_general_json_multiple_signatures_verify():
    """Seam: protocol handoff between general JSON signatures and callable key resolution."""
    protected = {"alg": "HS256"}
    headers = [
        {"protected": protected, "header": {"kid": "sig-a"}},
        {"protected": protected, "header": {"kid": "sig-b"}},
    ]

    def load_key(header, payload):
        assert payload == PAYLOAD_ALPHA
        return "secret-a" if header.get("kid") == "sig-a" else "secret-b"

    jws = JsonWebSignature()
    signed = jws.serialize(headers, PAYLOAD_ALPHA, load_key)
    verified = jws.deserialize(json.dumps(signed), load_key)
    assert verified["payload"] == PAYLOAD_ALPHA
    assert verified["header"][0]["kid"] == "sig-a"


def test_symmetric_jwe_dir_mode_round_trip():
    """Seam: lifecycle crossing through generate key, encrypt, and decrypt projections."""
    key = OctKey.generate_key(128, options={"kid": "dir-mode"}, is_private=True)
    jwe = JsonWebEncryption()
    encrypted = jwe.serialize_compact({"alg": "dir", "enc": "A128GCM"}, PAYLOAD_ALPHA, key)
    decrypted = jwe.deserialize_compact(encrypted, key)
    assert decrypted["payload"] == PAYLOAD_ALPHA
    assert decrypted["header"]["alg"] == "dir"


def test_sign_then_encrypt_then_decrypt_then_verify():
    """Seam: state consistency across JWS signing, JWE wrapping, and nested deserialization."""
    enc_key = OctKey.generate_key(128, is_private=True)
    jws = JsonWebSignature()
    jwe = JsonWebEncryption()
    signed = jws.serialize({"alg": "HS256"}, PAYLOAD_BETA, SYMMETRIC_SECRET)
    encrypted = jwe.serialize_compact({"alg": "dir", "enc": "A128GCM"}, signed, enc_key)
    decrypted = jwe.deserialize_compact(encrypted, enc_key)
    verified = jws.deserialize(decrypted["payload"], SYMMETRIC_SECRET)
    assert verified["payload"] == PAYLOAD_BETA


def test_custom_claims_class_receives_options_and_params():
    """Seam: protocol handoff between decode claims_cls and BaseClaims options projection."""

    class CustomClaims(BaseClaims):
        pass

    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, {"sub": "custom-user"}, SYMMETRIC_SECRET)
    claims = JsonWebToken(["HS256"]).decode(
        token,
        SYMMETRIC_SECRET,
        claims_cls=CustomClaims,
        claims_options={"sub": {"value": "custom-user"}},
        claims_params={"tenant": "oracle-tenant"},
    )
    assert isinstance(claims, CustomClaims)
    assert claims.options["sub"]["value"] == "custom-user"
    assert claims.params["tenant"] == "oracle-tenant"
    assert claims["sub"] == "custom-user"


def test_jwe_json_ignores_extra_top_level_members(oct_key_128):
    """Seam: state consistency when JSON JWE carries ignored additional members."""
    jwe = JsonWebEncryption()
    header = {"protected": {"alg": "dir", "enc": "A128GCM"}}
    encrypted = jwe.serialize_json(header, PAYLOAD_ALPHA, oct_key_128)
    encrypted["ignored_member"] = "ignored-value"
    decrypted = jwe.deserialize_json(encrypted, oct_key_128)
    assert decrypted["payload"] == PAYLOAD_ALPHA


def test_jwe_unrestricted_private_headers_allow_custom_fields(okp_x25519_key):
    """Seam: config interaction between unrestricted private headers and round-trip payload."""
    jwe = JsonWebEncryption()
    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM", "custom": "allowed"}
    encrypted = jwe.serialize_compact(protected, PAYLOAD_BETA, okp_x25519_key)
    decrypted = jwe.deserialize_compact(encrypted, okp_x25519_key)
    assert decrypted["payload"] == PAYLOAD_BETA


def test_jwt_remote_jku_header_observable_without_fetch(oct_key_256):
    """Seam: state consistency for remote header metadata without network lookup."""
    token = JsonWebToken(["HS256"]).encode(
        {"alg": "HS256", "jku": "https://keys.example.test/jwks.json"},
        {"sub": "local-only"},
        oct_key_256,
    )
    claims = JsonWebToken(["HS256"]).decode(token, oct_key_256)
    assert claims["sub"] == "local-only"
    assert claims.header["jku"] == "https://keys.example.test/jwks.json"


def test_subprocess_symmetric_jws_round_trip():
    """Seam: lifecycle crossing through subprocess import and JWS round trip."""
    code = (
        "from authlib.jose import JsonWebSignature; "
        "jws=JsonWebSignature(); "
        "s=jws.serialize({'alg':'HS256'}, b'subprocess-jws', 'subprocess-secret'); "
        "assert jws.deserialize(s, 'subprocess-secret')['payload'] == b'subprocess-jws'"
    )
    proc = run_python_snippet(code)
    assert proc.returncode == 0


def test_subprocess_symmetric_jwe_round_trip():
    """Seam: lifecycle crossing through subprocess import and JWE round trip."""
    code = (
        "from authlib.jose import JsonWebEncryption, OctKey; "
        "key=OctKey.generate_key(128, is_private=True); "
        "jwe=JsonWebEncryption(); "
        "s=jwe.serialize_compact({'alg':'dir','enc':'A128GCM'}, b'subprocess-jwe', key); "
        "assert jwe.deserialize_compact(s, key)['payload'] == b'subprocess-jwe'"
    )
    proc = run_python_snippet(code)
    assert proc.returncode == 0
