"""

Scheduler - Jadwal otomatis untuk sync logs dan kirim laporan mingguan

Menggunakan local G: drive sync (lebih simple dari API)

"""

import asyncio

from datetime import datetime, time

import logging



logger = logging.getLogger(__name__)

# Global signal toggle state
_signal_enabled = True

def get_signal_status() -> bool:
    return _signal_enabled

def toggle_signal(enabled: bool):
    global _signal_enabled
    _signal_enabled = enabled
    logger.info(f"Auto signal toggled: {'ON' if enabled else 'OFF'}")


class TaskScheduler:

    """Scheduler untuk task otomatis"""

    

    def __init__(self):

        self.running = False

    

    async def daily_sync_task(self):

        """Task sync harian ke G: drive atau Supabase (setiap jam 23:00)"""

        import os

        from datetime import timedelta

        

        while self.running:

            now = datetime.now()

            

            # Hitung waktu sampai jam 23:00

            target_time = now.replace(hour=23, minute=0, second=0, microsecond=0)

            if now >= target_time:

                # Jika sudah lewat jam 23:00, jadwalkan untuk besok

                target_time = target_time + timedelta(days=1)

            

            wait_seconds = (target_time - now).total_seconds()

            

            logger.info(f"Next daily sync in {wait_seconds/3600:.1f} hours")

            await asyncio.sleep(wait_seconds)

            

            # Sync logs - auto-detect environment

            try:

                use_gdrive = os.getenv('USE_GDRIVE', 'true').lower() == 'true'

                

                if use_gdrive and os.path.exists('G:/'):

                    # Local: Sync to G: drive

                    from app.local_gdrive_sync import local_gdrive_sync

                    synced, failed = local_gdrive_sync.sync_all_logs()

                    logger.info(f"[OK] G: drive sync: {synced} files synced, {failed} failed")

                else:

                    # Railway: Upload to Supabase

                    from app.supabase_storage import supabase_storage

                    uploaded, failed = supabase_storage.upload_all_logs()

                    logger.info(f"[OK] Supabase upload: {uploaded} files uploaded, {failed} failed")

                    

            except Exception as e:

                logger.error(f"Daily sync failed: {e}")

    

    async def weekly_report_task(self):

        """Task laporan mingguan (setiap Senin jam 09:00)"""

        from app.weekly_report import weekly_reporter

        from datetime import timedelta

        

        while self.running:

            now = datetime.now()

            

            # Hitung hari sampai Senin berikutnya

            days_until_monday = (7 - now.weekday()) % 7

            if days_until_monday == 0 and now.hour >= 9:

                days_until_monday = 7

            

            target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)

            target_time = target_time + timedelta(days=days_until_monday)

            

            wait_seconds = (target_time - now).total_seconds()

            

            logger.info(f"Next weekly report in {wait_seconds/3600:.1f} hours")

            await asyncio.sleep(wait_seconds)

            

            # Generate dan kirim laporan

            try:

                await weekly_reporter.generate_and_send()

                logger.info("[OK] Weekly report sent to admins")

            except Exception as e:

                logger.error(f"Weekly report failed: {e}")

    

    async def start(self):

        """Start semua scheduled tasks"""

        self.running = True

        logger.info("[ROCKET] Scheduler started")

        

        # Jalankan tasks secara parallel

        await asyncio.gather(

            self.daily_sync_task(),

            self.weekly_report_task()

        )

    

    def stop(self):

        """Stop scheduler"""

        self.running = False

        logger.info("[STOP] Scheduler stopped")



# Global instance

task_scheduler = TaskScheduler()


def start_scheduler(application):
    """Start scheduler dan auto-restart autotrade engines."""
    import asyncio

    async def _start():
        # Tunggu bot fully ready sebelum restore
        await asyncio.sleep(3)

        # ── Auto-restore autotrade engines ────────────────────────────
        logger.info("="*80)
        logger.info("[AutoRestore] Starting engine restoration process...")
        logger.info("="*80)
        
        try:
            from app.supabase_repo import _client
            from app.handlers_autotrade import get_user_api_keys
            from app.autotrade_engine import start_engine, is_running
            from app.engine_restore import migrate_to_risk_based, set_scalping_mode
            from app.skills_repo import has_skill

            # Query sessions that should be restored (exclude stopped, pending, rejected)
            # CRITICAL: Do NOT restore "stopped" engines - user explicitly stopped them
            res = _client().table("autotrade_sessions").select("*").not_.in_(
                "status", ["pending_verification", "uid_rejected", "pending", "stopped"]
            ).execute()
            sessions = res.data or []
            logger.info(f"[AutoRestore] Found {len(sessions)} active sessions to restore (excluding stopped)")

            restored = 0
            skipped = 0
            failed_users = []
            
            logger.info(f"[AutoRestore] Processing {len(sessions)} sessions...")

            for session in sessions:
                user_id = session.get("telegram_id")
                if not user_id:
                    logger.warning(f"[AutoRestore] Session missing telegram_id, skipping")
                    continue
                
                # Skip dummy/test users
                if user_id >= 999999990:
                    logger.debug(f"[AutoRestore] Skipping dummy user {user_id}")
                    continue
                
                # Check if already running
                if is_running(user_id):
                    logger.info(f"[AutoRestore] User {user_id} - Engine already running, skip")
                    skipped += 1
                    continue

                # Get API keys
                keys = get_user_api_keys(user_id)
                if not keys:
                    logger.warning(f"[AutoRestore] User {user_id} - No API keys found, notifying user")
                    failed_users.append(user_id)
                    async def _notify_no_key(uid):
                        try:
                            await application.bot.send_message(
                                chat_id=uid,
                                text=(
                                    "⚠️ <b>AutoTrade Could Not Resume</b>\n\n"
                                    "Your engine was active but API keys are missing.\n\n"
                                    "Please set up your API keys again:\n"
                                    "/autotrade → Settings → Change API Key"
                                ),
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            logger.error(f"[AutoRestore] Failed to notify user {uid}: {e}")
                    asyncio.create_task(_notify_no_key(user_id))
                    continue

                # Get session settings
                amount = float(session.get("initial_deposit") or 10)
                leverage = int(session.get("leverage") or 10)
                trading_mode = session.get("trading_mode", "swing")
                exchange_id = keys.get("exchange", "bitunix")

                logger.info(
                    f"[AutoRestore] User {user_id} - Restoring: "
                    f"{trading_mode} mode, {amount} USDT, {leverage}x, {exchange_id}"
                )

                try:
                    # Migrate to risk-based mode for safety (if not already)
                    migrate_to_risk_based(user_id)
                    
                    # Preserve user's trading mode preference (don't force scalping)
                    # Only set scalping if they don't have a mode set
                    if not trading_mode or trading_mode == "swing":
                        logger.info(f"[AutoRestore] User {user_id} - Setting to scalping mode (default)")
                        set_scalping_mode(user_id)
                    else:
                        logger.info(f"[AutoRestore] User {user_id} - Keeping {trading_mode} mode")
                    
                    # Check premium status
                    is_premium = has_skill(user_id, "dual_tp_rr3")
                    
                    # Start engine
                    start_engine(
                        bot=application.bot,
                        user_id=user_id,
                        api_key=keys["api_key"],
                        api_secret=keys["api_secret"],
                        amount=amount,
                        leverage=leverage,
                        notify_chat_id=user_id,
                        is_premium=is_premium,
                        silent=False,  # Send notification so user knows engine restarted
                        exchange_id=exchange_id,
                    )
                    restored += 1
                    logger.info(f"[AutoRestore] User {user_id} - ✅ Engine started successfully")

                    # Send detailed startup notification with full config (await directly)
                    try:
                        # Get trading mode details
                        from app.trading_mode_manager import TradingMode
                        is_scalping = trading_mode == "scalping"
                        
                        if is_scalping:
                            # Scalping mode notification
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "⚡ <b>Scalping Engine Active!</b>\n\n"
                                    "Mode: <b>Scalping (5M)</b>\n\n"
                                    "<b>Configuration:</b>\n"
                                    "• Timeframe: <b>5m</b>\n"
                                    "• Scan interval: <b>15s</b>\n"
                                    "• Min confidence: <b>80%</b>\n"
                                    "• Min R:R: <b>1:1.5</b>\n"
                                    "• Max hold time: <b>30 minutes</b>\n"
                                    f"• Max concurrent: <b>4 positions</b>\n"
                                    "• Trading pairs: <b>10 pairs</b>\n\n"
                                    f"💰 Capital: <b>{amount} USDT</b>\n"
                                    f"⚡ Leverage: <b>{leverage}x</b>\n\n"
                                    "Bot will scan for high-probability setups every 15 seconds.\n"
                                    "Patience = profit. 🎯"
                                ),
                                parse_mode='HTML'
                            )
                            logger.info(f"[AutoRestore] User {user_id} - ✅ Scalping notification sent")
                        else:
                            # Swing mode notification
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "📊 <b>Swing Engine Active!</b>\n\n"
                                    "Mode: <b>Swing (15M)</b>\n\n"
                                    "<b>Configuration:</b>\n"
                                    "• Timeframe: <b>15m</b>\n"
                                    "• Scan interval: <b>45s</b>\n"
                                    "• Min confidence: <b>68%</b>\n"
                                    "• Min R:R: <b>1:2</b>\n"
                                    f"• Max concurrent: <b>4 positions</b>\n"
                                    "• Trading pairs: <b>10 pairs</b>\n\n"
                                    f"💰 Capital: <b>{amount} USDT</b>\n"
                                    f"⚡ Leverage: <b>{leverage}x</b>\n\n"
                                    "Bot will scan for high-quality setups every 45 seconds.\n"
                                    "Professional trading = patience. 🎯"
                                ),
                                parse_mode='HTML'
                            )
                            logger.info(f"[AutoRestore] User {user_id} - ✅ Swing notification sent")
                    except Exception as e:
                        logger.error(f"[AutoRestore] Failed to notify user {user_id}: {e}")

                except Exception as e:
                    logger.error(f"[AutoRestore] User {user_id} - ❌ Failed to restore: {e}")
                    import traceback
                    traceback.print_exc()
                    failed_users.append(user_id)
                    
                    async def _notify_failed(uid, err):
                        try:
                            await application.bot.send_message(
                                chat_id=uid,
                                text=(
                                    "⚠️ <b>AutoTrade Failed to Resume</b>\n\n"
                                    f"Error: {str(err)[:100]}\n\n"
                                    "Please restart manually: /autotrade"
                                ),
                                parse_mode='HTML'
                            )
                        except Exception as e2:
                            logger.error(f"[AutoRestore] Failed to notify user {uid}: {e2}")
                    asyncio.create_task(_notify_failed(user_id, e))

            logger.info("="*80)
            logger.info(f"[AutoRestore] Restoration Summary:")
            logger.info(f"  ✅ Restored: {restored}")
            logger.info(f"  ⏭️  Skipped (already running): {skipped}")
            logger.info(f"  ❌ Failed: {len(failed_users)}")
            logger.info(f"  📊 Total sessions: {len(sessions)}")
            if failed_users:
                logger.info(f"  Failed users: {failed_users}")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"[AutoRestore] Critical error in restoration process: {e}")
            import traceback
            traceback.print_exc()

        # ── Send maintenance notifications to users with inactive engines ─
        # Wait longer for engines to fully start before checking status
        # Engine tasks are created but need time to initialize
        await asyncio.sleep(30)  # Give engines 30s to fully start and register
        try:
            from app.maintenance_notifier import send_maintenance_notifications
            # Pass restored users so notifier knows who was successfully restored
            await send_maintenance_notifications(application.bot, restored_user_ids=set(
                s.get("telegram_id") for s in sessions
                if s.get("telegram_id") and s.get("telegram_id") < 999999990
                and s.get("status") not in ("stopped", "pending_verification", "uid_rejected", "pending")
            ))
        except Exception as e:
            logger.error(f"[Maintenance] Failed to send notifications: {e}")
            import traceback
            traceback.print_exc()

        # ── Startup: cek open trades di DB vs kondisi market sekarang ─
        await asyncio.sleep(5)  # beri waktu engine start dulu
        await _check_stale_positions(application)

        # ── Start scheduler tasks ─────────────────────────────────────
        task_scheduler.running = True
        logger.info("[ROCKET] Scheduler started")

        # ── AutoTrade daily reminder ───────────────────────────────────
        asyncio.create_task(_autotrade_reminder_task(application))
        
        # ── Engine health check (every 5 minutes) ──────────────────────
        asyncio.create_task(_engine_health_check_task(application))

    asyncio.create_task(_start())


async def _engine_health_check_task(application):
    """
    Periodic health check for autotrade engines.
    Checks every 2 minutes if engines that should be running are still alive.
    Auto-restarts if they stopped unexpectedly.
    """
    from datetime import timedelta
    
    CHECK_INTERVAL_SECONDS = 120  # 2 minutes (reduced from 5 for faster detection)
    
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            
            from app.supabase_repo import _client
            from app.autotrade_engine import is_running, start_engine
            from app.handlers_autotrade import get_user_api_keys
            from app.skills_repo import has_skill
            
            # Get sessions that should be running (exclude stopped, pending, rejected)
            # CRITICAL: Do NOT restart "stopped" engines - user explicitly stopped them
            res = _client().table("autotrade_sessions").select("*").not_.in_(
                "status", ["pending_verification", "uid_rejected", "pending", "stopped"]
            ).execute()
            sessions = res.data or []
            
            if not sessions:
                continue
            
            dead_engines = []
            
            # Check each session
            for session in sessions:
                user_id = session.get("telegram_id")
                if not user_id:
                    continue
                
                # Skip dummy/test users (IDs like 999999999)
                if user_id >= 999999990:
                    continue
                
                # Check if engine is running
                if not is_running(user_id):
                    dead_engines.append(user_id)
                    logger.warning(f"[HealthCheck] User {user_id} - Engine should be running but is DEAD!")
            
            if dead_engines:
                logger.warning(f"[HealthCheck] ⚠️ Found {len(dead_engines)} DEAD engines: {dead_engines}")
                logger.warning(f"[HealthCheck] Attempting auto-restart for {len(dead_engines)} users...")
                
                for user_id in dead_engines:
                    try:
                        # Get session info
                        session = next((s for s in sessions if s.get("telegram_id") == user_id), None)
                        if not session:
                            continue
                        
                        # Get API keys
                        keys = get_user_api_keys(user_id)
                        if not keys:
                            logger.error(f"[HealthCheck] User {user_id} - No API keys, cannot restart")
                            # Notify user
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "⚠️ <b>AutoTrade Engine Stopped</b>\n\n"
                                    "Your engine stopped unexpectedly and cannot auto-restart because API keys are missing.\n\n"
                                    "Please restart manually: /autotrade"
                                ),
                                parse_mode='HTML'
                            )
                            continue
                        
                        # Get settings
                        amount = float(session.get("initial_deposit") or 10)
                        leverage = int(session.get("leverage") or 10)
                        trading_mode = session.get("trading_mode", "scalping")
                        exchange_id = keys.get("exchange", "bitunix")
                        is_premium = has_skill(user_id, "dual_tp_rr3")
                        
                        # Restart engine
                        start_engine(
                            bot=application.bot,
                            user_id=user_id,
                            api_key=keys["api_key"],
                            api_secret=keys["api_secret"],
                            amount=amount,
                            leverage=leverage,
                            notify_chat_id=user_id,
                            is_premium=is_premium,
                            silent=False,
                            exchange_id=exchange_id,
                        )
                        
                        logger.info(f"[HealthCheck] User {user_id} - ✅ Engine restarted")
                        
                        # Notify user
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=(
                                "🔄 <b>AutoTrade Engine Auto-Restarted</b>\n\n"
                                "Your engine stopped unexpectedly and has been automatically restarted.\n\n"
                                f"📊 Mode: <b>{trading_mode.title()}</b>\n"
                                f"💰 Capital: <b>{amount} USDT</b>\n"
                                f"⚡ Leverage: <b>{leverage}x</b>\n\n"
                                "If this happens frequently, please contact support.\n\n"
                                "Use /autotrade to check status."
                            ),
                            parse_mode='HTML'
                        )
                        
                    except Exception as e:
                        logger.error(f"[HealthCheck] Failed to restart user {user_id}: {e}")
                        # Notify user of failure
                        try:
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "⚠️ <b>AutoTrade Engine Stopped</b>\n\n"
                                    "Your engine stopped and auto-restart failed.\n\n"
                                    "Please restart manually: /autotrade"
                                ),
                                parse_mode='HTML'
                            )
                        except:
                            pass
            else:
                logger.info(f"[HealthCheck] All {len(sessions)} engines are healthy ✅")
        
        except Exception as e:
            logger.error(f"[HealthCheck] Error in health check task: {e}")
            import traceback
            traceback.print_exc()
            # Continue running despite errors
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _check_stale_positions(application):
    """
    Saat startup: baca semua open trades dari DB, cek apakah arahnya
    masih sesuai dengan kondisi market sekarang. Jika berlawanan,
    kirim alert ke user dan biarkan engine handle flip-nya.
    """
    try:
        from app.trade_history import get_all_open_trades
        from app.autotrade_engine import _compute_signal_pro, _is_reversal
        import asyncio

        open_trades = get_all_open_trades()
        if not open_trades:
            logger.info("[StartupCheck] No open trades in DB to check")
            return

        logger.info(f"[StartupCheck] Checking {len(open_trades)} open trades against current market")

        # Group by user
        by_user: dict = {}
        for t in open_trades:
            uid = t["telegram_id"]
            by_user.setdefault(uid, []).append(t)

        for user_id, trades in by_user.items():
            alerts = []
            for trade in trades:
                symbol    = trade.get("symbol", "")
                side      = trade.get("side", "LONG")   # LONG / SHORT
                base_sym  = symbol.replace("USDT", "")
                open_side = "BUY" if side == "LONG" else "SELL"

                try:
                    sig = await asyncio.to_thread(_compute_signal_pro, base_sym)
                except Exception:
                    continue

                if not sig:
                    continue

                new_side  = sig.get("side", "")
                trend_1h  = sig.get("trend_1h", "NEUTRAL")
                struct    = sig.get("market_structure", "ranging")
                conf      = sig.get("confidence", 0)

                # Cek apakah arah berlawanan
                is_against = (
                    (side == "LONG"  and new_side == "SHORT") or
                    (side == "SHORT" and new_side == "LONG")
                )

                if is_against:
                    alerts.append(
                        f"⚠️ <b>{symbol}</b>: Position <b>{side}</b> but current signal is <b>{new_side}</b>\n"
                        f"   1H: {trend_1h} | Struct: {struct} | Conf: {conf}%"
                    )
                    logger.warning(
                        f"[StartupCheck] STALE POSITION user={user_id} {symbol} "
                        f"{side} vs signal {new_side} (conf={conf}%)"
                    )

            if alerts:
                alert_text = "\n".join(alerts)
                try:
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🔍 <b>Startup Check — Conflicting Positions Detected</b>\n\n"
                            f"{alert_text}\n\n"
                            "Engine is active and will automatically flip if all "
                            "CHoCH conditions are met (confidence ≥75%, 1H trend flip, structure confirmed)."
                        ),
                        parse_mode='HTML'
                    )
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"[StartupCheck] Failed: {e}")



async def _autotrade_reminder_task(application):
    """
    Task harian: kirim reminder autotrade ke user yang belum daftar.
    Jalan setiap hari jam 10:00 WIB (03:00 UTC).
    """
    from datetime import timedelta

    REMINDER_HOUR_UTC = 3   # 10:00 WIB = 03:00 UTC
    REMINDER_MINUTE   = 0

    while True:
        try:
            now = datetime.utcnow()
            target = now.replace(hour=REMINDER_HOUR_UTC, minute=REMINDER_MINUTE, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            logger.info(f"[Reminder] Next autotrade reminder in {wait_seconds/3600:.1f} hours")
            await asyncio.sleep(wait_seconds)

            from app.autotrade_reminder import send_autotrade_reminders
            await send_autotrade_reminders(application.bot)

        except Exception as e:
            logger.error(f"[Reminder] Task error: {e}")
            await asyncio.sleep(3600)  # retry 1 jam kemudian kalau error
