
from aiogram import Router, types
from app.supabase_conn import health as sb_health
from app.sb_repo import upsert_user_strict, get_user_row, stats_totals

router = Router()

def _parse_ref(msg: types.Message):
    if not msg or not msg.text: return None
    parts = msg.text.split(maxsplit=1)
    if len(parts)==2:
        try: return int(parts[1])
        except: return None
    return None

@router.message(commands={"diag_supabase"})
async def diag(msg: types.Message):
    ok, detail = sb_health()
    tot=prem=0
    if ok:
        try: tot,prem = stats_totals()
        except Exception as e: detail=f"stats_totals error: {e}"
    await msg.answer(f"🔧 Supabase: {'✅' if ok else '❌'} {detail}\nTotals: users={tot}, premium={prem}")

@router.message(commands={"start"})
async def start(msg: types.Message):
    u = msg.from_user
    ref = _parse_ref(msg)
    try:
        _ = upsert_user_strict(u.id, u.username, u.first_name, u.last_name, referred_by=ref)
        fresh = get_user_row(u.id) or {}
        await msg.answer(
            "👋 Registered to Supabase\n"
            f"ID: {u.id}\n"
            f"Username: @{(u.username or '').lower()}\n"
            f"Credits: {fresh.get('credits','—')}\n"
            f"Premium: {fresh.get('is_premium', False)} | Lifetime: {fresh.get('is_lifetime', False)}"
        )
    except Exception as e:
        await msg.answer(f"⚠️ Registration failed: {e}")

@router.message(commands={"me"})
async def me(msg: types.Message):
    row = get_user_row(msg.from_user.id) or {}
    await msg.answer(
        "👤 Your Supabase row\n"
        f"credits={row.get('credits')}, premium={row.get('is_premium')}, "
        f"lifetime={row.get('is_lifetime')}, premium_until={row.get('premium_until')}"
    )
