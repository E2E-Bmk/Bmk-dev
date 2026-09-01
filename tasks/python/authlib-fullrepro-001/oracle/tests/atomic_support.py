from __future__ import annotations

import copy


PAYLOAD = b"synthetic-authlib-v2-atomic-payload-81f3"


def oct_key(kid, *, use="sig", alg="HS256", material=None):
    from authlib.jose import OctKey

    raw = material or ("material-" + kid).encode()
    options = {"kid": kid}
    if use is not None:
        options["use"] = use
    if alg is not None:
        options["alg"] = alg
    return OctKey.import_key(raw, options=options)


def rsa_pair(kid, *, use="sig", alg="RS256"):
    from authlib.jose import RSAKey

    private = RSAKey.generate_key(
        2048,
        options={"kid": kid, "use": use, "alg": alg},
        is_private=True,
    )
    public = RSAKey.import_key(private.as_dict(is_private=False))
    return private, public


def clone(value):
    return copy.deepcopy(value)
