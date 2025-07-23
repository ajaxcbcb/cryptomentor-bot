
import asyncio
import logging
from datetime import datetime, timedelta
from crypto_api import CryptoAPI
from ai_assistant import AIAssistant
from database import Database
import os

class AutoSignalMonitor:
    def __init__(self, bot_instance=None):
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()
        self.db = Database()
        self.bot_instance = bot_instance
        self.admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
        
        # High confidence symbols to monitor (expanded list)
        self.symbols_to_monitor = [
            'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE', 'AVAX', 'LINK', 'MATIC',
            'DOT', 'UNI', 'ATOM', 'LTC', 'BCH', 'ICP', 'NEAR', 'FTM', 'MANA', 'SAND',
            'APE', 'CRV', 'AAVE', 'COMP', 'SUSHI', 'YFI', 'BAL', 'LRC', 'ENJ', 'CHZ',
            'FLOW', 'EGLD', 'XTZ', 'ALGO', 'VET', 'ONE', 'HBAR', 'FIL', 'EOS', 'TRX',
            'THETA', 'KSM', 'WAVES', 'ZIL', 'SC', 'ONT', 'ICX', 'BAT', 'ZRX', 'REN'
        ]
        
        # Signal tracking to avoid spam
        self.last_signals_sent = {}
        self.signal_cooldown = 3600  # 1 hour cooldown per symbol
        
        # Confidence thresholds for auto-sending
        self.high_confidence_threshold = 8.5  # Score above 8.5/10
        self.risk_reward_threshold = 2.0  # R/R ratio above 2:1
        
    async def start_monitoring(self):
        """Start the automatic signal monitoring"""
        print("🚀 Starting Auto Signal Monitor for Admin & Premium Lifetime Users...")
        print(f"👑 Admin ID: {self.admin_id}")
        print(f"📊 Monitoring {len(self.symbols_to_monitor)} symbols")
        print(f"🎯 High Confidence Threshold: {self.high_confidence_threshold}/10")
        
        while True:
            try:
                await self.scan_for_high_confidence_signals()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"❌ Error in signal monitoring: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes before retry
    
    async def scan_for_high_confidence_signals(self):
        """Scan all symbols for high confidence trading opportunities"""
        print(f"🔍 Scanning for high confidence signals... {datetime.now().strftime('%H:%M:%S')}")
        
        high_confidence_signals = []
        
        for symbol in self.symbols_to_monitor:
            try:
                # Check cooldown
                if self._is_symbol_in_cooldown(symbol):
                    continue
                
                # Get comprehensive analysis
                signal_analysis = await self._analyze_symbol_for_signal(symbol)
                
                if signal_analysis and signal_analysis['confidence_score'] >= self.high_confidence_threshold:
                    high_confidence_signals.append(signal_analysis)
                    print(f"✅ High confidence signal found: {symbol} (Score: {signal_analysis['confidence_score']}/10)")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue
        
        # Send signals if found
        if high_confidence_signals:
            await self._send_high_confidence_signals(high_confidence_signals)
        else:
            print("📊 No high confidence signals detected at this time")
    
    async def _analyze_symbol_for_signal(self, symbol):
        """Analyze a symbol for high confidence trading signals"""
        try:
            # Get real-time data
            price_data = self.crypto_api.get_price(symbol, force_refresh=True)
            futures_data = self.crypto_api.get_futures_data(symbol)
            
            if not price_data or 'error' in price_data:
                return None
            
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            
            # Get technical indicators
            timeframes = ['15m', '1h', '4h', '1d']
            technical_scores = []
            
            for tf in timeframes:
                tf_data = self.crypto_api.get_timeframe_data(symbol, tf)
                if tf_data and 'error' not in tf_data:
                    score = self._calculate_technical_score(tf_data, tf)
                    technical_scores.append(score)
            
            if not technical_scores:
                return None
            
            avg_technical_score = sum(technical_scores) / len(technical_scores)
            
            # Get Long/Short ratio for sentiment
            ls_data = self.crypto_api.get_binance_long_short_ratio(symbol)
            long_ratio = ls_data.get('long_ratio', 50) if ls_data and 'error' not in ls_data else 50
            
            # Calculate market sentiment score
            sentiment_score = self._calculate_sentiment_score(change_24h, volume_24h, long_ratio)
            
            # Calculate overall confidence score
            confidence_score = (avg_technical_score * 0.6) + (sentiment_score * 0.4)
            
            # Generate trading signal if confidence is high
            if confidence_score >= self.high_confidence_threshold:
                trading_signal = self._generate_trading_signal(
                    symbol, current_price, technical_scores, sentiment_score, confidence_score
                )
                
                return {
                    'symbol': symbol,
                    'confidence_score': confidence_score,
                    'current_price': current_price,
                    'change_24h': change_24h,
                    'signal': trading_signal,
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_technical_score(self, timeframe_data, timeframe):
        """Calculate technical analysis score for a timeframe"""
        try:
            trend_analysis = timeframe_data.get('trend_analysis', {})
            support_resistance = timeframe_data.get('support_resistance', {})
            volatility = timeframe_data.get('volatility', {})
            
            score = 5.0  # Base score
            
            # Trend strength
            trend_direction = trend_analysis.get('direction', 'neutral')
            trend_strength = trend_analysis.get('strength', 'weak')
            
            if trend_direction in ['bullish', 'bearish']:
                if trend_strength == 'strong':
                    score += 2.0
                elif trend_strength == 'moderate':
                    score += 1.0
                else:
                    score += 0.5
            
            # Support/Resistance proximity
            dist_to_support = support_resistance.get('distance_to_support', 0)
            dist_to_resistance = support_resistance.get('distance_to_resistance', 0)
            
            if abs(dist_to_support) < 2:  # Near support
                score += 1.5
            elif abs(dist_to_resistance) < 2:  # Near resistance
                score += 1.0
            
            # Volatility consideration
            vol_level = volatility.get('volatility', 'low')
            if vol_level in ['moderate', 'high']:
                score += 0.5
            elif vol_level == 'very_high':
                score -= 1.0  # Too risky
            
            # Timeframe weight (longer timeframes more important)
            weights = {'15m': 0.8, '1h': 1.0, '4h': 1.2, '1d': 1.5}
            weight = weights.get(timeframe, 1.0)
            
            return min(score * weight, 10.0)
            
        except Exception as e:
            print(f"Error calculating technical score: {e}")
            return 5.0
    
    def _calculate_sentiment_score(self, change_24h, volume_24h, long_ratio):
        """Calculate market sentiment score"""
        try:
            score = 5.0
            
            # Price momentum
            if change_24h > 5:
                score += 2.0
            elif change_24h > 2:
                score += 1.0
            elif change_24h < -5:
                score += 1.5  # Oversold bounce potential
            elif change_24h < -2:
                score += 0.5
            
            # Volume analysis
            if volume_24h > 100000000:  # High volume
                score += 1.0
            elif volume_24h > 50000000:  # Medium volume
                score += 0.5
            
            # Long/Short ratio (contrarian indicator)
            if long_ratio > 75:  # Extremely bullish (potential reversal)
                score += 1.0
            elif long_ratio < 25:  # Extremely bearish (potential bounce)
                score += 1.5
            elif 40 <= long_ratio <= 60:  # Balanced
                score += 0.5
            
            return min(score, 10.0)
            
        except Exception as e:
            print(f"Error calculating sentiment score: {e}")
            return 5.0
    
    def _generate_trading_signal(self, symbol, current_price, technical_scores, sentiment_score, confidence_score):
        """Generate detailed trading signal"""
        try:
            # Determine direction based on scores
            avg_tech_score = sum(technical_scores) / len(technical_scores)
            
            if avg_tech_score > 6.5 and sentiment_score > 6.0:
                direction = "LONG"
                signal_emoji = "📈"
            elif avg_tech_score < 4.5 and sentiment_score < 4.5:
                direction = "SHORT"
                signal_emoji = "📉"
            else:
                direction = "NEUTRAL"
                signal_emoji = "⚪"
            
            # Calculate entry, stop loss, and take profit
            if direction == "LONG":
                entry_price = current_price * 0.999  # Slight discount for entry
                stop_loss = current_price * 0.985   # 1.5% stop loss
                take_profit_1 = current_price * 1.025  # 2.5% TP1
                take_profit_2 = current_price * 1.045  # 4.5% TP2
            elif direction == "SHORT":
                entry_price = current_price * 1.001  # Slight premium for short entry
                stop_loss = current_price * 1.015    # 1.5% stop loss
                take_profit_1 = current_price * 0.975  # 2.5% TP1
                take_profit_2 = current_price * 0.955  # 4.5% TP2
            else:
                return None
            
            # Calculate R/R ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit_1 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Only proceed if R/R is favorable
            if rr_ratio < self.risk_reward_threshold:
                return None
            
            return {
                'direction': direction,
                'signal_emoji': signal_emoji,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit_1': take_profit_1,
                'take_profit_2': take_profit_2,
                'rr_ratio': rr_ratio,
                'confidence_score': confidence_score,
                'technical_scores': technical_scores,
                'sentiment_score': sentiment_score
            }
            
        except Exception as e:
            print(f"Error generating trading signal: {e}")
            return None
    
    async def _send_high_confidence_signals(self, signals):
        """Send high confidence signals to admin and premium lifetime users"""
        try:
            # Get eligible users (admin + premium lifetime)
            eligible_users = self._get_eligible_users()
            
            if not eligible_users:
                print("⚠️ No eligible users found for auto signals")
                return
            
            # Sort signals by confidence score
            signals.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Take top 3 signals
            top_signals = signals[:3]
            
            # Format message
            message = self._format_auto_signal_message(top_signals)
            
            # Send to eligible users
            sent_count = 0
            for user_id in eligible_users:
                try:
                    if self.bot_instance and self.bot_instance.application:
                        await self.bot_instance.application.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                        
                        # Log the auto signal
                        self.db.log_user_activity(user_id, "auto_signal_received", f"High confidence signals sent: {len(top_signals)} signals")
                        
                        await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"❌ Failed to send signal to user {user_id}: {e}")
            
            # Update cooldown for sent signals
            for signal in top_signals:
                self.last_signals_sent[signal['symbol']] = datetime.now()
            
            print(f"✅ Auto signals sent to {sent_count}/{len(eligible_users)} eligible users")
            
        except Exception as e:
            print(f"❌ Error sending auto signals: {e}")
    
    def _get_eligible_users(self):
        """Get users eligible for auto signals (admin + premium lifetime)"""
        try:
            # Use database method for getting eligible users
            eligible_users = self.db.get_auto_signal_eligible_users()
            
            print(f"👥 Found {len(eligible_users)} eligible users for auto signals")
            return eligible_users
            
        except Exception as e:
            print(f"❌ Error getting eligible users: {e}")
            return []
    
    def _format_auto_signal_message(self, signals):
        """Format the auto signal message"""
        try:
            message = f"""🚨 **AUTO SIGNAL ALERT - HIGH CONFIDENCE**

🎯 **Elite Trading Opportunities Detected**
⏰ **Time**: {datetime.now().strftime('%H:%M:%S WIB')}
🔥 **Confidence Level**: VERY HIGH

"""
            
            for i, signal_data in enumerate(signals, 1):
                signal = signal_data['signal']
                symbol = signal_data['symbol']
                confidence = signal_data['confidence_score']
                
                message += f"""**#{i} {signal['signal_emoji']} {symbol} {signal['direction']}** (Score: {confidence:.1f}/10)
💰 **Entry**: ${signal['entry_price']:,.4f}
🛡️ **Stop Loss**: ${signal['stop_loss']:,.4f}
🎯 **TP1**: ${signal['take_profit_1']:,.4f}
🚀 **TP2**: ${signal['take_profit_2']:,.4f}
📊 **R/R**: {signal['rr_ratio']:.1f}:1

"""
            
            message += f"""⚡ **EXECUTION NOTES:**
• Use proper position sizing (1-2% risk per trade)
• Consider market conditions before entering
• Set stop losses immediately after entry
• Take partial profits at TP1, let runners go to TP2

🤖 **Auto Signal System**
📡 Real-time analysis dari {len(self.symbols_to_monitor)} symbols
🎯 Hanya mengirim sinyal dengan confidence >8.5/10
⏰ Update setiap 5 menit

**DISCLAIMER**: Trading berisiko tinggi! Gunakan money management yang tepat."""
            
            return message
            
        except Exception as e:
            print(f"❌ Error formatting message: {e}")
            return "❌ Error formatting auto signal message"
    
    def _is_symbol_in_cooldown(self, symbol):
        """Check if symbol is in cooldown period"""
        if symbol not in self.last_signals_sent:
            return False
        
        last_sent = self.last_signals_sent[symbol]
        cooldown_end = last_sent + timedelta(seconds=self.signal_cooldown)
        
        return datetime.now() < cooldown_end
    
    def get_monitor_status(self):
        """Get current monitoring status"""
        try:
            eligible_users = self._get_eligible_users()
            recent_signals = len([s for s in self.last_signals_sent.values() 
                                if (datetime.now() - s).total_seconds() < 3600])
            
            return {
                'eligible_users': len(eligible_users),
                'monitored_symbols': len(self.symbols_to_monitor),
                'recent_signals_sent': recent_signals,
                'confidence_threshold': self.high_confidence_threshold,
                'rr_threshold': self.risk_reward_threshold,
                'cooldown_minutes': self.signal_cooldown // 60
            }
            
        except Exception as e:
            print(f"Error getting monitor status: {e}")
            return {}
