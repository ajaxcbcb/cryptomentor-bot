
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
        
        # Check deployment mode for scan interval
        import os
        deployment_checks = [
            os.getenv('REPLIT_DEPLOYMENT') == '1',
            os.getenv('REPL_DEPLOYMENT') == '1',
            os.path.exists('/tmp/repl_deployment_flag'),
            bool(os.getenv('REPL_SLUG'))
        ]
        is_deployment = any(deployment_checks)
        
        # More frequent scanning in deployment
        self.scan_interval = 1800 if is_deployment else 3600  # 30 min deployment, 1 hour dev
        self.is_deployment = is_deployment
        
        # Prioritized altcoins for deployment
        if is_deployment:
            self.target_symbols = [
                'PEPE', 'SHIB', 'DOGE', 'WIF', 'BONK',  # High volume memecoins
                'SEI', 'SUI', 'APT', 'OP', 'ARB',      # Layer 1/2 with futures
                'ONDO', 'JUP', 'RENDER', 'PENDLE'      # DeFi tokens
            ]
        else:
            self.target_symbols = [
                'ONDO', 'SEI', 'PEPE', 'MOODENG', 'SHIB', 'FLOKI', 
                'WIF', 'BONK', 'JUP', 'PYTH', 'RENDER', 'INJ', 
                'SUI', 'APT', 'OP', 'ARB', 'TIA', 'POPCAT', 
                'PENDLE', 'EIGEN', 'DOGE', 'MATIC'
            ]
        
        self.min_confidence = 80 if is_deployment else 75  # Higher confidence for deployment
        
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
        """Scan symbols and send high-confidence signals with deployment optimization"""
        mode_text = "DEPLOYMENT" if self.is_deployment else "DEVELOPMENT"
        print(f"🔍 [{mode_text}] Scanning {len(self.target_symbols)} altcoins for SnD signals...")
        
        high_confidence_signals = []
        processed_count = 0
        
        for symbol in self.target_symbols:
            try:
                print(f"📈 [{mode_text}] Analyzing {symbol}...")
                signal = await self.analyze_snd_signal(symbol)
                processed_count += 1
                
                if signal and signal['confidence'] >= self.min_confidence:
                    high_confidence_signals.append(signal)
                    print(f"✅ [{mode_text}] High confidence signal: {symbol} - {signal['confidence']}%")
                else:
                    if signal:
                        print(f"⚠️ [{mode_text}] Low confidence: {symbol} - {signal.get('confidence', 0)}%")
                    
                # Adaptive rate limiting based on deployment
                sleep_time = 1 if self.is_deployment else 2
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                print(f"❌ [{mode_text}] Error analyzing {symbol}: {e}")
                continue
                
        print(f"📊 [{mode_text}] Scan complete: {processed_count}/{len(self.target_symbols)} symbols processed")
        
        if high_confidence_signals:
            print(f"🎯 [{mode_text}] Found {len(high_confidence_signals)} high-confidence signals")
            await self.send_signals_to_eligible_users(high_confidence_signals)
        else:
            print(f"📊 [{mode_text}] No high-confidence signals found in this scan")
            
    async def analyze_snd_signal(self, symbol):
        """Analyze SnD for a single symbol with deployment optimization and AI integration"""
        try:
            # Get comprehensive data with deployment-specific optimization
            force_refresh = self.is_deployment  # Always force refresh in deployment
            
            # Primary: Get real-time price data
            price_data = self.crypto_api.get_coinapi_price(symbol, force_refresh=force_refresh)
            
            # Secondary: Futures data for additional confirmation
            try:
                futures_data = self.crypto_api.get_binance_futures_price(symbol)
            except Exception as e:
                print(f"⚠️ Futures data unavailable for {symbol}: {e}")
                futures_data = None
            
            # Enhanced SnD analysis with AI assistant integration
            try:
                # Use AI assistant's SnD analysis method if available
                if hasattr(self.bot, 'ai') and hasattr(self.bot.ai, 'analyze_snd_for_auto_signals'):
                    print(f"🤖 Using AI assistant SnD analysis for {symbol}")
                    ai_snd_result = self.bot.ai.analyze_snd_for_auto_signals(symbol, self.crypto_api)
                    
                    if ai_snd_result and 'error' not in ai_snd_result:
                        print(f"✅ AI SnD analysis successful for {symbol}")
                        # Convert AI result to expected format
                        snd_analysis = {
                            'signals': [ai_snd_result['signal']] if 'signal' in ai_snd_result else [],
                            'support_levels': ai_snd_result.get('support_levels', []),
                            'resistance_levels': ai_snd_result.get('resistance_levels', [])
                        }
                    else:
                        print(f"⚠️ AI SnD analysis failed for {symbol}, using fallback")
                        snd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                else:
                    print(f"⚠️ AI assistant not available for {symbol}, using direct API")
                    snd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                    
            except Exception as e:
                print(f"⚠️ S&D analysis failed for {symbol}: {e}")
                # Use price-based S&D analysis as fallback
                snd_analysis = self._fallback_snd_analysis(symbol, price_data)
            
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
                # Find nearest support for S&D entry refinement
                nearest_support = self._find_nearest_level(support_levels, current_price, 'below')
                nearest_resistance = self._find_nearest_level(resistance_levels, current_price, 'above')
                
                if nearest_support and nearest_resistance:
                    # Precise S&D entry at demand zone
                    entry_price = nearest_support['price'] * 1.002  # Tight entry above support
                    stop_loss = nearest_support['price'] * 0.998   # SL below support zone
                    
                    # Calculate 1:1 RR based on risk
                    risk_amount = entry_price - stop_loss
                    tp1 = entry_price + risk_amount                 # 1:1 RR
                    tp2 = entry_price + (risk_amount * 1.2)         # 1:1.2 RR bonus
                    
                else:
                    # Default S&D-style calculation with 1:1 RR
                    entry_price = current_price * 0.998
                    risk_percentage = 0.015  # 1.5% risk
                    stop_loss = entry_price * (1 - risk_percentage)
                    tp1 = entry_price * (1 + risk_percentage)       # 1:1 RR
                    tp2 = entry_price * (1 + risk_percentage * 1.3) # 1:1.3 RR
                    
            elif signal_type == 'SELL':
                # Find nearest resistance for S&D entry refinement
                nearest_resistance = self._find_nearest_level(resistance_levels, current_price, 'above')
                nearest_support = self._find_nearest_level(support_levels, current_price, 'below')
                
                if nearest_resistance and nearest_support:
                    # Precise S&D entry at supply zone
                    entry_price = nearest_resistance['price'] * 0.998  # Tight entry below resistance
                    stop_loss = nearest_resistance['price'] * 1.002   # SL above supply zone
                    
                    # Calculate 1:1 RR based on risk
                    risk_amount = stop_loss - entry_price
                    tp1 = entry_price - risk_amount                   # 1:1 RR
                    tp2 = entry_price - (risk_amount * 1.2)           # 1:1.2 RR bonus
                    
                else:
                    # Default S&D-style calculation with 1:1 RR
                    entry_price = current_price * 1.002
                    risk_percentage = 0.015  # 1.5% risk
                    stop_loss = entry_price * (1 + risk_percentage)
                    tp1 = entry_price * (1 - risk_percentage)         # 1:1 RR
                    tp2 = entry_price * (1 - risk_percentage * 1.3)   # 1:1.3 RR
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
    
    def _fallback_snd_analysis(self, symbol, price_data):
        """Fallback SnD analysis based on price action"""
        if not price_data or 'error' in price_data:
            return {'error': 'No price data available'}
            
        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        volume = price_data.get('volume_24h', 0)
        
        # Simple SnD logic based on price action
        signals = []
        
        # Volume-based signal strength
        volume_strength = min(100, max(0, (volume / 1000000) * 10))  # Scale volume
        
        # Price momentum analysis
        if change_24h > 5 and volume_strength > 50:
            signals.append({
                'type': 'BUY',
                'confidence': min(95, 70 + volume_strength/10),
                'reason': f'Strong bullish momentum (+{change_24h:.1f}%) with high volume'
            })
        elif change_24h < -5 and volume_strength > 50:
            signals.append({
                'type': 'SELL', 
                'confidence': min(95, 70 + volume_strength/10),
                'reason': f'Strong bearish momentum ({change_24h:.1f}%) with high volume'
            })
        elif abs(change_24h) > 3:
            confidence = 60 + min(20, volume_strength/5)
            signal_type = 'BUY' if change_24h > 0 else 'SELL'
            signals.append({
                'type': signal_type,
                'confidence': confidence,
                'reason': f'Moderate momentum ({change_24h:+.1f}%) - price action signal'
            })
            
        return {
            'signals': signals,
            'support_levels': [{'price': current_price * 0.95}],
            'resistance_levels': [{'price': current_price * 1.05}]
        }
            
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
        """Format signals into telegram message with deployment info"""
        timestamp = datetime.now().strftime('%H:%M:%S UTC')
        mode_indicator = "🌐 DEPLOYMENT" if self.is_deployment else "🔧 DEVELOPMENT"
        
        message = f"""🎯 **AUTO SnD SIGNALS ALERT** 🎯

📊 **{len(signals)} High-Confidence Signals Found**
🕐 **Scan Time:** {timestamp}
🔄 **Mode:** {mode_indicator}

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

💰 **Entry:** ${entry:.6f} (S&D Zone)
🎯 **TP1:** ${tp1:.6f} (1:1 RR)
🚀 **TP2:** ${tp2:.6f} (Bonus)
🛡️ **SL:** ${sl:.6f} (Zone Protection)
📊 **R/R:** {rr:.1f}:1
✅ **Confidence:** {confidence}%
🔍 **Method:** Supply/Demand Analysis

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
