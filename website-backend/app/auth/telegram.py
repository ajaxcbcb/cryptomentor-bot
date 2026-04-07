"""
Verifikasi Telegram Login Widget data.
Docs: https://core.telegram.org/widgets/login#checking-authorization
"""
import hashlib
import hmac
from typing import Dict, Any
from config import TELEGRAM_BOT_TOKEN


def verify_telegram_auth(data: Dict[str, Any]) -> bool:
    """
    Verifikasi hash dari Telegram Login Widget.
    Telegram mengirim: id, first_name, username, photo_url, auth_date, hash
    """
    received_hash = data.get("hash", "")
    if not received_hash:
        return False

    # Buat data-check-string: semua field kecuali hash, sorted, newline-separated
    # Semua nilai harus string
    check_fields = {k: str(v) for k, v in data.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(check_fields.items())
    )

    # Secret key = SHA256 dari bot token
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()

    # HMAC-SHA256
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_hash, received_hash)
