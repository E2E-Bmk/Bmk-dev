# PGPy Specification

## Product Overview
PGPy is a Python implementation of OpenPGP for application developers. It provides objects for keys, keyrings, messages, signatures, user IDs, OpenPGP constants, and PGPy-specific exceptions. The library must read and write supported OpenPGP packets in binary and ASCII-armored forms, create and verify signatures, encrypt and decrypt messages with public keys or passphrases, and expose enough object state for callers to inspect key, message, signature, and verification results.

The public contract is object-oriented. `PGPKey`, `PGPMessage`, and `PGPSignature` must serialize with `str()` to ASCII-armored OpenPGP blocks and with `bytes()` to binary OpenPGP packet data. Public methods must raise the documented PGPy exception types instead of leaking lower-level parser or cryptography failures.

## Scope
This specification covers:

- Loading and exporting keys, messages, and signatures from files, bytes, bytearrays, and text blobs.
- Creating OpenPGP messages from text, bytes, bytearrays, and caller-supplied files.
- Generating, inspecting, protecting, unlocking, certifying, revoking, and exporting keys and user IDs.
- Creating detached, inline, timestamp, standalone, key, user ID, and revocation signatures.
- Verifying signatures and inspecting aggregate verification results.
- Encrypting and decrypting messages with passphrases and with supported public-key algorithms.
- Managing in-memory keyrings and selecting keys by fingerprint, key ID, short ID, user ID name, comment, email, message, or signature.
- Public constants, public exceptions, and documented helper return objects.

## Installable Surface
Installing the package named `PGPy` must provide the import package `pgpy`.

`import pgpy` and `from pgpy import ...` must expose:

- `PGPKey`
- `PGPKeyring`
- `PGPMessage`
- `PGPSignature`
- `PGPUID`
- `constants`
- `errors`

The documented helper objects `Fingerprint` and `SignatureVerification` must be importable from `pgpy.types`.

Constants must be importable from `pgpy.constants`. Exceptions must be importable from `pgpy.errors`. PGPy has no public command-line entry point in this specification.

## Public API
### Core Imports
```python
import pgpy
from pgpy import PGPKey, PGPKeyring, PGPMessage, PGPSignature, PGPUID
from pgpy import constants, errors
from pgpy.constants import (
    Backend, EllipticCurveOID, ECPointFormat, PacketTag,
    SymmetricKeyAlgorithm, PubKeyAlgorithm, CompressionAlgorithm,
    HashAlgorithm, RevocationReason, ImageEncoding, SignatureType,
    KeyServerPreferences, S2KGNUExtension, SecurityIssues,
    String2KeyType, TrustLevel, KeyFlags, Features,
    RevocationKeyClass, NotationDataFlags, TrustFlags,
)
from pgpy.errors import (
    PGPError, PGPEncryptionError, PGPDecryptionError,
    PGPIncompatibleECPointFormatError,
    PGPOpenSSLCipherNotSupportedError,
    PGPInsecureCipherError, WontImplementError,
)
from pgpy.types import Fingerprint, SignatureVerification
```

### Constants
All public constants are enum classes. Their members must be addressable by name and by their OpenPGP numeric value. Flag-style enums must support set membership and bitwise composition where OpenPGP flags are used.

- `Backend`: `OpenSSL`
- `EllipticCurveOID`: `Invalid`, `Curve25519`, `Ed25519`, `NIST_P256`, `NIST_P384`, `NIST_P521`, `Brainpool_P256`, `Brainpool_P384`, `Brainpool_P512`, `SECP256K1`
- `ECPointFormat`: `Standard`, `Native`, `OnlyX`, `OnlyY`
- `PacketTag`: `Invalid`, `PublicKeyEncryptedSessionKey`, `Signature`, `SymmetricKeyEncryptedSessionKey`, `OnePassSignature`, `SecretKey`, `PublicKey`, `SecretSubKey`, `CompressedData`, `SymmetricallyEncryptedData`, `Marker`, `LiteralData`, `Trust`, `UserID`, `PublicSubKey`, `UserAttribute`, `SymmetricallyEncryptedIntegrityProtectedData`, `ModificationDetectionCode`
- `SymmetricKeyAlgorithm`: `Plaintext`, `IDEA`, `TripleDES`, `CAST5`, `Blowfish`, `AES128`, `AES192`, `AES256`, `Twofish256`, `Camellia128`, `Camellia192`, `Camellia256`
- `PubKeyAlgorithm`: `Invalid`, `RSAEncryptOrSign`, `RSAEncrypt`, `RSASign`, `ElGamal`, `DSA`, `ECDH`, `ECDSA`, `FormerlyElGamalEncryptOrSign`, `DiffieHellman`, `EdDSA`
- `CompressionAlgorithm`: `Uncompressed`, `ZIP`, `ZLIB`, `BZ2`
- `HashAlgorithm`: `Invalid`, `MD5`, `SHA1`, `RIPEMD160`, `_reserved_1`, `_reserved_2`, `_reserved_3`, `_reserved_4`, `SHA256`, `SHA384`, `SHA512`, `SHA224`
- `RevocationReason`: `NotSpecified`, `Superseded`, `Compromised`, `Retired`, `UserID`
- `ImageEncoding`: `Unknown`, `JPEG`
- `SignatureType`: `BinaryDocument`, `CanonicalDocument`, `Standalone`, `Generic_Cert`, `Persona_Cert`, `Casual_Cert`, `Positive_Cert`, `Attestation`, `Subkey_Binding`, `PrimaryKey_Binding`, `DirectlyOnKey`, `KeyRevocation`, `SubkeyRevocation`, `CertRevocation`, `Timestamp`, `ThirdParty_Confirmation`
- `KeyServerPreferences`: `NoModify`
- `S2KGNUExtension`: `NoSecret`, `Smartcard`
- `SecurityIssues`: `OK`, `WrongSig`, `Expired`, `Disabled`, `Revoked`, `Invalid`, `BrokenAsymmetricFunc`, `HashFunctionNotCollisionResistant`, `HashFunctionNotSecondPreimageResistant`, `AsymmetricKeyLengthIsTooShort`, `InsecureCurve`, `NoSelfSignature`
- `String2KeyType`: `Simple`, `Salted`, `Reserved`, `Iterated`, `GNUExtension`
- `TrustLevel`: `Unknown`, `Expired`, `Undefined`, `Never`, `Marginal`, `Fully`, `Ultimate`
- `KeyFlags`: `Certify`, `Sign`, `EncryptCommunications`, `EncryptStorage`, `Split`, `Authentication`, `MultiPerson`
- `Features`: `ModificationDetection`
- `RevocationKeyClass`: `Sensitive`, `Normal`
- `NotationDataFlags`: `HumanReadable`
- `TrustFlags`: `Revoked`, `SubRevoked`, `Disabled`, `PendingCheck`

`SymmetricKeyAlgorithm.gen_key()` returns random bytes of the required key length, and `gen_iv()` returns random bytes of the required block size. `SymmetricKeyAlgorithm.is_insecure` returns `True` for `IDEA`. `SymmetricKeyAlgorithm.is_supported` returns whether the cipher backend is usable. Unsupported symmetric ciphers must raise `PGPEncryptionError` during encryption.

`PubKeyAlgorithm.can_gen`, `can_encrypt`, `can_sign`, and `deprecated` return booleans describing supported key generation and operation categories. `PubKeyAlgorithm.validate_params(size)` returns a `SecurityIssues` value for the supplied size or curve. Invalid generation parameters must raise `ValueError` or `NotImplementedError` through `PGPKey.new`.

`CompressionAlgorithm.compress(data)` and `decompress(data)` return transformed bytes for `ZIP`, `ZLIB`, and `BZ2`, and return input bytes unchanged for `Uncompressed`. Unsupported compression values raise `NotImplementedError`.

`HashAlgorithm.hasher`, `digest_size`, `tuned_count`, and `is_considered_secure` expose hash behavior. `is_considered_secure` returns `SecurityIssues.OK` for collision-resistant hashes and returns `SecurityIssues` flags with a warning for weak hashes.

`SecurityIssues.causes_signature_verify_to_fail` returns `True` for issues that make verification false: wrong signature, expired, disabled, invalid, and missing self-signature conditions.

### Main Classes
```python
PGPMessage()
PGPMessage.new(message, *, file=False, cleartext=False, sensitive=False,
               format=None, compression=CompressionAlgorithm.ZIP,
               encoding=None)
PGPMessage.from_file(filename)
PGPMessage.from_blob(blob)
PGPMessage.parse(packet)
PGPMessage.encrypt(passphrase, sessionkey=None, **prefs)
PGPMessage.decrypt(passphrase)
```

```python
PGPKey()
PGPKey.new(key_algorithm, key_size, created=None)
PGPKey.from_file(filename)
PGPKey.from_blob(blob)
PGPKey.parse(data)
PGPKey.add_uid(uid, selfsign=True, **prefs)
PGPKey.get_uid(search)
PGPKey.del_uid(search)
PGPKey.add_subkey(key, **prefs)
PGPKey.protect(passphrase, enc_alg, hash_alg)
PGPKey.unlock(passphrase)
PGPKey.sign(subject, **prefs)
PGPKey.certify(subject, level=SignatureType.Generic_Cert, **prefs)
PGPKey.revoke(target, **prefs)
PGPKey.revoker(revoker, **prefs)
PGPKey.bind(key, **prefs)
PGPKey.verify(subject, signature=None)
PGPKey.encrypt(message, sessionkey=None, **prefs)
PGPKey.decrypt(message)
```

```python
PGPSignature()
PGPSignature.new(sigtype, pkalg, halg, signer, created=None)
PGPSignature.from_file(filename)
PGPSignature.from_blob(blob)
PGPSignature.parse(packet)
PGPSignature.attests_to(othersig)
```

```python
PGPUID()
PGPUID.new(pn, comment="", email="")
PGPUID.attested_to(certifications)
```

```python
PGPKeyring(*args)
PGPKeyring.load(*args)
PGPKeyring.key(identifier)
PGPKeyring.fingerprints(keyhalf="any", keytype="any")
PGPKeyring.unload(key)
```

```python
Fingerprint(content)
SignatureVerification()
```

### Common Object Properties
Every `PGPKey`, `PGPMessage`, and `PGPSignature` instance must expose `ascii_headers`, an ordered mapping of ASCII armor headers. Setting `charset` on these objects must normalize the supplied codec name and store it as the `Charset` armor header; an invalid codec raises the codec lookup error.

`PGPMessage` properties:

- `message` returns the cleartext string, literal contents, or encrypted packet object according to `type`.
- `type` returns one of `cleartext`, `literal`, or `encrypted`.
- `filename` returns the stored literal filename, `_CONSOLE` for sensitive literal messages, or an empty string.
- `is_compressed`, `is_encrypted`, `is_sensitive`, and `is_signed` return booleans.
- `signatures` returns the attached signature objects.
- `signers`, `encrypters`, and `issuers` return key ID sets derived from attached signatures and encrypted session keys.

`PGPKey` properties:

- `created`, `expires_at`, `fingerprint`, `key_algorithm`, and `key_size` return the key metadata.
- `is_public`, `is_primary`, `is_protected`, `is_unlocked`, and `is_expired` return booleans for the key state.
- `pubkey` returns the public half of a private key and returns the object itself for a public key.
- `userids` returns `PGPUID` user IDs; `userattributes` returns `PGPUID` user attributes.
- `subkeys` returns an ordered mapping keyed by 16-character subkey ID.
- `signers`, `self_signatures`, `revocation_signatures`, and `revocation_keys` return signature-derived views.
- `_require_usage_flags` defaults to `True`; setting it to `False` must make usage-flag failures log or warn instead of raising `PGPError`.

`PGPSignature` properties:

- `type`, `created`, `expires_at`, `is_expired`, `signer`, `signer_fingerprint`, `key_algorithm`, and `hash_algorithm` return signature metadata.
- `cipherprefs`, `hashprefs`, `compprefs`, `key_flags`, `keyserverprefs`, `features`, `notation`, and `intended_recipients` return preference and notation data, using empty collections when absent.
- `keyserver`, `policy_uri`, and `signer_fingerprint` return empty strings when absent.
- `exportable` and `revocable` return `True` unless the signature explicitly says otherwise.
- `key_expiration`, `revocation_reason`, and `revocation_key` return the corresponding signature subpacket data or `None`.
- `attested_certifications` returns attested certification digests only for attestation signatures; other signature types return an empty set.

`PGPUID` properties:

- `name`, `comment`, `email`, and `userid` return user ID fields.
- `image` returns image bytes for a user attribute and returns `None` for a user ID.
- `is_uid`, `is_ua`, and `is_primary` return booleans.
- `selfsig` returns the most recent self-signature for the user ID or user attribute, or `None`.
- `signers`, `third_party_certifications`, and `attested_third_party_certifications` return signature-derived views.
- Formatting a user ID with `"{:s}".format(uid)` returns `name`, `name (comment)`, `name <email>`, or `name (comment) <email>` according to present fields. Formatting a user attribute raises `NotImplementedError`.

`Fingerprint` is a `str` subclass. Construction must uppercase input and remove spaces. Non-hexadecimal content raises `ValueError`. `keyid` returns the last 16 hex characters, and `shortid` returns the last 8. Equality with strings, bytes, bytearrays, and other `Fingerprint` instances must ignore spaces and must return true for matching full fingerprint, key ID, or short ID.

`SignatureVerification` represents the result of `PGPKey.verify`. `bool(result)` returns whether all collected signatures verified or had only non-failing security issues. `len(result)` returns the number of signature-subject records. `signature in result` and `subject in result` return membership against collected records. `good_signatures` and `bad_signatures` return generators of namedtuples with `issues`, `by`, `signature`, and `subject`. `left & right` merges two `SignatureVerification` objects into `left`; a non-`SignatureVerification` right operand raises `TypeError`.

## Product State Model
PGPy exposes the same OpenPGP data through three public projections:

1. The object graph projection: `PGPKey`, `PGPUID`, `PGPMessage`, `PGPSignature`, `Fingerprint`, and `SignatureVerification` instances and their properties.
2. The serialized projection: `str(obj)`, `bytes(obj)`, `from_file`, `from_blob`, and `parse`.
3. The operation projection: signatures, encrypted messages, decrypted messages, verification aggregates, and keyring selections returned by public methods.

State invariants before the subsystem details:

- A key loaded through `PGPKey.from_blob` must expose the same `fingerprint` through the object graph that a later binary or armored export represents.
- A message returned by `PGPMessage.decrypt` must expose plaintext through `message`, `type`, `is_encrypted`, and `bytes()` consistently.
- A signature attached with `message |= signature`, `uid |= signature`, or `key |= signature` must appear through the corresponding signature and signer views and must be included in exported data when it is exportable.
- A public key returned by `private_key.pubkey` must share the fingerprint, user IDs, user attributes, subkeys, and exportable signatures of the private key while reporting `is_public is True`.

## Behavioral Sections
### Loading, Parsing, and Exporting
`from_file(filename)` must read binary data from the given file path and parse it exactly as `from_blob` parses the same bytes. File loading raises `OSError` from normal file access failures, `ValueError` for the wrong ASCII armor block type, and `PGPError` for de-armoring or packet parsing failures.

`from_blob(blob)` must accept `str`, `bytes`, `bytearray`, and compatible text input. It raises `TypeError` when the value is not convertible to bytes for parsing. `PGPMessage.from_blob` returns a `PGPMessage`; `PGPSignature.from_blob` returns a `PGPSignature`; `PGPKey.from_blob` returns `(key, others)`.

`PGPKey.from_blob` and `PGPKey.from_file` must return a two-element tuple. The first element is the first parsed key. The second element is an ordered mapping of additional parsed keys keyed by `(keyid, is_public)`, where `keyid` is the 16-character key ID string and `is_public` is a boolean.

`parse(data)` on `PGPKey`, `PGPMessage`, and `PGPSignature` must mutate an empty object with parsed content. It raises `ValueError` when ASCII armor is present with the wrong block type. It raises `PGPError` when armor decoding, base64 payload decoding, or packet parsing fails. An incorrect ASCII armor CRC must emit a warning and continue parsing the decoded body.

`str(obj)` must return ASCII-armored OpenPGP data with ordered armor headers. `bytes(obj)` must return binary OpenPGP packet data. Non-exportable signatures must not appear in either serialized form.

### Messages
`PGPMessage.new(message, file=False, cleartext=False, sensitive=False, format=None, compression=CompressionAlgorithm.ZIP, encoding=None)` returns a new `PGPMessage`.

When `file=True` and `message` names an existing file, PGPy must read that file as bytes, store the basename as `filename`, and store the file modification time in the literal data. When `file=True` and the named file does not exist, PGPy must treat `message` as caller-supplied message content. File access failures raise the standard file exception.

When `cleartext=True`, the returned message must have `type == "cleartext"`, `is_compressed is False`, `is_sensitive is False`, and `message` as decoded text. Cleartext export with `str(message)` must canonicalize and dash-escape the message text and include inline signatures when present.

When `cleartext=False`, the returned message must have `type == "literal"`. Text input must produce UTF-8 text format by default. ASCII byte content must produce text format by default, and non-ASCII bytes must produce binary format by default. The `format` keyword must set the literal format when supplied. The `encoding` keyword must decode textual byte input and set the armor `Charset` header.

When `sensitive=True` for a literal message, `filename` must return `_CONSOLE` and `is_sensitive` must return `True`. When `sensitive=False`, a message made from direct content must use an empty filename and a message made from a file must use the file basename.

`compression` must default to `CompressionAlgorithm.ZIP`. `CompressionAlgorithm.Uncompressed` must make `is_compressed` return `False`; other supported compression algorithms must make it return `True`.

`message.encrypt(passphrase, sessionkey=None, **prefs)` returns a new encrypted `PGPMessage`. The optional `cipher` preference defaults to `SymmetricKeyAlgorithm.AES256`; the optional `hash` preference defaults to `HashAlgorithm.SHA256`. If `sessionkey` is `None`, the selected cipher must generate a session key. Insecure cipher selection raises `PGPInsecureCipherError`. Unsupported cipher selection raises `PGPEncryptionError`. A session key with an invalid type raises `TypeError`.

`message.decrypt(passphrase)` returns a new decrypted `PGPMessage`. It raises `PGPError` when the message is not encrypted. It raises `PGPDecryptionError` when no passphrase session key decrypts successfully, when the passphrase is wrong, or when the encrypted message uses an unsupported symmetric algorithm.

### Keys and User IDs
`PGPKey.new(key_algorithm, key_size, created=None)` returns a new private primary key. It must support valid generation requests for RSA, DSA, ECDSA, ECDH, and EdDSA key algorithms. RSA deprecated generation algorithms must emit a warning and generate `RSAEncryptOrSign`. Unsupported algorithms raise `NotImplementedError`. Invalid sizes or unsupported curves raise `ValueError`. A supplied `created` datetime must become the key creation time.

A new key without a user ID is incomplete for normal key actions. Signing, encryption, decryption, certification, revocation, and binding actions on an empty or incomplete key raise `PGPError`, except self-certification performed by `add_uid`.

`PGPUID.new(pn, comment="", email="")` returns a user ID when `pn` is text and returns a user attribute when `pn` is a `bytearray`. For text user IDs, comment and email must be included only when non-empty. For image user attributes, comment and email must be ignored.

`key.add_uid(uid, selfsign=True, **prefs)` must attach the `PGPUID` to the key. When `selfsign=True`, it must create and attach a positive self-certification using the supplied certification preferences. When `selfsign=False`, it must attach the UID without creating a self-signature. Invalid signing preconditions raise `PGPError`.

Self-certification preferences include `usage`, `ciphers`, `hashes`, `compression`, `key_expiration`, `keyserver`, `keyserver_flags`, and `primary`. These preferences must be visible through the resulting `PGPSignature` properties. `Features.ModificationDetection` must be present on certification signatures that carry PGPy feature data.

`key.get_uid(search)` returns the first user ID whose name, comment, or email exactly matches `search`; it returns `None` when no user ID matches. On a subkey, `get_uid` must delegate to the parent key. `key.del_uid(search)` must remove the matching user ID from the key and must raise `KeyError` when no user ID matches.

`key.add_subkey(subkey, **prefs)` must attach a private key as a subkey, bind it to the primary key, and make it visible in `subkeys` by key ID. It raises `PGPError` when called on a public primary key, when the supplied subkey is public, or when the supplied key already has subkeys.

`key.bind(subkey, **prefs)` returns a subkey binding signature for a primary/subkey pair. A signing-capable subkey must have a cross-signature unless `usage` excludes signing. Missing required cross-signature conditions raise `PGPError`.

`key.protect(passphrase, enc_alg, hash_alg)` must passphrase-protect private key material with the selected algorithms. It must warn and leave the key unchanged when called on a public key. It must warn and leave the key unchanged when the key is already protected and locked. It must protect the primary key and its subkeys together.

`key.unlock(passphrase)` is a context manager. It yields the same key object. For a protected private key, entering the context must decrypt private key material and make `is_unlocked` true; exiting the context must clear decrypted private key material and make `is_unlocked` false. A wrong passphrase raises `PGPDecryptionError`. Unlocking a public key or an unprotected private key must warn and yield the key without changing private material.

`key.pubkey` must return a public key object for a private key and must return `self` for an already-public key. Assigning `pubkey` on a public key raises `TypeError`; assigning a private key as the public sibling raises `TypeError`; assigning a public key with a different fingerprint raises `ValueError`; assigning a second public sibling raises `ValueError`.

### Signing, Certification, Revocation, and Verification
`key.sign(subject, **prefs)` returns a `PGPSignature`. It must raise `PGPError` when the key is public, protected but locked, incomplete, missing required usage flags, or otherwise not usable for signing. If the selected hash is outside key preferences, it must warn and sign.

Signing text, bytes, bytearrays, or literal messages must create a `SignatureType.BinaryDocument` signature. Signing a cleartext message must create a `SignatureType.CanonicalDocument` signature. Signing `None` with no additional signature subpackets must create a `SignatureType.Timestamp` signature. Signing `None` with notation or other signed subpacket data must create a `SignatureType.Standalone` signature.

Signature preferences accepted by `sign`, `certify`, `revoke`, and `bind` include `hash`, `expires`, `notation`, `policy_uri`, `revocable`, `user`, `created`, `intended_recipients`, and `include_issuer_fingerprint`. These preferences must be reflected through `PGPSignature` properties. Invalid intended-recipient entries must warn and be ignored.

`key.certify(subject, level=SignatureType.Generic_Cert, **prefs)` returns a certification signature. Certifying a `PGPUID` must use the requested certification level. Certifying a `PGPKey` must create `SignatureType.DirectlyOnKey`. It raises `PGPError` for the same private-key and usage preconditions as signing.

For self-certifications, `certify` must honor `usage`, `ciphers`, `hashes`, `compression`, `key_expiration`, `attested_certifications`, `keyserver`, `keyserver_flags`, and `primary`. For non-self-certifications, it must honor `trust`, `regex`, and `exportable`. Invalid attested certification elements must warn and be ignored.

`key.revoke(target, **prefs)` returns a revocation signature. Revoking a primary key must create `SignatureType.KeyRevocation`; revoking a subkey must create `SignatureType.SubkeyRevocation`; revoking a user ID must create `SignatureType.CertRevocation`. `reason` defaults to `RevocationReason.NotSpecified`, and `comment` defaults to an empty string. Unsupported target types raise `TypeError`.

`key.revoker(revoker, **prefs)` returns a direct-key signature that marks another key as a revocation key. The `sensitive` preference must set the sensitive revocation-key class flag. The resulting signature must be non-revocable. Private-key precondition failures raise `PGPError`.

`key.verify(subject, signature=None)` returns `SignatureVerification`. It accepts `None`, text, bytes, bytearrays, `PGPMessage`, `PGPKey`, `PGPUID`, and `PGPSignature` subjects. Detached verification uses the supplied `PGPSignature`; embedded verification collects applicable signatures from messages, keys, user IDs, user attributes, and subkeys. An unsupported subject type raises `TypeError`. A non-`PGPSignature` detached signature raises `TypeError`. If no applicable signatures are found, it raises `PGPError`.

A successful verification result must be truthy and must include the verified signature and subject in membership checks. A cryptographically wrong signature must return a falsy `SignatureVerification` rather than raising. Unsupported public-key verification algorithms raise `NotImplementedError`.

### Public-Key Encryption and Decryption
`key.encrypt(message, sessionkey=None, **prefs)` returns a new encrypted `PGPMessage`. It requires a public encryption-capable key or subkey and a `PGPMessage` input. It raises `PGPError` when the key is incomplete, private where a public key is required, lacks required encryption usage flags, or otherwise fails key-action preconditions. It raises `PGPEncryptionError` when encryption fails.

The optional `cipher` preference selects the symmetric cipher. The optional `user` preference selects a user ID for preference lookup and usage validation. If the selected cipher or message compression is outside the recipient preferences, encryption must warn and continue. If `sessionkey` is `None`, the selected cipher must generate a session key. Re-encrypting an already encrypted `PGPMessage` must add another recipient session key.

`key.decrypt(message)` returns a new decrypted `PGPMessage`. It requires a private, unlocked key that matches one of the encrypted session keys. If the message is not encrypted, it must warn and return the original message. If a matching subkey is present, the primary key must delegate decryption to that subkey. If no matching key or subkey is present, it raises `PGPError`. Other decryption failures raise `PGPDecryptionError`.

### Keyrings
`PGPKeyring(*args)` must create an in-memory keyring and load any initial arguments using `load`.

`keyring.load(*args)` must accept `PGPKey` objects, filenames, blobs, and nested lists or tuples of those values. It returns a list of unique `Fingerprint` objects loaded in that operation, including subkeys. It must index each loaded primary key and subkey by fingerprint, key ID, short ID, user ID name, comment, and email. Invalid key input raises the same exception as `PGPKey.from_file` or `PGPKey.from_blob`.

`identifier in keyring` must return whether the identifier is a known alias. String identifiers must match with or without spaces in fingerprints.

`len(keyring)` returns the number of loaded key objects, including subkeys. Iterating a keyring yields loaded key objects.

`keyring.key(identifier)` is a context manager that yields a loaded `PGPKey`. A `PGPMessage` identifier must select a key matching one of the message issuers or encrypters. A `PGPSignature` identifier must select a key matching the signature signer. String and `Fingerprint` identifiers must select by alias. Missing identifiers raise `KeyError`.

`keyring.fingerprints(keyhalf="any", keytype="any")` returns a set of fingerprints. `keyhalf` accepts `any`, `public`, and `private`. `keytype` accepts `any`, `primary`, and `sub`. Unknown filter strings return an empty set rather than raising.

`keyring.unload(key)` must remove the selected key and, for a primary key, its subkeys. Removed aliases must no longer match unless another loaded key still owns the same alias. The method requires a `PGPKey`; other input raises `AssertionError`.

## Error Semantics
- `PGPError` raises for general PGPy operation failures: empty keys, incomplete keys, wrong key for decryption, no signatures to verify, public/private key precondition failures, locked protected-key use, usage-flag failures, wrong parsed packet category, and non-encrypted passphrase-message decryption.
- `PGPEncryptionError` raises when encryption fails because the selected cipher or backend is unsupported or encryption cannot complete.
- `PGPDecryptionError` raises when a passphrase or private key fails to decrypt protected data, when a protected private key receives the wrong unlock passphrase, or when encrypted data uses an unsupported decryption path.
- `PGPInsecureCipherError` raises when an insecure cipher such as `SymmetricKeyAlgorithm.IDEA` is selected for encryption.
- `PGPOpenSSLCipherNotSupportedError` represents OpenSSL cipher support failures.
- `PGPIncompatibleECPointFormatError` raises when an elliptic-curve point encoding is incompatible with the curve type.
- `WontImplementError` represents a feature that PGPy intentionally does not implement.
- `ValueError` raises for wrong ASCII armor block types, invalid fingerprint text, invalid key sizes, unsupported curves, and incompatible public-key sibling fingerprints.
- `TypeError` raises for unsupported operand attachment, unsupported verification input types, invalid detached-signature types, invalid public-key sibling assignment types, invalid `SignatureVerification` merge operands, and invalid session-key types.
- `KeyError` raises for missing user IDs in `del_uid` and missing aliases in `PGPKeyring.key`.
- `NotImplementedError` raises for unsupported public-key algorithms, unsupported compression values, unsupported verification algorithms, user-attribute formatting, and explicitly unimplemented OpenPGP behaviors.
- Warnings must be emitted, rather than exceptions, for public-key protect/unlock requests, unlocking an unprotected key, protecting an already locked protected key, incorrect ASCII armor CRC, selected hash/cipher/compression outside preferences, non-encrypted private-key decryption input, and ignored optional attestation or intended-recipient entries.

## Cross-View Invariants
- A value returned by `PGPKey.fingerprint` must compare equal to the same key's full fingerprint string, 16-character key ID, and 8-character short ID through `Fingerprint` equality.
- A `PGPUID` added with `key.add_uid` must appear in `key.userids` or `key.userattributes`, must report the key as its parent-derived signing context, and must appear in exported key data when exportable.
- A signature returned by `key.sign(message)` and attached with `message |= signature` must make `message.is_signed` return `True`, must place the signature in `message.signatures`, and must make `message.signers` include the signer key ID.
- A message returned by passphrase encryption must return `is_encrypted is True`, `type == "encrypted"`, and decrypt with the same passphrase to a new message whose `message` property returns the original plaintext.
- A message returned by public-key encryption must include the recipient key ID in `encrypters`, and decrypting with the matching private key or matching private subkey must return the original message contents.
- A protected private key inside `with key.unlock(passphrase)` must return `is_unlocked is True`; after the context exits, the same key must return `is_unlocked is False`.
- A keyring that loads a key must return `True` for membership checks by fingerprint, key ID, short ID, and available user ID fields; after unloading the only key for an alias, the same alias must return `False`.
- A `SignatureVerification` returned by `verify` must agree across boolean value, `good_signatures` or `bad_signatures`, and membership checks for the verified signature and subject.
- A private key's `pubkey` projection must retain fingerprint, user IDs, user attributes, subkeys, and exportable signatures, and it must serialize as a public key block.

## Representative Workflows
### Generate a Key, Sign a Message, Verify, Encrypt, and Decrypt
```python
from datetime import timedelta

import pgpy
from pgpy.constants import (
    PubKeyAlgorithm, KeyFlags, HashAlgorithm,
    SymmetricKeyAlgorithm, CompressionAlgorithm,
)

key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
uid = pgpy.PGPUID.new("Example User", email="user@example.com")
key.add_uid(
    uid,
    usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
    hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384],
    ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES128],
    compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.Uncompressed],
    key_expiration=timedelta(days=365),
)

message = pgpy.PGPMessage.new("hello from PGPy")
signature = key.sign(message, notation={"purpose": "example"})
message |= signature

verification = key.pubkey.verify(message)
assert verification

encrypted = key.pubkey.encrypt(message, cipher=SymmetricKeyAlgorithm.AES256)
decrypted = key.decrypt(encrypted)
assert decrypted.message == "hello from PGPy"
```

### Protect and Temporarily Unlock a Private Key
```python
from pgpy.constants import SymmetricKeyAlgorithm, HashAlgorithm

key.protect("correct horse battery staple", SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
assert key.is_protected
assert not key.is_unlocked

with key.unlock("correct horse battery staple") as unlocked_key:
    assert unlocked_key is key
    assert unlocked_key.is_unlocked
    sig = unlocked_key.sign("signed text")

assert not key.is_unlocked
assert key.pubkey.verify("signed text", sig)
```

### Load Keys into a Keyring and Select by Message
```python
ring = pgpy.PGPKeyring()
loaded = ring.load(key, key.pubkey)
assert key.fingerprint in loaded
assert key.fingerprint in ring
assert key.fingerprint.keyid in ring

encrypted = key.pubkey.encrypt(pgpy.PGPMessage.new("keyring message"))
with ring.key(encrypted) as selected:
    assert selected.fingerprint == key.fingerprint
```

## Non-Goals
- Packet classes, packet field classes, subpacket classes, and private helper modules are not part of this public specification.
- Exact `repr()` strings, object memory identities, private storage containers, and private packet ordering helpers are not part of this public specification.
- A public CLI is not part of this public specification.
- HKP keyserver retrieval, keyserver upload, DNS key lookup, and GnuPG keybox parsing are not part of this public specification.
- Twofish encryption support, insecure-cipher encryption support, and unsupported OpenPGP algorithms are not required beyond the documented exceptions.
- Matching exact warning text is not required; warning categories and trigger conditions are part of the behavior.
- Interoperability checks against an external `gpg` executable are not part of this specification.

## Evaluation Notes
Evaluation should exercise the public API described above: importability, enum and exception availability, object creation, parsing, serialization, message state, key and user ID state, signing, verification, passphrase encryption, public-key encryption, keyring selection, documented warnings, and documented exception classes.

Scoring should be behavioral. A correct implementation receives credit for returning the documented object types, state transitions, serialized forms, booleans, warnings, and exception classes. Evaluation should not require private module names, exact private helper structures, exact `repr()` strings, local file layouts, or external service availability.
