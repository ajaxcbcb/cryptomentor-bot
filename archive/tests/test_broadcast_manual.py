#!/usr/bin/env python3
"""
Manual test script untuk social proof broadcast
Kirim test broadcast ke admin/test users dulu sebelum ke semua user
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

async def test_broadcast_to_admins():
    """
    Test broadcast dengan mengirim ke admin users dulu
    Menggunakan data real dari database (Bhax's profit)
    """
    
    print("=" * 70)
    print("🧪 SOCIAL PROOF BROADCAST - MANUAL TEST")
    print("=" * 70)
    print()
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not found in .env")
        return
    
    print(f"✅ Bot token loaded: {bot_token[:20]}...")
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
    test_user_id = 1234500019  # Bhax
    test_first_name = "Test User"  # Will be masked
    test_symbol = "BTCUSDT"
    test_side = "LONG"
    test_pnl = 26.93  # Real profit from database
    test_leverage = 100
    
    print("📊 Test Data:")
    print(f"   User ID: {test_user_id}")
    print(f"   Symbol: {test_symbol}")
    print(f"   Side: {test_side}")
    print(f"   Profit: ${test_pnl} USDT")
    print(f"   Leverage: {test_leverage}x")
    print()
    
    # Import broadcast function
    print("📦 Importing broadcast function...")
    from app.social_proof import broadcast_profit, _mask_name
    
    # Test username masking
    print("🎭 Testing username masking:")
    test_names = ["Bhax", "Budi Santoso", "John", "A", "Test User"]
    for name in test_names:
        masked = _mask_name(name)
        print(f"   '{name}' → '{masked}'")
    print()
    
    # Get admin IDs for test
    admin_ids = []
    for key in ['ADMIN1', 'ADMIN2', 'ADMIN3']:
        val = os.getenv(key, '')
        if val and val.isdigit():
            admin_ids.append(int(val))
    
    if not admin_ids:
        print("⚠️ No admin IDs found in .env")
        print("   Will send to test user ID instead")
        admin_ids = [test_user_id]
    
    print(f"🎯 Target recipients: {len(admin_ids)} admin(s)")
    for aid in admin_ids:
        print(f"   - Admin ID: {aid}")
    print()
    
    # Build test message
    display_name = _mask_name(test_first_name)
    emoji = "🟢" if test_side == "LONG" else "🔴"
    direction = "LONG ↑" if test_side == "LONG" else "SHORT ↓"
    
    test_message = (
        f"🔥 <b>Trade Profit Alert!</b>\n\n"
        f"👤 User <b>{display_name}</b> baru saja profit:\n\n"
        f"{emoji} <b>{test_symbol}</b> {direction}\n"
        f"💰 Profit: <b>+{test_pnl:.2f} USDT</b>\n"
        f"⚡ Leverage: {test_leverage}x\n\n"
        f"🤖 <i>Dieksekusi otomatis oleh CryptoMentor AI</i>\n\n"
        f"💡 Mau bot trading juga buat kamu?\n"
        f"Ketik /autotrade untuk mulai!\n\n"
        f"<i>🧪 This is a TEST broadcast</i>"
    )
    
    print("📝 Test Message Preview:")
    print("-" * 70)
    print(test_message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''))
    print("-" * 70)
    print()
    
    # Confirm before sending
    print("⚠️ Ready to send test broadcast to admin(s)")
    print()
    
    # Send to admins
    print("📤 Sending test broadcast...")
    sent = 0
    failed = 0
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=test_message,
                parse_mode='HTML'
            )
            print(f"   ✅ Sent to admin {admin_id}")
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"   ❌ Failed to send to admin {admin_id}: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    print(f"✅ Sent: {sent}")
    print(f"❌ Failed: {failed}")
    print()
    
    if sent > 0:
        print("✅ TEST SUCCESSFUL!")
        print()
        print("🎯 Next Steps:")
        print("   1. Check your Telegram to verify message received")
        print("   2. Verify message format looks good")
        print("   3. If OK, we can proceed to full broadcast test")
        print()
        print("⚠️ Note: This was a TEST to admin only")
        print("   Real broadcast will go to 1,229 non-autotrade users")
    else:
        print("❌ TEST FAILED - No messages sent")
        print("   Check bot token and admin IDs in .env")
    
    print()
    
    # Cleanup
    await app.stop()
    await app.shutdown()

async def test_full_broadcast():
    """
    Test FULL broadcast ke semua non-autotrade users
    HANYA jalankan setelah test ke admin berhasil!
    """
    
    print("=" * 70)
    print("🚀 FULL BROADCAST TEST - TO ALL NON-AUTOTRADE USERS")
    print("=" * 70)
    print()
    
    print("⚠️ WARNING: This will send to ~1,229 users!")
    print()
    
    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    if response != 'YES':
        print("❌ Cancelled")
        return
    
    print()
    print("🤖 Initializing bot...")
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not found in .env")
        return
    
    # Initialize bot
    app = Application.builder().token(bot_token).build()
    await app.initialize()
    await app.start()
    
    bot = app.bot
    bot_info = await bot.get_me()
    print(f"✅ Bot connected: @{bot_info.username}")
    print()
    
    # Import broadcast function
    from app.social_proof import broadcast_profit
    
    # Use real data from Bhax
    print("📤 Triggering full broadcast...")
    print()
    
    await broadcast_profit(
        bot=bot,
        user_id=1234500019,  # Bhax
        first_name="Bhax",
        symbol="BTCUSDT",
        side="LONG",
        pnl_usdt=26.93,
        leverage=100
    )
    
    print()
    print("✅ Broadcast triggered!")
    print("   Check logs for delivery status")
    print()
    
    # Cleanup
    await app.stop()
    await app.shutdown()

def main():
    """Main menu"""
    print()
    print("=" * 70)
    print("🧪 SOCIAL PROOF BROADCAST - MANUAL TEST TOOL")
    print("=" * 70)
    print()
    print("Choose test mode:")
    print()
    print("1. Test to ADMIN only (safe, recommended first)")
    print("2. Full broadcast to ALL users (~1,229 users)")
    print("3. Exit")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        print()
        asyncio.run(test_broadcast_to_admins())
    elif choice == '2':
        print()
        asyncio.run(test_full_broadcast())
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
