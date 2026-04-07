"""
Maintenance Notification System
Notifies users with inactive engines after bot restart/maintenance
"""

import logging
import asyncio
from typing import List, Dict

logger = logging.getLogger(__name__)


async def send_maintenance_notifications(bot):
    """
    Send notifications to users with autotrade sessions after bot restart.
    Notifies about engine status (active/inactive).
    """
    logger.info("=" * 80)
    logger.info("[Maintenance] Sending notifications to users with autotrade sessions...")
    logger.info("=" * 80)
    
    try:
        from app.supabase_repo import _client
        from app.autotrade_engine import is_running
        
        # Query ALL autotrade sessions (any status - notify everyone who ever used autotrade)
        # This includes: active, stopped, uid_verified, etc.
        result = _client().table("autotrade_sessions").select("*").execute()
        
        sessions = result.data or []
        
        if not sessions:
            logger.info("[Maintenance] No autotrade sessions found")
            return
        
        logger.info(f"[Maintenance] Found {len(sessions)} autotrade sessions")
        
        # Send notifications to ALL users
        sent = 0
        failed = 0
        active_count = 0
        inactive_count = 0
        
        for session in sessions:
            user_id = session.get("telegram_id")
            if not user_id:
                continue
            
            # Check if engine is running
            engine_running = is_running(user_id)
            
            if engine_running:
                active_count += 1
                # Send notification for active engine
                message = (
                    "🔧 <b>Pemberitahuan Maintenance</b>\n\n"
                    "Bot baru saja selesai maintenance.\n\n"
                    "📊 <b>Status Engine Anda:</b>\n"
                    "• Engine: <b>✅ Active</b>\n"
                    "• Trading: <b>Running</b>\n\n"
                    "💡 <b>Apa artinya?</b>\n"
                    "Engine AutoTrade Anda sudah aktif kembali secara otomatis dan siap trading.\n\n"
                    "Gunakan <code>/autotrade</code> untuk melihat status lengkap."
                )
            else:
                inactive_count += 1
                # Send notification for inactive engine
                message = (
                    "🔧 <b>Pemberitahuan Maintenance</b>\n\n"
                    "Bot baru saja selesai maintenance dan engine AutoTrade Anda saat ini <b>tidak aktif</b>.\n\n"
                    "📊 <b>Status:</b>\n"
                    "• Engine: <b>❌ Inactive</b>\n"
                    "• Trading: <b>Stopped</b>\n\n"
                    "💡 <b>Apa yang harus dilakukan?</b>\n"
                    "Untuk melanjutkan trading, silakan aktifkan kembali engine Anda secara manual:\n\n"
                    "👉 Ketik: <code>/autotrade</code>\n\n"
                    "Kemudian pilih <b>Start Engine</b> untuk mengaktifkan kembali.\n\n"
                    "⚠️ <b>Penting:</b> Engine tidak akan trading sampai Anda mengaktifkannya kembali."
                )
            
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
                sent += 1
                status = "Active" if engine_running else "Inactive"
                logger.info(f"[Maintenance] ✅ Notified user {user_id} (Engine: {status})")
                
            except Exception as e:
                failed += 1
                logger.error(f"[Maintenance] ❌ Failed to notify user {user_id}: {e}")
        
        logger.info("=" * 80)
        logger.info(f"[Maintenance] Notification Summary:")
        logger.info(f"  📤 Sent: {sent}")
        logger.info(f"  ❌ Failed: {failed}")
        logger.info(f"  ✅ Active engines: {active_count}")
        logger.info(f"  ❌ Inactive engines: {inactive_count}")
        logger.info(f"  📊 Total users: {len(sessions)}")
        logger.info("=" * 80)
        
        # Schedule follow-up reminder for inactive engines (1 hour later)
        if inactive_count > 0:
            logger.info(f"[Maintenance] Scheduling follow-up reminder in 1 hour for {inactive_count} inactive engines")
            asyncio.create_task(_send_delayed_reminder(bot, sessions))
        
    except Exception as e:
        logger.error(f"[Maintenance] Critical error: {e}")
        import traceback
        traceback.print_exc()


async def _send_delayed_reminder(bot, sessions: List[Dict]):
    """
    Send a follow-up reminder 1 hour after maintenance for users with inactive engines.
    This ensures users who missed the first notification get a second chance.
    """
    try:
        # Wait 1 hour
        await asyncio.sleep(3600)
        
        logger.info("=" * 80)
        logger.info("[Maintenance] Sending 1-hour follow-up reminders...")
        logger.info("=" * 80)
        
        from app.autotrade_engine import is_running
        
        sent = 0
        still_inactive = 0
        
        for session in sessions:
            user_id = session.get("telegram_id")
            if not user_id:
                continue
            
            # Only remind if engine is STILL inactive after 1 hour
            if not is_running(user_id):
                still_inactive += 1
                
                message = (
                    "⏰ <b>Reminder: Engine Masih Inactive</b>\n\n"
                    "Sudah 1 jam sejak maintenance selesai, tapi engine AutoTrade Anda masih belum aktif.\n\n"
                    "📊 <b>Status:</b>\n"
                    "• Engine: <b>❌ Inactive</b>\n"
                    "• Trading: <b>Stopped</b>\n\n"
                    "💡 <b>Apa yang harus dilakukan?</b>\n"
                    "Untuk melanjutkan trading, aktifkan engine Anda:\n\n"
                    "👉 Ketik: <code>/autotrade</code>\n"
                    "Kemudian pilih <b>Start Engine</b>\n\n"
                    "⚠️ <b>Penting:</b> Engine tidak akan trading sampai Anda mengaktifkannya kembali."
                )
                
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    sent += 1
                    logger.info(f"[Maintenance] ✅ Reminder sent to user {user_id}")
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"[Maintenance] ❌ Failed to send reminder to user {user_id}: {e}")
        
        logger.info("=" * 80)
        logger.info(f"[Maintenance] Follow-up Reminder Summary:")
        logger.info(f"  📤 Reminders sent: {sent}")
        logger.info(f"  ❌ Still inactive: {still_inactive}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"[Maintenance] Follow-up reminder error: {e}")
        import traceback
        traceback.print_exc()

