
# app/routers/core.py
from aiogram import Router, types
from app.supabase_conn import health as sb_health
from app.sb_repo import upsert_user_with_ref_optional, stats_totals

router = Router()

def _parse_ref(msg: types.Message):
    if not msg or not msg.text: return None
    parts = msg.text.split(maxsplit=1)
    if len(parts)==2:
        try: return int(parts[1])
        except: return None
    return None

@router.message(commands={"start"})
async def start(msg: types.Message):
    u = msg.from_user
    ref = _parse_ref(msg)
    try:
        row = upsert_user_with_ref_optional(
            tg_id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            referred_by=ref
        )
        await msg.answer(
            "👋 Welcome to CryptoMentor AI!\n\n"
            f"• ID: {u.id}\n"
            f"• Username: @{(u.username or '').lower()}\n"
            f"• Credits: {row.get('credits', '—')}\n"
            f"• Referred by: {row.get('referred_by', 'none')}\n\n"
            "Use /help to see available commands!"
        )
    except Exception as e:
        await msg.answer(f"⚠️ Registration failed: {e}")

@router.message(commands={"diag_supabase"})
async def diag_supabase(msg: types.Message):
    ok, detail = sb_health()
    tot=prem=0
    if ok:
        try: tot,prem = stats_totals()
        except Exception as e: detail = f"stats_totals error: {e}"
    await msg.answer(
        "🔧 Supabase Diagnostics\n\n"
        f"• Health: {'✅' if ok else '❌'} {detail}\n"
        f"• Totals: users={tot}, premium={prem}"
    )
