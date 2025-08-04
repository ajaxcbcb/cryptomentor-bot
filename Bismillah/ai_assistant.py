# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
from datetime import datetime

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name
        self.coinglass_key = os.getenv("COINGLASS_API_KEY")
        if not self.coinglass_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
            print("💡 Please set COINGLASS_API_KEY in Replit Secrets")

    def greet(self):
        return f"Halo! Saya {self.name}, siap membantu analisis dan informasi crypto kamu."

    def analyze_text(self, text):
        if "btc" in text.lower():
            return "📈 BTC sedang menarik untuk dianalisis hari ini!"
        elif "eth" in text.lower():
            return "📉 ETH menunjukkan sinyal konsolidasi."
        else:
            return "Saya tidak yakin, tapi saya akan bantu cari datanya."

    def help_message(self):
        return """🤖 **CryptoMentor AI Bot - Help**

📊 **Harga & Data Pasar:**
• `/price <symbol>` - Harga real-time
• `/market` - Overview pasar komprehensif

📈 **Analisis Trading:**
• `/analyze <symbol>` - Analisis mendalam (20 credit)
• `/futures <symbol>` - Analisis futures 1 coin (20 credit)
• `/futures_signals` - Sinyal futures lengkap (30 credit)

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio
• `/add_coin <symbol> <amount>` - Tambah ke portfolio
• `/credits` - Cek sisa credit
• `/subscribe` - Upgrade premium

🎯 **Lainnya:**
• `/ask_ai <pertanyaan>` - Tanya AI crypto
• `/referral` - Program referral
• `/language` - Ubah bahasa

💡 **Tips:**
- Ketik nama crypto langsung untuk harga cepat
- Fitur premium = unlimited access
- Gunakan referral untuk bonus credit

🚀 **Semua analisis menggunakan data real-time dari Coinglass & CMC!**"""

    def _get_coinglass_headers(self):
        """Get headers for Coinglass API requests"""
        return {
            "accept": "application/json",
            "coinglassSecret": self.coinglass_key
        }

    def _get_coinglass_long_short_data(self, symbol, timeframe='1h'):
        """Get long/short ratio data from Coinglass"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol (remove USDT if present)
            clean_symbol = symbol.upper().replace('USDT', '')

            url = "https://open-api.coinglass.com/public/v2/futures/longShortChart"
            headers = self._get_coinglass_headers()

            # Map timeframe to intervalType
            interval_map = {
                '5m': 0, '15m': 1, '1h': 2, '4h': 3, '12h': 4, '24h': 5
            }
            interval_type = interval_map.get(timeframe, 2)  # Default to 1h

            params = {
                'symbol': clean_symbol,
                'intervalType': interval_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', {})
                if result_data and len(result_data) > 0:
                    latest = result_data[-1]  # Get latest data point

                    return {
                        'symbol': clean_symbol,
                        'long_ratio': float(latest.get('longShortRatio', 50)),
                        'short_ratio': 100 - float(latest.get('longShortRatio', 50)),
                        'timestamp': latest.get('time', ''),
                        'source': 'coinglass',
                        'raw_data': latest
                    }
                else:
                    return {'error': 'No data available from Coinglass'}
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass long/short data error: {str(e)}"}

    def _get_coinglass_open_interest_data(self, symbol, timeframe='1h'):
        """Get open interest and funding rate data from Coinglass"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol
            clean_symbol = symbol.upper().replace('USDT', '')

            url = "https://open-api.coinglass.com/public/v2/futures/openInterest"
            headers = self._get_coinglass_headers()

            # Map timeframe to intervalType
            interval_map = {
                '5m': 0, '15m': 1, '1h': 2, '4h': 3, '12h': 4, '24h': 5
            }
            interval_type = interval_map.get(timeframe, 2)

            params = {
                'symbol': clean_symbol,
                'intervalType': interval_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', {})
                if result_data and len(result_data) > 0:
                    latest = result_data[-1]
                    previous = result_data[-2] if len(result_data) > 1 else latest

                    # Calculate OI change
                    current_oi = float(latest.get('openInterest', 0))
                    previous_oi = float(previous.get('openInterest', 0))
                    oi_change = ((current_oi - previous_oi) / previous_oi * 100) if previous_oi > 0 else 0

                    return {
                        'symbol': clean_symbol,
                        'open_interest': current_oi,
                        'oi_change_percent': oi_change,
                        'funding_rate': float(latest.get('fundingRate', 0)),
                        'timestamp': latest.get('time', ''),
                        'source': 'coinglass',
                        'raw_data': latest
                    }
                else:
                    return {'error': 'No open interest data available'}
            else:
                return {'error': f"Coinglass OI API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass open interest error: {str(e)}"}

    def _analyze_smc_structure(self, long_short_data, oi_data, symbol):
        """Analyze Smart Money Concepts (SMC) structure"""
        try:
            smc_analysis = {
                'market_structure': 'neutral',
                'smart_money_bias': 'neutral',
                'liquidity_zones': [],
                'confidence': 50,
                'entry_type': 'HOLD'
            }

            if 'error' in long_short_data or 'error' in oi_data:
                return smc_analysis

            long_ratio = long_short_data.get('long_ratio', 50)
            oi_change = oi_data.get('oi_change_percent', 0)
            funding_rate = oi_data.get('funding_rate', 0)

            # SMC Analysis based on smart money indicators
            confidence_score = 50

            # 1. Long/Short Ratio Analysis (Contrarian indicator)
            if long_ratio > 70:
                # Overleveraged longs - Smart money likely short
                smc_analysis['smart_money_bias'] = 'bearish'
                smc_analysis['market_structure'] = 'distribution'
                confidence_score += 20
            elif long_ratio < 30:
                # Overleveraged shorts - Smart money likely long
                smc_analysis['smart_money_bias'] = 'bullish'
                smc_analysis['market_structure'] = 'accumulation'
                confidence_score += 20
            elif 45 <= long_ratio <= 55:
                # Balanced - Look at other indicators
                confidence_score += 5

            # 2. Open Interest Analysis
            if oi_change > 5:
                # Increasing OI with trend continuation
                if smc_analysis['smart_money_bias'] == 'bullish':
                    confidence_score += 15
                elif smc_analysis['smart_money_bias'] == 'bearish':
                    confidence_score += 15
                else:
                    smc_analysis['smart_money_bias'] = 'bullish' if long_ratio < 50 else 'bearish'
                    confidence_score += 10
            elif oi_change < -5:
                # Decreasing OI - Potential reversal
                confidence_score -= 10

            # 3. Funding Rate Analysis
            if funding_rate > 0.01:  # High positive funding (1%+)
                # Longs paying shorts heavily - Smart money short bias
                if smc_analysis['smart_money_bias'] != 'bearish':
                    smc_analysis['smart_money_bias'] = 'bearish'
                confidence_score += 15
            elif funding_rate < -0.005:  # Negative funding
                # Shorts paying longs - Smart money long bias
                if smc_analysis['smart_money_bias'] != 'bullish':
                    smc_analysis['smart_money_bias'] = 'bullish'
                confidence_score += 15

            # 4. Determine entry type based on SMC bias
            if smc_analysis['smart_money_bias'] == 'bullish' and confidence_score >= 70:
                smc_analysis['entry_type'] = 'LONG'
            elif smc_analysis['smart_money_bias'] == 'bearish' and confidence_score >= 70:
                smc_analysis['entry_type'] = 'SHORT'
            else:
                smc_analysis['entry_type'] = 'HOLD'

            # 5. Generate liquidity zones (simplified)
            if oi_data.get('open_interest', 0) > 0:
                base_price = self._get_estimated_price(symbol)
                if smc_analysis['smart_money_bias'] == 'bullish':
                    smc_analysis['liquidity_zones'] = [
                        {'type': 'support', 'price': base_price * 0.97, 'strength': 'high'},
                        {'type': 'support', 'price': base_price * 0.95, 'strength': 'medium'}
                    ]
                elif smc_analysis['smart_money_bias'] == 'bearish':
                    smc_analysis['liquidity_zones'] = [
                        {'type': 'resistance', 'price': base_price * 1.03, 'strength': 'high'},
                        {'type': 'resistance', 'price': base_price * 1.05, 'strength': 'medium'}
                    ]

            smc_analysis['confidence'] = min(95, max(30, confidence_score))
            return smc_analysis

        except Exception as e:
            print(f"❌ SMC analysis error: {e}")
            return {
                'market_structure': 'unknown',
                'smart_money_bias': 'neutral',
                'liquidity_zones': [],
                'confidence': 30,
                'entry_type': 'HOLD'
            }

    def _calculate_smc_levels(self, symbol, smc_analysis, long_short_data, oi_data):
        """Calculate precise entry, TP, and SL levels based on SMC analysis"""
        try:
            base_price = self._get_estimated_price(symbol)
            entry_type = smc_analysis.get('entry_type', 'HOLD')
            confidence = smc_analysis.get('confidence', 50)

            # Risk management based on confidence
            if confidence >= 80:
                risk_percent = 0.015  # 1.5% risk for high confidence
                reward_ratio = 3.0    # 3:1 RR
            elif confidence >= 70:
                risk_percent = 0.012  # 1.2% risk for medium confidence
                reward_ratio = 2.5    # 2.5:1 RR
            else:
                risk_percent = 0.01   # 1% risk for low confidence
                reward_ratio = 2.0    # 2:1 RR

            if entry_type == 'LONG':
                entry = base_price * 0.9995  # Slight discount for better fill
                sl = entry * (1 - risk_percent)
                tp1 = entry * (1 + (risk_percent * (reward_ratio / 2)))
                tp2 = entry * (1 + (risk_percent * reward_ratio))

            elif entry_type == 'SHORT':
                entry = base_price * 1.0005  # Slight premium for short entry
                sl = entry * (1 + risk_percent)
                tp1 = entry * (1 - (risk_percent * (reward_ratio / 2)))
                tp2 = entry * (1 - (risk_percent * reward_ratio))

            else:  # HOLD
                entry = base_price
                tp1 = base_price * 1.01
                tp2 = base_price * 1.02
                sl = base_price * 0.99

            return {
                'entry_type': entry_type,
                'entry': entry,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl,
                'risk_percent': risk_percent * 100,
                'reward_ratio': reward_ratio,
                'confidence': confidence
            }

        except Exception as e:
            print(f"❌ SMC levels calculation error: {e}")
            base_price = self._get_estimated_price(symbol)
            return {
                'entry_type': 'HOLD',
                'entry': base_price,
                'tp1': base_price * 1.01,
                'tp2': base_price * 1.02,
                'sl': base_price * 0.99,
                'risk_percent': 1.0,
                'reward_ratio': 2.0,
                'confidence': 50
            }

    def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Generate enhanced futures analysis using Coinglass data with SMC analysis"""
        try:
            print(f"🎯 Generating enhanced Coinglass futures analysis for {symbol} {timeframe}")

            # Get Coinglass data
            long_short_data = self._get_coinglass_long_short_data(symbol, timeframe)
            oi_data = self._get_coinglass_open_interest_data(symbol, timeframe)

            # Get CMC data for additional context if available
            cmc_data = {}
            if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider:
                try:
                    cmc_data = crypto_api.cmc_provider.get_cryptocurrency_quotes(symbol)
                except Exception as e:
                    print(f"⚠️ CMC data unavailable: {e}")

            # Analyze SMC structure
            smc_analysis = self._analyze_smc_structure(long_short_data, oi_data, symbol)

            # Calculate trading levels
            trading_levels = self._calculate_smc_levels(symbol, smc_analysis, long_short_data, oi_data)

            # Format output
            return self._format_coinglass_analysis(
                symbol, timeframe, long_short_data, oi_data, cmc_data, 
                smc_analysis, trading_levels, language
            )

        except Exception as e:
            print(f"❌ Error in Coinglass futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _format_coinglass_analysis(self, symbol, timeframe, long_short_data, oi_data, cmc_data, smc_analysis, trading_levels, language='id'):
        """Format Coinglass analysis output"""
        try:
            entry_type = trading_levels.get('entry_type', 'HOLD')
            confidence = trading_levels.get('confidence', 50)

            # Smart price formatting
            def format_price(price):
                if price < 1:
                    return f"${price:.8f}"
                elif price < 100:
                    return f"${price:.6f}"
                else:
                    return f"${price:,.4f}"

            # Get current price
            current_price = trading_levels.get('entry', 0)
            if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
                current_price = cmc_data.get('price', 0)
                price_source = "CMC Real-time"
                source_emoji = "🟢"
            else:
                price_source = "Estimated"
                source_emoji = "🟡"

            # Direction emoji
            if entry_type == 'LONG':
                direction_emoji = "🟢"
                signal_emoji = "📈"
            elif entry_type == 'SHORT':
                direction_emoji = "🔴"
                signal_emoji = "📉"
            else:
                direction_emoji = "⏸️"
                signal_emoji = "📊"

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            if language == 'id':
                message = f"""🎯 **ANALISIS FUTURES COINGLASS - {symbol.upper()} ({timeframe})**

💰 **Data Harga:**
• **Current**: {format_price(current_price)} {source_emoji}
• **Source**: {price_source}

{direction_emoji} **SMART MONEY SIGNAL: {entry_type}** {signal_emoji}
📊 **Confidence**: {confidence:.0f}%
🧠 **SMC Bias**: {smc_analysis.get('smart_money_bias', 'neutral').title()}

💰 **REKOMENDASI TRADING COINGLASS:**"""

                if entry_type != 'HOLD':
                    message += f"""
┣━ 📍 **ENTRY**: {format_price(trading_levels['entry'])}
┣━ 🎯 **TP 1**: {format_price(trading_levels['tp1'])} (50% profit)
┣━ 🎯 **TP 2**: {format_price(trading_levels['tp2'])} (50% profit)
┗━ 🛡️ **STOP LOSS**: {format_price(trading_levels['sl'])} (**WAJIB!**)"""
                else:
                    message += f"""
┣━ ⏸️ **HOLD POSITION** - Tunggu setup yang lebih jelas
┣━ 📊 **Monitor Level**: {format_price(current_price * 0.98)} - {format_price(current_price * 1.02)}
┗━ 🔍 **Next Signal**: Tunggu perubahan struktur market"""

                # Add Coinglass data analysis
                message += f"""

📊 **ANALISIS COINGLASS DATA:**"""

                if 'error' not in long_short_data:
                    long_ratio = long_short_data.get('long_ratio', 50)
                    short_ratio = long_short_data.get('short_ratio', 50)
                    message += f"""
• **Long/Short Ratio**: {long_ratio:.1f}% / {short_ratio:.1f}%"""

                    if long_ratio > 70:
                        message += f" (⚠️ Overleveraged Longs)"
                    elif long_ratio < 30:
                        message += f" (💎 Oversold Conditions)"
                    else:
                        message += f" (⚖️ Balanced)"

                if 'error' not in oi_data:
                    oi_change = oi_data.get('oi_change_percent', 0)
                    funding_rate = oi_data.get('funding_rate', 0) * 100
                    message += f"""
• **Open Interest Change**: {oi_change:+.2f}%"""
                    if oi_change > 5:
                        message += f" (📈 Strong momentum)"
                    elif oi_change < -5:
                        message += f" (📉 Weakening momentum)"
                    else:
                        message += f" (📊 Stable)"

                    message += f"""
• **Funding Rate**: {funding_rate:.4f}%"""
                    if funding_rate > 1:
                        message += f" (💸 Longs overpaying)"
                    elif funding_rate < -0.5:
                        message += f" (💰 Shorts overpaying)"

                # SMC Analysis
                message += f"""

🧠 **SMART MONEY CONCEPTS (SMC):**
• **Market Structure**: {smc_analysis.get('market_structure', 'neutral').title()}
• **Smart Money Bias**: {smc_analysis.get('smart_money_bias', 'neutral').title()}"""

                # Liquidity zones
                liquidity_zones = smc_analysis.get('liquidity_zones', [])
                if liquidity_zones:
                    message += f"""
• **Liquidity Zones**:"""
                    for zone in liquidity_zones[:2]:
                        zone_price = format_price(zone.get('price', 0))
                        zone_type = zone.get('type', '').title()
                        zone_strength = zone.get('strength', 'medium').title()
                        message += f"""
  - {zone_type}: {zone_price} ({zone_strength})"""

                if entry_type != 'HOLD':
                    message += f"""

⚡ **STRATEGI SMC {timeframe.upper()}:**
• **Risk Management**: {trading_levels.get('risk_percent', 1):.1f}% risk per trade
• **Reward Ratio**: {trading_levels.get('reward_ratio', 2):.1f}:1
• **Position Size**: {"2-3%" if confidence >= 80 else "1-2%" if confidence >= 70 else "0.5-1%"} modal
• **Market Bias**: Follow smart money {smc_analysis.get('smart_money_bias', 'neutral')} bias

🛡️ **RISK MANAGEMENT KETAT:**
• Set SL WAJIB sebelum entry
• Take profit: 50% di TP1, 50% di TP2
• Move SL ke breakeven setelah TP1 hit
• Exit jika SMC structure berubah"""
                else:
                    message += f"""

⏸️ **STRATEGI HOLD:**
• Market belum memberikan setup SMC yang jelas
• Tunggu konfirmasi smart money bias
• Monitor perubahan long/short ratio dan OI
• Entry hanya setelah confidence >70%"""

                message += f"""

📡 **DATA SOURCES:**
• **Long/Short Data**: Coinglass Futures API
• **Open Interest**: Coinglass Real-time
• **Price Data**: {price_source}
• **SMC Analysis**: Advanced algorithmic analysis

⏰ **Analysis Time**: {current_time}
🔄 **Next Update**: Real-time via Coinglass API"""

            else:
                # English version (similar structure)
                message = f"""🎯 **COINGLASS FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

💰 **Price Data:**
• **Current**: {format_price(current_price)} {source_emoji}
• **Source**: {price_source}

{direction_emoji} **SMART MONEY SIGNAL: {entry_type}** {signal_emoji}
📊 **Confidence**: {confidence:.0f}%
🧠 **SMC Bias**: {smc_analysis.get('smart_money_bias', 'neutral').title()}

💰 **COINGLASS TRADING RECOMMENDATIONS:**"""

                if entry_type != 'HOLD':
                    message += f"""
┣━ 📍 **ENTRY**: {format_price(trading_levels['entry'])}
┣━ 🎯 **TP 1**: {format_price(trading_levels['tp1'])} (50% profit)
┣━ 🎯 **TP 2**: {format_price(trading_levels['tp2'])} (50% profit)
┗━ 🛡️ **STOP LOSS**: {format_price(trading_levels['sl'])} (**MANDATORY!**)"""
                else:
                    message += f"""
┣━ ⏸️ **HOLD POSITION** - Wait for clearer setup
┣━ 📊 **Monitor Levels**: {format_price(current_price * 0.98)} - {format_price(current_price * 1.02)}
┗━ 🔍 **Next Signal**: Wait for market structure change"""

                # Add similar analysis sections in English...
                message += f"""

📊 **COINGLASS DATA ANALYSIS:**"""

                message += f"""

📡 **DATA SOURCES:**
• **Long/Short Data**: Coinglass Futures API
• **Open Interest**: Coinglass Real-time
• **Price Data**: {price_source}
• **SMC Analysis**: Advanced algorithmic analysis

⏰ **Analysis Time**: {current_time}
🔄 **Next Update**: Real-time via Coinglass API"""

            return message

        except Exception as e:
            print(f"❌ Error formatting Coinglass analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate futures signals using Coinglass data for multiple coins"""
        try:
            print(f"🎯 Generating Coinglass futures signals for top coins")

            target_symbols = self._get_top_5_coins_by_market_cap(crypto_api)
            coinglass_recommendations = []

            for symbol in target_symbols:
                try:
                    # Get Coinglass analysis for each symbol
                    long_short_data = self._get_coinglass_long_short_data(symbol, '1h')
                    oi_data = self._get_coinglass_open_interest_data(symbol, '1h')

                    if 'error' not in long_short_data and 'error' not in oi_data:
                        smc_analysis = self._analyze_smc_structure(long_short_data, oi_data, symbol)
                        trading_levels = self._calculate_smc_levels(symbol, smc_analysis, long_short_data, oi_data)

                        if trading_levels.get('confidence', 0) >= 70:  # Only high confidence signals
                            coinglass_recommendations.append({
                                'symbol': symbol,
                                'analysis': smc_analysis,
                                'levels': trading_levels,
                                'long_short_data': long_short_data,
                                'oi_data': oi_data
                            })

                except Exception as e:
                    print(f"❌ Error processing Coinglass signal for {symbol}: {e}")
                    continue

            return self._format_coinglass_signals_output(coinglass_recommendations, language)

        except Exception as e:
            print(f"❌ Error in generate_futures_signals: {e}")
            return "❌ Error generating Coinglass futures signals. Please try again later."

    def _format_coinglass_signals_output(self, recommendations, language='id'):
        """Format Coinglass signals output"""
        if not recommendations:
            if language == 'id':
                return "❌ Tidak ada sinyal Coinglass dengan confidence >70%. Coba lagi nanti."
            else:
                return "❌ No Coinglass signals with confidence >70%. Try again later."

        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            header = f"""🎯 SINYAL FUTURES COINGLASS + SMC
⏰ {current_time} | 📊 TOP {len(recommendations)} SIGNALS BY CONFIDENCE

💡 **STRATEGI**: Smart Money Concepts + Coinglass Futures Data

"""

            formatted_signals = []
            for i, rec in enumerate(recommendations, 1):
                symbol = rec['symbol']
                levels = rec['levels']
                smc = rec['analysis']
                long_short = rec['long_short_data']
                oi = rec['oi_data']

                entry_type = levels.get('entry_type', 'HOLD')
                confidence = levels.get('confidence', 50)

                def format_price(price):
                    if price < 1:
                        return f"${price:.8f}"
                    elif price < 100:
                        return f"${price:.6f}"
                    else:
                        return f"${price:,.4f}"

                direction_emoji = "🟢" if entry_type == 'LONG' else "🔴" if entry_type == 'SHORT' else "⏸️"

                signal_analysis = f"""**{i}. {symbol} {direction_emoji} - {entry_type}**
💰 Entry: {format_price(levels['entry'])} | Confidence: {confidence:.0f}%

📋 **COINGLASS SETUP:**
• **TP1**: {format_price(levels['tp1'])} (50% profit)
• **TP2**: {format_price(levels['tp2'])} (50% profit)
• **SL**: {format_price(levels['sl'])} (Risk: {levels.get('risk_percent', 1):.1f}%)

🧠 **SMC Analysis:**
• **Smart Money Bias**: {smc.get('smart_money_bias', 'neutral').title()}
• **Long/Short Ratio**: {long_short.get('long_ratio', 50):.1f}% / {long_short.get('short_ratio', 50):.1f}%
• **OI Change**: {oi.get('oi_change_percent', 0):+.2f}%
• **Funding Rate**: {oi.get('funding_rate', 0)*100:.4f}%"""

                formatted_signals.append(signal_analysis)

            footer = """

══════════════════════════════════════════
🎯 **CARA MENGGUNAKAN SINYAL COINGLASS:**

1️⃣ **Setup Trading:**
   • Entry sesuai level yang diberikan
   • Set SL WAJIB sebelum entry
   • Take profit bertahap di TP1 dan TP2

2️⃣ **Smart Money Concepts:**
   • Follow bias smart money (bullish/bearish)
   • Monitor perubahan long/short ratio
   • Watch funding rate untuk konfirmasi

3️⃣ **Risk Management:**
   • Position size maksimal 2% modal untuk confidence >80%
   • Position size maksimal 1% modal untuk confidence 70-80%
   • Move SL ke breakeven setelah TP1 hit

📊 **Data Source**: Coinglass Real-time + CMC + SMC Analysis
⚠️ **Risk Warning**: Trading futures berisiko tinggi, gunakan proper risk management!

💡 **Pro Tip**: Kombinasikan dengan analisis chart manual untuk hasil optimal"""

        else:
            # English version would follow similar structure
            header = f"""🎯 COINGLASS FUTURES SIGNALS + SMC
⏰ {current_time} | 📊 TOP {len(recommendations)} SIGNALS BY CONFIDENCE

💡 **STRATEGY**: Smart Money Concepts + Coinglass Futures Data

"""
            formatted_signals = []
            # Similar formatting in English...

            footer = """

══════════════════════════════════════════
🎯 **HOW TO USE COINGLASS SIGNALS:**

Use strict risk management and follow SMC principles."""

        return header + "\n\n".join(formatted_signals) + footer

    def get_ai_response(self, text, language='id'):
        """Enhanced AI response for crypto beginners and general questions"""
        text_lower = text.lower()

        if language == 'id':
            # Crypto basics and education
            if any(keyword in text_lower for keyword in ['apa itu bitcoin', 'bitcoin itu apa', 'penjelasan bitcoin']):
                return """🪙 **Apa itu Bitcoin?**

Bitcoin (BTC) adalah cryptocurrency pertama dan terbesar di dunia, diciptakan oleh Satoshi Nakamoto pada 2009.

🔑 **Karakteristik Utama:**
- **Digital Currency**: Mata uang digital yang tidak dikendalikan bank
- **Blockchain**: Teknologi buku besar terdistribusi yang aman
- **Limited Supply**: Hanya 21 juta BTC yang akan pernah ada
- **Decentralized**: Tidak ada otoritas pusat yang mengendalikan

💡 **Kegunaan Bitcoin:**
- Store of value (penyimpan nilai)
- Medium of exchange (alat tukar)
- Hedge against inflation (lindung nilai inflasi)

📈 **Untuk pemula**: Mulai dengan belajar tentang wallet, private key, dan cara membeli BTC di exchange resmi.

Gunakan `/price btc` untuk cek harga terkini!"""

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`.\nContoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

            elif any(keyword in text_lower for keyword in ['help', 'bantuan', 'command']):
                return self.help_message()

            elif any(keyword in text_lower for keyword in ['terima kasih', 'thanks', 'thx']):
                return "🙏 Sama-sama! Senang bisa membantu belajar crypto Anda. Jangan ragu untuk bertanya lagi!"

            # Default response for unmatched queries
            else:
                return f"""🤖 **CryptoMentor AI**

Saya memahami Anda bertanya tentang: "{text}"

📚 **Yang bisa saya bantu:**
- Analisisharga crypto (`/price btc`)
- Analisis mendalam (`/analyze eth`) 
- Sinyal trading (`/futures_signals`)
- Overview pasar (`/market`)
- Pertanyaan crypto umum
- Tutorial trading dan DeFi

💡 **Tip**: Coba ketik pertanyaan lebih spesifik atau gunakan command yang tersedia.

Gunakan `/help` untuk melihat semua fitur!"""

        else:
            # English responses
            if any(keyword in text_lower for keyword in ['price', 'cost', 'how much']):
                return "💰 To check crypto prices, use `/price <symbol>`. Example: `/price btc`\n\nFor comprehensive analysis: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['help', 'command']):
                return self.help_message()

            elif any(keyword in text_lower for keyword in ['thank', 'thanks', 'thx']):
                return "🙏 You're welcome! Happy to help with your crypto learning journey. Feel free to ask anytime!"

            else:
                return """🤖 **CryptoMentor AI - Crypto Learning Assistant**

I'm here to help you learn about cryptocurrency!

📚 **Topics I can explain:**
- Crypto basics (Bitcoin, Blockchain, DeFi)
- How to buy and store crypto
- Trading and technical analysis
- Security and wallet management
- NFTs and blockchain technology

💡 **Example questions:**
- "What is Bitcoin?"
- "How to buy crypto?"
- "What is DeFi?"
- "How to trade cryptocurrency?"
- "Best crypto wallets?"

📊 **Available commands:**
- `/price <symbol>` - Check real-time prices
- `/analyze <symbol>` - Deep analysis
- `/futures_signals` - Trading signals
- `/help` - See all commands

Ask me anything about crypto! 🚀"""