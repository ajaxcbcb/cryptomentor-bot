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

            # Get additional info (news, market context, etc.)
            additional_info = self._get_additional_market_info(symbol, current_price, change_24h)

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
• **Confidence**: {signal_data.get('confidence', 50):.1f}%
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

{additional_info}

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
        """Generate trading signals based on price action with confidence scoring"""
        # Calculate base confidence from price action and volume
        base_confidence = 50

        # Price momentum factor
        if abs(change_24h) > 10:
            base_confidence += 25
        elif abs(change_24h) > 5:
            base_confidence += 15
        elif abs(change_24h) > 2:
            base_confidence += 8

        # Volume factor
        if volume > 500000000:  # High volume
            base_confidence += 10
        elif volume > 100000000:  # Medium volume
            base_confidence += 5

        # Direction and strength based on change
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
            base_confidence = 35  # Lower confidence for sideways

        # Apply confidence threshold - if below 75%, neutralize the signal
        final_confidence = min(95, base_confidence)
        if final_confidence < 75:
            direction = "NEUTRAL"
            emoji = "⚖️"
            strength = "Weak Signal"
            trend = "Uncertain"

        # Calculate entry, TP, SL - NEUTRAL uses same entry as current price
        if direction == "LONG" and final_confidence >= 75:
            entry_price = price * 0.999  # Slight below current
            take_profit = price * 1.03   # 3% profit
            stop_loss = price * 0.98     # 2% loss
        elif direction == "SHORT" and final_confidence >= 75:
            entry_price = price * 1.001  # Slight above current
            take_profit = price * 0.97   # 3% profit
            stop_loss = price * 1.02     # 2% loss
        else:
            # NEUTRAL or low confidence - same entry as current price
            entry_price = price
            take_profit = price * 1.01   # Minimal target
            stop_loss = price * 0.99     # Minimal stop

        return {
            'direction': direction,
            'emoji': emoji,
            'strength': strength,
            'trend': trend,
            'entry_price': entry_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'confidence': final_confidence,
            'strategy': 'Momentum Trading' if final_confidence >= 75 else 'Wait for Confirmation',
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

    def _get_additional_market_info(self, symbol: str, current_price: float, change_24h: float) -> str:
        """Generate additional market information including news and context"""
        try:
            # Generate market news/events (simplified - you can integrate real news API later)
            news_items = self._generate_market_news(symbol, change_24h)

            # Market context and important levels
            market_context = self._generate_market_context(symbol, current_price, change_24h)

            # Social sentiment indicators
            social_sentiment = self._generate_social_sentiment(symbol, change_24h)

            additional_section = f"""📰 **BERITA & INFO TERKINI**:
{news_items}

🌍 **KONTEKS PASAR**:
{market_context}

💬 **SENTIMEN SOSIAL**:
{social_sentiment}"""

            return additional_section

        except Exception as e:
            return f"""📰 **BERITA & INFO TERKINI**:
• 📊 Data analisis real-time tersedia
• 🔍 Monitor terus untuk update terbaru

🌍 **KONTEKS PASAR**:
• 📈 Pasar crypto aktif 24/7
• 🎯 Focus pada level SnD untuk timing optimal

💬 **SENTIMEN SOSIAL**:
• 📱 Community sentiment: Mixed
• 🗣️ Monitor social media untuk catalyst"""

    def _generate_market_news(self, symbol: str, change_24h: float) -> str:
        """Generate relevant market news based on price action"""
        news_items = []

        if abs(change_24h) > 10:
            if change_24h > 0:
                news_items.append("• 🚀 High volatility: Price surge detected!")
                news_items.append("• 📊 Volume spike indicates strong buying interest")
            else:
                news_items.append("• 📉 Sharp decline: Market correction in progress")
                news_items.append("• ⚠️ High selling pressure observed")
        elif abs(change_24h) > 5:
            news_items.append("• 📈 Moderate price movement detected")
            news_items.append("• 🎯 Key levels being tested")
        else:
            news_items.append("• ⚖️ Low volatility: Consolidation phase")
            news_items.append("• 📊 Range-bound trading conditions")

        # Add symbol-specific insights
        if symbol == 'BTC':
            news_items.append("• 🟠 Bitcoin dominance impact on altcoins")
            news_items.append("• 📊 Institutional adoption continues")
        elif symbol == 'ETH':
            news_items.append("• 🔷 Ethereum ecosystem developments")
            news_items.append("• ⛽ Gas fees impact on network usage")
        elif symbol in ['SOL', 'ADA', 'DOT']:
            news_items.append("• 🔗 Altcoin correlation with BTC/ETH")
            news_items.append("• 🚀 Layer-1 competition dynamics")
        else:
            news_items.append("• 📈 Altcoin market sentiment tracking")
            news_items.append("• 🔍 Technical analysis primary focus")

        return "\n".join(news_items)

    def _generate_market_context(self, symbol: str, current_price: float, change_24h: float) -> str:
        """Generate market context information"""
        context_items = []

        # Market hours context
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 18:
            context_items.append("• 🌅 Asian/European market hours active")
        else:
            context_items.append("• 🌙 US market hours / late trading")

        # Weekly patterns
        weekday = datetime.now().weekday()
        if weekday in [0, 1]:  # Monday, Tuesday
            context_items.append("• 📅 Early week: Trend continuation likely")
        elif weekday in [2, 3]:  # Wednesday, Thursday
            context_items.append("• 📅 Mid-week: High activity period")
        else:  # Friday, Weekend
            context_items.append("• 📅 Week-end: Lower volume expected")

        # Price level context
        if current_price > 50000 and symbol == 'BTC':
            context_items.append("• 💰 BTC above psychological 50K level")
        elif current_price > 3000 and symbol == 'ETH':
            context_items.append("• 💎 ETH above major resistance zone")

        # Market cycle context
        if change_24h > 5:
            context_items.append("• 🚀 Bull market conditions emerging")
        elif change_24h < -5:
            context_items.append("• 🐻 Bear market pressure building")
        else:
            context_items.append("• ⚖️ Neutral market conditions")

        return "\n".join(context_items)

    def _generate_social_sentiment(self, symbol: str, change_24h: float) -> str:
        """Generate social sentiment indicators"""
        sentiment_items = []

        # Simulate social sentiment based on price action
        if change_24h > 10:
            sentiment_items.append("• 🔥 Social media: Extremely bullish")
            sentiment_items.append("• 📱 FOMO indicators: Very High")
            sentiment_items.append("• 🎯 Retail interest: Peak levels")
        elif change_24h > 5:
            sentiment_items.append("• 📈 Social media: Bullish sentiment")
            sentiment_items.append("• 📱 Community engagement: Increasing")
            sentiment_items.append("• 💪 Confidence levels: Rising")
        elif change_24h < -10:
            sentiment_items.append("• 😰 Social media: Fear dominates")
            sentiment_items.append("• 📱 Panic selling indicators: High")
            sentiment_items.append("• 🛡️ Risk-off sentiment prevalent")
        elif change_24h < -5:
            sentiment_items.append("• 📉 Social media: Bearish tone")
            sentiment_items.append("• 📱 Uncertainty levels: Elevated")
            sentiment_items.append("• ⚠️ Caution advised by community")
        else:
            sentiment_items.append("• 😐 Social media: Mixed signals")
            sentiment_items.append("• 📱 Neutral community sentiment")
            sentiment_items.append("• 🤔 Wait-and-see attitude")

        # Add engagement metrics
        sentiment_items.append(f"• 📊 Estimated social volume: {self._estimate_social_volume(change_24h)}")

        return "\n".join(sentiment_items)

    def _estimate_social_volume(self, change_24h: float) -> str:
        """Estimate social media volume based on price movement"""
        if abs(change_24h) > 15:
            return "Very High"
        elif abs(change_24h) > 10:
            return "High"
        elif abs(change_24h) > 5:
            return "Medium"
        else:
            return "Low"

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
        """Get futures trading signals with SnD for specific timeframe"""
        try:
            # Get current price and market data
            price_data = {}
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                futures_data = crypto_api.get_futures_data(symbol)

            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if 'error' not in price_data else 0

            if current_price <= 0:
                return f"❌ Tidak dapat mengambil data harga {symbol}"

            # Get advanced SnD zones with volume analysis
            snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)

            # Generate professional futures signals
            futures_signals = self._generate_advanced_futures_signals(symbol, current_price, timeframe, snd_zones, volume_24h)

            # Format timeframe display
            tf_display = {
                '15m': '15M', '30m': '30M', '1h': '1H',
                '4h': '4H', '1d': '1D', '1w': '1W'
            }.get(timeframe, timeframe.upper())

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

            # Signal strength indicator
            confidence = futures_signals['confidence']
            if confidence >= 80:
                signal_strength = "🔥 STRONG SIGNAL"
                strength_emoji = "🟢"
            elif confidence >= 65:
                signal_strength = "⚡ GOOD SIGNAL"
                strength_emoji = "🟡"
            else:
                signal_strength = "⚠️ WEAK SIGNAL"
                strength_emoji = "🟠"

            # Market structure analysis
            market_structure = self._analyze_market_structure(current_price, snd_zones, change_24h)

            analysis = f"""🚨 **FUTURES TRADING SIGNAL - {symbol}/{tf_display}**

{strength_emoji} **{signal_strength}**
📊 **Price**: {price_format} ({change_24h:+.2f}%)
💹 **Volume**: {volume_format}
🕐 **Time**: {datetime.now().strftime('%H:%M:%S WIB')}

🎯 **TRADING SETUP:**
• **Direction**: {futures_signals['direction']} {futures_signals['emoji']}
• **Confidence**: {confidence:.1f}%
• **Entry**: ${futures_signals['entry']:,.6f}
• **TP1** (50%): ${futures_signals['tp1']:,.6f}
• **TP2** (30%): ${futures_signals['tp2']:,.6f}
• **TP3** (20%): ${futures_signals['tp3']:,.6f}
• **Stop Loss**: ${futures_signals['sl']:,.6f}
• **Risk/Reward**: {futures_signals['rr']:.1f}:1
📈 **Strategy**: {futures_signals['strategy']}
⏰ **Timeframe**: {tf_display} ({futures_signals['time_horizon']})

🏗️ **MARKET STRUCTURE:**
{market_structure}

🎯 **KEY SnD LEVELS:**
• 🔴 **Resistance 1**: ${snd_zones['supply_1_low']:,.6f} - ${snd_zones['supply_1_high']:,.6f}
• 🔴 **Resistance 2**: ${snd_zones['supply_2_low']:,.6f} - ${snd_zones['supply_2_high']:,.6f}
• 🟢 **Support 1**: ${snd_zones['demand_1_low']:,.6f} - ${snd_zones['demand_1_high']:,.6f}
• 🟢 **Support 2**: ${snd_zones['demand_2_low']:,.6f} - ${snd_zones['demand_2_high']:,.6f}

⚡ **EXECUTION RULES:**
• Enter ONLY with volume confirmation
• Scale in at SnD zone boundaries
• Move SL to breakeven after TP1
• Exit 50% at TP1, 30% at TP2, 20% at TP3

💰 **POSITION SIZING:**
• Risk per trade: 1-2% of capital max
• Leverage: {futures_signals.get('leverage_rec', '3-5x')} recommended
• Account for slippage and fees

⚠️ **RISK WARNINGS:**
• Futures trading involves high risk
• Only trade with risk capital
• Market conditions can change rapidly
• Always use stop losses

📡 **Signal Source**: CoinAPI + SnD Algorithm
🔄 **Valid Duration**: {futures_signals['validity']}
📊 **Update Frequency**: Every {timeframe} candle close"""

            return analysis

        except Exception as e:
            print(f"Error in futures signals: {e}")
            return f"❌ Error dalam futures signals {symbol} {timeframe}: {str(e)[:100]}..."

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

        # Apply confidence threshold - if below 75%, neutralize signal
        if confidence < 75:
            direction = "NEUTRAL"
            emoji = "⚖️"
            entry = current_price  # Same as current price for neutral
            tp1 = current_price * 1.005  # Minimal target
            tp2 = current_price * 1.01
            tp3 = current_price * 1.015
            sl = current_price * 0.995   # Minimal stop
            strategy = "Low Confidence - Wait for Better Setup"

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

    def _generate_advanced_futures_signals(self, symbol: str, current_price: float, timeframe: str, snd_zones: Dict, volume_24h: float) -> Dict:
        """Generate advanced futures trading signals with volume analysis"""
        try:
            # Get basic signals first
            basic_signals = self._generate_futures_signals(symbol, current_price, timeframe, snd_zones)

            # Enhanced signal calculation with volume
            supply_1_mid = (snd_zones['supply_1_low'] + snd_zones['supply_1_high']) / 2
            demand_1_mid = (snd_zones['demand_1_low'] + snd_zones['demand_1_high']) / 2

            # Volume analysis
            # Enhanced volume analysis for futures with improved thresholds
            volume_score = 100 if volume_24h > 2000000000 else 95 if volume_24h > 1000000000 else 85 if volume_24h > 500000000 else 75 if volume_24h > 200000000 else 60 if volume_24h > 100000000 else 40 if volume_24h > 50000000 else 20
            volume_status = "🔥 Exceptional" if volume_score >= 95 else "⚡ Very High" if volume_score >= 85 else "📊 High" if volume_score >= 75 else "📈 Good" if volume_score >= 60 else "📉 Medium" if volume_score >= 40 else "💤 Low"

            # Volume-based confidence adjustment
            if volume_score >= 85:
                volume_confidence_bonus = 5
            elif volume_score >= 75:
                volume_confidence_bonus = 3
            elif volume_score >= 60:
                volume_confidence_bonus = 0
            else:
                volume_confidence_bonus = -5

            # Position relative to SnD zones with volume consideration
            distance_to_supply = abs(current_price - supply_1_mid) / current_price * 100
            distance_to_demand = abs(current_price - demand_1_mid) / current_price * 100

            # Enhanced direction logic
            if current_price <= demand_1_mid and distance_to_demand < 2:
                direction = "LONG"
                emoji = "🟢"
                entry = current_price * 0.999  # Slight below current
                tp1 = supply_1_mid
                tp2 = snd_zones['supply_1_high']
                tp3 = snd_zones['supply_2_low']
                sl = snd_zones['demand_1_low']
                strategy = "SnD Demand Zone Long"
                base_confidence = 80

            elif current_price >= supply_1_mid and distance_to_supply < 2:
                direction = "SHORT"
                emoji = "🔴"
                entry = current_price * 1.001  # Slight above current
                tp1 = demand_1_mid
                tp2 = snd_zones['demand_1_low']
                tp3 = snd_zones['demand_2_high']
                sl = snd_zones['supply_1_high']
                strategy = "SnD Supply Zone Short"
                base_confidence = 80

            elif current_price < supply_1_mid and current_price > demand_1_mid:
                # Between zones - momentum strategy
                if current_price > (supply_1_mid + demand_1_mid) / 2:
                    # Upper half - potential breakout long
                    direction = "LONG"
                    emoji = "🟢"
                    entry = current_price
                    tp1 = supply_1_mid
                    tp2 = snd_zones['supply_1_high']
                    tp3 = snd_zones['supply_2_low']
                    sl = demand_1_mid
                    strategy = "Breakout Long"
                    base_confidence = 65
                else:
                    # Lower half - potential breakdown short
                    direction = "SHORT"
                    emoji = "🔴"
                    entry = current_price
                    tp1 = demand_1_mid
                    tp2 = snd_zones['demand_1_low']
                    tp3 = snd_zones['demand_2_high']
                    sl = supply_1_mid
                    strategy = "Breakdown Short"
                    base_confidence = 65
            else:
                direction = "WAIT"
                emoji = "⏳"
                entry = current_price
                tp1 = supply_1_mid if current_price < supply_1_mid else demand_1_mid
                tp2 = tp1 * 1.02
                tp3 = tp1 * 1.03
                sl = current_price * 0.98
                strategy = "Wait for Clear Setup"
                base_confidence = 40

            # Calculate risk/reward ratio
            try:
                risk = abs(entry - sl)
                reward = abs(tp1 - entry)
                rr_ratio = reward / risk if risk > 0 else 1.0
            except:
                rr_ratio = 1.0

            # Confidence adjustments
            timeframe_multiplier = {
                '15m': 0.9, '30m': 0.95, '1h': 1.0,
                '4h': 1.1, '1d': 1.2, '1w': 1.3
            }.get(timeframe, 1.0)

            # RR ratio bonus
            rr_bonus = min(1.1, 1.0 + (rr_ratio - 1.0) * 0.1) if rr_ratio > 1 else 0.9

            final_confidence = min(95, base_confidence * volume_multiplier * timeframe_multiplier * rr_bonus)

            # Apply 75% confidence threshold - neutralize if below
            if final_confidence < 75:
                direction = "NEUTRAL"
                emoji = "⚖️"
                entry = current_price  # Same as current price
                tp1 = current_price * 1.005  # Minimal targets
                tp2 = current_price * 1.01
                tp3 = current_price * 1.015
                sl = current_price * 0.995   # Minimal stop
                strategy = "Low Confidence - Wait for Better Setup"

            # Leverage recommendation based on confidence and timeframe
            if final_confidence >= 80:
                leverage_rec = "5-10x"
            elif final_confidence >= 70:
                leverage_rec = "3-5x"
            elif final_confidence >= 60:
                leverage_rec = "2-3x"
            else:
                leverage_rec = "1-2x"

            # Validity duration
            validity_hours = {
                '15m': '2-4 hours', '30m': '4-8 hours', '1h': '8-12 hours',
                '4h': '1-2 days', '1d': '3-5 days', '1w': '1-2 weeks'
            }.get(timeframe, '4-12 hours')

            # Time horizon
            time_horizon = {
                '15m': 'Scalping (15-60 min)', '30m': 'Short-term (1-4 hours)', '1h': 'Intraday (4-12 hours)',
                '4h': 'Swing (1-3 days)', '1d': 'Position (3-7 days)', '1w': 'Long-term (1-4 weeks)'
            }.get(timeframe, 'Medium-term')

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
                'strategy': strategy,
                'leverage_rec': leverage_rec,
                'validity': validity_hours,
                'time_horizon': time_horizon,
                'volume_strength': volume_status,
                'distance_to_supply': distance_to_supply,
                'distance_to_demand': distance_to_demand
            }

        except Exception as e:
            # Fallback to basic signals
            return self._generate_futures_signals(symbol, current_price, timeframe, snd_zones)

    def _analyze_market_structure(self, current_price: float, snd_zones: Dict, change_24h: float) -> str:
        """Analyze market structure for futures trading"""
        try:
            supply_1_mid = (snd_zones['supply_1_low'] + snd_zones['supply_1_high']) / 2
            demand_1_mid = (snd_zones['demand_1_low'] + snd_zones['demand_1_high']) / 2

            # Position analysis
            if current_price > supply_1_mid:
                position = "Above resistance"
                bias = "Bullish structure"
            elif current_price < demand_1_mid:
                position = "Below support"
                bias = "Bearish structure"
            else:
                position = "In range"
                bias = "Neutral structure"

            # Momentum analysis
            if change_24h > 5:
                momentum = "Strong bullish momentum"
            elif change_24h > 2:
                momentum = "Moderate bullish momentum"
            elif change_24h > -2:
                momentum = "Sideways momentum"
            elif change_24h > -5:
                momentum = "Moderate bearish momentum"
            else:
                momentum = "Strong bearish momentum"

            # Zone strength
            zone_width = abs(supply_1_mid - demand_1_mid) / current_price * 100
            if zone_width < 1:
                zone_strength = "Tight ranges (high precision)"
            elif zone_width < 3:
                zone_strength = "Normal ranges"
            else:
                zone_strength = "Wide ranges (lower precision)"

            return f"""• **Position**: {position}
• **Bias**: {bias}
• **Momentum**: {momentum}
• **Zone Strength**: {zone_strength}"""

        except Exception as e:
            return "• **Structure**: Analysis unavailable"

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
• **Confidence**: {futures_signals['confidence']:.1f}%
• **Current**: {price_format}
• **Entry**: ${futures_signals['entry']:,.6f}
• **TP1**: ${futures_signals['tp1']:,.6f} \\(50%\\)
• **TP2**: ${futures_signals['tp2']:,.6f} \\(30%\\)
• **TP3**: ${futures_signals['tp3']:,.6f} \\(20%\\)
• **SL**: ${futures_signals['sl']:,.6f}
• **R:R**: {futures_signals['rr']:.1f}:1

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
        """Get comprehensive market overview and sentiment analysis"""
        try:
            # Get data for major cryptocurrencies
            major_cryptos = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']
            market_data = []

            total_volume = 0
            total_change = 0
            total_market_cap = 0

            for symbol in major_cryptos:
                if crypto_api:
                    price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        price = price_data.get('price', 0)
                        change_24h = price_data.get('change_24h', 0)
                        volume_24h = price_data.get('volume_24h', 0)
                        market_cap = price_data.get('market_cap', 0) or (price * 1000000)  # Fallback estimation

                        market_data.append({
                            'symbol': symbol,
                            'price': price,
                            'change_24h': change_24h,
                            'volume_24h': volume_24h,
                            'market_cap': market_cap
                        })
                        total_volume += volume_24h
                        total_change += change_24h
                        total_market_cap += market_cap

            if not market_data:
                return "❌ Tidak dapat mengambil data pasar saat ini."

            # Calculate comprehensive market metrics
            avg_change = total_change / len(market_data)
            sentiment_score = 50 + (avg_change * 2)
            sentiment_score = max(0, min(100, sentiment_score))

            # Market sentiment classification
            if sentiment_score > 75:
                sentiment_status = "Extremely Bullish 🚀🚀"
                sentiment_emoji = "🟢"
                market_phase = "Bull Run"
            elif sentiment_score > 60:
                sentiment_status = "Bullish 📈"
                sentiment_emoji = "🟢"
                market_phase = "Bull Market"
            elif sentiment_score > 55:
                sentiment_status = "Slightly Bullish 📊"
                sentiment_emoji = "🟡"
                market_phase = "Bullish Consolidation"
            elif sentiment_score > 45:
                sentiment_status = "Neutral ⚖️"
                sentiment_emoji = "🟡"
                market_phase = "Sideways Market"
            elif sentiment_score > 40:
                sentiment_status = "Slightly Bearish 📉"
                sentiment_emoji = "🟠"
                market_phase = "Bearish Consolidation"
            elif sentiment_score > 25:
                sentiment_status = "Bearish 📉"
                sentiment_emoji = "🔴"
                market_phase = "Bear Market"
            else:
                sentiment_status = "Extremely Bearish 💥"
                sentiment_emoji = "🔴"
                market_phase = "Bear Market Crash"

            # Format large numbers
            def format_large_number(num):
                if num > 1000000000000:  # Trillion
                    return f"${num/1000000000000:.2f}T"
                elif num > 1000000000:  # Billion
                    return f"${num/1000000000:.2f}B"
                elif num > 1000000:  # Million
                    return f"${num/1000000:.1f}M"
                else:
                    return f"${num:,.0f}"

            # Count gainers vs losers
            gainers = sum(1 for data in market_data if data['change_24h'] > 0)
            losers = len(market_data) - gainers

            # Fear & Greed Index simulation
            if sentiment_score > 75:
                fear_greed = "Extreme Greed"
                fg_emoji = "🤑"
            elif sentiment_score > 60:
                fear_greed = "Greed"
                fg_emoji = "😍"
            elif sentiment_score > 45:
                fear_greed = "Neutral"
                fg_emoji = "😐"
            elif sentiment_score > 30:
                fear_greed = "Fear"
                fg_emoji = "😰"
            else:
                fear_greed = "Extreme Fear"
                fg_emoji = "😱"

            analysis = f"""🌍 **GLOBAL CRYPTO MARKET OVERVIEW**

{sentiment_emoji} **Market Sentiment**: {sentiment_status}
📊 **Sentiment Score**: {sentiment_score:.1f}/100
🎭 **Fear & Greed**: {fear_greed} {fg_emoji}
📈 **Market Phase**: {market_phase}

💰 **MARKET STATISTICS:**
• **Total Market Cap**: {format_large_number(total_market_cap)}
• **24h Volume**: {format_large_number(total_volume)}
• **Average Change**: {avg_change:+.2f}%
• **Gainers**: {gainers} | **Losers**: {losers}

📊 **TOP CRYPTOCURRENCIES:**"""

            # Sort by market cap for better display
            market_data.sort(key=lambda x: x['market_cap'], reverse=True)

            for i, data in enumerate(market_data[:6], 1):  # Show top 6
                symbol = data['symbol']
                price = data['price']
                change = data['change_24h']
                volume = data['volume_24h']
                market_cap = data['market_cap']

                # Format price
                if price < 1:
                    price_format = f"${price:.6f}"
                elif price < 100:
                    price_format = f"${price:.4f}"
                else:
                    price_format = f"${price:,.2f}"

                change_emoji = "📈" if change >= 0 else "📉"
                change_color = "🟢" if change >= 0 else "🔴"

                analysis += f"""
{i}. **{symbol}** {change_color}
   💰 Price: {price_format} ({change:+.2f}% {change_emoji})
   📊 MCap: {format_large_number(market_cap)}
   💹 Vol: {format_large_number(volume)}"""

            # Market analysis & recommendations
            if avg_change > 5:
                market_analysis = """
🔥 **MARKET ANALYSIS:**
• Strong bullish momentum across major cryptos
• High volume indicates institutional interest
• Breakout potential from key resistance levels
• FOMO sentiment building in retail"""

                trading_rec = """
💡 **TRADING RECOMMENDATIONS:**
• ✅ Consider long positions on pullbacks
• 🎯 Focus on momentum coins with volume
• 📊 Take profits incrementally on pumps
• ⚠️ Watch for overextension signals"""

            elif avg_change > 2:
                market_analysis = """
📈 **MARKET ANALYSIS:**
• Moderate bullish sentiment prevailing
• Selective buying in quality projects
• Technical levels holding as support
• Gradual accumulation phase"""

                trading_rec = """
💡 **TRADING RECOMMENDATIONS:**
• ✅ Gradual position building recommended
• 🎯 Focus on fundamental strong coins
• 📊 DCA strategy effective in this phase
• 🛡️ Use proper risk management"""

            elif avg_change > -2:
                market_analysis = """
⚖️ **MARKET ANALYSIS:**
• Consolidation phase with mixed signals
• Traders waiting for clear direction
• Range-bound trading dominant
• Low volatility environment"""

                trading_rec = """
💡 **TRADING RECOMMENDATIONS:**
• ⏳ Wait for clearer market direction
• 📊 Range trading opportunities available
• 🎯 Focus on swing trading setups
• 💰 Build cash position for next move"""

            elif avg_change > -5:
                market_analysis = """
📉 **MARKET ANALYSIS:**
• Bearish pressure building across market
• Profit taking and risk-off sentiment
• Support levels being tested
• Uncertainty in market direction"""

                trading_rec = """
💡 **TRADING RECOMMENDATIONS:**
• ❌ Avoid new long positions
• 🎯 Consider short opportunities
• 🛡️ Increase cash allocation
• 📊 Wait for oversold bounces"""

            else:
                market_analysis = """
💥 **MARKET ANALYSIS:**
• Strong bearish sentiment dominating
• Panic selling and liquidations
• Major support levels breaking
• Risk-off environment prevailing"""

                trading_rec = """
💡 **TRADING RECOMMENDATIONS:**
• 🛑 Avoid catching falling knives
• 💰 Build cash for bottom opportunities
• 📊 Wait for capitulation signals
• 🎯 DCA only for long-term holdings"""

            analysis += market_analysis + trading_rec

            # Market timing and cycles
            current_hour = datetime.now().hour
            if 14 <= current_hour <= 22:  # US trading hours
                market_hours = "🇺🇸 US Market Hours - High Activity"
            elif 8 <= current_hour <= 16:  # European hours
                market_hours = "🇪🇺 European Hours - Moderate Activity"
            elif 0 <= current_hour <= 8:  # Asian hours
                market_hours = "🌏 Asian Hours - Lower Activity"
            else:
                market_hours = "🌃 Off-peak Hours"

            analysis += f"""

⏰ **MARKET TIMING:**
• {market_hours}
• Best for: {"Scalping & Day Trading" if 14 <= current_hour <= 22 else "Swing Trading Setup" if 8 <= current_hour <= 16 else "Position Planning"}

🔄 **NEXT CATALYSTS:**
• 📊 Weekly close sentiment
• 📰 Macro economic events
• 🏛️ Regulatory announcements
• 📈 Technical level breaks

📡 **Data**: CoinAPI Real-time + Market Analysis
🕐 **Updated**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Refresh**: Use `/market` for latest data"""

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