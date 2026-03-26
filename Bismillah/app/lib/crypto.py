"""
AES-256-GCM encryption helper untuk menyimpan API secret user.
Key diambil dari ENCRYPTION_KEY env (base64url, 32 bytes).
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    raw = os.getenv("ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError("ENCRYPTION_KEY tidak di-set di environment")
    # padding base64url jika perlu
    padded = raw + "=" * (-len(raw) % 4)
    key = base64.urlsafe_b64decode(padded)
    if len(key) != 32:
        raise RuntimeError(f"ENCRYPTION_KEY harus 32 bytes, dapat {len(key)}")
    return key


def encrypt(plaintext: str) -> str:
    """Enkripsi string → base64url(nonce[12] + ciphertext+tag)"""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt(token: str) -> str:
    """Dekripsi base64url(nonce+ciphertext) → plaintext string"""
    key = _get_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
