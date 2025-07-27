
import asyncio
import logging
from datetime import datetime, timedelta
from crypto_api import CryptoAPI
from database import Database

class SnDAutoSignals:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.crypto_api = CryptoAPI()
        self.db = Database()
        self.is_running = False
        self.scan_interval = 3600  # 1 hour
        
        # Altcoins kecil dengan volume tinggi
        self.target_symbols = [
            'ONDO', 'SEI', 'PEPE', 'MOODENG', 'SHIB', 'FLOKI', 
            'WIF', 'BONK', 'JUP', 'PYTH', 'RENDER', 'INJ', 
            'SUI', 'APT', 'OP', 'ARB', 'TIA', 'POPCAT', 
            'PENDLE', 'EIGEN', 'DOGE', 'MATIC'
        ]
        
        self.min_confidence = 75  # Minimum confidence level
        
    async def start_auto_scanner(self):
        """Start automatic SnD signal scanner"""
        if self.is_running:
            print("⚠️ Auto scanner already running")
            return
            
        self.is_running = True
        print(f"🚀 Starting SnD auto scanner for {len(self.target_symbols)} altcoins...")
        
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
        print("🛑 SnD auto scanner stopped")
        
    async def scan_and_send_signals(self):
        """Scan symbols and send high-confidence signals"""
        print(f"🔍 Scanning {len(self.target_symbols)} altcoins for SnD signals...")
        
        high_confidence_signals = []
        
        for symbol in self.target_symbols:
            try:
                signal = await self.analyze_snd_signal(symbol)
                if signal and signal['confidence'] >= self.min_confidence:
                    high_confidence_signals.append(signal)
                    print(f"✅ High confidence signal found: {symbol} - {signal['confidence']}%")
                    
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue
                
        if high_confidence_signals:
            await self.send_signals_to_eligible_users(high_confidence_signals)
        else:
            print("📊 No high-confidence signals found in this scan")
            
    async def analyze_snd_signal(self, symbol):
        """Analyze SnD for a single symbol"""
        try:
            # Get comprehensive data
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol)
            price_data = self.crypto_api.get_binance_price(symbol)
            futures_data = self.crypto_api.get_binance_futures_price(symbol)
            
            if 'error' in snd_analysis or 'error' in price_data:
                return None
                
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None
                
            # Extract SnD analysis
            support_levels = snd_analysis.get('support_levels', [])
            resistance_levels = snd_analysis.get('resistance_levels', [])
            signals = snd_analysis.get('signals', [])
            
            if not signals:
                return None
                
            # Find highest confidence signal
            best_signal = max(signals, key=lambda x: x.get('confidence', 0))
            confidence = best_signal.get('confidence', 0)
            
            if confidence < self.min_confidence:
                return None
                
            signal_type = best_signal.get('type', '').upper()
            
            # Calculate entry, TP, SL based on SnD levels
            entry_price = current_price
            
            if signal_type == 'BUY':
                # Find nearest support for entry refinement
                nearest_support = self._find_nearest_level(support_levels, current_price, 'below')
                nearest_resistance = self._find_nearest_level(resistance_levels, current_price, 'above')
                
                if nearest_support and nearest_resistance:
                    # Entry di support level atau current price
                    entry_price = max(nearest_support['price'], current_price * 0.995)
                    
                    # TP di resistance level
                    tp1 = nearest_resistance['price'] * 0.98  # Conservative TP
                    tp2 = nearest_resistance['price'] * 1.02  # Aggressive TP
                    
                    # SL below support
                    stop_loss = nearest_support['price'] * 0.97
                    
                else:
                    # Default calculation
                    tp1 = current_price * 1.03
                    tp2 = current_price * 1.06
                    stop_loss = current_price * 0.97
                    
            elif signal_type == 'SELL':
                # Find nearest resistance for entry refinement
                nearest_resistance = self._find_nearest_level(resistance_levels, current_price, 'above')
                nearest_support = self._find_nearest_level(support_levels, current_price, 'below')
                
                if nearest_resistance and nearest_support:
                    # Entry di resistance level atau current price
                    entry_price = min(nearest_resistance['price'], current_price * 1.005)
                    
                    # TP di support level
                    tp1 = nearest_support['price'] * 1.02  # Conservative TP
                    tp2 = nearest_support['price'] * 0.98  # Aggressive TP
                    
                    # SL above resistance
                    stop_loss = nearest_resistance['price'] * 1.03
                    
                else:
                    # Default calculation
                    tp1 = current_price * 0.97
                    tp2 = current_price * 0.94
                    stop_loss = current_price * 1.03
            else:
                return None
                
            # Calculate risk/reward ratio
            if signal_type == 'BUY':
                risk = abs(entry_price - stop_loss)
                reward = abs(tp1 - entry_price)
            else:
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - tp1)
                
            risk_reward = reward / risk if risk > 0 else 0
            
            # Only return signals with good R/R ratio
            if risk_reward < 1.5:
                return None
                
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'tp1': tp1,
                'tp2': tp2,
                'stop_loss': stop_loss,
                'risk_reward': risk_reward,
                'reasoning': best_signal.get('reason', ''),
                'current_price': current_price,
                'volume_24h': price_data.get('volume_24h', 0),
                'change_24h': price_data.get('change_24h', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in SnD analysis for {symbol}: {e}")
            return None
            
    def _find_nearest_level(self, levels, current_price, direction):
        """Find nearest support/resistance level"""
        if not levels:
            return None
            
        if direction == 'above':
            candidates = [level for level in levels if level['price'] > current_price]
            if candidates:
                return min(candidates, key=lambda x: abs(x['price'] - current_price))
        else:  # below
            candidates = [level for level in levels if level['price'] < current_price]
            if candidates:
                return max(candidates, key=lambda x: x['price'])
                
        return None
        
    async def send_signals_to_eligible_users(self, signals):
        """Send signals to admin and lifetime users only"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self._get_eligible_users()
            
            if not eligible_users:
                print("📊 No eligible users found for auto signals")
                return
                
            signals_text = self._format_signals_message(signals)
            
            success_count = 0
            for user_data in eligible_users:
                try:
                    await self.bot.application.bot.send_message(
                        chat_id=user_data['telegram_id'],
                        text=signals_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    success_count += 1
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    print(f"Failed to send to user {user_data['telegram_id']}: {e}")
                    continue
                    
            print(f"✅ Auto signals sent to {success_count}/{len(eligible_users)} eligible users")
            
            # Log the broadcast
            self.db.log_user_activity(0, "auto_snd_signals_sent", 
                                    f"Sent {len(signals)} signals to {success_count} users")
            
        except Exception as e:
            print(f"Error sending auto signals: {e}")
            
    def _get_eligible_users(self):
        """Get users eligible for auto signals (admin + lifetime)"""
        try:
            admin_id = int(self.bot.admin_id) if self.bot.admin_id else 0
            
            # Get all premium users (including lifetime)
            self.db.cursor.execute("""
                SELECT telegram_id, first_name, username, is_premium, subscription_end
                FROM users 
                WHERE (
                    telegram_id = ? OR 
                    (is_premium = 1 AND (subscription_end IS NULL OR subscription_end = ''))
                ) 
                AND telegram_id IS NOT NULL 
                AND telegram_id != 0
            """, (admin_id,))
            
            rows = self.db.cursor.fetchall()
            
            eligible_users = []
            for row in rows:
                telegram_id, first_name, username, is_premium, subscription_end = row
                
                # Include admin
                if telegram_id == admin_id:
                    eligible_users.append({
                        'telegram_id': telegram_id,
                        'first_name': first_name,
                        'username': username,
                        'type': 'admin'
                    })
                # Include lifetime premium (subscription_end is NULL or empty)
                elif is_premium and (subscription_end is None or subscription_end == ''):
                    eligible_users.append({
                        'telegram_id': telegram_id,
                        'first_name': first_name,
                        'username': username,
                        'type': 'lifetime'
                    })
                    
            print(f"📊 Found {len(eligible_users)} eligible users for auto signals")
            return eligible_users
            
        except Exception as e:
            print(f"Error getting eligible users: {e}")
            return []
            
    def _format_signals_message(self, signals):
        """Format signals into telegram message"""
        timestamp = datetime.now().strftime('%H:%M:%S UTC')
        
        message = f"""🎯 **AUTO SnD SIGNALS ALERT** 🎯

📊 **{len(signals)} High-Confidence Signals Found**
🕐 **Scan Time:** {timestamp}

"""

        for i, signal in enumerate(signals, 1):
            symbol = signal['symbol']
            signal_type = signal['signal_type']
            confidence = signal['confidence']
            entry = signal['entry_price']
            tp1 = signal['tp1']
            tp2 = signal['tp2']
            sl = signal['stop_loss']
            rr = signal['risk_reward']
            
            direction_emoji = "🟢" if signal_type == "BUY" else "🔴"
            
            message += f"""**{i}. {symbol} {direction_emoji} {signal_type}**

💰 **Entry:** ${entry:.6f}
🎯 **TP1:** ${tp1:.6f}
🚀 **TP2:** ${tp2:.6f}
🛡️ **SL:** ${sl:.6f}
📊 **R/R:** {rr:.1f}:1
✅ **Confidence:** {confidence}%

"""

        message += f"""⚡ **EXCLUSIVE AUTO SIGNALS**
🎯 Supply & Demand Analysis
📈 Only High-Confidence Setups
👑 Admin & Lifetime Users Only

⚠️ **Risk Warning:**
• Use proper position sizing
• Confirm entry with price action
• Set stop loss immediately
• Take partial profits at TP1

📡 **Auto Scanner:** Every 1 Hour
🔄 **Next Scan:** {(datetime.now() + timedelta(hours=1)).strftime('%H:%M UTC')}"""

        return message

# Global instance
snd_auto_signals = None

def initialize_auto_signals(bot_instance):
    """Initialize auto signals system"""
    global snd_auto_signals
    snd_auto_signals = SnDAutoSignals(bot_instance)
    return snd_auto_signals

def get_auto_signals_instance():
    """Get auto signals instance"""
    return snd_auto_signals
