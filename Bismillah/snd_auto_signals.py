#!/usr/bin/env python3
"""
Auto SnD Signals untuk CryptoMentor AI
Updated to use unified futures engine for consistency
"""

import os
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

class AutoSignalScanner:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.is_running = False

        # Configuration
        self.target_symbols = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 
            'MATIC', 'DOT', 'LINK', 'TRX', 'LTC', 'BCH', 'NEAR', 'UNI',
            'APT', 'ATOM', 'FIL', 'ETC', 'ALGO', 'VET', 'MANA', 'SAND', 'SHIB'
        ]
        self.scan_interval = int(os.getenv("AUTOSIGNAL_INTERVAL", "1800"))  # 30 minutes
        self.min_confidence = int(os.getenv("AUTOSIGNAL_MIN_CONF", "75"))
        self.cooldown_minutes = int(os.getenv("AUTOSIGNAL_COOLDOWN", "60"))  # 1 hour cooldown

        # State tracking
        self.last_scan_time = 0
        self.last_signals_sent = {}  # {(symbol, side): timestamp}
        self.active_scanner_task = None

        print(f"[AUTO-SIGNAL] Initialized with:")
        print(f"  📊 Target symbols: {len(self.target_symbols)}")
        print(f"  ⏰ Scan interval: {self.scan_interval // 60} minutes")
        print(f"  🎯 Min confidence: {self.min_confidence}%")
        print(f"  🛡️ Cooldown: {self.cooldown_minutes} minutes")

    async def start_auto_scanner(self):
        """Start the auto signal scanner"""
        if self.is_running:
            print("[AUTO-SIGNAL] Already running!")
            return

        self.is_running = True
        self.active_scanner_task = asyncio.create_task(self._scan_loop())
        print("[AUTO-SIGNAL] ✅ Scanner started!")

    async def stop_auto_scanner(self):
        """Stop the auto signal scanner"""
        self.is_running = False
        if self.active_scanner_task:
            self.active_scanner_task.cancel()
            try:
                await self.active_scanner_task
            except asyncio.CancelledError:
                pass
        print("[AUTO-SIGNAL] 🛑 Scanner stopped!")

    async def _scan_loop(self):
        """Main scanning loop"""
        while self.is_running:
            try:
                await self._perform_scan()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AUTO-SIGNAL] ❌ Error in scan loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _perform_scan(self):
        """Perform one complete scan of all symbols"""
        try:
            print(f"[AUTO-SIGNAL] 🔍 Starting scan at {datetime.now().strftime('%H:%M:%S')}")

            # Get eligible users
            eligible_users = self._get_eligible_users()
            if not eligible_users:
                print("[AUTO-SIGNAL] ⚠️ No eligible users found")
                return

            print(f"[AUTO-SIGNAL] 📊 Eligible users: Admin + Supabase Lifetime only")
            print(f"[AUTO-SIGNAL] 👥 Auto signals eligible: {len(eligible_users)} total (Admin + Lifetime from Supabase)")

            # Scan symbols for signals
            signals_found = []

            for symbol in self.target_symbols[:10]:  # Limit to top 10 to avoid API overload
                try:
                    signal = await self._analyze_symbol_for_signal(symbol)
                    if signal and self._should_send_signal(signal):
                        signals_found.append(signal)
                        print(f"[AUTO-SIGNAL] ✅ Found signal: {symbol} {signal['side']} ({signal['confidence']}%)")

                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"[AUTO-SIGNAL] ⚠️ Error analyzing {symbol}: {e}")
                    continue

            # Send signals to eligible users
            if signals_found:
                await self._send_signals_to_users(signals_found, eligible_users)
            else:
                print("[AUTO-SIGNAL] 📭 No signals meet criteria")

            self.last_scan_time = time.time()

        except Exception as e:
            print(f"[AUTO-SIGNAL] ❌ Error in perform_scan: {e}")

    async def _analyze_symbol_for_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze symbol using unified engine"""
        try:
            # Use the same engine as manual commands
            from app.futures.engine import analyze_symbol

            result = analyze_symbol(
                symbol=symbol,
                timeframe=os.getenv("AUTOSIGNAL_TF", "15m"),
                crypto_api=self.bot_instance.crypto_api
            )

            signals = result.get('signals', [])
            if not signals:
                return None

            # Get best signal (highest confidence)
            best_signal = max(signals, key=lambda s: s.get('confidence', 0))
            confidence = best_signal.get('confidence', 0)

            if confidence < self.min_confidence:
                return None

            # Format for AutoSignal
            signal = {
                'symbol': result.get('symbol', f"{symbol}USDT"),
                'side': best_signal.get('side'),
                'confidence': confidence,
                'price': result.get('price'),
                'entry': best_signal.get('entry'),
                'sl': best_signal.get('sl'),
                'tp': best_signal.get('tp', []),
                'reasons': best_signal.get('reasons', []),
                'timestamp': time.time()
            }

            return signal

        except Exception as e:
            print(f"[AUTO-SIGNAL] Error analyzing {symbol}: {e}")
            return None

    def _should_send_signal(self, signal: Dict[str, Any]) -> bool:
        """Check if signal should be sent based on cooldown"""
        try:
            symbol = signal['symbol']
            side = signal['side']
            key = (symbol, side)

            # Check cooldown
            if key in self.last_signals_sent:
                last_sent = self.last_signals_sent[key]
                time_diff = (time.time() - last_sent) / 60  # minutes
                if time_diff < self.cooldown_minutes:
                    return False

            return True

        except Exception as e:
            print(f"[AUTO-SIGNAL] Error checking cooldown: {e}")
            return False

    async def _send_signals_to_users(self, signals: List[Dict[str, Any]], users: List[int]):
        """Send signals to eligible users"""
        try:
            from app.futures.formatters import format_autosignal_message
            from app.safe_send import safe_dm

            sent_count = 0

            for signal in signals:
                # Format message
                message = format_autosignal_message(signal)

                # Send to users
                for user_id in users:
                    try:
                        await safe_dm(self.bot_instance.application.bot, user_id, message)
                        sent_count += 1
                        await asyncio.sleep(0.1)  # Rate limiting
                    except Exception as e:
                        print(f"[AUTO-SIGNAL] Failed to send to {user_id}: {e}")

                # Update cooldown tracking
                symbol = signal['symbol']
                side = signal['side']
                self.last_signals_sent[(symbol, side)] = time.time()

            print(f"[AUTO-SIGNAL] 📤 Sent {len(signals)} signals to {len(users)} users ({sent_count} total messages)")

        except Exception as e:
            print(f"[AUTO-SIGNAL] ❌ Error sending signals: {e}")

    def get_eligible_users(self) -> List[int]:
        """Get eligible users for AutoSignal - Only admin + Supabase lifetime users"""
        try:
            from app.supabase_conn import sb_list_users
            from app.chat_store import get_private_chat_id
            import os

            # Get admin IDs from environment
            admin_ids = set()
            for key in ("ADMIN_USER_ID", "ADMIN2_USER_ID", "ADMIN1", "ADMIN2"):
                val = os.getenv(key)
                if val and val.isdigit():
                    admin_ids.add(int(val))

            eligible_users = list(admin_ids)

            # Get lifetime premium from Supabase only
            try:
                rows = sb_list_users({
                    "is_premium": "eq.true",
                    "banned": "eq.false",
                    "premium_until": "is.null"  # lifetime only
                }, columns="telegram_id")

                # Add users who have private chat consent
                for row in rows:
                    tid = row.get("telegram_id")
                    if tid and get_private_chat_id(int(tid)) is not None:
                        eligible_users.append(int(tid))

            except Exception as e:
                print(f"[AUTO-SIGNAL] Error getting Supabase lifetime users: {e}")

            return list(set(eligible_users))  # Remove duplicates

        except Exception as e:
            print(f"[AUTO-SIGNAL] Error getting eligible users: {e}")
            return []

def initialize_auto_signals(bot_instance):
    """Initialize and return AutoSignal scanner"""
    try:
        return AutoSignalScanner(bot_instance)
    except Exception as e:
        print(f"[AUTO-SIGNAL] ❌ Failed to initialize: {e}")
        return None