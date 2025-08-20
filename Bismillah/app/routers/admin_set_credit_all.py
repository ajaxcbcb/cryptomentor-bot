
from aiogram import Router, types
from app.sb_repo import admin_set_credits_all
from app.lib.auth import is_admin
import html

router = Router()

def esc(t): 
    return html.escape(str(t), quote=False)

def admin_denied_text(uid):
    return f"❌ Access denied for user {uid}. Admin only command."

@router.message(commands={"set_credit_all"})
async def set_credit_all(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    
    if not is_admin(uid):
        await msg.answer(esc(admin_denied_text(uid)), parse_mode="HTML")
        return
    
    parts = (msg.text or "").split()
    amount = 100
    include_premium = any(p.lower() in ("--all", "-a") for p in parts[2:])
    
    if len(parts) >= 2:
        try: 
            amount = int(parts[1])
        except: 
            pass
    
    n = admin_set_credits_all(amount, include_premium)
    
    await msg.answer(
        esc(f"✅ Set credits={amount}\nTarget: {'ALL users' if include_premium else 'FREE users only'}\nAffected: {n}"), 
        parse_mode="HTML"
    )
