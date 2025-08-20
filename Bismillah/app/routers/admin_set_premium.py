
from aiogram import Router, types
import os
from app.sb_repo import set_premium_rpc

router = Router()
ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS","").split(",") if os.getenv("ADMIN_IDS") else [])}

@router.message(commands={"set_premium"})
async def set_premium(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if uid not in ADMIN_IDS:
        return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    p=(msg.text or "").split()
    if len(p)<3:
        return await msg.answer("Usage: /set_premium <telegram_id> <lifetime|days|months> [value]")
    
    try:
        tg_id=int(p[1]); dtype=p[2].lower()
        dval=int(p[3]) if len(p)>=4 and dtype in ("days","months") else 0
        
        set_premium_rpc(tg_id, dtype, dval)
        await msg.answer(f"✅ Premium updated for {tg_id}: {dtype} {dval}")
    except ValueError as e:
        await msg.answer(f"❌ Invalid input: {e}")
    except Exception as e:
        await msg.answer(f"⚠️ set_premium failed: {e}")
