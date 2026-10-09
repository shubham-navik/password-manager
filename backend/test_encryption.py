from app.security.encryption import encrypt_value, decrypt_value


def test_encrypt_and_decrypt():
    original = "MySuperSecretPassword123!"

    encrypted = encrypt_value(original)

    assert isinstance(encrypted, bytes)
    assert encrypted != original.encode("utf-8")
    assert decrypt_value(encrypted) == original


def test_same_value_produces_different_ciphertext():
    original = "MySuperSecretPassword123!"

    encrypted_1 = encrypt_value(original)
    encrypted_2 = encrypt_value(original)

    assert encrypted_1 != encrypted_2
    assert decrypt_value(encrypted_1) == original
    assert decrypt_value(encrypted_2) == original