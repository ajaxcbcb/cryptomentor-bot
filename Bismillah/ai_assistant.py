
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import random

class AIAssistant:
    """AI Assistant for crypto analysis with CoinAPI integration"""
    
    def __init__(self):
        self.openai_available = False
        self.setup_openai()
    
    def setup_openai(self):
        """Setup OpenAI client if available"""
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
                self.openai_available = True
                print("✅ OpenAI API initialized")
            else:
                print("⚠️ OPENAI_API_KEY not found in environment")
        except ImportError:
            print("⚠️ OpenAI library not available")
    
    def get_comprehensive_analysis(self, symbol: str, indicators: Dict = None, market_data: Dict = None, language: str = 'id', crypto_api=None) -> str:
        """Generate comprehensive crypto analysis"""
        try:
            # Get real-time price data
            price_data = {}
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            
            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if 'error' not in price_data else 0
            
            # Price formatting
            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"
            
            # Volume formatting
            if volume_24h > 1000000000:
                volume_format = f"${volume_24h/1000000000:.2f}B"
            elif volume_24h > 1000000:
                volume_format = f"${volume_24h/1000000:.1f}M"
            else:
                volume_format = f"${volume_24h:,.0f}"
            
            # Get Supply & Demand zones
            snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)
            
            # Generate signals
            signal_data = self._generate_trading_signals(symbol, current_price, change_24h, volume_24h)
            
            # Market sentiment
            sentiment = self._analyze_market_sentiment(change_24h, volume_24h)
            
            change_emoji = "📈" if change_24h >= 0 else "📉"
            sentiment_emoji = "🟢" if sentiment['score'] > 60 else "🟡" if sentiment['score'] > 40 else "🔴"
            
            # Format analysis
            analysis = f"""📊 **ANALISIS KOMPREHENSIF {symbol} (CoinAPI + SnD)**

💰 **Data Harga Real-time:**
• **Harga Saat Ini**: {price_format}
• **Perubahan 24j**: {change_24h:+.2f}% {change_emoji}
• **Volume 24j**: {volume_format}

🎯 **ENHANCED SUPPLY & DEMAND ZONES**:
• 🔴 Supply Zone 1: ${snd_zones['supply_1_low']:,.6f} - ${snd_zones['supply_1_high']:,.6f}
• 🔴 Supply Zone 2: ${snd_zones['supply_2_low']:,.6f} - ${snd_zones['supply_2_high']:,.6f}
• 🟢 Demand Zone 1: ${snd_zones['demand_1_low']:,.6f} - ${snd_zones['demand_1_high']:,.6f}
• 🟢 Demand Zone 2: ${snd_zones['demand_2_low']:,.6f} - ${snd_zones['demand_2_high']:,.6f}

📈 **SINYAL TRADING:**
• **Arah**: {signal_data.get('direction', 'NEUTRAL')} {signal_data.get('emoji', '⚖️')}
• **Kekuatan**: {signal_data.get('strength', 'Medium')}
• **Entry Point**: ${signal_data.get('entry_price', current_price):,.6f}
• **Take Profit**: ${signal_data.get('take_profit', current_price * 1.05):,.6f}
• **Stop Loss**: ${signal_data.get('stop_loss', current_price * 0.95):,.6f}

🧠 **ANALISIS SENTIMEN** {sentiment_emoji}:
• **Skor Sentimen**: {sentiment['score']}/100
• **Status**: {sentiment['status']}
• **Momentum**: {sentiment['momentum']}

📊 **TECHNICAL ANALYSIS:**
• **RSI Estimasi**: {self._calculate_rsi_estimate(change_24h)}
• **Trend**: {signal_data.get('trend', 'Sideways')}
• **Support**: ${current_price * 0.95:,.6f}
• **Resistance**: ${current_price * 1.05:,.6f}

💡 **REKOMENDASI TRADING:**
{self._generate_trading_recommendations(signal_data, sentiment, snd_zones, current_price)}

⚠️ **RISK MANAGEMENT:**
• Position size maksimal: 2-3% dari portfolio
• Selalu gunakan stop loss
• Take profit bertahap di level SnD zones
• Monitor volume untuk konfirmasi breakout

📡 **Data Source**: CoinAPI Real-time + Internal SnD Algorithm
🕐 **Analisis**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            return analysis
            
        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            return f"❌ Terjadi kesalahan dalam analisis {symbol}. Error: {str(e)[:100]}..."
    
    def _get_enhanced_supply_demand_zones(self, symbol: str, current_price: float, crypto_api=None) -> Dict:
        """Calculate enhanced Supply & Demand zones"""
        try:
            # Get basic SnD zones (simplified calculation)
            basic_snd = self._calculate_basic_snd_zones(current_price)
            
            # Get indicators for enhancement
            indicators = {}
            if crypto_api:
                # Try to get more data for better SnD calculation
                pass
            
            # Calculate ATR estimate for zone width
            atr = current_price * 0.02  # 2% ATR estimate
            
            # Get EMAs for zone validation
            ema_50 = indicators.get('ema_50', current_price)
            ema_200 = indicators.get('ema_200', current_price)

            # Calculate supply zones as ranges (resistance areas) - Smaller ranges
            supply_1_center = max(basic_snd.get('supply_1', current_price * 1.015), ema_50 * 1.01)
            supply_1_low = supply_1_center - (atr * 0.2)
            supply_1_high = supply_1_center + (atr * 0.2)
            
            supply_2_center = supply_1_center + (atr * 1.2)
            supply_2_low = supply_2_center - (atr * 0.2)
            supply_2_high = supply_2_center + (atr * 0.2)

            # Calculate demand zones as ranges (support areas) - Smaller ranges
            demand_1_center = min(basic_snd.get('demand_1', current_price * 0.985), ema_50 * 0.99)
            demand_1_low = demand_1_center - (atr * 0.2)
            demand_1_high = demand_1_center + (atr * 0.2)
            
            demand_2_center = demand_1_center - (atr * 1.2)
            demand_2_low = demand_2_center - (atr * 0.2)
            demand_2_high = demand_2_center + (atr * 0.2)

            # Determine current position relative to zones
            if current_price > supply_1_low:
                position = "Above Supply Zone 1"
                strength = "Strong"
            elif current_price < demand_1_high:
                position = "Below Demand Zone 1"
                strength = "Weak"
            else:
                position = "Between SnD Zones"
                strength = "Neutral"

            return {
                'supply_1_low': supply_1_low,
                'supply_1_high': supply_1_high,
                'supply_2_low': supply_2_low,
                'supply_2_high': supply_2_high,
                'demand_1_low': demand_1_low,
                'demand_1_high': demand_1_high,
                'demand_2_low': demand_2_low,
                'demand_2_high': demand_2_high,
                'position': position,
                'strength': strength
            }

        except Exception as e:
            # Fallback to basic calculation with smaller ranges
            atr_fallback = current_price * 0.02
            return {
                'supply_1_low': current_price * 1.010,
                'supply_1_high': current_price * 1.015,
                'supply_2_low': current_price * 1.020,
                'supply_2_high': current_price * 1.025,
                'demand_1_low': current_price * 0.985,
                'demand_1_high': current_price * 0.990,
                'demand_2_low': current_price * 0.975,
                'demand_2_high': current_price * 0.980,
                'position': 'Enhanced SnD analysis unavailable',
                'strength': 'Unknown',
                'error': str(e)
            }
    
    def _calculate_basic_snd_zones(self, current_price: float) -> Dict:
        """Calculate basic Supply & Demand zones"""
        return {
            'supply_1': current_price * 1.02,
            'supply_2': current_price * 1.05,
            'demand_1': current_price * 0.98,
            'demand_2': current_price * 0.95
        }
    
    def _generate_trading_signals(self, symbol: str, price: float, change_24h: float, volume: float) -> Dict:
        """Generate trading signals based on price action"""
        # Simple signal generation logic
        if change_24h > 5:
            direction = "LONG"
            emoji = "🟢"
            strength = "Strong"
            trend = "Strong Uptrend"
        elif change_24h < -5:
            direction = "SHORT"
            emoji = "🔴"
            strength = "Strong"
            trend = "Strong Downtrend"
        elif change_24h > 2:
            direction = "LONG"
            emoji = "🟢"
            strength = "Medium"
            trend = "Uptrend"
        elif change_24h < -2:
            direction = "SHORT"
            emoji = "🔴"
            strength = "Medium"
            trend = "Downtrend"
        else:
            direction = "NEUTRAL"
            emoji = "⚖️"
            strength = "Weak"
            trend = "Sideways"
        
        # Calculate entry, TP, SL
        if direction == "LONG":
            entry_price = price * 0.999  # Slight below current
            take_profit = price * 1.03   # 3% profit
            stop_loss = price * 0.98     # 2% loss
        elif direction == "SHORT":
            entry_price = price * 1.001  # Slight above current
            take_profit = price * 0.97   # 3% profit
            stop_loss = price * 1.02     # 2% loss
        else:
            entry_price = price
            take_profit = price * 1.02
            stop_loss = price * 0.98
        
        return {
            'direction': direction,
            'emoji': emoji,
            'strength': strength,
            'trend': trend,
            'entry_price': entry_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'strategy': 'Momentum Trading',
            'time_horizon': '4-24 hours'
        }
    
    def _analyze_market_sentiment(self, change_24h: float, volume: float) -> Dict:
        """Analyze market sentiment"""
        # Base sentiment score on price change
        base_score = 50 + (change_24h * 2)  # Convert % change to sentiment score
        
        # Adjust for volume (high volume = more confident sentiment)
        if volume > 100000000:  # High volume
            confidence_multiplier = 1.2
        elif volume > 10000000:  # Medium volume
            confidence_multiplier = 1.0
        else:  # Low volume
            confidence_multiplier = 0.8
        
        final_score = max(0, min(100, base_score * confidence_multiplier))
        
        if final_score > 70:
            status = "Very Bullish"
            momentum = "Strong Buy"
        elif final_score > 60:
            status = "Bullish"
            momentum = "Buy"
        elif final_score > 40:
            status = "Neutral"
            momentum = "Hold"
        elif final_score > 30:
            status = "Bearish"
            momentum = "Sell"
        else:
            status = "Very Bearish"
            momentum = "Strong Sell"
        
        return {
            'score': int(final_score),
            'status': status,
            'momentum': momentum
        }
    
    def _calculate_rsi_estimate(self, change_24h: float) -> str:
        """Estimate RSI based on 24h change"""
        # Simple RSI estimation
        if change_24h > 10:
            return "75+ (Overbought)"
        elif change_24h > 5:
            return "65-75 (Strong)"
        elif change_24h > 0:
            return "50-65 (Bullish)"
        elif change_24h > -5:
            return "35-50 (Bearish)"
        else:
            return "25- (Oversold)"
    
    def _generate_trading_recommendations(self, signal_data: Dict, sentiment: Dict, snd_zones: Dict, current_price: float) -> str:
        """Generate trading recommendations"""
        direction = signal_data.get('direction', 'NEUTRAL')
        strength = signal_data.get('strength', 'Medium')
        sentiment_score = sentiment.get('score', 50)
        
        recommendations = []
        
        if direction == "LONG" and sentiment_score > 60:
            recommendations.append("• ✅ Consider LONG position dengan konfirmasi SnD")
            recommendations.append("• 🎯 Entry dekat Demand Zone untuk risk optimal")
            recommendations.append("• 📈 Target profit di Supply Zone 1")
        elif direction == "SHORT" and sentiment_score < 40:
            recommendations.append("• ❌ Consider SHORT position dengan konfirmasi SnD")
            recommendations.append("• 🎯 Entry dekat Supply Zone untuk risk optimal")
            recommendations.append("• 📉 Target profit di Demand Zone 1")
        else:
            recommendations.append("• ⏳ Wait for clearer signals di SnD zones")
            recommendations.append("• 👀 Monitor price action di key levels")
            recommendations.append("• 📊 Tunggu konfirmasi volume breakout")
        
        recommendations.append("• 🛡️ Always use stop loss sesuai SnD zones")
        recommendations.append("• 💰 Position sizing max 2-3% portfolio")
        
        return "\n".join(recommendations)
    
    async def get_futures_analysis(self, symbol: str, timeframe: str, language: str = 'id', crypto_api=None) -> str:
        """Get futures analysis with SnD for specific timeframe"""
        try:
            # Get current price
            price_data = {}
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            
            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
            
            # Get SnD zones
            snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)
            
            # Generate futures-specific signals
            futures_signals = self._generate_futures_signals(symbol, current_price, timeframe, snd_zones)
            
            # Format timeframe display
            tf_display = {
                '15m': '15 Menit', '30m': '30 Menit', '1h': '1 Jam',
                '4h': '4 Jam', '1d': '1 Hari', '1w': '1 Minggu'
            }.get(timeframe, timeframe)
            
            # Price formatting
            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"
            
            analysis = f"""🎯 **PROFESSIONAL FUTURES ANALYSIS - {symbol} ({tf_display})**

📊 **Current Market Data:**
• **Price**: {price_format}
• **24h Change**: {change_24h:+.2f}%
• **Analysis Time**: {datetime.now().strftime('%H:%M:%S WIB')}

🎯 **SUPPLY & DEMAND ZONES ({tf_display}):**
• 🔴 **Supply Zone 1**: ${snd_zones['supply_1_low']:,.6f} \\- ${snd_zones['supply_1_high']:,.6f}
• 🔴 **Supply Zone 2**: ${snd_zones['supply_2_low']:,.6f} \\- ${snd_zones['supply_2_high']:,.6f}
• 🟢 **Demand Zone 1**: ${snd_zones['demand_1_low']:,.6f} \\- ${snd_zones['demand_1_high']:,.6f}
• 🟢 **Demand Zone 2**: ${snd_zones['demand_2_low']:,.6f} \\- ${snd_zones['demand_2_high']:,.6f}

📈 **FUTURES TRADING SETUP:**
• **Direction**: {futures_signals['direction']} {futures_signals['emoji']}
• **Entry Price**: ${futures_signals['entry']:,.6f}
• **Take Profit 1**: ${futures_signals['tp1']:,.6f} \\(50%\\)
• **Take Profit 2**: ${futures_signals['tp2']:,.6f} \\(30%\\)
• **Take Profit 3**: ${futures_signals['tp3']:,.6f} \\(20%\\)
• **Stop Loss**: ${futures_signals['sl']:,.6f}
• **Risk/Reward**: {futures_signals['rr']:.1f}:1

🎯 **CONFIDENCE & STRATEGY:**
• **Confidence Level**: {futures_signals['confidence']:.1f}%
• **Strategy**: {futures_signals['strategy']}
• **Timeframe**: {tf_display} analysis
• **Position Size**: Max 2\\-3% portfolio

⚡ **EXECUTION PLAN:**
• 🎯 Wait for price action confirmation at SnD zones
• 📊 Enter position with proper risk management
• 💰 Scale out profits at multiple TP levels
• 🛡️ Move SL to breakeven after TP1 hit

⚠️ **RISK MANAGEMENT:**
• Never risk more than 1\\-2% per trade
• Use proper position sizing
• Monitor for SnD zone invalidation
• Exit if price closes outside zones

📡 **Data**: CoinAPI Real\\-time \\+ SnD Algorithm
🕐 **Valid**: Next 4\\-24 hours \\({tf_display} timeframe\\)"""
            
            return analysis
            
        except Exception as e:
            print(f"Error in futures analysis: {e}")
            return f"❌ Error dalam analisis futures {symbol} {timeframe}: {str(e)[:100]}..."
    
    def _generate_futures_signals(self, symbol: str, current_price: float, timeframe: str, snd_zones: Dict) -> Dict:
        """Generate futures-specific trading signals"""
        # Calculate signals based on SnD zones and timeframe
        supply_1_mid = (snd_zones['supply_1_low'] + snd_zones['supply_1_high']) / 2
        demand_1_mid = (snd_zones['demand_1_low'] + snd_zones['demand_1_high']) / 2
        
        # Determine direction based on position relative to SnD zones
        if current_price < demand_1_mid:
            direction = "LONG"
            emoji = "🟢"
            entry = demand_1_mid
            tp1 = supply_1_mid
            tp2 = snd_zones['supply_2_low']
            tp3 = snd_zones['supply_2_high']
            sl = snd_zones['demand_2_high']
            confidence = 75
            strategy = "SnD Reversal Long"
        elif current_price > supply_1_mid:
            direction = "SHORT"
            emoji = "🔴"
            entry = supply_1_mid
            tp1 = demand_1_mid
            tp2 = snd_zones['demand_2_high']
            tp3 = snd_zones['demand_2_low']
            sl = snd_zones['supply_2_low']
            confidence = 75
            strategy = "SnD Reversal Short"
        else:
            # Between zones - neutral
            direction = "WAIT"
            emoji = "⏳"
            entry = current_price
            tp1 = supply_1_mid if current_price < current_price else demand_1_mid
            tp2 = tp1 * 1.02
            tp3 = tp1 * 1.03
            sl = current_price * 0.98
            confidence = 45
            strategy = "Wait for SnD Confirmation"
        
        # Calculate risk/reward ratio
        try:
            risk = abs(entry - sl)
            reward = abs(tp1 - entry)
            rr_ratio = reward / risk if risk > 0 else 1.0
        except:
            rr_ratio = 1.0
        
        # Adjust confidence based on timeframe
        timeframe_multiplier = {
            '15m': 0.9, '30m': 0.95, '1h': 1.0,
            '4h': 1.1, '1d': 1.2, '1w': 1.3
        }.get(timeframe, 1.0)
        
        final_confidence = min(95, confidence * timeframe_multiplier)
        
        return {
            'direction': direction,
            'emoji': emoji,
            'entry': entry,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'sl': sl,
            'rr': rr_ratio,
            'confidence': final_confidence,
            'strategy': strategy
        }
    
    async def generate_futures_signals(self, language: str = 'id', crypto_api=None, query_args: List = None) -> str:
        """Generate multiple futures signals for top cryptocurrencies"""
        try:
            # Default symbols to analyze
            symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
            
            # Parse query args if provided
            timeframe = '4h'  # Default timeframe
            if query_args:
                for arg in query_args:
                    arg_upper = arg.upper()
                    if any(tf in arg_upper for tf in ['M', 'H', 'D', 'W']):
                        timeframe = arg.lower()
                    elif arg_upper in ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI', 'LINK']:
                        symbols = [arg_upper]
            
            signals_text = f"""🎯 **FUTURES SIGNALS DASHBOARD \\({timeframe.upper()}\\)**

📊 **Analysis Time**: {datetime.now().strftime('%H:%M:%S WIB')}
⚡ **Timeframe**: {timeframe.upper()} charts
🔍 **Method**: Supply & Demand \\+ CoinAPI Real\\-time

"""
            
            signal_count = 0
            for symbol in symbols[:3]:  # Limit to 3 symbols to avoid message length issues
                try:
                    # Get price data
                    price_data = {}
                    if crypto_api:
                        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                    
                    current_price = price_data.get('price', 0) if 'error' not in price_data else 0
                    if current_price == 0:
                        continue
                    
                    # Get SnD zones and signals
                    snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)
                    futures_signals = self._generate_futures_signals(symbol, current_price, timeframe, snd_zones)
                    
                    # Skip if confidence too low
                    if futures_signals['confidence'] < 60:
                        continue
                    
                    signal_count += 1
                    
                    # Format price
                    if current_price < 1:
                        price_format = f"${current_price:.6f}"
                    elif current_price < 100:
                        price_format = f"${current_price:.4f}"
                    else:
                        price_format = f"${current_price:,.2f}"
                    
                    signals_text += f"""🔥 **{symbol} SIGNAL #{signal_count}**
• **Direction**: {futures_signals['direction']} {futures_signals['emoji']}
• **Current**: {price_format}
• **Entry**: ${futures_signals['entry']:,.6f}
• **TP1**: ${futures_signals['tp1']:,.6f} \\(50%\\)
• **TP2**: ${futures_signals['tp2']:,.6f} \\(30%\\)
• **TP3**: ${futures_signals['tp3']:,.6f} \\(20%\\)
• **SL**: ${futures_signals['sl']:,.6f}
• **R:R**: {futures_signals['rr']:.1f}:1
• **Confidence**: {futures_signals['confidence']:.1f}%

"""
                
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue
            
            if signal_count == 0:
                signals_text += """⚠️ **No High\\-Quality Signals Available**

📊 **Reasons:**
• Low market volatility
• Price between SnD zones
• Insufficient confidence levels

💡 **Recommendations:**
• Check back in 30\\-60 minutes
• Use `/futures btc` for specific analysis
• Monitor for breakout confirmations

"""
            else:
                signals_text += f"""📋 **SUMMARY:**
• **Total Signals**: {signal_count}
• **Quality Filter**: 60%\\+ confidence only
• **Risk Management**: Max 2\\% per position

⚠️ **TRADING RULES:**
• Wait for SnD zone confirmation
• Use proper position sizing
• Scale out at multiple TPs
• Move SL to breakeven after TP1

"""
            
            signals_text += f"""📡 **Data Sources**: CoinAPI \\+ Internal SnD Algorithm
🔄 **Refresh**: Every 15\\-30 minutes for new setups
⏰ **Valid**: Next 4\\-24 hours \\({timeframe.upper()} analysis\\)"""
            
            return signals_text
            
        except Exception as e:
            print(f"Error generating futures signals: {e}")
            return f"❌ Error generating futures signals: {str(e)[:100]}..."
    
    def get_market_sentiment(self, language: str = 'id', crypto_api=None) -> str:
        """Get overall market sentiment analysis"""
        try:
            # Get data for major cryptocurrencies
            major_cryptos = ['BTC', 'ETH', 'SOL', 'ADA']
            market_data = []
            
            total_volume = 0
            total_change = 0
            
            for symbol in major_cryptos:
                if crypto_api:
                    price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                    if 'error' not in price_data:
                        market_data.append({
                            'symbol': symbol,
                            'price': price_data.get('price', 0),
                            'change_24h': price_data.get('change_24h', 0),
                            'volume_24h': price_data.get('volume_24h', 0)
                        })
                        total_volume += price_data.get('volume_24h', 0)
                        total_change += price_data.get('change_24h', 0)
            
            if not market_data:
                return "❌ Tidak dapat mengambil data pasar saat ini."
            
            # Calculate market sentiment
            avg_change = total_change / len(market_data)
            sentiment_score = 50 + (avg_change * 2)
            sentiment_score = max(0, min(100, sentiment_score))
            
            if sentiment_score > 70:
                sentiment_status = "Very Bullish 🚀"
                sentiment_emoji = "🟢"
            elif sentiment_score > 60:
                sentiment_status = "Bullish 📈"
                sentiment_emoji = "🟢"
            elif sentiment_score > 40:
                sentiment_status = "Neutral ⚖️"
                sentiment_emoji = "🟡"
            elif sentiment_score > 30:
                sentiment_status = "Bearish 📉"
                sentiment_emoji = "🔴"
            else:
                sentiment_status = "Very Bearish 💥"
                sentiment_emoji = "🔴"
            
            # Format volume
            if total_volume > 1000000000:
                volume_format = f"${total_volume/1000000000:.2f}B"
            elif total_volume > 1000000:
                volume_format = f"${total_volume/1000000:.1f}M"
            else:
                volume_format = f"${total_volume:,.0f}"
            
            analysis = f"""🌍 **OVERVIEW PASAR CRYPTO (CoinAPI)**

{sentiment_emoji} **Sentimen Pasar**: {sentiment_status}
📊 **Skor Sentimen**: {sentiment_score:.1f}/100

📈 **Data Agregat:**
• **Rata-rata Perubahan 24j**: {avg_change:+.2f}%
• **Total Volume**: {volume_format}
• **Coin Dianalisis**: {len(market_data)} major cryptos

💰 **Breakdown Per Coin:**"""
            
            for data in market_data:
                symbol = data['symbol']
                price = data['price']
                change = data['change_24h']
                volume = data['volume_24h']
                
                # Format price
                if price < 1:
                    price_format = f"${price:.6f}"
                elif price < 100:
                    price_format = f"${price:.4f}"
                else:
                    price_format = f"${price:,.2f}"
                
                # Format volume
                if volume > 1000000000:
                    vol_format = f"${volume/1000000000:.1f}B"
                elif volume > 1000000:
                    vol_format = f"${volume/1000000:.0f}M"
                else:
                    vol_format = f"${volume:,.0f}"
                
                change_emoji = "📈" if change >= 0 else "📉"
                
                analysis += f"""
• **{symbol}**: {price_format} ({change:+.2f}% {change_emoji}) - Vol: {vol_format}"""
            
            # Add market recommendations
            if sentiment_score > 60:
                recommendations = """
💡 **Rekomendasi Pasar:**
• ✅ Market kondusif untuk long positions
• 🎯 Focus pada momentum trading
• 📊 Monitor untuk profit taking opportunities"""
            elif sentiment_score < 40:
                recommendations = """
💡 **Rekomendasi Pasar:**
• ❌ Hati-hati dengan long positions
• 🎯 Consider short opportunities
• 🛡️ Increase cash position untuk safety"""
            else:
                recommendations = """
💡 **Rekomendasi Pasar:**
• ⏳ Tunggu konfirmasi arah yang jelas
• 📊 Focus pada range trading
• 🎯 Cari setup dengan R:R tinggi"""
            
            analysis += recommendations
            
            analysis += f"""

📡 **Data Source**: CoinAPI Real-time Market Data
🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Refresh**: Gunakan `/market` untuk data terbaru"""
            
            return analysis
            
        except Exception as e:
            print(f"Error in market sentiment: {e}")
            return f"❌ Error dalam analisis pasar: {str(e)[:100]}..."
    
    def get_ai_response(self, question: str, language: str = 'id') -> str:
        """Get AI response for general crypto questions"""
        try:
            # Simple AI responses for common crypto questions
            question_lower = question.lower()
            
            if any(word in question_lower for word in ['bitcoin', 'btc']):
                return """🟠 **Bitcoin (BTC) - Info**

Bitcoin adalah cryptocurrency pertama dan terbesar di dunia, diciptakan oleh Satoshi Nakamoto pada 2009.

💡 **Key Features:**
• Decentralized digital currency
• Limited supply: 21 million BTC
• Store of value & digital gold
• Proof of Work consensus

📊 **Trading Tips:**
• Long-term store of value
• High volatility short-term
• Follow institutional adoption news
• Technical analysis very effective

💰 **Investment Perspective:**
Bitcoin sering dianggap sebagai "digital gold" dan hedge against inflation."""
            
            elif any(word in question_lower for word in ['ethereum', 'eth']):
                return """🔷 **Ethereum (ETH) - Info**

Ethereum adalah platform blockchain yang mendukung smart contracts dan DeFi ecosystem.

💡 **Key Features:**
• Smart contract platform
• DeFi ecosystem hub
• NFT marketplace backbone
• Proof of Stake (since Merge)

📊 **Trading Tips:**
• Follow DeFi trends
• Monitor gas fees impact
• Watch for major upgrades
• Strong correlation with DeFi tokens

💰 **Investment Perspective:**
Ethereum adalah "infrastructure" untuk Web3 dan aplikasi blockchain."""
            
            elif any(word in question_lower for word in ['defi', 'decentralized finance']):
                return """🏦 **DeFi (Decentralized Finance) - Explained**

DeFi adalah sistem finansial yang dibangun di blockchain, tanpa intermediary tradisional.

💡 **Core Components:**
• DEX (Decentralized Exchanges)
• Lending & Borrowing protocols
• Yield farming & Liquidity mining
• Stablecoins & Synthetic assets

📊 **Popular DeFi Protocols:**
• Uniswap (DEX)
• Aave (Lending)
• Compound (Lending)
• MakerDAO (Stablecoin)

⚠️ **Risks:**
• Smart contract risks
• Impermanent loss
• High gas fees
• Regulatory uncertainty

💰 **Opportunities:**
• Higher yields than traditional finance
• Innovation in financial products"""
            
            elif any(word in question_lower for word in ['trading', 'strategy', 'teknikal']):
                return """📈 **Crypto Trading Strategy - Basics**

💡 **Fundamental Strategies:**

**1. Technical Analysis:**
• Support & Resistance levels
• Moving averages (EMA 50, 200)
• RSI, MACD indicators
• Volume analysis

**2. Risk Management:**
• Never risk >2-3% per trade
• Always use stop losses
• Take profits incrementally
• Position sizing is crucial

**3. Market Types:**
• Bull market: Buy dips
• Bear market: Short rallies
• Sideways: Range trading

⚠️ **Common Mistakes:**
• FOMO buying at peaks
• No stop loss usage
• Overleveraging positions
• Emotional trading

💰 **Pro Tips:**
• Plan your trades
• Keep trading journal
• Stay updated with news
• Practice with small amounts first"""
            
            else:
                return f"""🤖 **AI Response**

Pertanyaan Anda: "{question[:100]}..."

Maaf, saya belum memiliki informasi spesifik untuk pertanyaan ini. 

💡 **Cobalah pertanyaan tentang:**
• Bitcoin, Ethereum, atau crypto populer
• DeFi dan Web3 concepts
• Trading strategies dan technical analysis
• Risk management dalam crypto

📚 **Untuk analisis mendalam, gunakan:**
• `/analyze btc` - Analisis komprehensif Bitcoin
• `/futures eth` - Sinyal trading Ethereum
• `/market` - Overview pasar crypto

Atau ajukan pertanyaan yang lebih spesifik tentang cryptocurrency dan trading!"""
            
        except Exception as e:
            return f"❌ Error dalam memproses pertanyaan: {str(e)[:100]}..."
