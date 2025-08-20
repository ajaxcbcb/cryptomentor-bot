
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..lib.auth import admin_only
from ..sb_client import supabase, available

router = Router()

@router.message(Command("set_credits_all"))
@admin_only
async def handle_set_credits_all(message: Message):
    """Admin command to set credits for all users"""
    args = message.text.split()[1:] if message.text else []
    
    if not args:
        await message.reply("❌ Usage: /set_credits_all <amount>")
        return
    
    try:
        amount = int(args[0])
        if amount < 0:
            await message.reply("❌ Credits amount must be positive")
            return
            
        if not available():
            await message.reply("❌ Supabase not available")
            return
            
        # Update all users credits
        response = supabase.table('users').update({'credits': amount}).neq('telegram_id', 0).execute()
        
        await message.reply(f"✅ Set credits to {amount} for all users")
        
    except ValueError:
        await message.reply("❌ Invalid amount. Must be a number.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
