# Authlib Specification

## Product Overview

Authlib provides a Python implementation of Javascript Object Signing and Encryption. This specification covers the `authlib.jose` package for JSON Web Key, JSON Web Signature, JSON Web Encryption, JSON Web Token, and related JSON Web Algorithm behavior. The package exposes high-level objects for importing keys, signing payloads, encrypting payloads, decoding tokens, and validating claims.

The `authlib.jose` package is deprecated in favor of the separate `joserfc` package, but the APIs described here remain part of the supported Authlib JOSE interface until the package removal boundary.

## Scope

The covered feature areas are:

- Public JOSE imports from `authlib.jose` and public exception imports from `authlib.jose.errors`.
- JSON Web Key import, generation, export, key set lookup, public/private projections, operation checks, and thumbprints.
- JSON Web Signature compact serialization and JSON serialization, including flattened and general JSON forms.
- JSON Web Encryption compact serialization and JSON serialization, including protected, shared unprotected, per-recipient, additional authenticated data, compression, and multiple recipients.
- JSON Web Token encode and decode over JWS or JWE compact serialization, key selection, sensitive-claim checks, and claims validation.
- Header validation, claim validation, and public exception behavior for JOSE operations.

## Installable Surface

The package is imported as `authlib`. The top-level package exposes metadata through `__version__`, `__homepage__`, `__author__`, and `__license__`. `__version__` must be a non-empty string, `__homepage__` must be `https://authlib.org`, and `__license__` must be `BSD-3-Clause`. The JOSE interface is imported from `authlib.jose`. Importing `authlib.jose` emits an `AuthlibDeprecationWarning`. The top-level JOSE exports are `JoseError`, `JsonWebSignature`, `JWSAlgorithm`, `JWSHeader`, `JWSObject`, `JsonWebEncryption`, `JWEAlgorithm`, `JWEEncAlgorithm`, `JWEZipAlgorithm`, `JsonWebKey`, `Key`, `KeySet`, `OctKey`, `RSAKey`, `ECKey`, `OKPKey`, `JsonWebToken`, `BaseClaims`, `JWTClaims`, and `jwt`.

Public JOSE exception classes are exposed from `authlib.jose.errors`. They include `DecodeError`, `MissingAlgorithmError`, `UnsupportedAlgorithmError`, `BadSignatureError`, `InvalidHeaderParameterNameError`, `InvalidCritHeaderParameterNameError`, `InvalidAlgorithmForMultipleRecipientsMode`, `KeyMismatchError`, `MissingEncryptionAlgorithmError`, `UnsupportedEncryptionAlgorithmError`, `UnsupportedCompressionAlgorithmError`, `InvalidUseError`, `InvalidClaimError`, `MissingClaimError`, `InsecureClaimError`, `ExpiredTokenError`, and `InvalidTokenError`.

The preconfigured `jwt` object is an instance of `JsonWebToken` that supports `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES256K`, `ES384`, `ES512`, `PS256`, `PS384`, `PS512`, and `EdDSA`.

## Public API

`JsonWebKey.generate_key(kty, crv_or_size, options=None, is_private=False)` returns a key object for `oct`, `RSA`, `EC`, or `OKP`. It raises `KeyError` when `kty` is not registered and raises `ValueError` when the selected key type rejects the requested size, curve, or privacy mode.

`JsonWebKey.import_key(raw, options=None)` returns an `OctKey`, `RSAKey`, `ECKey`, or `OKPKey`. It must use `options["kty"]` when provided, must use `raw["kty"]` when `raw` is a mapping with `kty`, and must try PEM or SSH key detection when no key type is provided. It raises `ValueError` when the input cannot be imported by the selected or detected key class.

`JsonWebKey.import_key_set(raw)` returns a `KeySet` when `raw` is a mapping with `keys`, a JSON object string with `keys`, or a list or tuple of key mappings. It raises `ValueError` when the input does not describe a key set.

`KeySet(keys)` stores the provided key objects. `KeySet.as_dict(is_private=False, **params)` returns `{"keys": [...]}` with each key exported through `as_dict`. `KeySet.as_json(is_private=False, **params)` returns that object as a JSON string. `KeySet.find_by_kid(kid, **params)` returns the first matching key. It raises `ValueError` when no key matches.

`Key` instances expose `tokens`, `kid`, `keys()`, `__getitem__`, `public_only`, `check_key_op(operation)`, `as_dict(is_private=False, **params)`, `as_json(is_private=False, **params)`, and `thumbprint()`. `check_key_op` raises `ValueError` when `key_ops` excludes the requested operation or when a public-only key is used for a private operation. It raises `InvalidUseError` when the key `use` value is incompatible with signing, verification, encryption, decryption, wrapping, or unwrapping.

`OctKey.import_key(raw, options=None)` imports an octet key from an existing `OctKey`, a JWK mapping, bytes, or string. `OctKey.generate_key(key_size=256, options=None, is_private=True)` returns a random symmetric key. It raises `ValueError` when `key_size` is not divisible by 8 or when `is_private` is false.

`RSAKey.import_key`, `ECKey.import_key`, and `OKPKey.import_key` import an existing key object, a cryptography key object, a JWK mapping, PEM bytes, DER bytes, or supported SSH public key bytes. `RSAKey.generate_key(key_size=2048, options=None, is_private=False)`, `ECKey.generate_key(crv="P-256", options=None, is_private=False)`, and `OKPKey.generate_key(crv="Ed25519", options=None, is_private=False)` return generated key objects. They raise `ValueError` when required JWK fields are missing or the size, curve, or raw key type is invalid.

`JsonWebSignature(algorithms=None, private_headers=None)` creates a JWS processor. `register_algorithm(algorithm)` registers a JWS algorithm object and raises `ValueError` when the algorithm object is missing or its algorithm type is not `JWS`. `serialize_compact(protected, payload, key)` returns bytes. `deserialize_compact(s, key, decode=None)` returns a `JWSObject`. `serialize_json(header_obj, payload, key)` returns a JSON serialization mapping. `deserialize_json(obj, key, decode=None)` returns a `JWSObject`. `serialize(header, payload, key)` and `deserialize(s, key, decode=None)` select compact or JSON serialization from the shape of the input.

`JWSHeader(protected, header)` is a dictionary combining unprotected and protected header values, with protected values taking precedence for duplicate names. Its `protected` attribute returns the protected header object and its `header` attribute returns the unprotected header object. `JWSHeader.from_dict(obj)` returns `obj` unchanged when it is already a `JWSHeader`, otherwise it builds a header from `obj["protected"]` and `obj["header"]`.

`JWSObject(header, payload, type="compact")` is a dictionary with `header` and `payload` keys plus `header`, `payload`, and `type` attributes. Its `headers` property returns the header list when `type` is `json`; it returns `None` when the object is not a general JSON JWS.

`JsonWebEncryption(algorithms=None, private_headers=None)` creates a JWE processor. `register_algorithm(algorithm)` registers a JWE `alg`, `enc`, or `zip` algorithm object and raises `ValueError` when the object is missing or its algorithm type is not `JWE`. `serialize_compact(protected, payload, key, sender_key=None)` returns compact bytes. `deserialize_compact(s, key, decode=None, sender_key=None)` returns a mapping with `header` and `payload`. `serialize_json(header_obj, payload, keys, sender_key=None)` returns a general JWE JSON serialization mapping. `deserialize_json(obj, key, decode=None, sender_key=None)` returns a mapping with `header` and `payload`. `serialize(header, payload, key, sender_key=None)` and `deserialize(obj, key, decode=None, sender_key=None)` select compact or JSON serialization from the shape of the input. `JsonWebEncryption.parse_json(obj)` and `JsonWebEncryption().parse_json(obj)` return a parsed JWE JSON mapping.

`JsonWebToken(algorithms, private_headers=None)` creates a JWT processor backed by a JWS processor and a JWE processor. `check_sensitive_data(payload)` raises `InsecureClaimError` when the payload contains sensitive claim names or sensitive string patterns. `encode(header, payload, key, check=True)` returns bytes. `decode(s, key, claims_cls=None, claims_options=None, claims_params=None)` returns an instance of the claims class.

`BaseClaims(payload, header, options=None, params=None)` is a dictionary subclass with `header`, `options`, and `params` attributes. `JWTClaims(payload, header, options=None, params=None)` extends `BaseClaims` with JWT registered claim validation. `JWTClaims.validate(now=None, leeway=0)` validates configured essential claims, issuer, subject, audience, expiration, not-before, issued-at, JWT ID, and custom configured claims.

## Product State Model

The core JOSE state has three public projections:

- Key state: JWK dictionaries, JSON strings, PEM or DER bytes, SSH public key bytes, cryptography key objects, and `Key` or `KeySet` instances.
- Message state: compact serialization bytes, JSON serialization mappings or strings, merged header objects, payload bytes, ciphertext bytes, signatures, and authentication tags.
- Token state: JWT header mappings, claims mappings, compact token bytes, decoded `JWTClaims` objects, and validation status.

Key state must round-trip through import and export projections when the selected key type has all required public or private fields. Message state must round-trip through serialize and deserialize operations when the same compatible key material and algorithms are used. Token state must round-trip through encode and decode when the header, payload, key, and allowed algorithms are compatible.

When a precondition is violated at any projection boundary, the API must raise the documented exception for that boundary instead of returning partial state.

## JSON Web Key Behavior

JWK import must preserve user-supplied allowed parameters such as `use`, `key_ops`, `alg`, and `kid`. Export methods must include those parameters when they are present and must apply keyword parameters passed to `as_dict` or `as_json` to the returned representation.

When a key lacks `kid`, `as_dict` must return a `kid` derived from the key thumbprint. `thumbprint()` must return the base64url-encoded SHA-256 digest over the required public JWK fields plus `kty`, sorted by field name. It raises `KeyError` when a required field needed for the thumbprint is absent.

`OctKey` must export a JWK with `kty` equal to `oct` and `k` as base64url-encoded key bytes. It must reject raw bytes that look like PEM, SSH RSA, SSH DSS, SSH Ed25519, or ECDSA SSH public key data by raising `ValueError`.

`RSAKey` must export public JWK fields `n` and `e`. It must export private JWK fields `d`, `p`, `q`, `dp`, `dq`, and `qi` when private export is requested from a private key. It must raise `ValueError` when private export is requested from a public key. It must raise `ValueError` when an RSA private JWK includes any of `p`, `q`, `dp`, `dq`, or `qi` without including all of them.

`ECKey` must support `P-256`, `P-384`, `P-521`, and `secp256k1`. It must export public JWK fields `crv`, `x`, and `y`, and must include `d` for private export from a private key. It must raise `ValueError` when an unsupported curve is requested.

`OKPKey` must support `Ed25519`, `Ed448`, `X25519`, and `X448`. It must export public JWK fields `crv` and `x`, and must include `d` for private export from a private key. It must raise `ValueError` when an unsupported curve is requested.

`KeySet.find_by_kid` must return the only key when `kid` is `None` and the set contains exactly one key. It must filter matching `kid` results by declared `use` and `alg` when those filter parameters are supplied. A key with no declared `use` or `alg` remains eligible for that filter. If several keys remain, it must return the first remaining key. If no key remains, it must raise `ValueError`.

## JSON Web Signature Behavior

JWS compact serialization must produce three dot-separated base64url segments: protected header, payload, and signature. Deserializing a valid compact serialization with the correct verification key must return a `JWSObject` whose `header` is a `JWSHeader` and whose `payload` is the decoded payload bytes or the return value of `decode(payload_bytes)` when `decode` is provided.

Supported JWS `alg` values are `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES384`, `ES512`, `ES256K`, `PS256`, `PS384`, `PS512`, and `EdDSA`. The `none` algorithm is registered as deprecated and must be rejected unless explicitly listed in `algorithms`.

JWS flattened JSON serialization must be selected when `serialize_json` receives one header mapping. It must return a mapping with `protected`, `signature`, `payload`, and `header` when an unprotected header is present. JWS general JSON serialization must be selected when `serialize_json` receives a list of header mappings. It must return a mapping with `payload` and `signatures`.

`serialize` must call JSON serialization when `header` is a list or tuple or when a header mapping contains `protected`. It must call compact serialization for a plain protected-header mapping. `deserialize` must call JSON deserialization when the input is a mapping or JSON object bytes or text, and must call compact deserialization for other bytes or text.

`deserialize_compact` must raise `ValueError` when the compact serialization exceeds `MAX_CONTENT_LENGTH`, whose default value is 256000 bytes.

When `algorithms` is `None`, the JWS processor must allow registered non-deprecated algorithms and must reject deprecated algorithms. When `algorithms` is provided, the processor must allow only listed algorithm names. Missing `alg` must raise `MissingAlgorithmError`; an unregistered, deprecated, or disallowed `alg` must raise `UnsupportedAlgorithmError`.

When `private_headers` is `None`, private header-name checking is disabled. When `private_headers` is provided, every header name must be a registered JWS header name or a listed private header name; otherwise the operation must raise `InvalidHeaderParameterNameError`.

When a protected JWS header includes `crit`, the `crit` value must be a list of strings, every listed name must be registered or configured as private, and every listed name must also appear in the protected header. A violation must raise `InvalidHeaderParameterNameError` for a malformed `crit` value and `InvalidCritHeaderParameterNameError` for an unknown or absent critical name. When a JSON JWS unprotected header contains `crit`, serialization or deserialization must raise `InvalidHeaderParameterNameError`.

When verification fails, `deserialize_compact` and `deserialize_json` must raise `BadSignatureError`. The exception must expose the partially decoded JWS object as `result`.

## JSON Web Encryption Behavior

JWE compact serialization must produce five dot-separated base64url segments: protected header, encrypted key, initialization vector, ciphertext, and authentication tag. Deserializing a valid compact serialization with the matching private or shared key must return a mapping with the protected header under `header` and the decrypted payload under `payload`.

JWE JSON serialization must return a mapping that represents general JSON serialization. It must include `protected` when the protected header is non-empty, `unprotected` when a shared unprotected header is non-empty, `recipients`, `aad` when additional authenticated data is supplied, `iv`, `ciphertext`, and `tag`. Each recipient must retain only `header` when non-empty and `encrypted_key`.

`serialize` must call JSON serialization when `header` contains `protected`, `unprotected`, or `recipients`. It must call compact serialization for a plain protected-header mapping. `deserialize` must call JSON deserialization when the input is a mapping or JSON object bytes or text, and must call compact deserialization for other bytes or text.

`JsonWebEncryption.parse_json` is callable from the class or from an instance. It must return the original mapping when the input is a mapping, and must parse a JSON object string into a mapping. It must raise `DecodeError` when the input is not a JSON object.

JWE compact and JSON encryption must require both `alg` and `enc`. Header validation must raise `MissingAlgorithmError` when `alg` is absent before checking other algorithm fields. When `alg` is present but unregistered, deprecated, or disallowed, validation must raise `UnsupportedAlgorithmError` before checking `enc`. When `alg` is supported, missing `enc` must raise `MissingEncryptionAlgorithmError`, an unregistered or disallowed `enc` must raise `UnsupportedEncryptionAlgorithmError`, and an unregistered or disallowed `zip` must raise `UnsupportedCompressionAlgorithmError`.

When `algorithms` is `None`, the JWE processor must allow registered non-deprecated `alg` values and registered `enc` and `zip` values. When `algorithms` is provided, `alg`, `enc`, and `zip` must each appear in that allow-list.

Supported JWE `alg` values are `dir`, `RSA-OAEP`, `RSA-OAEP-256`, `A128KW`, `A192KW`, `A256KW`, `A128GCMKW`, `A192GCMKW`, `A256GCMKW`, `ECDH-ES`, `ECDH-ES+A128KW`, `ECDH-ES+A192KW`, and `ECDH-ES+A256KW`. `RSA1_5` is registered as deprecated and must be rejected unless explicitly listed in `algorithms`. Supported JWE `enc` values are `A128CBC-HS256`, `A192CBC-HS384`, `A256CBC-HS512`, `A128GCM`, `A192GCM`, and `A256GCM`. Supported compression is `DEF`.

When `private_headers` is `None`, private header-name checking is disabled. When `private_headers` is provided, protected, shared unprotected, and per-recipient headers must contain only registered JWE header names, listed private header names, or algorithm extra header names. A violation must raise `InvalidHeaderParameterNameError`.

When JSON serialization receives a single key, it must accept a single key object or a one-item key list. When JSON serialization receives multiple keys, the number of recipient entries must match the number of keys; otherwise it must raise `ValueError`. When no keys are provided, it must raise `ValueError`. When multiple recipients are requested with an algorithm that does not produce a shared content encryption key, it must raise `InvalidAlgorithmForMultipleRecipientsMode`.

`sender_key` must be `None` for JWE algorithms that do not use sender authentication; passing a sender key to those algorithms must raise `ValueError`. Algorithms that require sender authentication must raise `ValueError` when `sender_key` is `None`.

When JSON deserialization receives a `(kid, key)` tuple, it must first try recipients whose per-recipient header has the same `kid`. When no explicit recipient match succeeds, it must try recipients in order. If no recipient decrypts and no lower-level unwrap error is available, it must raise `KeyMismatchError`; otherwise it must raise the last unwrap or decrypt error.

JWE JSON deserialization must ignore top-level members outside the JWE JSON serialization fields. It must remove per-recipient members other than `header` from the returned header view after decrypting. It must raise `DecodeError` when encoded protected header, encrypted key, additional authenticated data, initialization vector, ciphertext, or authentication tag values are malformed.

## JSON Web Token Behavior

JWT encoding must set `typ` to `JWT` in the header when the caller did not provide `typ`. For `exp`, `iat`, and `nbf`, a `datetime.datetime` value in the payload must be converted to a NumericDate integer before serialization. This conversion mutates the payload mapping supplied by the caller.

When `check` is true, JWT encoding must reject sensitive payloads with `InsecureClaimError`. Sensitive claim names are `password`, `token`, `secret`, and `secret_key`. Sensitive string values include common credit-card-number patterns, private-key PEM blocks, and US Social Security number patterns. When `check` is false, this sensitive-data check is skipped.

JWT encoding must use JWE compact serialization when the header contains `enc`; otherwise it must use JWS compact serialization. A missing or unsupported algorithm must raise the corresponding JWS or JWE algorithm exception.

JWT key selection for encoding must use `KeySet.find_by_kid(header["kid"])` when a `KeySet` and a header `kid` are provided. It must choose one key from the key set and write that key's `kid` into the header when a `KeySet` is provided without a header `kid`. For a JWK set mapping, it must use the key whose `kid` matches the header `kid`; without a header `kid`, it must choose one key from the mapping and write that key's `kid` into the header. If a JWK set mapping has a nonmatching `kid`, encoding must raise `ValueError`. If a single JWK mapping or `Key` has `kid`, encoding must write that `kid` into the header.

JWT decoding must select JWS verification for inputs with two dots and JWE decryption for inputs with four dots. Any other segment count must raise `DecodeError`. The decoded payload must be a JSON object; invalid JSON and non-object JSON must raise `DecodeError`.

When `claims_cls` is omitted, `decode` must return a `JWTClaims` instance. When `claims_cls` is supplied, `decode` must instantiate it as `claims_cls(payload, header, options=claims_options, params=claims_params)`.

JWT decoding key selection must call a callable key as `key(header, payload)`. For a `KeySet`, it must use `find_by_kid(header.get("kid"))`. For a JWK set mapping, it must return the key whose `kid` matches the header; when the header has no `kid`, it must return the only key in the set. It must raise `ValueError` when a JWK set mapping cannot identify a key.

## Claims Validation

`BaseClaims` must behave as a dictionary containing the payload claims. It must expose the decoded JOSE header through `header`. For names listed in `REGISTERED_CLAIMS`, attribute access must return the claim value or `None`. Attribute access for any other missing name must raise `AttributeError`.

Claim options must support `essential`, `value`, `values`, and `validate`. An essential claim must be present and truthy; absence must raise `MissingClaimError`, and a falsy present value must raise `InvalidClaimError`. A configured `value` must equal the claim value. A configured `values` list must contain the claim value. A configured `validate` callable must return truthy when called as `validate(claims, value)`. Failed value, values, or callable checks must raise `InvalidClaimError`.

`JWTClaims.validate(now=None, leeway=0)` must validate essential claims first, then registered claims `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, and `jti`, then configured custom claims. When `now` is `None`, validation must use the current Unix time.

Audience validation must accept a string audience or a list audience. When an audience option supplies `value` or `values`, at least one configured value must appear in the token audience. If no configured value appears, validation must raise `InvalidClaimError("aud")`.

Expiration validation must accept integer and float `exp` values. It must raise `InvalidClaimError("exp")` for non-numeric values. It must raise `ExpiredTokenError` when `exp < now - leeway`.

Not-before validation must accept integer and float `nbf` values. It must raise `InvalidClaimError("nbf")` for non-numeric values. It must raise `InvalidTokenError` when `nbf > now + leeway`.

Issued-at validation must accept integer and float `iat` values. It must raise `InvalidClaimError("iat")` for non-numeric values. It must raise `InvalidTokenError` when `iat > now + leeway`.

Issuer, subject, and JWT ID validation must use the configured claim option rules. Failed checks must raise `InvalidClaimError` for the claim name.

## Error Semantics

All JOSE-specific exceptions must inherit from `JoseError`. Each exception must expose its documented `error` code through the Authlib base error interface.

`DecodeError` must be raised for malformed compact segment counts, malformed base64url segments, malformed JSON serialization objects, invalid JWT payload JSON, and JWT payloads that are not JSON objects.

`MissingAlgorithmError` must be raised when a JWS or JWE operation requires `alg` and the header does not contain it.

`UnsupportedAlgorithmError` must be raised when a JWS or JWE `alg` is unregistered, deprecated without explicit allowance, or absent from the processor's allow-list. In JWE operations, an unsupported present `alg` must be reported before a missing or unsupported `enc`.

`MissingEncryptionAlgorithmError` must be raised when a JWE operation requires `enc` and the header does not contain it.

`UnsupportedEncryptionAlgorithmError` must be raised when a JWE `enc` value is unregistered or absent from the processor's allow-list.

`UnsupportedCompressionAlgorithmError` must be raised when a JWE `zip` value is unregistered or absent from the processor's allow-list.

`BadSignatureError` must be raised for JWS signature verification failure and must carry the partially decoded `JWSObject` as `result`.

`InvalidHeaderParameterNameError` must be raised for disallowed private header names, malformed JWS `crit`, and `crit` in an unprotected JWS header.

`InvalidCritHeaderParameterNameError` must be raised when a protected JWS `crit` entry names a header that is not understood or names a header absent from the protected header.

`InvalidUseError` must be raised when a key declares a `use` value incompatible with the requested operation.

`InvalidClaimError`, `MissingClaimError`, `InsecureClaimError`, `ExpiredTokenError`, and `InvalidTokenError` must be raised for the claim validation conditions described in the claims sections.

`KeyMismatchError` must be raised when JWE JSON deserialization has recipients but none match the provided key and no lower-level unwrap error explains the failure.

## Cross-View Invariants

1. A key imported with `JsonWebKey.import_key` must expose the same public JWK fields through `as_dict(False)` that are needed to verify signatures or encrypt messages with that key.
2. A private asymmetric key exported with `as_dict(True)` must import again as a private key whose `as_dict(False)` returns the same public projection.
3. A `kid` present on a key or selected from a key set must be visible in JWT headers produced by `JsonWebToken.encode`.
4. A payload signed with `JsonWebSignature.serialize_compact` must return the same payload bytes from `deserialize_compact` when verification uses the matching key.
5. A payload signed with `JsonWebSignature.serialize_json` must return the same payload bytes from `deserialize_json` when every signature verifies with the supplied key or key loader.
6. A payload encrypted with `JsonWebEncryption.serialize_compact` must return the same payload bytes from `deserialize_compact` when decryption uses the matching key.
7. A payload encrypted with `JsonWebEncryption.serialize_json` must return the same payload bytes from `deserialize_json` when decryption finds a matching recipient key.
8. A JWT encoded without `enc` must decode through the JWS path and return claims equal to the JSON payload after datetime conversion and sensitive-data checks.
9. A JWT encoded with `enc` must decode through the JWE path and return claims equal to the JSON payload after datetime conversion and sensitive-data checks.
10. A claims object returned by `JsonWebToken.decode` must expose the same header values that were protected in the compact JOSE serialization.

## Representative Workflows

Create and validate a signed JWT:

1. Import or generate a signing key with `JsonWebKey`, `RSAKey`, `ECKey`, `OKPKey`, or `OctKey`.
2. Build a JWT header with a supported `alg` and a claims mapping.
3. Call `jwt.encode(header, claims, key)` and store the returned compact bytes.
4. Call `jwt.decode(token, verification_key, claims_options=...)` with a matching verification key.
5. Call `claims.validate(now=..., leeway=...)`.
6. The workflow returns a validated `JWTClaims` object when the signature, key, header, payload, and claims are valid. It raises the matching JOSE exception when signature verification, algorithm selection, key selection, payload decoding, or claims validation fails.

Encrypt and decrypt a JWE message:

1. Import or generate an encryption key with `JsonWebKey`, `RSAKey`, `ECKey`, `OKPKey`, or `OctKey`.
2. Create `JsonWebEncryption()` or a restricted `JsonWebEncryption(algorithms=[...])`.
3. Call `serialize_compact` with a protected header containing compatible `alg` and `enc`.
4. Call `deserialize_compact` with the matching decryption key.
5. The workflow returns the original payload bytes when the key, algorithms, protected header, ciphertext, authentication tag, and compression header are valid. It raises the matching JOSE or cryptography exception when decryption or validation fails.

## Non-Goals

This specification does not cover OAuth 1.0, OAuth 2.0, OpenID Connect provider/client flows, Flask, Django, Starlette, HTTPX, Requests, SQLAlchemy integrations, grant classes, token endpoint behavior, remote key fetching, network I/O, CLI commands, draft ChaCha20-Poly1305 JOSE algorithms, ECDH-1PU draft algorithms, or internal helper modules.

This specification does not require exact exception message text unless the exception class exposes a public claim name or result object described above.

## Invocation Protocol

Authlib JOSE is a library API. It does not provide a JOSE console script. Running `python -m authlib` is not supported.

| Invocation | Supported | Result |
|---|---:|---|
| `import authlib` | yes | Imports package metadata including non-empty `__version__`, `__homepage__` equal to `https://authlib.org`, and `__license__` equal to `BSD-3-Clause`. |
| `from authlib.jose import ...` | yes | Imports the public JOSE API and emits `AuthlibDeprecationWarning` for `authlib.jose`. |
| `python -m authlib` | no | Python reports that the package has no module entry point. |
| JOSE console script | no | No command is installed for JOSE operations. |

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Assessment exercises the public import surface, key import and export projections, JWS compact and JSON round trips, JWE compact and JSON round trips, JWT encode and decode behavior, header validation, claims validation, and exception classes. Checks use public APIs and observable return values or raised exception classes. They do not require OAuth flows, framework integrations, network services, hidden internal helpers, or exact message text beyond public exception data described in this specification.
