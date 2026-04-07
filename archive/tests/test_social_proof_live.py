"""
Test Social Proof Broadcast - Live Test
Menggunakan data trade history kemarin untuk test broadcast
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Fix Windows encoding for emoji
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add Bismillah to path
sys.path.insert(0, 'Bismillah')

from dotenv import load_dotenv
load_dotenv('Bismillah/.env')


async def get_yesterday_profitable_trades():
    """Get all profitable trades from yesterday (profit >= $5)"""
    from app.supabase_repo import _client
    
    # Calculate yesterday's date range
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = (today - timedelta(days=1)).isoformat()
    yesterday_end = today.isoformat()
    
    print(f"\n📅 Fetching trades from: {yesterday_start} to {yesterday_end}")
    
    s = _client()
    
    # Query profitable trades
    result = s.table("autotrade_trades").select(
        "id, telegram_id, symbol, side, entry_price, exit_price, qty, leverage, pnl_usdt, status, closed_at"
    ).eq(
        "status", "closed_tp"
    ).gte(
        "closed_at", yesterday_start
    ).lt(
        "closed_at", yesterday_end
    ).order(
        "pnl_usdt", desc=True
    ).execute()
    
    trades = result.data or []
    
    # Filter trades with profit >= $5
    profitable_trades = [t for t in trades if float(t.get("pnl_usdt", 0)) >= 5.0]
    
    print(f"\n✅ Found {len(trades)} closed_tp trades")
    print(f"✅ Found {len(profitable_trades)} trades with profit >= $5")
    
    return profitable_trades


async def get_user_info(telegram_id):
    """Get user info from database"""
    from app.supabase_repo import _client, get_user_by_tid
    
    try:
        user_data = get_user_by_tid(telegram_id)
        if user_data:
            return {
                "telegram_id": telegram_id,
                "first_name": user_data.get("first_name", "User"),
                "username": user_data.get("username", ""),
            }
    except:
        pass
    
    return {
        "telegram_id": telegram_id,
        "first_name": "User",
        "username": "",
    }


async def get_target_users():
    """Get users who should receive broadcast (non-autotrade users)"""
    from app.supabase_repo import _client
    
    s = _client()
    
    # Get all users
    all_users = []
    offset = 0
    while True:
        res = s.table("users").select("telegram_id, first_name, username").range(offset, offset + 999).execute()
        batch = res.data or []
        all_users.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    
    # Get users with autotrade
    at_res = s.table("autotrade_sessions").select("telegram_id").execute()
    at_ids = {row["telegram_id"] for row in (at_res.data or [])}
    
    # Filter: only non-autotrade users
    target_users = [u for u in all_users if u["telegram_id"] not in at_ids]
    
    print(f"\n👥 Total users: {len(all_users)}")
    print(f"🤖 Users with autotrade: {len(at_ids)}")
    print(f"🎯 Target users (non-autotrade): {len(target_users)}")
    
    return target_users


def mask_name(name: str) -> str:
    """Mask username for privacy"""
    if not name:
        return "User***"
    
    parts = name.strip().split()
    masked_parts = []
    
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part + "***")
        elif len(part) == 2:
            masked_parts.append(part[0] + "***" + part[1])
        elif len(part) == 3:
            masked_parts.append(part[0] + "***" + part[-1])
        else:
            masked_parts.append(part[0] + "***" + part[-1])
    
    return " ".join(masked_parts)


async def test_broadcast_single_trade(trade, target_users, bot, dry_run=True):
    """Test broadcast for a single trade"""
    
    # Get user info
    user_info = await get_user_info(trade["telegram_id"])
    display_name = mask_name(user_info["first_name"])
    
    # Format message
    emoji = "🟢" if trade["side"] == "LONG" else "🔴"
    direction = "LONG ↑" if trade["side"] == "LONG" else "SHORT ↓"
    pnl = float(trade.get("pnl_usdt", 0))
    
    message = (
        f"🔥 <b>Trade Profit Alert!</b>\n\n"
        f"👤 User <b>{display_name}</b> baru saja profit:\n\n"
        f"{emoji} <b>{trade['symbol']}</b> {direction}\n"
        f"💰 Profit: <b>+{pnl:.2f} USDT</b>\n"
        f"⚡ Leverage: {trade['leverage']}x\n\n"
        f"🤖 <i>Dieksekusi otomatis oleh CryptoMentor AI</i>\n\n"
        f"💡 Mau bot trading juga buat kamu?\n"
        f"Ketik /autotrade untuk mulai!"
    )
    
    print(f"\n{'='*60}")
    print(f"📊 Trade #{trade['id']}")
    print(f"{'='*60}")
    print(f"User: {user_info['first_name']} (ID: {trade['telegram_id']})")
    print(f"Symbol: {trade['symbol']}")
    print(f"Side: {trade['side']}")
    print(f"Profit: ${pnl:.2f}")
    print(f"Leverage: {trade['leverage']}x")
    print(f"Closed: {trade['closed_at']}")
    print(f"\n📨 Message Preview:")
    print(f"{'-'*60}")
    print(message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''))
    print(f"{'-'*60}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - Would send to {len(target_users)} users")
        return {"sent": 0, "failed": 0, "dry_run": True}
    
    # Actually send
    print(f"\n📤 Sending to {len(target_users)} users...")
    sent = 0
    failed = 0
    
    for user in target_users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=message,
                parse_mode='HTML'
            )
            sent += 1
            if sent % 10 == 0:
                print(f"   Sent: {sent}/{len(target_users)}")
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception as e:
            failed += 1
            if failed <= 5:  # Only show first 5 errors
                print(f"   ❌ Failed to send to {user['telegram_id']}: {e}")
    
    print(f"\n✅ Broadcast complete: {sent} sent, {failed} failed")
    
    return {"sent": sent, "failed": failed, "dry_run": False}


async def main():
    """Main test function"""
    print("="*60)
    print("SOCIAL PROOF BROADCAST - LIVE TEST")
    print("="*60)
    
    # Step 1: Get profitable trades from yesterday
    print("\n📊 Step 1: Fetching profitable trades from yesterday...")
    trades = await get_yesterday_profitable_trades()
    
    if not trades:
        print("\n❌ No profitable trades found from yesterday!")
        print("   This could mean:")
        print("   1. No trades closed with profit >= $5 yesterday")
        print("   2. Database has no trade history")
        print("   3. PnL calculation is still broken")
        return
    
    # Display all trades
    print(f"\n{'='*60}")
    print(f"PROFITABLE TRADES (Profit >= $5)")
    print(f"{'='*60}")
    
    for i, trade in enumerate(trades, 1):
        user_info = await get_user_info(trade["telegram_id"])
        pnl = float(trade.get("pnl_usdt", 0))
        print(f"\n{i}. Trade #{trade['id']}")
        print(f"   User: {user_info['first_name']} (ID: {trade['telegram_id']})")
        print(f"   Symbol: {trade['symbol']} {trade['side']}")
        print(f"   Profit: ${pnl:.2f} USDT")
        print(f"   Leverage: {trade['leverage']}x")
        print(f"   Closed: {trade['closed_at']}")
    
    # Step 2: Get target users
    print(f"\n{'='*60}")
    print("📊 Step 2: Fetching target users...")
    print(f"{'='*60}")
    target_users = await get_target_users()
    
    if not target_users:
        print("\n⚠️  No target users found!")
        print("   All users already have autotrade active.")
        return
    
    # Step 3: Ask user what to do
    print(f"\n{'='*60}")
    print("🎯 BROADCAST OPTIONS")
    print(f"{'='*60}")
    print(f"\nFound {len(trades)} profitable trades")
    print(f"Target: {len(target_users)} non-autotrade users")
    print(f"\nOptions:")
    print(f"1. DRY RUN - Show what would be sent (no actual broadcast)")
    print(f"2. TEST - Send to first 5 users only")
    print(f"3. BROADCAST - Send to ALL {len(target_users)} users")
    print(f"4. EXIT - Cancel")
    
    choice = input(f"\nYour choice (1-4): ").strip()
    
    if choice == "4":
        print("\n❌ Cancelled by user")
        return
    
    # Initialize bot
    print("\n🤖 Initializing Telegram bot...")
    from telegram import Bot
    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN/TOKEN/TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    bot = Bot(token=bot_token)
    
    # Process based on choice
    if choice == "1":
        # Dry run - show all
        print(f"\n{'='*60}")
        print("🔍 DRY RUN MODE - Showing all broadcasts")
        print(f"{'='*60}")
        
        for trade in trades:
            await test_broadcast_single_trade(trade, target_users, bot, dry_run=True)
            await asyncio.sleep(1)
    
    elif choice == "2":
        # Test mode - send to first 5 users
        print(f"\n{'='*60}")
        print("🧪 TEST MODE - Sending to first 5 users")
        print(f"{'='*60}")
        
        test_users = target_users[:5]
        print(f"\nTest users:")
        for u in test_users:
            print(f"  - {u['first_name']} (ID: {u['telegram_id']})")
        
        confirm = input(f"\nSend test broadcast? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("❌ Cancelled")
            return
        
        # Use first profitable trade
        trade = trades[0]
        result = await test_broadcast_single_trade(trade, test_users, bot, dry_run=False)
        
        print(f"\n✅ Test complete!")
        print(f"   Sent: {result['sent']}")
        print(f"   Failed: {result['failed']}")
    
    elif choice == "3":
        # Full broadcast
        print(f"\n{'='*60}")
        print("📢 FULL BROADCAST MODE")
        print(f"{'='*60}")
        print(f"\n⚠️  WARNING: This will send to {len(target_users)} users!")
        print(f"   Using trade: #{trades[0]['id']} (${float(trades[0]['pnl_usdt']):.2f} profit)")
        
        confirm = input(f"\nAre you SURE? Type 'BROADCAST' to confirm: ").strip()
        if confirm != "BROADCAST":
            print("❌ Cancelled")
            return
        
        # Use first profitable trade
        trade = trades[0]
        result = await test_broadcast_single_trade(trade, target_users, bot, dry_run=False)
        
        print(f"\n{'='*60}")
        print("✅ BROADCAST COMPLETE!")
        print(f"{'='*60}")
        print(f"Sent: {result['sent']}")
        print(f"Failed: {result['failed']}")
        print(f"Success rate: {result['sent']/(result['sent']+result['failed'])*100:.1f}%")
    
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
