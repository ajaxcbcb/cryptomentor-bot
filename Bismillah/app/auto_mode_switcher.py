"""
Auto Mode Switcher
Automatically switches trading mode based on market sentiment
Runs as background task, checks every 15 minutes
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict

from app.market_sentiment_detector import detect_market_condition
from app.trading_mode_manager import TradingModeManager, TradingMode
from app.supabase_repo import _client

logger = logging.getLogger(__name__)


class AutoModeSwitcher:
    """
    Automatically switches trading mode based on market conditions
    
    Features:
    - Monitors BTC market sentiment every 15 minutes
    - Auto-switches between scalping (sideways) and swing (trending)
    - Notifies users when mode changes
    - Respects user preferences (can be disabled per user)
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.check_interval = max(
            60,
            int(os.getenv("AUTO_MODE_SWITCH_CHECK_INTERVAL_SECONDS", "900") or "900"),
        )
        # Low-trust detector defaults: stricter confidence + confirmation cycles.
        self.min_confidence = max(
            0,
            min(100, int(os.getenv("AUTO_MODE_SWITCH_MIN_CONFIDENCE", "65") or "65")),
        )
        self.required_confirmations = max(
            1,
            int(os.getenv("AUTO_MODE_SWITCH_CONFIRMATION_CYCLES", "2") or "2"),
        )
        self.switch_cooldown_seconds = max(
            0,
            int(os.getenv("AUTO_MODE_SWITCH_COOLDOWN_SECONDS", "1800") or "1800"),
        )
        # Repurposed tracker: user_id -> last successful auto-switch timestamp.
        self.switched_users: Dict[int, float] = {}
        # Per-user hysteresis state: user_id -> {"mode": str, "count": int}.
        self._recommendation_state: Dict[int, Dict[str, int | str]] = {}
        self.last_condition = None
        self.last_check = None
    
    async def start(self):
        """Start the auto mode switcher background task"""
        if self.running:
            logger.warning("[AutoModeSwitcher] Already running")
            return
        
        self.running = True
        logger.info(
            "[AutoModeSwitcher] Started "
            f"(interval={self.check_interval}s, min_conf={self.min_confidence}%, "
            f"confirm_cycles={self.required_confirmations}, cooldown={self.switch_cooldown_seconds}s)"
        )
        
        while self.running:
            try:
                await self._check_and_switch()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"[AutoModeSwitcher] Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the auto mode switcher"""
        self.running = False
        logger.info("[AutoModeSwitcher] Stopped")
    
    async def _check_and_switch(self):
        """Check market condition and switch modes if needed"""
        try:
            # Detect market condition
            result = detect_market_condition("BTC")
            
            condition = result['condition']
            confidence = result['confidence']
            recommended_mode = result['recommended_mode']
            
            self.last_condition = result
            self.last_check = datetime.now(timezone.utc)
            
            logger.info(
                f"[AutoModeSwitcher] Market: {condition} ({confidence}%) "
                f"→ Recommend: {recommended_mode.upper()}"
            )
            
            # Only switch if confidence is high enough
            if confidence < self.min_confidence:
                logger.info(
                    f"[AutoModeSwitcher] Confidence {confidence}% < {self.min_confidence}% "
                    f"- no switch"
                )
                return
            
            # Get all active autotrade users with auto-mode enabled
            users = self._get_auto_mode_users()
            
            if not users:
                logger.info("[AutoModeSwitcher] No users with auto-mode enabled")
                return
            
            # Switch mode for each user
            switched_count = 0
            for user_id in users:
                try:
                    switched = await self._switch_user_mode(
                        user_id, recommended_mode, result
                    )
                    if switched:
                        switched_count += 1
                except Exception as e:
                    logger.error(f"[AutoModeSwitcher] Error switching user {user_id}: {e}")
            
            logger.info(
                f"[AutoModeSwitcher] Switched {switched_count}/{len(users)} users "
                f"to {recommended_mode.upper()} mode"
            )
            
        except Exception as e:
            logger.error(f"[AutoModeSwitcher] Error in check_and_switch: {e}")
    
    def _get_auto_mode_users(self):
        """
        Get list of users with auto-mode enabled and engine running
        
        Returns list of user IDs
        """
        try:
            s = _client()
            
            # Get users with auto_mode_enabled = true and engine active
            result = s.table("autotrade_sessions").select(
                "telegram_id, auto_mode_enabled, engine_active"
            ).eq("auto_mode_enabled", True).eq("engine_active", True).execute()
            
            if not result.data:
                return []
            
            user_ids = [row['telegram_id'] for row in result.data]
            logger.info(f"[AutoModeSwitcher] Found {len(user_ids)} users with auto-mode enabled")
            
            return user_ids
            
        except Exception as e:
            logger.error(f"[AutoModeSwitcher] Error getting auto-mode users: {e}")
            return []

    def _record_recommendation(self, user_id: int, recommended_mode: str) -> int:
        """
        Track repeated recommendation streak per user for hysteresis.
        """
        uid = int(user_id)
        state = self._recommendation_state.get(uid) or {"mode": "", "count": 0}
        prev_mode = str(state.get("mode", ""))
        prev_count = int(state.get("count", 0) or 0)
        if prev_mode == recommended_mode:
            count = prev_count + 1
        else:
            count = 1
        self._recommendation_state[uid] = {"mode": recommended_mode, "count": count}
        return count

    def _in_switch_cooldown(self, user_id: int) -> bool:
        uid = int(user_id)
        last_switch_ts = float(self.switched_users.get(uid, 0.0) or 0.0)
        if last_switch_ts <= 0:
            return False
        return (time.time() - last_switch_ts) < float(self.switch_cooldown_seconds)
    
    async def _switch_user_mode(self, user_id: int, recommended_mode: str, 
                               market_result: Dict) -> bool:
        """
        Switch user's trading mode if different from current
        
        Returns True if switched, False if already in correct mode
        """
        try:
            recommended_mode = str(recommended_mode or "").strip().lower()
            if recommended_mode not in ("scalping", "swing"):
                logger.warning(f"[AutoModeSwitcher:{user_id}] Invalid recommended mode: {recommended_mode}")
                return False

            if TradingModeManager.is_manual_override_active(user_id):
                logger.info(
                    f"[AutoModeSwitcher:{user_id}] Manual override active - skipping auto switch"
                )
                return False

            if self._in_switch_cooldown(user_id):
                logger.info(
                    f"[AutoModeSwitcher:{user_id}] Auto-switch cooldown active "
                    f"({self.switch_cooldown_seconds}s)"
                )
                return False

            streak = self._record_recommendation(user_id, recommended_mode)
            if streak < self.required_confirmations:
                logger.info(
                    f"[AutoModeSwitcher:{user_id}] Hysteresis gate: {streak}/{self.required_confirmations} "
                    f"for {recommended_mode.upper()}"
                )
                return False

            # Get current mode
            current_mode = TradingModeManager.get_mode(user_id)
            if current_mode == TradingMode.MIXED:
                logger.info(
                    f"[AutoModeSwitcher:{user_id}] Mixed mode active - skipping legacy global auto-switch"
                )
                return False
            target_mode = TradingMode.SCALPING if recommended_mode == "scalping" else TradingMode.SWING
            
            # Check if already in correct mode
            if current_mode == target_mode:
                logger.debug(f"[AutoModeSwitcher:{user_id}] Already in {target_mode.value} mode")
                return False
            
            # Full switch path: stop current engine + persist mode + restart with new mode.
            # set_mode() alone only changes DB/cache and does NOT change the currently running engine.
            result = await TradingModeManager.switch_mode(
                user_id=user_id,
                new_mode=target_mode,
                bot=self.bot,
                context=None,
                switch_source="auto",
            )
            
            if not result.get("success"):
                logger.error(
                    f"[AutoModeSwitcher:{user_id}] Failed to switch mode: {result.get('message')}"
                )
                return False
            
            # Notify user
            await self._notify_user(user_id, current_mode, target_mode, market_result)
            self.switched_users[int(user_id)] = time.time()
            
            logger.info(
                f"[AutoModeSwitcher:{user_id}] Switched: {current_mode.value} → {target_mode.value}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[AutoModeSwitcher:{user_id}] Error switching mode: {e}")
            return False
    
    async def _notify_user(self, user_id: int, old_mode: TradingMode, 
                          new_mode: TradingMode, market_result: Dict):
        """Send notification to user about mode switch"""
        try:
            condition = market_result['condition']
            confidence = market_result['confidence']
            reason = market_result['reason']
            
            # Emoji based on condition
            emoji = "📊" if condition == "SIDEWAYS" else "📈" if condition == "TRENDING" else "⚡"
            
            message = (
                f"{emoji} <b>Auto Mode Switch</b>\n\n"
                f"Market Condition: <b>{condition}</b> ({confidence}%)\n"
                f"Mode: {old_mode.value.upper()} → <b>{new_mode.value.upper()}</b>\n\n"
                f"📋 Analysis:\n{reason}\n\n"
                f"💡 Your engine will automatically use the optimal strategy "
                f"for current market conditions.\n\n"
                f"⚙️ Disable auto-mode in /settings if you prefer manual control."
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.warning(f"[AutoModeSwitcher:{user_id}] Failed to send notification: {e}")
    
    def get_status(self) -> Dict:
        """Get current status of auto mode switcher"""
        return {
            'running': self.running,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_condition': self.last_condition,
            'check_interval_minutes': self.check_interval / 60,
            'min_confidence': self.min_confidence,
            'required_confirmations': self.required_confirmations,
            'switch_cooldown_seconds': self.switch_cooldown_seconds,
        }


# Global instance
_switcher = None


def start_auto_mode_switcher(bot):
    """Start the auto mode switcher background task"""
    global _switcher
    
    if _switcher and _switcher.running:
        logger.warning("[AutoModeSwitcher] Already running")
        return _switcher
    
    _switcher = AutoModeSwitcher(bot)
    asyncio.create_task(_switcher.start())
    
    return _switcher


def stop_auto_mode_switcher():
    """Stop the auto mode switcher"""
    global _switcher
    
    if _switcher:
        _switcher.stop()
        _switcher = None


def get_auto_mode_switcher():
    """Get the current auto mode switcher instance"""
    return _switcher
