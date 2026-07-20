import warnings
from pathlib import Path

import pytest

from pgpy import PGPKey, PGPKeyring, PGPMessage, PGPUID
from pgpy.constants import (
    CompressionAlgorithm,
    HashAlgorithm,
    KeyFlags,
    PubKeyAlgorithm,
    SymmetricKeyAlgorithm,
)
from pgpy.errors import PGPDecryptionError, PGPError
from pgpy.types import Fingerprint


DATA_DIR = Path(__file__).with_name("data")


def _load_key(name):
    return PGPKey.from_file(str(DATA_DIR / "keys" / name))[0]


def _generated_key():
    key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 1024)
    uid = PGPUID.new("Native Test User", comment="workflow", email="native@example.test")
    key.add_uid(
        uid,
        usage={
            KeyFlags.Certify,
            KeyFlags.Sign,
            KeyFlags.EncryptCommunications,
            KeyFlags.EncryptStorage,
        },
        hashes=[HashAlgorithm.SHA256],
        ciphers=[SymmetricKeyAlgorithm.AES256],
        compression=[CompressionAlgorithm.ZLIB],
    )
    return key, uid


def test_message_text_cleartext_and_binary_views():
    literal = PGPMessage.new("hello from PGPy", compression=CompressionAlgorithm.ZLIB)
    cleartext = PGPMessage.new("signed-looking text", cleartext=True)
    binary = PGPMessage.new(b"\x00\x01payload")

    assert literal.type == "literal"
    assert literal.message == "hello from PGPy"
    assert literal.is_compressed
    assert cleartext.type == "cleartext"
    assert cleartext.message == "signed-looking text"
    assert binary.message == b"\x00\x01payload"


def test_message_symmetric_encryption_roundtrip():
    original = PGPMessage.new("symmetric secret", compression=CompressionAlgorithm.ZLIB)
    encrypted = original.encrypt("correct horse battery staple")

    assert encrypted is not original
    assert encrypted.is_encrypted
    assert encrypted.type == "encrypted"
    decrypted = encrypted.decrypt("correct horse battery staple")
    assert decrypted.message == original.message
    assert decrypted.type == original.type


def test_key_generation_uid_and_export_roundtrip():
    key, uid = _generated_key()

    assert uid in key
    assert not key.is_public
    assert key.is_primary
    assert key.fingerprint
    reloaded, remainder = PGPKey.from_blob(str(key))
    assert hasattr(remainder, "items")
    assert reloaded.fingerprint == key.fingerprint
    assert reloaded.get_uid("Native Test User").email == "native@example.test"


def test_sign_and_verify_text():
    private_key, _ = _generated_key()
    public_key = private_key.pubkey
    signature = private_key.sign("public behavioral contract")

    assert public_key.verify("public behavioral contract", signature)
    assert not public_key.verify("different text", signature)


def test_attach_and_verify_message_signature():
    private_key, _ = _generated_key()
    public_key = private_key.pubkey
    message = PGPMessage.new("attached signature")
    message |= private_key.sign(message)

    assert message.is_signed
    verification = public_key.verify(message)
    assert verification
    assert len(verification) == 1


def test_public_key_encrypt_decrypt_roundtrip():
    private_key, _ = _generated_key()
    public_key = private_key.pubkey
    message = PGPMessage.new("recipient secret")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        encrypted = public_key.encrypt(message, cipher=SymmetricKeyAlgorithm.AES256)
        decrypted = private_key.decrypt(encrypted)

    assert encrypted.is_encrypted
    assert decrypted.message == "recipient secret"


def test_protect_and_temporarily_unlock_private_key():
    key, _ = _generated_key()
    key.protect("local passphrase", SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)

    assert key.is_protected
    assert not key.is_unlocked
    with key.unlock("local passphrase") as unlocked:
        assert unlocked is key
        assert key.is_unlocked
        signature = key.sign("unlocked operation")
    assert not key.is_unlocked
    assert key.pubkey.verify("unlocked operation", signature)


def test_public_error_types_for_invalid_inputs():
    with pytest.raises(ValueError):
        Fingerprint("not-a-fingerprint")
    with pytest.raises(PGPError):
        PGPKey().sign("missing key material")
    with pytest.raises(TypeError):
        PGPUID.new("User") | object()


def test_wrong_password_and_wrong_private_key_errors():
    message = PGPMessage.new("password secret").encrypt("right password")
    with pytest.raises(PGPDecryptionError):
        message.decrypt("wrong password")

    recipient_private, _ = _generated_key()
    rsa_public = recipient_private.pubkey
    unrelated_private, _ = _generated_key()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        encrypted = rsa_public.encrypt(PGPMessage.new("wrong recipient"))
    with pytest.raises(PGPError):
        unrelated_private.decrypt(encrypted)


def test_keyring_selects_key_for_encrypted_message():
    private_key, _ = _generated_key()
    public_key = private_key.pubkey
    keyring = PGPKeyring(private_key)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        encrypted = public_key.encrypt(PGPMessage.new("keyring selection"))

    with keyring.key(encrypted) as selected:
        decrypted = selected.decrypt(encrypted)
    assert decrypted.message == "keyring selection"


def test_generated_key_sign_verify_encrypt_decrypt_workflow():
    key, _ = _generated_key()
    public_key = key.pubkey
    signature = key.sign("workflow text")
    assert public_key.verify("workflow text", signature)

    message = PGPMessage.new("workflow secret")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        encrypted = public_key.encrypt(message, cipher=SymmetricKeyAlgorithm.AES256)
        decrypted = key.decrypt(encrypted)
    assert decrypted.message == message.message


def test_cross_view_key_and_message_reparse():
    private_key, _ = _generated_key()
    key = private_key.pubkey
    from_text, text_remainder = PGPKey.from_blob(str(key))
    from_bytes, bytes_remainder = PGPKey.from_blob(bytes(key))
    assert from_text.fingerprint == from_bytes.fingerprint == key.fingerprint
    assert {item.fingerprint for item in text_remainder.values()} == {
        item.fingerprint for item in bytes_remainder.values()
    }

    message = PGPMessage.new("cross-view message")
    reparsed = PGPMessage.from_blob(str(message))
    assert reparsed.message == message.message
    assert bytes(reparsed) == bytes(message)
