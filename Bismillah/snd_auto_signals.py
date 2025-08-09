import asyncio
import logging
import time
from datetime import datetime, timedelta
import json
import random
import requests
from typing import Dict, List, Any, Optional
from crypto_api import CryptoAPI
from database import Database

class SnDAutoSignals:
    """
    Manages the automatic detection and sending of Supply & Demand trading signals.
    It scans target cryptocurrencies at a defined interval, analyzes their market data
    using enhanced logic, and sends high-confidence signals to eligible users (admin and lifetime).
    """
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.crypto_api = bot_instance.crypto_api
        self.ai = bot_instance.ai # Assuming AI capabilities are used elsewhere or for future enhancements

        # Configuration for the auto scanner
        self.scan_interval = 30 * 60  # Scan every 30 minutes
        self.min_confidence = 70      # Minimum confidence threshold for sending signals
        self.signal_cooldown = 3600   # Cooldown period for sending similar signals (1 hour)
        self.is_running = False       # Flag to track if the scanner is active
        self.last_scan_time = 0       # Timestamp of the last scan

        # Target cryptocurrencies for auto signals. Excludes symbols known to cause issues.
        self.target_symbols = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SHIB', 'DOT',
            'LINK', 'TRX', 'MATIC', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT',
            'ATOM', 'FIL', 'ETC', 'ALGO', 'VET', 'MANA', 'SAND'
        ]

        # Anti-spam system to track sent signals
        self.sent_signals = {}  # Format: {symbol: {direction: timestamp}}

        # Initial logging of configuration
        print(f"🎯 Auto SnD Signals initialized with {len(self.target_symbols)} altcoins")
        print(f"⏰ Scan interval: {self.scan_interval // 60} minutes")
        print(f"📈 Min confidence: {self.min_confidence}%")

    async def start_auto_scanner(self):
        """
        Starts the automated signal scanning process.
        It runs in a loop, performing scans at the configured interval.
        Handles potential errors during scanning and ensures the scanner continues running.
        """
        try:
            if self.is_running:
                print("[AUTO-SIGNAL SND] Scanner already running.")
                return

            self.is_running = True
            print(f"[AUTO-SIGNAL SND] ✅ Scanner started - Interval: {self.scan_interval // 60} minutes")

            while self.is_running:
                try:
                    print(f"[AUTO-SIGNAL SND] 🔄 Starting scan cycle...")
                    await self.scan_and_send_signals()

                    # Check if the scanner is still intended to be running after the scan
                    if self.is_running:
                        print(f"[AUTO-SIGNAL SND] ⏰ Next scan in {self.scan_interval // 60} minutes...")
                        await asyncio.sleep(self.scan_interval)

                except Exception as scan_error:
                    print(f"[AUTO-SIGNAL SND] ❌ Scan error encountered: {scan_error}")
                    # Wait before retrying to avoid overwhelming the system or API
                    await asyncio.sleep(300)  # Wait 5 minutes before the next retry

        except Exception as e:
            print(f"[AUTO-SIGNAL SND] ❌ Critical scanner error: {e}")
            self.is_running = False # Ensure scanner stops on critical errors

    async def stop_auto_scanner(self):
        """Stops the auto signal scanner gracefully."""
        self.is_running = False
        print("🛑 Enhanced SnD auto scanner stopped.")

    async def scan_and_send_signals(self):
        """
        Performs a full scan of target cryptocurrencies for SnD signals.
        Analyzes each symbol, filters by confidence, and sends valid signals.
        Logs scan duration and results.
        """
        scan_start = time.time()
        print(f"🔍 Scanning {len(self.target_symbols)} altcoins for enhanced SnD signals...")

        high_confidence_signals = []
        total_scanned = 0

        # Iterate through each target symbol to analyze for signals
        for symbol in self.target_symbols:
            try:
                # Analyze for enhanced SnD signals using specific logic
                signal = await self.analyze_enhanced_snd_signal(symbol)
                total_scanned += 1

                # Check if a signal was found and meets the minimum confidence threshold
                if signal and signal['confidence'] >= self.min_confidence:
                    high_confidence_signals.append(signal)
                    print(f"✅ High confidence signal found: {symbol} - {signal['confidence']:.1f}% ({signal['direction']})")

                # Implement a small delay between API calls to avoid rate limits
                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue # Continue scanning other symbols even if one fails

        scan_duration = time.time() - scan_start
        print(f"📊 Scan completed: {total_scanned}/{len(self.target_symbols)} coins analyzed in {scan_duration:.1f}s")

        # Send the collected high-confidence signals if any were found
        if high_confidence_signals:
            print(f"🎯 Found {len(high_confidence_signals)} high-confidence signals")
            await self.send_signals_to_eligible_users(high_confidence_signals)
        else:
            print("📊 No high-confidence signals found in this scan.")

        self.last_scan_time = time.time() # Update the last scan time

    async def analyze_enhanced_snd_signal(self, symbol):
        """
        Analyzes Supply & Demand for a given symbol with a FORCED entry logic.
        This function combines various data points (price change, futures ratios, SnD analysis)
        to determine a signal direction and confidence level.
        It also calculates entry, take profit, and stop loss levels with risk management.
        """
        try:
            # Fetch necessary data for analysis
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol, '1h')
            price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=True)
            futures_data = self.crypto_api.get_long_short_ratio(symbol)

            # Validate price data retrieval
            if 'error' in price_data:
                print(f"❌ Price data error for {symbol}")
                return None

            current_price = price_data.get('price', 0)
            if current_price <= 0: # Ensure price is valid
                return None

            change_24h = price_data.get('change_24h', 0)
            # Safely get long_ratio, default to 50 if futures_data has an error
            long_ratio = futures_data.get('long_ratio', 50) if 'error' not in futures_data else 50

            # --- FORCED DECISION LOGIC ---
            # This logic prioritizes certain factors to determine the signal direction.
            direction = "LONG"  # Default direction
            base_confidence = 70  # Base confidence for auto signals (higher requirement)
            reason = "Auto signal analysis" # Default reason

            # Primary logic: Use 24-hour price change for initial direction
            if change_24h > 3:
                direction = "LONG"
                base_confidence += 10
                reason = f"Strong bullish momentum (+{change_24h:.1f}%)"
            elif change_24h < -3:
                direction = "SHORT"
                base_confidence += 10
                reason = f"Strong bearish momentum ({change_24h:.1f}%)"

            # Secondary logic: Incorporate Futures Long/Short ratio (contrarian approach)
            if long_ratio > 75: # High longs indicate potential for a short
                direction = "SHORT"
                base_confidence += 8
                reason = f"Extremely overcrowded longs ({long_ratio:.1f}%)"
            elif long_ratio < 25: # Low longs indicate potential for a long
                direction = "LONG"
                base_confidence += 8
                reason = f"Extremely oversold positions ({long_ratio:.1f}%)"

            # Tertiary logic: Use Supply/Demand analysis if available and provides a clear signal
            elif 'error' not in snd_analysis:
                signals = snd_analysis.get('signals', [])
                if signals:
                    # Select the signal with the highest confidence from the SnD analysis
                    best_signal = max(signals, key=lambda x: x.get('confidence', 0))
                    direction = best_signal.get('direction', 'LONG') # Use SnD direction
                    base_confidence = max(base_confidence, best_signal.get('confidence', 70)) # Use higher confidence
                    reason = f"SnD {direction.lower()} zone confirmed"
                else:
                    # Fallback to trend score if no specific SnD signals are found
                    trend_score = snd_analysis.get('trend_score', 0)
                    if trend_score > 0:
                        direction = "LONG"
                        reason = "Positive trend detected"
                    else:
                        direction = "SHORT"
                        reason = "Negative trend detected"
            else:
                # Final fallback strategy based on sentiment if no other data is available
                direction = "SHORT" if long_ratio > 50 else "LONG"
                reason = f"Sentiment-based {direction}"

            # --- Risk Management: Calculate Entry, Take Profit (TP), Stop Loss (SL) ---
            # These are set with fixed profit targets and stop loss percentages.
            if direction == "LONG":
                entry_price = current_price * 0.997  # Aim for a slightly better entry
                tp1 = current_price * 1.03   # Target Profit 1: 3% gain
                tp2 = current_price * 1.055  # Target Profit 2: 5.5% gain
                sl = current_price * 0.97    # Stop Loss: 3% loss
            else:  # SHORT
                entry_price = current_price * 1.003  # Aim for a slightly better entry
                tp1 = current_price * 0.97   # Target Profit 1: 3% gain
                tp2 = current_price * 0.945  # Target Profit 2: 5.5% gain
                sl = current_price * 1.03    # Stop Loss: 3% loss

            # Calculate Risk/Reward ratio
            risk = abs(entry_price - sl)
            reward = abs(tp2 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 2.0 # Default RR to 2:1 if risk is zero

            # Final confidence adjustment. Auto signals require higher confidence.
            final_confidence = min(95, max(80, base_confidence)) # Ensure confidence is between 80-95%

            # Reject signal if it doesn't meet the minimum confidence threshold
            if final_confidence < self.min_confidence:
                print(f"[AUTO-SIGNAL SND] ❌ Signal rejected for {symbol}: confidence {final_confidence:.1f}% < required {self.min_confidence}%")
                return None

            # Return the structured signal data
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
                'market_structure': f"{direction.lower()}_bias", # Simplified market structure
                'risk_level': 'medium', # Default risk level
                'timeframe': '1h',
                'scan_time': datetime.now().strftime('%H:%M:%S'),
                'reason': reason,
                'zone_strength': 75, # Placeholder, can be refined
                'long_ratio': long_ratio,
                'change_24h': change_24h
            }

        except Exception as e:
            print(f"❌ Error in enhanced SnD analysis for {symbol}: {e}")
            return None # Return None if any error occurs during analysis

    def _calculate_enhanced_confidence(self, signal, snd_analysis, futures_data, current_price):
        """
        Calculates an enhanced confidence score based on multiple factors.
        This is a helper function that could be used to refine confidence scoring.
        (Note: This function is defined but not currently used in the main flow of analyze_enhanced_snd_signal)
        """
        base_confidence = signal.get('confidence', 50)

        # Factor 1: Risk/Reward ratio contribution
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

        # Factor 4: Futures sentiment alignment (contrarian approach)
        if 'error' not in futures_data:
            long_ratio = futures_data.get('long_ratio', 50)
            direction = signal.get('direction', '')

            if direction == 'LONG' and long_ratio < 40:  # Contrarian bullish signal
                base_confidence += 8
            elif direction == 'SHORT' and long_ratio > 65:  # Contrarian bearish signal
                base_confidence += 8

        # Factor 5: Zone strength contribution
        zone_strength = signal.get('zone_strength', 50)
        if zone_strength > 80:
            base_confidence += 10
        elif zone_strength > 60:
            base_confidence += 5

        return min(95, max(30, base_confidence)) # Clamp confidence between 30 and 95

    def _calculate_risk_level(self, confidence, market_structure):
        """
        Calculates the risk level for position sizing based on confidence and market structure.
        (Note: This function is defined but not currently used in the main flow.)
        """
        if confidence >= 85 and market_structure.get('strength') == 'strong':
            return 'low'
        elif confidence >= 75:
            return 'medium'
        else:
            return 'high'

    async def send_signals_to_eligible_users(self, signals):
        """
        Sends the collected trading signals to eligible users (Admin and Lifetime premium).
        Formats the signals into a readable message and handles sending to each user.
        Includes error handling for sending and logs broadcast activity.
        """
        try:
            # Retrieve users who are eligible for auto signals from the database
            eligible_users = self.db.get_eligible_auto_signal_users()

            if not eligible_users:
                print("❌ No eligible users found for auto signals.")
                return

            print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

            # Format the signals into a plain text message to avoid markdown parsing issues
            signals_message = self._format_signals_message(signals)

            success_count = 0
            # Iterate through each eligible user to send the signals
            for user_data in eligible_users:
                user_id = None
                # Handle different possible formats of user data from the database
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id') or user_data.get('telegram_id') or user_data.get('id')
                elif isinstance(user_data, (list, tuple)) and len(user_data) > 0:
                    user_id = user_data[0] # Assume the first element is the user ID
                elif isinstance(user_data, (int, str)):
                    user_id = int(user_data) # Convert to int if it's a string or int
                else:
                    print(f"⚠️ Unknown user format encountered: {user_data}")
                    continue # Skip if user format is unrecognized

                if not user_id:
                    print(f"⚠️ No user_id could be extracted from user data: {user_data}")
                    continue # Skip if no user ID is found

                try:
                    # Send the message using the bot instance. Parse mode is None for plain text.
                    await self.bot.application.bot.send_message(
                        chat_id=int(user_id),
                        text=signals_message,
                        parse_mode=None, # Use None for plain text to prevent errors
                        disable_web_page_preview=True
                    )
                    success_count += 1
                    print(f"✅ Successfully sent signals to user {user_id}")
                    await asyncio.sleep(0.2)  # Small delay to respect Telegram API rate limits

                except Exception as e:
                    print(f"❌ Failed to send signal to user {user_id}: {e}")
                    continue # Continue to the next user even if one fails

            print(f"✅ Auto signals broadcast summary: Sent to {success_count}/{len(eligible_users)} users")

            # Attempt to log the broadcast activity, but don't let it crash the process
            try:
                self.db.log_auto_signals_broadcast(len(signals), success_count, len(eligible_users))
            except:
                pass # Ignore errors during logging

        except Exception as e:
            print(f"❌ An unexpected error occurred during signal sending: {e}")
            import traceback
            traceback.print_exc() # Print traceback for debugging critical errors

    def _format_signals_message(self, signals):
        """
        Formats a list of trading signals into a human-readable plain text message.
        Limits the number of signals displayed and includes a disclaimer.
        """
        message = f"""🚨 AUTO SIGNALS - SUPPLY & DEMAND ANALYSIS

🕐 Scan Time: {datetime.now().strftime('%H:%M:%S WIB')}
📊 Signals Found: {len(signals)}

"""
        # Display only the top 5 signals for brevity
        for i, signal in enumerate(signals[:5], 1):
            # Emojis for direction and confidence
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐" if signal['confidence'] >= 75 else "💡"

            # Construct the message for each signal
            message += f"""{i}. {signal['symbol']} {direction_emoji} {signal['direction']}
{confidence_emoji} Confidence: {signal['confidence']:.1f}%
💰 Entry: ${signal['entry_price']:.6f}
🛑 Stop Loss: ${signal['sl']:.6f}
🎯 TP1: ${signal['tp1']:.6f}
🎯 TP2: ${signal['tp2']:.6f}
📊 R/R Ratio: {signal['risk_reward']:.1f}:1
🔄 Trend: {signal['trend'].title()}
⚡ Structure: {signal['market_structure'].replace('_', ' ').title()}
🧠 Reason: {signal['reason']}
📈 24h Change: {signal.get('change_24h', 0):.1f}%

"""
        # Add a trading disclaimer and information about the next scan
        message += f"""⚠️ TRADING DISCLAIMER:
• Signals are based on Supply & Demand analysis.
• Always use proper risk management.
• Position sizing should align with risk level.
• Do Your Own Research (DYOR) before trading.

🎯 Auto Signals are exclusive to Admin & Lifetime users.
📡 Next scan scheduled in {self.scan_interval / 60:.0f} minutes."""

        return message

    def _get_enhanced_snd_analysis(self, symbol):
        """
        Retrieves and processes candlestick data to perform an enhanced Supply & Demand analysis.
        This function calculates support/resistance levels, analyzes volume trends, and generates
        a preliminary signal based on these factors. It includes robust error handling for data retrieval and parsing.
        (Note: This function is defined but not currently used in the main flow of analyze_enhanced_snd_signal)
        """
        try:
            # Fetch candlestick data for the 1-hour timeframe, using the last 100 candles
            candlestick_data = self.crypto_api.get_candlestick_data(symbol, '1h', 100)

            if 'error' in candlestick_data:
                return {'error': candlestick_data['error']} # Return error if API call failed

            candles = candlestick_data.get('data', [])
            # Ensure enough data is available for analysis
            if not candles or len(candles) < 20:
                return {'error': 'Insufficient candlestick data'}

            # Extract price and volume data, ensuring it's valid and numerical
            try:
                highs = [float(candle[2]) for candle in candles if len(candle) > 2]
                lows = [float(candle[3]) for candle in candles if len(candle) > 3]
                closes = [float(candle[4]) for candle in candles if len(candle) > 4]
                volumes = [float(candle[5]) for candle in candles if len(candle) > 5]

                # Validate that data extraction was successful
                if not highs or not lows or not closes or not volumes:
                    return {'error': 'Invalid candlestick data structure after extraction'}

                # Check if enough valid data points were obtained after potential filtering
                if len(highs) < 20 or len(lows) < 20 or len(closes) < 20:
                    return {'error': 'Insufficient price data points after validation'}

            except (ValueError, IndexError) as e:
                # Catch errors during data conversion or access
                return {'error': f'Price data parsing error: {str(e)}'}

            current_price = closes[-1] # Current price is the last closing price

            # Calculate key technical levels: resistance and support
            resistance_levels = self._calculate_resistance_levels(highs, closes)
            support_levels = self._calculate_support_levels(lows, closes)

            # Analyze the trend in trading volume
            volume_trend = self._analyze_volume_trend(volumes, closes)

            # Generate a preliminary SnD signal based on calculated levels and trends
            self.current_symbol = symbol # Set current symbol context for _generate_snd_signal
            signal = self._generate_snd_signal(
                current_price, resistance_levels, support_levels,
                volume_trend, highs, lows, closes
            )

            return signal

        except Exception as e:
            # Catch any unexpected errors during the enhanced analysis process
            return {'error': f'Enhanced SnD analysis error: {str(e)}'}

    def _calculate_resistance_levels(self, highs, closes):
        """
        Calculates potential resistance levels from historical high prices.
        Uses a window-based approach to identify local maxima. Includes fallbacks.
        """
        try:
            # Validate input: requires at least 10 data points
            if not highs or len(highs) < 10:
                return []

            resistance_levels = []
            # Adaptive window size for identifying local peaks, capped by data availability
            window = min(5, len(highs) // 4)

            # Iterate through data points to find local highs
            for i in range(window, len(highs) - window):
                local_highs = highs[i-window:i+window+1]
                if local_highs and highs[i] == max(local_highs):
                    resistance_levels.append(highs[i])

            # If significant resistance levels are found, sort and return top 3
            if resistance_levels:
                resistance_levels.sort(reverse=True)
                return resistance_levels[:3]
            else:
                # Fallback: use the highest recent highs if no clear local peaks are found
                recent_highs = sorted(highs[-20:], reverse=True)
                return recent_highs[:3] if recent_highs else []

        except Exception as e:
            print(f"❌ Error calculating resistance levels: {e}")
            return []

    def _calculate_support_levels(self, lows, closes):
        """
        Calculates potential support levels from historical low prices.
        Uses a window-based approach to identify local minima. Includes fallbacks.
        """
        try:
            # Validate input: requires at least 10 data points
            if not lows or len(lows) < 10:
                return []

            support_levels = []
            # Adaptive window size for identifying local troughs
            window = min(5, len(lows) // 4)

            # Iterate through data points to find local lows
            for i in range(window, len(lows) - window):
                local_lows = lows[i-window:i+window+1]
                if local_lows and lows[i] == min(local_lows):
                    support_levels.append(lows[i])

            # If significant support levels are found, sort and return top 3
            if support_levels:
                support_levels.sort() # Sort in ascending order
                return support_levels[:3]
            else:
                # Fallback: use the lowest recent lows if no clear local troughs are found
                recent_lows = sorted(lows[-20:])
                return recent_lows[:3] if recent_lows else []

        except Exception as e:
            print(f"❌ Error calculating support levels: {e}")
            return []

    def _analyze_volume_trend(self, volumes, closes):
        """
        Analyzes recent volume trends in relation to price movement.
        Returns 1 for bullish volume, -1 for bearish volume, 0 for neutral.
        """
        try:
            # Requires at least 5 volume data points for analysis
            if len(volumes) < 5: return 0

            recent_volumes = volumes[-5:] # Consider the last 5 volume bars
            avg_volume = sum(recent_volumes) / len(recent_volumes) # Calculate average volume

            # Check for significant volume increase (1.5x average)
            if recent_volumes[-1] > avg_volume * 1.5:
                if closes[-1] > closes[-2]: # Price increased with high volume
                    return 1 # Bullish volume confirmation
                elif closes[-1] < closes[-2]: # Price decreased with high volume
                    return -1 # Bearish volume confirmation

            return 0 # Volume trend is neutral

        except Exception as e:
            print(f"❌ Error analyzing volume trend: {e}")
            return 0

    def _generate_snd_signal(self, current_price, resistance_levels, support_levels, volume_trend, highs, lows, closes):
        """
        Generates a Supply & Demand signal based on price action, support/resistance levels, and volume.
        Sets entry, TP, SL, and confidence score.
        """
        # Initialize signal structure with default values
        signal = {
            'symbol': self.current_symbol, # Symbol is set by the caller
            'direction': 'LONG', # Default direction
            'entry_price': current_price,
            'tp1': current_price,
            'tp2': current_price,
            'sl': current_price,
            'confidence': 50, # Base confidence
            'risk_reward': 1.0,
            'current_price': current_price,
            'trend': 'neutral',
            'market_structure': 'sideways',
            'risk_level': 'medium',
            'timeframe': '1h',
            'scan_time': datetime.now().strftime('%H:%M:%S'),
            'reason': 'Initial analysis',
            'zone_strength': 50,
            'long_ratio': 50, # Default if futures data is unavailable
            #'change_24h': 0 # Default if not available
        }

        # Determine overall trend from recent price action
        if closes[-1] > closes[-5] and closes[-5] > closes[-10]:
            signal['trend'] = 'bullish'
        elif closes[-1] < closes[-5] and closes[-5] < closes[-10]:
            signal['trend'] = 'bearish'

        # Check if current price is near support or resistance levels
        # Using a small tolerance (e.g., 2% for support, 1% for resistance)
        is_in_support = any(current_price >= support * 0.98 and current_price <= support for support in support_levels)
        is_near_resistance = any(current_price >= resistance * 0.99 and current_price <= resistance for resistance in resistance_levels)

        # --- Signal Generation Logic ---
        if is_in_support:
            signal['direction'] = 'LONG'
            signal['reason'] = 'Price at support level'
            signal['market_structure'] = 'uptrend_bias'
            signal['confidence'] += 15 # Boost confidence for support bounce
            signal['zone_strength'] = 75 # Indicate strength of the support zone

            # Calculate TP/SL for a LONG signal
            signal['entry_price'] = current_price * 0.995 # Aim for entry slightly below current price
            signal['sl'] = support_levels[0] * 0.99 if support_levels else current_price * 0.97 # SL below support
            signal['tp1'] = signal['entry_price'] * 1.02 # 2% profit target
            signal['tp2'] = signal['entry_price'] * 1.04 # 4% profit target

            # Calculate Risk/Reward ratio
            risk = abs(signal['entry_price'] - signal['sl'])
            reward = abs(signal['tp2'] - signal['entry_price'])
            signal['risk_reward'] = round(reward / risk, 1) if risk > 0 else 2.0
            # Adjust confidence based on R/R ratio
            signal['confidence'] = min(95, signal['confidence'] + int(signal['risk_reward'] * 5))

        elif is_near_resistance:
            signal['direction'] = 'SHORT'
            signal['reason'] = 'Price near resistance level'
            signal['market_structure'] = 'downtrend_bias'
            signal['confidence'] += 15 # Boost confidence for resistance rejection
            signal['zone_strength'] = 75 # Indicate strength of the resistance zone

            # Calculate TP/SL for a SHORT signal
            signal['entry_price'] = current_price * 1.005 # Aim for entry slightly above current price
            signal['sl'] = resistance_levels[0] * 1.01 if resistance_levels else current_price * 1.03 # SL above resistance
            signal['tp1'] = signal['entry_price'] * 0.98 # 2% profit target
            signal['tp2'] = signal['entry_price'] * 0.96 # 4% profit target

            # Calculate Risk/Reward ratio
            risk = abs(signal['entry_price'] - signal['sl'])
            reward = abs(signal['tp2'] - signal['entry_price'])
            signal['risk_reward'] = round(reward / risk, 1) if risk > 0 else 2.0
            # Adjust confidence based on R/R ratio
            signal['confidence'] = min(95, signal['confidence'] + int(signal['risk_reward'] * 5))

        else: # Sideways consolidation or no clear S/R levels hit
            # Use the determined trend for signal direction
            if signal['trend'] == 'bullish':
                signal['direction'] = 'LONG'
                signal['reason'] = 'Bullish trend continuation'
                signal['market_structure'] = 'uptrend'
                signal['confidence'] += 5 # Small boost for trend continuation
            elif signal['trend'] == 'bearish':
                signal['direction'] = 'SHORT'
                signal['reason'] = 'Bearish trend continuation'
                signal['market_structure'] = 'downtrend'
                signal['confidence'] += 5 # Small boost for trend continuation
            else:
                signal['reason'] = 'Consolidation or unclear trend' # No clear direction

        # Incorporate volume trend into confidence and zone strength
        if volume_trend > 0 and signal['direction'] == 'LONG':
            signal['confidence'] += 5 # Increase confidence if volume supports the long move
            signal['zone_strength'] = min(90, signal['zone_strength'] + 5) # Strengthen zone indication
        elif volume_trend < 0 and signal['direction'] == 'SHORT':
            signal['confidence'] += 5 # Increase confidence if volume supports the short move
            signal['zone_strength'] = min(90, signal['zone_strength'] + 5) # Strengthen zone indication

        # Ensure final confidence is within acceptable bounds (30-95%)
        signal['confidence'] = max(30, min(95, signal['confidence']))

        # Adjust entry price slightly if it wasn't set by S/R logic
        if is_in_support and signal['entry_price'] == current_price:
            signal['entry_price'] = current_price * 0.995
        elif is_near_resistance and signal['entry_price'] == current_price:
            signal['entry_price'] = current_price * 1.005

        return signal

# --- Initialization Function ---
def initialize_auto_signals(bot_instance):
    """
    Initializes and returns an instance of the SnDAutoSignals class.
    Handles potential errors during initialization.
    """
    try:
        auto_signals = SnDAutoSignals(bot_instance)
        print("✅ Enhanced SnD Auto Signals system initialized successfully.")
        return auto_signals
    except Exception as e:
        print(f"❌ Failed to initialize auto signals system: {e}")
        return None

# --- Helper functions potentially for future use or refactoring ---
# Note: These functions are defined but not actively called in the current `analyze_enhanced_snd_signal` logic.
# They might be intended for future enhancements or were part of previous implementations.

async def send_auto_signals_to_users(self, signals):
    """
    Sends signals to eligible users (Admin + Lifetime premium).
    (This seems to be a duplicate or alternative implementation of `send_signals_to_eligible_users`.)
    """
    try:
        eligible_users = self.db.get_eligible_auto_signal_users()

        if not eligible_users:
            print("📊 No eligible users for auto signals.")
            return

        print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

        message = self._format_auto_signals_message(signals) # Assumes a different formatting method

        for user in eligible_users:
            user_id = None
            if isinstance(user, dict):
                user_id = user.get('telegram_id') or user.get('id')
            elif isinstance(user, (list, tuple)) and len(user) > 0:
                user_id = user[0]
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
                parse_mode='Markdown' # Uses Markdown, potentially different from plain text
            )

            print(f"✅ Sent auto signals to user {user_id}")
            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"❌ Error sending auto signals: {e}")
        import traceback
        traceback.print_exc()

async def send_signals_to_users(self, signals):
    """
    Sends signals to eligible users, including logging user activity.
    (Another potentially redundant function for sending signals.)
    """
    try:
        if not signals:
            print("📊 No signals to send")
            return

        eligible_users = self.db.get_eligible_auto_signal_users()

        if not eligible_users:
            print("👥 No eligible users for auto signals")
            return

        print(f"📤 Sending {len(signals)} signals to {len(eligible_users)} eligible users")

        message = self._format_auto_signals_message(signals) # Assumes a different formatting method

        for user in eligible_users:
            user_id = None
            user_name = 'User'
            if isinstance(user, dict):
                user_id = user.get('telegram_id')
                user_name = user.get('first_name', 'User')
            elif isinstance(user, (list, tuple)) and len(user) > 0:
                user_id = user[0]
                user_name = user[1] if len(user) > 1 else 'User'
            elif isinstance(user, int):
                user_id = user

            if not user_id:
                print(f"❌ No user_id found for user: {user}")
                continue

            await self.bot.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            print(f"✅ Sent auto signals to user {user_id} ({user_name})")

            # Log user activity for receiving signals
            self.db.log_user_activity(user_id, "auto_signal_received", f"Received {len(signals)} auto SnD signals")

    except Exception as e:
        print(f"❌ Error sending auto signals: {e}")
        import traceback
        traceback.print_exc()