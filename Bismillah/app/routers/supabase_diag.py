
from aiogram import Router, types
from app.supabase_conn import (
    health, upsert_user_via_rpc, get_user_by_tid,
    set_premium_via_rpc, revoke_premium, set_credits,
    stats_totals, is_premium_active
)
import os

router = Router()
ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS","").split(",") if os.getenv("ADMIN_IDS") else [])}

def _parse_ref(msg: types.Message):
    if not msg or not msg.text: return None
    p = msg.text.split(maxsplit=1)
    if len(p)==2:
        try: return int(p[1])
        except: return None
    return None

@router.message(commands={"diag_supabase"})
async def diag(msg: types.Message):
    ok, detail = health()
    tot=prem=0
    if ok:
        try: tot,prem = stats_totals()
        except Exception as e: detail = f"stats_totals error: {e}"
    await msg.answer(f"🔧 Supabase: {'✅' if ok else '❌'} {detail}\nTotals: users={tot}, premium={prem}")

@router.message(commands={"start"})
async def start(msg: types.Message):
    u = msg.from_user
    ref = _parse_ref(msg)
    try:
        row = upsert_user_via_rpc(u.id, u.username, u.first_name, u.last_name, referred_by=ref)
        # ambil ulang fresh dari DB
        fresh = get_user_by_tid(u.id) or {}
        await msg.answer(
            "👋 Registered (Supabase)\n"
            f"ID={u.id}, user=@{(u.username or '').lower()}\n"
            f"credits={fresh.get('credits','—')}, premium={fresh.get('is_premium')}, lifetime={fresh.get('is_lifetime')}"
        )
    except Exception as e:
        await msg.answer(f"⚠️ upsert failed: {e}")

@router.message(commands={"me"})
async def me(msg: types.Message):
    row = get_user_by_tid(msg.from_user.id) or {}
    await msg.answer(
        "👤 DB row:\n"
        f"credits={row.get('credits')}, premium={row.get('is_premium')}, "
        f"lifetime={row.get('is_lifetime')}, until={row.get('premium_until')}, active={is_premium_active(msg.from_user.id)}"
    )

@router.message(commands={"setpremium"})
async def setpremium(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if uid not in ADMIN_IDS: return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<3: return await msg.answer("Usage: /setpremium <telegram_id> <lifetime|days|months> [value]")
    tg_id=int(p[1]); dtype=p[2].lower()
    dval=int(p[3]) if len(p)>=4 and dtype in ("days","months") else 0
    try:
        set_premium_via_rpc(tg_id, dtype, dval)
        row = get_user_by_tid(tg_id) or {}
        await msg.answer(f"✅ setpremium OK → premium={row.get('is_premium')}, lifetime={row.get('is_lifetime')}, until={row.get('premium_until')}")
    except Exception as e:
        await msg.answer(f"⚠️ setpremium failed: {e}")

@router.message(commands={"revoke_premium"})
async def revoke(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if uid not in ADMIN_IDS: return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<2: return await msg.answer("Usage: /revoke_premium <telegram_id>")
    tg_id=int(p[1])
    try:
        revoke_premium(tg_id)
        row = get_user_by_tid(tg_id) or {}
        await msg.answer(f"✅ revoke OK → premium={row.get('is_premium')}, lifetime={row.get('is_lifetime')}, until={row.get('premium_until')}")
    except Exception as e:
        await msg.answer(f"⚠️ revoke failed: {e}")

@router.message(commands={"setcredits"})
async def setcredits(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if uid not in ADMIN_IDS: return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<3: return await msg.answer("Usage: /setcredits <telegram_id> <amount>")
    tg_id=int(p[1]); amount=int(p[2])
    try:
        set_credits(tg_id, amount)
        row = get_user_by_tid(tg_id) or {}
        await msg.answer(f"✅ credits set {amount} → row now: {row.get('credits')}")
    except Exception as e:
        await msg.answer(f"⚠️ setcredits failed: {e}")
