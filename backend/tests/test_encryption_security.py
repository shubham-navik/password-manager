import pytest

from app.security.encryption import (
    VaultEncryptionError,
    decrypt_value,
    encrypt_value,
)


def test_encrypted_value_does_not_contain_plaintext():
    password = "MySecretPassword123!"

    encrypted = encrypt_value(password)

    assert password.encode() not in encrypted


def test_tampered_ciphertext_is_rejected():
    encrypted = bytearray(encrypt_value("MySecretPassword123!"))

    encrypted[-1] ^= 1

    with pytest.raises(VaultEncryptionError):
        decrypt_value(bytes(encrypted))


def test_truncated_ciphertext_is_rejected():
    with pytest.raises(VaultEncryptionError):
        decrypt_value(b"too-short")


def test_different_values_cannot_be_interchanged():
    encrypted = encrypt_value("FirstPassword123!")
    another_encrypted = encrypt_value("SecondPassword456!")

    assert decrypt_value(encrypted) == "FirstPassword123!"
    assert decrypt_value(another_encrypted) == "SecondPassword456!"