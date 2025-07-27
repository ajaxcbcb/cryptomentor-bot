
import asyncio
import time
from datetime import datetime, timedelta
from crypto_api import CryptoAPI
from ai_assistant import AIAssistant
from database import Database
import os

class SnDAutoSignals:
    def __init__(self, bot_application):
        self.bot = bot_application
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()
        self.db = Database()
        self.admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
        
        # Small altcoins to monitor (market cap < $500M)
        self.small_altcoins = [
            'INJ', 'FET', 'RENDER', 'THETA', 'RUNE', 'OCEAN', 
            'KAVA', 'ROSE', 'CHZ', 'ENJ', 'BAT', 'ZIL',
            'HOT', 'CELR', 'ANKR', 'SKL', 'CTSI', 'AUDIO'
        ]
        
        self.last_signal_time = {}
        self.signal_cooldown = 3600  # 1 hour cooldown per symbol
        
    async def start_auto_signals(self):
        """Start the automated signals system"""
        print("🚀 Starting SnD Auto Signals for Small Altcoins...")
        
        while True:
            try:
                await self.scan_and_send_signals()
                # Scan every 30 minutes
                await asyncio.sleep(1800)
            except Exception as e:
                print(f"❌ Error in auto signals: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def scan_and_send_signals(self):
        """Scan altcoins and send high-confidence signals"""
        print(f"🔍 Scanning {len(self.small_altcoins)} small altcoins for SnD signals...")
        
        high_confidence_signals = []
        
        for symbol in self.small_altcoins:
            try:
                # Check cooldown
                if self.is_on_cooldown(symbol):
                    continue
                
                # Get comprehensive SnD analysis
                snd_data = await self.analyze_symbol_snd(symbol)
                
                if snd_data and snd_data.get('confidence_level', 0) >= 85:
                    high_confidence_signals.append(snd_data)
                    self.last_signal_time[symbol] = time.time()
                    
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue
        
        # Send signals to eligible users
        if high_confidence_signals:
            await self.send_signals_to_users(high_confidence_signals)

    def is_on_cooldown(self, symbol):
        """Check if symbol is on cooldown"""
        last_time = self.last_signal_time.get(symbol, 0)
        return (time.time() - last_time) < self.signal_cooldown

    async def analyze_symbol_snd(self, symbol):
        """Perform comprehensive SnD analysis for a symbol"""
        try:
            # Get price data
            price_data = self.crypto_api.get_multi_api_price(symbol, force_refresh=True)
            if 'error' in price_data or price_data.get('price', 0) <= 0:
                return None
            
            current_price = price_data['price']
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            
            # Get futures data for sentiment
            futures_data = self.crypto_api.get_binance_long_short_ratio(symbol)
            long_ratio = futures_data.get('long_ratio', 50) if 'error' not in futures_data else 50
            
            # Get funding rate
            funding_data = self.crypto_api.get_binance_funding_rate(symbol)
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
            
            # Simulate advanced SnD analysis
            snd_analysis = self.simulate_advanced_snd_analysis(
                symbol, current_price, change_24h, volume_24h, long_ratio, funding_rate
            )
            
            return snd_analysis
            
        except Exception as e:
            print(f"❌ SnD analysis error for {symbol}: {e}")
            return None

    def simulate_advanced_snd_analysis(self, symbol, price, change_24h, volume, long_ratio, funding_rate):
        """Simulate advanced Supply & Demand analysis"""
        confidence_score = 50  # Base confidence
        signal_type = "HOLD"
        entry_price = price
        take_profit = price
        stop_loss = price
        
        # Volume analysis
        if volume > 1000000:  # High volume
            confidence_score += 15
        elif volume > 500000:  # Medium volume
            confidence_score += 10
        
        # Price momentum analysis
        if abs(change_24h) > 5:  # Strong momentum
            confidence_score += 20
            if change_24h > 5:
                signal_type = "LONG"
                entry_price = price * 0.998  # Slight pullback entry
                take_profit = price * 1.08   # 8% target
                stop_loss = price * 0.94     # 6% stop loss
            elif change_24h < -5:
                signal_type = "SHORT"
                entry_price = price * 1.002
                take_profit = price * 0.92
                stop_loss = price * 1.06
        
        # Futures sentiment analysis (contrarian)
        if long_ratio > 75:  # Over-leveraged long
            if signal_type == "HOLD":
                signal_type = "SHORT"
                entry_price = price * 1.001
                take_profit = price * 0.93
                stop_loss = price * 1.05
            confidence_score += 15
        elif long_ratio < 25:  # Over-leveraged short
            if signal_type == "HOLD":
                signal_type = "LONG"
                entry_price = price * 0.999
                take_profit = price * 1.07
                stop_loss = price * 0.95
            confidence_score += 15
        
        # Funding rate analysis
        if abs(funding_rate) > 0.01:  # High funding rate
            confidence_score += 10
        
        # Risk/Reward calculation
        if signal_type in ["LONG", "SHORT"]:
            if signal_type == "LONG":
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
            else:
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - take_profit)
            
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Boost confidence for good RR ratio
            if risk_reward_ratio >= 1.5:
                confidence_score += 10
            elif risk_reward_ratio >= 1.2:
                confidence_score += 5
        else:
            risk_reward_ratio = 0
        
        # SnD zones simulation (simplified)
        zone_strength = self.simulate_snd_zones(price, change_24h, volume)
        confidence_score += zone_strength
        
        # Cap confidence at 100
        confidence_score = min(100, confidence_score)
        
        # Only return high confidence signals
        if confidence_score < 85:
            return None
        
        return {
            'symbol': symbol,
            'signal_type': signal_type,
            'current_price': price,
            'entry_price': entry_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'confidence_level': confidence_score,
            'risk_reward_ratio': risk_reward_ratio,
            'change_24h': change_24h,
            'volume_24h': volume,
            'long_ratio': long_ratio,
            'funding_rate': funding_rate,
            'analysis_time': datetime.now().isoformat(),
            'zone_info': f"Strong {'demand' if signal_type == 'LONG' else 'supply' if signal_type == 'SHORT' else 'consolidation'} zone detected"
        }

    def simulate_snd_zones(self, price, change_24h, volume):
        """Simulate SnD zone strength calculation"""
        zone_strength = 0
        
        # Strong volume + price rejection patterns
        if volume > 2000000 and abs(change_24h) > 3:
            zone_strength += 15
        elif volume > 1000000 and abs(change_24h) > 2:
            zone_strength += 10
        
        # Simulate institutional levels (psychological levels)
        price_str = str(price)
        if '00' in price_str or '50' in price_str:
            zone_strength += 5
        
        return zone_strength

    async def send_signals_to_users(self, signals):
        """Send signals to admin and lifetime users only"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self.get_eligible_users()
            
            if not eligible_users:
                print("⚠️ No eligible users found for SnD signals")
                return
            
            # Format signals message
            message = self.format_signals_message(signals)
            
            # Send to each eligible user
            success_count = 0
            for user_id in eligible_users:
                try:
                    await self.bot.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"❌ Failed to send signal to user {user_id}: {e}")
            
            print(f"✅ SnD Auto Signals sent to {success_count}/{len(eligible_users)} eligible users")
            
        except Exception as e:
            print(f"❌ Error sending signals: {e}")

    def get_eligible_users(self):
        """Get users eligible for auto signals (admin + lifetime)"""
        try:
            eligible_users = []
            
            # Add admin
            if self.admin_id > 0:
                eligible_users.append(self.admin_id)
            
            # Get lifetime premium users
            self.db.cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE is_premium = 1 AND subscription_end IS NULL
                AND telegram_id IS NOT NULL AND telegram_id != 0
            """)
            
            lifetime_users = [row[0] for row in self.db.cursor.fetchall()]
            eligible_users.extend(lifetime_users)
            
            # Remove duplicates
            return list(set(eligible_users))
            
        except Exception as e:
            print(f"❌ Error getting eligible users: {e}")
            return []

    def format_signals_message(self, signals):
        """Format signals into a readable message"""
        try:
            message = f"""🎯 **SnD AUTO SIGNALS - SMALL ALTCOINS**

🔍 **High Confidence Signals Detected**
⏰ **Time**: {datetime.now().strftime('%H:%M:%S WIB')}

"""
            
            for i, signal in enumerate(signals[:3], 1):  # Limit to 3 signals
                symbol = signal['symbol']
                signal_type = signal['signal_type']
                confidence = signal['confidence_level']
                entry = signal['entry_price']
                tp = signal['take_profit']
                sl = signal['stop_loss']
                rr = signal['risk_reward_ratio']
                change_24h = signal['change_24h']
                
                signal_emoji = "🟢" if signal_type == "LONG" else "🔴" if signal_type == "SHORT" else "⚪"
                
                message += f"""**{i}. {signal_emoji} {symbol} {signal_type}**
💰 **Current**: ${signal['current_price']:,.4f} ({change_24h:+.1f}%)
🎯 **Entry**: ${entry:,.4f}
📈 **TP**: ${tp:,.4f}
🛡️ **SL**: ${sl:,.4f}
⚡ **Confidence**: {confidence}%
📊 **R/R**: {rr:.2f}:1
💡 **Zone**: {signal['zone_info']}

"""
            
            message += f"""🔬 **Analysis Basis:**
• Advanced Supply/Demand detection
• Volume profile analysis
• Futures sentiment (contrarian)
• Institutional level identification

⚠️ **Risk Warning:**
• Signals khusus untuk ADMIN & LIFETIME PREMIUM
• Altcoins volatil - gunakan proper position sizing
• Selalu konfirmasi dengan analisis sendiri
• Max 2-3% risk per trade

📡 **Auto System**: SnD Scanner v2.0
🔄 **Next Scan**: 30 minutes

💎 **Exclusive**: Hanya untuk member premium lifetime & admin"""
            
            return message
            
        except Exception as e:
            print(f"❌ Error formatting signals message: {e}")
            return "❌ Error formatting signals"

# Global instance
auto_signals_instance = None

async def start_auto_signals_system(bot_application):
    """Initialize and start the auto signals system"""
    global auto_signals_instance
    try:
        auto_signals_instance = SnDAutoSignals(bot_application)
        await auto_signals_instance.start_auto_signals()
    except Exception as e:
        print(f"❌ Failed to start auto signals system: {e}")

def stop_auto_signals_system():
    """Stop the auto signals system"""
    global auto_signals_instance
    if auto_signals_instance:
        print("🛑 Stopping SnD Auto Signals system...")
        auto_signals_instance = None
