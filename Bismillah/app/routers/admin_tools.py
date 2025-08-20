
import os
from aiogram import Router, types
from app.sb_repo import set_premium_rpc, revoke_premium_db, set_credits_db, get_user_row

router = Router()
ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS","").split(",") if os.getenv("ADMIN_IDS") else [])}

def _admin_only(uid:int)->bool: return uid in ADMIN_IDS

@router.message(commands={"setpremium"})
async def setpremium(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if not _admin_only(uid): return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<3: return await msg.answer("Usage: /setpremium <telegram_id> <lifetime|days|months> [value]")
    tg_id=int(p[1]); dtype=p[2].lower()
    dval=int(p[3]) if len(p)>=4 and dtype in ("days","months") else 0
    try:
        set_premium_rpc(tg_id, dtype, dval)
        row = get_user_row(tg_id) or {}
        await msg.answer(f"✅ setpremium OK\npremium={row.get('is_premium')} lifetime={row.get('is_lifetime')} until={row.get('premium_until')}")
    except Exception as e:
        await msg.answer(f"⚠️ setpremium failed: {e}")

@router.message(commands={"revoke_premium"})
async def revoke(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if not _admin_only(uid): return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<2: return await msg.answer("Usage: /revoke_premium <telegram_id>")
    tg_id=int(p[1])
    try:
        revoke_premium_db(tg_id)
        row = get_user_row(tg_id) or {}
        await msg.answer(f"✅ revoke OK\npremium={row.get('is_premium')} lifetime={row.get('is_lifetime')} until={row.get('premium_until')}")
    except Exception as e:
        await msg.answer(f"⚠️ revoke failed: {e}")

@router.message(commands={"setcredits"})
async def setcredits(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if not _admin_only(uid): return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<3: return await msg.answer("Usage: /setcredits <telegram_id> <amount>")
    tg_id=int(p[1]); amount=int(p[2])
    try:
        set_credits_db(tg_id, amount)
        row = get_user_row(tg_id) or {}
        await msg.answer(f"✅ credits set {amount}\nnow: {row.get('credits')}")
    except Exception as e:
        await msg.answer(f"⚠️ setcredits failed: {e}")
