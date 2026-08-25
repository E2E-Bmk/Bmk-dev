from __future__ import annotations

import pytest

from tests.composition_support import PAYLOAD, clone, oct_key, rsa_pair


def test_c01_pending_rotation_is_invisible_until_commit_then_becomes_default():
    from authlib.jose import JsonWebToken, KeySet

    old = oct_key("rotation-old")
    new = oct_key("rotation-new")
    ring = KeySet([old])
    ring.stage(new)
    api = JsonWebToken(["HS256"])
    before = api.encode({"alg": "HS256"}, {"seq": 1}, ring)
    assert api.decode(before, ring).header["kid"] == "rotation-old"
    ring.commit()
    after = api.encode({"alg": "HS256"}, {"seq": 2}, ring)
    assert api.decode(after, ring).header["kid"] == "rotation-new"
    assert api.decode(before, ring)["seq"] == 1


def test_c02_failed_rotation_rolls_back_then_clean_retry_changes_all_public_views():
    from authlib.jose import JsonWebToken, KeySet

    original = oct_key("retry-base")
    ring = KeySet([original])
    ring.stage(oct_key("retry-base"))
    with pytest.raises(ValueError):
        ring.commit()
    assert ring.pending == ()
    assert ring.revision == 0
    assert ring.snapshot()["active"]["sig:HS256"] == "retry-base"

    replacement = oct_key("retry-next")
    ring.stage(replacement)
    assert ring.commit() == 1
    exported_ids = [item["kid"] for item in ring.as_dict()["keys"]]
    assert exported_ids == ["retry-base", "retry-next"]
    token = JsonWebToken(["HS256"]).encode(
        {"alg": "HS256"}, {"state": "recovered"}, ring
    )
    assert JsonWebToken(["HS256"]).decode(token, ring).header["kid"] == "retry-next"


def test_c03_jwks_export_import_preserves_rotation_order_and_default_selection():
    from authlib.jose import JsonWebKey, JsonWebToken, KeySet

    ring = KeySet([oct_key("export-old")])
    ring.stage(oct_key("export-new"))
    ring.commit()
    restored = JsonWebKey.import_key_set(ring.as_json())
    assert [key.kid for key in restored.keys] == ["export-old", "export-new"]
    assert restored.find_by_kid(None, use="sig", alg="HS256").kid == "export-new"
    api = JsonWebToken(["HS256"])
    token = api.encode({"alg": "HS256"}, {"view": "restored"}, restored)
    assert api.decode(token, restored).header["kid"] == "export-new"


def test_c04_canonical_protected_header_agrees_across_compact_and_json_jws():
    from authlib.jose import JsonWebSignature

    key = oct_key("canon-c04")
    api = JsonWebSignature(["HS256"])
    first = {"cty": "text/plain", "kid": "canon-c04", "alg": "HS256"}
    second = {"alg": "HS256", "kid": "canon-c04", "cty": "text/plain"}
    compact_a = api.serialize_compact(first, PAYLOAD, key)
    compact_b = api.serialize_compact(second, PAYLOAD, key)
    flat_a = api.serialize_json({"protected": first}, PAYLOAD, key)
    flat_b = api.serialize_json({"protected": second}, PAYLOAD, key)
    assert compact_a == compact_b
    assert flat_a["protected"] == flat_b["protected"] == compact_a.split(b".")[0].decode()
    assert flat_a["signature"] == flat_b["signature"]
    assert api.deserialize_json(flat_a, key).payload == PAYLOAD


def test_c05_jwt_is_reproducible_across_header_permutations_without_input_mutation():
    from authlib.jose import JsonWebToken, KeySet

    ring = KeySet([oct_key("det-old"), oct_key("det-new")])
    api = JsonWebToken(["HS256"])
    left_header = {"cty": "application/json", "alg": "HS256"}
    right_header = {"alg": "HS256", "cty": "application/json"}
    left_before, right_before = clone(left_header), clone(right_header)
    payload = {"sub": "stable", "counter": 17}
    left = api.encode(left_header, payload, ring)
    right = api.encode(right_header, payload, ring)
    assert left == right
    assert left_header == left_before and right_header == right_before
    decoded = api.decode(left, ring)
    assert decoded.header["kid"] == "det-new"
    assert decoded["counter"] == 17


def test_c06_strict_recipient_failure_does_not_consume_or_mutate_jwe_object():
    from authlib.jose import JsonWebEncryption
    from authlib.jose.errors import KeyMismatchError

    first = oct_key("strict-one", use="enc", alg="A128KW", material=b"5" * 16)
    second = oct_key("strict-two", use="enc", alg="A128KW", material=b"6" * 16)
    api = JsonWebEncryption(["A128KW", "A128GCM"])
    header = {
        "protected": {"enc": "A128GCM", "alg": "A128KW"},
        "recipients": [
            {"header": {"kid": "strict-one"}},
            {"header": {"kid": "strict-two"}},
        ],
    }
    obj = api.serialize_json(header, PAYLOAD, [first, second])
    frozen = clone(obj)
    with pytest.raises(KeyMismatchError):
        api.deserialize_json(obj, ("absent", second))
    assert obj == frozen
    assert api.deserialize_json(obj, ("strict-two", second))["payload"] == PAYLOAD
    assert obj == frozen


def test_c07_falsy_claim_roundtrip_validates_then_can_be_repaired_and_revalidated():
    from authlib.jose import JsonWebToken
    from authlib.jose.errors import InvalidClaimError

    key = oct_key("claims-c07")
    api = JsonWebToken(["HS256"])
    token = api.encode(
        {"alg": "HS256"},
        {"sub": "", "quota": 0},
        key,
    )
    claims = api.decode(
        token,
        key,
        claims_options={
            "sub": {"essential": True},
            "quota": {"essential": True, "value": 0},
        },
    )
    claims.validate(now=500)
    claims.options["quota"]["value"] = 1
    with pytest.raises(InvalidClaimError):
        claims.validate(now=500)
    claims["quota"] = 1
    claims.validate(now=500)


def test_c08_rotated_signing_key_composes_with_outer_encryption_and_old_verification():
    from authlib.jose import JsonWebEncryption, JsonWebToken, KeySet

    old = oct_key("nested-old")
    new = oct_key("nested-new")
    ring = KeySet([old])
    jwt_api = JsonWebToken(["HS256"])
    old_token = jwt_api.encode({"alg": "HS256"}, {"generation": 0}, ring)
    ring.stage(new)
    ring.commit()
    new_token = jwt_api.encode({"alg": "HS256"}, {"generation": 1}, ring)

    wrapping = oct_key("outer", use="enc", alg="dir", material=b"7" * 16)
    jwe = JsonWebEncryption(["dir", "A128GCM"])
    envelope = jwe.serialize_compact(
        {"alg": "dir", "enc": "A128GCM", "cty": "JWT"}, new_token, wrapping
    )
    restored = jwe.deserialize_compact(envelope, wrapping)["payload"]
    assert jwt_api.decode(restored, ring)["generation"] == 1
    assert jwt_api.decode(old_token, ring)["generation"] == 0


def test_c09_rsa_private_signs_and_public_projection_verifies_compact_jws():
    from authlib.jose import JsonWebSignature

    private, public = rsa_pair("rsa-c09")
    api = JsonWebSignature(["RS256"])
    token = api.serialize_compact({"alg": "RS256", "kid": "rsa-c09"}, PAYLOAD, private)
    result = api.deserialize_compact(token, public)
    assert result.payload == PAYLOAD
    assert result.header["kid"] == "rsa-c09"


def test_c10_rsa_oaep_public_encrypts_and_private_decrypts_compact_jwe():
    from authlib.jose import JsonWebEncryption

    private, public = rsa_pair("rsa-c10", use="enc", alg="RSA-OAEP-256")
    api = JsonWebEncryption(["RSA-OAEP-256", "A256GCM"])
    token = api.serialize_compact(
        {"alg": "RSA-OAEP-256", "enc": "A256GCM", "kid": "rsa-c10"},
        PAYLOAD,
        public,
    )
    assert api.deserialize_compact(token, private)["payload"] == PAYLOAD


def test_c11_general_json_jws_is_canonical_across_protected_header_permutations():
    from authlib.jose import JsonWebSignature

    first = oct_key("general-one")
    second = oct_key("general-two")
    by_kid = {first.kid: first, second.kid: second}
    seen = []

    def loader(header, payload):
        seen.append((header["kid"], payload))
        return by_kid[header["kid"]]

    api = JsonWebSignature(["HS256"])
    left = api.serialize_json(
        [
            {
                "protected": {
                    "typ": "JOSE",
                    "alg": "HS256",
                    "kid": "general-one",
                }
            },
            {
                "protected": {
                    "cty": "application/octet-stream",
                    "kid": "general-two",
                    "alg": "HS256",
                }
            },
        ],
        PAYLOAD,
        loader,
    )
    right = api.serialize_json(
        [
            {
                "protected": {
                    "kid": "general-one",
                    "alg": "HS256",
                    "typ": "JOSE",
                }
            },
            {
                "protected": {
                    "alg": "HS256",
                    "kid": "general-two",
                    "cty": "application/octet-stream",
                }
            },
        ],
        PAYLOAD,
        loader,
    )
    assert [item["protected"] for item in left["signatures"]] == [
        item["protected"] for item in right["signatures"]
    ]
    assert [item["signature"] for item in left["signatures"]] == [
        item["signature"] for item in right["signatures"]
    ]
    result = api.deserialize_json(right, loader)
    assert result.payload == PAYLOAD
    assert [header["kid"] for header in result.header] == ["general-one", "general-two"]
    assert {item[0] for item in seen} == {"general-one", "general-two"}


def test_c12_each_aes_keywrap_recipient_decrypts_same_general_jwe_payload():
    from authlib.jose import JsonWebEncryption
    from authlib.jose.errors import KeyMismatchError

    first = oct_key("wrap-one", use="enc", alg="A128KW", material=b"8" * 16)
    second = oct_key("wrap-two", use="enc", alg="A128KW", material=b"9" * 16)
    api = JsonWebEncryption(["A128KW", "A128GCM"])
    obj = api.serialize_json(
        {
            "protected": {"alg": "A128KW", "enc": "A128GCM"},
            "recipients": [
                {"header": {"kid": "wrap-one"}},
                {"header": {"kid": "wrap-two"}},
            ],
        },
        PAYLOAD,
        [first, second],
    )
    frozen = clone(obj)
    with pytest.raises(KeyMismatchError):
        api.deserialize_json(obj, ("missing-recipient", second))
    assert obj == frozen
    assert api.deserialize_json(obj, ("wrap-one", first))["payload"] == PAYLOAD
    assert api.deserialize_json(obj, ("wrap-two", second))["payload"] == PAYLOAD
    assert obj == frozen


def test_c13_rsa_encrypted_jwt_roundtrips_as_typed_claims():
    from authlib.jose import JsonWebToken, JWTClaims

    private, public = rsa_pair("jwt-c13", use="enc", alg="RSA-OAEP")
    api = JsonWebToken(["RSA-OAEP", "A128GCM"])
    token = api.encode(
        {"alg": "RSA-OAEP", "enc": "A128GCM", "kid": "jwt-c13"},
        {"sub": "encrypted-subject", "scope": ["read", "write"]},
        public,
    )
    assert token.count(b".") == 4
    claims = api.decode(token, private)
    assert isinstance(claims, JWTClaims)
    assert claims["scope"] == ["read", "write"]


def test_c14_signed_compact_bytes_survive_outer_direct_jwe_roundtrip():
    from authlib.jose import JsonWebEncryption, JsonWebSignature

    signing = oct_key("nested-c14")
    wrapping = oct_key("outer-c14", use="enc", alg="dir", material=b"A" * 16)
    jws = JsonWebSignature(["HS256"])
    jwe = JsonWebEncryption(["dir", "A128GCM"])
    signed = jws.serialize_compact({"alg": "HS256"}, PAYLOAD, signing)
    encrypted = jwe.serialize_compact(
        {"alg": "dir", "enc": "A128GCM", "cty": "JOSE"}, signed, wrapping
    )
    recovered = jwe.deserialize_compact(encrypted, wrapping)["payload"]
    assert recovered == signed
    assert jws.deserialize_compact(recovered, signing).payload == PAYLOAD


def test_c15_custom_claims_receives_header_options_params_and_validator_context():
    from authlib.jose import JWTClaims, JsonWebToken

    class TenantClaims(JWTClaims):
        pass

    calls = []

    def validate_tenant(claims, value):
        calls.append((value, claims.params["tenant"], claims.header["kid"]))
        return value == claims.params["tenant"]

    key = oct_key("claims-c15")
    api = JsonWebToken(["HS256"])
    token = api.encode({"alg": "HS256"}, {"tenant": "north"}, key)
    claims = api.decode(
        token,
        key,
        claims_cls=TenantClaims,
        claims_options={"tenant": {"validate": validate_tenant}},
        claims_params={"tenant": "north"},
    )
    claims.validate(now=900)
    assert calls == [("north", "north", "claims-c15")]


def test_c16_rsa_jwks_rotation_selects_newest_default_and_verifies_after_export():
    from authlib.jose import JsonWebKey, JsonWebToken, KeySet

    first_private, first_public = rsa_pair("jwks-rsa-one")
    second_private, second_public = rsa_pair("jwks-rsa-two")
    exported = KeySet([first_public, second_public]).as_json()
    restored = JsonWebKey.import_key_set(exported)
    api = JsonWebToken(["RS256"])
    signing_ring = KeySet([first_private])
    signing_ring.stage(second_private)
    signing_ring.commit()
    token = api.encode(
        {"alg": "RS256"},
        {"sub": "jwks-subject"},
        signing_ring,
    )
    claims = api.decode(token, restored)
    assert claims["sub"] == "jwks-subject"
    assert claims.header["kid"] == "jwks-rsa-two"
