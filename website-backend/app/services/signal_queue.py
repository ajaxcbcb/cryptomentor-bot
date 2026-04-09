"""
Shared Signal Queue Manager

Coordinates signal generation and execution between:
- Web Dashboard (frontend requests signals)
- Telegram Bot (autotrade engine)

Prevents concurrent execution on same symbol and ensures consistent queue ordering.
Uses Supabase to persist queue state across systems.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueuedSignal:
    """Represents a signal in the queue."""
    symbol: str
    direction: str  # LONG or SHORT
    confidence: float
    entry_price: float
    tp1: float
    tp2: float
    tp3: float
    sl: float
    generated_at: str
    reason: str
    source: str = "autotrade"  # "autotrade" or "web"
    status: str = "pending"  # pending, executing, executed, failed

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tp3": self.tp3,
            "sl": self.sl,
            "generated_at": self.generated_at,
            "reason": self.reason,
            "source": self.source,
            "status": self.status,
        }


class SignalQueueManager:
    """
    Manages signal queue with persistence to Supabase.

    Ensures:
    ✅ Higher confidence signals execute first
    ✅ No concurrent execution on same symbol (both web & telegram aware)
    ✅ Consistent queue ordering across all systems
    ✅ Queue state persisted to database
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.queue: List[QueuedSignal] = []
        self.executing_symbols: set = set()
        self._load_from_db()

    def _load_from_db(self):
        """Load queue state from Supabase."""
        try:
            from app.db.supabase import _client
            s = _client()
            res = s.table("signal_queue").select(
                "*"
            ).eq("user_id", self.user_id).eq(
                "status", "pending"
            ).order("confidence", desc=True).execute()

            self.queue = []
            for row in res.data or []:
                sig = QueuedSignal(
                    symbol=row["symbol"],
                    direction=row["direction"],
                    confidence=float(row["confidence"]),
                    entry_price=float(row["entry_price"]),
                    tp1=float(row["tp1"]),
                    tp2=float(row["tp2"]),
                    tp3=float(row["tp3"]),
                    sl=float(row["sl"]),
                    generated_at=row["generated_at"],
                    reason=row["reason"],
                    source=row.get("source", "autotrade"),
                    status=row.get("status", "pending"),
                )
                self.queue.append(sig)

            # Load executing symbols
            exec_res = s.table("signal_queue").select(
                "symbol"
            ).eq("user_id", self.user_id).eq(
                "status", "executing"
            ).execute()

            self.executing_symbols = {row["symbol"] for row in exec_res.data or []}

        except Exception as e:
            logger.warning(f"[SignalQueue:{self.user_id}] Failed to load from DB: {e}")

    def add_signal(self, signal: QueuedSignal) -> bool:
        """
        Add a signal to the queue.

        Returns: True if added, False if symbol already in queue/executing
        """
        # Check if symbol already exists in queue or is executing
        if signal.symbol in self.executing_symbols:
            logger.info(f"[SignalQueue:{self.user_id}] {signal.symbol} already executing, skipping")
            return False

        if any(s.symbol == signal.symbol for s in self.queue):
            logger.info(f"[SignalQueue:{self.user_id}] {signal.symbol} already in queue, updating confidence")
            # Update existing signal if new confidence is higher
            for existing in self.queue:
                if existing.symbol == signal.symbol and signal.confidence > existing.confidence:
                    existing.confidence = signal.confidence
                    existing.reason = signal.reason
                    self._save_signal_to_db(existing)
            return False

        # Add to local queue
        self.queue.append(signal)

        # Sort by confidence (highest first)
        self.queue.sort(key=lambda s: s.confidence, reverse=True)

        # Persist to database
        self._save_signal_to_db(signal)

        logger.info(f"[SignalQueue:{self.user_id}] Added {signal.symbol} (conf={signal.confidence}%) to queue")
        return True

    def get_next_signal(self) -> Optional[QueuedSignal]:
        """
        Get next signal to execute (highest confidence, not executing).

        Returns: QueuedSignal if available, None if all executing or queue empty
        """
        for signal in self.queue:
            if signal.symbol not in self.executing_symbols:
                return signal
        return None

    def mark_executing(self, symbol: str) -> bool:
        """
        Mark a signal as currently executing.

        Returns: True if marked, False if already executing
        """
        if symbol in self.executing_symbols:
            return False

        self.executing_symbols.add(symbol)

        # Update in DB
        try:
            from app.db.supabase import _client
            s = _client()
            s.table("signal_queue").update({
                "status": "executing",
                "started_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", self.user_id).eq(
                "symbol", symbol
            ).eq("status", "pending").execute()
        except Exception as e:
            logger.warning(f"[SignalQueue:{self.user_id}] Failed to mark executing: {e}")

        logger.info(f"[SignalQueue:{self.user_id}] Marked {symbol} as executing")
        return True

    def mark_completed(self, symbol: str, success: bool = True):
        """
        Mark signal as executed (success or failed).
        Removes from queue and executing set.
        """
        self.executing_symbols.discard(symbol)
        self.queue = [s for s in self.queue if s.symbol != symbol]

        # Update in DB
        try:
            from app.db.supabase import _client
            s = _client()
            status = "executed" if success else "failed"
            s.table("signal_queue").update({
                "status": status,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", self.user_id).eq(
                "symbol", symbol
            ).execute()
        except Exception as e:
            logger.warning(f"[SignalQueue:{self.user_id}] Failed to mark completed: {e}")

        logger.info(f"[SignalQueue:{self.user_id}] Marked {symbol} as {status}")

    def get_queue_status(self) -> Dict:
        """Get current queue status for user."""
        return {
            "queue": [s.to_dict() for s in self.queue],
            "executing": list(self.executing_symbols),
            "total_pending": len(self.queue),
            "total_executing": len(self.executing_symbols),
        }

    def _save_signal_to_db(self, signal: QueuedSignal):
        """Save signal to Supabase."""
        try:
            from app.db.supabase import _client
            s = _client()

            # Check if signal already exists
            res = s.table("signal_queue").select("id").eq(
                "user_id", self.user_id
            ).eq("symbol", signal.symbol).eq(
                "status", "pending"
            ).limit(1).execute()

            if res.data:
                # Update existing
                s.table("signal_queue").update({
                    "direction": signal.direction,
                    "confidence": signal.confidence,
                    "entry_price": signal.entry_price,
                    "tp1": signal.tp1,
                    "tp2": signal.tp2,
                    "tp3": signal.tp3,
                    "sl": signal.sl,
                    "generated_at": signal.generated_at,
                    "reason": signal.reason,
                    "source": signal.source,
                }).eq("id", res.data[0]["id"]).execute()
            else:
                # Insert new
                s.table("signal_queue").insert({
                    "user_id": self.user_id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "confidence": signal.confidence,
                    "entry_price": signal.entry_price,
                    "tp1": signal.tp1,
                    "tp2": signal.tp2,
                    "tp3": signal.tp3,
                    "sl": signal.sl,
                    "generated_at": signal.generated_at,
                    "reason": signal.reason,
                    "source": signal.source,
                    "status": "pending",
                }).execute()
        except Exception as e:
            logger.warning(f"[SignalQueue:{self.user_id}] Failed to save signal to DB: {e}")


# Global queue instances per user (for fast in-memory access)
_queue_instances: Dict[int, SignalQueueManager] = {}


def get_signal_queue(user_id: int) -> SignalQueueManager:
    """Get or create queue manager for user."""
    if user_id not in _queue_instances:
        _queue_instances[user_id] = SignalQueueManager(user_id)
    return _queue_instances[user_id]
