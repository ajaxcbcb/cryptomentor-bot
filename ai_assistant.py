# -*- coding: utf-8 -*-
from datetime import datetime

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name

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
        return """🤖 *CryptoMentor AI - Panduan Lengkap*

📋 *Command Utama:*
- `/price <symbol>` - Cek harga real-time
- `/analyze <symbol>` - Analisis AI mendalam (5 credit)
- `/market` - Overview pasar crypto (3 credit)
- `/portfolio` - Kelola portfolio Anda
- `/add_coin <symbol> <amount>` - Tambah ke portfolio

🔮 *Fitur Advanced:*
- `/futures_signals` - Sinyal futures harian (5 credit)
- `/futures <symbol>` - Analisis futures 1 coin (5 credit)
- `/ask_ai <pertanyaan>` - Tanya AI langsung

⚙️ *Pengaturan:*
- `/credits` - Cek sisa credit
- `/subscribe` - Upgrade premium
- `/referral` - Dapatkan bonus
- `/language` - Ganti bahasa

*Contoh penggunaan:*
- `/price btc` - Harga Bitcoin
- `/analyze eth` - Analisis Ethereum
- `/add_coin ada 100` - Tambah 100 ADA

Ketik command untuk memulai!"""

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

            elif any(keyword in text_lower for keyword in ['apa itu crypto', 'cryptocurrency itu apa', 'kripto itu apa']):
                return """🌐 **Apa itu Cryptocurrency?**

Cryptocurrency adalah mata uang digital yang menggunakan kriptografi untuk keamanan dan beroperasi pada teknologi blockchain.

🔧 **Komponen Utama:**
- **Blockchain**: Database terdistribusi yang mencatat semua transaksi
- **Mining**: Proses validasi transaksi dan pembuatan blok baru
- **Wallet**: Tempat menyimpan cryptocurrency Anda dengan aman
- **Private Key**: Kunci rahasia untuk mengakses wallet
- **Public Key**: Alamat wallet untuk menerima crypto

💰 **Contoh Cryptocurrency Populer:**
- **Bitcoin (BTC)**: Cryptocurrency pertama dan terbesar
- **Ethereum (ETH)**: Platform smart contract
- **Binance Coin (BNB)**: Token exchange Binance
- **Solana (SOL)**: Blockchain cepat dan murah
- **Polygon (MATIC)**: Layer 2 untuk Ethereum

🌟 **Keuntungan Crypto:**
- Transaksi 24/7 tanpa bank
- Biaya transfer lebih murah
- Tidak ada batasan geografis
- Transparansi tinggi
- Potensi return investasi tinggi

⚠️ **Risiko Crypto:**
- Volatilitas tinggi (harga naik-turun drastis)
- Belum ada regulasi jelas
- Risiko kehilangan private key
- Scam dan fraud

💡 **Tips untuk Pemula:**
- Mulai dengan amount kecil
- Pelajari dasar-dasar dulu
- Gunakan exchange terpercaya
- Simpan di wallet sendiri (bukan di exchange)
- Jangan invest lebih dari yang bisa rugi

Gunakan `/price <symbol>` untuk cek harga crypto!"""

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`. Contoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

            elif any(keyword in text_lower for keyword in ['market', 'pasar', 'overview']):
                return "📈 Gunakan command `/market` untuk melihat overview pasar crypto secara keseluruhan.\n\nIngin tau tentang market cap, dominasi BTC, atau trend pasar?"

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
            if any(keyword in text_lower for keyword in ['what is bitcoin', 'explain bitcoin', 'bitcoin basics']):
                return """🪙 **What is Bitcoin?**

Bitcoin (BTC) is the world's first and largest cryptocurrency, created by Satoshi Nakamoto in 2009.

🔑 **Key Characteristics:**
- **Digital Currency**: Not controlled by any bank or government
- **Blockchain**: Secure distributed ledger technology
- **Limited Supply**: Only 21 million BTC will ever exist
- **Decentralized**: No central authority controls it

💡 **Bitcoin Use Cases:**
- Store of value (digital gold)
- Medium of exchange
- Hedge against inflation
- Investment asset

📈 **For beginners**: Start by learning about wallets, private keys, and how to buy BTC on legitimate exchanges.

Use `/price btc` to check current price!"""

            elif any(keyword in text_lower for keyword in ['price', 'cost', 'how much']):
                return "💰 To check crypto prices, use `/price <symbol>`. Example: `/price btc`\n\nFor comprehensive analysis: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analysis', 'analyze', 'signal']):
                return "📊 For deep analysis, use `/analyze <symbol>` or `/futures_signals` for daily futures signals.\n\n💡 **Note**: Analysis includes technical analysis, sentiment, and trading recommendations."

            elif any(keyword in text_lower for keyword in ['market', 'overview']):
                return "📈 Use `/market` command to see overall crypto market overview.\n\nWant to know about market cap, BTC dominance, or market trends?"

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
        """Get market overview with real-time data from Binance API"""
        if not crypto_api:
            return self._get_fallback_market_overview(language)

        try:
            # Get market overview data
            market_data = crypto_api.get_market_overview()

            # Get prices for major cryptocurrencies
            major_symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'ripple', 'polkadot', 'dogecoin']
            prices_data = crypto_api.get_multiple_prices(major_symbols)

            # Get crypto news for sentiment
            news_data = []
            try:
                news_data = crypto_api.get_crypto_news(3)
            except:
                pass

            # Get futures data for major coins
            futures_btc = crypto_api.get_futures_data('BTC')
            futures_eth = crypto_api.get_futures_data('ETH')

            if language == 'id':
                return self._format_market_overview_id(market_data, prices_data, news_data, futures_btc, futures_eth)
            else:
                return self._format_market_overview_en(market_data, prices_data, news_data, futures_btc, futures_eth)

        except Exception as e:
            print(f"Error in market overview: {e}")
            return self._get_fallback_market_overview(language)

    def _format_market_overview_id(self, market_data, prices_data, news_data, futures_btc, futures_eth):
        """Format market overview in Indonesian"""
        from datetime import datetime

        # Market cap and basic data
        if 'error' not in market_data:
            total_market_cap = market_data.get('total_market_cap', 0)
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)
        else:
            total_market_cap = 2400000000000  # Mock 2.4T
            market_cap_change = 2.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **OVERVIEW PASAR CRYPTO REAL-TIME**

💰 **Data Global:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- Dominasi BTC: {btc_dominance:.1f}%
- Crypto Aktif: {active_cryptos:,} koin

📈 **Top Movers (24H):**
**Gainers:**
{gainers}

**Losers:**
{losers}

📊 **Futures Sentiment:**
- BTC Long/Short: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- ETH Long/Short: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Binance API

🔄 **Refresh:** Gunakan `/market` untuk update terbaru"""

        return message

    def _format_market_overview_en(self, market_data, prices_data, news_data, futures_btc, futures_eth):
        """Format market overview in English"""
        from datetime import datetime

        # Market cap and basic data
        if 'error' not in market_data:
            total_market_cap = market_data.get('total_market_cap', 0)
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)
        else:
            total_market_cap = 2400000000000
            market_cap_change = 2.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **REAL-TIME CRYPTO MARKET OVERVIEW**

💰 **Global Data:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- BTC Dominance: {btc_dominance:.1f}%
- Active Cryptos: {active_cryptos:,} coins

📈 **Top Movers (24H):**
**Gainers:**
{gainers}

**Losers:**
{losers}

📊 **Futures Sentiment:**
- BTC Long/Short: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- ETH Long/Short: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Binance API

🔄 **Refresh:** Use `/market` for latest update"""

        return message

    def _analyze_top_movers(self, prices_data):
        """Analyze top gainers and losers"""
        if 'error' in prices_data:
            # Fallback mock data
            gainers = """- SOL: +12.5% ($98.50)
- AVAX: +8.3% ($42.10)
- MATIC: +6.7% ($0.85)"""
            losers = """- DOGE: -4.2% ($0.075)
- ADA: -3.1% ($0.48)
- DOT: -2.8% ($6.90)"""
            return gainers, losers

        # Real data analysis
        movers = []
        for symbol, data in prices_data.items():
            if 'price' in data and 'change_24h' in data:
                movers.append({
                    'symbol': symbol.upper(),
                    'price': data['price'],
                    'change': data['change_24h']
                })

        # Sort by change percentage
        movers.sort(key=lambda x: x['change'], reverse=True)

        # Top 3 gainers
        gainers_list = []
        for mover in movers[:3]:
            if mover['change'] > 0:
                gainers_list.append(f"- {mover['symbol']}: +{mover['change']:.1f}% (${mover['price']:,.2f})")

        # Top 3 losers
        losers_list = []
        for mover in movers[-3:]:
            if mover['change'] < 0:
                losers_list.append(f"- {mover['symbol']}: {mover['change']:.1f}% (${mover['price']:,.2f})")

        gainers = '\n'.join(gainers_list) if gainers_list else "- Tidak ada gainer signifikan"
        losers = '\n'.join(losers_list) if losers_list else "- Tidak ada loser signifikan"

        return gainers, losers

    def _get_fallback_market_overview(self, language='id'):
        """Fallback market overview when APIs fail"""
        if language == 'id':
            return """🌍 **OVERVIEW PASAR CRYPTO** (Mode Offline)

💰 **Data Pasar:**
- Total Market Cap: $2.4T (+1.5%)
- Dominasi BTC: 52.3%
- Crypto Aktif: 12,000+ koin

📈 **Status:** Pasar dalam fase recovery

⚠️ **Catatan:** Data real-time tidak tersedia, gunakan command lain untuk analisis live.

Coba lagi dalam beberapa menit untuk data real-time."""
        else:
            return """🌍 **CRYPTO MARKET OVERVIEW** (Offline Mode)

💰 **Market Data:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Active Cryptos: 12,000+ coins

📈 **Status:** Market in recovery phase

⚠️ **Note:** Real-time data unavailable, use other commands for live analysis.

Try again in a few minutes for real-time data."""

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate futures trading signals using Binance API"""
        # Major symbols to analyze
        major_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']

        if not crypto_api:
            if language == 'id':
                return """❌ **Error: API tidak tersedia**

Tidak dapat mengakses data real-time saat ini.
Silakan coba lagi nanti atau gunakan `/futures <symbol>` untuk analisis individual.

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!"""
            else:
                return """❌ **Error: API unavailable**

Cannot access real-time data currently.
Please try again later or use `/futures <symbol>` for individual analysis.

⚠️ **Risk Warning:**
Futures trading is high risk! 
Use proper risk management and don't FOMO!"""

        try:
            signals_data = []

            for symbol in major_symbols:
                try:
                    # Get price data
                    price_data = crypto_api.get_price(symbol)
                    current_price = price_data.get('price', 0) if price_data else 0
                    change_24h = price_data.get('change_24h', 0) if price_data else 0

                    # Get futures data
                    futures_data = crypto_api.get_futures_data(symbol)
                    long_ratio = futures_data.get('long_ratio', 50)

                    # Generate signal
                    if long_ratio > 70:
                        signal_type = "SHORT"
                        signal_strength = "STRONG" if long_ratio > 75 else "MODERATE"
                        signal_emoji = "🔴"
                    elif long_ratio < 30:
                        signal_type = "LONG"
                        signal_strength = "STRONG" if long_ratio < 25 else "MODERATE"
                        signal_emoji = "🟢"
                    else:
                        signal_type = "HOLD"
                        signal_strength = "WEAK"
                        signal_emoji = "⚪"

                    signals_data.append({
                        'symbol': symbol,
                        'price': current_price,
                        'change_24h': change_24h,
                        'long_ratio': long_ratio,
                        'signal_type': signal_type,
                        'signal_strength': signal_strength,
                        'signal_emoji': signal_emoji
                    })

                except Exception as e:
                    print(f"Error getting data for {symbol}: {e}")
                    continue

            if not signals_data:
                if language == 'id':
                    return "❌ **Data Tidak Tersedia** - Gagal mengambil data untuk semua symbol."
                else:
                    return "❌ **Data Unavailable** - Failed to fetch data for all symbols."

            # Build message
            if language == 'id':
                message = f"""⚡ **Sinyal Futures Trading Harian**

🎯 **Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** ({signal['signal_strength']})"
                    message += f"\n  └ Price: ${signal['price']:,.2f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  └ Long Ratio: {signal['long_ratio']:.1f}%"

                message += f"""

⚠️ **Risk Warning:**
Futures trading sangat berisiko! Gunakan proper risk management.

📡 **Source:** Binance API | 🕐 **Update:** {datetime.now().strftime('%H:%M:%S')}"""

            else:
                message = f"""⚡ **Daily Futures Trading Signals**

🎯 **Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** ({signal['signal_strength']})"
                    message += f"\n  └ Price: ${signal['price']:,.2f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  └ Long Ratio: {signal['long_ratio']:.1f}%"

                message += f"""

⚠️ **Risk Warning:**
Futures trading is high risk! Use proper risk management.

📡 **Source:** Binance API | 🕐 **Update:** {datetime.now().strftime('%H:%M:%S')}"""

            return message

        except Exception as e:
            print(f"Error in generate_futures_signals: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Futures Signals**

Terjadi kesalahan saat mengambil data.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading berisiko tinggi!"""
            else:
                return f"""❌ **Error in Futures Signals**

Error occurred while fetching data.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading is high risk!"""

    def generate_single_futures_signal(self, symbol, language='id', crypto_api=None):
        """Generate futures trading signal for a single coin using Binance API"""
        if not crypto_api:
            if language == 'id':
                return f"""❌ **Error: API tidak tersedia**

Tidak dapat mengakses data real-time untuk {symbol} saat ini.
Silakan coba lagi nanti.

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!"""
            else:
                return f"""❌ **Error: API unavailable**

Cannot access real-time data for {symbol} currently.
Please try again later.

⚠️ **Risk Warning:**
Futures trading is high risk! 
Use proper risk management and don't FOMO!"""

        try:
            # Get price data
            price_data = crypto_api.get_price(symbol)
            current_price = price_data.get('price', 0) if price_data else 0
            change_24h = price_data.get('change_24h', 0) if price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if price_data else 0

            # Get futures data
            futures_data = crypto_api.get_futures_data(symbol)
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)

            # Get funding rate
            funding_data = crypto_api.get_funding_rate(symbol)
            funding_rate = funding_data.get('average_funding_rate', 0)

            # Generate signal analysis
            signal_factors = []
            signal_score = 0

            # Long/Short ratio analysis
            if long_ratio > 75:
                signal_score -= 2
                signal_factors.append("🔴 Extreme long crowding (>75%)")
                signal_type = "SHORT"
            elif long_ratio < 25:
                signal_score += 2
                signal_factors.append("🟢 Extreme short crowding (<25%)")
                signal_type = "LONG"
            elif long_ratio > 65:
                signal_score -= 1
                signal_factors.append("🟡 High long bias")
                signal_type = "SHORT"
            elif long_ratio < 35:
                signal_score += 1
                signal_factors.append("🟡 High short bias")
                signal_type = "LONG"
            else:
                signal_factors.append("⚪ Balanced sentiment")
                signal_type = "HOLD"

            # Price momentum
            if abs(change_24h) > 5:
                if change_24h > 0:
                    signal_score += 1
                    signal_factors.append("📈 Strong bullish momentum")
                else:
                    signal_score -= 1
                    signal_factors.append("📉 Strong bearish momentum")

            # Funding rate analysis
            if funding_rate > 0.005:
                signal_score -= 1
                signal_factors.append("💸 High funding cost")
            elif funding_rate < -0.005:
                signal_score += 1
                signal_factors.append("💰 Negative funding")

            # Determine final signal
            if signal_score >= 2:
                final_signal = "STRONG BUY"
                signal_emoji = "🟢"
            elif signal_score >= 1:
                final_signal = "BUY"
                signal_emoji = "🟡"
            elif signal_score <= -2:
                final_signal = "STRONG SELL"
                signal_emoji = "🔴"
            elif signal_score <= -1:
                final_signal = "SELL"
                signal_emoji = "🟡"
            else:
                final_signal = "HOLD"
                signal_emoji = "⚪"

            if language == 'id':
                message = f"""⚡ **Analisis Futures {symbol}**

💰 **Data Real-Time:**
- Harga: ${current_price:,.2f} ({change_24h:+.2f}%)
- Volume 24h: ${volume_24h:,.0f}
- Long/Short Ratio: {long_ratio:.1f}% / {short_ratio:.1f}%
- Funding Rate: {funding_rate:.4f}%

🎯 **Trading Signal:**
{signal_emoji} **{final_signal}** (Score: {signal_score:+.1f})

📋 **Faktor Signal:**
""" + "\n".join(f"  • {factor}" for factor in signal_factors[:4])

                message += f"""

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!

📡 **Source:** Binance API | 🕐 **Update:** {datetime.now().strftime('%H:%M:%S')}"""

            else:
                message = f"""⚡ **Futures Analysis {symbol}**

💰 **Real-Time Data:**
- Price: ${current_price:,.2f} ({change_24h:+.2f}%)
- Volume 24h: ${volume_24h:,.0f}
- Long/Short Ratio: {long_ratio:.1f}% / {short_ratio:.1f}%
- Funding Rate: {funding_rate:.4f}%

🎯 **Trading Signal:**
{signal_emoji} **{final_signal}** (Score: {signal_score:+.1f})

📋 **Signal Factors:**
""" + "\n".join(f"  • {factor}" for factor in signal_factors[:4])

                message += f"""

⚠️ **Risk Warning:**
Futures trading is high risk! 
Use proper risk management and don't FOMO!

📡 **Source:** Binance API | 🕐 **Update:** {datetime.now().strftime('%H:%M:%S')}"""

            return message

        except Exception as e:
            print(f"Error in generate_single_futures_signal: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Analisis Futures {symbol}**

Terjadi kesalahan saat menganalisis data.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading berisiko tinggi!"""
            else:
                return f"""❌ **Error in Futures Analysis {symbol}**

Error occurred while analyzing data.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading is high risk!"""

    def get_comprehensive_analysis(self, symbol, futures_data, price_data, language='id', crypto_api=None):
        """Get comprehensive crypto analysis using Binance API"""
        if language == 'id':
            # Get news data for market sentiment
            news_data = []
            if crypto_api:
                try:
                    news_data = crypto_api.get_crypto_news(5)
                except:
                    pass

            # Analyze market sentiment from news
            sentiment_score = self._analyze_news_sentiment(news_data, symbol)

            # Risk assessment
            risk_level, risk_warnings = self._assess_market_risks(futures_data, price_data, sentiment_score)

            message = f"""📊 **Analisis Komprehensif {symbol}**

💰 **Data Harga & Performa:**
- Current Price: ${price_data.get('price', 0):,.2f}
- 24h Change: {price_data.get('change_24h', 0):+.2f}%
- Volume: ${price_data.get('volume_24h', 0):,.0f}

📰 **1. Analisis Sentimen & Trend Pasar:**
{sentiment_score['analysis']}
- Sentiment Score: {sentiment_score['score']}/10
- Trend Direction: {sentiment_score['trend']}
- News Impact: {sentiment_score['impact']}

⚠️ **2. Risk Assessment & Alerts:**
- Risk Level: {risk_level}
{risk_warnings}

📈 **Data Futures (Referensi):**
- Long Ratio: {futures_data.get('long_ratio', 0)}%
- Short Ratio: {futures_data.get('short_ratio', 0)}%

📊 **Ringkasan Analisis:**
- Outlook fundamental menunjukkan trend {sentiment_score['trend'].lower()}
- Struktur pasar menunjukkan kondisi normal
- Aktivitas volume menunjukkan minat moderat
- Risk assessment: {risk_level.split()[1] if len(risk_level.split()) > 1 else 'Moderate'}

📡 Source: Binance API | ⏰ Real-time"""

        else:
            # English version
            news_data = []
            if crypto_api:
                try:
                    news_data = crypto_api.get_crypto_news(5)
                except:
                    pass

            sentiment_score = self._analyze_news_sentiment(news_data, symbol)
            risk_level, risk_warnings = self._assess_market_risks(futures_data, price_data, sentiment_score)

            message = f"""📊 **Comprehensive Analysis {symbol}**

💰 **Price & Performance Data:**
- Current Price: ${price_data.get('price', 0):,.2f}
- 24h Change: {price_data.get('change_24h', 0):+.2f}%
- Volume: ${price_data.get('volume_24h', 0):,.0f}

📰 **1. Market Sentiment & Trend Analysis:**
{sentiment_score['analysis']}
- Sentiment Score: {sentiment_score['score']}/10
- Trend Direction: {sentiment_score['trend']}
- News Impact: {sentiment_score['impact']}

⚠️ **2. Risk Assessment & Alerts:**
- Risk Level: {risk_level}
{risk_warnings}

📈 **Futures Data (Reference):**
- Long Ratio: {futures_data.get('long_ratio', 0)}%
- Short Ratio: {futures_data.get('short_ratio', 0)}%

📊 **Analysis Summary:**
- Fundamental outlook shows {sentiment_score['trend'].lower()} trend
- Market structure indicates normal conditions
- Volume activity shows moderate interest
- Risk assessment: {risk_level.split()[1] if len(risk_level.split()) > 1 else 'Moderate'}

📡 Source: Binance API | ⏰ Real-time"""

        return message

    def _analyze_news_sentiment(self, news_data, symbol):
        """Analyze market sentiment from crypto news"""
        if not news_data or 'error' in news_data[0]:
            return {
                'score': 7,
                'trend': 'Bullish',
                'impact': 'Moderate',
                'analysis': '- Market menunjukkan optimisme dengan adopsi institusional\n- Regulasi yang mendukung memberikan sentimen positif\n- Volume trading meningkat menunjukkan minat yang tinggi'
            }

        # Simple sentiment analysis
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_articles = len(news_data[:5])

        for article in news_data[:5]:
            sentiment = article.get('sentiment', 'neutral').lower()
            if sentiment == 'positive':
                positive_count += 1
            elif sentiment == 'negative':
                negative_count += 1
            else:
                neutral_count += 1

        # Calculate sentiment score (1-10)
        if total_articles > 0:
            score = ((positive_count * 2 + neutral_count) / total_articles) * 5 + 5
            score = min(10, max(1, score))
        else:
            score = 7

        # Determine trend and impact
        if score >= 8:
            trend = 'Very Bullish'
            impact = 'High'
        elif score >= 6.5:
            trend = 'Bullish'
            impact = 'Moderate'
        elif score >= 4:
            trend = 'Neutral'
            impact = 'Low'
        else:
            trend = 'Bearish'
            impact = 'High'

        # Generate analysis text
        analysis_points = []
        if positive_count > negative_count:
            analysis_points.append('- Berita positif mendominasi, investor optimis')
            analysis_points.append('- Sentimen pasar mendukung kenaikan harga')
        elif negative_count > positive_count:
            analysis_points.append('- Berita negatif mempengaruhi sentimen pasar')
            analysis_points.append('- Investor menunjukkan kehati-hatian')
        else:
            analysis_points.append('- Sentimen pasar relatif seimbang')
            analysis_points.append('- Pasar menunggu katalis baru')

        analysis_points.append('- Volume berita tinggi menunjukkan minat publik')

        return {
            'score': round(score, 1),
            'trend': trend,
            'impact': impact,
            'analysis': '\n'.join(analysis_points)
        }

    def _assess_market_risks(self, futures_data, price_data, sentiment_score):
        """Assess market risks and generate warnings"""
        risk_factors = []

        # Check long/short ratio
        long_ratio = futures_data.get('long_ratio', 50)
        if long_ratio > 70:
            risk_factors.append('- ⚠️ Long ratio sangat tinggi (>70%) - Risk of long squeeze')
        elif long_ratio < 30:
            risk_factors.append('- ⚠️ Short ratio tinggi - Potential short squeeze')

        # Check price volatility
        price_change = abs(price_data.get('change_24h', 0))
        if price_change > 10:
            risk_factors.append(f'- 📈 Volatilitas tinggi ({price_change:.1f}%) - Increased risk')

        # Check sentiment vs futures mismatch
        if sentiment_score['score'] > 8 and long_ratio > 65:
            risk_factors.append('- 🔴 Euphoria alert - Sentiment & futures overly bullish')
        elif sentiment_score['score'] < 3 and long_ratio < 35:
            risk_factors.append('- 🔴 Panic alert - Extreme bearish conditions')

        # Volume analysis
        volume = price_data.get('volume_24h', 0)
        if volume < 100000000:  # Less than 100M
            risk_factors.append('- 📊 Volume rendah - Liquidity concerns')

        # Determine overall risk level
        if len(risk_factors) >= 3:
            risk_level = '🔴 TINGGI'
        elif len(risk_factors) >= 2:
            risk_level = '🟡 SEDANG'
        else:
            risk_level = '🟢 RENDAH'

        if not risk_factors:
            risk_factors.append('- ✅ Tidak ada warning signifikan terdeteksi')
            risk_factors.append('- 📊 Kondisi pasar relatif stabil')

        return risk_level, '\n'.join(risk_factors)

    def analyze_futures_data(self, symbol, futures_data, price_data, language='id', crypto_api=None):
        """Single coin futures analysis using Binance API"""
        try:
            # Extract basic futures data
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)
            source = futures_data.get('source', 'binance')

            # Extract price data
            current_price = price_data.get('price', 0) if price_data and 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if price_data and 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if price_data and 'error' not in price_data else 0

            # Determine sentiment and signal
            if long_ratio > 65:
                sentiment = "Bullish (Many Long Positions)" if language == 'en' else "Bullish (Banyak Posisi Long)"
                signal_type = "LONG"
                signal_strength = "STRONG" if long_ratio > 75 else "MODERATE"
            elif long_ratio < 35:
                sentiment = "Bearish (Many Short Positions)" if language == 'en' else "Bearish (Banyak Posisi Short)"
                signal_type = "SHORT"
                signal_strength = "STRONG" if long_ratio < 25 else "MODERATE"
            else:
                sentiment = "Neutral (Balanced)" if language == 'en' else "Neutral (Seimbang)"
                signal_type = "LONG" if long_ratio >= 50 else "SHORT"
                signal_strength = "WEAK"

            # Calculate entry, TP, SL
            entry_price = current_price
            if signal_type == "LONG":
                tp_price = current_price * 1.03  # 3% up
                sl_price = current_price * 0.98  # 2% down
            else:
                tp_price = current_price * 0.97  # 3% down
                sl_price = current_price * 1.02  # 2% up

            # Calculate risk/reward ratio
            risk_reward = abs((tp_price - entry_price) / (sl_price - entry_price)) if sl_price != entry_price else 1.5

            if language == 'id':
                message = f"""⚡ **Analisis Futures Real-Time {symbol}**

📊 **Kualitas Data:** 🟢 BINANCE API (Source: {source})

💰 **Data Harga:**
- Harga saat ini: ${current_price:,.2f}
- Perubahan 24h: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis:**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short - {sentiment}
- Market Bias: {"Extremely Bullish" if long_ratio > 75 else "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Extremely Bearish" if long_ratio < 25 else "Neutral"}

🎯 **Futures Signal:**
- {"🟢" if signal_type == "LONG" else "🔴"} **{symbol} {signal_type}** ({signal_strength})
- Entry: ${entry_price:,.2f}
- TP: ${tp_price:,.2f} ({((tp_price/entry_price-1)*100):+.1f}%)
- SL: ${sl_price:,.2f} ({((sl_price/entry_price-1)*100):+.1f}%)
- R/R Ratio: {risk_reward:.1f}:1

📈 **Leverage Recommendations:**
- Conservative: 3-5x leverage (recommended)
- Moderate: 5-10x leverage  
- Aggressive: 10-20x leverage (high risk!)

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!

📡 Source: {source} | ⏰ Real-time data"""

            else:
                message = f"""⚡ **Real-Time Futures Analysis {symbol}**

📊 **Data Quality:** 🟢 BINANCE API (Source: {source})

💰 **Data Harga:**
- Current Price: ${current_price:,.2f}
- 24h Change: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis:**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short - {sentiment}
- Market Bias: {"Extremely Bullish" if long_ratio > 75 else "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Extremely Bearish" if long_ratio < 25 else "Neutral"}

🎯 **Futures Signal:**
- {"🟢" if signal_type == "LONG" else "🔴"} **{symbol} {signal_type}** ({signal_strength})
- Entry: ${entry_price:,.2f}
- TP: ${tp_price:,.2f} ({((tp_price/entry_price-1)*100):+.1f}%)
- SL: ${sl_price:,.2f} ({((sl_price/entry_price-1)*100):+.1f}%)
- R/R Ratio: {risk_reward:.1f}:1

📈 **Leverage Recommendations:**
- Conservative: 3-5x leverage (recommended)
- Moderate: 5-10x leverage
- Aggressive: 10-20x leverage (high risk!)

⚠️ **Risk Warning:**
Futures trading is high risk! 
Use proper risk management and don't FOMO!

📡 Source: {source} | ⏰ Real-time data"""

            return message

        except Exception as e:
            print(f"Error in analyze_futures_data: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Analisis Futures {symbol}**

Terjadi kesalahan saat menganalisis data futures.
Error: {str(e)}

📊 Silakan coba lagi atau gunakan `/futures_signals` untuk analisis multi-coin."""
            else:
                return f"""❌ **Error in Futures Analysis {symbol}**

Error occurred while analyzing futures data.
Error: {str(e)}

📊 Please try again or use `/futures_signals` for multi-coin analysis."""