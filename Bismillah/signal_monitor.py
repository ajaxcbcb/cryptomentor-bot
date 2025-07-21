
import asyncio
import logging
import time
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
        
        # Get all available symbols from Binance
        self.monitored_symbols = self._get_all_tradeable_symbols()
        
        # Fallback symbols if API fails
        self.fallback_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'AVAX', 'LINK', 'MATIC', 'DOGE',
                                'DOT', 'UNI', 'ATOM', 'FIL', 'LTC', 'BCH', 'XLM', 'VET', 'THETA', 'TRX',
                                'EOS', 'AAVE', 'COMP', 'MKR', 'SNX', 'YFI', 'SUSHI', 'BAT', 'ZRX', 'CRV',
                                'KNC', 'REN', 'LRC', 'OMG', 'ANT', 'REP', 'STORJ', 'GRT', '1INCH', 'ALPHA']
        
        # Signal thresholds
        self.signal_threshold = 7.5  # Score >= 7.5 considered strong signal
        self.last_signals = {}  # Track last signals to avoid spam
        self.signal_cooldown = 3600  # 1 hour cooldown per symbol
        
    def _get_all_tradeable_symbols(self):
        """Get all tradeable USDT pairs from Binance"""
        try:
            import requests
            
            # Get all Binance futures symbols
            response = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                data = response.json()
                symbols = []
                
                for symbol_info in data.get('symbols', []):
                    symbol = symbol_info.get('symbol', '')
                    status = symbol_info.get('status', '')
                    
                    # Only include active USDT perpetual contracts
                    if (symbol.endswith('USDT') and 
                        status == 'TRADING' and
                        symbol_info.get('contractType') == 'PERPETUAL'):
                        
                        # Extract base symbol (remove USDT)
                        base_symbol = symbol.replace('USDT', '')
                        
                        # Filter out very small/inactive coins by checking volume
                        # This will be done in the scanning process
                        symbols.append(base_symbol)
                
                print(f"📡 Found {len(symbols)} tradeable symbols from Binance")
                return symbols[:200]  # Limit to first 200 to avoid overwhelming
            else:
                print("⚠️ Failed to fetch symbols, using fallback list")
                return self.fallback_symbols
                
        except Exception as e:
            print(f"❌ Error fetching symbols: {e}, using fallback list")
            return self.fallback_symbols

    async def start_monitoring(self):
        """Start the signal monitoring system"""
        print(f"🔄 Starting Enhanced Signal Monitor for {len(self.monitored_symbols)} symbols...")
        print(f"👥 Monitoring for Admin & Lifetime Users...")
        
        # Refresh symbols list every hour
        last_symbol_refresh = 0
        
        while True:
            try:
                # Refresh symbols list every hour
                current_time = time.time()
                if current_time - last_symbol_refresh > 3600:  # 1 hour
                    print("🔄 Refreshing symbols list...")
                    self.monitored_symbols = self._get_all_tradeable_symbols()
                    last_symbol_refresh = current_time
                
                await self.scan_for_signals()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"❌ Signal monitor error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def scan_for_signals(self):
        """Scan all monitored symbols for trading signals with volume filtering"""
        print(f"🔍 Scanning {len(self.monitored_symbols)} symbols for signals...")
        
        signals_found = 0
        symbols_processed = 0
        
        # Process symbols in batches to avoid overwhelming the system
        batch_size = 20
        
        for i in range(0, len(self.monitored_symbols), batch_size):
            batch = self.monitored_symbols[i:i+batch_size]
            
            for symbol in batch:
                try:
                    symbols_processed += 1
                    
                    # Check if we recently sent signal for this symbol
                    if self.is_on_cooldown(symbol):
                        continue
                    
                    # Quick volume filter - only analyze coins with decent volume
                    price_data = self.crypto_api.get_binance_price(symbol)
                    if 'error' in price_data:
                        continue
                    
                    volume_24h = price_data.get('volume_24h', 0)
                    price = price_data.get('price', 0)
                    change_24h = abs(price_data.get('change_24h', 0))
                    
                    # Skip coins with very low volume or extremely volatile moves (likely errors)
                    if (volume_24h < 1000000 or  # Less than 1M volume
                        price <= 0 or
                        change_24h > 50):  # More than 50% change (likely error)
                        continue
                    
                    # Analyze supply & demand for qualifying symbols
                    sd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                    
                    if 'error' in sd_analysis:
                        continue
                    
                    # Check if signal meets threshold
                    sd_score = sd_analysis.get('supply_demand_score', {})
                    overall_score = sd_score.get('score', 0)
                    
                    # More sophisticated scoring that includes volume and market cap consideration
                    volume_score_multiplier = min(volume_24h / 10000000, 2.0)  # Max 2x multiplier
                    adjusted_score = overall_score * volume_score_multiplier
                    
                    if adjusted_score >= self.signal_threshold:
                        await self.send_signal_notification(symbol, sd_analysis, volume_24h, price)
                        self.last_signals[symbol] = datetime.now()
                        signals_found += 1
                        print(f"✅ Signal sent for {symbol} (Score: {overall_score:.1f}, Adj: {adjusted_score:.1f}, Vol: ${volume_24h:,.0f})")
                
                except Exception as e:
                    print(f"⚠️ Error analyzing {symbol}: {e}")
                    continue
            
            # Small delay between batches to prevent rate limiting
            await asyncio.sleep(1)
        
        print(f"📊 Scan complete: {symbols_processed} processed, {signals_found} signals found")
    
    def is_on_cooldown(self, symbol):
        """Check if symbol is on cooldown"""
        if symbol not in self.last_signals:
            return False
        
        time_diff = datetime.now() - self.last_signals[symbol]
        return time_diff.total_seconds() < self.signal_cooldown
    
    async def send_signal_notification(self, symbol, sd_analysis, volume_24h=0, current_price=0):
        """Send signal notification to admin and lifetime users"""
        try:
            # Get eligible users (admin + lifetime premium)
            eligible_users = self.get_eligible_users()
            
            # Generate enhanced signal message
            signal_message = self.format_signal_message(symbol, sd_analysis, volume_24h, current_price)
            
            # Send to eligible users
            sent_count = 0
            for user_id in eligible_users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=signal_message,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"⚠️ Failed to send signal to {user_id}: {e}")
            
            print(f"📤 Enhanced signal notification sent to {sent_count}/{len(eligible_users)} users")
            
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
    
    def format_signal_message(self, symbol, sd_analysis, volume_24h=0, current_price=0):
        """Format enhanced signal message for notification"""
        try:
            price = sd_analysis.get('current_price', current_price)
            sd_score = sd_analysis.get('supply_demand_score', {})
            entry_rec = sd_analysis.get('entry_recommendation', {})
            
            overall_score = sd_score.get('score', 0)
            signal_strength = sd_score.get('confidence', 'Medium')
            bias = sd_score.get('bias', 'Balanced')
            
            # Get entry recommendation
            primary_rec = entry_rec.get('primary_recommendation', {})
            entry_price = primary_rec.get('entry_price', price)
            stop_loss = primary_rec.get('stop_loss', price * 0.98)
            take_profit = primary_rec.get('take_profit', price * 1.02)
            direction = primary_rec.get('direction', 'HOLD')
            
            # Determine signal emoji and strength
            if overall_score >= 80:
                signal_emoji = "🚀"
                strength_text = "SANGAT KUAT"
            elif overall_score >= 70:
                signal_emoji = "🔥"
                strength_text = "KUAT"
            elif overall_score >= 60:
                signal_emoji = "⚡"
                strength_text = "BAGUS"
            else:
                signal_emoji = "🔔"
                strength_text = "MODERATE"
            
            # Format volume display
            if volume_24h >= 1000000000:  # 1B+
                volume_display = f"${volume_24h/1000000000:.1f}B"
            elif volume_24h >= 1000000:  # 1M+
                volume_display = f"${volume_24h/1000000:.1f}M"
            else:
                volume_display = f"${volume_24h:,.0f}"
            
            # Market cap estimation (rough)
            market_tier = "🟢 Large Cap" if volume_24h > 100000000 else "🟡 Mid Cap" if volume_24h > 10000000 else "🔴 Small Cap"
            
            message = f"""{signal_emoji} **SINYAL AUTO - {symbol}** ({market_tier})

💰 **Market Data:**
• Harga: ${price:,.4f}
• Volume 24h: {volume_display}
• S&D Score: {overall_score:.0f}/100 ({strength_text})
• Bias: {bias}

🎯 **Trading Setup:**
• **Direction**: {direction}
• **Entry**: ${entry_price:,.4f}
• **Stop Loss**: ${stop_loss:,.4f}
• **Take Profit**: ${take_profit:,.4f}

💡 **AI Reasoning:**
{primary_rec.get('logic', 'Supply/demand analysis menunjukkan peluang trading yang baik')}

⏰ **Time**: {datetime.now().strftime('%H:%M:%S WIB')}
🤖 **Auto Scanner**: Enhanced All-Coins Monitor

⚠️ **Risk Warning:**
- Position size maksimal 2% dari portfolio
- Selalu gunakan stop loss
- Coin kecil = volatilitas tinggi
- DYOR sebelum entry!"""

            return message
            
        except Exception as e:
            print(f"❌ Error formatting enhanced signal message: {e}")
            return f"🚨 Enhanced Signal Alert: {symbol} menunjukkan potensi kuat dari analisis supply/demand otomatis. Volume 24h: ${volume_24h:,.0f}. Check manual untuk detail lengkap."

# Singleton instance
signal_monitor = None

def get_signal_monitor(bot_token):
    """Get or create signal monitor instance"""
    global signal_monitor
    if signal_monitor is None:
        signal_monitor = SignalMonitor(bot_token)
    return signal_monitor
