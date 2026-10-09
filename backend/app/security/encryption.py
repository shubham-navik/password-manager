import base64
import binascii
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


class VaultEncryptionError(Exception):
    """Raised when vault data cannot be decrypted or is invalid."""


def _get_encryption_key() -> bytes:
    try:
        key = base64.urlsafe_b64decode(
            settings.VAULT_ENCRYPTION_KEY.encode("ascii")
        )
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise RuntimeError("Invalid vault encryption key encoding") from exc

    if len(key) != 32:
        raise RuntimeError("Vault encryption key must decode to exactly 32 bytes")

    return key


def encrypt_value(value: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError("Value to encrypt must be a string")

    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(_get_encryption_key())

    ciphertext = aesgcm.encrypt(
        nonce,
        value.encode("utf-8"),
        None,
    )

    return nonce + ciphertext


def decrypt_value(encrypted_value: bytes) -> str:
    if len(encrypted_value) < 28:
        raise VaultEncryptionError("Encrypted value is invalid")

    nonce = encrypted_value[:12]
    ciphertext = encrypted_value[12:]

    aesgcm = AESGCM(_get_encryption_key())

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise VaultEncryptionError(
            "Encrypted value failed authentication"
        ) from exc

    return plaintext.decode("utf-8")