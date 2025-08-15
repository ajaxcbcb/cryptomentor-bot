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
        """Analyze enhanced SnD signal using exact /futures_signals logic for consistency"""
        try:
            # Use the same logic as /futures_signals command through the AI assistant
            signal = await self._enhanced_scan_symbol_for_signal(symbol, self.crypto_api)

            if signal and signal.get('confidence', 0) >= self.min_confidence:
                # Ensure the format matches our expectations
                return {
                    'symbol': signal['symbol'],
                    'direction': signal['direction'],
                    'entry_price': signal['entry'],  # Match old format
                    'tp1': signal['tp1'],
                    'tp2': signal['tp2'],
                    'sl': signal['sl'],
                    'confidence': signal['confidence'],
                    'risk_reward': signal['rr_ratio'],
                    'current_price': signal.get('current_price', 0),
                    'trend': signal['trend'],
                    'market_structure': signal['structure'] + '_bias',
                    'risk_level': 'medium',
                    'timeframe': '1h',
                    'scan_time': datetime.now().strftime('%H:%M:%S'),
                    'reason': signal['reason'],
                    'zone_strength': 75,
                    'long_ratio': signal.get('long_ratio', 50),
                    'change_24h': signal.get('change_24h', 0)
                }

            return None

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
            # Get eligible users (admin and lifetime from Supabase)
            eligible_users = self._get_eligible_users_supabase()

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
💰 Entry: ${signal['entry_price']:,.2f}
🛑 Stop Loss: ${signal['sl']:,.2f}
🎯 TP1: ${signal['tp1']:,.2f}
🎯 TP2: ${signal['tp2']:,.2f}
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

    def _get_eligible_users_supabase(self):
        """Get eligible users from Supabase (admin + lifetime premium)"""
        try:
            import os
            from app.supabase_conn import sb_list_users
            
            # Get admin IDs from environment
            eligible_users = []
            
            # Add admin users
            for i in range(1, 10):
                env_key = f'ADMIN{i}'
                admin_id_str = (os.getenv(env_key) or "").strip()
                
                # Fallback to old naming format
                if not admin_id_str and i <= 2:
                    fallback_key = f'ADMIN{i}_USER_ID' if i > 1 else 'ADMIN_USER_ID'
                    admin_id_str = (os.getenv(fallback_key) or "").strip()
                
                if admin_id_str and admin_id_str.lower() != "none" and admin_id_str.isdigit():
                    eligible_users.append(int(admin_id_str))
            
            # Get lifetime premium users from Supabase
            lifetime_users = sb_list_users({
                "is_premium": "eq.true",
                "banned": "eq.false", 
                "premium_until": "is.null",
                "select": "telegram_id"
            })
            
            # Add lifetime users
            for user in lifetime_users:
                user_id = user.get("telegram_id")
                if user_id and user_id not in eligible_users:
                    eligible_users.append(user_id)
            
            print(f"📊 Eligible users found: {len(eligible_users)} (Admins + Lifetime from Supabase)")
            return eligible_users
            
        except Exception as e:
            print(f"❌ Error getting eligible users from Supabase: {e}")
            return []

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

        # Determine trend with multiple timeframes
        short_trend = 'neutral'
        medium_trend = 'neutral'

        # Short-term trend (last 5 candles)
        if closes[-1] > closes[-3] and closes[-3] > closes[-5]:
            short_trend = 'bullish'
        elif closes[-1] < closes[-3] and closes[-3] < closes[-5]:
            short_trend = 'bearish'

        # Medium-term trend (last 10 candles)
        if closes[-1] > closes[-5] and closes[-5] > closes[-10]:
            medium_trend = 'bullish'
        elif closes[-1] < closes[-5] and closes[-5] < closes[-10]:
            medium_trend = 'bearish'

        # Set overall trend
        if short_trend == 'bullish' and medium_trend == 'bullish':
            signal['trend'] = 'bullish'
        elif short_trend == 'bearish' and medium_trend == 'bearish':
            signal['trend'] = 'bearish'
        elif short_trend == 'bullish' or medium_trend == 'bullish':
            signal['trend'] = 'bullish'
        elif short_trend == 'bearish' or medium_trend == 'bearish':
            signal['trend'] = 'bearish'
        else:
            signal['trend'] = 'neutral'

        # Determine market structure and generate signal - BALANCED APPROACH
        is_near_support = any(abs(current_price - support) / current_price <= 0.02 for support in support_levels)
        is_near_resistance = any(abs(current_price - resistance) / current_price <= 0.02 for resistance in resistance_levels)

        # Score-based signal generation
        long_signal_score = 0
        short_signal_score = 0

        # Support/Resistance scoring
        if is_near_support:
            long_signal_score += 3
        if is_near_resistance:
            short_signal_score += 3

        # Trend scoring
        if signal['trend'] == 'bullish':
            long_signal_score += 2
        elif signal['trend'] == 'bearish':
            short_signal_score += 2

        # Price momentum scoring
        recent_change = ((closes[-1] - closes[-3]) / closes[-3]) * 100
        if recent_change > 1:
            long_signal_score += 2
        elif recent_change < -1:
            short_signal_score += 2
        elif recent_change > 0:
            long_signal_score += 1
        else:
            short_signal_score += 1

        # Determine final signal direction
        if long_signal_score > short_signal_score:
            signal['direction'] = 'LONG'
            signal['confidence'] += min(20, long_signal_score * 3)

            if is_near_support:
                signal['reason'] = 'Price bouncing from support level'
                signal['market_structure'] = 'support_bounce'
                signal['zone_strength'] = 80
            elif signal['trend'] == 'bullish':
                signal['reason'] = 'Bullish trend continuation'
                signal['market_structure'] = 'uptrend'
                signal['zone_strength'] = 70
            else:
                signal['reason'] = 'Bullish momentum detected'
                signal['market_structure'] = 'bullish_bias'
                signal['zone_strength'] = 65

            # Set TP/SL for LONG
            signal['entry_price'] = current_price * 0.998  # Slightly below current
            signal['sl'] = support_levels[0] * 0.99 if support_levels else current_price * 0.975
            signal['tp1'] = signal['entry_price'] * 1.025  # 2.5% profit
            signal['tp2'] = signal['entry_price'] * 1.045  # 4.5% profit

        elif short_signal_score > long_signal_score:
            signal['direction'] = 'SHORT'
            signal['confidence'] += min(20, short_signal_score * 3)

            if is_near_resistance:
                signal['reason'] = 'Price rejected at resistance level'
                signal['market_structure'] = 'resistance_rejection'
                signal['zone_strength'] = 80
            elif signal['trend'] == 'bearish':
                signal['reason'] = 'Bearish trend continuation'
                signal['market_structure'] = 'downtrend'
                signal['zone_strength'] = 70
            else:
                signal['reason'] = 'Bearish momentum detected'
                signal['market_structure'] = 'bearish_bias'
                signal['zone_strength'] = 65

            # Set TP/SL for SHORT
            signal['entry_price'] = current_price * 1.002  # Slightly above current
            signal['sl'] = resistance_levels[0] * 1.01 if resistance_levels else current_price * 1.025
            signal['tp1'] = signal['entry_price'] * 0.975  # 2.5% profit
            signal['tp2'] = signal['entry_price'] * 0.955  # 4.5% profit

        else: # Equal scores - use trend as tiebreaker
            if signal['trend'] == 'bullish':
                signal['direction'] = 'LONG'
                signal['reason'] = 'Neutral setup with bullish bias'
                signal['market_structure'] = 'consolidation_bullish'
                signal['confidence'] += 5

                # Conservative LONG setup
                signal['entry_price'] = current_price * 0.998
                signal['sl'] = current_price * 0.98
                signal['tp1'] = current_price * 1.02
                signal['tp2'] = current_price * 1.035

            elif signal['trend'] == 'bearish':
                signal['direction'] = 'SHORT'
                signal['reason'] = 'Neutral setup with bearish bias'
                signal['market_structure'] = 'consolidation_bearish'
                signal['confidence'] += 5

                # Conservative SHORT setup
                signal['entry_price'] = current_price * 1.002
                signal['sl'] = current_price * 1.02
                signal['tp1'] = current_price * 0.98
                signal['tp2'] = current_price * 0.965

            else:
                # Truly neutral - default to trend following recent momentum
                if recent_change >= 0:
                    signal['direction'] = 'LONG'
                    signal['reason'] = 'Consolidation with slight bullish momentum'
                    signal['entry_price'] = current_price * 0.999
                    signal['sl'] = current_price * 0.985
                    signal['tp1'] = current_price * 1.015
                    signal['tp2'] = current_price * 1.025
                else:
                    signal['direction'] = 'SHORT'
                    signal['reason'] = 'Consolidation with slight bearish momentum'
                    signal['entry_price'] = current_price * 1.001
                    signal['sl'] = current_price * 1.015
                    signal['tp1'] = current_price * 0.985
                    signal['tp2'] = current_price * 0.975

        # Calculate risk/reward ratio
        risk = abs(signal['entry_price'] - signal['sl'])
        reward = abs(signal['tp2'] - signal['entry_price'])
        signal['risk_reward'] = round(reward / risk, 1) if risk > 0 else 2.0

        # Bonus confidence for good risk/reward
        if signal['risk_reward'] > 2:
            signal['confidence'] += 5
        elif signal['risk_reward'] > 1.5:
            signal['confidence'] += 3

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

    # --- New methods for consistent signal generation ---
    def _handle_signal_generation_error(self, e):
        """Handle errors in signal generation with fallback response"""
        try:
            return {
                'direction': 'NEUTRAL',
                'confidence': 50,
                'strategy': 'Basic Analysis',
                'time_horizon': '4-24 hours',
                'error': str(e)
            }
        except Exception as fallback_error:
            return {
                'direction': 'NEUTRAL',
                'confidence': 50,
                'strategy': 'Error Recovery',
                'time_horizon': '4-24 hours',
                'error': f'Signal generation failed: {str(fallback_error)}'
            }

    async def _enhanced_scan_symbol_for_signal(self, symbol, crypto_api):
        """Enhanced symbol scanning with exact /futures_signals logic"""
        try:
            if not crypto_api:
                return None

            # Get comprehensive market data like /futures_signals does
            price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            futures_data = crypto_api.get_futures_data(symbol)

            if 'error' in price_data or not price_data.get('success'):
                return None

            current_price = self._normalize_data(price_data, ['price', 'current_price'])
            change_24h = self._normalize_data(price_data, ['change_24h', 'price_change_24h', 'percent_change_24h'])

            if not current_price:
                return None

            # Use AI assistant's futures signal generation for consistency
            # This ensures we use the exact same logic as /futures_signals command
            signal_data = await self._generate_consistent_futures_signal(
                symbol, current_price, price_data, futures_data, crypto_api
            )

            if signal_data and signal_data.get('confidence', 0) >= self.min_confidence:
                return signal_data

            return None

        except Exception as e:
            print(f"❌ Enhanced scan error for {symbol}: {e}")
            return None

    async def _generate_consistent_futures_signal(self, symbol, current_price, price_data, futures_data, crypto_api):
        """Generate signal using the same enhanced logic as /futures_signals"""
        try:
            # Multi-timeframe technical analysis like in /futures_signals
            ohlcv_1h = self.ai.get_coinapi_ohlcv_data(symbol, '1HRS', 100)
            ohlcv_4h = self.ai.get_coinapi_ohlcv_data(symbol, '4HRS', 100)

            primary_indicators = {}
            higher_tf_indicators = {}

            if ohlcv_1h.get('success'):
                primary_indicators = self.ai.calculate_technical_indicators(ohlcv_1h['data'])

            if ohlcv_4h.get('success'):
                higher_tf_indicators = self.ai.calculate_technical_indicators(ohlcv_4h['data'])

            if 'error' in primary_indicators:
                return None

            # Enhanced signal generation matching AI assistant logic
            signal_data = self.ai._generate_enhanced_trading_signal(
                primary_indicators, higher_tf_indicators, futures_data, current_price, {}
            )

            if signal_data['direction'] == 'NEUTRAL':
                return None

            # Trading levels calculation matching AI assistant logic  
            trading_levels = self.ai._calculate_advanced_trading_levels(
                current_price, signal_data, primary_indicators, {}
            )

            # Format exactly like /futures_signals output
            change_24h = self._normalize_data(price_data, ['change_24h', 'price_change_24h', 'percent_change_24h']) or 0

            # Get futures bias
            long_ratio = 50
            if futures_data and futures_data.get('success'):
                long_short_data = futures_data.get('data', {}).get('long_short', {})
                long_ratio = long_short_data.get('long_ratio', 50)

            return {
                'symbol': symbol,
                'direction': signal_data['direction'],
                'confidence': round(signal_data['confidence'], 2),
                'entry': round(trading_levels['entry'], 2),
                'sl': round(trading_levels['stop_loss'], 2),
                'tp1': round(trading_levels['tp1'], 2),
                'tp2': round(trading_levels['tp2'], 2),
                'rr_ratio': f"{trading_levels['rr_ratio']:.1f}:1",
                'trend': signal_data.get('strategy', 'Technical').replace(' Analysis', '').lower(),
                'structure': signal_data['direction'].lower(),
                'reason': self._generate_signal_reason(signal_data, change_24h, long_ratio),
                'current_price': current_price,
                'change_24h': change_24h,
                'long_ratio': long_ratio,
                'timeframe': '1h',
                'scan_time': datetime.now().strftime('%H:%M:%S WIB')
            }

        except Exception as e:
            print(f"❌ Consistent signal generation error for {symbol}: {e}")
            return None

    def _normalize_data(self, data, field_aliases):
        """Normalize data fields using aliases - same as AI assistant"""
        if not isinstance(data, dict):
            return None

        for alias in field_aliases:
            if alias in data and data[alias] is not None:
                try:
                    return float(data[alias]) if isinstance(data[alias], (str, int, float)) else data[alias]
                except (ValueError, TypeError):
                    continue
        return None

    def _generate_signal_reason(self, signal_data, change_24h, long_ratio):
        """Generate signal reason matching /futures_signals style"""
        direction = signal_data['direction']
        confidence = signal_data['confidence']

        if change_24h > 5:
            return f"Strong {direction.lower()} momentum (+{change_24h:.1f}%)"
        elif change_24h > 2:
            return f"{direction.title()} momentum (+{change_24h:.1f}%)"
        elif change_24h < -5:
            return f"Strong {direction.lower()} momentum ({change_24h:.1f}%)"
        elif change_24h < -2:
            return f"{direction.title()} momentum ({change_24h:.1f}%)"
        elif confidence >= 85:
            return f"High confidence {direction.lower()} setup"
        elif long_ratio > 70 and direction == 'SHORT':
            return f"Contrarian {direction.lower()} - overcrowded longs"
        elif long_ratio < 30 and direction == 'LONG':
            return f"Contrarian {direction.lower()} - oversold conditions"
        else:
            return f"Technical {direction.lower()} confluence"