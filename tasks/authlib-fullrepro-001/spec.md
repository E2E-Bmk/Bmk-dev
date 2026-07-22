# Authlib JOSE Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Authlib JOSE is a Python library for JSON Object Signing and Encryption. It exposes high-level processors for importing cryptographic keys, signing and verifying payloads, encrypting and decrypting payloads, encoding and decoding JSON Web Tokens, and validating token claims. The public contract lives in the `authlib.jose` package and covers JWK, JWS, JWE, and JWT workflows through compact and JSON serializations.

The library is a programmatic API only. All behavior described here is observable through public imports, return values, raised exception types, and documented public attributes on returned objects.

## Non-Goals

- This specification does not require OAuth 1.0, OAuth 2.0, OpenID Connect provider or client flows, web framework integrations, HTTP clients, database layers, or remote key fetching over the network.
- This specification does not require private helper modules, private attributes, internal module layout, or exact textual representations such as `repr()` output and log message wording.
- This specification does not require command-line interfaces or `python -m authlib` entry points.
- This specification does not require draft ChaCha20-Poly1305 JOSE algorithms, ECDH-1PU draft algorithms, or compatibility with every historical draft extension.
- This specification does not require exact exception message text except where a public claim name or partially decoded result object is part of the contract.

## Representative Workflows

### Signed JWT Validation

```python
from authlib.jose import JsonWebKey, jwt

key = JsonWebKey.import_key("secret", {"kty": "oct", "kid": "signing-key"})
token = jwt.encode({"alg": "HS256"}, {"sub": "user-42", "iss": "issuer.test"}, key)
claims = jwt.decode(token, key, claims_options={"iss": {"value": "issuer.test"}})
claims.validate(now=1_700_000_000, leeway=0)

assert claims["sub"] == "user-42"
assert claims.header["typ"] == "JWT"
```

A signed JWT must round-trip through encode and decode when the header algorithm, key material, and claims are compatible. Validation must enforce configured essential, registered, and custom claim rules and must raise the documented JOSE exception when a rule fails.

### Compact JWE Encryption

```python
from authlib.jose import JsonWebEncryption, OctKey

key = OctKey.generate_key(256, is_private=True)
jwe = JsonWebEncryption()
protected = {"alg": "dir", "enc": "A128GCM"}
ciphertext = jwe.serialize_compact(protected, b"confidential-bytes", key)
result = jwe.deserialize_compact(ciphertext, key)

assert result["payload"] == b"confidential-bytes"
assert result["header"]["alg"] == "dir"
```

A compact JWE message must contain five dot-separated segments. Decryption with the matching key must restore the original payload bytes and expose the protected header under `header`.

## Key Import and Export

**Key generation and import.** `JsonWebKey.generate_key(kty, crv_or_size, options=None, is_private=False)` must return a key object for `oct`, `RSA`, `EC`, or `OKP`. It must raise `KeyError` when `kty` is unknown and `ValueError` when the requested size, curve, or privacy mode is invalid.

`JsonWebKey.import_key(raw, options=None)` must return an `OctKey`, `RSAKey`, `ECKey`, or `OKPKey`. When `options["kty"]` is provided, that key type must be used. When `raw` is a mapping with `kty`, that type must be inferred. When no key type is provided, PEM or SSH key detection must be attempted. Invalid input must raise `ValueError`.

`JsonWebKey.import_key_set(raw)` must accept a mapping with `keys`, a JSON object string containing `keys`, or a list or tuple of key mappings. Invalid input must raise `ValueError`.

**KeySet behavior.** `KeySet(keys)` stores the provided key objects. `KeySet.as_dict(is_private=False, **params)` must return `{"keys": [...]}` with each key exported through `as_dict`. `KeySet.as_json(is_private=False, **params)` must return that object as a JSON string. `KeySet.find_by_kid(kid, **params)` must return the first matching key and must raise `ValueError` when no key matches.

When `kid` is `None` and the set contains exactly one key, `find_by_kid` must return that key. When `use` or `alg` filter parameters are supplied, keys with no declared `use` or `alg` remain eligible. If several keys remain, the first remaining key must be returned.

**Key projections.** `Key` instances expose `tokens`, `kid`, `keys()`, `__getitem__`, `public_only`, `check_key_op(operation)`, `as_dict(is_private=False, **params)`, `as_json(is_private=False, **params)`, and `thumbprint()`.

`check_key_op` must raise `ValueError` when `key_ops` excludes the requested operation or when a public-only key is used for a private operation. It must raise `InvalidUseError` when the key `use` value is incompatible with signing, verification, encryption, decryption, wrapping, or unwrapping.

When a key lacks `kid`, `as_dict` must include a `kid` derived from the key thumbprint. `thumbprint()` must return the base64url-encoded SHA-256 digest over required public JWK fields plus `kty`, sorted by field name. Missing required thumbprint fields must raise `KeyError`.

**OctKey.** `OctKey.import_key` must accept an existing `OctKey`, a JWK mapping, bytes, or string. `OctKey.generate_key(key_size=256, options=None, is_private=True)` must return a random symmetric key. It must raise `ValueError` when `key_size` is not divisible by 8 or when `is_private` is false. Export must include `kty` equal to `oct` and `k` as base64url-encoded key bytes. Raw bytes resembling PEM or SSH public key material must raise `ValueError`.

**RSAKey.** Import must accept an existing key object, a cryptography key object, a JWK mapping, PEM bytes, DER bytes, or supported SSH public key bytes. `RSAKey.generate_key(key_size=2048, options=None, is_private=False)` must return a generated key and must raise `ValueError` for invalid sizes.

Public export must include `n` and `e`. Private export from a private key must include `d`, `p`, `q`, `dp`, `dq`, and `qi`. Private export from a public key must raise `ValueError`. A private JWK that includes any of `p`, `q`, `dp`, `dq`, or `qi` without all of them must raise `ValueError`.

**ECKey and OKPKey.** `ECKey` must support curves `P-256`, `P-384`, `P-521`, and `secp256k1`. `OKPKey` must support `Ed25519`, `Ed448`, `X25519`, and `X448`. Public export must include the curve and coordinate fields. Private export from a private key must include `d`. Unsupported curves must raise `ValueError`.

## JSON Web Signature Processing

`JsonWebSignature(algorithms=None, private_headers=None)` creates a JWS processor. `register_algorithm(algorithm)` registers a JWS algorithm object and raises `ValueError` when the algorithm object is missing or its type is not `JWS`.

**Serialization selection.** `serialize_compact(protected, payload, key)` returns compact bytes with three dot-separated base64url segments. `serialize_json(header_obj, payload, key)` returns a JSON serialization mapping. Flattened JSON serialization is selected for one header mapping. General JSON serialization is selected for a list of header mappings and must return `payload` and `signatures`.

`serialize(header, payload, key)` must call JSON serialization when `header` is a list or tuple or when a header mapping contains `protected`. It must call compact serialization for a plain protected-header mapping. `deserialize(s, key, decode=None)` must call JSON deserialization for mappings or JSON object bytes or text, and compact deserialization otherwise.

**Header objects.** `JWSHeader(protected, header)` combines unprotected and protected header values, with protected values taking precedence for duplicate names. Its `protected` attribute returns the protected header object and its `header` attribute returns the unprotected header object. `JWSHeader.from_dict(obj)` returns `obj` unchanged when it is already a `JWSHeader`.

`JWSObject(header, payload, type="compact")` exposes `header`, `payload`, and `type`. Its `headers` property returns the header list for general JSON JWS and `None` for compact JWS.

**Algorithm policy.** Supported JWS `alg` values are `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES384`, `ES512`, `ES256K`, `PS256`, `PS384`, `PS512`, and `EdDSA`. The `none` algorithm is deprecated and must be rejected unless explicitly listed in `algorithms`.

When `algorithms` is `None`, registered non-deprecated algorithms must be allowed. When `algorithms` is provided, only listed algorithm names must be allowed. Missing `alg` must raise `MissingAlgorithmError`. An unregistered, deprecated, or disallowed `alg` must raise `UnsupportedAlgorithmError`.

**Private and critical headers.** When `private_headers` is `None`, private header-name checking is disabled. When `private_headers` is provided, every header name must be a registered JWS header name or a listed private header name; otherwise the operation must raise `InvalidHeaderParameterNameError`.

When a protected header includes `crit`, the value must be a list of strings, every listed name must be registered or configured as private, and every listed name must also appear in the protected header. Malformed `crit` must raise `InvalidHeaderParameterNameError`. Unknown or absent critical names must raise `InvalidCritHeaderParameterNameError`. `crit` in an unprotected JWS header must raise `InvalidHeaderParameterNameError`.

**Verification failures.** Signature verification failure must raise `BadSignatureError` and expose the partially decoded JWS object as `result`. `deserialize_compact` must raise `ValueError` when compact serialization exceeds `MAX_CONTENT_LENGTH`, whose default is 256000 bytes.

## JSON Web Encryption Processing

`JsonWebEncryption(algorithms=None, private_headers=None)` creates a JWE processor. `register_algorithm(algorithm)` registers a JWE `alg`, `enc`, or `zip` algorithm object and raises `ValueError` when the object is missing or its type is not `JWE`.

**Serialization selection.** Compact serialization must produce five dot-separated base64url segments. JSON serialization must return a general JSON mapping with `protected`, optional `unprotected`, `recipients`, optional `aad`, `iv`, `ciphertext`, and `tag`. Each recipient must retain only non-empty `header` and `encrypted_key`.

`serialize(header, payload, key, sender_key=None)` must call JSON serialization when `header` contains `protected`, `unprotected`, or `recipients`. It must call compact serialization for a plain protected-header mapping. `deserialize(obj, key, decode=None, sender_key=None)` must call JSON deserialization for mappings or JSON object bytes or text, and compact deserialization otherwise.

`JsonWebEncryption.parse_json(obj)` must return the original mapping when the input is a mapping and must parse a JSON object string into a mapping. Non-object JSON must raise `DecodeError`.

**Algorithm policy.** JWE operations require both `alg` and `enc`. Missing `alg` must raise `MissingAlgorithmError` before other algorithm checks. Unsupported present `alg` must raise `UnsupportedAlgorithmError` before `enc` checks. Missing `enc` must raise `MissingEncryptionAlgorithmError`. Unsupported `enc` must raise `UnsupportedEncryptionAlgorithmError`. Unsupported `zip` must raise `UnsupportedCompressionAlgorithmError`.

Supported JWE `alg` values are `dir`, `RSA-OAEP`, `RSA-OAEP-256`, `A128KW`, `A192KW`, `A256KW`, `A128GCMKW`, `A192GCMKW`, `A256GCMKW`, `ECDH-ES`, `ECDH-ES+A128KW`, `ECDH-ES+A192KW`, and `ECDH-ES+A256KW`. `RSA1_5` is deprecated and must be rejected unless explicitly listed in `algorithms`. Supported `enc` values are `A128CBC-HS256`, `A192CBC-HS384`, `A256CBC-HS512`, `A128GCM`, `A192GCM`, and `A256GCM`. Supported compression is `DEF`.

When `algorithms` is `None`, registered non-deprecated `alg` values and registered `enc` and `zip` values must be allowed. When `algorithms` is provided, `alg`, `enc`, and `zip` must each appear in that allow-list.

**Private headers and recipients.** When `private_headers` is provided, protected, shared unprotected, and per-recipient headers must contain only registered JWE header names, listed private header names, or algorithm extra header names. Violations must raise `InvalidHeaderParameterNameError`.

JSON serialization with a single key must accept one key object or a one-item key list. With multiple keys, the recipient count must match the key count or raise `ValueError`. Missing keys must raise `ValueError`. Multiple recipients with an algorithm that does not support shared content encryption keys must raise `InvalidAlgorithmForMultipleRecipientsMode`.

**Sender keys and recipient selection.** `sender_key` must be `None` for algorithms that do not use sender authentication; passing a sender key to those algorithms must raise `ValueError`. Algorithms that require sender authentication must raise `ValueError` when `sender_key` is `None`.

JSON deserialization with a `(kid, key)` tuple must first try recipients whose per-recipient header has the same `kid`, then try recipients in order. If no recipient decrypts and no lower-level unwrap error is available, `KeyMismatchError` must be raised; otherwise the last unwrap or decrypt error must be raised.

JSON deserialization must ignore top-level members outside the JWE JSON serialization fields. After decrypting, per-recipient members other than `header` must be removed from the returned header view. Malformed encoded protected header, encrypted key, additional authenticated data, initialization vector, ciphertext, or authentication tag values must raise `DecodeError`.

## JSON Web Token Encoding and Decoding

`JsonWebToken(algorithms, private_headers=None)` creates a JWT processor backed by JWS and JWE processors. The preconfigured `jwt` object supports `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES256K`, `ES384`, `ES512`, `PS256`, `PS384`, `PS512`, and `EdDSA`.

**Encoding.** `encode(header, payload, key, check=True)` returns bytes. When `typ` is absent, the header must include `typ` equal to `JWT`. For `exp`, `iat`, and `nbf`, `datetime.datetime` values in the payload must be converted to NumericDate integers before serialization, mutating the caller-supplied payload mapping.

When `check` is true, encoding must reject sensitive payloads with `InsecureClaimError`. Sensitive claim names are `password`, `token`, `secret`, and `secret_key`. Sensitive string values include common credit-card-number patterns, private-key PEM blocks, and US Social Security number patterns.

Encoding must use JWE compact serialization when the header contains `enc`; otherwise it must use JWS compact serialization. A missing or unsupported algorithm must raise the corresponding JWS or JWE algorithm exception.

**Key selection for encoding.** When a `KeySet` and header `kid` are provided, encoding must use `KeySet.find_by_kid(header["kid"])`. When a `KeySet` is provided without header `kid`, it must choose one key and write that key's `kid` into the header. For a JWK set mapping, it must use the key whose `kid` matches the header `kid`; without header `kid`, it must choose one key and write that key's `kid` into the header. A nonmatching `kid` in a JWK set mapping must raise `ValueError`. A single JWK mapping or `Key` with `kid` must write that `kid` into the header.

**Decoding.** Decoding must select JWS verification for inputs with two dots and JWE decryption for inputs with four dots. Any other segment count must raise `DecodeError`. The decoded payload must be a JSON object; invalid JSON and non-object JSON must raise `DecodeError`.

When `claims_cls` is omitted, `decode` must return a `JWTClaims` instance. When `claims_cls` is supplied, `decode` must instantiate it as `claims_cls(payload, header, options=claims_options, params=claims_params)`.

Decoding key selection must call a callable key as `key(header, payload)`. For a `KeySet`, it must use `find_by_kid(header.get("kid"))`. For a JWK set mapping, it must return the key whose `kid` matches the header; when the header has no `kid`, it must return the only key in the set. It must raise `ValueError` when a JWK set mapping cannot identify a key.

## Claims Validation

`BaseClaims(payload, header, options=None, params=None)` is a dictionary subclass with `header`, `options`, and `params` attributes. For names listed in `REGISTERED_CLAIMS`, attribute access must return the claim value or `None`. Attribute access for any other missing name must raise `AttributeError`.

Claim options support `essential`, `value`, `values`, and `validate`. An essential claim must be present and truthy; absence must raise `MissingClaimError`, and a falsy present value must raise `InvalidClaimError`. A configured `value` must equal the claim value. A configured `values` list must contain the claim value. A configured `validate` callable must return truthy when called as `validate(claims, value)`. Failed value, values, or callable checks must raise `InvalidClaimError`.

`JWTClaims.validate(now=None, leeway=0)` must validate essential claims first, then registered claims `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, and `jti`, then configured custom claims. When `now` is `None`, validation must use the current Unix time.

Audience validation must accept string or list audience values. When an audience option supplies `value` or `values`, at least one configured value must appear in the token audience or validation must raise `InvalidClaimError("aud")`.

Expiration validation must accept integer and float `exp` values, raise `InvalidClaimError("exp")` for non-numeric values, and raise `ExpiredTokenError` when `exp < now - leeway`.

Not-before validation must accept integer and float `nbf` values, raise `InvalidClaimError("nbf")` for non-numeric values, and raise `InvalidTokenError` when `nbf > now + leeway`.

Issued-at validation must accept integer and float `iat` values, raise `InvalidClaimError("iat")` for non-numeric values, and raise `InvalidTokenError` when `iat > now + leeway`.

Issuer, subject, and JWT ID validation must use configured claim option rules. Failed checks must raise `InvalidClaimError` for the claim name.

## State Model

The core JOSE state has three public projections:

- **Key state**: JWK dictionaries, JSON strings, PEM or DER bytes, SSH public key bytes, cryptography key objects, and `Key` or `KeySet` instances.
- **Message state**: compact serialization bytes, JSON serialization mappings or strings, merged header objects, payload bytes, ciphertext bytes, signatures, and authentication tags.
- **Token state**: JWT header mappings, claims mappings, compact token bytes, decoded claims objects, and validation status.

Key state must round-trip through import and export projections when the selected key type has all required public or private fields. Message state must round-trip through serialize and deserialize operations when the same compatible key material and algorithms are used. Token state must round-trip through encode and decode when the header, payload, key, and allowed algorithms are compatible.

When a precondition is violated at any projection boundary, the API must raise the documented exception for that boundary instead of returning partial state.

## Error Semantics

| Condition | Required result |
|-----------|-----------------|
| Malformed compact segment count, malformed base64url, malformed JSON serialization, invalid JWT payload JSON, or JWT payload not a JSON object | Raise `DecodeError` |
| JWS or JWE operation requires `alg` and header lacks it | Raise `MissingAlgorithmError` |
| JWS or JWE `alg` is unregistered, deprecated without explicit allowance, or absent from processor allow-list | Raise `UnsupportedAlgorithmError` |
| JWE operation requires `enc` and header lacks it | Raise `MissingEncryptionAlgorithmError` |
| JWE `enc` is unregistered or absent from processor allow-list | Raise `UnsupportedEncryptionAlgorithmError` |
| JWE `zip` is unregistered or absent from processor allow-list | Raise `UnsupportedCompressionAlgorithmError` |
| JWS signature verification failure | Raise `BadSignatureError` with partially decoded `result` |
| Disallowed private header name, malformed JWS `crit`, or `crit` in unprotected JWS header | Raise `InvalidHeaderParameterNameError` |
| Protected JWS `crit` names unknown or absent header | Raise `InvalidCritHeaderParameterNameError` |
| Key `use` incompatible with requested operation | Raise `InvalidUseError` |
| Essential claim missing | Raise `MissingClaimError` |
| Claim value fails configured validation | Raise `InvalidClaimError` |
| Sensitive payload encoded with `check=True` | Raise `InsecureClaimError` |
| Token expired per `exp` and leeway | Raise `ExpiredTokenError` |
| Token not yet valid per `nbf` or `iat` and leeway | Raise `InvalidTokenError` |
| JWE JSON deserialization has recipients but none match provided key | Raise `KeyMismatchError` |
| Multiple recipients with unsupported algorithm mode | Raise `InvalidAlgorithmForMultipleRecipientsMode` |
| Unknown `kty` in `JsonWebKey.generate_key` | Raise `KeyError` |
| Invalid key import input or invalid key size, curve, or privacy mode | Raise `ValueError` |
| Invalid key set input or no matching key in `KeySet.find_by_kid` | Raise `ValueError` |
| Missing required thumbprint field | Raise `KeyError` |
| Compact JWS exceeds `MAX_CONTENT_LENGTH` | Raise `ValueError` |

All JOSE-specific exceptions must inherit from `JoseError` and expose a documented `error` code through the Authlib base error interface.

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

## Public Interface

### Import Surface

The package is installed as `authlib`.

```python
from authlib.jose import (
    JoseError,
    JsonWebSignature,
    JWSAlgorithm,
    JWSHeader,
    JWSObject,
    JsonWebEncryption,
    JWEAlgorithm,
    JWEEncAlgorithm,
    JWEZipAlgorithm,
    JsonWebKey,
    Key,
    KeySet,
    OctKey,
    RSAKey,
    ECKey,
    OKPKey,
    JsonWebToken,
    BaseClaims,
    JWTClaims,
    jwt,
)
from authlib.jose.errors import (
    DecodeError,
    MissingAlgorithmError,
    UnsupportedAlgorithmError,
    BadSignatureError,
    InvalidHeaderParameterNameError,
    InvalidCritHeaderParameterNameError,
    InvalidAlgorithmForMultipleRecipientsMode,
    KeyMismatchError,
    MissingEncryptionAlgorithmError,
    UnsupportedEncryptionAlgorithmError,
    UnsupportedCompressionAlgorithmError,
    InvalidUseError,
    InvalidClaimError,
    MissingClaimError,
    InsecureClaimError,
    ExpiredTokenError,
    InvalidTokenError,
)
```

There is no JOSE console script. `python -m authlib` is not a supported invocation.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| JsonWebKey | class | Factory for importing and generating JWK key objects |
| Key | class | Base key object with export and operation checks |
| KeySet | class | Collection of keys with lookup and export helpers |
| OctKey | class | Symmetric octet key import, generation, and export |
| RSAKey | class | RSA key import, generation, and export |
| ECKey | class | Elliptic-curve key import, generation, and export |
| OKPKey | class | Octet key pair import, generation, and export |
| JsonWebSignature | class | JWS compact and JSON serialize/deserialize processor |
| JWSAlgorithm | class | Base class for registrable JWS signing algorithms |
| JWSHeader | class | Combined protected and unprotected JWS header view |
| JWSObject | class | Decoded JWS payload and header container |
| JsonWebEncryption | class | JWE compact and JSON serialize/deserialize processor |
| JWEAlgorithm | class | Base class for registrable JWE key-management algorithms |
| JWEEncAlgorithm | class | Base class for registrable JWE content-encryption algorithms |
| JWEZipAlgorithm | class | Base class for registrable JWE compression algorithms |
| JsonWebToken | class | JWT encode/decode processor over JWS and JWE |
| BaseClaims | class | Dictionary-like decoded claims with options |
| JWTClaims | class | JWT registered-claim validation helper |
| jwt | object | Preconfigured JsonWebToken with common algorithms |
| JoseError | exception | Base class for JOSE-specific errors |
| DecodeError | exception | Malformed serialization or payload decoding failure |
| MissingAlgorithmError | exception | Required `alg` header missing |
| UnsupportedAlgorithmError | exception | Disallowed or unknown `alg` value |
| MissingEncryptionAlgorithmError | exception | Required `enc` header missing |
| UnsupportedEncryptionAlgorithmError | exception | Disallowed or unknown `enc` value |
| UnsupportedCompressionAlgorithmError | exception | Disallowed or unknown `zip` value |
| BadSignatureError | exception | JWS verification failure |
| InvalidHeaderParameterNameError | exception | Disallowed or malformed header parameter |
| InvalidCritHeaderParameterNameError | exception | Invalid protected critical header extension |
| InvalidAlgorithmForMultipleRecipientsMode | exception | Algorithm incompatible with multi-recipient JWE |
| KeyMismatchError | exception | No JWE recipient matches supplied key |
| InvalidUseError | exception | Key `use` incompatible with operation |
| InvalidClaimError | exception | Claim value failed validation |
| MissingClaimError | exception | Required claim absent |
| InsecureClaimError | exception | Sensitive payload rejected during encode |
| ExpiredTokenError | exception | Token expiration validation failure |
| InvalidTokenError | exception | Token not-yet-valid validation failure |

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `authlib`, `cryptography`, `pytest`.

The assessment environment provides the same interpreter and package set. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root so the package can be installed with pip. All JOSE workflows must operate locally without network services.

## Appendix B: Assessment Notes

Implementations are exercised through public Python APIs in `authlib.jose`. Checks cover key import and export, JWS compact and JSON round trips, JWE compact and JSON round trips, JWT encode and decode, header validation, claims validation, and documented exception types. Tests use locally generated keys and in-memory payloads instead of live network services. The focus is on observable behavior from the public contract above, not private data structures or exact textual representations.
