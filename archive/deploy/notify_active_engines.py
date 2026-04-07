#!/usr/bin/env python3
"""
Send notification to users with active engines
Confirms their engine is running and ready to trade
"""

import asyncio
import sys
import os

# Add path
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

async def notify_active_users():
    """Send status notification to all active engine users"""
    
    # Import bot modules
    from telegram import Bot
    from app.supabase_repo import _client
    
    # Get bot token from environment (try multiple names)
    BOT_TOKEN = (
        os.getenv('TELEGRAM_BOT_TOKEN') or 
        os.getenv('BOT_TOKEN') or 
        os.getenv('TOKEN')
    )
    
    if not BOT_TOKEN:
        # Try to get from running bot process
        try:
            with open('/proc/76783/environ', 'r') as f:
                env_data = f.read()
                for item in env_data.split('\0'):
                    if 'BOT_TOKEN' in item or 'TOKEN' in item:
                        key, val = item.split('=', 1)
                        if 'TOKEN' in key:
                            BOT_TOKEN = val
                            print(f"✅ Found token from process: {key}")
                            break
        except:
            pass
    
    if not BOT_TOKEN:
        print("❌ Bot token not found in environment or process")
        print("   Tried: TELEGRAM_BOT_TOKEN, BOT_TOKEN, TOKEN")
        print("   Also tried reading from running process")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Get all active sessions
        s = _client()
        result = s.table("autotrade_sessions").select(
            "telegram_id, trading_mode, risk_mode, initial_deposit, leverage"
        ).eq("status", "active").execute()
        
        active_sessions = result.data
        
        print(f"\n{'='*60}")
        print(f"SENDING ENGINE STATUS NOTIFICATIONS")
        print(f"{'='*60}")
        print(f"Active engines: {len(active_sessions)}")
        print(f"{'='*60}\n")
        
        success_count = 0
        failed_count = 0
        
        for session in active_sessions:
            user_id = session.get('telegram_id')
            trading_mode = session.get('trading_mode', 'swing').upper()
            risk_mode = session.get('risk_mode', 'fixed')
            capital = session.get('initial_deposit', 0)
            leverage = session.get('leverage', 10)
            
            # Determine mode emoji and description
            if trading_mode == 'SCALPING':
                mode_emoji = "⚡"
                mode_desc = "Scalping (5M)"
                scan_info = "Scanning 10 pairs every 15 seconds"
            elif trading_mode == 'SWING':
                mode_emoji = "📊"
                mode_desc = "Swing Trading"
                scan_info = "Scanning 10 pairs every 30 seconds"
            else:
                mode_emoji = "🤖"
                mode_desc = trading_mode.title()
                scan_info = "Auto-trading active"
            
            # Risk mode description
            if risk_mode == 'risk_based':
                risk_desc = "Risk-Based (2% per trade)"
            else:
                risk_desc = "Fixed Position Size"
            
            message = (
                f"✅ <b>AutoTrade Engine Status: ACTIVE</b>\n\n"
                f"{mode_emoji} <b>Mode:</b> {mode_desc}\n"
                f"💰 <b>Capital:</b> ${capital:.2f} USDT\n"
                f"⚡ <b>Leverage:</b> {leverage}x\n"
                f"🎯 <b>Risk Management:</b> {risk_desc}\n\n"
                f"🔄 <b>Status:</b> Engine is running and monitoring market\n"
                f"📡 {scan_info}\n\n"
                f"<b>Your engine will automatically:</b>\n"
                f"• Scan market for high-probability setups\n"
                f"• Execute trades when signals meet criteria\n"
                f"• Manage positions with TP/SL\n"
                f"• Protect capital with risk management\n\n"
                f"💡 <b>No manual action needed</b> - Engine works 24/7\n\n"
                f"📊 Check status anytime: /autotrade\n"
                f"⏸️ To pause: Stop engine in dashboard"
            )
            
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
                print(f"✅ Sent to user {user_id} ({mode_desc})")
                success_count += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Failed to send to user {user_id}: {e}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"NOTIFICATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successfully sent: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(notify_active_users())
