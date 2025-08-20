
# app/admin_status.py
from aiogram import Router, types
from datetime import datetime, timezone
from app.supabase_conn import health as sb_health
from app.sb_repo import stats_totals
from app.admin_auth import is_admin, denied

router = Router()

@router.message(commands={"admin"})
async def admin_status(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if not is_admin(uid): 
        return await msg.answer(denied(uid))
    
    ok, reason = sb_health()
    tot, prem = (0, 0)
    if ok:
        try: 
            tot, prem = stats_totals()
        except Exception as e: 
            reason = f"stats_totals error: {e}"
    
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    text = (
        "📊 System Status\n\n"
        f"🗄️ Database: SUPABASE - {'✅' if ok else '❌'}\n\n"
        f"• Supabase  - Total Users: {tot} | Premium: {prem}\n\n"
        f"🔎 DB Detail: {('OK' if ok else reason)}\n"
        f"⏰ Last Update: {now}"
    )
    await msg.answer(text)

async def get_admin_status():
    """Get admin status for integration with existing bot"""
    ok, reason = sb_health()
    tot, prem = (0, 0)
    if ok:
        try: 
            tot, prem = stats_totals()
        except Exception as e: 
            reason = f"stats_totals error: {e}"
    
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return {
        'ok': ok,
        'reason': reason,
        'total_users': tot,
        'premium_users': prem,
        'timestamp': now
    }
