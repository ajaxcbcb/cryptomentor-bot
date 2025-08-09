import asyncio
import time
import random
from datetime import datetime
from crypto_api import CryptoAPI
from database import Database

class SnDAutoSignals:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.crypto_api = bot_instance.crypto_api
        self.ai = bot_instance.ai

        # Configuration
        self.scan_interval = 30 * 60  # 30 minutes
        self.min_confidence = 70
        self.signal_cooldown = 3600  # 1 hour between same signals
        self.is_running = False
        self.last_scan_time = 0

        # Target cryptocurrencies for auto signals (excluding problematic Binance symbols)
        self.target_symbols = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SHIB', 'DOT',
            'LINK', 'TRX', 'MATIC', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT',
            'ATOM', 'FIL', 'ETC', 'ALGO', 'VET', 'MANA', 'SAND'
        ]

        # Anti-spam system
        self.sent_signals = {}  # Track sent signals: {symbol: {direction: timestamp}}

        print(f"🎯 Auto SnD Signals initialized with {len(self.target_symbols)} altcoins")
        print(f"⏰ Scan interval: {self.scan_interval // 60} minutes")
        print(f"📈 Min confidence: {self.min_confidence}%")

    async def start_auto_scanner(self):
        """Start the auto signal scanner"""
        try:
            if self.is_running:
                print("[AUTO-SIGNAL SND] Scanner sudah berjalan")
                return

            self.is_running = True
            print(f"[AUTO-SIGNAL SND] ✅ Scanner started - Interval: {self.scan_interval//60} minutes")

            while self.is_running:
                try:
                    print(f"[AUTO-SIGNAL SND] 🔄 Starting scan cycle...")
                    await self.scan_and_send_signals()

                    if self.is_running:  # Check if still running after scan
                        print(f"[AUTO-SIGNAL SND] ⏰ Next scan in {self.scan_interval//60} minutes...")
                        await asyncio.sleep(self.scan_interval)

                except Exception as scan_error:
                    print(f"[AUTO-SIGNAL SND] ❌ Scan error: {scan_error}")
                    # Continue running even if one scan fails
                    await asyncio.sleep(300)  # Wait 5 minutes before retry

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Scanner error: {e}")
            self.is_running = False

    async def stop_auto_scanner(self):
        """Stop the auto SnD scanner"""
        self.is_running = False
        print("🛑 Enhanced SnD auto scanner stopped")

    async def scan_and_send_signals(self):
        """Scan for SnD signals and send to eligible users"""
        scan_start = time.time()
        print(f"🔍 Scanning {len(self.target_symbols)} altcoins for enhanced SnD signals...")

        high_confidence_signals = []
        total_scanned = 0

        for symbol in self.target_symbols:
            try:
                signal = await self.analyze_enhanced_snd_signal(symbol)
                total_scanned += 1

                if signal and signal['confidence'] >= self.min_confidence:
                    high_confidence_signals.append(signal)
                    print(f"✅ High confidence signal found: {symbol} - {signal['confidence']:.1f}% ({signal['direction']})")

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue

        scan_duration = time.time() - scan_start
        print(f"📊 Scan completed: {total_scanned}/{len(self.target_symbols)} coins analyzed in {scan_duration:.1f}s")

        if high_confidence_signals:
            print(f"🎯 Found {len(high_confidence_signals)} high-confidence signals")
            await self.send_signals_to_eligible_users(high_confidence_signals)
        else:
            print("📊 No high-confidence signals found in this scan")

        self.last_scan_time = time.time()

    async def analyze_enhanced_snd_signal(self, symbol):
        """Analyze enhanced SnD for a single symbol with FORCED entry logic"""
        try:
            # Get comprehensive data
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol, '1h')
            price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=True)
            futures_data = self.crypto_api.get_long_short_ratio(symbol)

            if 'error' in price_data:
                print(f"❌ Price data error for {symbol}")
                return None

            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            change_24h = price_data.get('change_24h', 0)
            long_ratio = futures_data.get('long_ratio', 50) if 'error' not in futures_data else 50

            # FORCED DECISION LOGIC - Always choose LONG or SHORT
            direction = "LONG"  # Default
            base_confidence = 70  # Auto signals need higher confidence
            reason = "Auto signal analysis"

            # Primary logic: 24h price change
            if change_24h > 3:
                direction = "LONG"
                base_confidence += 10
                reason = f"Strong bullish momentum (+{change_24h:.1f}%)"
            elif change_24h < -3:
                direction = "SHORT"
                base_confidence += 10
                reason = f"Strong bearish momentum ({change_24h:.1f}%)"
            # Secondary logic: Long/Short ratio (contrarian approach)
            if long_ratio > 75:
                direction = "SHORT"
                base_confidence += 8
                reason = f"Extremely overcrowded longs ({long_ratio:.1f}%)"
            elif long_ratio < 25:
                direction = "LONG"
                base_confidence += 8
                reason = f"Extremely oversold positions ({long_ratio:.1f}%)"
            # Use SnD analysis if available
            elif 'error' not in snd_analysis:
                signals = snd_analysis.get('signals', [])
                if signals:
                    best_signal = max(signals, key=lambda x: x.get('confidence', 0))
                    direction = best_signal.get('direction', 'LONG')
                    base_confidence = max(base_confidence, best_signal.get('confidence', 70))
                    reason = f"SnD {direction.lower()} zone confirmed"
                else:
                    # Use trend score
                    trend_score = snd_analysis.get('trend_score', 0)
                    if trend_score > 0:
                        direction = "LONG"
                        reason = "Positive trend detected"
                    else:
                        direction = "SHORT"
                        reason = "Negative trend detected"
            else:
                # Final fallback based on sentiment
                direction = "SHORT" if long_ratio > 50 else "LONG"
                reason = f"Sentiment-based {direction}"

            # Calculate entry, TP, SL with better risk management
            if direction == "LONG":
                entry_price = current_price * 0.997  # Better entry
                tp1 = current_price * 1.03   # 3% profit
                tp2 = current_price * 1.055  # 5.5% profit
                sl = current_price * 0.97    # 3% loss
            else:  # SHORT
                entry_price = current_price * 1.003  # Better entry
                tp1 = current_price * 0.97   # 3% profit
                tp2 = current_price * 0.945  # 5.5% profit
                sl = current_price * 1.03    # 3% loss

            # Risk/Reward calculation
            risk = abs(entry_price - sl)
            reward = abs(tp2 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 2.0

            # Final confidence (auto signals need minimum 80% for reduced spam)
            final_confidence = min(95, max(80, base_confidence))

            # Only return signal if it meets our strict confidence requirement
            if final_confidence < self.min_confidence:
                print(f"[AUTO-SIGNAL SND] ❌ Signal rejected for {symbol}: confidence {final_confidence:.1f}% < required {self.min_confidence}%")
                return None

            return {
                'symbol': symbol,
                'direction': direction,
                'entry_price': round(entry_price, 6),
                'tp1': round(tp1, 6),
                'tp2': round(tp2, 6),
                'sl': round(sl, 6),
                'confidence': final_confidence,
                'risk_reward': round(rr_ratio, 1),
                'current_price': current_price,
                'trend': 'bullish' if direction == 'LONG' else 'bearish',
                'market_structure': f"{direction.lower()}_bias",
                'risk_level': 'medium',
                'timeframe': '1h',
                'scan_time': datetime.now().strftime('%H:%M:%S'),
                'reason': reason,
                'zone_strength': 75,
                'long_ratio': long_ratio,
                'change_24h': change_24h
            }

        except Exception as e:
            print(f"❌ Error in enhanced SnD analysis for {symbol}: {e}")
            return None

    def _calculate_enhanced_confidence(self, signal, snd_analysis, futures_data, current_price):
        """Calculate enhanced confidence with multiple factors"""
        base_confidence = signal.get('confidence', 50)

        # Factor 1: Risk/Reward ratio
        rr_ratio = signal.get('risk_reward_ratio', 1)
        if rr_ratio > 3:
            base_confidence += 15
        elif rr_ratio > 2:
            base_confidence += 10
        elif rr_ratio > 1.5:
            base_confidence += 5

        # Factor 2: Market structure alignment
        market_structure = snd_analysis.get('market_structure', {})
        if market_structure.get('pattern') in ['uptrend', 'downtrend']:
            base_confidence += 10
        elif market_structure.get('strength') == 'strong':
            base_confidence += 5

        # Factor 3: Trend score alignment
        trend_score = snd_analysis.get('trend_score', 1)
        if trend_score >= 2:
            base_confidence += 8
        elif trend_score >= 1:
            base_confidence += 4

        # Factor 4: Futures sentiment alignment
        if 'error' not in futures_data:
            long_ratio = futures_data.get('long_ratio', 50)
            direction = signal.get('direction', '')

            if direction == 'LONG' and long_ratio < 40:  # Contrarian bullish
                base_confidence += 8
            elif direction == 'SHORT' and long_ratio > 65:  # Contrarian bearish
                base_confidence += 8

        # Factor 5: Zone strength
        zone_strength = signal.get('zone_strength', 50)
        if zone_strength > 80:
            base_confidence += 10
        elif zone_strength > 60:
            base_confidence += 5

        return min(95, max(30, base_confidence))

    def _calculate_risk_level(self, confidence, market_structure):
        """Calculate risk level for position sizing"""
        if confidence >= 85 and market_structure.get('strength') == 'strong':
            return 'low'
        elif confidence >= 75:
            return 'medium'
        else:
            return 'high'

    async def send_signals_to_eligible_users(self, signals):
        """Send signals to admin and lifetime users only"""
        try:
            # Get eligible users (admin and lifetime)
            eligible_users = self.db.get_eligible_auto_signal_users()

            if not eligible_users:
                print("❌ No eligible users found for auto signals")
                return

            print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

            # Format signals message with better handling
            signals_message = self._format_signals_message(signals)

            success_count = 0
            for user_data in eligible_users:
                # Handle different user data formats
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id') or user_data.get('telegram_id') or user_data.get('id')
                elif isinstance(user_data, (list, tuple)) and len(user_data) > 0:
                    user_id = user_data[0]
                elif isinstance(user_data, (int, str)):
                    user_id = int(user_data)
                else:
                    print(f"⚠️ Unknown user format: {user_data}")
                    continue

                if not user_id:
                    print(f"⚠️ No user_id found for: {user_data}")
                    continue

                try:
                    # Send with plain text first to avoid markdown issues
                    await self.bot.application.bot.send_message(
                        chat_id=int(user_id),
                        text=signals_message,
                        parse_mode=None,  # No markdown to avoid parsing errors
                        disable_web_page_preview=True
                    )
                    success_count += 1
                    print(f"✅ Sent signals to user {user_id}")
                    await asyncio.sleep(0.2)  # Rate limiting

                except Exception as e:
                    print(f"❌ Failed to send signal to user {user_id}: {e}")
                    continue

            print(f"✅ Auto signals sent to {success_count}/{len(eligible_users)} users")

            # Log the broadcast
            try:
                self.db.log_auto_signals_broadcast(len(signals), success_count, len(eligible_users))
            except:
                pass  # Don't fail if logging fails

        except Exception as e:
            print(f"❌ Error sending auto signals: {e}")
            import traceback
            traceback.print_exc()

    def _format_signals_message(self, signals):
        """Format signals into a readable message (plain text to avoid parsing errors)"""
        message = f"""🚨 AUTO SIGNALS - SUPPLY & DEMAND ANALYSIS

🕐 Scan Time: {datetime.now().strftime('%H:%M:%S WIB')}
📊 Signals Found: {len(signals)}

"""

        for i, signal in enumerate(signals[:5], 1):  # Limit to top 5 signals
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐" if signal['confidence'] >= 75 else "💡"

            message += f"""{i}. {signal['symbol']} {direction_emoji} {signal['direction']}
{confidence_emoji} Confidence: {signal['confidence']:.1f}%
💰 Entry: ${signal['entry_price']:.2f}
🛑 Stop Loss: ${signal['sl']:.2f}
🎯 TP1: ${signal['tp1']:.2f}
🎯 TP2: ${signal['tp2']:.2f}
📊 R/R Ratio: {signal['risk_reward']:.1f}:1
🔄 Trend: {signal['trend'].title()}
⚡ Structure: {signal['market_structure'].replace('_', ' ').title()}
🧠 Reason: {signal['reason']}
📈 24h Change: {signal.get('change_24h', 0):+.2f}%

"""

        message += f"""⚠️ TRADING DISCLAIMER:
• Signals berbasis Supply & Demand analysis
• Gunakan proper risk management
• Position sizing sesuai risk level
• DYOR sebelum trading

🎯 Auto Signals hanya untuk Admin & Lifetime users
📡 Next scan in {self.scan_interval/60:.0f} minutes"""

        return message

    def _get_enhanced_snd_analysis(self, symbol):
        """Get enhanced Supply & Demand analysis with error handling"""
        try:
            # Get candlestick data for SnD analysis
            candlestick_data = self.crypto_api.get_candlestick_data(symbol, '1h', 100)

            if 'error' in candlestick_data:
                return {'error': candlestick_data['error']}

            candles = candlestick_data.get('data', [])
            if not candles or len(candles) < 20:
                return {'error': 'Insufficient candlestick data'}

            # Extract price data with validation
            try:
                highs = [float(candle[2]) for candle in candles if len(candle) > 2]
                lows = [float(candle[3]) for candle in candles if len(candle) > 3]
                closes = [float(candle[4]) for candle in candles if len(candle) > 4]
                volumes = [float(candle[5]) for candle in candles if len(candle) > 5]

                # Validate we have enough data
                if not highs or not lows or not closes or not volumes:
                    return {'error': 'Invalid candlestick data structure'}

                if len(highs) < 20 or len(lows) < 20 or len(closes) < 20:
                    return {'error': 'Insufficient price data after filtering'}

            except (ValueError, IndexError) as e:
                return {'error': f'Price data parsing error: {str(e)}'}

            current_price = closes[-1]

            # Calculate key levels with validation
            resistance_levels = self._calculate_resistance_levels(highs, closes)
            support_levels = self._calculate_support_levels(lows, closes)

            # Volume analysis
            volume_trend = self._analyze_volume_trend(volumes, closes)

            # Generate signals
            self.current_symbol = symbol # Set current symbol for _generate_snd_signal
            signal = self._generate_snd_signal(
                current_price, resistance_levels, support_levels,
                volume_trend, highs, lows, closes
            )

            return signal

        except Exception as e:
            return {'error': f'Enhanced SnD analysis error: {str(e)}'}

    def _calculate_resistance_levels(self, highs, closes):
        """Calculate resistance levels using pivot points"""
        try:
            # Validate input data
            if not highs or len(highs) < 10:
                return []

            # Find local maxima for resistance
            resistance_levels = []
            window = min(5, len(highs) // 4)  # Adaptive window size

            for i in range(window, len(highs) - window):
                local_highs = highs[i-window:i+window+1]
                if local_highs and highs[i] == max(local_highs):
                    resistance_levels.append(highs[i])

            # Get strongest resistance levels
            if resistance_levels:
                resistance_levels.sort(reverse=True)
                return resistance_levels[:3]  # Top 3 resistance levels
            else:
                # Fallback: use recent highs
                recent_highs = sorted(highs[-20:], reverse=True)
                return recent_highs[:3] if recent_highs else []

        except Exception as e:
            print(f"❌ Resistance calculation error: {e}")
            return []

    def _calculate_support_levels(self, lows, closes):
        """Calculate support levels using pivot points"""
        try:
            # Validate input data
            if not lows or len(lows) < 10:
                return []

            # Find local minima for support
            support_levels = []
            window = min(5, len(lows) // 4)  # Adaptive window size

            for i in range(window, len(lows) - window):
                local_lows = lows[i-window:i+window+1]
                if local_lows and lows[i] == min(local_lows):
                    support_levels.append(lows[i])

            # Get strongest support levels
            if support_levels:
                support_levels.sort()
                return support_levels[:3]  # Top 3 support levels
            else:
                # Fallback: use recent lows
                recent_lows = sorted(lows[-20:])
                return recent_lows[:3] if recent_lows else []

        except Exception as e:
            print(f"❌ Support calculation error: {e}")
            return []

    def _analyze_volume_trend(self, volumes, closes):
        """Analyze volume trend relative to price"""
        try:
            if len(volumes) < 5: return 0

            recent_volumes = volumes[-5:]
            avg_volume = sum(recent_volumes) / len(recent_volumes)

            # Check for significant volume increase
            if recent_volumes[-1] > avg_volume * 1.5:
                if closes[-1] > closes[-2]: # Price increased with volume
                    return 1 # Bullish volume
                elif closes[-1] < closes[-2]: # Price decreased with volume
                    return -1 # Bearish volume

            return 0 # Neutral volume

        except Exception as e:
            print(f"❌ Volume trend analysis error: {e}")
            return 0

    def _generate_snd_signal(self, current_price, resistance_levels, support_levels, volume_trend, highs, lows, closes):
        """Generate an SnD signal based on analysis"""
        signal = {
            'symbol': self.current_symbol, # Need to set this from caller
            'direction': 'LONG', # Default
            'entry_price': current_price,
            'tp1': current_price,
            'tp2': current_price,
            'sl': current_price,
            'confidence': 50,
            'risk_reward': 1.0,
            'current_price': current_price,
            'trend': 'neutral',
            'market_structure': 'sideways',
            'risk_level': 'medium',
            'timeframe': '1h',
            'scan_time': datetime.now().strftime('%H:%M:%S'),
            'reason': 'Initial analysis',
            'zone_strength': 50,
            'long_ratio': 50, # Default if not available
            #'change_24h': 0 # Default if not available
        }

        # Determine trend
        if closes[-1] > closes[-5] and closes[-5] > closes[-10]:
            signal['trend'] = 'bullish'
        elif closes[-1] < closes[-5] and closes[-5] < closes[-10]:
            signal['trend'] = 'bearish'

        # Determine market structure and generate signal
        is_in_support = any(current_price >= support <= current_price * 1.02 for support in support_levels)
        is_near_resistance = any(current_price >= resistance * 0.98 and current_price <= resistance for resistance in resistance_levels)

        if is_in_support:
            signal['direction'] = 'LONG'
            signal['reason'] = 'Price at support level'
            signal['market_structure'] = 'uptrend_bias'
            signal['confidence'] += 15
            signal['zone_strength'] = 75

            # Set TP/SL for LONG
            signal['entry_price'] = current_price * 0.995 # Slightly below current
            signal['sl'] = support_levels[0] * 0.99 if support_levels else current_price * 0.97
            signal['tp1'] = signal['entry_price'] * 1.02 # 2% profit
            signal['tp2'] = signal['entry_price'] * 1.04 # 4% profit

            risk = abs(signal['entry_price'] - signal['sl'])
            reward = abs(signal['tp2'] - signal['entry_price'])
            signal['risk_reward'] = round(reward / risk, 1) if risk > 0 else 2.0
            signal['confidence'] = min(95, signal['confidence'] + int(signal['risk_reward'] * 5))

        elif is_near_resistance:
            signal['direction'] = 'SHORT'
            signal['reason'] = 'Price near resistance level'
            signal['market_structure'] = 'downtrend_bias'
            signal['confidence'] += 15
            signal['zone_strength'] = 75

            # Set TP/SL for SHORT
            signal['entry_price'] = current_price * 1.005 # Slightly above current
            signal['sl'] = resistance_levels[0] * 1.01 if resistance_levels else current_price * 1.03
            signal['tp1'] = signal['entry_price'] * 0.98 # 2% profit
            signal['tp2'] = signal['entry_price'] * 0.96 # 4% profit

            risk = abs(signal['entry_price'] - signal['sl'])
            reward = abs(signal['tp2'] - signal['entry_price'])
            signal['risk_reward'] = round(reward / risk, 1) if risk > 0 else 2.0
            signal['confidence'] = min(95, signal['confidence'] + int(signal['risk_reward'] * 5))

        else: # Sideways or no clear S/R
            if signal['trend'] == 'bullish':
                signal['direction'] = 'LONG'
                signal['reason'] = 'Bullish trend continuation'
                signal['market_structure'] = 'uptrend'
                signal['confidence'] += 5
            elif signal['trend'] == 'bearish':
                signal['direction'] = 'SHORT'
                signal['reason'] = 'Bearish trend continuation'
                signal['market_structure'] = 'downtrend'
                signal['confidence'] += 5
            else:
                signal['reason'] = 'Consolidation or unclear trend'

        # Incorporate volume trend
        if volume_trend > 0 and signal['direction'] == 'LONG':
            signal['confidence'] += 5
            signal['zone_strength'] = min(90, signal['zone_strength'] + 5)
        elif volume_trend < 0 and signal['direction'] == 'SHORT':
            signal['confidence'] += 5
            signal['zone_strength'] = min(90, signal['zone_strength'] + 5)

        # Ensure confidence is within bounds
        signal['confidence'] = max(30, min(95, signal['confidence']))

        # Adjust entry for slightly better price if not already set
        if is_in_support and signal['entry_price'] == current_price:
            signal['entry_price'] = current_price * 0.995
        elif is_near_resistance and signal['entry_price'] == current_price:
            signal['entry_price'] = current_price * 1.005

        return signal

# Initialize function for the auto signals system
def initialize_auto_signals(bot_instance):
    """Initialize the auto signals system"""
    try:
        auto_signals = SnDAutoSignals(bot_instance)
        print("✅ Enhanced SnD Auto Signals system initialized")
        return auto_signals
    except Exception as e:
        print(f"❌ Failed to initialize auto signals: {e}")
        return None

async def send_auto_signals_to_users(self, signals):
    """Send signals to eligible users (Admin + Lifetime)"""
    try:
        eligible_users = self.db.get_eligible_auto_signal_users()

        if not eligible_users:
            print("📊 No eligible users for auto signals")
            return

        print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

        # Format signals message
        message = self._format_auto_signals_message(signals)

        # Send to each eligible user
        for user in eligible_users:
            try:
                # Handle different user data formats
                if isinstance(user, dict):
                    user_id = user.get('telegram_id') or user.get('id')
                elif isinstance(user, (list, tuple)) and len(user) > 0:
                    user_id = user[0]  # First element should be telegram_id
                elif isinstance(user, (int, str)):
                    user_id = int(user)
                else:
                    print(f"⚠️ Unknown user format: {user} (type: {type(user)})")
                    continue

                if not user_id:
                    print(f"⚠️ No user_id found for user: {user}")
                    continue

                await self.bot.application.bot.send_message(
                    chat_id=int(user_id),
                    text=message,
                    parse_mode='Markdown'
                )

                print(f"✅ Sent auto signals to user {user_id}")
                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"❌ Failed to send to user {user_id}: {e}")
                continue

    except Exception as e:
        print(f"❌ Error sending auto signals: {e}")
        import traceback
        traceback.print_exc()

async def send_signals_to_users(self, signals):
    """Send signals to eligible users"""
    try:
        if not signals:
            print("📊 No signals to send")
            return

        # Get eligible users (Admin + Lifetime premium)
        eligible_users = self.db.get_eligible_auto_signal_users()

        if not eligible_users:
            print("👥 No eligible users for auto signals")
            return

        print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

        # Format signals message
        message = self._format_auto_signals_message(signals)

        # Send to each eligible user
        for user in eligible_users:
            try:
                # Handle different user data formats
                if isinstance(user, dict):
                    user_id = user.get('telegram_id')
                    user_name = user.get('first_name', 'User')
                elif isinstance(user, (list, tuple)) and len(user) > 0:
                    user_id = user[0]
                    user_name = user[1] if len(user) > 1 else 'User'
                elif isinstance(user, int):
                    user_id = user
                    user_name = 'User'
                else:
                    print(f"❌ Invalid user format: {user}")
                    continue

                if not user_id:
                    print(f"❌ No user_id found for user: {user}")
                    continue

                await self.bot.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                print(f"✅ Sent auto signals to user {user_id} ({user_name})")

                # Log the activity
                self.db.log_user_activity(user_id, "auto_signal_received", f"Received {len(signals)} auto SnD signals")

            except Exception as e:
                print(f"❌ Failed to send signals to user {user_id}: {e}")

    except Exception as e:
        print(f"❌ Error sending auto signals: {e}")
        import traceback
        traceback.print_exc()