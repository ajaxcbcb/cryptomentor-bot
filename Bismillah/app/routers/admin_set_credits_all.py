
from aiogram import Router, types
from ..lib.auth import is_admin
from ..sb_client import admin_set_credits_all_rpc
import html
import logging

router = Router()

def esc(t): 
    """Escape HTML entities"""
    return html.escape(str(t), quote=False)

def admin_denied_text(uid: int) -> str:
    """Return admin access denied message"""
    return f"❌ Access denied. User ID {uid} is not an admin."

@router.message(commands={"set_credits_all"})
async def set_all_credits_command(msg: types.Message):
    """Admin command to set credits for all users"""
    uid = msg.from_user.id if msg.from_user else 0
    
    if not is_admin(uid):
        await msg.answer(esc(admin_denied_text(uid)), parse_mode="HTML")
        return

    # Format: /set_credits_all 100 [--all]
    amount = 100
    include_premium = False
    
    parts = (msg.text or "").split()
    if len(parts) >= 2:
        try:
            amount = int(parts[1])
        except ValueError:
            await msg.answer("❌ Invalid amount. Please provide a number.", parse_mode="HTML")
            return
    
    # Check for --all or -a flag to include premium users
    if any(p.lower() in ("--all", "-a") for p in parts[2:]):
        include_premium = True

    try:
        n = admin_set_credits_all_rpc(amount, include_premium)
        
        target_text = "ALL users" if include_premium else "FREE users only"
        response = f"✅ Set credits = {amount}\nTarget: {target_text}\nAffected: {n} users"
        
        await msg.answer(esc(response), parse_mode="HTML")
        logging.info(f"Admin {uid} set credits to {amount} for {n} users (include_premium: {include_premium})")
        
    except Exception as e:
        logging.error(f"Error in set_credits_all command: {e}")
        await msg.answer(f"❌ Error: {esc(str(e))}", parse_mode="HTML")
