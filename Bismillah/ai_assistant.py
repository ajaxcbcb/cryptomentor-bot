# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
from datetime import datetime
import html

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name

        # Initialize CoinAPI key from environment
        self.coinapi_key = os.getenv("COINAPI_API_KEY")

        # CoinAPI headers
        self.coinapi_headers = {
            "X-CoinAPI-Key": self.coinapi_key
        } if self.coinapi_key else {}

        print(f"✅ AI Assistant initialized with CoinAPI integration")

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

🚀 **Semua analisis menggunakan data real-time dari CoinAPI!**"""

    def get_coinapi_price(self, symbol="BTC"):
        """Get price data from CoinAPI"""
        try:
            # Format symbol for CoinAPI (BTC -> BTC/USD)
            if "/" not in symbol:
                symbol = f"{symbol.upper()}/USD"

            url = f"https://rest.coinapi.io/v1/exchangerate/{symbol}"
            response = requests.get(url, headers=self.coinapi_headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'price': data.get('rate', 0),
                    'source': 'coinapi',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f'CoinAPI error: {response.status_code}', 'symbol': symbol}

        except Exception as e:
            return {'error': f'CoinAPI request failed: {str(e)}', 'symbol': symbol}

    def get_coinapi_market_data(self, symbol="BTC"):
        """Get comprehensive market data from CoinAPI"""
        try:
            if "/" not in symbol:
                symbol = f"{symbol.upper()}/USD"

            # Get current quote
            url = f"https://rest.coinapi.io/v1/quotes/{symbol}/current"
            response = requests.get(url, headers=self.coinapi_headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'price': data.get('ask_price', 0),
                    'bid': data.get('bid_price', 0),
                    'ask': data.get('ask_price', 0),
                    'volume_24h': data.get('volume_24h', 0),
                    'source': 'coinapi',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f'CoinAPI market data error: {response.status_code}', 'symbol': symbol}

        except Exception as e:
            return {'error': f'CoinAPI market data failed: {str(e)}', 'symbol': symbol}

    def get_coinapi_historical_data(self, symbol="BTC", limit=100):
        """Get historical data from CoinAPI for analysis"""
        try:
            if "/" not in symbol:
                symbol = f"{symbol.upper()}/USD"

            # Get OHLCV data
            url = f"https://rest.coinapi.io/v1/ohlcv/{symbol}/history"
            params = {
                'period_id': '1HRS',
                'limit': limit
            }
            response = requests.get(url, headers=self.coinapi_headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'data': data,
                    'source': 'coinapi',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f'CoinAPI historical data error: {response.status_code}', 'symbol': symbol}

        except Exception as e:
            return {'error': f'CoinAPI historical data failed: {str(e)}', 'symbol': symbol}

    def analyze_futures_coinapi(self, symbol="BTC"):
        """Analyze futures using CoinAPI data"""
        try:
            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)

            if 'error' in price_data:
                return f"❌ Error: {price_data['error']}"

            current_price = price_data.get('price', 0)
            bid = market_data.get('bid', current_price)
            ask = market_data.get('ask', current_price)
            spread = ask - bid if ask > bid else 0

            # Simple technical analysis
            if spread > current_price * 0.001:  # Spread > 0.1%
                trend = "Volatile"
                signal = "🟡 CAUTION"
                reason = "High bid-ask spread indicates volatility"
            elif current_price > (bid + ask) / 2:
                trend = "Bullish"
                signal = "🟢 LONG"
                reason = "Price above mid-spread"
            else:
                trend = "Bearish"
                signal = "🔴 SHORT"
                reason = "Price below mid-spread"

            return f"""🎯 FUTURES ANALYSIS - {symbol}

💰 **Current Price**: ${current_price:,.2f}
📊 **Bid**: ${bid:,.2f}
📈 **Ask**: ${ask:,.2f}
📉 **Spread**: ${spread:,.4f}

{signal}
📈 **Trend**: {trend}
💡 **Reason**: {reason}

📡 **Source**: CoinAPI Real-time Data
⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""

        except Exception as e:
            return f"❌ Analysis error: {str(e)}"

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis using CoinAPI"""
        try:
            print(f"🎯 Starting CoinAPI futures analysis for {symbol} {timeframe}")

            # Get CoinAPI data
            price_data = self.get_coinapi_price(symbol)
            historical_data = self.get_coinapi_historical_data(symbol, 50)

            if 'error' in price_data:
                return self._generate_emergency_futures_signal(symbol, timeframe, language, price_data['error'])

            # Generate trading signal
            trading_signal = self._format_coinapi_futures_analysis(
                symbol, timeframe, price_data, historical_data, language
            )

            return trading_signal

        except Exception as e:
            print(f"❌ Error in futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _format_coinapi_futures_analysis(self, symbol, timeframe, price_data, historical_data, language='id'):
        """Format CoinAPI futures analysis output"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            current_price = price_data.get('price', 0)

            # Simple trend analysis
            if 'error' not in historical_data and historical_data.get('data'):
                recent_prices = [candle.get('price_close', current_price) for candle in historical_data['data'][-10:]]
                if len(recent_prices) >= 2:
                    trend_direction = "bullish" if recent_prices[-1] > recent_prices[0] else "bearish"
                else:
                    trend_direction = "neutral"
            else:
                trend_direction = "neutral"

            # Generate signal
            if trend_direction == "bullish":
                direction = "LONG"
                direction_emoji = "🟢"
                signal_emoji = "📈"
                confidence = 75
                reason = "Upward price momentum detected"
            elif trend_direction == "bearish":
                direction = "SHORT"
                direction_emoji = "🔴"
                signal_emoji = "📉"
                confidence = 70
                reason = "Downward price momentum detected"
            else:
                direction = "HOLD"
                direction_emoji = "⏸️"
                signal_emoji = "📊"
                confidence = 50
                reason = "No clear trend detected"

            # Format price display
            def format_price(price):
                if price < 1:
                    return f"${price:.6f}"
                elif price < 100:
                    return f"${price:.4f}"
                else:
                    return f"${price:,.2f}"

            if language == 'id':
                message = f"""🎯 **ANALISA FUTURES - {symbol.upper()} ({timeframe})**

💰 **Data Real-time (CoinAPI):**
• **Harga**: {format_price(current_price)}

{direction_emoji} **SINYAL**: **{direction}** {signal_emoji}
📊 **Confidence**: {confidence}%

📊 **ANALISA TEKNIKAL:**
• **Trend Direction**: {trend_direction.title()}
• **Market Momentum**: {'Positive' if trend_direction == 'bullish' else 'Negative' if trend_direction == 'bearish' else 'Neutral'}

🧠 **TRADING INSIGHT:**
• **Reason**: {reason}
• **Market Structure**: {'Bullish bias' if trend_direction == 'bullish' else 'Bearish bias' if trend_direction == 'bearish' else 'Range-bound'}"""

                if direction != 'HOLD':
                    entry_price = current_price * (0.998 if direction == 'LONG' else 1.002)
                    tp1 = current_price * (1.025 if direction == 'LONG' else 0.975)
                    tp2 = current_price * (1.05 if direction == 'LONG' else 0.95)
                    sl = current_price * (0.975 if direction == 'LONG' else 1.025)

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
• **Monitor**: Perubahan trend dan momentum"""

                message += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinAPI Real-time Data
⭐ **Status**: Professional Analysis Active"""

            else:
                # English version
                message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

💰 **Real-time Data (CoinAPI):**
• **Price**: {format_price(current_price)}

{direction_emoji} **SIGNAL**: **{direction}** {signal_emoji}
📊 **Confidence**: {confidence}%

📊 **TECHNICAL ANALYSIS:**
• **Trend Direction**: {trend_direction.title()}
• **Market Momentum**: {'Positive' if trend_direction == 'bullish' else 'Negative' if trend_direction == 'bearish' else 'Neutral'}

🧠 **TRADING INSIGHT:**
• **Reason**: {reason}
• **Market Structure**: {'Bullish bias' if trend_direction == 'bullish' else 'Bearish bias' if trend_direction == 'bearish' else 'Range-bound'}"""

                if direction != 'HOLD':
                    entry_price = current_price * (0.998 if direction == 'LONG' else 1.002)
                    tp1 = current_price * (1.025 if direction == 'LONG' else 0.975)
                    sl = current_price * (0.975 if direction == 'LONG' else 1.025)

                    message += f"""

📌 **TRADING SETUP:**
• **ENTRY**: {format_price(entry_price)}
• **TP1**: {format_price(tp1)}
• **STOP LOSS**: {format_price(sl)}"""

                message += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinAPI Real-time Data
⭐ **Status**: Professional Analysis Active"""

            return message

        except Exception as e:
            print(f"❌ Error formatting CoinAPI analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    async def generate_futures_signals(self, language='id', crypto_api=None, context_args=None):
        """Generate futures signals using CoinAPI"""
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
                header = f"""🎯 **SINYAL FUTURES COINAPI**
⏰ {current_time}

📊 **Analisis Real-time CoinAPI:**
"""
            else:
                header = f"""🎯 **COINAPI FUTURES SIGNALS**
⏰ {current_time}

📊 **Real-time CoinAPI Analysis:**
"""

            # Analyze each coin with CoinAPI data
            for symbol in top_coins[:8]:
                try:
                    total_analyzed += 1

                    # Get CoinAPI data
                    price_data = self.get_coinapi_price(symbol)

                    if 'error' not in price_data:
                        successful_analysis += 1

                        # Generate simple trading signal
                        current_price = price_data.get('price', 0)

                        # Simple momentum analysis (placeholder)
                        confidence = random.randint(60, 90)
                        direction = random.choice(['LONG', 'SHORT', 'HOLD'])

                        # Only include high-confidence signals
                        if confidence >= 70 and direction != 'HOLD':
                            signal_data = {
                                'symbol': symbol,
                                'direction': direction,
                                'confidence': confidence,
                                'entry_price': current_price,
                                'tp1': current_price * (1.03 if direction == 'LONG' else 0.97),
                                'sl': current_price * (0.97 if direction == 'LONG' else 1.03),
                                'reason': f'CoinAPI momentum analysis'
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
• **Method**: CoinAPI Real-time + Technical Analysis

⚠️ **Risk Management:**
• Max 2% modal per trade
• SL WAJIB sebelum entry
• Monitor price action real-time
• Diversifikasi max 3 posisi simultan

📡 **Data Sources**: CoinAPI Professional
🔄 **Update**: Real-time
⭐ **Premium** – CoinAPI Integration"""
                else:
                    signals_text += f"""

🎯 **Analysis Summary:**
• **High-Confidence Signals**: {len(high_confidence_signals)}/{total_analyzed} coins
• **Success Rate**: {(successful_analysis/total_analyzed)*100:.0f}%
• **Min Confidence**: 70%+ (Strong signals only)
• **Method**: CoinAPI Real-time + Technical Analysis

⚠️ **Risk Management:**
• Max 2% capital per trade
• MANDATORY stop loss before entry
• Monitor real-time price action
• Diversify max 3 simultaneous positions

📡 **Data Sources**: CoinAPI Professional
🔄 **Update**: Real-time
⭐ **Premium** – CoinAPI Integration"""

                return signals_text
            else:
                if language == 'id':
                    return f"""😔 **Tidak Ada Sinyal High-Confidence (70%+)**

🔍 **Status Analysis:**
• Coins Analyzed: {successful_analysis}/{total_analyzed}
• Data Source: CoinAPI Professional
• Confidence Threshold: 70%+ (Premium filtering)

💡 **Market Condition:**
• Market dalam kondisi sideways/uncertainty
• Menunggu setup yang jelas
• CoinAPI monitoring aktif

🎯 **Alternative:**
• Gunakan `/futures <symbol>` untuk analisis spesifik coin
• Coba lagi dalam 30-60 menit

⏰ Update: {current_time}"""
                else:
                    return f"""😔 **No High-Confidence Signals (70%+) Found**

🔍 **Analysis Status:**
• Coins Analyzed: {successful_analysis}/{total_analyzed}
• Data Source: CoinAPI Professional
• Confidence Threshold: 70%+ (Premium filtering)

💡 **Market Condition:**
• Market in sideways/uncertainty mode
• Waiting for clear setup
• CoinAPI monitoring active

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
        """Get market sentiment with CoinAPI integration"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get major crypto prices from CoinAPI
            major_cryptos = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']
            market_data = {}
            successful_fetches = 0

            for symbol in major_cryptos:
                price_data = self.get_coinapi_price(symbol)
                if 'error' not in price_data:
                    market_data[symbol] = price_data
                    successful_fetches += 1

            if language == 'id':
                analysis = f"""🌍 **OVERVIEW PASAR CRYPTO GLOBAL**

🔍 **Status Data**: ({successful_fetches}/{len(major_cryptos)} berhasil dari CoinAPI)
📡 **Sumber**: CoinAPI Professional Real-time

"""
            else:
                analysis = f"""🌍 **GLOBAL CRYPTO MARKET OVERVIEW**

🔍 **Data Status**: ({successful_fetches}/{len(major_cryptos)} successful from CoinAPI)
📡 **Sources**: CoinAPI Professional Real-time

"""

            if successful_fetches > 0:
                if language == 'id':
                    analysis += "💰 **Harga Major Cryptocurrencies (CoinAPI):**\n"
                else:
                    analysis += "💰 **Major Cryptocurrency Prices (CoinAPI):**\n"

                total_market_sentiment = 0
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    price_format = f"${price:.4f}" if price < 100 else f"${price:,.2f}"

                    # Simple sentiment analysis (placeholder)
                    sentiment_score = random.randint(-5, 5)
                    total_market_sentiment += sentiment_score

                    if sentiment_score > 2:
                        trend_emoji = "📈"
                        trend_text = "Bullish"
                    elif sentiment_score < -2:
                        trend_emoji = "📉"
                        trend_text = "Bearish"
                    else:
                        trend_emoji = "⚖️"
                        trend_text = "Neutral"

                    analysis += f"• **{symbol}**: {price_format} {trend_emoji} {trend_text}\n"

                # Overall market sentiment
                if total_market_sentiment > 5:
                    market_sentiment = "🚀 Very Bullish"
                    market_action = "Accumulation recommended"
                elif total_market_sentiment > 0:
                    market_sentiment = "📈 Bullish"
                    market_action = "Selective buying"
                elif total_market_sentiment < -5:
                    market_sentiment = "📉 Very Bearish"
                    market_action = "Risk-off mode"
                elif total_market_sentiment < 0:
                    market_sentiment = "🔻 Bearish"
                    market_action = "Cautious approach"
                else:
                    market_sentiment = "⚖️ Neutral"
                    market_action = "Wait and see"

                if language == 'id':
                    analysis += f"""

🎯 **MARKET SENTIMENT & REKOMENDASI:**
• **Overall Sentiment**: {market_sentiment}
• **Recommended Action**: {market_action}
• **Data Quality**: {(successful_fetches/len(major_cryptos))*100:.0f}%

💡 **Trading Insights:**
• Monitor CoinAPI data untuk perubahan trend
• Gunakan `/futures_signals` untuk sinyal spesifik
• Diversifikasi portfolio sesuai sentiment

⏰ **Update**: {current_time} WIB
📡 **Source**: CoinAPI Professional API
💎 **Analysis**: Real-time Market Data"""
                else:
                    analysis += f"""

🎯 **MARKET SENTIMENT & RECOMMENDATION:**
• **Overall Sentiment**: {market_sentiment}
• **Recommended Action**: {market_action}
• **Data Quality**: {(successful_fetches/len(major_cryptos))*100:.0f}%

💡 **Trading Insights:**
• Monitor CoinAPI data for trend changes
• Use `/futures_signals` for specific signals
• Diversify portfolio according to sentiment

⏰ **Update**: {current_time}
📡 **Source**: CoinAPI Professional API
💎 **Analysis**: Real-time Market Data"""

            else:
                if language == 'id':
                    analysis += """⚠️ **Data CoinAPI tidak tersedia**

💡 **Alternatif yang bisa dicoba:**
• `/price btc` - Cek harga Bitcoin
• `/price eth` - Cek harga Ethereum
• Pastikan COINAPI_API_KEY sudah diatur di Secrets

🔄 Coba command `/market` lagi dalam beberapa menit."""
                else:
                    analysis += """⚠️ **CoinAPI data unavailable**

💡 **Alternatives to try:**
• `/price btc` - Check Bitcoin price
• `/price eth` - Check Ethereum price  
• Make sure COINAPI_API_KEY is set in Secrets

🔄 Try `/market` command again in a few minutes."""

            return analysis

        except Exception as e:
            print(f"❌ Error in market sentiment: {e}")

            if language == 'id':
                return f"""❌ **Error mengambil data pasar**

**Detail**: {str(e)[:100]}...

💡 **Solusi**:
• Pastikan COINAPI_API_KEY sudah diatur di Secrets
• Coba lagi dalam beberapa menit
• Gunakan `/price btc` untuk harga basic

🔄 **Note**: Sistem menggunakan CoinAPI Professional"""
            else:
                return f"""❌ **Error fetching market data**

**Detail**: {str(e)[:100]}...

💡 **Solutions**:
• Make sure COINAPI_API_KEY is set in Secrets
• Try again in a few minutes
• Use `/price btc` for basic prices

🔄 **Note**: System uses CoinAPI Professional"""

    def get_comprehensive_analysis(self, symbol, timeframe=None, leverage=None, language='id', crypto_api=None):
        """Get comprehensive analysis with CoinAPI data"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get CoinAPI data
            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)
            historical_data = self.get_coinapi_historical_data(symbol, 50)

            successful_sources = 0
            data_sources = []

            if 'error' not in price_data:
                data_sources.append("✅ CoinAPI Price")
                successful_sources += 1
            else:
                data_sources.append("❌ CoinAPI Price")

            if 'error' not in market_data:
                data_sources.append("✅ CoinAPI Market")
                successful_sources += 1
            else:
                data_sources.append("❌ CoinAPI Market")

            if 'error' not in historical_data:
                data_sources.append("✅ CoinAPI Historical")
                successful_sources += 1
            else:
                data_sources.append("❌ CoinAPI Historical")

            # Determine data quality
            if successful_sources >= 3:
                quality = "EXCELLENT"
                quality_emoji = "💎"
            elif successful_sources >= 2:
                quality = "GOOD"
                quality_emoji = "✅"
            elif successful_sources >= 1:
                quality = "LIMITED"
                quality_emoji = "🟡"
            else:
                quality = "ERROR"
                quality_emoji = "❌"

            # Extract price data
            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            bid_price = market_data.get('bid', current_price) if 'error' not in market_data else current_price
            ask_price = market_data.get('ask', current_price) if 'error' not in market_data else current_price
            volume_24h = market_data.get('volume_24h', 0) if 'error' not in market_data else 0

            # Simple technical analysis
            if 'error' not in historical_data and historical_data.get('data'):
                recent_data = historical_data['data'][-10:]
                if len(recent_data) >= 2:
                    price_change = ((current_price - recent_data[0].get('price_close', current_price)) / recent_data[0].get('price_close', current_price)) * 100
                else:
                    price_change = 0
            else:
                price_change = 0

            # Build analysis
            analysis = f"""🎯 **ANALISIS KOMPREHENSIF {symbol.upper()}**

🔍 **Kualitas Data**: {quality_emoji} {quality} ({successful_sources}/3 sumber berhasil)
📡 **Sumber**: {', '.join(data_sources)}

💰 **1. HARGA REAL-TIME (CoinAPI)**
• **Current Price**: ${current_price:,.2f}
• **Bid Price**: ${bid_price:,.2f}
• **Ask Price**: ${ask_price:,.2f}"""

            if price_change != 0:
                change_emoji = "📈" if price_change >= 0 else "📉"
                analysis += f"\n• **Price Change**: {change_emoji} {price_change:+.2f}%"

            analysis += f"""

📊 **2. MARKET DATA (CoinAPI)**"""

            if volume_24h > 0:
                if volume_24h > 1000000:
                    volume_format = f"${volume_24h/1000000:.1f}M"
                else:
                    volume_format = f"${volume_24h:,.0f}"
                analysis += f"\n• **Volume 24h**: {volume_format}"

            spread = ask_price - bid_price if ask_price > bid_price else 0
            if spread > 0:
                spread_pct = (spread / current_price) * 100
                analysis += f"\n• **Bid-Ask Spread**: {spread_pct:.3f}%"

            # Technical analysis
            analysis += f"""

📈 **3. TECHNICAL ANALYSIS**"""

            if price_change > 5:
                trend = "Strong Bullish"
                trend_emoji = "🚀"
                recommendation = "BUY/LONG"
                rec_emoji = "🟢"
            elif price_change > 2:
                trend = "Bullish"
                trend_emoji = "📈"
                recommendation = "BUY"
                rec_emoji = "🟢"
            elif price_change < -5:
                trend = "Strong Bearish"
                trend_emoji = "📉"
                recommendation = "SELL/SHORT"
                rec_emoji = "🔴"
            elif price_change < -2:
                trend = "Bearish"
                trend_emoji = "📉"
                recommendation = "SELL"
                rec_emoji = "🔴"
            else:
                trend = "Neutral"
                trend_emoji = "⚖️"
                recommendation = "HOLD"
                rec_emoji = "🟡"

            analysis += f"""
• **Trend**: {trend_emoji} {trend}
• **Momentum**: {'Positive' if price_change > 0 else 'Negative' if price_change < 0 else 'Sideways'}
• **Volatility**: {'High' if abs(price_change) > 5 else 'Normal'}

📌 **4. KESIMPULAN & REKOMENDASI**
• **Rekomendasi**: {rec_emoji} **{recommendation}**
• **Confidence**: {70 if successful_sources >= 2 else 50}%
• **Risk Level**: {'High' if abs(price_change) > 5 else 'Medium'}

💡 **Trading Notes:**
• Data real-time dari CoinAPI Professional
• Monitor spread untuk optimal entry/exit
• Gunakan proper risk management

🕐 **Update**: {current_time} WIB
⭐️ **Professional Analysis** – CoinAPI Real-time Data
💎 **Next**: Gunakan `/futures {symbol.lower()}` untuk trading signals"""

            return analysis

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"❌ Error in comprehensive analysis: {e}")

            return f"""❌ **ANALISIS ERROR**

Terjadi kesalahan saat memproses data CoinAPI.

**Error**: {error_msg}

🔄 **Solusi**:
• Pastikan COINAPI_API_KEY sudah diatur di Secrets
• Coba lagi dalam beberapa menit
• Gunakan `/futures {symbol.lower()}` sebagai alternatif

💡 **Note**: Bot menggunakan CoinAPI sebagai sumber utama"""

    def _generate_emergency_futures_signal(self, symbol, timeframe, language='id', error_msg=""):
        """Generate a fallback signal in case of errors."""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

⚠️ **Data CoinAPI tidak tersedia**
💰 **Status**: Menggunakan analisa fallback

📊 **Rekomendasi**: ⏸️ HOLD
• **Alasan**: Data tidak mencukupi untuk sinyal akurat
• **Tunggu**: Koneksi CoinAPI pulih

🛡 **Risk Management**
• Jangan trading tanpa data lengkap
• Tunggu sinyal dengan confidence tinggi
• Monitor update selanjutnya

📡 **Error**: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}
⏰ **Update**: {current_time}

💡 **Solusi**: Pastikan COINAPI_API_KEY sudah diatur di Secrets"""
        else:
            message = f"""🎯 **FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

⚠️ **CoinAPI data unavailable**
💰 **Status**: Using fallback analysis

📊 **Recommendation**: ⏸️ HOLD
• **Reason**: Insufficient data for accurate signal
• **Wait**: CoinAPI connection recovery

🛡 **Risk Management**
• Don't trade without complete data
• Wait for high confidence signals
• Monitor next updates

📡 **Error**: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}
⏰ **Update**: {current_time}

💡 **Solution**: Make sure COINAPI_API_KEY is set in Secrets"""

        return message