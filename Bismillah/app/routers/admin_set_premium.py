
# app/routers/admin_set_premium.py
from aiogram import Router, types
from app.sb_repo import set_premium_rpc
from app.admin_auth import is_admin, denied

router = Router()

@router.message(commands={"set_premium"})
async def set_premium(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if not is_admin(uid): 
        return await msg.answer(denied(uid))
    
    p = (msg.text or "").split()
    if len(p) < 3:
        return await msg.answer("Usage: /set_premium <telegram_id> <lifetime|days|months> [value]")
    
    try:
        tg_id = int(p[1])
        dtype = p[2].lower()
        dval = int(p[3]) if len(p) >= 4 and dtype in ("days", "months") else 0
        
        set_premium_rpc(tg_id, dtype, dval)
        await msg.answer(f"✅ Premium updated for {tg_id}: {dtype} {dval}")
    except Exception as e:
        await msg.answer(f"❌ Error: {e}")
