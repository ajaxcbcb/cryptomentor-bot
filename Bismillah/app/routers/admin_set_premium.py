
from aiogram import Router, types
from app.sb_repo import set_premium
from app.lib.auth import is_admin
import html

router = Router()

def esc(t): 
    return html.escape(str(t), quote=False)

def admin_denied_text(uid):
    return f"❌ Access denied for user {uid}. Admin only command."

@router.message(commands={"set_premium"})
async def set_prem(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    
    if not is_admin(uid):
        await msg.answer(esc(admin_denied_text(uid)), parse_mode="HTML")
        return
    
    # Format: /set_premium <telegram_id> <lifetime|days|months> [value]
    parts = (msg.text or "").split()
    
    if len(parts) < 3:
        await msg.answer(
            esc("Usage: /set_premium <telegram_id> <lifetime|days|months> [value]"), 
            parse_mode="HTML"
        )
        return
    
    try:
        tg_id = int(parts[1])
        dtype = parts[2].lower()
        dval = int(parts[3]) if len(parts) >= 4 and dtype in ("days", "months") else 0
        
        set_premium(tg_id, dtype, dval)
        
        await msg.answer(
            esc(f"✅ Premium updated for {tg_id}: {dtype} {dval}"), 
            parse_mode="HTML"
        )
    except ValueError:
        await msg.answer(esc("❌ Invalid telegram_id or duration value"), parse_mode="HTML")
    except Exception as e:
        await msg.answer(esc(f"❌ Error: {e}"), parse_mode="HTML")
