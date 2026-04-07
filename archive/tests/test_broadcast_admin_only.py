#!/usr/bin/env python3
"""
Test broadcast ke admin only - no interactive menu
"""

import os
import sys
import asyncio
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / 'Bismillah' / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from telegram.ext import Application

async def main():
    """Test broadcast to admin only"""
    
    print("=" * 70)
    print("🧪 SOCIAL PROOF BROADCAST - TEST TO ADMIN")
    print("=" * 70)
    print()
    
    # Get bot token (try multiple env var names)
    bot_token = os.getenv('BOT_TOKEN') or os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ Bot token not found in .env")
        print("   Tried: BOT_TOKEN, TOKEN, TELEGRAM_BOT_TOKEN")
        return
    
    print(f"✅ Bot token loaded")
    print()
    
    # Initialize bot
    print("🤖 Initializing bot...")
    app = Application.builder().token(bot_token).build()
    await app.initialize()
    await app.start()
    
    bot = app.bot
    bot_info = await bot.get_me()
    print(f"✅ Bot connected: @{bot_info.username}")
    print()
    
    # Test data - using real profit from Bhax
    test_symbol = "BTCUSDT"
    test_side = "LONG"
    test_pnl = 26.93
    test_leverage = 100
    
    print("📊 Test Data:")
    print(f"   Symbol: {test_symbol}")
    print(f"   Side: {test_side}")
    print(f"   Profit: ${test_pnl} USDT")
    print(f"   Leverage: {test_leverage}x")
    print()
    
    # Import masking function
    from app.social_proof import _mask_name
    
    # Test username masking
    print("🎭 Username Masking Test:")
    test_names = ["Bhax", "Budi Santoso", "John Doe", "Test User"]
    for name in test_names:
        masked = _mask_name(name)
        print(f"   '{name}' → '{masked}'")
    print()
    
    # Get admin IDs
    admin_ids = []
    for key in ['ADMIN1', 'ADMIN2', 'ADMIN3']:
        val = os.getenv(key, '')
        if val and val.isdigit():
            admin_ids.append(int(val))
    
    if not admin_ids:
        print("⚠️ No admin IDs found, using fallback test ID")
        admin_ids = [1234500019]  # Bhax as fallback
    
    print(f"🎯 Sending to {len(admin_ids)} admin(s):")
    for aid in admin_ids:
        print(f"   - {aid}")
    print()
    
    # Build message
    display_name = _mask_name("Test User")
    emoji = "🟢"
    direction = "LONG ↑"
    
    message = (
        f"🔥 <b>Trade Profit Alert!</b>\n\n"
        f"👤 User <b>{display_name}</b> baru saja profit:\n\n"
        f"{emoji} <b>{test_symbol}</b> {direction}\n"
        f"💰 Profit: <b>+{test_pnl:.2f} USDT</b>\n"
        f"⚡ Leverage: {test_leverage}x\n\n"
        f"🤖 <i>Dieksekusi otomatis oleh CryptoMentor AI</i>\n\n"
        f"💡 Mau bot trading juga buat kamu?\n"
        f"Ketik /autotrade untuk mulai!\n\n"
        f"<i>🧪 TEST BROADCAST - Admin Only</i>"
    )
    
    print("📝 Message Preview:")
    print("-" * 70)
    # Remove HTML tags for preview
    preview = message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
    print(preview)
    print("-" * 70)
    print()
    
    # Send to admins
    print("📤 Sending...")
    sent = 0
    failed = 0
    
    for admin_id in admin_ids:
        try:
            result = await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"   ✅ Sent to {admin_id} (message_id: {result.message_id})")
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"   ❌ Failed to {admin_id}: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print(f"✅ Sent: {sent}")
    print(f"❌ Failed: {failed}")
    print()
    
    if sent > 0:
        print("✅ TEST SUCCESSFUL!")
        print()
        print("🎯 Next Steps:")
        print("   1. Check Telegram to verify message received")
        print("   2. Verify format and content look good")
        print("   3. Username masking working correctly")
        print()
        print("💡 If everything looks good, the broadcast system is working!")
        print("   It will automatically trigger when real trades close with profit ≥$5")
    else:
        print("❌ TEST FAILED")
        print("   Check bot token and permissions")
    
    print()
    
    # Cleanup
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
