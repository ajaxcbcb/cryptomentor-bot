# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
from datetime import datetime
import html
from crypto_api import CryptoAPI

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name

        # Initialize CryptoAPI for comprehensive data
        self.crypto_api = CryptoAPI()

        print(f"✅ AI Assistant initialized with Binance API integration")

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

🚀 **Semua analisis menggunakan data real-time dari Binance API!**"""

    def get_binance_futures_data(self, symbol="BTCUSDT"):
        """Get futures data from Binance API"""
        try:
            base_url = "https://fapi.binance.com"

            # Clean symbol format
            if not symbol.upper().endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get long/short ratio
            long_short_url = f"{base_url}/futures/data/globalLongShortAccountRatio"
            long_short_params = {'symbol': symbol, 'period': '30m', 'limit': 1}

            # Get funding rate
            funding_url = f"{base_url}/fapi/v1/fundingRate"
            funding_params = {'symbol': symbol, 'limit': 1}

            # Get open interest
            oi_url = f"{base_url}/fapi/v1/openInterest"
            oi_params = {'symbol': symbol}

            # Get 24hr ticker statistics
            ticker_url = f"{base_url}/fapi/v1/ticker/24hr"
            ticker_params = {'symbol': symbol}

            # Make requests
            long_short_response = requests.get(long_short_url, params=long_short_params, timeout=10)
            funding_response = requests.get(funding_url, params=funding_params, timeout=10)
            oi_response = requests.get(oi_url, params=oi_params, timeout=10)
            ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)

            # Parse responses
            long_short_data = long_short_response.json()[0] if long_short_response.status_code == 200 and long_short_response.json() else {}
            funding_data = funding_response.json()[0] if funding_response.status_code == 200 and funding_response.json() else {}
            oi_data = oi_response.json() if oi_response.status_code == 200 else {}
            ticker_data = ticker_response.json() if ticker_response.status_code == 200 else {}

            return {
                'symbol': symbol,
                'price': float(ticker_data.get('lastPrice', 0)),
                'price_change_24h': float(ticker_data.get('priceChangePercent', 0)),
                'volume_24h': float(ticker_data.get('volume', 0)),
                'long_short_ratio': float(long_short_data.get('longShortRatio', 1.0)),
                'long_account': float(long_short_data.get('longAccount', 50)),
                'short_account': float(long_short_data.get('shortAccount', 50)),
                'funding_rate': float(funding_data.get('fundingRate', 0)),
                'open_interest': float(oi_data.get('openInterest', 0)),
                'source': 'binance_futures_api',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f'Binance futures data error: {str(e)}',
                'symbol': symbol,
                'source': 'binance_error'
            }

    def analyze_futures_binance(self, symbol="BTCUSDT"):
        """Analyze futures using Binance data"""
        try:
            data = self.get_binance_futures_data(symbol)

            if 'error' in data:
                return f"❌ Error: {data['error']}"

            # Determine trend based on long/short ratio and funding rate
            long_ratio = data.get('long_short_ratio', 1.0)
            funding_rate = data.get('funding_rate', 0)
            price_change = data.get('price_change_24h', 0)

            # Analysis logic
            if long_ratio > 1.2 and funding_rate > 0.01:
                trend = "Bearish"
                signal = "🔴 SHORT"
                reason = "Overleveraged longs + high funding rate"
            elif long_ratio < 0.8 and funding_rate < -0.005:
                trend = "Bullish"
                signal = "🟢 LONG"
                reason = "Oversold conditions + negative funding"
            elif price_change > 5:
                trend = "Bullish"
                signal = "🟢 LONG"
                reason = "Strong upward momentum"
            elif price_change < -5:
                trend = "Bearish"
                signal = "🔴 SHORT"
                reason = "Strong downward momentum"
            else:
                trend = "Neutral"
                signal = "⏸️ HOLD"
                reason = "Mixed signals"

            return f"""🎯 FUTURES ANALYSIS - {symbol}

💰 Price: ${data['price']:,.2f}
📊 24h Change: {data['price_change_24h']:+.2f}%
📈 Long/Short Ratio: {data['long_short_ratio']:.2f}
💸 Funding Rate: {data['funding_rate']*100:.4f}%
💰 Open Interest: ${float(data['open_interest']):,.0f}

{signal}
📈 Trend: {trend}
💡 Reason: {reason}

📡 Source: Binance Futures API"""

        except Exception as e:
            return f"❌ Analysis error: {str(e)}"

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis using Binance API"""
        try:
            print(f"🎯 Starting Binance futures analysis for {symbol} {timeframe}")

            # Get Binance futures data
            binance_data = self.get_binance_futures_data(symbol)

            if 'error' in binance_data:
                return self._generate_emergency_futures_signal(symbol, timeframe, language, binance_data['error'])

            # Generate trading signal
            trading_signal = self._format_binance_futures_analysis(
                symbol, timeframe, binance_data, language
            )

            return trading_signal

        except Exception as e:
            print(f"❌ Error in futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _format_binance_futures_analysis(self, symbol, timeframe, binance_data, language='id'):
        """Format Binance futures analysis output"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Extract data
            price = binance_data.get('price', 0)
            price_change = binance_data.get('price_change_24h', 0)
            long_ratio = binance_data.get('long_short_ratio', 1.0)
            funding_rate = binance_data.get('funding_rate', 0)
            open_interest = binance_data.get('open_interest', 0)

            # Generate signal
            signal_analysis = self._analyze_binance_signal(binance_data)
            direction = signal_analysis['direction']
            confidence = signal_analysis['confidence']
            reason = signal_analysis['reason']

            # Format price display
            def format_price(price):
                if price < 1:
                    return f"${price:.6f}"
                elif price < 100:
                    return f"${price:.4f}"
                else:
                    return f"${price:,.2f}"

            # Direction emoji
            if direction == 'LONG':
                direction_emoji = "🟢"
                signal_emoji = "📈"
            elif direction == 'SHORT':
                direction_emoji = "🔴"
                signal_emoji = "📉"
            else:
                direction_emoji = "⏸️"
                signal_emoji = "📊"

            if language == 'id':
                message = f"""🎯 **ANALISA FUTURES - {symbol.upper()} ({timeframe})**

💰 **Data Real-time (Binance):**
• **Harga**: {format_price(price)}
• **Perubahan 24j**: {price_change:+.2f}%
• **Funding Rate**: {funding_rate*100:+.4f}%

{direction_emoji} **SINYAL**: **{direction}** {signal_emoji}
📊 **Confidence**: {confidence:.0f}%

📊 **ANALISA MENDALAM:**
• **Long/Short Ratio**: {long_ratio:.2f}"""

                if long_ratio > 1.3:
                    message += f" (⚠️ Overleveraged Longs)"
                elif long_ratio < 0.7:
                    message += f" (💎 Oversold Conditions)"
                else:
                    message += f" (⚖️ Balanced)"

                message += f"""
• **Open Interest**: ${open_interest:,.0f}
• **Funding Rate**: {funding_rate*100:+.4f}%"""

                if funding_rate > 0.01:
                    message += f" (💸 Longs overpaying)"
                elif funding_rate < -0.005:
                    message += f" (💰 Shorts overpaying)"
                else:
                    message += f" (⚖️ Neutral)"

                message += f"""

🧠 **SMART MONEY ANALYSIS:**
• **Reason**: {reason}
• **Market Sentiment**: {'Bullish' if long_ratio > 1.2 else 'Bearish' if long_ratio < 0.8 else 'Neutral'}
• **Funding Bias**: {'Bullish expensive' if funding_rate > 0.01 else 'Bearish expensive' if funding_rate < -0.005 else 'Neutral'}"""

                if direction != 'HOLD':
                    entry_price = price * (0.998 if direction == 'LONG' else 1.002)
                    tp1 = price * (1.025 if direction == 'LONG' else 0.975)
                    tp2 = price * (1.05 if direction == 'LONG' else 0.95)
                    sl = price * (0.975 if direction == 'LONG' else 1.025)

                    message += f"""

📌 **TRADING SETUP:**
┣━ 📍 **ENTRY**: {format_price(entry_price)}
┣━ 🎯 **TP1**: {format_price(tp1)} (RR 2:1)
┣━ 🎯 **TP2**: {format_price(tp2)} (RR 4:1)
┗━ 🛡️ **STOP LOSS**: {format_price(sl)} (**WAJIB!**)

💡 **Strategi**: {reason}"""
                else:
                    message += f"""

⏸️ **HOLD POSITION**
• **Alasan**: {reason}
• **Tunggu**: Setup yang lebih jelas
• **Monitor**: Perubahan funding rate & ratio"""

                message += f"""

⏰ **Update**: {current_time}
📡 **Source**: Binance Futures API
⭐ **Status**: Real-time Analysis Active"""

            else:
                # English version
                message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

💰 **Real-time Data (Binance):**
• **Price**: {format_price(price)}
• **24h Change**: {price_change:+.2f}%
• **Funding Rate**: {funding_rate*100:+.4f}%

{direction_emoji} **SIGNAL**: **{direction}** {signal_emoji}
📊 **Confidence**: {confidence:.0f}%

📊 **COMPREHENSIVE ANALYSIS:**
• **Long/Short Ratio**: {long_ratio:.2f}"""

                if long_ratio > 1.3:
                    message += f" (⚠️ Overleveraged Longs)"
                elif long_ratio < 0.7:
                    message += f" (💎 Oversold Conditions)"
                else:
                    message += f" (⚖️ Balanced)"

                message += f"""
• **Open Interest**: ${open_interest:,.0f}
• **Funding Rate**: {funding_rate*100:+.4f}%"""

                if funding_rate > 0.01:
                    message += f" (💸 Longs overpaying)"
                elif funding_rate < -0.005:
                    message += f" (💰 Shorts overpaying)"
                else:
                    message += f" (⚖️ Neutral)"

                message += f"""

🧠 **SMART MONEY ANALYSIS:**
• **Reason**: {reason}
• **Market Sentiment**: {'Bullish' if long_ratio > 1.2 else 'Bearish' if long_ratio < 0.8 else 'Neutral'}
• **Funding Bias**: {'Bullish expensive' if funding_rate > 0.01 else 'Bearish expensive' if funding_rate < -0.005 else 'Neutral'}"""

                if direction != 'HOLD':
                    entry_price = price * (0.998 if direction == 'LONG' else 1.002)
                    tp1 = price * (1.025 if direction == 'LONG' else 0.975)
                    tp2 = price * (1.05 if direction == 'LONG' else 0.95)
                    sl = price * (0.975 if direction == 'LONG' else 1.025)

                    message += f"""

📌 **TRADING SETUP:**
• **ENTRY**: {format_price(entry_price)}
• **TP1**: {format_price(tp1)}
• **STOP LOSS**: {format_price(sl)}"""

                message += f"""

⏰ **Update**: {current_time}
📡 **Source**: Binance Futures API
⭐ **Status**: Real-time Analysis Active"""

            return message

        except Exception as e:
            print(f"❌ Error formatting Binance analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _analyze_binance_signal(self, binance_data):
        """Analyze Binance data for trading signal"""
        try:
            long_ratio = binance_data.get('long_short_ratio', 1.0)
            funding_rate = binance_data.get('funding_rate', 0)
            price_change = binance_data.get('price_change_24h', 0)

            direction = 'HOLD'
            confidence = 50
            reason = 'Mixed signals'

            # Long/Short ratio analysis (contrarian)
            if long_ratio > 1.4:
                direction = 'SHORT'
                confidence += 25
                reason = f'Overleveraged longs (Ratio: {long_ratio:.2f})'
            elif long_ratio < 0.6:
                direction = 'LONG'
                confidence += 20
                reason = f'Oversold conditions (Ratio: {long_ratio:.2f})'

            # Funding rate analysis
            if funding_rate > 0.015:
                direction = 'SHORT'
                confidence += 30
                reason = f'Extreme funding rate {funding_rate*100:.3f}%'
            elif funding_rate < -0.008:
                direction = 'LONG'
                confidence += 25
                reason = f'Negative funding {funding_rate*100:.3f}%'

            # Price momentum
            if abs(price_change) > 5:
                confidence += 10
                if price_change > 0 and direction != 'SHORT':
                    direction = 'LONG'
                    reason += f' + Strong momentum ({price_change:+.1f}%)'
                elif price_change < 0 and direction != 'LONG':
                    direction = 'SHORT'
                    reason += f' + Bearish momentum ({price_change:+.1f}%)'

            confidence = min(95, max(30, confidence))

            if confidence < 65:
                direction = 'HOLD'
                reason = 'Mixed signals - wait for clearer setup'

            return {
                'direction': direction,
                'confidence': confidence,
                'reason': reason
            }

        except Exception as e:
            return {
                'direction': 'HOLD',
                'confidence': 40,
                'reason': f'Analysis error: {str(e)[:50]}...'
            }

    async def generate_futures_signals(self, language='id', crypto_api=None, context_args=None):
        """Generate futures signals using Binance API"""
        try:
            # Get top coins for analysis
            top_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOT', 'MATIC', 'LINK']

            # Process query args if provided
            if context_args and len(context_args) > 0:
                raw_query = ' '.join(context_args).upper()
                query_parts = raw_query.split()
                cleaned_parts = [part for part in query_parts if part != 'SND']

                if cleaned_parts:
                    if any(tf in cleaned_parts[0] for tf in ['M', 'H', 'D', 'W']):
                        timeframe = cleaned_parts[0]
                        symbol = cleaned_parts[1] if len(cleaned_parts) > 1 else 'BTC'
                    else:
                        symbol = cleaned_parts[0]
                        timeframe = '1H'

                    return await self.get_futures_analysis(symbol, timeframe, language, crypto_api)

            current_time = datetime.now().strftime('%H:%M:%S WIB')
            high_confidence_signals = []
            total_analyzed = 0
            successful_analysis = 0

            if language == 'id':
                header = f"""🎯 **SINYAL FUTURES BINANCE**
⏰ {current_time}

📊 **Analisis Real-time Binance:**
"""
            else:
                header = f"""🎯 **BINANCE FUTURES SIGNALS**
⏰ {current_time}

📊 **Real-time Binance Analysis:**
"""

            # Analyze each coin with Binance data
            for symbol in top_coins[:8]:
                try:
                    total_analyzed += 1

                    # Get Binance futures data
                    binance_data = self.get_binance_futures_data(symbol + 'USDT')

                    if 'error' not in binance_data:
                        successful_analysis += 1

                        # Generate trading signal
                        signal_analysis = self._analyze_binance_signal(binance_data)

                        # Only include high-confidence signals
                        if signal_analysis['confidence'] >= 70 and signal_analysis['direction'] != 'HOLD':
                            signal_data = {
                                'symbol': symbol,
                                'direction': signal_analysis['direction'],
                                'confidence': signal_analysis['confidence'],
                                'entry_price': binance_data['price'],
                                'tp1': binance_data['price'] * (1.03 if signal_analysis['direction'] == 'LONG' else 0.97),
                                'sl': binance_data['price'] * (0.97 if signal_analysis['direction'] == 'LONG' else 1.03),
                                'reason': signal_analysis['reason']
                            }
                            high_confidence_signals.append(signal_data)

                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

            # Format results
            if high_confidence_signals:
                signals_text = header

                for i, signal in enumerate(high_confidence_signals[:6], 1):
                    symbol = signal['symbol']
                    direction = signal['direction']
                    confidence = signal['confidence']
                    entry = signal['entry_price']
                    tp1 = signal['tp1']
                    sl = signal['sl']
                    reason = signal['reason']

                    # Direction emoji
                    if direction == 'LONG':
                        emoji = "🟢"
                        signal_emoji = "📈"
                    elif direction == 'SHORT':
                        emoji = "🔴"
                        signal_emoji = "📉"
                    else:
                        emoji = "⏸️"
                        signal_emoji = "📊"

                    def format_price(price):
                        if price < 1:
                            return f"${price:.6f}"
                        elif price < 100:
                            return f"${price:.4f}"
                        else:
                            return f"${price:,.2f}"

                    signals_text += f"""
**{i}. {symbol}** {emoji} **{direction}** {signal_emoji} ({confidence}%)
• Entry: {format_price(entry)} | TP: {format_price(tp1)} | SL: {format_price(sl)}
• Reason: {reason[:60]}{'...' if len(reason) > 60 else ''}"""

                if language == 'id':
                    signals_text += f"""

🎯 **Ringkasan Analysis:**
• **High-Confidence Signals**: {len(high_confidence_signals)}/{total_analyzed} coins
• **Success Rate**: {(successful_analysis/total_analyzed)*100:.0f}%
• **Min Confidence**: 70%+ (Strong signals only)
• **Method**: Binance Long/Short + Funding + Price momentum

⚠️ **Risk Management:**
• Max 2% modal per trade
• SL WAJIB sebelum entry
• Monitor funding rate shifts
• Diversifikasi max 3 posisi simultan

📡 **Data Sources**: Binance Futures API
🔄 **Update**: Real-time
⭐ **Premium** – Advanced Signal Logic"""
                else:
                    signals_text += f"""

🎯 **Analysis Summary:**
• **High-Confidence Signals**: {len(high_confidence_signals)}/{total_analyzed} coins
• **Success Rate**: {(successful_analysis/total_analyzed)*100:.0f}%
• **Min Confidence**: 70%+ (Strong signals only)
• **Method**: Binance Long/Short + Funding + Price momentum

⚠️ **Risk Management:**
• Max 2% capital per trade
• MANDATORY stop loss before entry
• Monitor funding rate shifts
• Diversify max 3 simultaneous positions

📡 **Data Sources**: Binance Futures API
🔄 **Update**: Real-time
⭐ **Premium** – Advanced Signal Logic"""

                return signals_text
            else:
                if language == 'id':
                    return f"""😔 **Tidak Ada Sinyal High-Confidence (70%+)**

🔍 **Status Analysis:**
• Coins Analyzed: {successful_analysis}/{total_analyzed}
• Data Source: Binance Futures API
• Confidence Threshold: 70%+ (Premium filtering)

💡 **Market Condition:**
• Market dalam kondisi sideways/uncertainty
• Menunggu setup yang jelas
• Funding rates dalam range normal

🎯 **Alternative:**
• Gunakan `/futures <symbol>` untuk analisis spesifik coin
• Coba lagi dalam 30-60 menit

⏰ Update: {current_time}"""
                else:
                    return f"""😔 **No High-Confidence Signals (70%+) Found**

🔍 **Analysis Status:**
• Coins Analyzed: {successful_analysis}/{total_analyzed}
• Data Source: Binance Futures API
• Confidence Threshold: 70%+ (Premium filtering)

💡 **Market Condition:**
• Market in sideways/uncertainty mode
• Waiting for clear setup
• Funding rates in normal ranges

🎯 **Alternative:**
• Use `/futures <symbol>` for specific coin analysis
• Try again in 30-60 minutes

⏰ Update: {current_time}"""

        except Exception as e:
            print(f"Error in futures signals: {e}")
            return self._generate_emergency_futures_signal('MULTI', '1H', language, str(e))

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

                    # Get BTC futures data for sentiment analysis
                    btc_futures = self.get_binance_futures_data('BTC')
                    btc_long_ratio = btc_futures.get('long_short_ratio', 1.0) if 'error' not in btc_futures else 1.0

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

                        # Add market-wide trading recommendations
                        overall_sentiment_score = 0

                        # Market cap change factor
                        if market_cap_change > 5:
                            overall_sentiment_score += 3
                        elif market_cap_change > 2:
                            overall_sentiment_score += 2
                        elif market_cap_change > 0:
                            overall_sentiment_score += 1
                        elif market_cap_change < -5:
                            overall_sentiment_score -= 3
                        elif market_cap_change < -2:
                            overall_sentiment_score -= 2
                        elif market_cap_change < 0:
                            overall_sentiment_score -= 1

                        # Fear & Greed factor
                        if fng_value < 20:  # Extreme Fear - contrarian bullish
                            overall_sentiment_score += 2
                        elif fng_value > 80:  # Extreme Greed - contrarian bearish
                            overall_sentiment_score -= 2

                        # Futures sentiment factor
                        if 'error' not in btc_futures:
                            if btc_long_ratio > 1.4:  # Too many longs
                                overall_sentiment_score -= 1
                            elif btc_long_ratio < 0.6:  # Too many shorts
                                overall_sentiment_score += 1

                        # Generate market recommendation
                        if overall_sentiment_score >= 4:
                            market_rec = "🟢 **BULLISH MARKET** - Good time untuk accumulate"
                            market_action = "• **Action**: DCA strategy pada major coins\n• **Focus**: BTC, ETH, strong altcoins\n• **Risk**: Medium - Market momentum positif"
                        elif overall_sentiment_score >= 2:
                            market_rec = "🟡 **CAUTIOUSLY BULLISH** - Selective buying"
                            market_action = "• **Action**: Cherry-pick strong performers\n• **Focus**: Top 10 coins dengan volume tinggi\n• **Risk**: Medium - Mixed signals"
                        elif overall_sentiment_score <= -4:
                            market_rec = "🔴 **BEARISH MARKET** - Risk-off mode"
                            market_action = "• **Action**: Cash/stablecoin position\n• **Focus**: Wait for better entry points\n• **Risk**: High - Trend masih bearish"
                        elif overall_sentiment_score <= -2:
                            market_rec = "🟠 **CAUTIOUSLY BEARISH** - Limited exposure"
                            market_action = "• **Action**: Small position sizing\n• **Focus**: Strong fundamental coins only\n• **Risk**: High - Volatility tinggi"
                        else:
                            market_rec = "⚖️ **NEUTRAL MARKET** - Range-bound"
                            market_action = "• **Action**: Range trading strategies\n• **Focus**: Scalping opportunities\n• **Risk**: Medium - Sideways movement"

                        analysis += f"""

🎯 **MARKET OUTLOOK & RECOMMENDATION:**
{market_rec}

📋 **Trading Strategy:**
{market_action}

💡 **Key Levels untuk Monitor:**
• **BTC Dominance**: {btc_dominance:.1f}% (Alt season jika <40%)
• **Total Market Cap**: {format_currency(total_market_cap)}
• **24h Volume**: {format_currency(total_volume)}

⏰ **Update**: {current_time} WIB
📡 **Sources**: CoinMarketCap Pro + Binance Futures
💎 **Analysis**: Real-time Multi-API Integration
⭐ **Premium**: Advanced Market Intelligence"""

                        return analysis
                    else:
                        # English version
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

                        # Add market-wide trading recommendations
                        overall_sentiment_score = 0

                        # Market cap change factor
                        if market_cap_change > 5:
                            overall_sentiment_score += 3
                        elif market_cap_change > 2:
                            overall_sentiment_score += 2
                        elif market_cap_change > 0:
                            overall_sentiment_score += 1
                        elif market_cap_change < -5:
                            overall_sentiment_score -= 3
                        elif market_cap_change < -2:
                            overall_sentiment_score -= 2
                        elif market_cap_change < 0:
                            overall_sentiment_score -= 1

                        # Fear & Greed factor
                        if fng_value < 20:  # Extreme Fear - contrarian bullish
                            overall_sentiment_score += 2
                        elif fng_value > 80:  # Extreme Greed - contrarian bearish
                            overall_sentiment_score -= 2

                        # Futures sentiment factor
                        if 'error' not in btc_futures:
                            if btc_long_ratio > 1.4:  # Too many longs
                                overall_sentiment_score -= 1
                            elif btc_long_ratio < 0.6:  # Too many shorts
                                overall_sentiment_score += 1

                        # Generate market recommendation
                        if overall_sentiment_score >= 4:
                            market_rec = "🟢 **BULLISH MARKET** - Good time to accumulate"
                            market_action = "• **Action**: DCA strategy on major coins\n• **Focus**: BTC, ETH, strong altcoins\n• **Risk**: Medium - Positive market momentum"
                        elif overall_sentiment_score >= 2:
                            market_rec = "🟡 **CAUTIOUSLY BULLISH** - Selective buying"
                            market_action = "• **Action**: Cherry-pick strong performers\n• **Focus**: Top 10 coins with high volume\n• **Risk**: Medium - Mixed signals"
                        elif overall_sentiment_score <= -4:
                            market_rec = "🔴 **BEARISH MARKET** - Risk-off mode"
                            market_action = "• **Action**: Cash/stablecoin positions\n• **Focus**: Wait for better entry points\n• **Risk**: High - Downtrend persists"
                        elif overall_sentiment_score <= -2:
                            market_rec = "🟠 **CAUTIOUSLY BEARISH** - Limited exposure"
                            market_action = "• **Action**: Small position sizing\n• **Focus**: Strong fundamental coins only\n• **Risk**: High - High volatility"
                        else:
                            market_rec = "⚖️ **NEUTRAL MARKET** - Range-bound"
                            market_action = "• **Action**: Range trading strategies\n• **Focus**: Scalping opportunities\n• **Risk**: Medium - Sideways movement"

                        analysis += f"""

🎯 **MARKET OUTLOOK & RECOMMENDATION:**
{market_rec}

📋 **Trading Strategy:**
{market_action}

💡 **Key Levels to Monitor:**
• **BTC Dominance**: {btc_dominance:.1f}% (Alt season if <40%)
• **Total Market Cap**: {format_currency(total_market_cap)}
• **24h Volume**: {format_currency(total_volume)}

⏰ **Update**: {current_time}
📡 **Sources**: CoinMarketCap Pro + Binance Futures
💎 **Analysis**: Real-time Multi-API Integration
⭐ **Premium**: Advanced Market Intelligence"""

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

    def get_comprehensive_analysis(self, symbol, timeframe=None, leverage=None, risk=None, crypto_api=None):
        """Get comprehensive analysis using Binance + CoinMarketCap integration"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            data_sources = []
            successful_sources = 0
            total_sources = 2  # CMC, Binance

            # Initialize data containers
            cmc_data = {'error': 'Not fetched'}
            binance_data = {'error': 'Not fetched'}

            # 1. Get CoinMarketCap data
            try:
                if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider and crypto_api.cmc_provider.api_key:
                    cmc_data = crypto_api.cmc_provider.get_cryptocurrency_quotes(symbol)

                    if (cmc_data and
                        isinstance(cmc_data, dict) and
                        'error' not in cmc_data):

                        # Get additional info and merge safely
                        try:
                            cmc_info = crypto_api.cmc_provider.get_cryptocurrency_info(symbol)
                            if cmc_info and isinstance(cmc_info, dict) and 'error' not in cmc_info:
                                cmc_data.update(cmc_info)
                        except:
                            pass  # Info is optional

                        data_sources.append("✅ CoinMarketCap")
                        successful_sources += 1
                    else:
                        data_sources.append("⚠️ CoinMarketCap")
                        cmc_data = {'error': 'Invalid response'}
                else:
                    data_sources.append("❌ CoinMarketCap")
                    cmc_data = {'error': 'API not available'}
            except Exception as e:
                data_sources.append("❌ CoinMarketCap")
                cmc_data = {'error': f'Exception: {str(e)}'}
                print(f"CoinMarketCap API error: {e}")

            # 2. Get Binance futures data
            try:
                binance_data = self.get_binance_futures_data(symbol)

                if 'error' not in binance_data and binance_data.get('price', 0) > 0:
                    data_sources.append("✅ Binance")
                    successful_sources += 1
                else:
                    data_sources.append("⚠️ Binance")
            except Exception as e:
                data_sources.append("❌ Binance")
                binance_data = {'error': f'Exception: {str(e)}'}
                print(f"❌ Binance API error: {e}")

            # Determine data quality
            if successful_sources >= 2:
                quality = "EXCELLENT"
                quality_emoji = "✅"
            elif successful_sources >= 1:
                quality = "GOOD"
                quality_emoji = "🟡"
            else:
                quality = "LIMITED"
                quality_emoji = "⚠️"

            # Extract price data (prioritize CMC, fallback to Binance)
            current_price = 0
            change_24h = 0
            volume_24h = 0
            funding_rate = 0
            price_source = "Estimasi"

            # Try CMC first
            if ('error' not in cmc_data and
                cmc_data.get('price') is not None and
                cmc_data.get('price', 0) > 0):
                current_price = float(cmc_data.get('price', 0))
                change_24h = float(cmc_data.get('percent_change_24h', 0))
                volume_24h = float(cmc_data.get('volume_24h', 0))
                price_source = "CoinMarketCap"
            # Fallback to Binance
            elif ('error' not in binance_data and
                  binance_data.get('price', 0) > 0):
                current_price = float(binance_data.get('price', 0))
                change_24h = float(binance_data.get('price_change_24h', 0))
                volume_24h = float(binance_data.get('volume_24h', 0))
                price_source = "Binance"
            # Final fallback to estimated price
            else:
                current_price = float(self._get_estimated_price(symbol))
                change_24h = 0
                volume_24h = 0
                price_source = "Estimasi"

            # Get funding rate from Binance
            if 'error' not in binance_data:
                funding_rate = float(binance_data.get('funding_rate', 0))

            # Build comprehensive analysis
            analysis = f"""🎯 **ANALISIS KOMPREHENSIF {symbol.upper()}**

🔍 **Kualitas Data**: {quality_emoji} {quality} ({successful_sources}/{total_sources} sumber berhasil)
📡 **Sumber**: {', '.join(data_sources)}

💰 **1. Harga Terkini**
• Real-time Price: {self._format_price_display(current_price)} ({price_source})
• 24h Change: {change_24h:+.2f}%
• Volume 24h: {self._format_currency_display(volume_24h)}"""

            # Add CMC data if available
            if 'error' not in cmc_data:
                market_cap = cmc_data.get('market_cap', 0)
                rank = cmc_data.get('cmc_rank', 0)
                circulating_supply = cmc_data.get('circulating_supply', 0)

                analysis += f"""

📈 **2. Market Overview (CoinMarketCap)**"""

                if market_cap and market_cap > 0:
                    analysis += f"\n• Market Cap: {self._format_currency_display(market_cap)}"
                if rank and rank > 0:
                    analysis += f"\n• Rank: #{rank}"
                if circulating_supply and circulating_supply > 0:
                    analysis += f"\n• Supply Beredar: {circulating_supply:,.0f} {symbol.upper()}"
            else:
                analysis += f"\n• ⚠️ Data CoinMarketCap tidak tersedia"

            # Add Binance futures data
            if 'error' not in binance_data:
                long_ratio = binance_data.get('long_short_ratio', 1.0)
                open_interest = binance_data.get('open_interest', 0)

                analysis += f"""

📊 **3. Futures Data (Binance)**
• Funding Rate: {funding_rate*100:+.4f}%
• Long/Short Ratio: {long_ratio:.2f}
• Open Interest: {self._format_currency_display(open_interest)}"""

                if long_ratio > 1.3:
                    analysis += f" (⚠️ Overleveraged longs)"
                elif long_ratio < 0.7:
                    analysis += f" (💎 Oversold conditions)"
                else:
                    analysis += f" (⚖️ Balanced)"
            else:
                analysis += f"""

📊 **3. Futures Data (Binance)**
• ⚠️ Binance Futures data unavailable"""

            # Risk assessment
            risk_level = "🟠 Sedang"
            if change_24h > 10:
                risk_level = "🔴 Tinggi"
            elif change_24h < -10:
                risk_level = "🔴 Tinggi"
            elif abs(change_24h) < 3:
                risk_level = "🟢 Rendah"

            # Generate recommendation
            if change_24h > 5 and successful_sources >= 2:
                recommendation = "BUY/LONG"
                rec_emoji = "🟢"
            elif change_24h < -5 and successful_sources >= 2:
                recommendation = "WAIT/SHORT"
                rec_emoji = "🔴"
            else:
                recommendation = "HOLD/WAIT"
                rec_emoji = "🟡"

            analysis += f"""

⚠️ **4. Risk Assessment**
• Risk Level: {risk_level}
• Volatilitas: {'Tinggi' if abs(change_24h) > 5 else 'Normal'}

📌 **5. Kesimpulan & Rekomendasi**
• Rekomendasi: {rec_emoji} {recommendation}
• Confidence: {70 if successful_sources >= 2 else 50}%

🕐 **Update**: {current_time} WIB
⭐️ **Status** – Binance + CoinMarketCap Integration"""

            return analysis

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Error in comprehensive analysis: {e}")
            import traceback
            traceback.print_exc()

            return f"""❌ **ANALISIS ERROR**

Terjadi kesalahan saat memproses data multi-API.

**Error**: {error_msg}

🔄 **Solusi**:
• Coba lagi dalam beberapa menit
• Gunakan `/futures {symbol.lower()}` sebagai alternatif

💡 **Note**: Menggunakan Binance API sebagai sumber utama"""

    def _get_estimated_price(self, symbol):
        """Helper to get an estimated price, fallback based on symbol"""
        price_estimates = {
            'BTC': 70000.0, 'ETH': 4000.0, 'BNB': 600.0, 'SOL': 200.0,
            'XRP': 0.6, 'ADA': 0.5, 'DOGE': 0.15, 'AVAX': 40.0,
            'DOT': 8.0, 'MATIC': 1.0, 'LINK': 15.0, 'UNI': 10.0,
            'LTC': 100.0, 'BCH': 500.0, 'ATOM': 12.0
        }

        estimated_price = price_estimates.get(symbol.upper(), 50.0)
        print(f"⚠️ Using estimated price for {symbol}: ${estimated_price}")
        return estimated_price

    def _format_price_display(self, price):
        """Format price for display with null safety"""
        if price is None or price <= 0:
            return "$0.00"

        try:
            price = float(price)
            if price < 1:
                return f"${price:.8f}"
            elif price < 100:
                return f"${price:.4f}"
            else:
                return f"${price:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    def _format_currency_display(self, amount):
        """Format currency for display with null safety"""
        if amount is None or amount <= 0:
            return "$0"

        try:
            amount = float(amount)
            if amount >= 1_000_000_000_000:
                return f"${amount/1_000_000_000_000:.2f}T"
            elif amount >= 1_000_000_000:
                return f"${amount/1_000_000_000:.2f}B"
            elif amount >= 1_000_000:
                return f"${amount/1_000_000:.1f}M"
            else:
                return f"${amount:,.0f}"
        except (ValueError, TypeError):
            return "$0"

    def _generate_emergency_futures_signal(self, symbol, timeframe, language='id', error_msg=""):
        """Generate a fallback signal in case of errors."""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

⚠️ **Data API tidak tersedia**
💰 **Harga Estimasi**: {self._format_price_display(self._get_estimated_price(symbol))}

📊 **Status**: Menggunakan analisa fallback
🧠 **Rekomendasi**: ⏸️ HOLD
• **Alasan**: Data tidak mencukupi untuk sinyal akurat
• **Tunggu**: Koneksi API pulih

🛡 **Risk Management**
• Jangan trading tanpa data lengkap
• Tunggu sinyal dengan confidence tinggi
• Monitor update selanjutnya

📡 **Error**: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}
⏰ **Update**: {current_time}

💡 **Solusi**: Sistem menggunakan Binance API sebagai sumber utama"""
        else:
            message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

⚠️ **API data unavailable**
💰 **Estimated Price**: {self._format_price_display(self._get_estimated_price(symbol))}

📊 **Status**: Using fallback analysis
🧠 **Recommendation**: ⏸️ HOLD
• **Reason**: Insufficient data for accurate signal
• **Wait**: API connection recovery

🛡 **Risk Management**
• Don't trade without complete data
• Wait for high confidence signals
• Monitor next updates

📡 **Error**: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}
⏰ **Update**: {current_time}

💡 **Solution**: System using Binance API as primary source"""

        return message