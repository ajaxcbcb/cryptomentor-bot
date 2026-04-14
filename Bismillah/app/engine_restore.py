"""
Auto-restore autotrade engines on bot restart
Ensures all active users continue trading after bot restart
"""

import asyncio
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def get_active_sessions() -> List[Dict]:
    """Get all active autotrade sessions from Supabase."""
    try:
        from app.supabase_repo import _client
        s = _client()
        
        # Get all sessions with status = active or uid_verified
        result = s.table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        return []


def migrate_to_risk_based(user_id: int) -> bool:
    """
    Migrate user to risk-based mode if not already set.
    Returns True if migration successful or already risk-based.
    """
    try:
        from app.supabase_repo import _client, get_risk_mode, set_risk_mode, set_risk_per_trade
        
        current_mode = get_risk_mode(user_id)
        
        # If already risk-based, no migration needed
        if current_mode == "risk_based":
            logger.info(f"[Restore] User {user_id} already risk-based")
            return True
        
        # Migrate to risk-based with default 2% risk
        set_risk_mode(user_id, "risk_based")
        set_risk_per_trade(user_id, 2.0)  # Default 2% risk
        
        logger.info(f"[Restore] Migrated user {user_id} to risk-based mode (2% risk)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate user {user_id} to risk-based: {e}")
        return False


def set_scalping_mode(user_id: int) -> bool:
    """
    Set user trading mode to Scalping for max 4 concurrent positions.
    Returns True if successful.
    """
    try:
        from app.trading_mode_manager import TradingModeManager, TradingMode
        
        # Set to scalping mode
        TradingModeManager.set_mode(user_id, TradingMode.SCALPING)
        
        logger.info(f"[Restore] Set user {user_id} to Scalping mode")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set scalping mode for user {user_id}: {e}")
        return False


async def reconcile_coordinator_state(user_id: int, client) -> None:
    """
    Reconcile multi-user symbol coordinator state from live exchange positions.

    This is called after engine start to restore coordinator state so that
    ownership tracking is in sync with actual open positions on the exchange.
    """
    try:
        from app.symbol_coordinator import get_coordinator
        from app.supabase_repo import _client as get_supabase

        coordinator = get_coordinator()

        # Get live positions from exchange
        try:
            exchange_positions = await asyncio.to_thread(
                client.get_open_positions
            )
            if not exchange_positions:
                exchange_positions = []
        except Exception as e:
            logger.warning(f"[Restore:{user_id}] Could not fetch exchange positions: {e}")
            exchange_positions = []

        # Get open trades from DB to provide ownership hints
        try:
            db = get_supabase()
            db_result = db.table("trades").select("*").eq(
                "user_id", user_id
            ).eq(
                "status", "open"
            ).execute()
            db_trades = db_result.data if db_result.data else []
        except Exception as e:
            logger.warning(f"[Restore:{user_id}] Could not fetch DB trades: {e}")
            db_trades = []

        # Reconcile with coordinator
        if exchange_positions or db_trades:
            notes = await coordinator.reconcile_user(user_id, exchange_positions, db_trades)
            if notes:
                for symbol, note in notes.items():
                    logger.info(f"[Restore:{user_id}] {symbol}: {note}")
        else:
            logger.info(f"[Restore:{user_id}] No positions to reconcile")

    except Exception as e:
        logger.error(f"[Restore:{user_id}] Coordinator reconciliation failed: {e}")
        # Non-fatal — engine can still run


def restore_user_engine(bot, session: Dict, keys: Dict) -> bool:
    """
    Restore autotrade engine for a single user.
    Returns True if successful.
    """
    try:
        user_id = int(session['telegram_id'])
        amount = float(session.get('initial_deposit', 0))
        leverage = int(session.get('leverage', 10))
        exchange_id = keys.get('exchange', 'bitunix')

        if amount <= 0:
            logger.warning(f"[Restore] User {user_id} has invalid balance: {amount}")
            return False

        # Migrate to risk-based mode
        if not migrate_to_risk_based(user_id):
            logger.warning(f"[Restore] Failed to migrate user {user_id}, skipping")
            return False

        # Set to scalping mode for max 4 concurrent positions
        set_scalping_mode(user_id)

        # Check if engine already running
        from app.autotrade_engine import is_running, start_engine
        if is_running(user_id):
            logger.info(f"[Restore] Engine already running for user {user_id}")
            return True

        # Check if user has premium skill
        from app.skills_repo import has_skill
        is_premium = has_skill(user_id, "dual_tp_rr3")

        # Start engine
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=amount,
            leverage=leverage,
            notify_chat_id=user_id,
            is_premium=is_premium,
            exchange_id=exchange_id,
        )

        # Schedule coordinator reconciliation in background
        # This restores ownership state from live exchange positions
        try:
            from app.exchange_clients import get_exchange_client
            client = get_exchange_client(user_id, keys['api_key'], keys['api_secret'], exchange_id)
            asyncio.create_task(reconcile_coordinator_state(user_id, client))
        except Exception as e:
            logger.warning(f"[Restore:{user_id}] Failed to schedule coordinator reconciliation: {e}")

        logger.info(
            f"[Restore] ✅ Engine restored for user {user_id} "
            f"(risk-based, scalping, {amount} USDT, {leverage}x)"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to restore engine for user {session.get('telegram_id')}: {e}")
        return False


async def restore_all_engines(bot):
    """
    Restore all active autotrade engines on bot startup.
    This ensures continuity after bot restart.
    """
    logger.info("=" * 60)
    logger.info("[Engine Restore] Starting auto-restore process...")
    logger.info("=" * 60)
    
    try:
        # Get all active sessions
        sessions = get_active_sessions()
        
        if not sessions:
            logger.info("[Engine Restore] No active sessions found")
            return
        
        logger.info(f"[Engine Restore] Found {len(sessions)} active session(s)")
        
        # Get API keys for all users
        from app.handlers_autotrade import get_user_api_keys
        
        restored = 0
        failed = 0
        skipped = 0
        
        for session in sessions:
            user_id = int(session['telegram_id'])
            
            # Get API keys
            keys = get_user_api_keys(user_id)
            if not keys:
                logger.warning(f"[Restore] No API keys for user {user_id}, skipping")
                skipped += 1
                continue
            
            # Restore engine
            if restore_user_engine(bot, session, keys):
                restored += 1
                
                # Send notification to user
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🔄 <b>AutoTrade Engine Restored</b>\n\n"
                            "✅ Your AutoTrade engine has been automatically restarted\n\n"
                            "📊 <b>New Settings:</b>\n"
                            "• Mode: <b>Risk-Based (Safer)</b>\n"
                            "• Trading: <b>Scalping (5M)</b>\n"
                            "• Max Positions: <b>4 concurrent</b>\n"
                            "• Risk per trade: <b>2%</b>\n\n"
                            "💡 These settings provide better risk management and more trading opportunities.\n\n"
                            "Use /autotrade to check status or adjust settings."
                        ),
                        parse_mode='HTML'
                    )
                except Exception as notify_err:
                    logger.warning(f"Failed to notify user {user_id}: {notify_err}")
            else:
                failed += 1
        
        logger.info("=" * 60)
        logger.info(f"[Engine Restore] Summary:")
        logger.info(f"  ✅ Restored: {restored}")
        logger.info(f"  ❌ Failed: {failed}")
        logger.info(f"  ⏭️  Skipped: {skipped}")
        logger.info(f"  📊 Total: {len(sessions)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"[Engine Restore] Critical error: {e}")
        import traceback
        traceback.print_exc()
