
# app/middlewares/referral_gate.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Optional
from ..sb_repo import user_exists, upsert_user_ref_required

JOIN_TEXT_NO_REF = (
    "🚪 Untuk bergabung, gunakan tautan referral.\n"
    "• Minta teman kirimkan link: <code>https://t.me/{bot_username}?start=&lt;USER_ID&gt;</code>\n"
    "• Atau klik link undangan yang valid dari komunitas.\n\n"
    "ℹ️ Referral wajib agar akunmu terdaftar."
)

JOIN_TEXT_BAD_REF = (
    "⚠️ Referral tidak valid.\n"
    "• Pastikan kamu memakai link <b>resmi</b> yang berisi ID Telegram perujuk.\n"
    "• Coba minta ulang link referral dari temanmu."
)

def _parse_ref_from_start(msg: Message) -> Optional[int]:
    if not msg or not msg.text: return None
    if not msg.text.startswith("/start"): return None
    parts = msg.text.split(maxsplit=1)
    if len(parts) != 2: return None
    try:
        return int(parts[1])
    except Exception:
        return None

def _try_register_with_ref(msg: Message) -> bool:
    u = msg.from_user
    if not u: return False
    ref = _parse_ref_from_start(msg)
    if ref is None:
        # tidak ada payload referral
        return False
    try:
        upsert_user_ref_required(
            tg_id=u.id,
            username=getattr(u, "username", None),
            first_name=getattr(u, "first_name", None),
            last_name=getattr(u, "last_name", None),
            referred_by=ref,
        )
        return True
    except Exception:
        return False

class ReferralGateMiddleware(BaseMiddleware):
    def __init__(self, bot_username: str):
        super().__init__()
        self.bot_username = bot_username

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        # Messages
        if isinstance(event, Message):
            u = event.from_user
            if u and not user_exists(u.id):
                # belum terdaftar → hanya boleh /start <ref>
                if event.text and event.text.startswith("/start"):
                    if _try_register_with_ref(event):
                        return await handler(event, data)
                    else:
                        await event.answer(JOIN_TEXT_BAD_REF, parse_mode="HTML")
                        return
                else:
                    await event.answer(JOIN_TEXT_NO_REF.format(bot_username=self.bot_username), parse_mode="HTML")
                    return
            # sudah terdaftar
            return await handler(event, data)

        # CallbackQuery (user baru ditolak)
        if isinstance(event, CallbackQuery):
            u = event.from_user
            if u and not user_exists(u.id):
                await event.message.answer(JOIN_TEXT_NO_REF.format(bot_username=self.bot_username), parse_mode="HTML")
                return
            return await handler(event, data)

        return await handler(event, data)
