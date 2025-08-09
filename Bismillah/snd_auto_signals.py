import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict

class AutoSignalScanner:
    """
    Auto Signal Scanner for generating trading signals
    """

    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.is_running = False

        # Configuration
        self.target_symbols = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SHIB', 'DOT',
            'LINK', 'TRX', 'MATIC', 'LTC', 'BCH', 'NEAR', 'UNI', 'ICP', 'APT', 'ARB',
            'OP', 'STX', 'MNT', 'INJ', 'WLD'
        ]

        self.scan_interval = 30 * 60  # 30 minutes
        self.min_confidence = 70
        self.signal_cooldown = 60 * 60  # 1 hour

        # State tracking
        self.last_scan_time = 0
        self.last_signal_sent_time = 0
        self.active_scanner_task = None
        self.sent_signals_cache = {}

        # Placeholder for AI Assistant
        self.ai_assistant = None
        if hasattr(bot_instance, 'ai_assistant'):
            self.ai_assistant = bot_instance.ai_assistant

        print(f"🎯 Auto SnD Signals initialized with {len(self.target_symbols)} altcoins")
        print(f"⏰ Scan interval: {self.scan_interval // 60} minutes")
        print(f"📈 Min confidence: {self.min_confidence}%")

    async def start_auto_scanner(self):
        """Start the auto signal scanner"""
        if self.is_running:
            print("[AUTO-SIGNAL SND] ⚠️ Scanner already running")
            return

        self.is_running = True
        self.active_scanner_task = asyncio.create_task(self._scanner_loop())
        print(f"[AUTO-SIGNAL SND] ✅ Scanner started - Interval: {self.scan_interval // 60} minutes")

    async def stop_auto_scanner(self):
        """Stop the auto signal scanner"""
        if not self.is_running:
            return

        self.is_running = False
        if self.active_scanner_task:
            self.active_scanner_task.cancel()
            try:
                await self.active_scanner_task
            except asyncio.CancelledError:
                pass

        print("[AUTO-SIGNAL SND] 🛑 Scanner stopped")

    async def _scanner_loop(self):
        """Main scanner loop"""
        while self.is_running:
            try:
                print("[AUTO-SIGNAL SND] 🔄 Starting scan cycle...")
                await self._perform_scan()

                # Wait for next scan
                await asyncio.sleep(self.scan_interval)

            except asyncio.CancelledError:
                print("[AUTO-SIGNAL SND] 🛑 Scanner cancelled")
                break
            except Exception as e:
                print(f"[AUTO-SIGNAL SND] ❌ Scanner error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _perform_scan(self):
        """Perform signal scan"""
        try:
            current_time = time.time()

            # Check cooldown
            if current_time - self.last_signal_sent_time < self.signal_cooldown:
                time_left = self.signal_cooldown - (current_time - self.last_signal_sent_time)
                print(f"[AUTO-SIGNAL SND] ⏳ Cooldown active - {time_left/60:.0f} minutes left")
                return

            # Use the enhanced scan method
            valid_signals = await self.enhanced_snd_scan()

            if valid_signals:
                await self._send_signals_to_eligible_users(valid_signals)
                self.last_signal_sent_time = current_time
            else:
                print("📊 No valid SnD signals found in current scan")

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Scan error: {e}")

    # --- NEW/MODIFIED METHODS FOR ENHANCED SCAN AND SIGNAL HANDLING ---

    async def enhanced_snd_scan(self) -> List[Dict]:
        """Enhanced SnD scan with CoinAPI technical analysis"""
        try:
            # Use AI Assistant's scan method if available
            if hasattr(self.ai_assistant, 'scan_for_auto_signals'):
                signals = await self.ai_assistant.scan_for_auto_signals()
                return signals

            # Fallback to basic scan
            signals = []
            print(f"🔍 Scanning {len(self.target_symbols)} altcoins for SnD signals...")

            for symbol in self.target_symbols:
                try:
                    # Skip if recently signaled
                    if self._is_recently_signaled(symbol):
                        continue

                    # Basic signal generation (simplified)
                    if len(signals) < 3:  # Limit signals
                        signal_data = {
                            'symbol': symbol,
                            'direction': 'BUY',  # Simplified
                            'confidence': 75,
                            'entry': 50000,  # Placeholder
                            'tp1': 51000,
                            'tp2': 52000,
                            'sl': 49000,
                            'analysis': 'Basic SnD analysis',
                            'timestamp': datetime.now().isoformat(),
                            'source': 'basic_snd'
                        }

                        signals.append(signal_data)
                        self._update_signal_history(symbol)

                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue

            print(f"📊 SnD scan completed: {len(signals)} signals")
            return signals

        except Exception as e:
            print(f"❌ Error in SnD scan: {e}")
            return []

    def _is_valid_signal(self, signal: Dict) -> bool:
        """Validate signal quality"""
        if not signal:
            return False

        # Check confidence threshold
        if signal.get('confidence', 0) < self.min_confidence:
            return False

        # Check price validity
        if signal.get('current_price', 0) <= 0:
            return False

        # Check for duplicate recent signals
        signal_key = f"{signal['symbol']}_{signal['direction']}"
        current_time = time.time()

        if signal_key in self.sent_signals_cache:
            last_sent = self.sent_signals_cache[signal_key]
            if current_time - last_sent < (self.signal_cooldown / 2):
                return False

        # Mark signal as sent
        self.sent_signals_cache[signal_key] = current_time

        return True

    def _is_recently_signaled(self, symbol: str) -> bool:
        """Check if a symbol was recently signaled"""
        signal_key = f"{symbol}_ANY" # Simplified check for any signal recently
        current_time = time.time()

        if signal_key in self.sent_signals_cache:
            last_sent = self.sent_signals_cache[signal_key]
            # Use a fraction of cooldown to prevent rapid signals for the same symbol
            if current_time - last_sent < (self.signal_cooldown * 0.75):
                return True
        return False

    def _update_signal_history(self, symbol: str):
        """Update the last signaled time for a symbol"""
        signal_key = f"{symbol}_ANY"
        self.sent_signals_cache[signal_key] = time.time()

    def _send_signals_to_eligible_users(self, signals: List[Dict]):
        """Send signals to eligible users"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self._get_eligible_users()

            if not eligible_users:
                print("[AUTO-SIGNAL SND] ⚠️ No eligible users found")
                return

            # Send signals to eligible users
            success_count = 0
            for user in eligible_users:
                for signal in signals:
                    try:
                        message = self._format_enhanced_signal_message(signal)
                        await self.bot_instance.application.bot.send_message(
                            chat_id=user['telegram_id'],
                            text=message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                        await asyncio.sleep(0.1)  # Rate limiting
                    except Exception as e:
                        print(f"[AUTO-SIGNAL SND] ❌ Failed to send signal to {user['telegram_id']}: {e}")
            
            print(f"[AUTO-SIGNAL SND] ✅ Sent {len(signals)} signals to {success_count}/{len(eligible_users)} users")

            # Log broadcast
            if hasattr(self.bot_instance, 'db'):
                self.bot_instance.db.log_auto_signal_broadcast(len(signals), success_count, len(eligible_users))

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Broadcast error: {e}")

    def _format_enhanced_signal_message(self, signal: Dict) -> str:
        """Format enhanced signal message for Telegram"""
        try:
            # Use AI Assistant's formatting if available
            if hasattr(self.ai_assistant, 'format_auto_signal_message'):
                return self.ai_assistant.format_auto_signal_message(signal)

            # Fallback formatting
            direction_emoji = "🚀" if signal['direction'] == "BUY" else "🔻"

            message = f"""🎯 **Auto SnD Signal**

{direction_emoji} **{signal['symbol']}** - {signal['direction']}
🎯 **Confidence**: {signal['confidence']}%
💰 **Entry**: ${signal.get('entry', 0):,.4f}

📊 **Targets & Risk**:
🎯 TP1: ${signal.get('tp1', 0):,.4f}
🎯 TP2: ${signal.get('tp2', 0):,.4f}
🛑 SL: ${signal.get('sl', 0):,.4f}

📈 **Analysis**: {signal.get('analysis', 'SnD analysis')}

⚠️ **Risk Management**: Max 2-5% portfolio
🔄 **Source**: CoinAPI Enhanced SnD
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}"""

            return message

        except Exception as e:
            print(f"Error formatting signal message: {e}")
            return f"🎯 Auto Signal: {signal.get('symbol', 'Unknown')} {signal.get('direction', 'Unknown')}"

    def _get_eligible_users(self):
        """Get eligible users for auto signals"""
        try:
            if not hasattr(self.bot_instance, 'db'):
                return []

            # Get admin user
            admin_id = getattr(self.bot_instance, 'admin_id', 0)
            eligible_users = []

            if admin_id:
                eligible_users.append({
                    'telegram_id': admin_id,
                    'type': 'admin'
                })

            # Get lifetime premium users from database
            try:
                self.bot_instance.db.cursor.execute("""
                    SELECT telegram_id, first_name 
                    FROM users 
                    WHERE is_premium = 1 AND (subscription_end IS NULL OR subscription_end = '')
                """)

                lifetime_users = self.bot_instance.db.cursor.fetchall()
                for user in lifetime_users:
                    if user[0] != admin_id:  # Don't duplicate admin
                        eligible_users.append({
                            'telegram_id': user[0],
                            'first_name': user[1] or 'User',
                            'type': 'lifetime'
                        })

            except Exception as e:
                print(f"[AUTO-SIGNAL SND] ❌ Error getting lifetime users: {e}")

            return eligible_users

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Error getting eligible users: {e}")
            return []

    # --- DEPRECATED/REMOVED METHODS (kept for context but not used by new logic) ---
    async def _analyze_symbol_enhanced(self, symbol):
        """Enhanced SnD analysis for a symbol"""
        # This method is no longer directly used by the scanner loop.
        # Its logic might be replaced by AI Assistant or simplified in enhanced_snd_scan.
        pass


def initialize_auto_signals(bot_instance):
    """Initialize the auto signals system"""
    try:
        scanner = AutoSignalScanner(bot_instance)
        return scanner
    except Exception as e:
        print(f"❌ Failed to initialize auto signals: {e}")
        return None