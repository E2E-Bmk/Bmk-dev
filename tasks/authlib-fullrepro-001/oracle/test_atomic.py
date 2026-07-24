"""Atomic tests for authlib-fullrepro-001.

Each test verifies ONE public API entry point and ONE behavior point.
"""

from __future__ import annotations

import datetime as dt

import pytest

from authlib.jose import (
    ECKey,
    JWSHeader,
    JsonWebEncryption,
    JsonWebKey,
    JsonWebSignature,
    JsonWebToken,
    JWTClaims,
    KeySet,
    OctKey,
    RSAKey,
    errors,
    jwt,
)
from authlib.jose.errors import (
    DecodeError,
    ExpiredTokenError,
    InvalidClaimError,
    InvalidHeaderParameterNameError,
    JoseError,
    MissingAlgorithmError,
    MissingClaimError,
    MissingEncryptionAlgorithmError,
    UnsupportedAlgorithmError,
    UnsupportedCompressionAlgorithmError,
    UnsupportedEncryptionAlgorithmError,
)

from conftest import (
    ORACLE_KID_ALPHA,
    PAYLOAD_ALPHA,
    SYMMETRIC_SECRET,
    b64url_to_int,
)


# --- Key Import and Export: OctKey ---


def test_oct_key_import_preserves_base64url_k_value():
    obj = {
        "kty": "oct",
        "kid": "oct-import-7a",
        "use": "sig",
        "alg": "HS256",
        "k": "aGVsbG8tb3JhY2xlLXRlc3Q",
    }
    key = OctKey.import_key(obj)
    exported = key.as_dict()
    assert exported["k"] == obj["k"]
    assert exported["use"] == "sig"


def test_oct_key_import_empty_mapping_raises_value_error():
    with pytest.raises(ValueError):
        OctKey.import_key({})


def test_oct_key_generate_rejects_non_byte_aligned_size():
    with pytest.raises(ValueError):
        OctKey.generate_key(251)


def test_oct_key_generate_rejects_public_only_mode():
    with pytest.raises(ValueError):
        OctKey.generate_key(is_private=False)


def test_oct_key_generate_includes_kid_in_export():
    key = OctKey.generate_key(256, options={"kid": "generated-oct-1"}, is_private=True)
    exported = key.as_dict()
    assert exported["kid"] == "generated-oct-1"
    assert exported["kty"] == "oct"


# --- Key Import and Export: RSAKey ---


def test_rsa_key_import_preserves_public_modulus_and_exponent(rsa_private_key):
    source = rsa_private_key.as_dict(is_private=True)
    imported = RSAKey.import_key(source)
    exported = imported.as_dict(is_private=False)
    assert b64url_to_int(exported["n"]) == b64url_to_int(source["n"])
    assert b64url_to_int(exported["e"]) == b64url_to_int(source["e"])


def test_rsa_key_import_missing_required_fields_raises_value_error():
    with pytest.raises(ValueError):
        RSAKey.import_key({"kty": "RSA"})


def test_rsa_key_import_partial_crt_fields_raises_value_error(rsa_private_key):
    source = rsa_private_key.as_dict(is_private=True)
    partial = {
        "kty": "RSA",
        "n": source["n"],
        "e": source["e"],
        "d": source["d"],
        "p": source["p"],
    }
    with pytest.raises(ValueError):
        RSAKey.import_key(partial)


def test_rsa_key_generate_rejects_invalid_key_size():
    with pytest.raises(ValueError):
        RSAKey.generate_key(256)


def test_rsa_public_key_private_export_raises_value_error(rsa_public_key):
    with pytest.raises(ValueError):
        rsa_public_key.as_dict(is_private=True)


# --- Key Import and Export: ECKey and JsonWebKey ---


def test_ec_key_import_preserves_curve_coordinates(ec_private_key):
    source = ec_private_key.as_dict(is_private=True)
    imported = ECKey.import_key(source)
    exported = imported.as_dict(is_private=False)
    assert exported["crv"] == source["crv"]
    assert exported["x"] == source["x"]
    assert exported["y"] == source["y"]


def test_json_web_key_import_dispatches_oct_key_type():
    key = JsonWebKey.import_key(SYMMETRIC_SECRET, {"kty": "oct", "kid": "dispatch-oct"})
    exported = key.as_dict()
    assert exported["kty"] == "oct"
    assert exported["kid"] == "dispatch-oct"


def test_json_web_key_import_key_set_from_keys_list(oct_key_256):
    raw = {"keys": [oct_key_256.as_dict(is_private=True)]}
    key_set = JsonWebKey.import_key_set(raw)
    found = key_set.find_by_kid(ORACLE_KID_ALPHA)
    assert found["kid"] == ORACLE_KID_ALPHA


def test_key_set_find_by_kid_returns_matching_key(oct_key_256):
    key_set = KeySet([oct_key_256])
    found = key_set.find_by_kid(ORACLE_KID_ALPHA)
    assert found["kid"] == ORACLE_KID_ALPHA


def test_key_set_find_by_kid_raises_when_no_match(oct_key_256):
    key_set = KeySet([oct_key_256])
    with pytest.raises(ValueError):
        key_set.find_by_kid("missing-kid-404")


def test_key_thumbprint_is_deterministic_base64url_sha256(oct_key_256):
    first = oct_key_256.thumbprint()
    second = oct_key_256.thumbprint()
    assert first == second
    # SHA-256 digest is 32 bytes -> 43 unpadded base64url characters.
    assert len(first) == 43
    assert "=" not in first


# --- JSON Web Signature Processing: headers and policy ---


def test_jws_header_protected_values_take_precedence_over_unprotected():
    header = JWSHeader({"alg": "HS256", "kid": "protected-kid"}, {"kid": "unprotected-kid"})
    assert header["kid"] == "protected-kid"
    assert header.protected["kid"] == "protected-kid"
    assert header.header["kid"] == "unprotected-kid"


def test_jws_private_header_restriction_raises_invalid_header_error():
    jws = JsonWebSignature(private_headers=[])
    with pytest.raises(InvalidHeaderParameterNameError):
        jws.serialize({"alg": "HS256", "custom_hdr": True}, PAYLOAD_ALPHA, SYMMETRIC_SECRET)


def test_jws_missing_alg_raises_missing_algorithm_error():
    jws = JsonWebSignature()
    with pytest.raises(MissingAlgorithmError):
        jws.serialize_compact({}, PAYLOAD_ALPHA, SYMMETRIC_SECRET)


def test_jws_disallowed_alg_raises_unsupported_algorithm_error():
    jws = JsonWebSignature(algorithms=["HS256"])
    with pytest.raises(UnsupportedAlgorithmError):
        jws.serialize({"alg": "HS512"}, PAYLOAD_ALPHA, SYMMETRIC_SECRET)


# --- JSON Web Encryption Processing: headers and policy ---


def test_jwe_missing_alg_raises_missing_algorithm_error(rsa_public_key):
    jwe = JsonWebEncryption()
    with pytest.raises(MissingAlgorithmError):
        jwe.serialize_compact({}, PAYLOAD_ALPHA, rsa_public_key)


def test_jwe_unsupported_alg_raises_unsupported_algorithm_error(rsa_public_key):
    jwe = JsonWebEncryption()
    with pytest.raises(UnsupportedAlgorithmError):
        jwe.serialize_compact({"alg": "invalid-alg-name"}, PAYLOAD_ALPHA, rsa_public_key)


def test_jwe_missing_enc_raises_missing_encryption_algorithm_error(rsa_public_key):
    jwe = JsonWebEncryption()
    with pytest.raises(MissingEncryptionAlgorithmError):
        jwe.serialize_compact({"alg": "RSA-OAEP"}, PAYLOAD_ALPHA, rsa_public_key)


def test_jwe_unsupported_enc_raises_unsupported_encryption_algorithm_error(rsa_public_key):
    jwe = JsonWebEncryption()
    with pytest.raises(UnsupportedEncryptionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "invalid-enc-name"},
            PAYLOAD_ALPHA,
            rsa_public_key,
        )


def test_jwe_unsupported_zip_raises_unsupported_compression_algorithm_error(rsa_public_key):
    jwe = JsonWebEncryption()
    with pytest.raises(UnsupportedCompressionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "A256GCM", "zip": "invalid-zip"},
            PAYLOAD_ALPHA,
            rsa_public_key,
        )


def test_jwe_parse_json_rejects_non_object_json():
    with pytest.raises(DecodeError):
        JsonWebEncryption.parse_json("[]")


def test_jwe_deserialize_compact_wrong_segment_count_raises_decode_error():
    jwe = JsonWebEncryption()
    with pytest.raises(DecodeError):
        jwe.deserialize_compact("a.b.c", None)


# --- JSON Web Token Encoding and Decoding ---


def test_jwt_decode_wrong_segment_count_raises_decode_error():
    token = JsonWebToken(["HS256"])
    with pytest.raises(DecodeError):
        token.decode(b"only-one-segment", SYMMETRIC_SECRET)


# --- Claims Validation ---


def test_jwt_claims_registered_attribute_returns_value():
    claims = JWTClaims({"iss": "issuer-alpha"}, {"alg": "HS256"})
    assert claims.iss == "issuer-alpha"


def test_jwt_claims_unknown_attribute_raises_attribute_error():
    claims = JWTClaims({"iss": "issuer-alpha"}, {"alg": "HS256"})
    with pytest.raises(AttributeError):
        claims.nonexistent_claim_name


def test_jwt_claims_validate_missing_essential_claim_raises_missing_claim_error():
    token = jwt.encode({"alg": "HS256"}, {"iss": "issuer-alpha"}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET, claims_options={"sub": {"essential": True}})
    with pytest.raises(MissingClaimError):
        claims.validate(now=1_700_000_000)


def test_jwt_claims_validate_wrong_value_raises_invalid_claim_error():
    token = jwt.encode({"alg": "HS256"}, {"iss": "issuer-alpha"}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET, claims_options={"iss": {"value": "other-issuer"}})
    with pytest.raises(InvalidClaimError):
        claims.validate(now=1_700_000_000)


def test_jwt_claims_validate_expired_token_raises_expired_token_error():
    token = jwt.encode({"alg": "HS256"}, {"exp": 1_600_000_000}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    with pytest.raises(ExpiredTokenError):
        claims.validate(now=1_700_000_000)


def test_jwt_claims_validate_non_numeric_exp_raises_invalid_claim_error():
    token = jwt.encode({"alg": "HS256"}, {"exp": "not-a-number"}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    with pytest.raises(InvalidClaimError):
        claims.validate(now=1_700_000_000)


def test_jwt_claims_validate_audience_list_membership():
    token = jwt.encode({"alg": "HS256"}, {"aud": ["service-a", "service-b"]}, SYMMETRIC_SECRET)
    claims = jwt.decode(
        token,
        SYMMETRIC_SECRET,
        claims_options={"aud": {"essential": True, "value": "service-b"}},
    )
    claims.validate(now=1_700_000_000)
    assert claims.aud == ["service-a", "service-b"]


def test_jwt_claims_validate_nbf_in_future_raises_invalid_token_error():
    token = jwt.encode({"alg": "HS256"}, {"nbf": 9_999_999_999}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    with pytest.raises(errors.InvalidTokenError):
        claims.validate(now=1_700_000_000)


def test_jwt_claims_validate_iat_in_future_raises_invalid_token_error():
    future = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=120)
    token = jwt.encode({"alg": "HS256"}, {"iat": future}, SYMMETRIC_SECRET)
    claims = jwt.decode(token, SYMMETRIC_SECRET)
    with pytest.raises(errors.InvalidTokenError):
        claims.validate()


# --- Error Semantics ---


def test_decode_error_inherits_from_jose_error_and_exposes_error_code():
    assert issubclass(DecodeError, JoseError)
    assert DecodeError.error == "decode_error"


def test_jose_error_subclass_is_raised_for_malformed_jwt_segments():
    with pytest.raises(DecodeError):
        JsonWebToken(["HS256"]).decode(b"bad.token", SYMMETRIC_SECRET)
