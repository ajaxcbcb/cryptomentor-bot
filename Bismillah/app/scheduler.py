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
        try:
            from app.supabase_repo import _client
            from app.handlers_autotrade import get_user_api_keys
            from app.autotrade_engine import start_engine, is_running

            res = _client().table("autotrade_sessions").select("*").eq("status", "active").execute()
            sessions = res.data or []
            logger.info(f"[AutoTrade] Found {len(sessions)} active sessions to restore")

            restored = 0
            failed_users = []

            for session in sessions:
                user_id = session.get("telegram_id")
                if not user_id:
                    continue
                if is_running(user_id):
                    logger.info(f"[AutoTrade] Engine already running for user {user_id}, skip")
                    continue

                keys = get_user_api_keys(user_id)
                if not keys:
                    logger.warning(f"[AutoTrade] No API keys for user {user_id}, skipping")
                    failed_users.append(user_id)
                    # Beritahu user bahwa engine tidak bisa di-restore
                    try:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=(
                                "⚠️ <b>AutoTrade could not be resumed</b>\n\n"
                                "API Key not found. Please set it up again:\n"
                                "/autotrade → Input API Key"
                            ),
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass
                    continue

                amount   = float(session.get("initial_deposit") or 10)
                leverage = int(session.get("leverage") or 10)

                try:
                    start_engine(
                        bot=application.bot,
                        user_id=user_id,
                        api_key=keys["api_key"],
                        api_secret=keys["api_secret"],
                        amount=amount,
                        leverage=leverage,
                        notify_chat_id=user_id,
                    )
                    restored += 1
                    logger.info(f"[AutoTrade] Engine restored for user {user_id} (amount={amount}, lev={leverage}x)")

                    # Notify user that engine is active again
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🔄 <b>AutoTrade Engine Resumed</b>\n\n"
                            "The bot just restarted and your engine is automatically active again.\n\n"
                            f"💰 Capital: <b>{amount} USDT</b>\n"
                            f"⚡ Leverage: <b>{leverage}x</b>\n"
                            f"🤖 Status: <b>ACTIVE — Scanning market...</b>\n\n"
                            "The engine is looking for high-quality setups. "
                            "You'll receive a notification when an order is placed."
                        ),
                        parse_mode='HTML'
                    )

                except Exception as e:
                    logger.error(f"[AutoTrade] Failed to restore engine for user {user_id}: {e}")
                    failed_users.append(user_id)
                    try:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"⚠️ <b>AutoTrade failed to resume</b>\n\n"
                                f"Error: {e}\n\n"
                                "Please restart manually: /autotrade"
                            ),
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass

            logger.info(f"[AutoTrade] Restore complete: {restored} restored, {len(failed_users)} failed")

        except Exception as e:
            logger.error(f"[AutoTrade] Auto-restore failed: {e}")

        # ── Startup: cek open trades di DB vs kondisi market sekarang ─
        await asyncio.sleep(5)  # beri waktu engine start dulu
        await _check_stale_positions(application)

        # ── Start scheduler tasks ─────────────────────────────────────
        task_scheduler.running = True
        logger.info("[ROCKET] Scheduler started")

    asyncio.create_task(_start())


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

