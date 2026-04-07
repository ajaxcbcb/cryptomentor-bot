"""
Trading Mode Manager
Manages trading mode selection, persistence, and switching between scalping and swing modes
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from app.trading_mode import TradingMode
from app.supabase_repo import _client

logger = logging.getLogger(__name__)


class TradingModeManager:
    """
    Centralized manager for trading mode selection and persistence
    """
    
    # In-memory cache: {user_id: TradingMode}
    _mode_cache: Dict[int, TradingMode] = {}
    
    @staticmethod
    def get_mode(user_id: int) -> TradingMode:
        """
        Load trading mode — uses in-memory cache to avoid DB spam.
        Cache is invalidated when set_mode() is called.
        """
        # Return cached value if available
        if user_id in TradingModeManager._mode_cache:
            return TradingModeManager._mode_cache[user_id]
        
        try:
            s = _client()
            res = s.table("autotrade_sessions").select("trading_mode").eq(
                "telegram_id", int(user_id)
            ).limit(1).execute()
            
            if not res.data:
                mode = TradingMode.SWING
            else:
                mode_str = res.data[0].get("trading_mode", "swing")
                mode = TradingMode.from_string(mode_str)
            
            # Cache the result
            TradingModeManager._mode_cache[user_id] = mode
            logger.info(f"[TradingMode:{user_id}] Loaded mode: {mode.value}")
            return mode
            
        except Exception as e:
            logger.error(f"[TradingMode:{user_id}] Error loading mode: {e}")
            return TradingMode.SWING
    
    @staticmethod
    def set_mode(user_id: int, mode: TradingMode) -> bool:
        """Update trading mode in database and invalidate cache."""
        try:
            s = _client()
            s.table("autotrade_sessions").upsert({
                "telegram_id": int(user_id),
                "trading_mode": mode.value,
                "updated_at": datetime.utcnow().isoformat(),
            }, on_conflict="telegram_id").execute()
            
            # Invalidate cache
            TradingModeManager._mode_cache[user_id] = mode
            logger.info(f"[TradingMode:{user_id}] Mode updated to: {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"[TradingMode:{user_id}] Error updating mode: {e}")
            return False
    
    @staticmethod
    async def switch_mode(user_id: int, new_mode: TradingMode, bot, context) -> Dict:
        """
        Switch trading mode with engine restart
        
        Algorithm:
        1. Get current mode
        2. Stop current engine
        3. Update database with new mode
        4. Start new engine with new mode config
        5. Send confirmation to user
        
        Args:
            user_id: Telegram user ID
            new_mode: TradingMode enum value to switch to
            bot: Telegram bot instance
            context: Telegram context
            
        Returns:
            Dict with success status and message
        """
        current_mode = None
        engine_stopped = False
        db_updated = False
        
        try:
            # Step 1: Get current mode
            current_mode = TradingModeManager.get_mode(user_id)
            
            if current_mode == new_mode:
                return {
                    "success": False,
                    "message": f"Already in {new_mode.value} mode"
                }
            
            # Step 2: Stop engine (close sideways positions first if switching from scalping)
            try:
                from app.autotrade_engine import stop_engine, get_engine
                # Close open sideways positions before stopping if switching away from scalping
                if current_mode == TradingMode.SCALPING and new_mode != TradingMode.SCALPING:
                    try:
                        engine = get_engine(user_id)
                        if engine and hasattr(engine, 'positions'):
                            sideways_symbols = [
                                sym for sym, pos in engine.positions.items()
                                if getattr(pos, 'is_sideways', False)
                            ]
                            for sym in sideways_symbols:
                                pos = engine.positions[sym]
                                await engine._close_sideways_max_hold(pos)
                                logger.info(f"[ModeSwitch:{user_id}] Closed sideways position {sym} before mode switch")
                    except Exception as sw_err:
                        logger.warning(f"[ModeSwitch:{user_id}] Could not close sideways positions: {sw_err}")
                stop_engine(user_id)
                engine_stopped = True
                logger.info(f"[ModeSwitch:{user_id}] Stopped {current_mode.value} engine")
            except Exception as e:
                logger.warning(f"[ModeSwitch:{user_id}] Engine stop warning: {e}")
                # Continue - engine may not be running
            
            # Step 3: Update database
            try:
                success = TradingModeManager.set_mode(user_id, new_mode)
                if not success:
                    raise Exception("Database update returned False")
                db_updated = True
            except Exception as e:
                logger.error(f"[ModeSwitch:{user_id}] Database update failed: {e}")
                
                # Rollback: restart old engine if it was stopped
                if engine_stopped and current_mode:
                    try:
                        await TradingModeManager._restart_engine_with_mode(
                            user_id, current_mode, bot, context
                        )
                    except Exception as restart_err:
                        logger.error(f"[ModeSwitch:{user_id}] Rollback failed: {restart_err}")
                
                return {
                    "success": False,
                    "message": f"Database update failed: {str(e)[:100]}"
                }
            
            # Step 4: Start new engine
            try:
                await TradingModeManager._restart_engine_with_mode(
                    user_id, new_mode, bot, context
                )
            except Exception as e:
                logger.error(f"[ModeSwitch:{user_id}] Engine start failed: {e}")
                
                # Rollback: restore old mode in database
                if db_updated and current_mode:
                    try:
                        TradingModeManager.set_mode(user_id, current_mode)
                        await TradingModeManager._restart_engine_with_mode(
                            user_id, current_mode, bot, context
                        )
                    except Exception as rollback_err:
                        logger.critical(
                            f"[ModeSwitch:{user_id}] CRITICAL: Rollback failed: {rollback_err}"
                        )
                
                return {
                    "success": False,
                    "message": f"Engine start failed: {str(e)[:100]}"
                }
            
            # Success
            logger.info(
                f"[ModeSwitch:{user_id}] Successfully switched from {current_mode.value} to {new_mode.value}"
            )
            return {
                "success": True,
                "message": f"Switched to {new_mode.value} mode",
                "mode": new_mode,
                "previous_mode": current_mode
            }
        
        except Exception as e:
            logger.error(f"[ModeSwitch:{user_id}] Unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)[:100]}"
            }
    
    @staticmethod
    async def _restart_engine_with_mode(user_id: int, mode: TradingMode, bot, context):
        """
        Helper method to restart engine with specific mode
        
        Args:
            user_id: Telegram user ID
            mode: TradingMode to start
            bot: Telegram bot instance
            context: Telegram context
        """
        from app.autotrade_engine import start_engine
        from app.handlers_autotrade import get_user_api_keys, get_autotrade_session
        from app.supabase_repo import get_user_by_tid
        
        # Get user's API keys and settings
        keys = get_user_api_keys(user_id)
        session = get_autotrade_session(user_id)
        
        if not keys or not session:
            raise Exception("User configuration not found")
        
        # Check if user is premium
        user_data = get_user_by_tid(user_id)
        is_premium = user_data.get("premium_active", False) if user_data else False
        
        # Start engine with mode-specific config (silent=False to send notification)
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=session.get('initial_deposit', 100),
            leverage=session.get('leverage', 10),
            notify_chat_id=user_id,
            is_premium=is_premium,
            silent=False,  # Send startup notification
            exchange_id=keys.get('exchange', 'bitunix')
        )
        
        logger.info(f"[ModeSwitch:{user_id}] Started {mode.value} engine with notification")
