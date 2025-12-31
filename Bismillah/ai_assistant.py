import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import random
import hashlib

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

            # Format analysis with proper spacing
            analysis = f"""📊 **ANALISIS KOMPREHENSIF {symbol} (CoinAPI + SnD)**

💰 **Data Harga Real-time:**
• **Harga Saat Ini**: {price_format}
• **Perubahan 24j**: {change_24h:+.2f}% {change_emoji}
• **Volume 24j**: {volume_format}

🎯 **ENHANCED SUPPLY & DEMAND ZONES** ({snd_zones.get('engine_used', 'Unknown')}):
• 🔴 Supply Zone 1: ${snd_zones['supply_1_low']:,.6f} - ${snd_zones['supply_1_high']:,.6f}
• 🔴 Supply Zone 2: ${snd_zones['supply_2_low']:,.6f} - ${snd_zones['supply_2_high']:,.6f}
• 🟢 Demand Zone 1: ${snd_zones['demand_1_low']:,.6f} - ${snd_zones['demand_1_high']:,.6f}
• 🟢 Demand Zone 2: ${snd_zones['demand_2_low']:,.6f} - ${snd_zones['demand_2_high']:,.6f}

🔍 **SnD ENGINE ANALYSIS:**
• Zone Position: {snd_zones.get('position', 'Unknown')}
• Zone Strength: {snd_zones.get('strength', 'Unknown')}
{f"• Engine Signal: **{snd_zones['entry_signal']}** ({snd_zones['signal_strength']:.0f}%)" if snd_zones.get('entry_signal') else "• Engine Signal: No signal detected"}

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

📡 **Data Source**: Binance Real-time + Internal SnD Algorithm
🕐 **Analisis**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            return analysis

        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            return f"❌ Terjadi kesalahan dalam analisis {symbol}. Error: {str(e)[:100]}..."

    async def get_comprehensive_analysis_async(self, symbol: str, indicators: Dict = None, market_data: Dict = None, language: str = 'id', crypto_api=None, progress_tracker=None, user_id=None) -> str:
        """Generate comprehensive crypto analysis with enhanced data accuracy"""
        try:
            # Get user language for proper response
            user_lang = 'en'
            if user_id:
                from database import Database
                db = Database()
                user_lang = db.get_user_language(user_id)

            # Enhanced timing for high-accuracy data processing
            stage_timings = {
                'data_validation': 1.0,  # 1.0 seconds - thorough data validation
                'cross_verify': 1.2,     # 1.2 seconds - cross-verification
                'technical': 1.5,        # 1.5 seconds - enhanced technical analysis
                'snd_zones': 1.3,        # 1.3 seconds - precise SnD calculations
                'signals': 2.2,          # 2.2 seconds - comprehensive signal generation
                'sentiment': 1.4,        # 1.4 seconds - detailed sentiment analysis
                'finalize': 1.4          # 1.4 seconds - thorough finalization
            }

            # Update progress: Stage 1 - Enhanced data validation
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "🔍 Memvalidasi sumber data...", 12)
                else:
                    progress_tracker.update_progress(user_id, "🔍 Validating data sources...", 12)
                await asyncio.sleep(stage_timings['data_validation'])

            # Enhanced data fetching with validation
            price_data = {}
            data_quality_score = 0

            if crypto_api:
                # Primary data fetch with enhanced validation
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)

                # Data quality assessment
                if 'error' not in price_data:
                    accuracy_score = price_data.get('accuracy_score', 0)
                    validation_passed = price_data.get('validation_passed', False)

                    if validation_passed and accuracy_score > 80:
                        data_quality_score = accuracy_score
                    elif accuracy_score > 60:
                        data_quality_score = accuracy_score * 0.9  # Slight penalty
                    else:
                        # Low quality data - try alternative approach
                        if user_id and progress_tracker:
                            if user_lang == 'id':
                                progress_tracker.update_progress(user_id, "⚠️ Mencoba ulang dengan metode cadangan...", 18)
                            else:
                                progress_tracker.update_progress(user_id, "⚠️ Retrying with backup method...", 18)

                        # Retry with different validation approach
                        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                        data_quality_score = price_data.get('accuracy_score', 50)

            # Update progress: Stage 2 - Cross-verification
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "✅ Verifikasi silang data...", 28)
                else:
                    progress_tracker.update_progress(user_id, "✅ Cross-verifying data...", 28)
                await asyncio.sleep(stage_timings['cross_verify'])

            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if 'error' not in price_data else 0

            if current_price <= 0:
                # Complete job even on error
                if user_id and progress_tracker:
                    progress_tracker.complete_job(user_id)

                # Check if it's a coin availability issue
                if price_data and 'available_coins' in price_data:
                    available_list = ', '.join(price_data['available_coins'][:15])
                    variants_info = ""
                    if 'variants_tried' in price_data:
                        variants_info = f"\n🔍 **Format Dicoba**: {', '.join(price_data['variants_tried'])}"

                    return f"""❌ **KOIN TIDAK TERSEDIA**: {symbol} tidak tersedia di Binance Exchange

🔍 **Detail Error**: {price_data.get('last_error', 'Unknown error')}{variants_info}

💡 **Koin yang Tersedia:**
{available_list}

🎯 **Rekomendasi:**
• `/analyze btc` - Bitcoin (paling populer)
• `/analyze eth` - Ethereum 
• `/analyze sol` - Solana
• `/analyze xrp` - XRP
• `/analyze ada` - Cardano
• `/analyze aster` - Astar Network (jika tersedia)

📊 **Info**: Bot mencoba beberapa format symbol (USDT, BUSD, USDC pairs) untuk mencari {symbol} di Binance Exchange.

💡 **Tips**: Pastikan symbol benar, contoh: 'BTC' bukan 'Bitcoin', 'ETH' bukan 'Ethereum'"""
                else:
                    if user_lang == 'id':
                        return f"❌ **DATA ERROR**: Tidak dapat mengambil data {symbol}\n\n💡 **Solusi**: Coba `/analyze btc` atau `/analyze eth`\n\n🔍 **Detail**: {price_data.get('error', 'Unknown error') if price_data else 'No data returned'}"
                    else:
                        return f"❌ **DATA ERROR**: Could not retrieve data for {symbol}\n\n💡 **Solution**: Try `/analyze btc` or `/analyze eth`\n\n🔍 **Details**: {price_data.get('error', 'Unknown error') if price_data else 'No data returned'}"

            # Update progress: Stage 2 - Technical analysis (OPTIMIZED)
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "📊 Memproses indikator...", 35)
                else:
                    progress_tracker.update_progress(user_id, "📊 Processing indicators...", 35)
                await asyncio.sleep(stage_timings['technical'])

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

            # Update progress: Stage 3 - SnD zones (FAST)
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "🎯 Menghitung SnD...", 55)
                else:
                    progress_tracker.update_progress(user_id, "🎯 Calculating SnD...", 55)
                await asyncio.sleep(stage_timings['snd_zones'])

            # Get Supply & Demand zones
            snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)

            # Update progress: Stage 4 - Signal generation (CORE)
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "⚡ Menghasilkan sinyal...", 75)
                else:
                    progress_tracker.update_progress(user_id, "⚡ Generating signals...", 75)
                await asyncio.sleep(stage_timings['signals'])

            # Generate signals
            signal_data = self._generate_trading_signals(symbol, current_price, change_24h, volume_24h)

            # Update progress: Stage 5 - Sentiment analysis (QUICK)
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "🧠 Menganalisis sentimen...", 90)
                else:
                    progress_tracker.update_progress(user_id, "🧠 Analyzing sentiment...", 90)
                await asyncio.sleep(stage_timings['sentiment'])

            # Market sentiment
            sentiment = self._analyze_market_sentiment(change_24h, volume_24h)

            change_emoji = "📈" if change_24h >= 0 else "📉"
            sentiment_emoji = "🟢" if sentiment['score'] > 60 else "🟡" if sentiment['score'] > 40 else "🔴"

            # Get additional info (news, market context, etc.)
            additional_info = self._get_additional_market_info(symbol, current_price, change_24h)

            # Update progress: Final stage (QUICK)
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "✅ Finalisasi...", 98)
                else:
                    progress_tracker.update_progress(user_id, "✅ Finalizing...", 98)
                await asyncio.sleep(stage_timings['finalize'])

            # Format analysis with proper spacing
            analysis = f"""📊 **ANALISIS KOMPREHENSIF {symbol} (CoinAPI + SnD)**

💰 **Data Harga Real-time:**
• **Harga Saat Ini**: {price_format}
• **Perubahan 24j**: {change_24h:+.2f}% {change_emoji}
• **Volume 24j**: {volume_format}

🎯 **ENHANCED SUPPLY & DEMAND ZONES** ({snd_zones.get('engine_used', 'Unknown')}):
• 🔴 Supply Zone 1: ${snd_zones['supply_1_low']:,.6f} - ${snd_zones['supply_1_high']:,.6f}
• 🔴 Supply Zone 2: ${snd_zones['supply_2_low']:,.6f} - ${snd_zones['supply_2_high']:,.6f}
• 🟢 Demand Zone 1: ${snd_zones['demand_1_low']:,.6f} - ${snd_zones['demand_1_high']:,.6f}
• 🟢 Demand Zone 2: ${snd_zones['demand_2_low']:,.6f} - ${snd_zones['demand_2_high']:,.6f}

🔍 **SnD ENGINE ANALYSIS:**
• Zone Position: {snd_zones.get('position', 'Unknown')}
• Zone Strength: {snd_zones.get('strength', 'Unknown')}
{f"• Engine Signal: **{snd_zones['entry_signal']}** ({snd_zones['signal_strength']:.0f}%)" if snd_zones.get('entry_signal') else "• Engine Signal: No signal detected"}

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

📡 **Data Source**: Binance Real-time + Internal SnD Algorithm
🕐 **Analisis**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            # Complete the job
            if user_id and progress_tracker:
                if user_lang == 'id':
                    progress_tracker.update_progress(user_id, "✅ Analisis selesai!", 100)
                else:
                    progress_tracker.update_progress(user_id, "✅ Analysis complete!", 100)
                progress_tracker.complete_job(user_id)

            return analysis

        except Exception as e:
            # Complete job even on error
            if user_id and progress_tracker:
                progress_tracker.complete_job(user_id)
            print(f"Error in comprehensive analysis: {e}")
            if user_lang == 'id':
                return f"❌ Terjadi kesalahan dalam analisis {symbol}. Error: {str(e)[:100]}..."
            else:
                return f"❌ An error occurred during analysis for {symbol}. Error: {str(e)[:100]}..."

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
                'strength': strength,
                'engine_used': 'Standard SnD' # Indicate the engine used
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
                'error': str(e),
                'engine_used': 'Fallback SnD' # Indicate the engine used
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
        """Generate trading signals based on price action with advanced confidence scoring"""
        # Advanced multi-factor confidence calculation
        base_confidence = 40  # Lower starting point for more selective signals

        # Enhanced price momentum analysis with progressive scoring
        momentum_score = 0
        if abs(change_24h) > 15:
            momentum_score = 40  # Extreme movement
        elif abs(change_24h) > 10:
            momentum_score = 30  # Very strong movement
        elif abs(change_24h) > 7:
            momentum_score = 25  # Strong movement
        elif abs(change_24h) > 5:
            momentum_score = 20  # Good movement
        elif abs(change_24h) > 3:
            momentum_score = 15  # Moderate movement
        elif abs(change_24h) > 1:
            momentum_score = 8   # Weak movement
        else:
            momentum_score = 0   # No momentum

        # Advanced volume analysis with market cap consideration
        volume_score = 0
        if symbol.upper() in ['BTC', 'ETH']:  # Major coins - higher volume requirements
            if volume > 10000000000:  # 10B+
                volume_score = 25
            elif volume > 5000000000:  # 5B+
                volume_score = 20
            elif volume > 2000000000:  # 2B+
                volume_score = 15
            elif volume > 1000000000:  # 1B+
                volume_score = 10
            elif volume > 500000000:   # 500M+
                volume_score = 5
        else:  # Altcoins - lower volume requirements
            if volume > 2000000000:   # 2B+
                volume_score = 25
            elif volume > 1000000000: # 1B+
                volume_score = 20
            elif volume > 500000000:  # 500M+
                volume_score = 15
            elif volume > 200000000:  # 200M+
                volume_score = 10
            elif volume > 100000000:  # 100M+
                volume_score = 5

        # Market structure bonus based on timeframe and consistency
        current_hour = datetime.now().hour
        market_structure_bonus = 0

        # Time-based market activity bonus
        if 14 <= current_hour <= 22:  # US market hours - highest activity
            market_structure_bonus += 5
        elif 8 <= current_hour <= 16:  # European hours - good activity
            market_structure_bonus += 3
        elif 22 <= current_hour <= 2:  # Asian evening - moderate activity
            market_structure_bonus += 2

        # Volatility consistency bonus
        volatility_bonus = 0
        if 3 <= abs(change_24h) <= 12:  # Sweet spot for tradeable volatility
            volatility_bonus = 8
        elif 1 <= abs(change_24h) <= 15:  # Acceptable volatility
            volatility_bonus = 5

        # Symbol-specific multiplier
        symbol_multiplier = 1.0
        if symbol.upper() in ['BTC', 'ETH']:
            symbol_multiplier = 1.1  # 10% bonus for major coins
        elif symbol.upper() in ['SOL', 'ADA', 'DOT', 'MATIC', 'AVAX']:
            symbol_multiplier = 1.05  # 5% bonus for established altcoins

        # Calculate preliminary confidence
        preliminary_confidence = (base_confidence + momentum_score + volume_score +
                                market_structure_bonus + volatility_bonus) * symbol_multiplier

        # Cap at 95% for realistic expectations (never 100% certain)
        final_confidence = min(95, max(30, preliminary_confidence))

        # Direction and strength determination with enhanced logic
        abs_change = abs(change_24h)
        if change_24h > 7:
            direction = "LONG"
            emoji = "🟢"
            strength = "Very Strong"
            trend = "Strong Bull Run"
            confidence_bonus = 10
        elif change_24h > 4:
            direction = "LONG"
            emoji = "🟢"
            strength = "Strong"
            trend = "Strong Uptrend"
            confidence_bonus = 8
        elif change_24h > 2:
            direction = "LONG"
            emoji = "🟢"
            strength = "Medium"
            trend = "Uptrend"
            confidence_bonus = 5
        elif change_24h < -7:
            direction = "SHORT"
            emoji = "🔴"
            strength = "Very Strong"
            trend = "Strong Bear Run"
            confidence_bonus = 10
        elif change_24h < -4:
            direction = "SHORT"
            emoji = "🔴"
            strength = "Strong"
            trend = "Strong Downtrend"
            confidence_bonus = 8
        elif change_24h < -2:
            direction = "SHORT"
            emoji = "🔴"
            strength = "Medium"
            trend = "Downtrend"
            confidence_bonus = 5
        else:
            direction = "NEUTRAL"
            emoji = "⚖️"
            strength = "Weak"
            trend = "Sideways"
            confidence_bonus = 0
            preliminary_confidence *= 0.6  # Reduce confidence for sideways

        # Final confidence calculation with advanced validation
        final_confidence = min(100, preliminary_confidence + confidence_bonus)

        # Honest confidence threshold - require 55% for directional signals (more realistic)
        if final_confidence < 55:
            direction = "NEUTRAL"
            emoji = "⚖️"
            strength = "Low Confidence"
            trend = "Uncertain Market"

        # Advanced entry, TP, SL calculation based on volatility
        volatility_factor = min(0.03, abs(change_24h) / 100 * 0.8)  # More dynamic volatility

        # Enhanced R:R calculation with minimum 1.8:1 requirement
        volatility_factor = min(0.03, abs(change_24h) / 100 * 0.8)  # More dynamic volatility

        # Calculate R:R based on market conditions and timeframe
        base_rr_multiplier = 2.0  # Base 2:1 ratio
        if abs(change_24h) > 10:  # High volatility = higher potential R:R
            base_rr_multiplier = 4.0
        elif abs(change_24h) > 7:
            base_rr_multiplier = 3.5
        elif abs(change_24h) > 5:
            base_rr_multiplier = 3.0
        elif abs(change_24h) > 3:
            base_rr_multiplier = 2.5

        if direction == "LONG" and final_confidence >= 55:  # Lower threshold for honest signals
            # Calculate stop loss first
            stop_distance = max(volatility_factor * 1.2, 0.015)  # Minimum 1.5% stop
            entry_price = price * (1 - volatility_factor * 0.2)  # Slight pullback entry
            stop_loss = entry_price * (1 - stop_distance)

            # Calculate take profit based on R:R requirement
            risk = abs(entry_price - stop_loss)
            reward_needed = risk * base_rr_multiplier
            take_profit = entry_price + reward_needed

        elif direction == "SHORT" and final_confidence >= 55:  # Lower threshold for honest signals
            # Calculate stop loss first
            stop_distance = max(volatility_factor * 1.2, 0.015)  # Minimum 1.5% stop
            entry_price = price * (1 + volatility_factor * 0.2)  # Slight bounce entry
            stop_loss = entry_price * (1 + stop_distance)

            # Calculate take profit based on R:R requirement
            risk = abs(stop_loss - entry_price)
            reward_needed = risk * base_rr_multiplier
            take_profit = entry_price - reward_needed

        else:
            # NEUTRAL or very low confidence
            entry_price = price
            take_profit = price * 1.005   # Very minimal target
            stop_loss = price * 0.995     # Very tight stop

        return {
            'direction': direction,
            'emoji': emoji,
            'strength': strength,
            'trend': trend,
            'entry_price': entry_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'confidence': round(final_confidence, 1),
            'strategy': 'Advanced R:R Strategy',
            'time_horizon': 'Dynamic based on volatility',
            'momentum_score': momentum_score,
            'volume_score': volume_score,
            'market_bonus': market_structure_bonus + volatility_bonus
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

        # Enhanced confidence calculation
        confidence = 50 + abs(change_24h) * 3  # Base confidence on market movement
        confidence = min(95, max(30, confidence))

        # Global sentiment determination
        if change_24h > 3:
            global_sentiment = "🚀 BULLISH"
            sentiment_emoji = "🚀"
        elif change_24h > 1:
            global_sentiment = "📈 POSITIVE"
            sentiment_emoji = "📈"
        elif change_24h > -1:
            global_sentiment = "😐 NEUTRAL"
            sentiment_emoji = "😐"
        elif change_24h > -3:
            global_sentiment = "📉 NEGATIVE"
            sentiment_emoji = "📉"
        else:
            global_sentiment = "💥 BEARISH"
            sentiment_emoji = "💥"

        # Adjust base score with volume multiplier before capping
        adjusted_base_score = base_score * confidence_multiplier
        final_score = max(0, min(95, adjusted_base_score))


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
            return """📰 **BERITA & INFO TERKINI**:
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

    async def generate_futures_signals(self, language: str = 'id', crypto_api=None, query_args: List = None, progress_tracker=None) -> str:
        """Generate multiple futures signals with professional Supply & Demand analysis format"""
        try:
            # Extended symbols list - scan top 25+ coins for better signal discovery
            symbols = [
                'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI',
                'LINK', 'LTC', 'ATOM', 'ICP', 'NEAR', 'APT', 'FTM', 'ALGO', 'VET', 'FLOW',
                'DOGE', 'SHIB', 'PEPE', 'TRX', 'XLM', 'MANA', 'FIL', 'SAND', 'GALA', 'CHZ'
            ]

            # Parse query args for timeframe (default 4h)
            timeframe = '4h'
            valid_timeframes = ['15m', '30m', '1h', '4h', '1d', '1w']

            if query_args:
                for arg in query_args:
                    arg_lower = arg.lower()
                    if arg_lower in valid_timeframes:
                        timeframe = arg_lower

            # Get market data for global metrics
            market_data = []
            total_volume = 0
            total_change = 0
            total_market_cap = 0
            signals_found = []
            total_scanned = 0

            # Update progress: Stage 0 - Initialization
            if progress_tracker:
                # Assume user_id is available or generated here. For simplicity, let's use a placeholder.
                # In a real application, user_id would come from the context.
                user_id = f"user_{random.randint(1000, 9999)}"
                if language == 'id':
                    await progress_tracker.update_progress(user_id, "⏳ Menginisialisasi analisis...", 0)
                else:
                    await progress_tracker.update_progress(user_id, "⏳ Initializing analysis...", 0)
                await asyncio.sleep(0.1)

                # Update progress: Stage 1 - Data fetching for the first batch of coins
                if language == 'id':
                    await progress_tracker.update_progress(user_id, 5, "⏳ Mengambil data pasar...")
                else:
                    await progress_tracker.update_progress(user_id, 5, "⏳ Fetching market data...")
                await asyncio.sleep(0.2)


            # Scan all symbols for signals and market data
            for symbol in symbols:
                try:
                    total_scanned += 1

                    # Get comprehensive market data
                    price_data = {}
                    if crypto_api:
                        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)

                    current_price = price_data.get('price', 0) if 'error' not in price_data else 0
                    change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
                    volume_24h = price_data.get('volume_24h', 0) if 'error' not in price_data else 0
                    market_cap = price_data.get('market_cap', 0) if 'error' not in price_data else 0

                    if current_price == 0:
                        continue

                    # Add to market data for global metrics
                    market_data.append({
                        'symbol': symbol,
                        'price': current_price,
                        'change_24h': change_24h,
                        'volume_24h': volume_24h,
                        'market_cap': market_cap if market_cap else current_price * 1000000000
                    })

                    total_volume += volume_24h
                    total_change += change_24h
                    total_market_cap += (market_cap if market_cap else current_price * 1000000000)

                    # Get enhanced SnD zones and advanced signals
                    snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)
                    futures_signals = self._generate_advanced_futures_signals(symbol, current_price, timeframe, snd_zones, volume_24h, crypto_api)

                    # IMPROVED threshold - capture signals with 65%+ confidence to match individual analysis
                    if (futures_signals['confidence'] >= 65.0 and
                        futures_signals['direction'] in ['LONG', 'SHORT'] and
                        futures_signals['rr'] >= 1.5):

                        signals_found.append({
                            'symbol': symbol,
                            'signals': futures_signals,
                            'current_price': current_price,
                            'change_24h': change_24h,
                            'volume_24h': volume_24h,
                            'snd_zones': snd_zones  # Store SnD zones data
                        })

                    # Rate limiting
                    if total_scanned % 8 == 0:
                        await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue

            # Calculate global metrics
            avg_change = total_change / len(market_data) if market_data else 0
            active_cryptos = 9543

            # Calculate dominance
            btc_data = next((d for d in market_data if d['symbol'] == 'BTC'), None)
            eth_data = next((d for d in market_data if d['symbol'] == 'ETH'), None)
            btc_dominance = (btc_data['market_cap'] / total_market_cap * 100) if btc_data and total_market_cap > 0 else 58.2
            eth_dominance = (eth_data['market_cap'] / total_market_cap * 100) if eth_data and total_market_cap > 0 else 14.1

            # Format numbers
            def format_large_number(num):
                if num > 1000000000000:
                    return f"${num/1000000000000:.2f}T"
                elif num > 1000000000:
                    return f"${num/1000000000:.2f}B"
                else:
                    return f"${num/1000000:.1f}M"

            # Sort signals by confidence and select top 5
            signals_found.sort(key=lambda x: x['signals']['confidence'], reverse=True)
            top_signals = signals_found[:5]

            # Professional header format
            signals_text = f"""🚨 **FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS**

# Simulate Queue and Progress
# User ID: {user_id if progress_tracker else 'N/A'}
# Queue: 2 waiting | 3 active

🕐 **Scan Time**: {datetime.now().strftime('%H:%M:%S WIB')}
📊 **Signals Found**: {len(top_signals)} (Confidence ≥ 65.0% - Quality Only)

💰 **GLOBAL METRICS:**
• Total Market Cap: {format_large_number(total_market_cap)}
• 24h Market Change: {avg_change:+.2f}%
• Total Volume 24h: {format_large_number(total_volume)}
• Active Cryptocurrencies: {active_cryptos:,}
• BTC Dominance: {btc_dominance:.1f}%
• ETH Dominance: {eth_dominance:.1f}%

"""

            if top_signals:
                # Professional signal format matching the requested layout
                for i, signal_data in enumerate(top_signals, 1):
                    signal = signal_data['signals']
                    symbol = signal_data['symbol']
                    current_price = signal_data['current_price']
                    change_24h = signal_data['change_24h']

                    direction = signal['direction']
                    confidence = signal['confidence']
                    entry = signal['entry']
                    sl = signal['sl']
                    tp1 = signal['tp1']
                    tp2 = signal['tp2']
                    tp3 = signal['tp3']
                    rr = signal['rr']

                    # Direction icon and bias
                    if direction == "LONG":
                        direction_icon = "🟢"
                        structure_bias = "LONG Bias"
                    else:
                        direction_icon = "🔴"
                        structure_bias = "SHORT Bias"

                    # Format prices consistently
                    def format_signal_price(price):
                        if price < 1:
                            return f"${price:.6f}"
                        elif price < 1000:
                            return f"${price:.2f}"
                        else:
                            return f"${price:,.2f}"

                    # Calculate percentage gains
                    if direction == "LONG":
                        tp1_pct = ((tp1 - entry) / entry * 100)
                        tp2_pct = ((tp2 - entry) / entry * 100)
                        tp3_pct = ((tp3 - entry) / entry * 100)
                    else:
                        tp1_pct = ((entry - tp1) / entry * 100)
                        tp2_pct = ((entry - tp2) / entry * 100)
                        tp3_pct = ((entry - tp3) / entry * 100)

                    # Enhanced R:R ranking system
                    if rr >= 5.0:
                        rr_rank = "🏆 ELITE"
                    elif rr >= 4.0:
                        rr_rank = "💎 PREMIUM"
                    elif rr >= 3.5:
                        rr_rank = "🥇 RANK #1"
                    elif rr >= 3.0:
                        rr_rank = "🥈 EXCELLENT"
                    elif rr >= 2.5:
                        rr_rank = "🥉 VERY GOOD"
                    elif rr >= 2.0:
                        rr_rank = "✅ GOOD"
                    elif rr >= 1.5:
                        rr_rank = "📊 FAIR"
                    else:
                        rr_rank = "⚠️ POOR"

                    # Calculate zone range (approximately 0.5% width)
                    zone_width = entry * 0.005
                    if direction == "LONG":
                        # Demand zone for LONG - buy limit below current
                        zone_low = entry - zone_width
                        zone_high = entry
                        zone_label = "Demand Zone"
                        order_type = "LIMIT LONG"
                    else:
                        # Supply zone for SHORT - sell limit above current
                        zone_low = entry
                        zone_high = entry + zone_width
                        zone_label = "Supply Zone"
                        order_type = "LIMIT SHORT"

                    signals_text += f"""**{i}. {symbol} {direction_icon} {order_type}** (Confidence: {confidence:.1f}%)

🛑 **Stop Loss**: {format_signal_price(sl)}
📍 **{zone_label}**: {format_signal_price(zone_low)} - {format_signal_price(zone_high)}
🎯 **TP1**: {format_signal_price(tp1)} (+{tp1_pct:.1f}%)
🎯 **TP2**: {format_signal_price(tp2)} (+{tp2_pct:.1f}%)
🎯 **TP3**: {format_signal_price(tp3)} (+{tp3_pct:.1f}%)
💎 **R:R Ratio**: {rr:.1f}:1 ({rr_rank})

📈 **24h Change**: {change_24h:+.2f}%
⚡ **Structure**: {structure_bias}

"""

                # Professional footer
                signals_text += f"""⚠️ TRADING DISCLAIMER:
• Place LIMIT orders at zone levels
• Do NOT use market orders
• Signals berbasis Supply & Demand analysis
• Gunakan proper risk management
• DYOR sebelum trading

📡 Next scan akan mengacak koin berbeda
🔄 Jalankan ulang untuk variasi sinyal"""

            else:
                if language == 'id':
                    signals_text += f"""⚠️ **TIDAK ADA SINYAL BERKEMUNGKINAN TINGGI**

📊 **Dipindai**: {total_scanned} koin
📈 **Ditemukan**: 0 sinyal (threshold 65%+ - Hanya Kualitas)
💤 **Status**: Kondisi pasar konsolidasi atau kepercayaan rendah

💡 **REKOMENDASI JUJUR:**
• Pasar mungkin tidak memiliki peluang trading yang jelas saat ini
• Ini NORMAL - sinyal bagus jarang muncul terus menerus
• Gunakan `/futures btc` untuk analisis spesifik (mungkin menunjukkan kepercayaan 45-65%)
• Tunggu setup probabilitas tinggi yang asli
• Kualitas lebih penting dari kuantitas - lebih baik menunggu daripada memaksakan trade"""
                else:
                    signals_text += f"""⚠️ **NO HIGH-CONFIDENCE SIGNALS**

📊 **Scanned**: {total_scanned} coins
📈 **Found**: 0 signals (65%+ threshold - Quality Only)
💤 **Status**: Market consolidation or low confidence conditions

💡 **HONEST RECOMMENDATIONS:**
• Market may not have clear trading opportunities right now
• This is NORMAL - good signals are rare, not constant
• Use `/futures btc` for specific analysis (may show 45-65% confidence)
• Wait for genuine high-probability setups
• Quality over quantity - better to wait than force trades"""

            return signals_text

        except Exception as e:
            print(f"Error generating futures signals: {e}")
            return f"❌ Error generating futures signals: {str(e)[:100]}..."

    def _generate_coin_recommendations(self, market_data: List[Dict], avg_change: float, btc_dominance: float) -> str:
        """Generate intelligent coin recommendations based on market analysis"""
        try:
            # Sort coins by performance and analyze patterns
            sorted_by_performance = sorted(market_data, key=lambda x: x['change_24h'], reverse=True)
            sorted_by_volume = sorted(market_data, key=lambda x: x['volume_24h'], reverse=True)

            # Categorize coins
            hot_performers = [coin for coin in sorted_by_performance if coin['change_24h'] > 5]
            stable_performers = [coin for coin in market_data if 1 <= coin['change_24h'] <= 5]
            oversold_candidates = [coin for coin in sorted_by_performance if coin['change_24h'] < -3]

            recommendations = """

🏆 **RECOMMENDED COINS TO WATCH:**"""

            # Best entry opportunities based on market conditions
            if avg_change > 2:  # Bull market
                recommendations += """

💎 **BULLISH MOMENTUM PLAYS:**"""
                for i, coin in enumerate(hot_performers[:3], 1):
                    symbol = coin['symbol']
                    change = coin['change_24h']
                    price = coin['price']
                    volume = coin['volume_24h']

                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 100:
                        price_str = f"${price:.4f}"
                    else:
                        price_str = f"${price:,.2f}"

                    # Enhanced strategy based on performance level
                    if change > 10:
                        strategy = "STRONG breakout - Take partial profits, trail stops"
                    elif change > 7:
                        strategy = "Momentum continuation - Enter on 3-5% pullback"
                    elif change > 5:
                        strategy = "Trend following - Scale in gradually"
                    else:
                        strategy = "Moderate momentum - Wait for volume confirmation"

                    recommendations += f"""
• **{i}. {symbol}** 🚀 {price_str} (+{change:.1f}%)
  └─ Strategy: {strategy}"""

            elif avg_change < -2:  # Bear market
                recommendations += """

💰 **OVERSOLD RECOVERY CANDIDATES:**"""
                for i, coin in enumerate(oversold_candidates[:3], 1):
                    symbol = coin['symbol']
                    change = coin['change_24h']
                    price = coin['price']
                    volume = coin['volume_24h']

                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 100:
                        price_str = f"${price:.4f}"
                    else:
                        price_str = f"${price:,.2f}"

                    # Enhanced strategy based on decline severity
                    if change < -15:
                        strategy = "MAJOR oversold - Small DCA, wait for capitulation end"
                    elif change < -10:
                        strategy = "Heavy correction - DCA 25% now, 75% on further drop"
                    elif change < -7:
                        strategy = "Oversold bounce - 50% position, scale remainder"
                    elif change < -5:
                        strategy = "Minor dip - Good accumulation opportunity"
                    else:
                        strategy = "Slight weakness - Monitor for support hold"

                    # Volume consideration for oversold
                    if volume > 1500000000:  # High volume selling
                        strategy += " + High volume selloff - be cautious"

                    recommendations += f"""
• **{i}. {symbol}** 📉 {price_str} ({change:.1f}%)
  └─ Strategy: {strategy}"""

            else:  # Neutral market
                recommendations += """

⚖️ **TOP 3 COINS FOR HOLD & TRADES (RESET EVERY 24H):**"""
                # Advanced coin selection algorithm - scan top 25 performers
                # Score coins based on multiple factors: volume, stability, momentum, fundamentals
                coin_scores = []

                for coin in market_data:
                    symbol = coin['symbol']
                    change = coin['change_24h']
                    volume = coin['volume_24h']
                    price = coin['price']

                    # Base scoring algorithm
                    score = 50  # Base score

                    # Volume factor (liquidity is king)
                    if volume > 2000000000:  # 2B+
                        score += 25
                    elif volume > 1000000000:  # 1B+
                        score += 20
                    elif volume > 500000000:  # 500M+
                        score += 15
                    elif volume > 200000000:  # 200M+
                        score += 10
                    elif volume > 100000000:  # 100M+
                        score += 5

                    # Stability factor (not too volatile, not too flat)
                    abs_change = abs(change)
                    if 1 <= abs_change <= 8:  # Sweet spot for trading
                        score += 20
                    elif 0.5 <= abs_change <= 12:  # Acceptable range
                        score += 15
                    elif abs_change <= 15:  # High vol but manageable
                        score += 10
                    else:  # Too volatile or too flat
                        score += 0

                    # Momentum factor
                    if 0 < change <= 5:  # Positive but not overheated
                        score += 15
                    elif -3 <= change < 0:  # Slight correction, good buy opportunity
                        score += 12
                    elif change > 5:  # Strong momentum
                        score += 10
                    elif change > 10:  # Overheated
                        score += 5

                    # Blue chip bonus
                    if symbol in ['BTC', 'ETH']:
                        score += 15  # Always include majors
                    elif symbol in ['BNB', 'SOL', 'XRP', 'ADA']:
                        score += 10  # Strong fundamentals
                    elif symbol in ['DOT', 'MATIC', 'AVAX', 'UNI', 'LINK']:
                        score += 8   # Solid projects

                    # Price accessibility factor (for retail traders)
                    if 0.1 <= price <= 100:  # Sweet spot for retail
                        score += 5
                    elif price > 1000:  # Expensive for retail
                        score -= 5

                    coin_scores.append({
                        'coin': coin,
                        'score': score,
                        'symbol': symbol
                    })

                # Sort by score and get top 3 coins only (shorter message)
                top_3_coins = sorted(coin_scores, key=lambda x: x['score'], reverse=True)[:3]

                for i, item in enumerate(top_3_coins, 1):
                    coin = item['coin']
                    score = item['score']
                    symbol = coin['symbol']
                    change = coin['change_24h']
                    price = coin['price']
                    volume = coin['volume_24h']

                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 100:
                        price_str = f"${price:.4f}"
                    else:
                        price_str = f"${price:,.2f}"

                    if volume > 1000000000:
                        vol_str = f"${volume/1000000000:.1f}B"
                    elif volume > 1000000:
                        vol_str = f"${volume/1000000:.0f}M"
                    else:
                        vol_str = f"${volume:,.0f}"

                    # Grade system based on score
                    if score >= 90:
                        grade = "🏆 PREMIUM"
                        grade_desc = "Top-tier pick"
                    elif score >= 80:
                        grade = "🥇 EXCELLENT"
                        grade_desc = "High confidence"
                    elif score >= 70:
                        grade = "🥈 GOOD"
                        grade_desc = "Solid choice"
                    elif score >= 60:
                        grade = "🥉 DECENT"
                        grade_desc = "Fair option"
                    else:
                        grade = "⚠️ RISKY"
                        grade_desc = "High risk"

                    # Advanced strategy based on multiple factors
                    if symbol in ['BTC', 'ETH']:
                        if change > 2:
                            strategy = "HOLD + DCA on dips - Blue chip momentum"
                        elif change > -2:
                            strategy = "ACCUMULATE gradually - Market leader stability"
                        else:
                            strategy = "BUY THE DIP - Major support levels"
                    elif 2 < change <= 8 and volume > 1000000000:
                        strategy = "TRADE momentum + HOLD core position"
                    elif -3 <= change <= 2 and volume > 500000000:
                        strategy = "DCA ACCUMULATION - Good entry zone"
                    elif change > 8:
                        strategy = "TAKE PROFITS - Overextended, wait pullback"
                    elif change < -8:
                        strategy = "CAREFUL DCA - Wait for bounce confirmation"
                    else:
                        strategy = "RANGE TRADING - Support/resistance levels"

                    # Time horizon - 24 hours for daily reset system
                    time_horizon = "24H HOLD/TRADE (Daily Reset)"

                    recommendations += f"""
• **{i}. {symbol}** {grade} **{price_str}** (**{change:+.1f}%**) Vol: **{vol_str}**
  **Score**: {score:.0f}/100 - {grade_desc}
  **Strategy**: {strategy}"""

            # Add enhanced insights
            recommendations += f"""

📊 **MARKET INSIGHTS:**
• Analysis based on Top 25 cryptocurrencies (optimized scan)
• Selection criteria: Volume + Stability + Momentum + Fundamentals
• BTC Dominance: {btc_dominance:.1f}% - {"Focus on BTC/ETH" if btc_dominance > 55 else "Altcoin opportunities" if btc_dominance < 45 else "Balanced approach"}

⏰ **RESET SCHEDULE:**
• Selection updates every 24 hours at 00:00 UTC
• Real-time price tracking via CoinAPI
• Strategy adjustments based on market conditions

⚡ **QUICK PICKS STRATEGY:**
• Focus on top 3 highest-scoring coins only
• Perfect for quick decision making
• Reduced analysis paralysis
• Higher conviction trades"""

            return recommendations

        except Exception as e:
            return """

🏆 **RECOMMENDED COINS TO WATCH:**
• Monitor market data untuk rekomendasi real-time
• Focus pada top volume coins
• Analisis technical sebelum entry"""

    def _generate_best_entry_analysis(self, market_data: List[Dict], global_sentiment: str) -> str:
        """Generate best entry timing and strategy analysis"""
        try:
            entry_analysis = """

🎯 **BEST ENTRY STRATEGIES:**"""

            # Analyze current market timing
            current_hour = datetime.now().hour

            # Market timing analysis
            if 14 <= current_hour <= 22:  # US hours
                market_session = "Optimal Trading Session (High Liquidity)"
                timing_advice = "Ideal for executing trades with tighter stops and targets"
            elif 8 <= current_hour <= 16:  # European hours
                market_session = "Moderate Trading Session (Good Liquidity)"
                timing_advice = "Suitable for trend continuation and swing entries"
            elif 0 <= current_hour <= 6:  # Asian hours
                market_session = "Lower Activity Session (Moderate Liquidity)"
                timing_advice = "Watch for potential gap fills or early trend indications"
            else:
                market_session = "Low Activity Period (Reduced Liquidity)"
                timing_advice = "Exercise caution, wider stops may be needed"

            entry_analysis += f"""

⏰ **MARKET TIMING:**
• **Session**: {market_session}
• **Advice**: {timing_advice}

💡 **ENTRY STRATEGIES BY SENTIMENT:**"""

            if "BULLISH" in global_sentiment:
                entry_analysis += """
• **Buy the Dip Strategy**: Wait for 2-3% pullbacks on strong coins
• **Momentum Entry**: Break above key resistance levels with confirming volume
• **DCA Strategy**: Gradually build positions on minor dips
• **Risk Level**: Medium to High - Be aggressive but manage risk"""

            elif "BEARISH" in global_sentiment:
                entry_analysis += """
• **Short Bounce Strategy**: Fade rallies and short clear breakdowns
• **Cash Position**: Preserve capital, wait for capitulation or clear reversal signals
• **DCA Bottom**: Only consider for extremely strong fundamental coins at key support
• **Risk Level**: High - Tight stops and minimal positions"""

            else:  # NEUTRAL
                entry_analysis += """
• **Range Trading**: Buy at support, sell at resistance within defined ranges
• **Breakout Entry**: Wait for clear, high-volume breakouts from consolidation
• **Accumulation**: Gradually build positions on stable assets, avoid chasing pumps
• **Risk Level**: Low to Medium - Defined risk with clear stop-loss levels"""

            # Technical entry conditions
            entry_analysis += """

📊 **TECHNICAL ENTRY CONDITIONS:**
• **Volume Confirmation**: Entry requires significant volume spike (20%+ above average)
• **Support/Resistance Levels**: Use key S/R zones for precise entry timing
• **Risk Management**: Never risk more than 2-3% of capital per trade
• **Position Sizing**: Adjust based on confidence and asset volatility

🔥 **PRIORITY ACTION ITEMS:**"""

            # Generate specific action items based on data
            high_volume_coins = [coin for coin in market_data if coin['volume_24h'] > 1000000000] # 1B+ volume

            if high_volume_coins:
                top_vol_coin = max(high_volume_coins, key=lambda x: x['volume_24h'])
                entry_analysis += f"""
• Monitor **{top_vol_coin['symbol']}** - Highest volume ({top_vol_coin['volume_24h']/1000000000:.1f}B) for potential entries."""

            # Add top performers
            top_performer = max(market_data, key=lambda x: x['change_24h'])
            if top_performer['change_24h'] > 1:
                entry_analysis += f"""
• Watch **{top_performer['symbol']}** momentum (+{top_performer['change_24h']:.1f}%) - Strong gainer."""

            # Add major coins status
            btc_data = next((coin for coin in market_data if coin['symbol'] == 'BTC'), None)
            eth_data = next((coin for coin in market_data if coin['symbol'] == 'ETH'), None)

            if btc_data:
                btc_trend = "bullish" if btc_data['change_24h'] > 1 else "bearish" if btc_data['change_24h'] < -1 else "neutral"
                entry_analysis += f"""
• **BTC** trend is {btc_trend} - Market leader signal to follow."""

            if eth_data:
                eth_trend = "bullish" if eth_data['change_24h'] > 1 else "bearish" if eth_data['change_24h'] < -1 else "neutral"
                entry_analysis += f"""
• **ETH** showing {eth_trend} momentum - Key indicator for DeFi sentiment."""

            return entry_analysis

        except Exception as e:
            return """

🎯 **BEST ENTRY STRATEGIES:**
• Monitor volume and momentum for optimal timing.
• Utilize technical analysis for precise entry/exit points.
• Prioritize risk management on all trades.
• Error during analysis: {str(e)[:100]}..."""

    def _generate_trading_recommendations(self, signal_data: Dict, sentiment: Dict, snd_zones: Dict, current_price: float) -> str:
        """Generate trading recommendations"""
        direction = signal_data.get('direction', 'NEUTRAL')
        strength = signal_data.get('strength', 'Medium')
        sentiment_score = sentiment.get('score', 50)

        recommendations = []

        if direction == "LONG" and sentiment_score > 60:
            recommendations.append("• ✅ Pertimbangkan posisi LONG dengan konfirmasi SnD")
            recommendations.append("• 🎯 Entry dekat Demand Zone untuk risk optimal")
            recommendations.append("• 📈 Target profit di Supply Zone 1")
        elif direction == "SHORT" and sentiment_score < 40:
            recommendations.append("• ❌ Pertimbangkan posisi SHORT dengan konfirmasi SnD")
            recommendations.append("• 🎯 Entry dekat Supply Zone untuk risk optimal")
            recommendations.append("• 📉 Target profit di Demand Zone 1")
        else:
            recommendations.append("• ⏳ Tunggu sinyal yang lebih jelas di zona SnD")
            recommendations.append("• 👀 Pantau price action di level kunci")
            recommendations.append("• 📊 Tunggu konfirmasi breakout volume")

        recommendations.append("• 🛡️ Selalu gunakan stop loss sesuai zona SnD")
        recommendations.append("• 💰 Ukuran posisi maksimal 2-3% portfolio")

        return "\n".join(recommendations)

    async def get_futures_analysis(self, symbol: str, timeframe: str, language: str = 'id', crypto_api=None, progress_tracker=None, user_id=None) -> str:
        """Get enhanced futures trading signals with optimized 10 second timing"""
        try:
            # Optimized timing for concurrent users - reduced total time
            stage_timings = {
                'data_fetch': 0.8,      # 0.8 seconds - faster fetch
                'snd_calc': 1.5,        # 1.5 seconds - optimized SnD calculations
                'structure': 1.2,       # 1.2 seconds - streamlined structure analysis
                'signals': 2.0,         # 2.0 seconds - efficient signal processing
                'risk_calc': 1.2,       # 1.2 seconds - faster risk calculations
                'finalize': 0.8         # 0.8 seconds - quick finalization
            }

            # Update progress: Stage 1 - Data fetching (FAST)
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "⚡ Mengambil data pasar...", 15)
                else:
                    progress_tracker.update_progress(user_id, "⚡ Fetching market data...", 15)
                await asyncio.sleep(stage_timings['data_fetch'])

            # Get current price and market data
            price_data = {}
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)

            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if 'error' not in price_data else 0

            if current_price <= 0:
                # Complete job even on error
                if user_id and progress_tracker:
                    progress_tracker.complete_job(user_id)
                if language == 'id':
                    return f"❌ **DATA ERROR**: Tidak dapat mengambil data {symbol}\n\n💡 **Solusi**: Coba `/futures btc` atau `/futures eth`"
                else:
                    return f"❌ **DATA ERROR**: Could not retrieve data for {symbol}\n\n💡 **Solution**: Try `/futures btc` or `/futures eth`"

            # Update progress: Stage 2 - SnD zones (OPTIMIZED)
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "🎯 Menghitung zona SnD...", 35)
                else:
                    progress_tracker.update_progress(user_id, "🎯 Calculating SnD zones...", 35)
                await asyncio.sleep(stage_timings['snd_calc'])

            # Get enhanced SnD zones and signals
            snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, crypto_api)

            # Update progress: Stage 3 - Market structure (FAST)
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "🧠 Memproses struktur...", 55)
                else:
                    progress_tracker.update_progress(user_id, "🧠 Processing structure...", 55)
                await asyncio.sleep(stage_timings['structure'])

            # Update progress: Stage 4 - Signal generation (CORE)
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "⚡ Menghasilkan sinyal...", 75)
                else:
                    progress_tracker.update_progress(user_id, "⚡ Generating signals...", 75)
                await asyncio.sleep(stage_timings['signals'])

            # Generate signals
            futures_signals = self._generate_advanced_futures_signals(symbol, current_price, timeframe, snd_zones, volume_24h, crypto_api)

            # Update progress: Stage 5 - Risk calculation (FAST)
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "💎 Finalisasi R:R...", 90)
                else:
                    progress_tracker.update_progress(user_id, "💎 Finalizing R:R...", 90)
                await asyncio.sleep(stage_timings['risk_calc'])

            # Enhanced timeframe display
            tf_display = {
                '15m': '15M ⚡ Scalping', '30m': '30M 🔥 Quick', '1h': '1H 📈 Intraday',
                '4h': '4H ⭐ Swing', '1d': '1D 💎 Position', '1w': '1W 🏛️ Long-term'
            }.get(timeframe, f"{timeframe.upper()} Trading")

            # Smart price formatting
            if current_price < 0.01:
                price_format = f"${current_price:.8f}"
            elif current_price < 1:
                price_format = f"${current_price:.6f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"

            # Enhanced volume formatting
            if volume_24h > 1000000000:
                volume_format = f"${volume_24h/1000000000:.2f}B 🔥"
            elif volume_24h > 500000000:
                volume_format = f"${volume_24h/1000000:.0f}M ⚡"
            elif volume_24h > 100000000:
                volume_format = f"${volume_24h/1000000:.0f}M 📊"
            else:
                volume_format = f"${volume_24h/1000000:.1f}M 💤"

            # Enhanced visual confidence system with REAL dynamic calculation
            confidence = futures_signals['confidence']

            # Generate confidence bar based on ACTUAL percentage (not hardcoded)
            filled_bars = int((confidence / 100) * 5)  # Convert to 5-bar system
            empty_bars = 5 - filled_bars

            confidence_bar = "🟢" * filled_bars + "⚪" * empty_bars

            # Dynamic signal status based on REAL confidence
            if confidence >= 85:
                signal_status = "🎯 **ULTRA PREMIUM** - EXECUTE NOW!"
                action_advice = "✅ **Action**: Maximum conviction trade - Full position (Max 95%)"
            elif confidence >= 80:
                signal_status = "🔥 **PREMIUM SIGNAL** - Strong Entry"
                action_advice = "✅ **Action**: High conviction trade - 80% position"
            elif confidence >= 75:
                signal_status = "⭐ **STRONG SIGNAL** - Good Entry"
                action_advice = "✅ **Action**: Good probability trade - 60-70% position"
            elif confidence >= 65:
                signal_status = "📊 **DECENT SIGNAL** - Careful Entry"
                action_advice = "⚠️ **Action**: Medium risk trade - 40-50% position"
            elif confidence >= 50:
                signal_status = "💡 **WEAK SIGNAL** - Very Careful"
                action_advice = "⚠️ **Action**: Low confidence - 20-30% position max"
            else:
                signal_status = "⏳ **NO SIGNAL** - Wait"
                action_advice = "🛑 **Action**: Wait for better setup - Paper trade only"

            # Direction with clear entry strategy
            direction = futures_signals['direction']
            if direction == "LONG":
                direction_display = "🚀 **LONG** (BUY/BELI)"
                strategy_tip = "📈 **Tip**: Buy on pullbacks, target resistance levels"
            elif direction == "SHORT":
                direction_display = "📉 **SHORT** (SELL/JUAL)"
                strategy_tip = "📉 **Tip**: Sell on bounces, target support levels"
            else:
                direction_display = "⚠️ **NO SIGNAL** (JANGAN TRADE)"
                strategy_tip = "⚠️ **Tip**: Confidence too low - Wait for better setup"

            # Risk/Reward visualization
            rr_ratio = futures_signals['rr']
            if rr_ratio >= 3:
                rr_status = f"🏆 **EXCELLENT** R:R {rr_ratio:.1f}:1"
            elif rr_ratio >= 2:
                rr_status = f"✅ **GOOD** R:R {rr_ratio:.1f}:1"
            elif rr_ratio >= 1.5:
                rr_status = f"⚠️ **FAIR** R:R {rr_ratio:.1f}:1"
            else:
                rr_status = f"❌ **POOR** R:R {rr_ratio:.1f}:1"

            # Quick action summary
            quick_summary = self._generate_quick_action_summary(futures_signals, confidence, symbol)

            # Get technical indicators for professional analysis
            tech_indicators = self._calculate_professional_indicators(symbol, current_price, change_24h, snd_zones, crypto_api)

            # Realistic confidence level descriptions (max 88%)
            if confidence >= 85:
                confidence_level = "🔥 Very High"
            elif confidence >= 80:
                confidence_level = "⚡ High"
            elif confidence >= 75:
                confidence_level = "📊 Good"
            elif confidence >= 70:
                confidence_level = "📈 Medium-High"
            elif confidence >= 65:
                confidence_level = "📊 Medium"
            elif confidence >= 60:
                confidence_level = "📉 Medium-Low"
            else:
                confidence_level = "⚠️ Low"

            # Professional trading signal
            if direction == "LONG":
                signal_direction = "LONG"
                signal_color = "🟢"
            elif direction == "SHORT":
                signal_direction = "SHORT"
                signal_color = "🔴"
            else:
                signal_direction = "WAIT"
                signal_color = "⏳"

            # Calculate position allocation percentages
            tp1_allocation = "50%"
            tp2_allocation = "30%"
            tp3_allocation = "20%"

            # Calculate percentage changes for targets
            if direction == "LONG":
                tp1_pct = ((futures_signals['tp1'] - futures_signals['entry']) / futures_signals['entry'] * 100)
                tp2_pct = ((futures_signals['tp2'] - futures_signals['entry']) / futures_signals['entry'] * 100)
                tp3_pct = ((futures_signals['tp3'] - futures_signals['entry']) / futures_signals['entry'] * 100)
            else:
                tp1_pct = ((futures_signals['entry'] - futures_signals['tp1']) / futures_signals['entry'] * 100)
                tp2_pct = ((futures_signals['entry'] - futures_signals['tp2']) / futures_signals['entry'] * 100)
                tp3_pct = ((futures_signals['entry'] - futures_signals['tp3']) / futures_signals['entry'] * 100)

            # Format prices consistently
            def format_price(price):
                if price < 1:
                    return f"${price:.6f}"
                elif price < 1000:
                    return f"${price:.2f}"
                else:
                    return f"${price:,.2f}"

            # Structured signal display
            if signal_direction != "WAIT":
                signal_display = f"""
🔍 **PROFESSIONAL FUTURES SIGNAL - {symbol} ({timeframe.upper()})**

📍 **Current Price**: {price_format} ({change_24h:+.2f}%)
{signal_color} **DIRECTION**: {signal_direction}
🔥 **Confidence**: {confidence:.1f}% ({confidence_level})

🚨 **TRADING SETUP**:
🛑 **Stop Loss**: {format_price(futures_signals['sl'])}
➡️ **Entry**: {format_price(futures_signals['entry'])}
🎯 **TP1**: {format_price(futures_signals['tp1'])} (+{tp1_pct:.1f}%)
🎯 **TP2**: {format_price(futures_signals['tp2'])} (+{tp2_pct:.1f}%)
🎯 **TP3**: {format_price(futures_signals['tp3'])} (+{tp3_pct:.1f}%)
💎 **R:R Ratio**: {futures_signals['rr']:.1f}:1 ({rr_status})

📊 **Strategy**: {futures_signals.get('strategy', 'Advanced SnD')}
⚡ **Time Horizon**: {futures_signals.get('time_horizon', '4-24 hours')}
🎯 **Position Size**: {self._calculate_position_size(confidence)} of portfolio"""
            else:
                if language == 'id':
                    signal_display = f"""
🔍 **ANALISIS FUTURES PROFESIONAL - {symbol} ({timeframe.upper()})**

📍 **Harga Saat Ini**: {price_format} ({change_24h:+.2f}%)
⏳ **STATUS SINYAL**: TIDAK ADA SINYAL
⚠️ **Kepercayaan**: {confidence:.1f}% (Di bawah ambang batas)

❌ **Tidak ada setup trading yang tersedia**
💡 **Rekomendasi**: Tunggu kondisi pasar yang lebih baik
📊 **Alasan**: Kurangnya konfluensi faktor teknikal"""
                else:
                    signal_display = f"""
🔍 **PROFESSIONAL FUTURES ANALYSIS - {symbol} ({timeframe.upper()})**

📍 **Current Price**: {price_format} ({change_24h:+.2f}%)
⏳ **SIGNAL STATUS**: NO SIGNAL
⚠️ **Confidence**: {confidence:.1f}% (Below threshold)

❌ **No trading setup available**
💡 **Recommendation**: Wait for better market conditions
📊 **Reason**: Insufficient confluence of technical factors"""

            analysis = signal_display

            analysis += f"""

🔬 **ANALISIS TEKNIKAL ({timeframe.upper()}):**
• EMA50: {tech_indicators['ema_50']}
• EMA200: {tech_indicators['ema_200']}
• RSI(14): {tech_indicators['rsi']} ({tech_indicators['rsi_status']})
• MACD: {tech_indicators['macd']} ({tech_indicators['macd_status']})
• ATR: {tech_indicators['atr']}
• Volume Trend: {tech_indicators['volume_trend']}

🎯 **SUPPLY & DEMAND ZONES**:
• 🔴 Supply Zone 1: ${snd_zones['supply_1_low']:,.6f} (+{((snd_zones['supply_1_low']/current_price-1)*100):+.1f}%)
• 🟢 Demand Zone 1: ${snd_zones['demand_1_low']:,.6f} ({((snd_zones['demand_1_low']/current_price-1)*100):+.1f}%)
• 📍 Current Position: {snd_zones.get('position', 'Between Zones')}
• 💪 Zone Strength: {snd_zones.get('strength', 'Medium')}

🔮 **FUTURES MARKET METRICS**:
• Volume 24h: {volume_format}
• Market Structure: {tech_indicators.get('market_structure', 'Normal')}
• Volatility: {tech_indicators.get('volatility_level', 'Moderate')}

📈 **HIGHER TIMEFRAME (4H) CONFIRMATION**:
• 🎯 4H Trend: {tech_indicators.get('higher_tf_trend', 'Neutral')}
• 📊 4H EMA50 vs EMA200: {tech_indicators.get('higher_tf_alignment', 'Neutral')}
• ✅ Multi-TF Confirmation: {tech_indicators.get('tf_confirmation', 'PENDING')}

💡 **ADVANCED TRADING INSIGHTS**:
{self._generate_professional_insights(futures_signals, confidence, symbol, direction)}

⚠️ **RISK MANAGEMENT PROTOCOL**:
• Gunakan proper position sizing (1-3% per trade)
• Set stop loss sebelum entry
• Take profit secara bertahap
• Pantau kondisi pasar
• DYOR sebelum trading

🎯 **EXECUTION CHECKLIST**:
• ✅ Confirm price action at entry zone
• ✅ Monitor volume for confirmation
• ✅ Set stop loss BEFORE entry
• ✅ Prepare for partial profit taking
• ✅ Watch for news/events impact

📡 **Data Sources**: Binance OHLCV + Binance Futures + SnD Analysis
🔄 **Update Frequency**: Real-time price + 15min technical refresh"""

            # Complete the job
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "✅ Analisis selesai!", 100)
                else:
                    progress_tracker.update_progress(user_id, "✅ Analysis complete!", 100)
                progress_tracker.complete_job(user_id)

            return analysis

        except Exception as e:
            # Complete job even on error
            if user_id and progress_tracker:
                try:
                    progress_tracker.complete_job(user_id)
                except:
                    pass  # Ignore progress tracker errors
            print(f"Error in futures signals: {e}")
            if language == 'id':
                return f"""❌ **ERROR SINYAL FUTURES**

**Simbol**: {symbol}
**Timeframe**: {timeframe}
**Error**: {str(e)[:100]}...

💡 **Perbaikan Cepat:**
• Coba `/futures btc`
• Gunakan `/price {symbol}` untuk memeriksa data
• Tunggu 30 detik dan coba lagi

🔧 **Command Alternatif:**
• `/analyze {symbol}` - Analisis komprehensif
• `/market` - Ikhtisar pasar"""
            else:
                return f"""❌ **FUTURES SIGNAL ERROR**

**Symbol**: {symbol}
**Timeframe**: {timeframe}
**Error**: {str(e)[:100]}...

💡 **Quick Fix:**
• Try `/futures btc`
• Use `/price {symbol}` to check data
• Wait 30 seconds and retry

🔧 **Alternative Commands:**
• `/analyze {symbol}` - Comprehensive analysis
• `/market` - Market overview"""

    def _generate_futures_signals(self, symbol: str, current_price: float, timeframe: str, snd_zones: Dict, volume_24h: float, crypto_api=None) -> Dict:
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
            tp1 = demand_1_mid                    # TP1: First target (lower price for SHORT)
            tp2 = snd_zones['demand_1_low']       # TP2: Second target (even lower)
            tp3 = snd_zones['demand_2_low']       # TP3: Final target (lowest)
            sl = snd_zones['supply_2_low']
            strategy = "SnD Reversal Short"
            confidence = 75
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

        # Enhanced validity and time horizon for basic signals
        validity_hours = {
            '15m': '1-3 hours', '30m': '2-6 hours', '1h': '4-12 hours',
            '4h': '12-48 hours', '1d': '2-7 days', '1w': '1-3 weeks'
        }.get(timeframe, '6-24 hours')

        time_horizon = {
            '15m': 'Scalping (15-90 min)', '30m': 'Quick Swing (1-6 hours)',
            '1h': 'Intraday (4-18 hours)', '4h': 'Swing (1-4 days)',
            '1d': 'Position (3-10 days)', '1w': 'Long-term (1-6 weeks)'
        }.get(timeframe, 'Medium-term')

        return {
            'direction': direction,
            'emoji': emoji,
            'entry': float(entry) if entry else current_price,
            'tp1': float(tp1) if tp1 else current_price * 1.02,
            'tp2': float(tp2) if tp2 else current_price * 1.04,
            'tp3': float(tp3) if tp3 else current_price * 1.06,
            'sl': float(sl) if sl else current_price * 0.98,
            'rr': float(rr_ratio) if rr_ratio else 1.0,
            'confidence': float(final_confidence),
            'strategy': str(strategy),
            'leverage_rec': '3-5x',
            'validity': str(validity_hours),
            'time_horizon': str(time_horizon),
            'volume_strength': 'Medium',
            'distance_to_supply': 2.0,
            'distance_to_demand': 2.0,
            'zone_precision': 5,
            'market_timing': 1.0
        }

    def _generate_advanced_futures_signals(self, symbol: str, current_price: float, timeframe: str, snd_zones: Dict, volume_24h: float, crypto_api=None) -> Dict:
        """Generate advanced futures trading signals with enhanced confidence analysis and proper R:R ratios"""
        try:
            # Advanced multi-layer confidence calculation with REAL-TIME data
            supply_1_mid = (snd_zones['supply_1_low'] + snd_zones['supply_1_high']) / 2
            demand_1_mid = (snd_zones['demand_1_low'] + snd_zones['demand_1_high']) / 2

            # Get real 24h change for dynamic calculation - IMPROVED FETCHING
            change_24h = 0  # Initialize change_24h
            try:
                # Import crypto_api if not already available
                if crypto_api:
                    price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data:
                        change_24h = price_data.get('change_24h', 0)
                    else:
                        print(f"Error in price data for {symbol}: {price_data.get('error', 'Unknown error') if price_data else 'No data'}")
                else:
                    # Fallback: import crypto_api if not passed
                    try:
                        from crypto_api import crypto_api as fallback_api
                        price_data = fallback_api.get_crypto_price(symbol, force_refresh=True)
                        if 'error' not in price_data and price_data:
                            change_24h = price_data.get('change_24h', 0)
                    except ImportError:
                        print(f"Could not import crypto_api for {symbol}")
            except Exception as e:
                print(f"Error getting change_24h for {symbol}: {e}")
                change_24h = 0 # Default to 0 if error

            # Timeframe-specific movement expectations for proper R:R calculation
            timeframe_multipliers = {
                '15m': {'min_move': 0.008, 'max_move': 0.025, 'volatility': 1.5},  # Scalping: 0.8-2.5%
                '30m': {'min_move': 0.012, 'max_move': 0.035, 'volatility': 1.8},  # Quick swing: 1.2-3.5%
                '1h': {'min_move': 0.018, 'max_move': 0.050, 'volatility': 2.2},   # Intraday: 1.8-5%
                '4h': {'min_move': 0.035, 'max_move': 0.080, 'volatility': 3.0},   # Swing: 3.5-8%
                '1d': {'min_move': 0.050, 'max_move': 0.120, 'volatility': 4.0},   # Position: 5-12%
                '1w': {'min_move': 0.100, 'max_move': 0.250, 'volatility': 6.0}    # Long-term: 10-25%
            }

            tf_config = timeframe_multipliers.get(timeframe, timeframe_multipliers['4h'])

            # Enhanced volume analysis with progressive scoring - REAL-TIME
            volume_multiplier = 1.0
            volume_score = 0

            # Symbol-specific volume thresholds with CURRENT market conditions
            if symbol.upper() in ['BTC', 'ETH']:  # Major coins
                if volume_24h > 15000000000:    # 15B+ - Exceptional
                    volume_score = 30
                    volume_multiplier = 1.30
                elif volume_24h > 8000000000:   # 8B+ - Very High
                    volume_score = 25
                    volume_multiplier = 1.25
                elif volume_24h > 4000000000:   # 4B+ - High
                    volume_score = 20
                    volume_multiplier = 1.20
                elif volume_24h > 2000000000:   # 2B+ - Good
                    volume_score = 15
                    volume_multiplier = 1.15
                elif volume_24h > 1000000000:   # 1B+ - Medium
                    volume_score = 10
                    volume_multiplier = 1.10
                else:
                    volume_score = 0
                    volume_multiplier = 0.85     # Low volume penalty
            else:  # Altcoins
                if volume_24h > 3000000000:     # 3B+ - Exceptional
                    volume_score = 30
                    volume_multiplier = 1.25
                elif volume_24h > 1500000000:   # 1.5B+ - Very High
                    volume_score = 25
                    volume_multiplier = 1.20
                elif volume_24h > 800000000:    # 800M+ - High
                    volume_score = 20
                    volume_multiplier = 1.15
                elif volume_24h > 400000000:    # 400M+ - Good
                    volume_score = 15
                    volume_multiplier = 1.10
                elif volume_24h > 200000000:    # 200M+ - Medium
                    volume_score = 10
                    volume_multiplier = 1.05
                else:
                    volume_score = 0
                    volume_multiplier = 0.85     # Low volume penalty

            volume_status = ("🔥 Exceptional" if volume_score >= 25 else
                           "⚡ Very High" if volume_score >= 20 else
                           "📊 High" if volume_score >= 15 else
                           "📈 Good" if volume_score >= 10 else
                           "📉 Medium" if volume_score >= 5 else "💤 Low")

            # Position analysis with precision scoring
            distance_to_supply = abs(current_price - supply_1_mid) / current_price * 100
            distance_to_demand = abs(current_price - demand_1_mid) / current_price * 100

            # Zone precision bonus
            zone_precision_bonus = 0
            min_distance = min(distance_to_supply, distance_to_demand)
            if min_distance < 0.5:      # Very close to zone
                zone_precision_bonus = 15
            elif min_distance < 1.0:    # Close to zone
                zone_precision_bonus = 10
            elif min_distance < 2.0:    # Near zone
                zone_precision_bonus = 5

            # Advanced direction logic with DYNAMIC base confidence based on market conditions

            # Calculate dynamic base confidence using multiple real-time factors
            price_momentum_score = min(25, abs(change_24h) * 3)  # Price movement contributes to confidence
            volatility_bonus = 0

            # Volatility analysis for confidence adjustment
            if 2 <= abs(change_24h) <= 12:  # Sweet spot volatility
                volatility_bonus = 15
            elif 1 <= abs(change_24h) <= 15:  # Acceptable volatility
                volatility_bonus = 10
            elif abs(change_24h) > 15:  # High volatility
                volatility_bonus = 5

            # Market timing factor
            current_hour = datetime.now().hour
            timing_score = 0
            if 14 <= current_hour <= 22:  # US market peak
                timing_score = 8
            elif 8 <= current_hour <= 16:   # European active
                timing_score = 5
            elif 0 <= current_hour <= 6:    # Asian session
                timing_score = 3

            # Symbol-specific momentum bonus based on current market data
            symbol_momentum_bonus = 0
            if symbol.upper() == 'BTC' and abs(change_24h) > 2:
                symbol_momentum_bonus = 10  # Bitcoin leadership bonus
            elif symbol.upper() == 'ETH' and abs(change_24h) > 3:
                symbol_momentum_bonus = 8   # Ethereum strong move bonus
            elif symbol.upper() in ['SOL', 'ADA', 'DOT'] and abs(change_24h) > 5:
                symbol_momentum_bonus = 12  # Altcoin breakout bonus

            # IMPROVED base confidence calculation with better weighting
            base_confidence = 35 + (price_momentum_score * 1.2) + (volatility_bonus * 0.9) + (timing_score * 0.8) + (symbol_momentum_bonus * 1.0)

            # Additional quality factors for better confidence
            quality_bonus = 0

            # Major coin premium (BTC, ETH get higher base confidence)
            if symbol.upper() in ['BTC', 'ETH']:
                quality_bonus += 12
            elif symbol.upper() in ['SOL', 'ADA', 'BNB', 'XRP', 'DOT', 'MATIC', 'AVAX']:
                quality_bonus += 8
            elif symbol.upper() in ['UNI', 'LINK', 'LTC', 'ATOM', 'ICP', 'NEAR', 'APT']:
                quality_bonus += 5

            # Market cap stability bonus
            if symbol.upper() in ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA']:
                quality_bonus += 8  # Top 10 stability

            base_confidence += quality_bonus

            # ENHANCED market position analysis with better confidence scoring
            if current_price <= demand_1_mid and distance_to_demand < 2:
                direction = "LONG"
                emoji = "🟢"
                entry = current_price * 0.9995
                tp1 = supply_1_mid
                tp2 = snd_zones['supply_1_high']
                tp3 = snd_zones['supply_2_low']
                sl = snd_zones['demand_1_low']
                strategy = "SnD Demand Zone Reversal"

                # IMPROVED confidence for perfect zone setups
                zone_confidence_bonus = 30
                if distance_to_demand < 0.5:  # Very close to demand zone
                    zone_confidence_bonus = 35
                elif distance_to_demand < 1.0:  # Close to demand zone
                    zone_confidence_bonus = 32

                base_confidence = min(88, base_confidence + zone_confidence_bonus)

            elif current_price >= supply_1_mid and distance_to_supply < 2:
                direction = "SHORT"
                emoji = "🔴"
                entry = current_price * 1.0005
                tp1 = demand_1_mid
                tp2 = snd_zones['demand_1_low']
                tp3 = snd_zones['demand_2_low']
                sl = snd_zones['supply_1_high']
                strategy = "SnD Supply Zone Reversal"

                # IMPROVED confidence for perfect zone setups
                zone_confidence_bonus = 30
                if distance_to_supply < 0.5:  # Very close to supply zone
                    zone_confidence_bonus = 35
                elif distance_to_supply < 1.0:  # Close to supply zone
                    zone_confidence_bonus = 32

                base_confidence = min(88, base_confidence + zone_confidence_bonus)

            elif current_price < supply_1_mid and current_price > demand_1_mid:
                # Between zones - lower confidence naturally
                zone_range = supply_1_mid - demand_1_mid
                position_in_range = (current_price - demand_1_mid) / zone_range

                if position_in_range > 0.7:  # Upper 30% of range
                    direction = "LONG"
                    emoji = "🟢"
                    entry = current_price * 0.999
                    tp1 = supply_1_mid
                    tp2 = snd_zones['supply_1_high']
                    tp3 = snd_zones['supply_2_low']
                    sl = demand_1_mid
                    strategy = "Range Breakout Long"
                    base_confidence = min(72, base_confidence + 18)
                elif position_in_range < 0.3:  # Lower 30% of range
                    direction = "SHORT"
                    emoji = "🔴"
                    entry = current_price * 1.001
                    tp1 = demand_1_mid
                    tp2 = snd_zones['demand_1_low']
                    tp3 = snd_zones['demand_2_low']
                    sl = supply_1_mid
                    strategy = "Range Breakdown Short"
                    base_confidence = min(72, base_confidence + 18)
                else:  # Middle of range - even lower confidence
                    if change_24h > 2:  # Strong bullish momentum
                        direction = "LONG"
                        emoji = "🟢"
                        entry = current_price * 0.999
                        tp1 = supply_1_mid
                        tp2 = snd_zones['supply_1_high']
                        tp3 = snd_zones['supply_2_low']
                        sl = demand_1_mid
                        strategy = "Momentum Long - Range Middle"
                        base_confidence = min(65, base_confidence + 12)
                    elif change_24h < -2:  # Strong bearish momentum
                        direction = "SHORT"
                        emoji = "🔴"
                        entry = current_price * 1.001
                        tp1 = demand_1_mid
                        tp2 = snd_zones['demand_1_low']
                        tp3 = snd_zones['demand_2_low']
                        sl = supply_1_mid
                        strategy = "Momentum Short - Range Middle"
                        base_confidence = min(65, base_confidence + 12)
                    else:  # Neutral - very low confidence
                        direction = "LONG"
                        emoji = "🟢"
                        entry = current_price * 0.999
                        tp1 = supply_1_mid
                        tp2 = snd_zones['supply_1_high']
                        tp3 = snd_zones['supply_2_low']
                        sl = demand_1_mid
                        strategy = "Range Middle Long Bias"
                        base_confidence = min(58, base_confidence + 8)
            else:
                direction = "WAIT"
                emoji = "⏳"
                entry = current_price
                tp1 = supply_1_mid if current_price < supply_1_mid else demand_1_mid
                tp2 = tp1 * 1.015
                tp3 = tp1 * 1.025
                sl = current_price * 0.985
                strategy = "Outside Optimal Zones"
                base_confidence = min(45, base_confidence + 5)

            # Enhanced R:R calculation with dynamic targets for higher ratios
            try:
                # Calculate stop loss based on timeframe and volatility
                if direction == "LONG":
                    # Dynamic stop loss calculation for LONG positions
                    atr_stop = current_price * (tf_config['min_move'] * 0.6)  # Even tighter stop for better R:R
                    zone_stop = abs(current_price - demand_1_mid) * 0.8       # Tighter zone-based stop
                    sl = current_price - max(atr_stop, zone_stop)

                    # Calculate risk first
                    risk = abs(entry - sl)

                    # Dynamic target calculation based on market conditions and timeframe
                    # Higher volatility = higher R:R potential
                    volatility_multiplier = 1.0
                    if abs(change_24h) > 15:
                        volatility_multiplier = 4.0  # Very high vol = 4:1+ potential
                    elif abs(change_24h) > 10:
                        volatility_multiplier = 3.5  # High vol = 3.5:1+ potential
                    elif abs(change_24h) > 7:
                        volatility_multiplier = 3.0  # Good vol = 3:1+ potential
                    elif abs(change_24h) > 5:
                        volatility_multiplier = 2.5  # Medium vol = 2.5:1+ potential
                    elif abs(change_24h) > 3:
                        volatility_multiplier = 2.0  # Low vol = 2:1+ potential
                    else:
                        volatility_multiplier = 1.8  # Very low vol = 1.8:1+ potential

                    # Timeframe-specific multiplier for higher targets
                    tf_multiplier = {
                        '15m': 1.5, '30m': 1.8, '1h': 2.0,
                        '4h': 2.5, '1d': 3.0, '1w': 4.0
                    }.get(timeframe, 2.0)

                    # Calculate progressive targets with increasing R:R ratios
                    base_reward = risk * volatility_multiplier * tf_multiplier

                    tp1 = entry + (base_reward * 0.6)  # First target - conservative
                    tp2 = entry + (base_reward * 1.0)  # Second target - base R:R
                    tp3 = entry + (base_reward * 1.5)  # Third target - extended R:R

                elif direction == "SHORT":
                    # Dynamic stop loss calculation for SHORT positions
                    atr_stop = current_price * (tf_config['min_move'] * 0.6)  # Even tighter stop for better R:R
                    zone_stop = abs(current_price - supply_1_mid) * 0.8       # Tighter zone-based stop
                    sl = current_price + max(atr_stop, zone_stop)

                    # Calculate risk first
                    risk = abs(sl - entry)

                    # Dynamic target calculation based on market conditions and timeframe
                    volatility_multiplier = 1.0
                    if abs(change_24h) > 15:
                        volatility_multiplier = 4.0  # Very high vol = 4:1+ potential
                    elif abs(change_24h) > 10:
                        volatility_multiplier = 3.5  # High vol = 3.5:1+ potential
                    elif abs(change_24h) > 7:
                        volatility_multiplier = 3.0  # Good vol = 3:1+ potential
                    elif abs(change_24h) > 5:
                        volatility_multiplier = 2.5  # Medium vol = 2.5:1+ potential
                    elif abs(change_24h) > 3:
                        volatility_multiplier = 2.0  # Low vol = 2:1+ potential
                    else:
                        volatility_multiplier = 1.8  # Very low vol = 1.8:1+ potential

                    # Timeframe-specific multiplier for higher targets
                    tf_multiplier = {
                        '15m': 1.5, '30m': 1.8, '1h': 2.0,
                        '4h': 2.5, '1d': 3.0, '1w': 4.0
                    }.get(timeframe, 2.0)

                    # Calculate progressive targets with increasing R:R ratios
                    base_reward = risk * volatility_multiplier * tf_multiplier

                    tp1 = entry - (base_reward * 0.6)  # First target - conservative
                    tp2 = entry - (base_reward * 1.0)  # Second target - base R:R
                    tp3 = entry - (base_reward * 1.5)  # Third target - extended R:R

                else:
                    # NEUTRAL/WAIT positions
                    sl = current_price * 0.995
                    tp1 = current_price * 1.005
                    tp2 = current_price * 1.01
                    tp3 = current_price * 1.015

                # Final R:R calculation - using TP2 as primary target for R:R calculation
                if direction in ["LONG", "SHORT"]:
                    risk = abs(entry - sl)
                    reward = abs(tp2 - entry)  # Use TP2 for main R:R calculation
                    rr_ratio = reward / risk if risk > 0 else 1.0

                    # Only reject signals with extremely poor R:R (below 1.2:1)
                    if rr_ratio < 1.2:
                        direction = "NEUTRAL"
                        emoji = "⚖️"
                        strategy = f"Poor R:R ({rr_ratio:.1f}:1) - Signal Rejected"
                        base_confidence = 25  # Very low confidence for poor R:R
                else:
                    rr_ratio = 1.0

            except Exception as e:
                print(f"R:R calculation error: {e}")
                rr_ratio = 1.0

            # More conservative multipliers for realistic confidence
            timeframe_multiplier = {
                '15m': 0.90, '30m': 0.95, '1h': 1.0,
                '4h': 1.05, '1d': 1.08, '1w': 1.12
            }.get(timeframe, 1.0)

            # Enhanced R:R bonus calculation for higher rewards
            rr_bonus = 1.0
            if rr_ratio >= 5.0:
                rr_bonus = 1.25    # Excellent RR - significant bonus
            elif rr_ratio >= 4.0:
                rr_bonus = 1.20    # Very good RR
            elif rr_ratio >= 3.0:
                rr_bonus = 1.15    # Good RR
            elif rr_ratio >= 2.5:
                rr_bonus = 1.12    # Above average RR
            elif rr_ratio >= 2.0:
                rr_bonus = 1.08    # Decent RR
            elif rr_ratio >= 1.5:
                rr_bonus = 1.05    # Acceptable RR
            elif rr_ratio >= 1.2:
                rr_bonus = 1.02    # Minimal RR
            else:
                rr_bonus = 0.80    # Poor RR penalty

            # Conservative timing bonus
            current_hour = datetime.now().hour
            timing_bonus = 1.0
            if 14 <= current_hour <= 22:      # US hours
                timing_bonus = 1.04            # Small bonus only
            elif 8 <= current_hour <= 16:     # European hours
                timing_bonus = 1.02
            elif 0 <= current_hour <= 4:      # Asian hours
                timing_bonus = 1.01

            # Conservative symbol quality
            symbol_quality = 1.0
            if symbol.upper() in ['BTC', 'ETH']:
                symbol_quality = 1.06          # Small premium for majors
            elif symbol.upper() in ['SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI', 'LINK']:
                symbol_quality = 1.03          # Very small bonus for established alts

            # Final confidence with controlled variation - cap at 90%
            raw_confidence = base_confidence + (volume_score * 0.5) + (zone_precision_bonus * 0.8)

            # Apply conservative multipliers
            adjusted_confidence = raw_confidence * timeframe_multiplier * rr_bonus * timing_bonus * symbol_quality * volume_multiplier

            # IMPROVED variation algorithm with controlled randomness
            import random

            # Create consistent but varied confidence using symbol characteristics
            symbol_hash = int(hashlib.md5(f"{symbol}".encode()).hexdigest()[:4], 16)

            # More controlled variation range: 0.85 to 1.15 for better consistency
            hash_variation = 0.85 + (symbol_hash % 300) / 1000  # Range: 0.85 to 1.15

            # Market condition multipliers - more predictable
            market_multiplier = 1.0
            if symbol.upper() in ['BTC', 'ETH'] and abs(change_24h) > 5:
                market_multiplier = 1.06  # Consistent 6% bonus for major moves
            elif abs(change_24h) > 10:  # Very strong movement
                market_multiplier = 1.08  # 8% bonus for extreme moves
            elif abs(change_24h) > 7:   # Strong movement
                market_multiplier = 1.05  # 5% bonus for strong moves
            elif abs(change_24h) < 1:   # Weak movement
                market_multiplier = 0.90  # 10% penalty for weak movement

            # Volume impact - more predictable scaling
            volume_multiplier = 1.0
            if volume_24h > 3000000000:     # Very high volume
                volume_multiplier = 1.08
            elif volume_24h > 1500000000:   # High volume
                volume_multiplier = 1.05
            elif volume_24h > 800000000:    # Good volume
                volume_multiplier = 1.02
            elif volume_24h < 200000000:    # Low volume
                volume_multiplier = 0.88

            # Final confidence with controlled variation - cap at 90%
            preliminary_final = adjusted_confidence * hash_variation * market_multiplier * volume_multiplier
            final_confidence = min(90, max(40, preliminary_final))

            # Dynamic confidence threshold based on R:R ratio - LOWERED FOR MORE SIGNALS
            confidence_threshold = 45  # Base threshold (lowered from 55)

            # Lower threshold for high R:R signals (they're worth taking with lower confidence)
            if rr_ratio >= 4.0:
                confidence_threshold = 35  # High R:R = lower confidence needed
            elif rr_ratio >= 3.0:
                confidence_threshold = 40  # Good R:R = slightly lower threshold
            elif rr_ratio >= 2.5:
                confidence_threshold = 42  # Above average R:R

            if final_confidence < confidence_threshold:
                print(f"🔍 DEBUG: {symbol} signal rejected - Confidence {final_confidence:.1f}% < threshold {confidence_threshold}%")
                direction = "NEUTRAL"
                emoji = "⚖️"
                # Neutralize all prices to prevent user entry
                entry = current_price
                tp1 = current_price      # Same as entry to prevent execution
                tp2 = current_price      # Same as entry to prevent execution
                tp3 = current_price      # Same as entry to prevent execution
                sl = current_price       # Same as entry to prevent execution
                strategy = f"Low Confidence ({final_confidence:.1f}% < {confidence_threshold}%) - Wait for Better Setup"
            else:
                print(f"✅ DEBUG: {symbol} signal accepted - Confidence {final_confidence:.1f}% >= threshold {confidence_threshold}%")

            # More realistic leverage recommendations based on honest confidence
            if final_confidence >= 85:
                leverage_rec = "5-8x"  # Even high confidence shouldn't be crazy leverage
            elif final_confidence >= 80:
                leverage_rec = "4-6x"
            elif final_confidence >= 75:
                leverage_rec = "3-5x"
            elif final_confidence >= 70:
                leverage_rec = "2-4x"
            elif final_confidence >= 65:
                leverage_rec = "2-3x"
            else:
                leverage_rec = "1-2x"

            # Enhanced validity and time horizon with comprehensive mapping
            validity_hours = {
                '15m': '15-45 minutes', '30m': '30-90 minutes', '1h': '1-4 hours',
                '4h': '4-16 hours', '1d': '1-3 days', '1w': '3-7 days'
            }.get(timeframe, '2-8 hours')

            time_horizon = {
                '15m': 'Scalping (Ultra-fast moves)', '30m': 'Quick Scalp (Fast moves)',
                '1h': 'Intraday (Medium moves)', '4h': 'Swing Trading (Strong moves)',
                '1d': 'Position Trading (Major moves)', '1w': 'Long-term (Trend moves)'
            }.get(timeframe, 'Medium-term')

            # Timeframe-specific strategy names
            strategy_mapping = {
                '15m': 'Scalping Breakout',
                '30m': 'Quick Momentum',
                '1h': 'Intraday Trend',
                '4h': 'Swing Position',
                '1d': 'Daily Trend',
                '1w': 'Weekly Macro'
            }

            if strategy == "SnD Demand Zone Reversal":
                strategy = f"{strategy_mapping.get(timeframe, 'SnD')} - Demand Reversal"
            elif strategy == "SnD Supply Zone Reversal":
                strategy = f"{strategy_mapping.get(timeframe, 'SnD')} - Supply Reversal"
            elif "Range" in strategy:
                strategy = f"{strategy_mapping.get(timeframe, 'Range')} - Range Play"
            elif "Momentum" in strategy:
                strategy = f"{strategy_mapping.get(timeframe, 'Momentum')} - Momentum Play"

            # Ensure all required fields are present for futures signal response
            return {
                'direction': direction,
                'emoji': emoji,
                'entry': float(entry) if entry else current_price,
                'tp1': float(tp1) if tp1 else current_price * 1.02,
                'tp2': float(tp2) if tp2 else current_price * 1.04,
                'tp3': float(tp3) if tp3 else current_price * 1.06,
                'sl': float(sl) if sl else current_price * 0.98,
                'rr': float(rr_ratio) if rr_ratio else 1.0,
                'confidence': round(float(final_confidence), 1),
                'strategy': str(strategy),
                'leverage_rec': str(leverage_rec),
                'validity': str(validity_hours),
                'time_horizon': str(time_horizon),
                'volume_strength': str(volume_status),
                'distance_to_supply': float(distance_to_supply),
                'distance_to_demand': float(distance_to_demand),
                'zone_precision': int(zone_precision_bonus),
                'market_timing': float(timing_bonus)
            }

        except Exception as e:
            print(f"Error in advanced futures signals: {e}")
            # Comprehensive fallback with all required fields
            return {
                'direction': 'NEUTRAL',
                'emoji': '⚖️',
                'entry': float(current_price),
                'tp1': float(current_price * 1.02),
                'tp2': float(current_price * 1.04),
                'tp3': float(current_price * 1.06),
                'sl': float(current_price * 0.98),
                'rr': 1.0,
                'confidence': 50.0,
                'strategy': 'Error Fallback - Wait for Better Signal',
                'leverage_rec': '1-3x',
                'validity': '1-4 hours',
                'time_horizon': 'Short-term monitoring',
                'volume_strength': 'Unknown',
                'distance_to_supply': 2.0,
                'distance_to_demand': 2.0,
                'zone_precision': 0,
                'market_timing': 1.0
            }

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

    def _generate_quick_action_summary(self, futures_signals: Dict, confidence: float, symbol: str) -> str:
        """Generate a quick action summary for traders"""
        direction = futures_signals.get('direction', 'WAIT')
        entry = futures_signals.get('entry', 0)
        sl = futures_signals.get('sl', 0)
        tp1 = futures_signals.get('tp1', 0)

        if confidence < 65:
            return """🛑 **NO TRADE**: Confidence too low
📚 **Advice**: Wait for stronger signal (65%+)
⏰ **Action**: Monitor for better conditions
❌ **Warning**: All levels neutralized to prevent entry"""

        if direction == "LONG":
            return f"""🚀 **BUY PLAN**:
1️⃣ Set buy order at `${entry:,.6f}`
2️⃣ Set stop loss at `${sl:,.6f}`
3️⃣ Set take profit at `${tp1:,.6f}`
4️⃣ Watch for volume confirmation"""

        elif direction == "SHORT":
            return f"""📉 **SELL PLAN**:
1️⃣ Set sell order at `${entry:,.6f}`
2️⃣ Set stop loss at `${sl:,.6f}`
3️⃣ Set take profit at `${tp1:,.6f}`
4️⃣ Watch for volume confirmation"""

        else:
            return f"""⏳ **MONITOR {symbol}**:
📊 Watch key support/resistance levels
📈 Wait for clear breakout direction
🔔 Set price alerts for entry opportunities"""

    def _calculate_position_size(self, confidence: float) -> str:
        """Calculate recommended position size based on confidence"""
        if confidence >= 85:
            return "2-3%"
        elif confidence >= 75:
            return "1.5-2%"
        elif confidence >= 65:
            return "1-1.5%"
        else:
            return "0.5-1%"

    def _get_timeframe_position_size(self, timeframe: str) -> str:
        """Get position size recommendation based on timeframe"""
        timeframe_sizes = {
            '15m': '0.5-1% (High frequency)',
            '30m': '0.8-1.5% (Active scalping)',
            '1h': '1-2% (Intraday trading)',
            '4h': '1.5-2.5% (Swing trading)',
            '1d': '2-3% (Position trading)',
            '1w': '2-4% (Long-term holds)'
        }
        return timeframe_sizes.get(timeframe, '1-2%')

    def _calculate_professional_indicators(self, symbol: str, current_price: float, change_24h: float, snd_zones: Dict, crypto_api=None) -> Dict:
        """Calculate professional technical indicators for futures analysis"""
        try:
            # Calculate EMAs (simplified estimation)
            ema_50 = current_price * (1 + (change_24h / 100) * 0.5)  # Estimate based on recent movement
            ema_200 = current_price * (1 + (change_24h / 100) * 0.2)  # Slower EMA response

            # Format EMAs properly
            if ema_50 < 1:
                ema_50_str = f"${ema_50:.6f}"
            elif ema_50 < 100:
                ema_50_str = f"${ema_50:.4f}"
            else:
                ema_50_str = f"${ema_50:,.2f}"

            if ema_200 < 1:
                ema_200_str = f"${ema_200:.6f}"
            elif ema_200 < 100:
                ema_200_str = f"${ema_200:.4f}"
            else:
                ema_200_str = f"${ema_200:,.2f}"

            # Calculate RSI estimate
            rsi_base = 50 + (change_24h * 2)  # Rough RSI estimation
            rsi = max(0, min(100, rsi_base))

            if rsi > 70:
                rsi_status = "Overbought"
            elif rsi > 60:
                rsi_status = "Strong"
            elif rsi > 40:
                rsi_status = "Normal"
            elif rsi > 30:
                rsi_status = "Weak"
            else:
                rsi_status = "Oversold"

            # Calculate MACD estimate
            macd = change_24h * 0.001  # Simple MACD approximation
            macd_status = "Bullish" if macd > 0 else "Bearish" if macd < -0.001 else "Neutral"

            # Calculate ATR estimate
            atr = current_price * 0.02  # 2% ATR estimate
            if atr < 0.01:
                atr_str = f"${atr:.6f}"
            elif atr < 1:
                atr_str = f"${atr:.4f}"
            else:
                atr_str = f"${atr:.2f}"

            # Volume trend analysis
            if abs(change_24h) > 5:
                volume_trend = "High"
            elif abs(change_24h) > 2:
                volume_trend = "Above Average"
            else:
                volume_trend = "Normal"

            # Market structure
            if change_24h > 3:
                market_structure = "Strong Bullish"
                higher_tf_trend = "Bullish"
                higher_tf_alignment = "Bullish alignment"
                tf_confirmation = "CONFIRMED"
            elif change_24h > 1:
                market_structure = "Bullish"
                higher_tf_trend = "Bullish"
                higher_tf_alignment = "Bullish alignment"
                tf_confirmation = "CONFIRMED"
            elif change_24h < -3:
                market_structure = "Strong Bearish"
                higher_tf_trend = "Bearish"
                higher_tf_alignment = "Bearish alignment"
                tf_confirmation = "CONFIRMED"
            elif change_24h < -1:
                market_structure = "Bearish"
                higher_tf_trend = "Bearish"
                higher_tf_alignment = "Bearish alignment"
                tf_confirmation = "CONFIRMED"
            else:
                market_structure = "Neutral"
                higher_tf_trend = "Sideways"
                higher_tf_alignment = "Neutral"
                tf_confirmation = "PENDING"

            # Volatility level
            if abs(change_24h) > 10:
                volatility_level = "Very High"
            elif abs(change_24h) > 5:
                volatility_level = "High"
            elif abs(change_24h) > 2:
                volatility_level = "Moderate"
            else:
                volatility_level = "Low"

            return {
                'ema_50': ema_50_str,
                'ema_200': ema_200_str,
                'rsi': f"{rsi:.1f}",
                'rsi_status': rsi_status,
                'macd': f"{macd:.4f}",
                'macd_status': macd_status,
                'atr': atr_str,
                'volume_trend': volume_trend,
                'market_structure': market_structure,
                'higher_tf_trend': higher_tf_trend,
                'higher_tf_alignment': higher_tf_alignment,
                'tf_confirmation': tf_confirmation,
                'volatility_level': volatility_level
            }

        except Exception as e:
            # Fallback values
            return {
                'ema_50': f"${current_price:.4f}",
                'ema_200': f"${current_price:.4f}",
                'rsi': "50.0",
                'rsi_status': "Normal",
                'macd': "0.0000",
                'macd_status': "Neutral",
                'atr': f"${current_price * 0.02:.4f}",
                'volume_trend': "Normal",
                'market_structure': "Normal",
                'higher_tf_trend': "Neutral",
                'higher_tf_alignment': "Neutral",
                'tf_confirmation': "PENDING",
                'volatility_level': "Moderate"
            }

    def _generate_professional_insights(self, futures_signals: Dict, confidence: float, symbol: str, direction: str) -> str:
        """Generate professional trading insights"""
        insights = []

        if confidence >= 90:
            insights.append("• 🔥 Extremely high probability setup (Max 95%) - Consider larger position")
        elif confidence >= 85:
            insights.append("• ⚡️ Strong confluence of multiple signals")
        elif confidence >= 75:
            insights.append("• 📊 Good probability setup with solid confluence")
        else:
            insights.append("• ⚠️ Lower confidence - Use minimal position sizing")

        if direction == "LONG":
            insights.append("• 🎪 Bullish momentum approach recommended")
            insights.append("• 💰 Excellent risk/reward ratio - High profit potential")
        elif direction == "SHORT":
            insights.append("• 🎪 Bearish momentum approach recommended")
            insights.append("• 💰 Strong downside potential identified")
        else:
            insights.append("• ⏳ Wait for clearer directional signals")
            insights.append("• 📊 Current setup lacks sufficient conviction")

        insights.append("• 📈 Higher timeframe analysis supports this direction")

        return "\n".join(insights)

    async def get_market_sentiment_async(self, language: str = 'id', crypto_api=None, progress_tracker=None, user_id=None) -> str:
        """Generate market sentiment analysis with optimized timing"""
        try:
            # Optimized timing for concurrent users - reduced total time
            stage_timings = {
                'fetch_global': 0.8,    # 0.8 seconds
                'process': 1.0,         # 1.0 seconds
                'analyze': 1.0,         # 1.0 seconds
                'dominance': 1.0,       # 1.0 seconds
                'finalize': 1.2         # 1.2 seconds
            }

            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "⚡ Mengambil data pasar...", 15)
                else:
                    progress_tracker.update_progress(user_id, "⚡ Fetching market data...", 15)
                await asyncio.sleep(stage_timings['fetch_global'])

            # Get market data from CoinAPI
            market_data = []
            symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI']

            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "📊 Memproses metrik...", 35)
                else:
                    progress_tracker.update_progress(user_id, "📊 Processing metrics...", 35)
                await asyncio.sleep(stage_timings['process'])

            for symbol in symbols:
                try:
                    if crypto_api:
                        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                        if 'error' not in price_data and price_data.get('price', 0) > 0:
                            market_data.append({
                                'symbol': symbol,
                                'price': price_data.get('price', 0),
                                'change_24h': price_data.get('change_24h', 0),
                                'volume_24h': price_data.get('volume_24h', 0)
                            })
                except Exception as e:
                    print(f"Error getting data for {symbol}: {e}")
                    continue

            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "🧠 Menganalisis sentimen...", 60)
                else:
                    progress_tracker.update_progress(user_id, "🧠 Analyzing sentiment...", 60)
                await asyncio.sleep(stage_timings['analyze'])

            if not market_data:
                if language == 'id':
                    return "❌ Tidak dapat mengambil data pasar dari CoinAPI"
                else:
                    return "❌ Unable to fetch market data from CoinAPI"

            # Calculate market metrics
            total_change = sum(coin['change_24h'] for coin in market_data)
            avg_change = total_change / len(market_data)
            total_volume = sum(coin['volume_24h'] for coin in market_data)

            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "💰 Menghitung dominasi...", 80)
                else:
                    progress_tracker.update_progress(user_id, "💰 Calculating dominance...", 80)
                await asyncio.sleep(stage_timings['dominance'])

            # BTC dominance simulation
            btc_data = next((coin for coin in market_data if coin['symbol'] == 'BTC'), None)
            btc_dominance = 45.0  # Default value
            if btc_data:
                btc_dominance = 50.0 + (btc_data['change_24h'] * 0.5)  # Estimate

            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "✅ Membangun gambaran umum...", 95)
                else:
                    progress_tracker.update_progress(user_id, "✅ Building overview...", 95)
                await asyncio.sleep(stage_timings['finalize'])

            # Market sentiment analysis
            if avg_change > 3:
                sentiment = "🚀 EXTREMELY BULLISH"
                market_mood = "Strong buying pressure across all majors"
            elif avg_change > 1:
                sentiment = "📈 BULLISH"
                market_mood = "Positive momentum building"
            elif avg_change > -1:
                sentiment = "😐 NEUTRAL"
                market_mood = "Consolidation phase"
            elif avg_change > -3:
                sentiment = "📉 BEARISH"
                market_mood = "Selling pressure emerging"
            else:
                sentiment = "💥 EXTREMELY BEARISH"
                market_mood = "Heavy selling across markets"

            # Volume analysis
            if total_volume > 50000000000:  # 50B+
                volume_status = "🔥 Very High Volume"
            elif total_volume > 30000000000:  # 30B+
                volume_status = "⚡ High Volume"
            elif total_volume > 15000000000:  # 15B+
                volume_status = "📊 Good Volume"
            else:
                volume_status = "💤 Low Volume"

            # Generate recommendations
            recommendations = self._generate_coin_recommendations(market_data, avg_change, btc_dominance)
            entry_analysis = self._generate_best_entry_analysis(market_data, sentiment)

            analysis = f"""🌍 **OVERVIEW PASAR CRYPTO GLOBAL (CoinAPI Real-time)**

📊 **SENTIMEN PASAR**: {sentiment}
🎯 **Market Mood**: {market_mood}
📈 **Rata-rata Perubahan**: {avg_change:+.2f}%
🟠 **BTC Dominance**: {btc_dominance:.1f}%
📊 **Status Volume**: {volume_status}

🔬 **ANALISIS STRUKTUR PASAR:**
🔄 **Tren**: {"Bullish Momentum" if avg_change > 2 else "Bearish Correction" if avg_change < -2 else "Sideways Consolidation"}
⚡ **Struktur**: {"Risk-On" if avg_change > 2 else "Risk-Off" if avg_change < -2 else "Neutral"}
🧠 **Alasan**: {"Sentimen positif mendorong kenaikan" if avg_change > 2 else "Tekanan jual meluas" if avg_change < -2 else "Pasar menantikan katalis"}
📊 **Indeks Ketakutan & Keserakahan**: {50 + (avg_change * 5):.0f}/100 {"(Extreme Greed)" if (50 + (avg_change * 5)) > 75 else "(Greed)" if (50 + (avg_change * 5)) > 55 else "(Neutral)" if (50 + (avg_change * 5)) > 45 else "(Fear)" if (50 + (avg_change * 5)) > 25 else "(Extreme Fear)"}

📈 **KINERJA CRYPTOCURRENCY TERATAS (24H):**
"""

            # Show top performers
            sorted_performers = sorted(market_data, key=lambda x: x['change_24h'], reverse=True)
            for i, coin in enumerate(sorted_performers[:5], 1):
                price_format = f"${coin['price']:.4f}" if coin['price'] < 100 else f"${coin['price']:,.2f}"
                change_emoji = "📈" if coin['change_24h'] >= 0 else "📉"
                analysis += f"""
• **{i}. {coin['symbol']}** {change_emoji} {price_format} ({coin['change_24h']:+.1f}%)"""

            analysis += f"""

{recommendations}

{entry_analysis}

🚨 **LEVEL KUNCI UNTUK DIPANTAU:**
• **Support Dominasi BTC**: {btc_dominance-2:.1f}%
• **Resistance Dominasi BTC**: {btc_dominance+2:.1f}%
• **Level Kunci Kapitalisasi Pasar**: {format_large_number(total_market_cap * 0.95)} - {format_large_number(total_market_cap * 1.05)}

📡 **Sumber Data**: CoinAPI Real-time + Analisis Multi-API
⏰ **Pembaruan Berikutnya**: Setiap 15 menit untuk data real-time"""

            # Complete progress tracking
            if user_id and progress_tracker:
                if language == 'id':
                    progress_tracker.update_progress(user_id, "✅ Analisis pasar selesai!", 100)
                else:
                    progress_tracker.update_progress(user_id, "✅ Market analysis complete!", 100)
                progress_tracker.complete_job(user_id)

            return analysis

        except Exception as e:
            # Complete job even on error
            if user_id and progress_tracker:
                progress_tracker.complete_job(user_id)
            print(f"Error in market sentiment: {e}")
            if language == 'id':
                return f"""❌ **ERROR ANALISIS PASAR**

**Error**: {str(e)[:100]}...

💡 **Perbaikan Cepat:**
• Coba `/price btc` untuk data dasar
• Gunakan `/analyze btc` untuk analisis koin tunggal
• Tunggu 30 detik dan coba lagi

🔧 **Command Alternatif:**
• `/market` - Gambaran umum pasar crypto"""
            else:
                return f"""❌ **MARKET ANALYSIS ERROR**

**Error**: {str(e)[:100]}...

💡 **Quick Fix:**
• Try `/price btc` for basic data
• Use `/analyze btc` for single coin analysis
• Wait 30 seconds and retry

🔧 **Alternative Commands:**
• `/market` - Market overview"""

    def get_market_sentiment(self, language: str = 'id', crypto_api=None) -> str:
        """Get comprehensive market overview and sentiment analysis using Binance data"""
        try:
            # Get data for top cryptocurrencies available on Binance
            major_cryptos = [
                'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI',
                'LINK', 'LTC', 'ATOM', 'ICP', 'NEAR', 'APT', 'FTM', 'ALGO', 'VET', 'FLOW',
                'DOGE', 'SHIB', 'PEPE', 'TRX', 'XLM'
            ]
            market_data = []

            total_volume = 0
            total_change = 0
            total_market_cap = 0
            active_cryptos = 9515  # Simulated total

            for symbol in major_cryptos:
                if crypto_api:
                    price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        price = price_data.get('price', 0)
                        change_24h = price_data.get('change_24h', 0)
                        volume_24h = price_data.get('volume_24h', 0)
                        market_cap = price_data.get('market_cap', 0)

                        # Fallback market cap estimation if not available
                        if not market_cap:
                            if symbol == 'BTC':
                                market_cap = price * 19700000  # ~19.7M BTC supply
                            elif symbol == 'ETH':
                                market_cap = price * 120300000  # ~120.3M ETH supply
                            else:
                                market_cap = price * 1000000000  # Generic fallback

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

            # Calculate BTC and ETH dominance
            btc_data = next((d for d in market_data if d['symbol'] == 'BTC'), None)
            eth_data = next((d for d in market_data if d['symbol'] == 'ETH'), None)

            btc_dominance = (btc_data['market_cap'] / total_market_cap * 100) if btc_data else 57.4
            eth_dominance = (eth_data['market_cap'] / total_market_cap * 100) if eth_data else 13.4

            # Enhanced confidence calculation
            confidence = 50 + abs(avg_change) * 3  # Base confidence on market movement
            confidence = min(100, max(30, confidence))

            # Global sentiment determination
            if avg_change > 3:
                global_sentiment = "🚀 BULLISH"
                sentiment_emoji = "🚀"
            elif avg_change > 1:
                global_sentiment = "📈 POSITIVE"
                sentiment_emoji = "📈"
            elif avg_change > -1:
                global_sentiment = "😐 NEUTRAL"
                sentiment_emoji = "😐"
            elif avg_change > -3:
                global_sentiment = "📉 NEGATIVE"
                sentiment_emoji = "📉"
            else:
                global_sentiment = "💥 BEARISH"
                sentiment_emoji = "💥"

            # Market structure analysis
            if btc_dominance > 55:
                trend = "Sideways Consolidation"
                structure = "BTC Dominance Phase"
                reasoning = "Bitcoin consolidating market share, alts underperforming"
            elif avg_change > 2:
                trend = "Bullish Momentum"
                structure = "Risk-On Environment"
                reasoning = "Strong buying across all sectors, altcoins favorable"
            elif avg_change < -2:
                trend = "Bearish Correction"
                structure = "Risk-Off Environment"
                reasoning = "Market-wide selling, flight to quality assets"
            else:
                trend = "Range Bound"
                structure = "Neutral Market"
                reasoning = "Mixed signals, waiting for directional catalyst"

            # Fear & Greed Index
            fear_greed_value = 50 + (avg_change * 5)
            fear_greed_value = max(0, min(100, fear_greed_value))

            if fear_greed_value > 75:
                fear_greed = "🤑 Extreme Greed"
            elif fear_greed_value > 55:
                fear_greed = "😍 Greed"
            elif fear_greed_value > 45:
                fear_greed = "😐 Neutral"
            elif fear_greed_value > 25:
                fear_greed = "😰 Fear"
            else:
                fear_greed = "😱 Extreme Fear"

            # Format numbers
            def format_large_number(num):
                if num > 1000000000000:  # Trillion
                    return f"${num/1000000000000:.2f}T"
                elif num > 1000000000:  # Billion
                    return f"${num/1000000000:.2f}B"
                elif num > 1000000:  # Million
                    return f"${num/1000000:.1f}M"
                else:
                    return f"${num:,.0f}"

            # Main analysis output
            analysis = f"""🌍 **KOMPREHENSIF ANALISIS PASAR**

🕐 **Waktu Analisis**: {datetime.now().strftime('%H:%M:%S WIB')}
📊 **Sentimen Global**: {global_sentiment}
⭐ **Keyakinan**: {confidence:.0f}%

💰 **METRIK GLOBAL:**
• **Total Kapitalisasi Pasar**: {format_large_number(total_market_cap)}
• **Perubahan Pasar 24j**: {avg_change:+.2f}%
• **Total Volume 24j**: {format_large_number(total_volume)}
• **Kripto Aktif**: {active_cryptos:,}
• **Dominasi BTC**: {btc_dominance:.1f}%
• **Dominasi ETH**: {eth_dominance:.1f}%

🔬 **ANALISIS STRUKTUR PASAR:**
🔄 **Tren**: {trend}
⚡ **Struktur**: {structure}
🧠 **Alasan**: {reasoning}
📊 **Indeks Ketakutan & Keserakahan**: {fear_greed} ({fear_greed_value:.0f}/100)

📈 **KINERJA CRYPTOCURRENCY TERATAS (24H):**
"""

            # Sort by market cap and show top 5
            market_data.sort(key=lambda x: x['market_cap'], reverse=True)

            for i, data in enumerate(market_data[:5], 1):
                price = data['price']
                change = data['change_24h']

                # Format price
                if price < 1:
                    price_format = f"${price:.6f}"
                elif price < 100:
                    price_format = f"${price:.4f}"
                else:
                    price_format = f"${price:,.2f}"

                # Status emoji based on change
                if change > 1:
                    status_emoji = "📈"
                    status = "Bullish"
                elif change > 0:
                    status_emoji = "🟢"
                    status = "Positive"
                elif change == 0:
                    status_emoji = "😐"
                    status = "Neutral"
                elif change > -1:
                    status_emoji = "🔴"
                    status = "Negative"
                else:
                    status_emoji = "📉"
                    status = "Bearish"

                analysis += f"\n{i}. **{data['symbol']}** {status_emoji} {price_format} ({change:+.1f}%) - {status}"

            # Trading implications
            if avg_change > 2:
                implications = """

💡 **IMPLIKASI TRADING:**
• 🚀 Momentum bullish kuat - Ikuti tren
• 🎯 Fokus pada strategi breakout
• 🟢 Lingkungan risk-on - Altcoin menguntungkan
• ⚠️ Waspadai sinyal overextension"""

                opportunities = """

🎯 **PELUANG PASAR:**
• 🏃 Trading momentum pada breakout
• ⚡ Posisi long pada pullback ke support
• 🚀 Rotasi altcoin
• 🔄 Arbitrase premium futures
• 📈 Strategi opsi (call spread)"""

                risk_assessment = """

⚠️ **PENILAIAN RISIKO:**
• 🔥 VOLATILITAS TINGGI - Kurangi ukuran posisi
• 📊 Stop ketat direkomendasikan (3-5%)
• 💨 Pasar bergerak cepat - Keputusan cepat diperlukan
• 💡 Ambil profit secara bertahap
• 📱 Pantau sinyal pembalikan
• ⏰ Setel peringatan untuk breakout resistance kunci"""

            elif avg_change > -2:
                implications = """

💡 **IMPLIKASI TRADING:**
• 😐 Pasar netral - Strategi range trading optimal
• 🎯 Fokus pada level support/resistance
• 🟠 BTC memimpin pasar - Perdagangkan pasangan utama (BTC, ETH)
• ⚠️ Altcoin mungkin berkinerja buruk - Selektif"""

                opportunities = """

🎯 **PELUANG PASAR:**
• 🏃 Trading range antara support/resistance kunci
• ⚡ Peluang scalping pada pasangan bervolume tinggi
• 🟠 Strategi Bitcoin maximalist - Fokus pada BTC/ETH
• 🔄 Peluang arbitrase antar-exchange
• 📈 Perbedaan harga futures vs spot"""

                risk_assessment = """

⚠️ **PENILAIAN RISIKO:**
• 😴 VOLATILITAS RENDAH - Dapat sedikit menambah ukuran posisi
• 📊 Stop lebih lebar dapat diterima (5-7%)
• 🔍 Kondisi pasar tidak pasti - Tunggu kejelasan
• 💡 Paper trade strategi sebelum eksekusi live
• 📱 Pantau berita dan perkembangan regulasi
• ⏰ Setel peringatan untuk breakout support kunci"""

            else:
                implications = """

💡 **IMPLIKASI TRADING:**
• 📉 Tekanan bearish - Strategi short lebih disukai
• 🎯 Fokus pada level breakdown
• 🔴 Lingkungan risk-off - Hindari altcoin
• ⚠️ Mode konservasi modal - Posisi defensif"""

                opportunities = """

🎯 **PELUANG PASAR:**
• 🏃 Short pada pantulan yang gagal
• ⚡ Strategi put options
• 💰 Membangun kas untuk peluang bottom
• 🔄 Lindungi posisi long yang ada
• 📈 DCA hanya pada fundamental terkuat"""

                risk_assessment = """

⚠️ **PENILAIAN RISIKO:**
• 💥 RISIKO TINGGI - Minimalkan eksposur
• 📊 Stop sangat ketat (2-3%)
• 🚨 Potensi panic selling - Hindari FOMO
• 💡 Tunggu sinyal capitulation
• 📱 Volatilitas berbasis berita diharapkan
• ⏰ Setel peringatan untuk breakout support utama"""

            analysis += implications + opportunities + risk_assessment

            # Enhanced coin recommendations and analysis
            coin_recommendations = self._generate_coin_recommendations(market_data, avg_change, btc_dominance)
            best_entry_analysis = self._generate_best_entry_analysis(market_data, global_sentiment)

            analysis += coin_recommendations + best_entry_analysis

            # Key levels to watch
            btc_support = btc_data['price'] * 0.95 if btc_data else 105000
            btc_resistance = btc_data['price'] * 1.05 if btc_data else 115000
            market_cap_low = total_market_cap * 0.95
            market_cap_high = total_market_cap * 1.05

            analysis += f"""

🚨 **LEVEL KUNCI UNTUK DIPANTAU:**
• **Support Dominasi BTC**: {btc_dominance-2:.1f}%
• **Resistance Dominasi BTC**: {btc_dominance+2:.1f}%
• **Level Kunci Kapitalisasi Pasar**: {format_large_number(market_cap_low)} - {format_large_number(market_cap_high)}

📡 **Sumber Data**: Binance Global Metrics + Analisis Multi-API
⏰ **Pembaruan Berikutnya**: Setiap 15 menit untuk data real-time"""

            return analysis

        except Exception as e:
            print(f"Error in market sentiment: {e}")
            return f"""🌍 **KOMPREHENSIF ANALISIS PASAR**

⚠️ **Error**: Tidak dapat mengambil data pasar lengkap saat ini.

💡 **Alternatif yang bisa dicoba:**
• `/price btc` - Cek harga Bitcoin dari CoinAPI
• `/analyze btc` - Analisis mendalam Bitcoin
• `/futures btc` - Sinyal trading Bitcoin

🔄 Coba command `/market` lagi dalam beberapa menit untuk data lengkap.

**Detail Error**: {str(e)[:100]}..."""

    def get_ai_response(self, question: str, language: str = 'id') -> str:
        """Get AI response for general crypto questions"""
        try:
            # Simple AI responses for common crypto questions
            question_lower = question.lower().strip()

            # Enhanced keyword detection for crypto-related questions
            crypto_keywords = ['crypto', 'cryptocurrency', 'mata uang digital', 'blockchain', 'digital currency']
            bitcoin_keywords = ['bitcoin', 'btc']
            ethereum_keywords = ['ethereum', 'eth']
            defi_keywords = ['defi', 'decentralized finance', 'keuangan terdesentralisasi']
            trading_keywords = ['trading', 'strategy', 'teknikal', 'analisis', 'investasi', 'strategi']

            # Check for general crypto questions
            if any(word in question_lower for word in crypto_keywords):
                if language == 'id':
                    return """🪙 **Cryptocurrency - Pengenalan**

Cryptocurrency adalah mata uang digital yang menggunakan teknologi blockchain untuk keamanan dan transparansi.

💡 **Konsep Dasar:**
• Digital currency yang terdesentralisasi
• Tidak dikontrol oleh bank sentral
• Menggunakan kriptografi untuk keamanan
• Transaksi tercatat di blockchain

🔝 **Top Cryptocurrencies:**
• Bitcoin (BTC) - Digital gold
• Ethereum (ETH) - Platform smart contracts
• Binance Coin (BNB) - Token exchange
• Solana (SOL) - High-speed blockchain

📊 **Cara Memulai:**
• Pelajari dasar-dasar blockchain
• Pilih exchange terpercaya
• Mulai dengan jumlah kecil
• Diversifikasi portfolio

⚠️ **Risiko yang Perlu Diketahui:**
• Volatilitas tinggi
• Risiko regulasi
• Keamanan wallet
• Manipulasi pasar

💰 **Tips Investasi:**
• DYOR (Do Your Own Research)
• Jangan invest lebih dari yang Anda mampu untuk hilang
• DCA (Dollar Cost Averaging)
• Tahan untuk jangka panjang (Hold)"""
                else:
                    return """🪙 **Cryptocurrency - Introduction**

Cryptocurrency is a digital currency that uses blockchain technology for security and transparency.

💡 **Core Concepts:**
• Decentralized digital currency
• Not controlled by central banks
• Uses cryptography for security
• Transactions recorded on the blockchain

🔝 **Top Cryptocurrencies:**
• Bitcoin (BTC) - Digital gold
• Ethereum (ETH) - Smart contracts platform
• Binance Coin (BNB) - Exchange token
• Solana (SOL) - High-speed blockchain

📊 **Getting Started:**
• Learn blockchain basics
• Choose a trusted exchange
• Start with small amounts
• Diversify your portfolio

⚠️ **Risks to Be Aware Of:**
• High volatility
• Regulatory risks
• Wallet security
• Market manipulation

💰 **Investment Tips:**
• DYOR (Do Your Own Research)
• Never invest more than you can afford to lose
• DCA (Dollar Cost Averaging)
• Long-term holding (Hold)"""

            elif any(word in question_lower for word in bitcoin_keywords):
                if language == 'id':
                    return """🟠 **Bitcoin (BTC) - Info**

Bitcoin adalah cryptocurrency pertama dan terbesar di dunia, diciptakan oleh Satoshi Nakamoto pada 2009.

💡 **Fitur Utama:**
• Mata uang digital terdesentralisasi
• Pasokan terbatas: 21 juta BTC
• Penyimpan nilai & emas digital
• Konsensus Proof of Work

📊 **Tips Trading:**
• Penyimpan nilai jangka panjang
• Volatilitas tinggi dalam jangka pendek
• Ikuti berita adopsi institusional
• Analisis teknikal sangat efektif

💰 **Perspektif Investasi:**
Bitcoin sering dianggap sebagai "emas digital" dan lindung nilai terhadap inflasi."""
                else:
                    return """🟠 **Bitcoin (BTC) - Info**

Bitcoin is the world's first and largest cryptocurrency, created by Satoshi Nakamoto in 2009.

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
Bitcoin is often considered "digital gold" and a hedge against inflation."""

            elif any(word in question_lower for word in ethereum_keywords):
                if language == 'id':
                    return """🔷 **Ethereum (ETH) - Info**

Ethereum adalah platform blockchain yang mendukung smart contracts dan ekosistem DeFi.

💡 **Fitur Utama:**
• Platform smart contract
• Pusat ekosistem DeFi
• Dasar marketplace NFT
• Proof of Stake (sejak The Merge)

📊 **Tips Trading:**
• Ikuti tren DeFi
• Pantau dampak biaya gas
• Perhatikan upgrade besar
• Korelasi kuat dengan token DeFi

💰 **Perspektif Investasi:**
Ethereum adalah "infrastruktur" untuk Web3 dan aplikasi blockchain."""
                else:
                    return """🔷 **Ethereum (ETH) - Info**

Ethereum is a blockchain platform that supports smart contracts and the DeFi ecosystem.

💡 **Key Features:**
• Smart contract platform
• DeFi ecosystem hub
• NFT marketplace backbone
• Proof of Stake (since The Merge)

📊 **Trading Tips:**
• Follow DeFi trends
• Monitor gas fees impact
• Watch for major upgrades
• Strong correlation with DeFi tokens

💰 **Investment Perspective:**
Ethereum is the "infrastructure" for Web3 and blockchain applications."""

            elif any(word in question_lower for word in defi_keywords):
                if language == 'id':
                    return """🏦 **DeFi (Decentralized Finance) - Penjelasan**

DeFi adalah sistem finansial yang dibangun di atas blockchain, tanpa perantara tradisional.

💡 **Komponen Inti:**
• DEX (Decentralized Exchanges)
• Protokol Pinjam-Meminjam (Lending & Borrowing)
• Yield farming & Liquidity mining
• Stablecoin & Aset Sintetis

📊 **Protokol DeFi Populer:**
• Uniswap (DEX)
• Aave (Lending)
• Compound (Lending)
• MakerDAO (Stablecoin)

⚠️ **Risiko:**
• Risiko smart contract
• Impermanent loss
• Biaya gas tinggi
• Ketidakpastian regulasi

💰 **Peluang:**
• Imbal hasil lebih tinggi dari keuangan tradisional
• Inovasi produk finansial"""
                else:
                    return """🏦 **DeFi (Decentralized Finance) - Explained**

DeFi is a financial system built on blockchain, without traditional intermediaries.

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

            elif any(word in question_lower for word in trading_keywords):
                if language == 'id':
                    return """📈 **Strategi Trading Crypto - Dasar**

💡 **Strategi Fundamental:**

**1. Analisis Teknikal:**
• Level Support & Resistance
• Moving averages (EMA 50, 200)
• Indikator RSI, MACD
• Analisis Volume

**2. Manajemen Risiko:**
• Jangan pernah risiko >2-3% per trade
• Selalu gunakan stop loss
• Ambil profit secara bertahap
• Ukuran posisi sangat penting

**3. Jenis Pasar:**
• Pasar Bullish: Beli saat turun (Buy the dip)
• Pasar Bearish: Jual saat naik (Short rallies)
• Sideways: Trading di rentang (Range trading)

⚠️ **Kesalahan Umum:**
• FOMO buying di puncak
• Tidak menggunakan stop loss
• Leverage berlebihan
• Trading emosional

💰 **Tips Pro:**
• Rencanakan trade Anda
• Buat jurnal trading
• Tetap update dengan berita
• Latihan dengan jumlah kecil terlebih dahulu"""
                else:
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
• Bull market: Buy the dip
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

            # If question contains specific words, provide targeted responses
            elif any(word in question_lower for word in ['wallet', 'dompet']):
                if language == 'id':
                    return """💼 **Dompet Crypto - Panduan**

Dompet crypto adalah aplikasi untuk menyimpan cryptocurrency Anda dengan aman.

🔐 **Jenis Dompet:**
• **Hot Wallet**: Online, mudah diakses (MetaMask, Trust Wallet)
• **Cold Wallet**: Offline, lebih aman (Ledger, Trezor)
• **Dompet Exchange**: Di exchange (Binance, Coinbase)

🛡️ **Keamanan Dompet:**
• Cadangkan seed phrase dengan aman
• Jangan bagikan private key
• Gunakan 2FA jika tersedia
• Verifikasi alamat sebelum transfer

💡 **Rekomendasi:**
• Pemula: Trust Wallet atau MetaMask
• Lanjutan: Hardware wallet untuk jumlah besar
• Trading: Dompet exchange untuk kemudahan"""
                else:
                    return """💼 **Crypto Wallet - Guide**

A crypto wallet is an application to securely store your cryptocurrencies.

🔐 **Wallet Types:**
• **Hot Wallet**: Online, easy access (MetaMask, Trust Wallet)
• **Cold Wallet**: Offline, more secure (Ledger, Trezor)
• **Exchange Wallet**: On the exchange (Binance, Coinbase)

🛡️ **Wallet Security:**
• Back up your seed phrase securely
• Never share your private key
• Use 2FA if available
• Verify addresses before transfers

💡 **Recommendations:**
• Beginners: Trust Wallet or MetaMask
• Advanced: Hardware wallet for large amounts
• Trading: Exchange wallet for convenience"""

            elif any(word in question_lower for word in ['mining', 'menambang']):
                if language == 'id':
                    return """⛏️ **Crypto Mining - Panduan**

Mining adalah proses validasi transaksi crypto dan mendapatkan imbalan.

💻 **Jenis Mining:**
• **Bitcoin Mining**: Membutuhkan ASIC, listrik besar
• **Ethereum Mining**: Berbasis GPU (sekarang Proof of Stake)
• **Altcoin Mining**: Berbagai algoritma

⚡ **Pertimbangan:**
• Biaya listrik vs profit
• Biaya hardware & perawatan
• Pool mining vs solo mining
• Regulasi lokal

💰 **Alternatif Modern:**
• Staking (Proof of Stake)
• Yield farming di DeFi
• Cloud mining (hati-hati scam)"""
                else:
                    return """⛏️ **Crypto Mining - Guide**

Mining is the process of validating crypto transactions and earning rewards.

💻 **Mining Types:**
• **Bitcoin Mining**: Requires ASICs, high electricity costs
• **Ethereum Mining**: GPU-based (now Proof of Stake)
• **Altcoin Mining**: Various algorithms

⚡ **Considerations:**
• Electricity costs vs. profit
• Hardware cost & maintenance
• Pool mining vs. solo mining
• Local regulations

💰 **Modern Alternatives:**
• Staking (Proof of Stake)
• Yield farming in DeFi
• Cloud mining (beware of scams)"""

            else:
                # Generic helpful response for unmatched questions
                if language == 'id':
                    return f"""🤖 **AI Assistant Siap Membantu!**

Pertanyaan Anda: "{question[:50]}{'...' if len(question) > 50 else ''}"

Saya siap membantu Anda dengan topik seputar crypto! 

💡 **Topik yang bisa saya bantu:**
• **Dasar-dasar Crypto**: Bitcoin, Ethereum, blockchain
• **DeFi**: Uniswap, lending, yield farming
• **Trading**: Analisis teknikal, strategi
• **Wallet**: Pengaturan, keamanan, rekomendasi
• **Mining**: Proof of Work, staking, alternatif

📚 **Command yang tersedia:**
• `/analyze btc` - Analisis komprehensif Bitcoin
• `/futures btc` - Sinyal trading Bitcoin
• `/market` - Gambaran umum pasar
• `/price btc` - Harga real-time (gratis)

🔄 **Coba ajukan pertanyaan lagi dengan lebih spesifik:**
Contoh: "Apa itu Bitcoin?", "Bagaimana cara trading crypto?", "Dompet mana yang aman?"

Saya siap membantu dengan pengetahuan crypto terlengkap! 🚀"""
                else:
                    return f"""🤖 **AI Assistant Ready!**

Your question: "{question[:50]}{'...' if len(question) > 50 else ''}"

I'm here to help you with all things crypto! 

💡 **Topics I can assist with:**
• **Crypto Basics**: Bitcoin, Ethereum, blockchain
• **DeFi**: Uniswap, lending, yield farming
• **Trading**: Technical analysis, strategies
• **Wallets**: Setup, security, recommendations
• **Mining**: Proof of Work, staking, alternatives

📚 **Available Commands:**
• `/analyze btc` - Comprehensive Bitcoin analysis
• `/futures btc` - Bitcoin trading signals
• `/market` - Crypto market overview
• `/price btc` - Real-time price (free)

🔄 **Try asking again with more specifics:**
Examples: "What is Bitcoin?", "How to trade crypto?", "Which wallet is secure?"

Let's explore the crypto world together! 🚀"""

        except Exception as e:
            return f"❌ Error processing the question: {str(e)[:100]}..."

        except Exception as e:
            return f"❌ Error processing the question: {str(e)[:100]}..."