from __future__ import annotations

import datetime

import pytest

from tests.atomic_support import PAYLOAD, clone, oct_key, rsa_pair


def test_a01_keyset_none_selects_newest_committed_eligible_key():
    from authlib.jose import KeySet

    old = oct_key("sig-old")
    new = oct_key("sig-new")
    ring = KeySet([old, new])
    assert ring.find_by_kid(None, use="sig", alg="HS256") is new


def test_a02_keyset_filters_are_exact_and_do_not_treat_missing_metadata_as_wildcards():
    from authlib.jose import KeySet

    unspecified = oct_key("shared", use=None, alg=None)
    explicit = oct_key("shared", use="sig", alg="HS256")
    ring = KeySet([unspecified, explicit])
    assert ring.find_by_kid("shared", use="sig", alg="HS256") is explicit


def test_a03_staged_key_is_pending_but_invisible_to_committed_views():
    from authlib.jose import KeySet

    first = oct_key("visible")
    pending = oct_key("pending")
    ring = KeySet([first])
    assert ring.stage(pending) is pending
    assert ring.pending == (pending,)
    assert [item["kid"] for item in ring.as_dict()["keys"]] == ["visible"]
    with pytest.raises(ValueError):
        ring.find_by_kid("pending")


def test_a04_commit_publishes_all_pending_keys_and_advances_one_revision():
    from authlib.jose import KeySet

    ring = KeySet([oct_key("base")])
    ring.stage(oct_key("next-a"))
    ring.stage(oct_key("next-b", use="enc", alg="A128KW"))
    assert ring.commit() == 1
    assert ring.revision == 1
    assert ring.pending == ()
    assert [key.kid for key in ring.keys] == ["base", "next-a", "next-b"]


def test_a05_failed_duplicate_commit_is_atomic_and_clears_pending_batch():
    from authlib.jose import KeySet

    original = oct_key("stable")
    ring = KeySet([original])
    ring.stage(oct_key("stable"))
    before = ring.as_dict()
    with pytest.raises(ValueError):
        ring.commit()
    assert ring.as_dict() == before
    assert ring.revision == 0
    assert ring.pending == ()
    assert ring.find_by_kid("stable") is original


def test_a06_rollback_reports_change_once_and_is_idempotent():
    from authlib.jose import KeySet

    ring = KeySet([oct_key("base")])
    ring.stage(oct_key("discard"))
    assert ring.rollback() is True
    assert ring.rollback() is False
    assert ring.pending == ()
    assert ring.revision == 0


def test_a07_snapshot_is_detached_and_exposes_revision_and_active_lanes():
    from authlib.jose import KeySet

    ring = KeySet([oct_key("s1")])
    ring.stage(oct_key("s2"))
    ring.commit()
    snapshot = ring.snapshot()
    assert snapshot["revision"] == 1
    assert snapshot["active"]["sig:HS256"] == "s2"
    snapshot["keys"][0]["kid"] = "tampered"
    snapshot["active"]["sig:HS256"] = "tampered"
    assert ring.keys[0].kid == "s1"
    assert ring.snapshot()["active"]["sig:HS256"] == "s2"


def test_a08_jws_compact_canonicalizes_equivalent_protected_mappings():
    from authlib.jose import JsonWebSignature

    key = oct_key("canon")
    jws = JsonWebSignature(["HS256"])
    first = {"typ": "JOSE", "kid": "canon", "alg": "HS256"}
    second = {"alg": "HS256", "kid": "canon", "typ": "JOSE"}
    assert jws.serialize_compact(first, PAYLOAD, key) == jws.serialize_compact(
        second, PAYLOAD, key
    )


def test_a09_jwe_compact_canonicalizes_equivalent_protected_mappings():
    from authlib.jose import JsonWebEncryption

    key = oct_key("enc", use="enc", alg="dir", material=b"0" * 16)
    jwe = JsonWebEncryption(["dir", "A128GCM"])
    first = {"typ": "JOSE", "enc": "A128GCM", "alg": "dir"}
    second = {"alg": "dir", "enc": "A128GCM", "typ": "JOSE"}
    left = jwe.serialize_compact(first, PAYLOAD, key)
    right = jwe.serialize_compact(second, PAYLOAD, key)
    assert left.split(b".", 1)[0] == right.split(b".", 1)[0]


def test_a10_jwt_encode_does_not_mutate_caller_header_during_defaulting_or_selection():
    from authlib.jose import JsonWebToken, KeySet

    ring = KeySet([oct_key("older"), oct_key("newer")])
    token_api = JsonWebToken(["HS256"])
    header = {"alg": "HS256"}
    before = clone(header)
    token = token_api.encode(header, {"sub": "subject-10"}, ring)
    assert header == before
    claims = token_api.decode(token, ring)
    assert claims.header["kid"] == "newer"
    assert claims.header["typ"] == "JWT"


def test_a11_jwt_encode_does_not_replace_datetime_values_in_caller_payload():
    from authlib.jose import JsonWebToken

    api = JsonWebToken(["HS256"])
    key = oct_key("date-key")
    moment = datetime.datetime(2042, 7, 8, 9, 10, 11, tzinfo=datetime.timezone.utc)
    payload = {"sub": "clock", "iat": moment}
    token = api.encode({"alg": "HS256"}, payload, key)
    assert payload["iat"] is moment
    assert isinstance(api.decode(token, key)["iat"], int)


def test_a12_jwe_tuple_kid_is_a_strict_recipient_constraint():
    from authlib.jose import JsonWebEncryption
    from authlib.jose.errors import KeyMismatchError

    first = oct_key("r-one", use="enc", alg="A128KW", material=b"1" * 16)
    second = oct_key("r-two", use="enc", alg="A128KW", material=b"2" * 16)
    jwe = JsonWebEncryption(["A128KW", "A128GCM"])
    obj = jwe.serialize_json(
        {
            "protected": {"alg": "A128KW", "enc": "A128GCM"},
            "recipients": [
                {"header": {"kid": "r-one"}},
                {"header": {"kid": "r-two"}},
            ],
        },
        PAYLOAD,
        [first, second],
    )
    with pytest.raises(KeyMismatchError):
        jwe.deserialize_json(obj, ("not-present", second))


def test_a13_essential_claim_requires_presence_not_truthiness():
    from authlib.jose import JWTClaims

    claims = JWTClaims(
        {"sub": ""},
        {"alg": "HS256"},
        options={"sub": {"essential": True}},
    )
    claims.validate(now=100)
    assert claims["sub"] == ""


def test_a14_configured_falsy_scalar_is_an_enforced_claim_value():
    from authlib.jose import JWTClaims
    from authlib.jose.errors import InvalidClaimError

    claims = JWTClaims(
        {"tier": 1},
        {"alg": "HS256"},
        options={"tier": {"value": 0}},
    )
    with pytest.raises(InvalidClaimError):
        claims.validate(now=100)


def test_a15_boolean_is_not_a_numeric_date():
    from authlib.jose import JWTClaims
    from authlib.jose.errors import InvalidClaimError

    with pytest.raises(InvalidClaimError):
        JWTClaims({"exp": False}, {"alg": "HS256"}).validate(now=0)


def test_a16_negative_or_boolean_leeway_is_rejected():
    from authlib.jose import JWTClaims

    claims = JWTClaims({"exp": 200}, {"alg": "HS256"})
    for invalid in (-1, True):
        with pytest.raises(ValueError):
            claims.validate(now=100, leeway=invalid)


def test_a17_rsa_private_export_reimports_to_same_public_projection():
    from authlib.jose import RSAKey

    private, public = rsa_pair("rsa-a17")
    restored = RSAKey.import_key(private.as_dict(is_private=True))
    assert restored.as_dict(is_private=False)["n"] == public.as_dict()["n"]
    assert restored.as_dict(is_private=False)["e"] == public.as_dict()["e"]


def test_a18_jws_bad_signature_exposes_partially_decoded_result():
    from authlib.jose import JsonWebSignature
    from authlib.jose.errors import BadSignatureError

    signer = oct_key("good")
    wrong = oct_key("wrong")
    jws = JsonWebSignature(["HS256"])
    token = jws.serialize_compact({"alg": "HS256", "kid": "good"}, PAYLOAD, signer)
    with pytest.raises(BadSignatureError) as caught:
        jws.deserialize_compact(token, wrong)
    assert caught.value.result.payload == PAYLOAD
    assert caught.value.result.header["kid"] == "good"


def test_a19_direct_jwe_rejects_multiple_json_recipients():
    from authlib.jose import JsonWebEncryption
    from authlib.jose.errors import InvalidAlgorithmForMultipleRecipientsMode

    first = oct_key("d1", use="enc", alg="dir", material=b"3" * 16)
    second = oct_key("d2", use="enc", alg="dir", material=b"4" * 16)
    jwe = JsonWebEncryption(["dir", "A128GCM"])
    with pytest.raises(InvalidAlgorithmForMultipleRecipientsMode):
        jwe.serialize_json(
            {
                "protected": {"alg": "dir", "enc": "A128GCM"},
                "recipients": [{"header": {"kid": "d1"}}, {"header": {"kid": "d2"}}],
            },
            PAYLOAD,
            [first, second],
        )


def test_a20_exact_kid_keyset_decodes_signed_jwt():
    from authlib.jose import JsonWebToken, KeySet

    first = oct_key("exact-one")
    second = oct_key("exact-two")
    ring = KeySet([first, second])
    api = JsonWebToken(["HS256"])
    token = api.encode(
        {"alg": "HS256", "kid": "exact-one"},
        {"sub": "exact-subject"},
        first,
    )
    claims = api.decode(token, ring)
    assert claims["sub"] == "exact-subject"
    assert claims.header["kid"] == "exact-one"
