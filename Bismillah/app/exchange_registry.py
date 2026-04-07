"""
Exchange Registry — konfigurasi semua exchange yang didukung autotrade.
Tambah exchange baru cukup di sini.
"""

EXCHANGES = {
    "bitunix": {
        "name":         "Bitunix",
        "emoji":        "",
        "coming_soon":  False,
        "referral_url": "https://www.bitunix.com/register?vipCode=sq45",
        "referral_code": "sq45",
        "group_url":    "https://t.me/+pKKCinyKUQlhMjk1",
        "uid_label":    "Bitunix UID",
        "uid_help":     "Login to Bitunix → tap your profile photo → UID is shown below your name",
        "uid_example":  "123456789",
        "uid_min_len":  5,
        "requires_uid_verification": True,  # Bitunix perlu verifikasi UID referral
        "api_key_help": (
            "1️⃣ <b>Note/Label:</b> <code>CryptoMentor Bot</code> (or any name)\n"
            "2️⃣ <b>IP Address:</b> Leave <b>BLANK</b> — do not enter anything\n"
            "3️⃣ <b>Permissions:</b> Enable ✅ <b>Trade</b> only\n"
            "   ❌ Do NOT enable Withdraw or Transfer\n"
            "4️⃣ Click <b>Confirm</b> → verify via email/2FA\n"
            "5️⃣ Copy the <b>API Key</b> and <b>Secret Key</b>"
        ),
        "api_key_url":  "https://www.bitunix.com/account/api-management",
        "client_class": "BitunixAutoTradeClient",
        "client_module": "app.bitunix_autotrade_client",
    },
    "bybit": {
        "name":         "Bybit",
        "emoji":        "",
        "coming_soon":  True,
        "referral_url": "",
        "referral_code": "",
        "group_url":    None,
        "uid_label":    "Bybit UID",
        "uid_help":     "Login to Bybit → click your avatar → UID is shown below your username",
        "uid_example":  "12345678",
        "uid_min_len":  5,
        "requires_uid_verification": False,  # Bybit tidak perlu verifikasi UID referral
        "api_key_help": (
            "1️⃣ <b>Note/Label:</b> <code>CryptoMentor Bot</code> (or any name)\n"
            "2️⃣ <b>IP Address:</b> Leave <b>BLANK</b> — do not enter anything\n"
            "3️⃣ <b>Permissions:</b> Enable ✅ <b>Derivatives Trading</b> only\n"
            "   ❌ Do NOT enable Withdraw or Spot Trading\n"
            "4️⃣ Click <b>Submit</b> → verify via 2FA\n"
            "5️⃣ Copy the <b>API Key</b> and <b>Secret Key</b>"
        ),
        "api_key_url":  "https://www.bybit.com/app/user/api-management",
        "client_class": "BybitAutoTradeClient",
        "client_module": "app.bybit_autotrade_client",
    },
    "binance": {
        "name":         "Binance",
        "emoji":        "",
        "coming_soon":  True,
        "referral_url": "",
        "referral_code": "",
        "group_url":    None,
        "uid_label":    "Binance UID",
        "uid_help":     "Login to Binance → click your avatar → UID (User ID) is shown in your profile",
        "uid_example":  "123456789",
        "uid_min_len":  5,
        "requires_uid_verification": False,  # Binance tidak perlu verifikasi UID referral
        "api_key_help": (
            "1️⃣ <b>Label:</b> <code>CryptoMentor Bot</code> (or any name)\n"
            "2️⃣ <b>IP Access Restriction:</b> Select <b>Unrestricted</b>\n"
            "3️⃣ <b>Permissions:</b> Enable ✅ <b>Enable Futures</b> only\n"
            "   ❌ Do NOT enable Spot, Margin, or Withdrawals\n"
            "4️⃣ Click <b>Next</b> → verify via 2FA\n"
            "5️⃣ Copy the <b>API Key</b> and <b>Secret Key</b>"
        ),
        "api_key_url":  "https://www.binance.com/en/my/settings/api-management",
        "client_class": "BinanceAutoTradeClient",
        "client_module": "app.binance_autotrade_client",
    },
    "bingx": {
        "name":         "BingX",
        "emoji":        "🔵",
        "coming_soon":  False,
        "referral_url": "https://bingx.pro/partner/CMAI",
        "referral_code": "CMAI",
        "group_url":    None,
        "uid_label":    "BingX UID",
        "uid_help":     "Login ke BingX → tap avatar/foto profil kamu → UID tertera di halaman profil",
        "uid_example":  "123456789",
        "uid_min_len":  5,
        "requires_uid_verification": False,  # BingX tidak perlu verifikasi UID referral
        "api_key_help": (
            "1️⃣ Login ke BingX → klik <b>avatar/foto profil</b> kamu\n"
            "2️⃣ Pilih <b>API Management</b>\n"
            "3️⃣ Klik <b>Create API</b>\n"
            "4️⃣ <b>Note/Label:</b> isi <code>CryptoMentor Bot</code>\n"
            "5️⃣ <b>IP Restriction:</b> biarkan <b>KOSONG</b> (jangan isi IP apapun)\n"
            "6️⃣ <b>Permissions:</b> centang ✅ <b>Perpetual Futures Trading</b>\n"
            "   ❌ Jangan centang Withdraw atau Transfer\n"
            "7️⃣ Klik <b>Confirm</b> → verifikasi via email/2FA\n"
            "8️⃣ Copy <b>API Key</b> dan <b>Secret Key</b> — simpan baik-baik!\n\n"
            "⚠️ Secret Key hanya tampil sekali, jangan sampai hilang."
        ),
        "api_key_url":  "https://bingx.com/en/accounts/api",
        "client_class": "BingXAutoTradeClient",
        "client_module": "app.bingx_autotrade_client",
    },
}


def get_exchange(exchange_id: str) -> dict:
    """Get exchange config. Raises ValueError if not found."""
    ex = EXCHANGES.get(exchange_id.lower())
    if not ex:
        raise ValueError(f"Exchange '{exchange_id}' not recognized")
    return ex


def get_client(exchange_id: str, api_key: str, api_secret: str):
    """Create a trading client instance for the selected exchange."""
    import importlib
    ex = get_exchange(exchange_id)
    module = importlib.import_module(ex["client_module"])
    cls    = getattr(module, ex["client_class"])
    return cls(api_key=api_key, api_secret=api_secret)


def exchange_list_keyboard():
    """Build InlineKeyboard for exchange selection. Coming soon = disabled (no-op)."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = []
    for eid, ex in EXCHANGES.items():
        if ex.get("coming_soon"):
            buttons.append([InlineKeyboardButton(
                f"{ex['name']}  (Coming Soon)",
                callback_data="at_noop"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                ex["name"],
                callback_data=f"at_exchange_{eid}"
            )])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")])
    return InlineKeyboardMarkup(buttons)
