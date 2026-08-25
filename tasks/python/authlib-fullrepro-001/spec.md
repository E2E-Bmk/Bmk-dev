# Authlib legacy JOSE compatibility specification

## Scope

This package supplies a compact, self-contained implementation of the legacy
`authlib.jose` public interface.  It covers JSON Web Keys, JWK sets, JSON Web
Signatures, JSON Web Encryption, JSON Web Tokens, and JWT claim validation.
The interface is suitable for applications that need deterministic artifacts,
explicit key rotation, and strict recipient and claim handling.

The public package reports version `1.7.2`.  The following names are importable
from `authlib.jose`: `Key`, `KeySet`, `JsonWebKey`, `JsonWebSignature`,
`JsonWebEncryption`, `JsonWebToken`, `JWTClaims`, `OctKey`, and `RSAKey`.
The documented JOSE exceptions, including `BadSignatureError`,
`KeyMismatchError`, `MissingClaimError`, and `InvalidClaimError`, are available
from `authlib.jose.errors`.

## Key material and JWK representation

`JsonWebKey.import_key` accepts a JWK mapping, an existing key object, symmetric
bytes, and supported RSA material.  `JsonWebKey.import_key_set` accepts the
standard JWKS mapping or its JSON representation and returns a `KeySet`.

Symmetric keys support the `oct` JWK form and the HMAC, direct-encryption, and
AES key-wrapping algorithm families appropriate to their key size.  RSA keys
support public and private JWK import/export, RSASSA-PKCS1-v1_5 signatures, and
RSA-OAEP encryption.  Exporting a private RSA key as public material omits all
private parameters while retaining public metadata.  Exported public material
can be imported again and used for verification or encryption.

Each key exposes its `kid` and preserves recognized JWK metadata such as `use`
and `alg`.  `as_dict(is_private=False)` and `as_json(is_private=False)` return
standard JWK representations.  Private parameters are included only when
explicitly requested and available.

## Transactional key sets

`KeySet(keys)` stores an ordered committed key sequence.  Its ordinary
`keys`, `as_dict()`, and `as_json()` views contain committed keys only.

`stage(key)` appends a key to a pending batch without publishing it through a
committed view or making it eligible for selection.  It returns the staged key.
`pending` is a read-only tuple representing the current pending batch.

`commit()` validates and publishes the whole pending batch as one transaction.
Every key in the resulting committed set must have a non-empty, unique `kid`.
On success the pending keys are appended in stage order, the pending batch is
cleared, and `revision` advances exactly once.  Calling `commit()` with no
pending keys returns the current revision without changing state.  If validation
fails, the committed sequence and revision remain unchanged and the rejected
pending batch is cleared.

`rollback()` clears the pending batch without changing committed state.  It
reports whether any pending state was removed, so repeated rollback is
idempotent.

`find_by_kid(kid, **metadata)` searches committed keys only.  A supplied `kid`,
`use`, or `alg` is an exact constraint; absent key metadata is not a wildcard
for a supplied constraint.  When `kid` is omitted, the newest committed key
eligible for all supplied constraints is selected.  Exact lookup also returns
the newest eligible match if duplicate identifiers exist in imported legacy
data.  If no eligible key exists, the method raises `ValueError`.

`snapshot(is_private=False)` returns a detached mapping with the current
revision, committed JWK representations, and an `active` mapping.  Active lanes
are named by the key's use and algorithm, with `*` representing unspecified
metadata, and point to the newest committed identifier in each lane.  Mutating
the snapshot cannot alter the key set.

## JWS behavior

`JsonWebSignature(algorithms)` restricts operations to the named algorithms.
It supports compact, flattened JSON, and general JSON serialization and their
corresponding deserialization operations.  Serialization accepts bytes-like or
text payloads and either key objects or key-loader callables.  General JSON
serialization supports independently protected signatures over one payload.

Protected header mappings are serialized in deterministic recursive key order.
Equivalent mappings therefore produce the same protected segment and, for a
deterministic signature algorithm and inputs, the same signature.  Sequence
order is preserved.  Serialization never mutates caller-owned header mappings.

Successful deserialization returns the protected header and payload.  A bad
signature raises `BadSignatureError` while retaining the decoded header and
payload on the exception's public result object for diagnostics.

## JWE behavior

`JsonWebEncryption(algorithms)` supports compact and JSON serialization for the
enabled key-management and content-encryption algorithms.  The required direct,
AES key-wrap, RSA-OAEP, and AES-GCM combinations follow their JOSE key-size and
recipient rules.  Direct key management is a single-recipient mode.  JSON key
wrapping can address multiple recipients, all of whom recover the same payload.

Protected JWE mappings use the same deterministic recursive ordering as JWS
protected mappings.  Caller-owned headers and serialized JSON objects are not
mutated by serialization or deserialization.

For JSON deserialization, a key argument of `(kid, key)` is a strict recipient
constraint.  The requested identifier must occur in a recipient header before
any unwrap or content-decryption attempt; otherwise `KeyMismatchError` is
raised.  A matching tuple decrypts only the named recipient.  Failed strict
selection leaves the serialized object reusable for a later attempt.

## JWT encoding and decoding

`JsonWebToken(algorithms)` creates and consumes signed JWTs using the enabled
algorithms.  Encoding supplies the conventional JWT type when it is absent and
adds the selected key identifier when available.  These defaults are applied to
an internal copy: the caller's header is not changed.  A `KeySet` with no
explicit `kid` uses the newest committed signing key whose `use` and `alg`
metadata are eligible.

JWT payload mappings are also caller-owned.  Datetime values in registered
numeric-date claims are converted to integer epoch values in the encoded token,
without replacing the values in the original mapping.  Decoding verifies the
signature, selects a key by the protected identifier when a key set is supplied,
and returns a claims object with its decoded header available as `header`.
Custom claims classes receive the header, claim options, and claim parameters.

## Claim validation

`JWTClaims(payload, header, options=None, params=None)` is mapping-compatible.
`validate(now=None, leeway=0)` validates registered time claims and configured
claim rules.

An essential claim is required to be present; its value is not required to be
truthy unless another configured rule says so.  A configured `value` is enforced
even when that configured value is false, zero, an empty string, or null.
Configured `values` and `validate` callbacks are likewise honored.  A callback
receives the claims object and current value and may consult `params` and
`header`.

Numeric dates are finite integers or floats, but booleans are not numeric dates.
Leeway is a non-negative real number and a boolean is not valid leeway.  Invalid
claim types or values use the documented public claim-error categories; invalid
leeway raises `ValueError`.

## Ownership and interoperability guarantees

Public encode, serialize, decode, validate, export, and snapshot operations do
not retain writable aliases to caller-provided mappings.  Serialized compact
values are bytes.  JSON forms are ordinary mappings containing JOSE base64url
text.  Exported JWK and JWKS data can be round-tripped through the matching
import functions, and compatible artifacts can be nested across signing and
encryption operations.
