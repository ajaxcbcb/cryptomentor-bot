"""
Verifikasi Telegram Login Widget data.
Docs: https://core.telegram.org/widgets/login#checking-authorization
"""
import hashlib
import hmac
from typing import Dict, Any, Tuple
from config import TELEGRAM_BOT_TOKEN

_VALID_AUTH_FIELDS = {"id", "first_name", "last_name", "username", "photo_url", "auth_date"}

REASON_OK = "ok"
REASON_MISSING_HASH = "missing_hash"
REASON_BOT_TOKEN_MISSING = "bot_token_missing"
REASON_MISSING_ID = "missing_id"
REASON_MISSING_AUTH_DATE = "missing_auth_date"
REASON_INVALID_SIGNATURE = "invalid_signature"


def verify_telegram_auth_detailed(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify Telegram Login Widget hash with explicit reason code.

    Returns:
        tuple[is_valid, reason_code]
    """
    received_hash = str(data.get("hash") or "").strip()
    if not received_hash:
        return False, REASON_MISSING_HASH

    bot_token = str(TELEGRAM_BOT_TOKEN or "").strip()
    if not bot_token:
        return False, REASON_BOT_TOKEN_MISSING

    # Telegram signatures only include these specific fields.
    # We must exclude custom fields like 'referred_by' which we add in the frontend.
    check_fields = {
        k: str(v) for k, v in data.items()
        if k in _VALID_AUTH_FIELDS and v is not None
    }
    if "id" not in check_fields:
        return False, REASON_MISSING_ID
    if "auth_date" not in check_fields:
        return False, REASON_MISSING_AUTH_DATE

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(check_fields.items())
    )

    # Secret key = SHA256 dari bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # HMAC-SHA256
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return False, REASON_INVALID_SIGNATURE
    return True, REASON_OK


def verify_telegram_auth(data: Dict[str, Any]) -> bool:
    """
    Verifikasi hash dari Telegram Login Widget.
    Telegram mengirim: id, first_name, username, photo_url, auth_date, hash
    """
    ok, _reason = verify_telegram_auth_detailed(data)
    return ok
