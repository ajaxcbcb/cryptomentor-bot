
from aiogram import Router, types
import os
from app.supabase_conn import get_supabase_client

router = Router()
ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS","").split(",") if os.getenv("ADMIN_IDS") else [])}

@router.message(commands={"set_credit_all"})
async def set_credit_all(msg: types.Message):
    uid = msg.from_user.id if msg.from_user else 0
    if uid not in ADMIN_IDS:
        return await msg.answer(f"❌ Admin only. Your ID: {uid}")
    
    p = (msg.text or "").split()
    if len(p) < 2:
        return await msg.answer("Usage: /set_credit_all <amount>")
    
    try:
        amount = int(p[1])
        if amount < 0:
            return await msg.answer("❌ Amount must be positive")
        
        s = get_supabase_client()
        
        # Update all users' credits
        result = s.table("users").update({"credits": amount}).neq("telegram_id", 0).execute()
        count = len(result.data) if result.data else 0
        
        await msg.answer(f"✅ Set {amount} credits for {count} users")
        
    except ValueError:
        await msg.answer("❌ Invalid amount. Must be a number.")
    except Exception as e:
        await msg.answer(f"⚠️ Failed to update credits: {e}")
