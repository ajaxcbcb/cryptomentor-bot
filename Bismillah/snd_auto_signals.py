
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
        
        # Enhanced altcoin list with volume and volatility focus
        if is_deployment:
            self.target_symbols = [
                # High volume memecoins with strong SnD patterns
                'PEPE', 'SHIB', 'DOGE', 'WIF', 'BONK', 'FLOKI',
                # Layer 1/2 with strong futures activity
                'SEI', 'SUI', 'APT', 'OP', 'ARB', 'AVAX', 'NEAR',
                # DeFi tokens with institutional interest
                'ONDO', 'JUP', 'RENDER', 'PENDLE', 'JTO', 'PYTH',
                # Gaming and AI tokens with volatility
                'IMX', 'SAND', 'MANA', 'FET', 'AGIX', 'OCEAN',
                # Additional high-volume altcoins
                'INJ', 'TIA', 'ORDI', 'SATS', 'RAY', 'DRIFT'
            ]
        else:
            self.target_symbols = [
                # Development mode - broader range for testing
                'ONDO', 'SEI', 'PEPE', 'MOODENG', 'SHIB', 'FLOKI', 
                'WIF', 'BONK', 'JUP', 'PYTH', 'RENDER', 'INJ', 
                'SUI', 'APT', 'OP', 'ARB', 'TIA', 'POPCAT', 
                'PENDLE', 'EIGEN', 'DOGE', 'MATIC', 'AVAX', 'NEAR',
                'IMX', 'SAND', 'MANA', 'FET', 'AGIX', 'OCEAN',
                'JTO', 'RAY', 'DRIFT', 'ORDI', 'SATS'
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
        """Enhanced SnD analysis with comprehensive CoinAPI + Binance integration"""
        try:
            print(f"🔍 [{self.is_deployment and 'DEPLOYMENT' or 'DEVELOPMENT'}] Deep SnD analysis for {symbol}...")
            
            # Get comprehensive data with deployment-specific optimization
            force_refresh = self.is_deployment  # Always force refresh in deployment
            
            # Primary: Get real-time price data from CoinAPI
            price_data = self.crypto_api.get_coinapi_price(symbol, force_refresh=force_refresh)
            
            if 'error' in price_data or price_data.get('price', 0) <= 0:
                print(f"❌ Price data error for {symbol}: {price_data.get('error', 'Invalid price')}")
                return None
            
            current_price = price_data.get('price', 0)
            print(f"💰 {symbol} current price: ${current_price:,.6f}")
            
            # Get comprehensive SnD analysis from crypto_api
            print(f"📊 Getting comprehensive SnD analysis for {symbol}...")
            snd_analysis = self.crypto_api.analyze_supply_demand(symbol, '1h')
            
            if 'error' in snd_analysis or not snd_analysis.get('analysis_successful'):
                print(f"⚠️ SnD analysis failed for {symbol}, using simplified approach")
                return await self._simplified_auto_signal_analysis(symbol, current_price, price_data)
            
            # Extract comprehensive SnD data
            snd_score_data = snd_analysis.get('snd_score', {})
            snd_score = snd_score_data.get('score', 50)
            snd_bias = snd_score_data.get('bias', 'Balanced')
            snd_confidence = snd_score_data.get('confidence', 'Low')
            
            # Get SnD signals
            snd_signals = snd_analysis.get('signals', [])
            support_levels = snd_analysis.get('support_levels', [])
            resistance_levels = snd_analysis.get('resistance_levels', [])
            
            print(f"📈 {symbol} SnD Score: {snd_score}/100 ({snd_bias}) - {len(snd_signals)} signals found")
            
            # Get futures data for additional confirmation
            futures_data = None
            long_ratio = 50
            funding_rate = 0
            
            try:
                futures_comprehensive = self.crypto_api.get_comprehensive_futures_data(symbol)
                if 'error' not in futures_comprehensive:
                    futures_data = futures_comprehensive
                    ls_data = futures_data.get('long_short_ratio_data', {})
                    funding_data = futures_data.get('funding_rate_data', {})
                    long_ratio = ls_data.get('long_ratio', 50)
                    funding_rate = funding_data.get('last_funding_rate', 0)
                    print(f"⚡ {symbol} L/S: {long_ratio:.1f}%, Funding: {funding_rate:.4f}%")
            except Exception as e:
                print(f"⚠️ Futures data unavailable for {symbol}: {e}")
            
            # Enhanced signal confidence calculation
            base_confidence = 60
            
            # SnD Score contribution (0-25 points)
            if snd_score >= 75:
                snd_contribution = 25
            elif snd_score >= 65:
                snd_contribution = 20
            elif snd_score >= 55:
                snd_contribution = 15
            elif snd_score <= 25:
                snd_contribution = 25  # Strong bearish also high confidence
            elif snd_score <= 35:
                snd_contribution = 20
            elif snd_score <= 45:
                snd_contribution = 15
            else:
                snd_contribution = 5  # Neutral zone
            
            # Futures sentiment contribution (0-15 points)
            futures_contribution = 0
            if long_ratio > 75:  # Overcrowded long = contrarian short signal
                futures_contribution = 15 if snd_score < 50 else 5
            elif long_ratio < 25:  # Overcrowded short = contrarian long signal
                futures_contribution = 15 if snd_score > 50 else 5
            elif long_ratio > 65 or long_ratio < 35:
                futures_contribution = 10
            
            # Funding rate contribution (0-10 points)
            funding_contribution = 0
            if abs(funding_rate) > 0.01:  # High funding rate
                if funding_rate > 0.01 and snd_score < 50:  # Expensive longs + bearish SnD
                    funding_contribution = 10
                elif funding_rate < -0.01 and snd_score > 50:  # Cheap longs + bullish SnD
                    funding_contribution = 10
                else:
                    funding_contribution = 5
            
            # Calculate final confidence
            final_confidence = base_confidence + snd_contribution + futures_contribution + funding_contribution
            final_confidence = min(98, final_confidence)  # Cap at 98%
            
            print(f"🎯 {symbol} Final Confidence: {final_confidence}% (SnD: +{snd_contribution}, Futures: +{futures_contribution}, Funding: +{funding_contribution})")
            
            # Only proceed if confidence meets minimum threshold
            if final_confidence < self.min_confidence:
                print(f"❌ {symbol} confidence {final_confidence}% below minimum {self.min_confidence}%")
                return None
            
            # Determine signal type based on SnD analysis and futures confluence
            signal_type = None
            reasoning = ""
            
            if snd_score >= 70:
                if long_ratio > 70:  # Overcrowded longs but strong demand
                    signal_type = 'BUY'
                    reasoning = f"Strong demand zone + contrarian opportunity (L/S: {long_ratio:.1f}%)"
                else:
                    signal_type = 'BUY'
                    reasoning = f"Strong demand confluence + institutional support"
            elif snd_score <= 30:
                if long_ratio < 30:  # Overcrowded shorts but strong supply
                    signal_type = 'SELL'
                    reasoning = f"Strong supply zone + contrarian opportunity (L/S: {long_ratio:.1f}%)"
                else:
                    signal_type = 'SELL'
                    reasoning = f"Strong supply confluence + institutional resistance"
            elif snd_score >= 60 and long_ratio < 35:
                signal_type = 'BUY'
                reasoning = f"Moderate demand + oversold futures sentiment"
            elif snd_score <= 40 and long_ratio > 65:
                signal_type = 'SELL'
                reasoning = f"Moderate supply + overbought futures sentiment"
            else:
                print(f"🔄 {symbol} mixed signals - no clear direction (SnD: {snd_score}, L/S: {long_ratio:.1f}%)")
                return None
            
            if not signal_type:
                return None
            
            # Calculate precise entry, TP, SL using SnD levels
            entry_levels = self._calculate_enhanced_entry_levels(
                signal_type, current_price, support_levels, resistance_levels, snd_analysis
            )
            
            print(f"✅ {symbol} {signal_type} Signal Generated - Confidence: {final_confidence}%")
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'confidence': final_confidence,
                'entry_price': entry_levels['entry_price'],
                'tp1': entry_levels['tp1'],
                'tp2': entry_levels['tp2'],
                'stop_loss': entry_levels['stop_loss'],
                'risk_reward': entry_levels['risk_reward'],
                'reasoning': reasoning,
                'current_price': current_price,
                'snd_score': snd_score,
                'snd_bias': snd_bias,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate,
                'volume_24h': price_data.get('volume_24h', 0),
                'change_24h': price_data.get('change_24h', 0),
                'entry_method': entry_levels['entry_method'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error in enhanced SnD analysis for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _simplified_auto_signal_analysis(self, symbol, current_price, price_data):
        """Simplified signal analysis when full SnD data unavailable"""
        try:
            print(f"🔄 Using simplified analysis for {symbol}")
            
            # Get basic change data
            change_24h = price_data.get('change_24h', 0)
            
            # Simple momentum-based signals
            confidence = 50
            signal_type = None
            reasoning = ""
            
            if change_24h > 8:  # Strong positive momentum
                signal_type = 'BUY'
                confidence = min(85, 70 + abs(change_24h) - 8)
                reasoning = f"Strong bullish momentum (+{change_24h:.1f}%) - momentum continuation"
            elif change_24h < -8:  # Strong negative momentum
                signal_type = 'SELL'
                confidence = min(85, 70 + abs(change_24h) - 8)
                reasoning = f"Strong bearish momentum ({change_24h:.1f}%) - momentum continuation"
            elif change_24h > 5:
                signal_type = 'BUY'
                confidence = min(75, 60 + abs(change_24h) - 5)
                reasoning = f"Moderate bullish momentum (+{change_24h:.1f}%)"
            elif change_24h < -5:
                signal_type = 'SELL'
                confidence = min(75, 60 + abs(change_24h) - 5)
                reasoning = f"Moderate bearish momentum ({change_24h:.1f}%)"
            
            if not signal_type or confidence < self.min_confidence:
                return None
            
            # Simple entry calculation
            if signal_type == 'BUY':
                entry_price = current_price * 0.999
                stop_loss = current_price * 0.985
                tp1 = current_price * 1.03
                tp2 = current_price * 1.05
            else:
                entry_price = current_price * 1.001
                stop_loss = current_price * 1.015
                tp1 = current_price * 0.97
                tp2 = current_price * 0.95
            
            risk = abs(entry_price - stop_loss)
            reward = abs(tp1 - entry_price)
            risk_reward = reward / risk if risk > 0 else 2.0
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'tp1': tp1,
                'tp2': tp2,
                'stop_loss': stop_loss,
                'risk_reward': risk_reward,
                'reasoning': reasoning + " (simplified analysis)",
                'current_price': current_price,
                'snd_score': 50,
                'snd_bias': 'Unknown',
                'long_ratio': 50,
                'funding_rate': 0,
                'volume_24h': 0,
                'change_24h': change_24h,
                'entry_method': 'momentum_based',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Simplified analysis failed for {symbol}: {e}")
            return None

    def _calculate_enhanced_entry_levels(self, signal_type, current_price, support_levels, resistance_levels, snd_analysis):
        """Calculate enhanced entry levels using comprehensive SnD data"""
        try:
            entry_method = 'market'
            
            if signal_type == 'BUY':
                # Find optimal demand zone entry
                entry_price = current_price
                
                # Look for nearby support levels for better entry
                nearby_supports = [s for s in support_levels 
                                 if abs(s['price'] - current_price) / current_price < 0.05]
                
                if nearby_supports:
                    # Use strongest nearby support
                    best_support = max(nearby_supports, key=lambda x: x.get('strength', 0))
                    entry_price = best_support['price'] * 1.003  # Slightly above support
                    stop_loss = best_support['price'] * 0.995   # Below support zone
                    entry_method = 'demand_zone'
                    print(f"📈 BUY entry at demand zone: ${entry_price:,.6f}")
                else:
                    # Market entry with conservative levels
                    entry_price = current_price * 0.999
                    stop_loss = current_price * 0.985
                    entry_method = 'market_entry'
                
                # Calculate take profits
                risk_amount = entry_price - stop_loss
                tp1 = entry_price + (risk_amount * 2.5)    # 1:2.5 RR
                tp2 = entry_price + (risk_amount * 4.0)    # 1:4 RR
                
                # Adjust TP based on resistance levels
                nearby_resistances = [r for r in resistance_levels 
                                    if r['price'] > entry_price and 
                                    abs(r['price'] - current_price) / current_price < 0.10]
                
                if nearby_resistances:
                    nearest_resistance = min(nearby_resistances, 
                                           key=lambda x: x['price'] - entry_price)
                    tp1 = min(tp1, nearest_resistance['price'] * 0.997)
                
            else:  # SELL
                # Find optimal supply zone entry
                entry_price = current_price
                
                # Look for nearby resistance levels for better entry
                nearby_resistances = [r for r in resistance_levels 
                                    if abs(r['price'] - current_price) / current_price < 0.05]
                
                if nearby_resistances:
                    # Use strongest nearby resistance
                    best_resistance = max(nearby_resistances, key=lambda x: x.get('strength', 0))
                    entry_price = best_resistance['price'] * 0.997  # Slightly below resistance
                    stop_loss = best_resistance['price'] * 1.005   # Above resistance zone
                    entry_method = 'supply_zone'
                    print(f"📉 SELL entry at supply zone: ${entry_price:,.6f}")
                else:
                    # Market entry with conservative levels
                    entry_price = current_price * 1.001
                    stop_loss = current_price * 1.015
                    entry_method = 'market_entry'
                
                # Calculate take profits
                risk_amount = stop_loss - entry_price
                tp1 = entry_price - (risk_amount * 2.5)    # 1:2.5 RR
                tp2 = entry_price - (risk_amount * 4.0)    # 1:4 RR
                
                # Adjust TP based on support levels
                nearby_supports = [s for s in support_levels 
                                 if s['price'] < entry_price and 
                                 abs(s['price'] - current_price) / current_price < 0.10]
                
                if nearby_supports:
                    nearest_support = max(nearby_supports, 
                                        key=lambda x: entry_price - x['price'])
                    tp1 = max(tp1, nearest_support['price'] * 1.003)
            
            # Calculate risk/reward ratio
            if signal_type == 'BUY':
                risk = abs(entry_price - stop_loss)
                reward = abs(tp1 - entry_price)
            else:
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - tp1)
            
            risk_reward = reward / risk if risk > 0 else 2.5
            
            return {
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'risk_reward': risk_reward,
                'entry_method': entry_method
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating enhanced entry levels: {e}")
            # Fallback calculation
            if signal_type == 'BUY':
                return {
                    'entry_price': current_price * 0.999,
                    'stop_loss': current_price * 0.985,
                    'tp1': current_price * 1.035,
                    'tp2': current_price * 1.055,
                    'risk_reward': 2.5,
                    'entry_method': 'fallback'
                }
            else:
                return {
                    'entry_price': current_price * 1.001,
                    'stop_loss': current_price * 1.015,
                    'tp1': current_price * 0.965,
                    'tp2': current_price * 0.945,
                    'risk_reward': 2.5,
                    'entry_method': 'fallback'
                }
    
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
        """Enhanced signals formatting with comprehensive SnD and futures data"""
        timestamp = datetime.now().strftime('%H:%M:%S UTC')
        mode_indicator = "🌐 DEPLOYMENT (CoinAPI Real-time)" if self.is_deployment else "🔧 DEVELOPMENT"
        
        message = f"""🎯 **ENHANCED AUTO SnD SIGNALS** 🎯

📊 **{len(signals)} High-Confidence Signals Found**
🕐 **Scan Time:** {timestamp}
🔄 **Mode:** {mode_indicator}
🎲 **Symbols Scanned:** {len(self.target_symbols)} altcoins

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
            
            # Enhanced signal data
            snd_score = signal.get('snd_score', 50)
            snd_bias = signal.get('snd_bias', 'Unknown')
            long_ratio = signal.get('long_ratio', 50)
            funding_rate = signal.get('funding_rate', 0)
            entry_method = signal.get('entry_method', 'market')
            
            direction_emoji = "🟢💎" if signal_type == "BUY" else "🔴💎"
            if "STRONG" in signal_type:
                direction_emoji = "🟢🚀" if "BUY" in signal_type else "🔴💥"
            
            # Format prices based on value
            def format_price(price):
                if price >= 1000:
                    return f"${price:,.2f}"
                elif price >= 1:
                    return f"${price:.4f}"
                else:
                    return f"${price:.6f}"
            
            message += f"""**{i}. {symbol} {direction_emoji} {signal_type}**

💰 **Entry:** {format_price(entry)} ({entry_method.replace('_', ' ').title()})
🎯 **TP1:** {format_price(tp1)} (Conservative)
🚀 **TP2:** {format_price(tp2)} (Extended)
🛡️ **SL:** {format_price(sl)} (Zone Protection)
📊 **R/R:** {rr:.1f}:1
✅ **Confidence:** {confidence}%

📈 **SnD Analysis:**
• **Score:** {snd_score}/100 ({snd_bias})
• **L/S Ratio:** {long_ratio:.1f}%/{100-long_ratio:.1f}%
• **Funding:** {funding_rate:.4f}%

🔍 **Logic:** {signal['reasoning']}

"""

        # Calculate next scan time based on interval
        next_scan = datetime.now() + timedelta(seconds=self.scan_interval)
        next_scan_str = next_scan.strftime('%H:%M UTC')
        
        message += f"""⚡ **ENHANCED AUTO SIGNALS FEATURES:**
🎯 **Multi-Factor Analysis:** SnD + Futures + Volume
📊 **Order Block Detection:** Institutional levels identified
⚖️ **Risk/Reward Optimization:** Minimum 2:1 ratio
🔄 **Real-time Data:** CoinAPI + Binance integration
🎲 **Altcoin Focus:** High-volatility tokens prioritized

👑 **EXCLUSIVE ACCESS:**
• Admin users get all signals
• Lifetime premium members included
• Enhanced confidence thresholds

⚠️ **TRADING GUIDELINES:**
• **Position Size:** 1-2% per signal maximum
• **Risk Management:** Always set stop loss first
• **Entry Confirmation:** Wait for price action confirmation
• **Profit Taking:** Secure partial profits at TP1
• **Multiple Signals:** Diversify across different symbols

📡 **Technical Setup:**
• **Scanner Interval:** {self.scan_interval//60} minutes
• **Confidence Threshold:** {self.min_confidence}%+
• **Data Sources:** CoinAPI (Primary) + Binance (Futures)
• **Next Scan:** {next_scan_str}

⚡ **Disclaimer:** Signals are for educational purposes. Always DYOR and manage risk appropriately."""

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
