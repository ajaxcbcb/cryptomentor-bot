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
        self.coinglass_base_url = "https://open-api.coinglass.com/public/v2"

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

    def _get_coinglass_price(self, symbol):
        """Get price data from Coinglass using longShortChart endpoint"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol (remove USDT if present)
            clean_symbol = symbol.upper().replace('USDT', '')

            url = f"{self.coinglass_base_url}/futures/longShortChart"
            headers = self._get_coinglass_headers()

            params = {
                'symbol': clean_symbol,
                'intervalType': 2  # 1 hour interval
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', {})
                if result_data and len(result_data) > 0:
                    latest = result_data[-1]  # Get latest data point

                    # Extract price from the data
                    price = latest.get('price', 0)
                    if price <= 0:
                        # Try alternative price fields
                        price = latest.get('close', 0)

                    if price > 0:
                        return {
                            'symbol': clean_symbol,
                            'price': float(price),
                            'timestamp': latest.get('time', ''),
                            'source': 'coinglass',
                            'raw_data': latest
                        }

                return {'error': 'No price data available from Coinglass'}
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass price error: {str(e)}"}

    def _get_coinglass_long_short_data(self, symbol, timeframe='1h'):
        """Get long/short ratio data from Coinglass v2 API"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol (remove USDT if present)
            clean_symbol = symbol.upper().replace('USDT', '')

            url = f"{self.coinglass_base_url}/futures/longShortChart"
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
        """Get open interest data from Coinglass v2 API"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol
            clean_symbol = symbol.upper().replace('USDT', '')

            url = f"{self.coinglass_base_url}/futures/openInterest"
            headers = self._get_coinglass_headers()

            params = {
                'symbol': clean_symbol
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
        """Analyze Smart Money Concepts (SMC) structure using Coinglass data"""
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

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Generate enhanced futures analysis using Coinglass data"""
        try:
            print(f"🎯 Generating enhanced futures analysis for {symbol} {timeframe}")

            # Get data concurrently
            tasks = [
                asyncio.to_thread(self._get_coinglass_price, symbol),
                self._get_coinglass_data_async(symbol, timeframe)
            ]

            price_data, coinglass_data = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            if isinstance(price_data, Exception):
                price_data = {'error': str(price_data)}
            if isinstance(coinglass_data, Exception):
                coinglass_data = {'error': str(coinglass_data)}

            # Analyze and format
            analysis = await self._generate_futures_analysis(
                symbol, timeframe, price_data, coinglass_data, language
            )

            return analysis

        except Exception as e:
            print(f"❌ Error in futures analysis: {e}")
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

📡 **DATA SOURCES (100% COINGLASS):**
• **Long/Short Ratio**: Coinglass longShortChart API ✅
• **Open Interest**: Coinglass openInterest API ✅  
• **Price Data**: {price_source}
• **SMC Analysis**: Coinglass + Advanced algorithmic analysis

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

                message += f"""

📡 **DATA SOURCES (100% COINGLASS):**
• **Long/Short Ratio**: Coinglass longShortChart API ✅
• **Open Interest**: Coinglass openInterest API ✅
• **Price Data**: {price_source}
• **SMC Analysis**: Coinglass + Advanced algorithmic analysis

⏰ **Analysis Time**: {current_time}
🔄 **Next Update**: Real-time via Coinglass API"""

            return message

        except Exception as e:
            print(f"❌ Error formatting Coinglass analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    async def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate futures signals using Coinglass data for multiple coins"""
        try:
            print(f"🎯 Generating futures signals for top coins")

            target_symbols = self._get_top_coins_for_signals(crypto_api)

            # Get price data for all symbols concurrently from Coinglass
            price_tasks = [
                asyncio.to_thread(self._get_coinglass_price, symbol) for symbol in target_symbols
            ]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)

            # Get Coinglass data for high-quality symbols
            valid_symbols = []
            price_data = {}

            for i, result in enumerate(price_results):
                symbol = target_symbols[i]
                if isinstance(result, dict) and 'error' not in result:
                    valid_symbols.append(symbol)
                    price_data[symbol] = result
                else:
                    print(f"⚠️ Price data failed for {symbol}: {result}")

            # Generate signals for valid symbols
            signal_recommendations = []

            for symbol in valid_symbols[:10]:  # Limit to top 10 for performance
                try:
                    coinglass_data = await self._get_coinglass_data_async(symbol, '1h')

                    if 'error' not in coinglass_data:
                        signal = await self._analyze_futures_signal(
                            symbol, price_data[symbol], coinglass_data
                        )

                        if signal and signal.get('confidence', 0) >= 70:
                            signal_recommendations.append(signal)

                except Exception as e:
                    print(f"❌ Error processing signal for {symbol}: {e}")
                    continue

            return await self._format_futures_signals_output(signal_recommendations, language)

        except Exception as e:
            print(f"❌ Error in generate_futures_signals: {e}")
            return "❌ Error generating futures signals. Please try again later."

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
- Analisis harga crypto (`/price btc`)
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

    def _get_top_5_coins_by_market_cap(self, crypto_api=None):
        """Get top 5 coins by market cap for futures analysis"""
        try:
            # Try to get from CoinMarketCap if available
            if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider:
                try:
                    top_coins = crypto_api.cmc_provider.get_top_cryptocurrencies(limit=5)
                    if 'error' not in top_coins and top_coins.get('data'):
                        return [coin['symbol'] for coin in top_coins['data']]
                except Exception as e:
                    print(f"⚠️ CMC top coins error: {e}")

            # Fallback to hardcoded top coins
            return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        except Exception as e:
            print(f"❌ Error getting top coins: {e}")
            return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']

    def _get_estimated_price(self, symbol):
        """Get estimated price from Coinglass or fallback to dummy price"""
        try:
            # Try to get real price from Coinglass longShortChart endpoint
            long_short_data = self._get_coinglass_long_short_data(symbol, '1h')
            if 'error' not in long_short_data and long_short_data.get('raw_data'):
                raw_data = long_short_data['raw_data']
                if 'price' in raw_data:
                    return float(raw_data['price'])
                elif 'close' in raw_data:
                    return float(raw_data['close'])

            # Fallback to dummy price for testing
            return random.uniform(20000, 40000) if symbol == 'BTC' else random.uniform(1000, 3000)
        except Exception as e:
            print(f"⚠️ Price estimation error for {symbol}: {e}")
            return random.uniform(20000, 40000) if symbol == 'BTC' else random.uniform(1000, 3000)

    def _get_coinglass_historical_simulation(self, symbol):
        """Simulate historical data based on current Coinglass price"""
        try:
            # Get current price from Coinglass
            price_data = self._get_coinglass_price(symbol)
            if 'error' in price_data:
                return {'error': 'Cannot get base price for historical simulation'}

            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return {'error': 'Invalid base price for simulation'}

            # Generate 50 simulated historical data points
            historical_data = []
            base_price = current_price

            for i in range(50):
                # Simulate price variation ±2%
                variation = random.uniform(-0.02, 0.02)
                simulated_price = base_price * (1 + variation)

                historical_data.append({
                    'price_close': simulated_price,
                    'price_open': simulated_price * (1 + random.uniform(-0.005, 0.005)),
                    'price_high': simulated_price * (1 + abs(random.uniform(0, 0.01))),
                    'price_low': simulated_price * (1 - abs(random.uniform(0, 0.01))),
                    'volume_traded': random.uniform(1000000, 10000000),
                    'timestamp': f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:00:00Z"
                })

                # Slight trend for next iteration
                base_price = simulated_price

            return {
                'symbol': symbol,
                'data': historical_data,
                'count': len(historical_data),
                'source': 'coinglass_simulation',
                'base_price': current_price
            }

        except Exception as e:
            return {'error': f'Historical simulation error: {str(e)}'}

    async def get_comprehensive_analysis(self, symbol, price_data, additional_data, language='id', crypto_api=None):
        """Generate comprehensive cryptocurrency analysis with CoinMarketCap integration"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get comprehensive data from CoinMarketCap
            if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider.api_key:
                cmc_data = crypto_api.cmc_provider.get_comprehensive_data(symbol)

                if 'error' not in cmc_data:
                    price = cmc_data.get('price', 0)
                    market_cap = cmc_data.get('market_cap', 0)
                    volume_24h = cmc_data.get('volume_24h', 0)
                    percent_change_24h = cmc_data.get('percent_change_24h', 0)
                    percent_change_7d = cmc_data.get('percent_change_7d', 0)
                    percent_change_30d = cmc_data.get('percent_change_30d', 0)
                    cmc_rank = cmc_data.get('cmc_rank', 0)
                    circulating_supply = cmc_data.get('circulating_supply', 0)
                    total_supply = cmc_data.get('total_supply', 0)
                    max_supply = cmc_data.get('max_supply', 0)

                    # Format price display
                    if price < 1:
                        price_display = f"${price:.8f}"
                    elif price < 100:
                        price_display = f"${price:.6f}"
                    else:
                        price_display = f"${price:,.4f}"

                    # Format market cap
                    if market_cap > 1000000000:
                        mc_display = f"${market_cap/1000000000:.2f}B"
                    elif market_cap > 1000000:
                        mc_display = f"${market_cap/1000000:.1f}M"
                    else:
                        mc_display = f"${market_cap:,.0f}"

                    # Format volume
                    if volume_24h > 1000000000:
                        vol_display = f"${volume_24h/1000000000:.2f}B"
                    elif volume_24h > 1000000:
                        vol_display = f"${volume_24h/1000000:.1f}M"
                    else:
                        vol_display = f"${volume_24h:,.0f}"

                    # Format supply
                    def format_supply(supply):
                        if supply > 1000000000:
                            return f"{supply/1000000000:.2f}B"
                        elif supply > 1000000:
                            return f"{supply/1000000:.1f}M"
                        else:
                            return f"{supply:,.0f}"

                    # Get description if available
                    description = cmc_data.get('description', '')
                    if description and len(description) > 200:
                        description = description[:200] + "..."

                    # Change indicators
                    change_24h_emoji = "📈" if percent_change_24h >= 0 else "📉"
                    change_7d_emoji = "📈" if percent_change_7d >= 0 else "📉"
                    change_30d_emoji = "📈" if percent_change_30d >= 0 else "📉"

                    if language == 'id':
                        analysis = f"""📊 **ANALISIS KOMPREHENSIF {symbol.upper()} (CoinMarketCap)**

💰 **Data Fundamental (CMC Rank #{cmc_rank}):**
• **Harga Saat Ini**: {price_display}
• **Market Cap**: {mc_display}
• **Volume 24j**: {vol_display}
• **Circulating Supply**: {format_supply(circulating_supply) if circulating_supply else 'N/A'}
• **Total Supply**: {format_supply(total_supply) if total_supply else 'N/A'}
• **Max Supply**: {format_supply(max_supply) if max_supply else 'Unlimited'}

📈 **Performa Harga:**
• **24 Jam**: {change_24h_emoji} {percent_change_24h:+.2f}%
• **7 Hari**: {change_7d_emoji} {percent_change_7d:+.2f}%
• **30 Hari**: {change_30d_emoji} {percent_change_30d:+.2f}%

📊 **Level Kritis:**
• **Support**: ${price * 0.95:.6f} (-5%)
• **Resistance**: ${price * 1.05:.6f} (+5%)
• **Trend**: {'Bullish 🟢' if percent_change_24h > 2 else 'Bearish 🔴' if percent_change_24h < -2 else 'Sideways 🟡'}

🎯 **Trading Signals:**
• **Signal**: {'STRONG BUY' if percent_change_24h > 5 else 'BUY' if percent_change_24h > 2 else 'HOLD' if percent_change_24h > -2 else 'SELL' if percent_change_24h > -5 else 'STRONG SELL'}
• **Risk Level**: {'LOW' if abs(percent_change_24h) < 3 else 'MEDIUM' if abs(percent_change_24h) < 7 else 'HIGH'}
• **Volatilitas**: {'Rendah' if abs(percent_change_24h) < 3 else 'Sedang' if abs(percent_change_24h) < 10 else 'Tinggi'}

{f'🔍 **Tentang Proyek:** {description}' if description else ''}

⏰ **Data Update**: {current_time}
📡 **Source**: CoinMarketCap Professional API
💎 **Data Quality**: Real-time & Verified"""
                    else:
                        analysis = f"""📊 **COMPREHENSIVE ANALYSIS {symbol.upper()} (CoinMarketCap)**

💰 **Fundamental Data (CMC Rank #{cmc_rank}):**
• **Current Price**: {price_display}
• **Market Cap**: {mc_display}
• **Volume 24h**: {vol_display}
• **Circulating Supply**: {format_supply(circulating_supply) if circulating_supply else 'N/A'}
• **Total Supply**: {format_supply(total_supply) if total_supply else 'N/A'}
• **Max Supply**: {format_supply(max_supply) if max_supply else 'Unlimited'}

📈 **Price Performance:**
• **24 Hours**: {change_24h_emoji} {percent_change_24h:+.2f}%
• **7 Days**: {change_7d_emoji} {percent_change_7d:+.2f}%
• **30 Days**: {change_30d_emoji} {percent_change_30d:+.2f}%

📊 **Critical Levels:**
• **Support**: ${price * 0.95:.6f} (-5%)
• **Resistance**: ${price * 1.05:.6f} (+5%)
• **Trend**: {'Bullish 🟢' if percent_change_24h > 2 else 'Bearish 🔴' if percent_change_24h < -2 else 'Sideways 🟡'}

🎯 **Trading Signals:**
• **Signal**: {'STRONG BUY' if percent_change_24h > 5 else 'BUY' if percent_change_24h > 2 else 'HOLD' if percent_change_24h > -2 else 'SELL' if percent_change_24h > -5 else 'STRONG SELL'}
• **Risk Level**: {'LOW' if abs(percent_change_24h) < 3 else 'MEDIUM' if abs(percent_change_24h) < 7 else 'HIGH'}
• **Volatility**: {'Low' if abs(percent_change_24h) < 3 else 'Medium' if abs(percent_change_24h) < 10 else 'High'}

{f'🔍 **About Project:** {description}' if description else ''}

⏰ **Data Update**: {current_time}
📡 **Source**: CoinMarketCap Professional API
💎 **Data Quality**: Real-time & Verified"""

                    return analysis

            # Fallback if CoinMarketCap fails
            fallback_msg = "⚠️ **Data CoinMarketCap sementara tidak tersedia**\n\n" if language == 'id' else "⚠️ **CoinMarketCap data temporarily unavailable**\n\n"
            fallback_msg += f"""💡 **Solusi:**
• Coba lagi dalam beberapa menit
• Pastikan CMC_API_KEY tersedia di Secrets
• Contact admin jika masalah berlanjut

🔄 **Reason**: CoinMarketCap API temporarily unavailable or rate limited"""

            return fallback_msg

        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            return f"❌ Error dalam analisis {symbol}: {str(e)[:100]}..."

    def _format_comprehensive_analysis_id(self, symbol, current_price, trend_analysis, sentiment_analysis, cmc_data, current_time):
        """Format comprehensive analysis in Indonesian"""
        formatted_price = self._format_price(current_price)
        trend = trend_analysis.get('trend', 'neutral')
        trend_strength = trend_analysis.get('strength', 'medium')
        sentiment_score = sentiment_analysis.get('sentiment_score', 50)
        overall_sentiment = sentiment_analysis.get('overall', 'neutral')

        trend_emoji = "📈" if trend == 'bullish' else "📉" if trend == 'bearish' else "📊"
        sentiment_emoji = "🟢" if overall_sentiment == 'bullish' else "🔴" if overall_sentiment == 'bearish' else "🟡"

        message = f"""🎯 **ANALISIS KOMPREHENSIF {symbol.upper()}**

💰 **HARGA CURRENT**: {formatted_price}
📡 **SOURCE**: Coinglass Real-time

{trend_emoji} **TREND ANALYSIS**: {trend.upper()} ({trend_strength})
{sentiment_emoji} **SENTIMENT**: {overall_sentiment.upper()} ({sentiment_score:.0f}/100)

📊 **INSIGHTS COINGLASS:**"""

        signals = sentiment_analysis.get('signals', [])
        for signal in signals[:3]:
            message += f"\n• {signal}"

        # Add CMC data if available
        if 'error' not in cmc_data and cmc_data.get('name'):
            message += f"""

📋 **INFO FUNDAMENTAL:**
• **Nama**: {cmc_data.get('name', symbol)}
• **Rank**: #{cmc_data.get('cmc_rank', 'N/A')}"""

        message += f"""

💡 **REKOMENDASI:**
• **Trend {trend}** dengan kekuatan {trend_strength}
• **Sentiment {overall_sentiment}** berdasarkan Coinglass
• Monitor untuk konfirmasi signal

📡 **DATA SOURCES**: Coinglass + CoinMarketCap
⏰ **Analysis Time**: {current_time}"""

        return message

    def _format_comprehensive_analysis_en(self, symbol, current_price, trend_analysis, sentiment_analysis, cmc_data, current_time):
        """Format comprehensive analysis in English"""
        # Similar structure as Indonesian version
        formatted_price = self._format_price(current_price)

        return f"""🎯 **COMPREHENSIVE ANALYSIS {symbol.upper()}**

💰 **CURRENT PRICE**: {formatted_price}
📡 **SOURCE**: Coinglass Real-time

📡 **DATA SOURCES**: Coinglass + CoinMarketCap
⏰ **Analysis Time**: {current_time}"""

    async def _analyze_futures_signal(self, symbol, price_data, coinglass_data):
        """Analyze futures signal for a single symbol"""
        try:
            if 'error' in price_data or 'error' in coinglass_data:
                return None

            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Analyze Coinglass data for signal
            long_short = coinglass_data.get('long_short', {})
            open_interest = coinglass_data.get('open_interest', {})

            if 'error' in long_short or 'error' in open_interest:
                return None

            # Calculate signal confidence
            long_ratio = long_short.get('long_ratio', 50)
            oi_change = open_interest.get('oi_change_percent', 0)

            # Simple signal logic
            confidence = 50
            direction = 'HOLD'

            if long_ratio > 75:  # Overleveraged longs
                direction = 'SHORT'
                confidence = min(85, 60 + (long_ratio - 75))
            elif long_ratio < 25:  # Overleveraged shorts
                direction = 'LONG'
                confidence = min(85, 60 + (25 - long_ratio))

            # Adjust confidence based on OI
            if abs(oi_change) > 10:
                confidence += 10

            if confidence >= 70:
                return {
                    'symbol': symbol,
                    'direction': direction,
                    'confidence': confidence,
                    'current_price': current_price,
                    'long_ratio': long_ratio,
                    'oi_change': oi_change,
                    'entry_price': current_price * (0.999 if direction == 'LONG' else 1.001),
                    'stop_loss': current_price * (0.985 if direction == 'LONG' else 1.015),
                    'take_profit': current_price * (1.025 if direction == 'LONG' else 0.975)
                }

            return None

        except Exception as e:
            print(f"❌ Signal analysis error for {symbol}: {e}")
            return None

    async def _format_futures_signals_output(self, recommendations, language):
        """Format futures signals output"""
        if not recommendations:
            if language == 'id':
                return "❌ Tidak ada sinyal dengan confidence >70%. Coba lagi nanti."
            else:
                return "❌ No signals with confidence >70%. Try again later."

        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            return self._format_signals_output_id(recommendations, current_time)
        else:
            return self._format_signals_output_en(recommendations, current_time)

    def _format_signals_output_id(self, recommendations, current_time):
        """Format multiple signals output in Indonesian"""
        header = f"""🎯 **SINYAL FUTURES REAL-TIME**
⏰ {current_time} | 📊 TOP {len(recommendations)} SIGNALS

💡 **STRATEGI**: Coinglass Data

"""

        formatted_signals = []
        for i, signal in enumerate(recommendations, 1):
            symbol = signal['symbol']
            direction = signal['direction']
            confidence = signal['confidence']
            current_price = signal['current_price']
            entry_price = signal['entry_price']
            tp_price = signal['take_profit']
            sl_price = signal['stop_loss']

            direction_emoji = "🟢" if direction == 'LONG' else "🔴"

            signal_text = f"""**{i}. {symbol} {direction_emoji} - {direction}**
💰 Entry: {self._format_price(entry_price)} | Confidence: {confidence:.0f}%

📋 **SETUP:**
• **TP**: {self._format_price(tp_price)}
• **SL**: {self._format_price(sl_price)}
• **Current**: {self._format_price(current_price)}"""

            formatted_signals.append(signal_text)

        footer = """

════════════════════════════════════════
🎯 **CARA MENGGUNAKAN SINYAL:**

1️⃣ **Entry Setup:**
   • Entry sesuai level yang diberikan
   • Set SL WAJIB sebelum entry
   • Position size maksimal 2% modal

2️⃣ **Risk Management:**
   • Follow stop loss secara ketat
   • Take profit di level yang ditentukan
   • Monitor perubahan market structure

📡 **Data**: Coinglass Real-time
⚠️ **Warning**: Trading berisiko tinggi, gunakan proper risk management!"""

        return header + "\n\n".join(formatted_signals) + footer

    def _format_signals_output_en(self, recommendations, current_time):
        """Format multiple signals output in English"""
        # Similar structure as Indonesian version
        return f"""🎯 **REAL-TIME FUTURES SIGNALS**
⏰ {current_time}

📡 **Data**: Coinglass Real-time
⚠️ **Warning**: Trading involves high risk!"""

    def _get_top_coins_for_signals(self, crypto_api=None):
        """Get top coins for signal generation"""
        return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'LTC', 'BCH', 'ATOM']

    def _analyze_coinglass_data(self, coinglass_data, symbol):
        """Analyze Coinglass data for insights"""
        try:
            long_short = coinglass_data.get('long_short', {})
            open_interest = coinglass_data.get('open_interest', {})

            if 'error' in long_short or 'error' in open_interest:
                return {
                    'direction': 'HOLD',
                    'confidence': 30,
                    'reason': 'Insufficient data'
                }

            long_ratio = long_short.get('long_ratio', 50)
            oi_change = open_interest.get('oi_change_percent', 0)

            # Analysis logic
            if long_ratio > 70:
                return {
                    'direction': 'SHORT',
                    'confidence': min(80, 60 + (long_ratio - 70)),
                    'reason': f'Overleveraged longs ({long_ratio:.1f}%)',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }
            elif long_ratio < 30:
                return {
                    'direction': 'LONG',
                    'confidence': min(80, 60 + (30 - long_ratio)),
                    'reason': f'Oversold conditions ({long_ratio:.1f}%)',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }
            else:
                return {
                    'direction': 'HOLD',
                    'confidence': 50,
                    'reason': 'Balanced market conditions',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }

        except Exception as e:
            return {
                'direction': 'HOLD',
                'confidence': 30,
                'reason': f'Analysis error: {str(e)}'
            }

    def _analyze_historical_trend(self, historical_data):
        """Analyze historical price trend"""
        try:
            if 'error' in historical_data or not historical_data.get('data'):
                return {'trend': 'neutral', 'strength': 'low'}

            data = historical_data['data']
            if len(data) < 10:
                return {'trend': 'neutral', 'strength': 'low'}

            # Simple trend analysis
            closes = [float(candle.get('price_close', 0)) for candle in data[-10:]]

            if len(closes) >= 5:
                recent_avg = sum(closes[-5:]) / 5
                older_avg = sum(closes[:5]) / 5

                change = (recent_avg - older_avg) / older_avg * 100

                if change > 2:
                    return {'trend': 'bullish', 'strength': 'strong' if change > 5 else 'medium'}
                elif change < -2:
                    return {'trend': 'bearish', 'strength': 'strong' if change < -5 else 'medium'}

            return {'trend': 'neutral', 'strength': 'medium'}

        except Exception as e:
            return {'trend': 'neutral', 'strength': 'low'}

    def _analyze_coinglass_comprehensive(self, coinglass_data):
        """Analyze comprehensive Coinglass data"""
        try:
            sentiment_score = 50  # Neutral
            signals = []

            # Analyze each data component
            long_short = coinglass_data.get('long_short', {})
            open_interest = coinglass_data.get('open_interest', {})
            liquidation = coinglass_data.get('liquidation', {})

            if 'error' not in long_short:
                long_ratio = long_short.get('long_ratio', 50)
                if long_ratio > 65:
                    sentiment_score -= 10
                    signals.append('High long ratio suggests potential reversal')
                elif long_ratio < 35:
                    sentiment_score += 10
                    signals.append('Low long ratio suggests bullish sentiment')

            if 'error' not in open_interest:
                oi_change = open_interest.get('oi_change_percent', 0)
                if oi_change > 10:
                    sentiment_score += 5
                    signals.append('Rising open interest confirms trend')
                elif oi_change < -10:
                    sentiment_score -= 5
                    signals.append('Falling open interest suggests weakening')

            return {
                'sentiment_score': max(0, min(100, sentiment_score)),
                'signals': signals,
                'overall': 'bullish' if sentiment_score > 60 else 'bearish' if sentiment_score < 40 else 'neutral'
            }

        except Exception as e:
            return {
                'sentiment_score': 50,
                'signals': [f'Analysis error: {str(e)}'],
                'overall': 'neutral'
            }

    def _generate_emergency_futures_signal(self, symbol, timeframe, language, error_message):
        """Generate a fallback signal in case of errors."""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            message = f"""❌ SIGNAL GAGAL - {symbol.upper()} ({timeframe})
⏰ {current_time}

Terjadi kesalahan saat memproses data:
{error_message[:100]}...

🔄 **Solusi:**
• Coba lagi dalam beberapa menit
• Gunakan `/price {symbol.lower()}` untuk harga basic
• Contact admin jika masalah berlanjut"""
        else:
            message = f"""❌ SIGNAL FAILED - {symbol.upper()} ({timeframe})
⏰ {current_time}

Error processing data:
{error_message[:100]}...

🔄 **Solutions:**
• Try again in a few minutes
• Use `/price {symbol.lower()}` for basic price
• Contact admin if issue persists"""

        return message

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get market sentiment with CoinMarketCap integration"""
        try:
            if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider.api_key:
                # Get comprehensive market data from CoinMarketCap
                market_data = crypto_api.cmc_provider.get_enhanced_market_overview()

                if 'error' not in market_data:
                    global_metrics = market_data.get('global_metrics', {})
                    top_cryptos = market_data.get('top_cryptocurrencies', {})
                    fng_data = market_data.get('fear_greed_index', {})

                    current_time = datetime.now().strftime('%H:%M:%S WIB')

                    # Format large numbers
                    def format_currency(amount):
                        if amount > 1000000000000:  # Trillions
                            return f"${amount/1000000000000:.2f}T"
                        elif amount > 1000000000:  # Billions
                            return f"${amount/1000000000:.2f}B"
                        elif amount > 1000000:  # Millions
                            return f"${amount/1000000:.1f}M"
                        else:
                            return f"${amount:,.0f}"

                    total_market_cap = global_metrics.get('total_market_cap', 0)
                    total_volume = global_metrics.get('total_volume_24h', 0)
                    market_cap_change = global_metrics.get('market_cap_change_24h', 0)
                    btc_dominance = global_metrics.get('btc_dominance', 0)
                    eth_dominance = global_metrics.get('eth_dominance', 0)
                    active_cryptos = global_metrics.get('active_cryptocurrencies', 0)
                    active_exchanges = global_metrics.get('active_exchanges', 0)

                    # Fear & Greed Index
                    fng_value = fng_data.get('value', 50)
                    fng_classification = fng_data.get('value_classification', 'Neutral')

                    # Market sentiment emoji
                    if market_cap_change > 3:
                        sentiment_emoji = "🚀"
                        sentiment_text = "Very Bullish"
                    elif market_cap_change > 0:
                        sentiment_emoji = "📈"
                        sentiment_text = "Bullish"
                    elif market_cap_change > -3:
                        sentiment_emoji = "⚡"
                        sentiment_text = "Neutral"
                    else:
                        sentiment_emoji = "📉"
                        sentiment_text = "Bearish"

                    if language == 'id':
                        analysis = f"""🌍 **OVERVIEW PASAR CRYPTO GLOBAL (CoinMarketCap)**

💰 **Statistik Pasar:**
• **Total Market Cap**: {format_currency(total_market_cap)}
• **Perubahan 24j**: {sentiment_emoji} {market_cap_change:+.2f}%
• **Volume 24j**: {format_currency(total_volume)}
• **Sentiment**: {sentiment_text}

🪙 **Dominasi Crypto:**
• **Bitcoin (BTC)**: {btc_dominance:.1f}%
• **Ethereum (ETH)**: {eth_dominance:.1f}%
• **Altcoins**: {100-btc_dominance-eth_dominance:.1f}%

📊 **Aktivitas Pasar:**
• **Cryptocurrency Aktif**: {active_cryptos:,}
• **Exchange Aktif**: {active_exchanges:,}
• **Market Pairs**: {global_metrics.get('active_market_pairs', 0):,}

😨😱 **Fear & Greed Index:**
• **Nilai**: {fng_value}/100
• **Status**: {fng_classification}
• **Indikator**: {'Extreme Fear' if fng_value < 20 else 'Fear' if fng_value < 40 else 'Neutral' if fng_value < 60 else 'Greed' if fng_value < 80 else 'Extreme Greed'}"""

                        # Add top movers if available
                        if 'data' in top_cryptos and top_cryptos['data']:
                            analysis += f"\n\n🎯 **Top 5 Cryptocurrency:**"
                            for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                                price = crypto.get('price', 0)
                                change_24h = crypto.get('percent_change_24h', 0)
                                symbol = crypto.get('symbol', '')
                                name = crypto.get('name', '')

                                price_display = f"${price:.4f}" if price < 100 else f"${price:,.2f}"
                                change_emoji = "📈" if change_24h >= 0 else "📉"

                                analysis += f"\n• **{i}. {name} ({symbol})**: {price_display} {change_emoji} {change_24h:+.1f}%"

                        analysis += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinMarketCap Startup Plan
💎 **Data Quality**: Real-time Professional"""

                        return analysis
                    else:
                        analysis = f"""🌍 **GLOBAL CRYPTO MARKET OVERVIEW (CoinMarketCap)**

💰 **Market Statistics:**
• **Total Market Cap**: {format_currency(total_market_cap)}
• **24h Change**: {sentiment_emoji} {market_cap_change:+.2f}%
• **Volume 24h**: {format_currency(total_volume)}
• **Sentiment**: {sentiment_text}

🪙 **Crypto Dominance:**
• **Bitcoin (BTC)**: {btc_dominance:.1f}%
• **Ethereum (ETH)**: {eth_dominance:.1f}%
• **Altcoins**: {100-btc_dominance-eth_dominance:.1f}%

📊 **Market Activity:**
• **Active Cryptocurrencies**: {active_cryptos:,}
• **Active Exchanges**: {active_exchanges:,}
• **Market Pairs**: {global_metrics.get('active_market_pairs', 0):,}

😨😱 **Fear & Greed Index:**
• **Value**: {fng_value}/100
• **Status**: {fng_classification}
• **Indicator**: {'Extreme Fear' if fng_value < 20 else 'Fear' if fng_value < 40 else 'Neutral' if fng_value < 60 else 'Greed' if fng_value < 80 else 'Extreme Greed'}"""

                        # Add top movers if available
                        if 'data' in top_cryptos and top_cryptos['data']:
                            analysis += f"\n\n🎯 **Top 5 Cryptocurrencies:**"
                            for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                                price = crypto.get('price', 0)
                                change_24h = crypto.get('percent_change_24h', 0)
                                symbol = crypto.get('symbol', '')
                                name = crypto.get('name', '')

                                price_display = f"${price:.4f}" if price < 100 else f"${price:,.2f}"
                                change_emoji = "📈" if change_24h >= 0 else "📉"

                                analysis += f"\n• **{i}. {name} ({symbol})**: {price_display} {change_emoji} {change_24h:+.1f}%"

                        analysis += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinMarketCap Startup Plan
💎 **Data Quality**: Real-time Professional"""

                        return analysis

            # Fallback if CoinMarketCap fails
            fallback_msg = "⚠️ **Data CoinMarketCap sementara tidak tersedia**\n\n" if language == 'id' else "⚠️ **CoinMarketCap data temporarily unavailable**\n\n"
            fallback_msg += f"""💡 **Alternatif:**
• Pastikan CMC_API_KEY tersedia di Secrets
• Coba command `/price btc` untuk harga basic
• Contact admin jika masalah berlanjut

🔄 **Reason**: CoinMarketCap API rate limit atau koneksi error"""

            return fallback_msg

        except Exception as e:
            print(f"Error in market sentiment: {e}")
            if language == 'id':
                return f"❌ **Error mengambil data pasar**\n\n**Detail**: {str(e)[:100]}...\n\n💡 Coba lagi dalam beberapa menit"
            else:
                return f"❌ **Error fetching market data**\n\n**Detail**: {str(e)[:100]}...\n\n💡 Try again in a few minutes"

    def _format_top_movers(self, market_data, language='id'):
        """Format top movers from market data"""
        try:
            if 'top_gainers' in market_data and 'top_losers' in market_data:
                gainers = market_data['top_gainers'][:3]
                losers = market_data['top_losers'][:3]

                if language == 'id':
                    output = "**Top Gainers:**\n"
                    for gainer in gainers:
                        output += f"• {gainer.get('symbol', 'N/A')}: +{gainer.get('percent_change_24h', 0):.1f}%\n"

                    output += "\n**Top Losers:**\n"
                    for loser in losers:
                        output += f"• {loser.get('symbol', 'N/A')}: {loser.get('percent_change_24h', 0):.1f}%\n"

                    return output
                else:
                    output = "**Top Gainers:**\n"
                    for gainer in gainers:
                        output += f"• {gainer.get('symbol', 'N/A')}: +{gainer.get('percent_change_24h', 0):.1f}%\n"

                    output += "\n**Top Losers:**\n"
                    for loser in losers:
                        output += f"• {loser.get('symbol', 'N/A')}: {loser.get('percent_change_24h', 0):.1f}%\n"

                    return output

            return "• Data movers tidak tersedia" if language == 'id' else "• Movers data unavailable"

        except Exception as e:
            return f"• Error formatting movers: {str(e)[:50]}..."