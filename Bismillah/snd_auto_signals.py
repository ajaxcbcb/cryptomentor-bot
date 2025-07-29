import asyncio
import time
import random
from datetime import datetime
from crypto_api import CryptoAPI
from database import Database

class SnDAutoSignals:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.crypto_api = CryptoAPI()
        self.db = Database()

        # Top market cap coins only (Top 25 by market cap excluding stablecoins)
        self.target_symbols = [
            # Top 10 
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SHIB', 'DOT',
            # Top 11-20
            'LINK', 'TRX', 'MATIC', 'TON', 'ICP', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT',
            # Top 21-25
            'LEO', 'CRO', 'ATOM', 'FIL', 'ETC'
        ]

        self.scan_interval = 7200  # 2 hours
        self.min_confidence = 65   # Higher confidence for auto signals
        self.is_running = False
        self.last_scan_time = 0

        print(f"🎯 Auto SnD Signals initialized with {len(self.target_symbols)} altcoins")
        print(f"⏰ Scan interval: {self.scan_interval // 60} minutes")
        print(f"📈 Min confidence: {self.min_confidence}%")

    async def start_auto_scanner(self):
        """Start the auto SnD scanner"""
        self.is_running = True
        print("🚀 Auto SnD signals scanner started")

        while self.is_running:
            try:
                await self.scan_and_send_signals()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                print(f"❌ Error in auto scanner: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def stop_auto_scanner(self):
        """Stop the auto SnD scanner"""
        self.is_running = False
        print("🛑 Auto SnD signals scanner stopped")

    async def scan_and_send_signals(self):
        """Scan for SnD signals and send to eligible users"""
        try:
            self.last_scan_time = int(time.time())
            print(f"🔄 Starting auto SnD scan at {datetime.now().strftime('%H:%M:%S')}")

            # Get eligible users (admin + lifetime)
            eligible_users = self.db.get_eligible_auto_signal_users()

            if not eligible_users:
                print("👥 No eligible users for auto signals")
                return

            print(f"👥 Found {len(eligible_users)} eligible users (Admin + Lifetime)")

            # Randomize target symbols for variety
            scan_symbols = random.sample(self.target_symbols, min(12, len(self.target_symbols)))
            print(f"🎯 Scanning {len(scan_symbols)} symbols: {scan_symbols}")

            signals = []
            processed = 0

            for symbol in scan_symbols:
                try:
                    processed += 1
                    print(f"🔄 Processing {symbol} ({processed}/{len(scan_symbols)})")

                    # Get enhanced SnD signal
                    signal = await self._get_enhanced_signal(symbol)

                    if signal and signal.get('confidence', 0) >= self.min_confidence:
                        signals.append(signal)
                        print(f"✅ Signal generated for {symbol} (confidence: {signal.get('confidence')}%)")

                    # Rate limiting
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"❌ Error processing {symbol}: {e}")
                    continue

            if signals:
                # Send signals to eligible users
                await self._send_signals_to_users(signals, eligible_users)
                print(f"📤 Sent {len(signals)} signals to {len(eligible_users)} users")
            else:
                print("⚠️ No qualifying signals found in this scan")

        except Exception as e:
            print(f"💥 Critical error in scan_and_send_signals: {e}")
            import traceback
            traceback.print_exc()

    async def _get_enhanced_signal(self, symbol):
        """Get enhanced SnD signal for a symbol"""
        try:
            # Get price from CoinAPI
            price_data = self.crypto_api.get_coinapi_price(symbol, force_refresh=True)

            # Get futures data
            futures_data = self.crypto_api.get_comprehensive_futures_data(symbol)
            if 'error' in futures_data:
                return None

            # Check volume filter (only liquid coins)
            price_data_futures = futures_data.get('price_data', {})
            if 'error' not in price_data_futures:
                volume_24h = price_data_futures.get('volume_24h', 0)
                if volume_24h < 500000:  # Minimum $500k volume
                    print(f"💧 {symbol} volume too low: ${volume_24h:,.0f}")
                    return None

            # Analyze SnD
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol, '1h')
            if 'error' in snd_analysis:
                return None

            # Generate signal using AI assistant
            signal = self.bot.ai._generate_enhanced_snd_signal(symbol, price_data, futures_data, snd_analysis)

            return signal

        except Exception as e:
            print(f"Error getting signal for {symbol}: {e}")
            return None

    async def _send_signals_to_users(self, signals, eligible_users):
        """Send auto signals to eligible users"""
        try:
            # Format the signals message
            message = self._format_auto_signals_message(signals)

            # Send to each eligible user
            sent_count = 0
            for user_id in eligible_users:
                try:
                    await self.bot.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    await asyncio.sleep(1)  # Rate limiting

                except Exception as e:
                    print(f"❌ Failed to send to user {user_id}: {e}")

            print(f"✅ Successfully sent auto signals to {sent_count}/{len(eligible_users)} users")

        except Exception as e:
            print(f"Error sending signals to users: {e}")

    def _format_auto_signals_message(self, signals):
        """Format auto signals message"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            message = f"""🚨 **AUTO SnD SIGNALS ALERT**

🎯 **Auto-Generated**: {current_time}
📊 **Signals Found**: {len(signals)} high-confidence setups
🔍 **Scan**: {len(self.target_symbols)} altcoins analyzed
⚡ **Min Confidence**: {self.min_confidence}%+

"""

            for i, signal in enumerate(signals[:4], 1):  # Max 4 auto signals
                symbol = signal['symbol']
                direction = signal['direction']
                entry = signal['entry_price']
                tp1 = signal['tp1']
                tp2 = signal['tp2']
                sl = signal['sl']
                confidence = signal['confidence']
                rr = signal['risk_reward']

                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                confidence_emoji = "🔥" if confidence >= 80 else "⚡"

                # Smart price formatting
                if entry < 1:
                    entry_fmt = f"${entry:.6f}"
                    tp1_fmt = f"${tp1:.6f}"
                    tp2_fmt = f"${tp2:.6f}"
                    sl_fmt = f"${sl:.6f}"
                elif entry < 100:
                    entry_fmt = f"${entry:.4f}"
                    tp1_fmt = f"${tp1:.4f}"
                    tp2_fmt = f"${tp2:.4f}"
                    sl_fmt = f"${sl:.4f}"
                else:
                    entry_fmt = f"${entry:,.2f}"
                    tp1_fmt = f"${tp1:,.2f}"
                    tp2_fmt = f"${tp2:,.2f}"
                    sl_fmt = f"${sl:,.2f}"

                message += f"""**{i}. {symbol} {direction}** {direction_emoji} {confidence_emoji}
Entry: {entry_fmt} | TP1: {tp1_fmt} | TP2: {tp2_fmt}
SL: {sl_fmt} | R/R: {rr:.1f}:1 | Conf: {confidence:.0f}%

"""

            message += f"""⚠️ **Auto Signal Rules:**
• Verify entry zones before position
• Use proper position sizing (1-3%)
• Set stop loss immediately
• Monitor price action for confirmation

🎯 **Exclusive**: Admin & Lifetime users only
📡 **Next Scan**: {self.scan_interval // 60} minutes

⚠️ Not financial advice - DYOR"""

            return message

        except Exception as e:
            return f"❌ Error formatting auto signals: {str(e)}"

def initialize_auto_signals(bot_instance):
    """Initialize auto signals system"""
    try:
        return SnDAutoSignals(bot_instance)
    except Exception as e:
        print(f"❌ Failed to initialize auto signals: {e}")
        return None

class SnDAutoSignals:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.crypto_api = CryptoAPI()
        self.db = Database()
        self.is_running = False
        self.scan_interval = 1800  # 30 minutes

        # Top market cap coins only (Top 25 by market cap excluding stablecoins)
        self.target_symbols = [
            # Top 10 
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SHIB', 'DOT',
            # Top 11-20
            'LINK', 'TRX', 'MATIC', 'TON', 'ICP', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT',
            # Top 21-25
            'LEO', 'CRO', 'ATOM', 'FIL', 'ETC'
        ]

        self.min_confidence = 70  # Minimum confidence level
        self.last_scan_time = 0

    async def start_auto_scanner(self):
        """Start automatic SnD signal scanner"""
        if self.is_running:
            print("⚠️ Auto scanner already running")
            return

        self.is_running = True
        print(f"🚀 Starting enhanced SnD auto scanner for {len(self.target_symbols)} altcoins...")
        print(f"📊 Scan interval: {self.scan_interval} seconds ({self.scan_interval/60:.1f} minutes)")

        while self.is_running:
            try:
                await self.scan_and_send_signals()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                print(f"❌ Error in auto scanner: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def stop_auto_scanner(self):
        """Stop automatic scanner"""
        self.is_running = False
        print("🛑 Enhanced SnD auto scanner stopped")

    async def scan_and_send_signals(self):
        """Scan symbols and send high-confidence signals"""
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
        """Analyze enhanced SnD for a single symbol"""
        try:
            # Get comprehensive data
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol, '1h')
            price_data = self.crypto_api.get_coinapi_price(symbol, force_refresh=True)
            futures_data = self.crypto_api.get_binance_long_short_ratio(symbol)

            if 'error' in snd_analysis or 'error' in price_data:
                return None

            current_price = price_data.get('price', 0)
            signals = snd_analysis.get('signals', [])
            confidence_score = snd_analysis.get('confidence_score', 50)

            if not signals or confidence_score < self.min_confidence:
                return None

            # Get the best signal
            best_signal = max(signals, key=lambda x: x.get('confidence', 0))

            # Enhanced confidence calculation
            enhanced_confidence = self._calculate_enhanced_confidence(
                best_signal, snd_analysis, futures_data, current_price
            )

            if enhanced_confidence < self.min_confidence:
                return None

            # Get market structure
            market_structure = snd_analysis.get('market_structure', {})

            # Calculate position sizing recommendation
            risk_level = self._calculate_risk_level(enhanced_confidence, market_structure)

            return {
                'symbol': symbol,
                'direction': best_signal['direction'],
                'entry_price': best_signal['entry_price'],
                'stop_loss': best_signal['stop_loss'],
                'take_profit_1': best_signal['take_profit_1'],
                'take_profit_2': best_signal['take_profit_2'],
                'confidence': enhanced_confidence,
                'risk_reward_ratio': best_signal['risk_reward_ratio'],
                'current_price': current_price,
                'trend': snd_analysis.get('trend', 'neutral'),
                'market_structure': market_structure['pattern'],
                'risk_level': risk_level,
                'timeframe': '1h',
                'scan_time': datetime.now().strftime('%H:%M:%S'),
                'reason': best_signal['reason'],
                'zone_strength': best_signal.get('zone_strength', 50)
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

            # Format signals message
            signals_message = self._format_signals_message(signals)

            success_count = 0
            for user_data in eligible_users:
                user_id = user_data.get('user_id')
                if not user_id:
                    continue

                try:
                    await self.bot.application.bot.send_message(
                        chat_id=user_id,
                        text=signals_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting

                except Exception as e:
                    print(f"❌ Failed to send signal to user {user_id}: {e}")
                    continue

            print(f"✅ Auto signals sent to {success_count}/{len(eligible_users)} users")

            # Log the broadcast
            self.db.log_auto_signals_broadcast(len(signals), success_count, len(eligible_users))

        except Exception as e:
            print(f"❌ Error sending auto signals: {e}")

    def _format_signals_message(self, signals):
        """Format signals into a readable message"""
        message = f"""🚨 **AUTO SIGNALS - SUPPLY & DEMAND ANALYSIS**

🕐 **Scan Time**: {datetime.now().strftime('%H:%M:%S WIB')}
📊 **Signals Found**: {len(signals)}

"""

        for i, signal in enumerate(signals[:5], 1):  # Limit to top 5 signals
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐" if signal['confidence'] >= 75 else "💡"

            message += f"""**{i}. {signal['symbol']} {direction_emoji}**
{confidence_emoji} **Confidence**: {signal['confidence']:.1f}%
📈 **Direction**: {signal['direction']}
💰 **Entry**: ${signal['entry_price']:.4f}
🛑 **Stop Loss**: ${signal['stop_loss']:.4f}
🎯 **TP1**: ${signal['take_profit_1']:.4f}
🎯 **TP2**: ${signal['take_profit_2']:.4f}
📊 **R/R**: {signal['risk_reward_ratio']:.1f}:1
🔄 **Trend**: {signal['trend'].title()}
⚡ **Structure**: {signal['market_structure'].replace('_', ' ').title()}

"""

        message += f"""⚠️ **TRADING DISCLAIMER:**
• Signals berbasis Supply & Demand analysis
• Gunakan proper risk management
• Position sizing sesuai risk level
• DYOR sebelum trading

🎯 **Auto Signals hanya untuk Admin & Lifetime users**
📡 **Next scan in {self.scan_interval/60:.0f} minutes**"""

        return message

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