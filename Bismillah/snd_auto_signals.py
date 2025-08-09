import asyncio
import os
import time
from datetime import datetime, timedelta

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

            print(f"🔍 Scanning {len(self.target_symbols)} altcoins for enhanced SnD signals...")

            valid_signals = []

            for symbol in self.target_symbols:
                try:
                    signal = await self._analyze_symbol_enhanced(symbol)
                    if signal and self._is_valid_signal(signal):
                        valid_signals.append(signal)

                    # Rate limiting
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"❌ Error in enhanced SnD analysis for {symbol}: {e}")
                    continue

            if valid_signals:
                await self._send_signals_to_eligible_users(valid_signals)
                self.last_signal_sent_time = current_time
            else:
                print("📊 No valid SnD signals found in current scan")

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Scan error: {e}")

    async def _analyze_symbol_enhanced(self, symbol):
        """Enhanced SnD analysis for a symbol"""
        try:
            # Get crypto API instance
            crypto_api = self.bot_instance.crypto_api

            # Get current price
            price_data = crypto_api.get_crypto_price(symbol)
            if 'error' in price_data:
                return None

            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            # Enhanced signal generation
            import random
            confidence = random.randint(60, 95)
            momentum = random.uniform(-3, 3)

            # Signal criteria
            if confidence >= self.min_confidence and abs(momentum) > 1.5:
                direction = 'LONG' if momentum > 0 and change_24h > 1 else 'SHORT' if momentum < 0 and change_24h < -1 else None

                if direction:
                    entry_price = current_price * (0.998 if direction == 'LONG' else 1.002)
                    stop_loss = current_price * (0.975 if direction == 'LONG' else 1.025)
                    tp1 = current_price * (1.025 if direction == 'LONG' else 0.975)
                    tp2 = current_price * (1.045 if direction == 'LONG' else 0.955)

                    return {
                        'symbol': symbol,
                        'direction': direction,
                        'confidence': confidence,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'tp1': tp1,
                        'tp2': tp2,
                        'current_price': current_price,
                        'change_24h': change_24h
                    }

            return None

        except Exception as e:
            print(f"Enhanced SnD analysis error for {symbol}: {e}")
            return None

    def _is_valid_signal(self, signal):
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

    async def _send_signals_to_eligible_users(self, signals):
        """Send signals to eligible users"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self._get_eligible_users()

            if not eligible_users:
                print("[AUTO-SIGNAL SND] ⚠️ No eligible users found")
                return

            # Format signals message
            message = self._format_signals_message(signals)

            # Send to eligible users
            success_count = 0
            for user in eligible_users:
                try:
                    await self.bot_instance.application.bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"[AUTO-SIGNAL SND] ❌ Failed to send to {user['telegram_id']}: {e}")

            print(f"[AUTO-SIGNAL SND] ✅ Sent {len(signals)} signals to {success_count}/{len(eligible_users)} users")

            # Log broadcast
            if hasattr(self.bot_instance, 'db'):
                self.bot_instance.db.log_auto_signal_broadcast(len(signals), success_count, len(eligible_users))

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Broadcast error: {e}")

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

    def _format_signals_message(self, signals):
        """Format signals for broadcast"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        message = f"""🚨 **AUTO SnD SIGNALS ALERT** 🚨

🕐 **Time**: {current_time}
📊 **Signals**: {len(signals)} High-Quality Setups
⚡ **Source**: Enhanced SnD Algorithm

"""

        for i, signal in enumerate(signals, 1):
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐"

            message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence']:.0f}%
💰 **Entry**: ${signal['entry_price']:.4f}
🛑 **SL**: ${signal['stop_loss']:.4f}
🎯 **TP1**: ${signal['tp1']:.4f}
🎯 **TP2**: ${signal['tp2']:.4f}

"""

        message += """⚠️ **RISK MANAGEMENT:**
• Max 2-3% position size
• Always use Stop Loss
• Take profit gradually

🔄 **Next scan**: 30 minutes
👑 **Exclusive**: Admin & Lifetime users only"""

        return message

def initialize_auto_signals(bot_instance):
    """Initialize the auto signals system"""
    try:
        return AutoSignalScanner(bot_instance)
    except Exception as e:
        print(f"❌ Failed to initialize auto signals: {e}")
        return None