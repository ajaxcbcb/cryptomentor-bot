
import asyncio
import logging
from datetime import datetime, timedelta
from database import Database
from crypto_api import CryptoAPI
from ai_assistant import AIAssistant
from telegram import Bot
import os

class SignalMonitor:
    def __init__(self, bot_token):
        self.bot = Bot(token=bot_token)
        self.db = Database()
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()
        self.admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
        
        # Symbols to monitor
        self.monitored_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'AVAX', 'LINK', 'MATIC', 'DOGE']
        
        # Signal thresholds
        self.signal_threshold = 7.5  # Score >= 7.5 considered strong signal
        self.last_signals = {}  # Track last signals to avoid spam
        self.signal_cooldown = 3600  # 1 hour cooldown per symbol
        
    async def start_monitoring(self):
        """Start the signal monitoring system"""
        print("🔄 Starting Signal Monitor for Admin & Lifetime Users...")
        
        while True:
            try:
                await self.scan_for_signals()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"❌ Signal monitor error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def scan_for_signals(self):
        """Scan all monitored symbols for trading signals"""
        print(f"🔍 Scanning {len(self.monitored_symbols)} symbols for signals...")
        
        for symbol in self.monitored_symbols:
            try:
                # Check if we recently sent signal for this symbol
                if self.is_on_cooldown(symbol):
                    continue
                
                # Analyze supply & demand
                sd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                
                if 'error' in sd_analysis:
                    continue
                
                # Check if signal meets threshold
                sd_score = sd_analysis.get('supply_demand_score', {})
                overall_score = sd_score.get('overall_score', 0)
                
                if overall_score >= self.signal_threshold:
                    await self.send_signal_notification(symbol, sd_analysis)
                    self.last_signals[symbol] = datetime.now()
                    print(f"✅ Signal sent for {symbol} (Score: {overall_score:.1f})")
                
            except Exception as e:
                print(f"⚠️ Error analyzing {symbol}: {e}")
                continue
    
    def is_on_cooldown(self, symbol):
        """Check if symbol is on cooldown"""
        if symbol not in self.last_signals:
            return False
        
        time_diff = datetime.now() - self.last_signals[symbol]
        return time_diff.total_seconds() < self.signal_cooldown
    
    async def send_signal_notification(self, symbol, sd_analysis):
        """Send signal notification to admin and lifetime users"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self.get_eligible_users()
            
            # Generate signal message
            signal_message = self.format_signal_message(symbol, sd_analysis)
            
            # Send to eligible users
            for user_id in eligible_users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=signal_message,
                        parse_mode='Markdown'
                    )
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"⚠️ Failed to send signal to {user_id}: {e}")
            
            print(f"📤 Signal notification sent to {len(eligible_users)} users")
            
        except Exception as e:
            print(f"❌ Error sending signal notification: {e}")
    
    def get_eligible_users(self):
        """Get list of admin and lifetime premium users"""
        try:
            eligible_users = []
            
            # Add admin
            if self.admin_id > 0:
                eligible_users.append(self.admin_id)
            
            # Get all lifetime premium users
            self.db.cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE is_premium = 1 AND subscription_end IS NULL 
                AND telegram_id IS NOT NULL AND telegram_id != 0
            """)
            
            lifetime_users = self.db.cursor.fetchall()
            for user in lifetime_users:
                if user[0] not in eligible_users:
                    eligible_users.append(user[0])
            
            print(f"👥 Found {len(eligible_users)} eligible users for signals")
            return eligible_users
            
        except Exception as e:
            print(f"❌ Error getting eligible users: {e}")
            return []
    
    def format_signal_message(self, symbol, sd_analysis):
        """Format signal message for notification"""
        try:
            current_price = sd_analysis.get('current_price', 0)
            sd_score = sd_analysis.get('supply_demand_score', {})
            entry_rec = sd_analysis.get('entry_recommendation', {})
            
            overall_score = sd_score.get('overall_score', 0)
            signal_strength = sd_score.get('signal_strength', 'Unknown')
            
            entry_price = entry_rec.get('entry_price', 0)
            entry_reason = entry_rec.get('reason', 'No specific reason')
            stop_loss = entry_rec.get('stop_loss', 0)
            target_1 = entry_rec.get('targets', [0])[0] if entry_rec.get('targets') else 0
            
            # Determine signal emoji
            if overall_score >= 9:
                signal_emoji = "🚀"
                strength_text = "SANGAT KUAT"
            elif overall_score >= 8:
                signal_emoji = "🔥"
                strength_text = "KUAT"
            else:
                signal_emoji = "⚡"
                strength_text = "BAGUS"
            
            message = f"""{signal_emoji} **SINYAL OTOMATIS - {symbol}**

💰 **Harga Saat Ini**: ${current_price:,.2f}
📊 **Skor S&D**: {overall_score:.1f}/10 ({strength_text})

🎯 **Rekomendasi Entry:**
• **Entry Price**: ${entry_price:,.2f}
• **Stop Loss**: ${stop_loss:,.2f}
• **Target 1**: ${target_1:,.2f}

💡 **Alasan Entry:**
{entry_reason}

⏰ **Waktu**: {datetime.now().strftime('%H:%M:%S WIB')}
🤖 **Auto Signal**: Supply & Demand Analysis

⚠️ **Risk Management**:
- Gunakan position sizing yang tepat
- Patuhi stop loss yang diberikan
- DYOR sebelum trading"""

            return message
            
        except Exception as e:
            print(f"❌ Error formatting signal message: {e}")
            return f"🚨 Signal Alert: {symbol} shows strong potential. Check manually for details."

# Singleton instance
signal_monitor = None

def get_signal_monitor(bot_token):
    """Get or create signal monitor instance"""
    global signal_monitor
    if signal_monitor is None:
        signal_monitor = SignalMonitor(bot_token)
    return signal_monitor
