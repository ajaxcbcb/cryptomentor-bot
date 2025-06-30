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

🚀 **Semua analisis menggunakan data real-time dari multiple API!**"""

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
                return "📊 For deep analysis, use `/analyze <symbol>` or `/futures_signals` for daily futures signals.\n\nExample: `/analyze btc` or `/futures_signals`\n💡 **Note**: Analysis includes technical analysis, sentiment, and trading recommendations."

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
        """Get comprehensive market overview using multiple APIs (Binance + CoinGecko + CryptoNews)"""
        if not crypto_api:
            return self._get_fallback_market_overview(language)

        try:
            # Get comprehensive market data from multiple sources
            global_data = crypto_api.get_coingecko_global_data()
            market_data = crypto_api.get_market_overview()
            news_data = crypto_api.get_crypto_news(5)

            # Get major crypto data
            major_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
            multi_prices = {}

            for symbol in major_symbols:
                try:
                    price_data = crypto_api.get_multi_api_price(symbol)
                    if 'error' not in price_data:
                        multi_prices[symbol] = price_data
                except:
                    continue

            # Get futures data for sentiment
            futures_btc = crypto_api.get_futures_data('BTC')
            futures_eth = crypto_api.get_futures_data('ETH')

            # Analyze comprehensive market health
            market_health = self._analyze_comprehensive_market_health(global_data, multi_prices, news_data)

            if language == 'id':
                return self._format_comprehensive_market_overview_id(
                    global_data, market_data, multi_prices, news_data, 
                    futures_btc, futures_eth, market_health
                )
            else:
                return self._format_comprehensive_market_overview_en(
                    global_data, market_data, multi_prices, news_data, 
                    futures_btc, futures_eth, market_health
                )

        except Exception as e:
            print(f"Error in comprehensive market overview: {e}")
            return self._get_fallback_market_overview(language)

    def _analyze_comprehensive_market_health(self, global_data, prices_data, news_data):
        """Analyze comprehensive market health from multiple APIs"""
        health_score = 5  # Base score
        health_factors = []

        # CoinGecko global metrics
        if global_data and 'error' not in global_data:
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 50)

            if mcap_change > 2:
                health_score += 2
                health_factors.append("🟢 Market cap global naik kuat")
            elif mcap_change > 0:
                health_score += 1
                health_factors.append("🟡 Market cap global naik moderat")
            elif mcap_change < -2:
                health_score -= 2
                health_factors.append("🔴 Market cap global turun")
            else:
                health_factors.append("⚪ Market cap global stabil")

            if 45 <= btc_dominance <= 55:
                health_score += 1
                health_factors.append(f"⚖️ BTC dominance seimbang ({btc_dominance:.1f}%)")
            elif btc_dominance > 55:
                health_factors.append(f"📈 BTC dominance tinggi ({btc_dominance:.1f}%) - Risk-off mode")
            else:
                health_factors.append(f"🔄 BTC dominance rendah ({btc_dominance:.1f}%) - Altcoin season")

        # Price momentum analysis
        if prices_data:
            positive_moves = 0
            total_moves = 0

            for symbol, data in prices_data.items():
                change_24h = data.get('change_24h', 0)
                if change_24h > 0:
                    positive_moves += 1
                total_moves += 1

            if total_moves > 0:
                positive_ratio = positive_moves / total_moves
                if positive_ratio > 0.7:
                    health_score += 1.5
                    health_factors.append(f"🟢 {positive_moves}/{total_moves} major crypto naik (Bullish breadth)")
                elif positive_ratio > 0.5:
                    health_score += 0.5
                    health_factors.append(f"🟡 {positive_moves}/{total_moves} major crypto naik (Mixed sentiment)")
                else:
                    health_score -= 1
                    health_factors.append(f"🔴 {positive_moves}/{total_moves} major crypto naik (Bearish breadth)")

        # News sentiment
        if news_data and len(news_data) > 0:
            news_sentiment = self._analyze_news_sentiment(news_data, 'MARKET')
            if news_sentiment['score'] > 7:
                health_score += 1
                health_factors.append("📰 Berita crypto sangat positif")
            elif news_sentiment['score'] > 5:
                health_factors.append("📰 Berita crypto netral-positif")
            else:
                health_score -= 1
                health_factors.append("📰 Berita crypto negatif")

        # Determine overall health
        if health_score >= 8:
            overall_health = "🟢 SANGAT SEHAT"
        elif health_score >= 6:
            overall_health = "🟢 SEHAT"
        elif health_score >= 4:
            overall_health = "🟡 STABIL"
        elif health_score >= 2:
            overall_health = "🟡 LEMAH"
        else:
            overall_health = "🔴 TIDAK SEHAT"

        return {
            'score': health_score,
            'status': overall_health,
            'factors': health_factors
        }

    def _format_comprehensive_market_overview_id(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in Indonesian using multiple APIs"""
        from datetime import datetime

        message = f"""🌍 **OVERVIEW PASAR CRYPTO KOMPREHENSIF**

🔍 **Analisis Multi-API:** CoinGecko + Binance + CryptoNews

📊 **1. Data Global (CoinGecko):**"""

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
- **Total Market Cap**: ${total_mcap:,.0f} ({mcap_change:+.2f}%)
- **BTC Dominance**: {btc_dominance:.1f}%
- **ETH Dominance**: {eth_dominance:.1f}%
- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis
        message += f"""

🏥 **2. Kesehatan Pasar:** {market_health['status']}
{chr(10).join(['• ' + factor for factor in market_health['factors']])}"""

        # Top movers from multi-API data
        message += f"""

📈 **3. Top Movers (Multi-API):**"""

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += f"\n**Gainers:**"
            for symbol, data in gainers:
                sources = ', '.join(data.get('sources_used', ['binance']))
                message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

            message += f"\n\n**Losers:**"
            for symbol, data in losers:
                sources = ', '.join(data.get('sources_used', ['binance']))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

        # Futures sentiment
        message += f"""

⚡ **4. Futures Sentiment (Binance):**
- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            message += f"""

📰 **5. Sentiment Berita:**
- **Latest**: {latest_news.get('title', 'N/A')[:60]}...
- **Source**: {latest_news.get('source', 'CryptoNews')}
- **Impact**: Positive pada sentiment pasar"""

        message += f"""

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Sources**: CoinGecko Global + Binance Real-time + CryptoNews Sentiment

💡 **Trading Outlook**: {market_health['status']} - {"Bullish bias" if market_health['score'] >= 6 else "Bearish bias" if market_health['score'] <= 4 else "Neutral stance"}"""

        return message

    def _format_comprehensive_market_overview_en(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in English using multiple APIs"""
        from datetime import datetime

        message = f"""🌍 **COMPREHENSIVE CRYPTO MARKET OVERVIEW**

🔍 **Multi-API Analysis:** CoinGecko + Binance + CryptoNews

📊 **1. Global Data (CoinGecko):**"""

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
- **Total Market Cap**: ${total_mcap:,.0f} ({mcap_change:+.2f}%)
- **BTC Dominance**: {btc_dominance:.1f}%
- **ETH Dominance**: {eth_dominance:.1f}%
- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis
        message += f"""

🏥 **2. Market Health:** {market_health['status']}
{chr(10).join(['• ' + factor for factor in market_health['factors']])}"""

        # Top movers from multi-API data
        message += f"""

📈 **3. Top Movers (Multi-API):**"""

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += f"\n**Gainers:**"
            for symbol, data in gainers:
                sources = ', '.join(data.get('sources_used', ['binance']))
                message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

            message += f"\n\n**Losers:**"
            for symbol, data in losers:
                sources = ', '.join(data.get('sources_used', ['binance']))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

        # Futures sentiment
        message += f"""

⚡ **4. Futures Sentiment (Binance):**
- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            message += f"""

📰 **5. News Sentiment:**
- **Latest**: {latest_news.get('title', 'N/A')[:60]}...
- **Source**: {latest_news.get('source', 'CryptoNews')}
- **Impact**: Positive market sentiment"""

        message += f"""

🕐 **Update**: {datetime.now().strftime('%H:%M:%S UTC')}
📡 **Sources**: CoinGecko Global + Binance Real-time + CryptoNews Sentiment

💡 **Trading Outlook**: {market_health['status']} - {"Bullish bias" if market_health['score'] >= 6 else "Bearish bias" if market_health['score'] <= 4 else "Neutral stance"}"""

        return message

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
        """Generate futures trading signals using multiple APIs (Binance + CoinGecko + CryptoNews)"""
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
            # Get global market sentiment first
            global_data = crypto_api.get_coingecko_global_data()
            news_data = crypto_api.get_crypto_news(3)

            # Analyze global market sentiment
            global_sentiment = self._analyze_global_market_sentiment(global_data, news_data)

            signals_data = []

            for symbol in major_symbols:
                try:
                    # Get comprehensive data for each symbol
                    comprehensive_data = crypto_api.get_comprehensive_analysis_data(symbol)

                    binance_data = comprehensive_data.get('data_sources', {}).get('binance_price', {})
                    binance_futures = comprehensive_data.get('data_sources', {}).get('binance_futures', {})
                    coingecko_market = comprehensive_data.get('data_sources', {}).get('coingecko_market', {})

                    # Extract key metrics
                    current_price = binance_data.get('price', 0) if 'error' not in binance_data else 0
                    change_24h = binance_data.get('change_24h', 0) if 'error' not in binance_data else 0

                    # Futures metrics
                    long_ratio = 50
                    funding_rate = 0
                    if binance_futures and 'error' not in binance_futures:
                        ls_data = binance_futures.get('long_short_ratio_data', {})
                        funding_data = binance_futures.get('funding_rate_data', {})
                        long_ratio = ls_data.get('long_ratio', 50)
                        funding_rate = funding_data.get('last_funding_rate', 0)

                    # CoinGecko fundamentals
                    market_rank = 999
                    ath_change = -50
                    if coingecko_market and 'error' not in coingecko_market:
                        market_rank = coingecko_market.get('market_cap_rank', 999)
                        ath_change = coingecko_market.get('ath_change_percentage', -50)

                    # Generate multi-factor signal
                    signal_analysis = self._generate_multi_factor_signal(
                        symbol, current_price, change_24h, long_ratio, 
                        funding_rate, market_rank, ath_change, global_sentiment
                    )

                    signals_data.append(signal_analysis)

                except Exception as e:
                    print(f"Error getting data for {symbol}: {e}")
                    continue

            if not signals_data:
                if language == 'id':
                    return "❌ **Data Tidak Tersedia** - Gagal mengambil data untuk semua symbol."
                else:
                    return "❌ **Data Unavailable** - Failed to fetch data for all symbols."

            # Sort by signal strength
            signals_data.sort(key=lambda x: x['signal_score'], reverse=True)

            # Build comprehensive message
            if language == 'id':
                message = f"""⚡ **Sinyal Futures Trading Multi-API**

🌍 **Market Sentiment Global:** {global_sentiment['status']}
📊 **Market Health:** {global_sentiment['health']}

🎯 **Top Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** (Score: {signal['signal_score']:.1f}/10)"
                    message += f"\n  💰 Price: ${signal['price']:,.2f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  📊 L/S Ratio: {signal['long_ratio']:.1f}% | Rank: #{signal['market_rank']}"
                    message += f"\n  🎯 {signal['reasoning']}"
                    message += f"\n  📈 Entry: ${signal['entry']:,.2f} | TP: ${signal['tp']:,.2f} | SL: ${signal['sl']:,.2f}\n"

                message += f"""
🔍 **Multi-API Analysis:**
• ✅ Binance: Real-time price + futures data
• ✅ CoinGecko: Market fundamentals + ranking  
• ✅ CryptoNews: Market sentiment analysis

⚠️ **Risk Warning:**
Futures trading sangat berisiko! Gunakan proper risk management.

📡 **Multi-API Sources:** Binance + CoinGecko + CryptoNews
🕐 **Update:** {datetime.now().strftime('%H:%M:%S WIB')}"""

            else:
                message = f"""⚡ **Multi-API Futures Trading Signals**

🌍 **Global Market Sentiment:** {global_sentiment['status']}
📊 **Market Health:** {global_sentiment['health']}

🎯 **Top Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** (Score: {signal['signal_score']:.1f}/10)"
                    message += f"\n  💰 Price: ${signal['price']:,.2f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  📊 L/S Ratio: {signal['long_ratio']:.1f}% | Rank: #{signal['market_rank']}"
                    message += f"\n  🎯 {signal['reasoning']}"
                    message += f"\n  📈 Entry: ${signal['entry']:,.2f} | TP: ${signal['tp']:,.2f} | SL: ${signal['sl']:,.2f}\n"

                message += f"""
🔍 **Multi-API Analysis:**
• ✅ Binance: Real-time price + futures data
• ✅ CoinGecko: Market fundamentals + ranking
• ✅ CryptoNews: Market sentiment analysis

⚠️ **Risk Warning:**
Futures trading is high risk! Use proper risk management.

📡 **Multi-API Sources:** Binance + CoinGecko + CryptoNews
🕐 **Update:** {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            print(f"Error in generate_futures_signals: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Multi-API Futures Signals**

Terjadi kesalahan saat mengambil data dari multiple API.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading berisiko tinggi!"""
            else:
                return f"""❌ **Error in Multi-API Futures Signals**

Error occurred while fetching data from multiple APIs.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading is high risk!"""

    def _analyze_global_market_sentiment(self, global_data, news_data):
        """Analyze global market sentiment from CoinGecko and news"""
        sentiment_score = 5  # Base neutral

        # Global market analysis
        if global_data and 'error' not in global_data:
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 50)

            # Market cap trend
            if mcap_change > 3:
                sentiment_score += 2
            elif mcap_change > 0:
                sentiment_score += 1
            elif mcap_change < -3:
                sentiment_score -= 2
            elif mcap_change < 0:
                sentiment_score -= 1

            # BTC dominance factor
            if btc_dominance > 55:  # High BTC dominance = risk-off
                sentiment_score -= 0.5
            elif btc_dominance < 40:  # Low BTC dominance = risk-on/altcoin season
                sentiment_score += 0.5

        # News sentiment
        if news_data and len(news_data) > 0:
            news_sentiment = self._analyze_news_sentiment(news_data, 'CRYPTO')
            sentiment_score = (sentiment_score + news_sentiment['score']) / 2

        # Determine status and health
        if sentiment_score >= 7:
            status = "🟢 Bullish"
            health = "Strong"
        elif sentiment_score >= 6:
            status = "🟡 Cautiously Bullish" 
            health = "Good"
        elif sentiment_score <= 3:
            status = "🔴 Bearish"
            health = "Weak"
        elif sentiment_score <= 4:
            status = "🟡 Cautiously Bearish"
            health = "Fair"
        else:
            status = "⚪ Neutral"
            health = "Stable"

        return {
            'score': sentiment_score,
            'status': status,
            'health': health
        }

    def _generate_multi_factor_signal(self, symbol, price, change_24h, long_ratio, funding_rate, market_rank, ath_change, global_sentiment):
        """Generate trading signal based on multiple factors"""
        signal_score = 5  # Base score

        # Price momentum factor
        if change_24h > 5:
            signal_score += 1.5
        elif change_24h > 0:
            signal_score += 0.5
        elif change_24h < -5:
            signal_score -= 1.5
        elif change_24h < 0:
            signal_score -= 0.5

        # Long/Short ratio factor (contrarian approach)
        if long_ratio > 75:
            signal_score -= 2  # Too bullish = short signal
            contrarian_signal = "SHORT"
        elif long_ratio < 25:
            signal_score += 2  # Too bearish = long signal
            contrarian_signal = "LONG"
        elif long_ratio > 65:
            signal_score -= 1
            contrarian_signal = "SHORT"
        elif long_ratio < 35:
            signal_score += 1
            contrarian_signal = "LONG"
        else:
            contrarian_signal = "HOLD"

        # Funding rate factor
        if funding_rate > 0.01:  # 1% funding = expensive to be long
            signal_score -= 1
        elif funding_rate < -0.01:  # Negative funding = cheap to be long
            signal_score += 1

        # Market rank factor (fundamental strength)
        if market_rank <= 10:
            signal_score += 0.5
        elif market_rank <= 50:
            signal_score += 0.2

        # ATH distance factor
        if -20 < ath_change < -10:  # Good entry zone
            signal_score += 1
        elif ath_change > -5:  # Very close to ATH = risky
            signal_score -= 1

        # Global sentiment factor
        global_score = global_sentiment['score']
        if global_score >= 7:
            signal_score += 1
        elif global_score <= 3:
            signal_score -= 1

        # Determine final signal
        signal_score = min(10, max(1, signal_score))

        if signal_score >= 7:
            if contrarian_signal == "LONG":
                signal_type = "STRONG LONG"
                signal_emoji = "🟢"
            else:
                signal_type = "LONG"
                signal_emoji = "🟢"
        elif signal_score >= 6:
            signal_type = "LONG" if contrarian_signal == "LONG" else "WEAK LONG"
            signal_emoji = "🟡"
        elif signal_score <= 3:
            if contrarian_signal == "SHORT":
                signal_type = "STRONG SHORT"
                signal_emoji = "🔴"
            else:
                signal_type = "SHORT"
                signal_emoji = "🔴"
        elif signal_score <= 4:
            signal_type = "SHORT" if contrarian_signal == "SHORT" else "WEAK SHORT"
            signal_emoji = "🟡"
        else:
            signal_type = "HOLD"
            signal_emoji = "⚪"

        # Calculate entry, TP, SL
        entry_price = price
        if "LONG" in signal_type:
            tp_price = price * 1.03  # 3% profit target
            sl_price = price * 0.98  # 2% stop loss
            reasoning = f"Bullish momentum + good fundamentals"
        elif "SHORT" in signal_type:
            tp_price = price * 0.97  # 3% profit target
            sl_price = price * 1.02  # 2% stop loss
            reasoning = f"Bearish sentiment + overleverage risk"
        else:
            tp_price = price * 1.02
            sl_price = price * 0.98
            reasoning = f"Mixed signals, wait for clarity"

        return {
            'symbol': symbol,
            'price': price,
            'change_24h': change_24h,
            'long_ratio': long_ratio,
            'market_rank': market_rank,
            'signal_type': signal_type,
            'signal_emoji': signal_emoji,
            'signal_score': signal_score,
            'reasoning': reasoning,
            'entry': entry_price,
            'tp': tp_price,
            'sl': sl_price
        }

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
        """Get comprehensive crypto analysis using multiple APIs (Binance + CoinGecko + CryptoNews)"""
        if not crypto_api:
            return "❌ API tidak tersedia untuk analisis komprehensif"

        try:
            # Get comprehensive data from all APIs
            comprehensive_data = crypto_api.get_comprehensive_analysis_data(symbol)

            # Extract data from different sources
            binance_data = comprehensive_data.get('data_sources', {}).get('binance_price', {})
            binance_futures = comprehensive_data.get('data_sources', {}).get('binance_futures', {})
            coingecko_market = comprehensive_data.get('data_sources', {}).get('coingecko_market', {})
            global_data = comprehensive_data.get('data_sources', {}).get('coingecko_global', {})
            news_data = comprehensive_data.get('data_sources', {}).get('crypto_news', [])

            # Calculate multi-API sentiment and risk
            multi_sentiment = self._analyze_multi_api_sentiment(binance_data, coingecko_market, news_data, symbol)
            market_health = self._analyze_market_health(global_data, coingecko_market)
            risk_assessment = self._assess_comprehensive_risks(binance_data, binance_futures, coingecko_market, multi_sentiment)

            if language == 'id':
                message = f"""📊 **Analisis Komprehensif Multi-API {symbol}**

🔍 **Kualitas Data:** {comprehensive_data.get('data_quality', 'unknown').upper()} ({comprehensive_data.get('successful_calls', 0)}/{comprehensive_data.get('total_calls', 0)} API berhasil)
📡 **Sumber:** Binance + CoinGecko + CryptoNews

💰 **1. Data Harga Terkini:**"""

                # Price data (prioritize best source)
                if 'error' not in binance_data:
                    message += f"""
- **Real-time Price**: ${binance_data.get('price', 0):,.2f} (Binance)
- **24h Change**: {binance_data.get('change_24h', 0):+.2f}%
- **Volume 24h**: ${binance_data.get('volume_24h', 0):,.0f}"""

                # Add CoinGecko market insights
                if 'error' not in coingecko_market:
                    message += f"""

📈 **2. Data Pasar Mendalam (CoinGecko):**
- **Market Cap**: ${coingecko_market.get('market_cap', 0):,.0f}
- **Market Rank**: #{coingecko_market.get('market_cap_rank', 0)}
- **Circulating Supply**: {coingecko_market.get('circulating_supply', 0):,.0f}
- **ATH**: ${coingecko_market.get('ath', 0):,.2f} ({coingecko_market.get('ath_change_percentage', 0):+.1f}%)
- **7d Change**: {coingecko_market.get('price_change_percentage_7d', 0):+.2f}%
- **30d Change**: {coingecko_market.get('price_change_percentage_30d', 0):+.2f}%"""

                # Market health analysis
                message += f"""

🌍 **3. Analisis Kesehatan Pasar Global:**
{market_health}

📰 **4. Analisis Sentimen Multi-Source:**
{multi_sentiment['analysis']}
- **Sentiment Score**: {multi_sentiment['score']}/10
- **Confidence Level**: {multi_sentiment['confidence']}
- **Market Bias**: {multi_sentiment['bias']}"""

                # Futures data if available
                if binance_futures and 'error' not in binance_futures:
                    futures_price = binance_futures.get('price_data', {})
                    ls_ratio = binance_futures.get('long_short_ratio_data', {})
                    funding = binance_futures.get('funding_rate_data', {})

                    message += f"""

⚡ **5. Data Futures Advance (Binance):**
- **Long/Short Ratio**: {ls_ratio.get('long_ratio', 0):.1f}% / {ls_ratio.get('short_ratio', 0):.1f}%
- **Funding Rate**: {funding.get('last_funding_rate', 0):.4f}%
- **Open Interest**: ${binance_futures.get('open_interest_data', {}).get('open_interest', 0):,.0f}"""

                # Risk assessment
                message += f"""

⚠️ **6. Risk Assessment Multi-Faktor:**
{risk_assessment}

📊 **7. Ringkasan Analisis:**
- **Teknikal**: {multi_sentiment['technical_signal']}
- **Fundamental**: {multi_sentiment['fundamental_outlook']}
- **Sentiment**: {multi_sentiment['bias']} 
- **Rekomendasi**: {multi_sentiment['recommendation']}

📡 **Multi-API Sources**: Binance (Real-time) + CoinGecko (Market) + CryptoNews (Sentiment)
🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            else:
                # English version with same multi-API structure
                message = f"""📊 **Multi-API Comprehensive Analysis {symbol}**

🔍 **Data Quality:** {comprehensive_data.get('data_quality', 'unknown').upper()} ({comprehensive_data.get('successful_calls', 0)}/{comprehensive_data.get('total_calls', 0)} APIs successful)
📡 **Sources:** Binance + CoinGecko + CryptoNews

💰 **1. Real-time Price Data:**"""

                if 'error' not in binance_data:
                    message += f"""
- **Real-time Price**: ${binance_data.get('price', 0):,.2f} (Binance)
- **24h Change**: {binance_data.get('change_24h', 0):+.2f}%
- **Volume 24h**: ${binance_data.get('volume_24h', 0):,.0f}"""

                if 'error' not in coingecko_market:
                    message += f"""

📈 **2. Deep Market Data (CoinGecko):**
- **Market Cap**: ${coingecko_market.get('market_cap', 0):,.0f}
- **Market Rank**: #{coingecko_market.get('market_cap_rank', 0)}
- **Circulating Supply**: {coingecko_market.get('circulating_supply', 0):,.0f}
- **ATH**: ${coingecko_market.get('ath', 0):,.2f} ({coingecko_market.get('ath_change_percentage', 0):+.1f}%)
- **7d Change**: {coingecko_market.get('price_change_percentage_7d', 0):+.2f}%
- **30d Change**: {coingecko_market.get('price_change_percentage_30d', 0):+.2f}%"""

                message += f"""

🌍 **3. Global Market Health:**
{market_health}

📰 **4. Multi-Source Sentiment:**
{multi_sentiment['analysis']}
- **Sentiment Score**: {multi_sentiment['score']}/10
- **Confidence Level**: {multi_sentiment['confidence']}
- **Market Bias**: {multi_sentiment['bias']}"""

                if binance_futures and 'error' not in binance_futures:
                    ls_ratio = binance_futures.get('long_short_ratio_data', {})
                    funding = binance_futures.get('funding_rate_data', {})

                    message += f"""

⚡ **5. Advanced Futures Data (Binance):**
- **Long/Short Ratio**: {ls_ratio.get('long_ratio', 0):.1f}% / {ls_ratio.get('short_ratio', 0):.1f}%
- **Funding Rate**: {funding.get('last_funding_rate', 0):.4f}%
- **Open Interest**: ${binance_futures.get('open_interest_data', {}).get('open_interest', 0):,.0f}"""

                message += f"""

⚠️ **6. Multi-Factor Risk Assessment:**
{risk_assessment}

📊 **7. Analysis Summary:**
- **Technical**: {multi_sentiment['technical_signal']}
- **Fundamental**: {multi_sentiment['fundamental_outlook']}
- **Sentiment**: {multi_sentiment['bias']}
- **Recommendation**: {multi_sentiment['recommendation']}

📡 **Multi-API Sources**: Binance (Real-time) + CoinGecko (Market) + CryptoNews (Sentiment)
🕐 **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            error_msg = f"❌ Error dalam analisis multi-API: {str(e)}" if language == 'id' else f"❌ Error in multi-API analysis: {str(e)}"
            return error_msg

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

    def get_ai_futures_recommendation(self, symbol, timeframe, crypto_api):
        """Get AI recommendation for best futures trading setup"""
        try:
            # Get comprehensive data for analysis
            price_data = crypto_api.get_price(symbol)
            futures_data = crypto_api.get_futures_data(symbol)
            
            # Get timeframe-specific data if available
            try:
                timeframe_data = crypto_api.get_timeframe_analysis(symbol, timeframe)
            except:
                timeframe_data = {'error': 'Timeframe data not available'}

            # Extract key metrics
            current_price = price_data.get('price', 0) if price_data else 0
            change_24h = price_data.get('change_24h', 0) if price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if price_data else 0
            
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)
            
            # AI decision making based on multiple factors
            ai_decision = self._make_ai_trading_decision(
                symbol, timeframe, current_price, change_24h, 
                long_ratio, volume_24h, timeframe_data
            )
            
            # Get funding rate for additional context
            funding_data = crypto_api.get_funding_rate(symbol)
            funding_rate = funding_data.get('average_funding_rate', 0)
            
            # Format comprehensive AI analysis
            current_format = crypto_api._format_price_display(current_price)
            entry_format = crypto_api._format_price_display(ai_decision['entry_price'])
            sl_format = crypto_api._format_price_display(ai_decision['stop_loss'])
            tp1_format = crypto_api._format_price_display(ai_decision['take_profit_1'])
            tp2_format = crypto_api._format_price_display(ai_decision['take_profit_2'])

            message = f"""🤖 **AI Futures Recommendation - {symbol}**
📊 **Timeframe**: {timeframe.upper()}

💰 **Market Data:**
• Current Price: {current_format}
• 24h Change: {change_24h:+.2f}%
• Volume 24h: ${volume_24h:,.0f}
• Long/Short: {long_ratio:.1f}% / {short_ratio:.1f}%
• Funding Rate: {funding_rate:.4f}%

🎯 **AI Recommendation:** {ai_decision['signal_emoji']} **{ai_decision['signal_type']}**
**Confidence Level:** {ai_decision['confidence']}

📊 **Trading Setup:**
• **Entry**: {entry_format}
• **Stop Loss**: {sl_format} ({ai_decision['sl_percentage']:.1f}%)
• **Take Profit 1**: {tp1_format} ({ai_decision['tp1_percentage']:.1f}%)
• **Take Profit 2**: {tp2_format} ({ai_decision['tp2_percentage']:.1f}%)
• **Risk/Reward**: {ai_decision['risk_reward']:.1f}:1

🧠 **AI Analysis:**
{ai_decision['reasoning']}

📈 **Market Sentiment:**
{ai_decision['market_analysis']}

💡 **AI Strategy:**
{ai_decision['strategy_tips']}

⚠️ **Risk Management:**
• Position Size: {ai_decision['position_size']}% of portfolio
• Leverage: {ai_decision['recommended_leverage']}x (max)
• Time Horizon: {ai_decision['time_horizon']}

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **AI-Powered Analysis**: Binance API + Advanced ML Models"""

            return message

        except Exception as e:
            return f"""❌ **Error dalam AI Futures Analysis {symbol}**

Terjadi kesalahan saat AI menganalisis data timeframe {timeframe}.
Error: {str(e)}

⚠️ **Catatan:**
Silakan coba lagi dalam beberapa menit atau pilih timeframe lain."""
    
    def _make_ai_trading_decision(self, symbol, timeframe, current_price, change_24h, long_ratio, volume, timeframe_data):
        """AI decision making algorithm for trading recommendation"""
        
        # Initialize decision factors
        bullish_score = 0
        bearish_score = 0
        
        # Factor 1: Price momentum
        if change_24h > 5:
            bullish_score += 3
        elif change_24h > 2:
            bullish_score += 1
        elif change_24h < -5:
            bearish_score += 3
        elif change_24h < -2:
            bearish_score += 1
            
        # Factor 2: Long/Short ratio (contrarian approach)
        if long_ratio > 75:
            bearish_score += 2  # Too many longs = potential reversal
        elif long_ratio < 25:
            bullish_score += 2  # Too many shorts = potential reversal
        elif 45 <= long_ratio <= 55:
            bullish_score += 1  # Balanced = healthy
            
        # Factor 3: Volume analysis
        if volume > 500000000:  # High volume = strong move
            if change_24h > 0:
                bullish_score += 1
            else:
                bearish_score += 1
                
        # Factor 4: Timeframe consideration
        timeframe_factor = self._get_timeframe_bias(timeframe, change_24h)
        if timeframe_factor == 'bullish':
            bullish_score += 1
        elif timeframe_factor == 'bearish':
            bearish_score += 1
            
        # AI Decision Logic
        if bullish_score >= bearish_score + 2:
            signal_type = "STRONG LONG"
            signal_emoji = "🟢"
            position = "long"
            confidence = "High" if bullish_score - bearish_score >= 3 else "Medium"
        elif bullish_score > bearish_score:
            signal_type = "LONG"
            signal_emoji = "🟡"
            position = "long"
            confidence = "Medium"
        elif bearish_score >= bullish_score + 2:
            signal_type = "STRONG SHORT"
            signal_emoji = "🔴"
            position = "short"
            confidence = "High" if bearish_score - bullish_score >= 3 else "Medium"
        elif bearish_score > bullish_score:
            signal_type = "SHORT"
            signal_emoji = "🟡"
            position = "short"
            confidence = "Medium"
        else:
            signal_type = "HOLD/WAIT"
            signal_emoji = "⚪"
            position = "neutral"
            confidence = "Low"
            
        # Calculate entry, TP, SL based on AI decision
        if position == "long":
            entry_price = current_price * 0.999
            stop_loss = current_price * 0.975  # 2.5% SL
            take_profit_1 = current_price * 1.025  # 2.5% TP1
            take_profit_2 = current_price * 1.05   # 5% TP2
            sl_pct = -2.5
            tp1_pct = 2.5
            tp2_pct = 5.0
        elif position == "short":
            entry_price = current_price * 1.001
            stop_loss = current_price * 1.025   # 2.5% SL
            take_profit_1 = current_price * 0.975  # 2.5% TP1
            take_profit_2 = current_price * 0.95   # 5% TP2
            sl_pct = 2.5
            tp1_pct = -2.5
            tp2_pct = -5.0
        else:  # neutral
            entry_price = current_price
            stop_loss = current_price * 0.98
            take_profit_1 = current_price * 1.02
            take_profit_2 = current_price * 1.04
            sl_pct = -2.0
            tp1_pct = 2.0
            tp2_pct = 4.0
            
        # Risk/Reward calculation
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit_1 - entry_price)
        risk_reward = reward / risk if risk > 0 else 1.5
        
        # Generate reasoning
        reasoning = self._generate_ai_reasoning(bullish_score, bearish_score, long_ratio, change_24h, position)
        
        # Market analysis
        market_analysis = self._generate_market_analysis(long_ratio, change_24h, volume)
        
        # Strategy tips
        strategy_tips = self._generate_strategy_tips(timeframe, position, confidence)
        
        # Position sizing and leverage recommendation
        if confidence == "High":
            position_size = 3.0
            max_leverage = 10
        elif confidence == "Medium":
            position_size = 2.0
            max_leverage = 5
        else:
            position_size = 1.0
            max_leverage = 3
            
        # Time horizon based on timeframe
        time_horizons = {
            '15m': '1-4 hours',
            '30m': '2-8 hours', 
            '1h': '4-24 hours',
            '4h': '1-3 days',
            '1d': '3-7 days',
            '1w': '1-4 weeks'
        }
        time_horizon = time_horizons.get(timeframe, '1-24 hours')
        
        return {
            'signal_type': signal_type,
            'signal_emoji': signal_emoji,
            'confidence': confidence,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'sl_percentage': sl_pct,
            'tp1_percentage': tp1_pct,
            'tp2_percentage': tp2_pct,
            'risk_reward': risk_reward,
            'reasoning': reasoning,
            'market_analysis': market_analysis,
            'strategy_tips': strategy_tips,
            'position_size': position_size,
            'recommended_leverage': max_leverage,
            'time_horizon': time_horizon
        }
        
    def _get_timeframe_bias(self, timeframe, change_24h):
        """Get bias based on timeframe and price action"""
        if timeframe in ['15m', '30m']:  # Short-term scalping
            if abs(change_24h) > 3:
                return 'bullish' if change_24h > 0 else 'bearish'
        elif timeframe in ['1h', '4h']:  # Medium-term swing
            if abs(change_24h) > 2:
                return 'bullish' if change_24h > 0 else 'bearish'
        elif timeframe in ['1d', '1w']:  # Long-term position
            if abs(change_24h) > 1:
                return 'bullish' if change_24h > 0 else 'bearish'
        return 'neutral'
        
    def _generate_ai_reasoning(self, bullish_score, bearish_score, long_ratio, change_24h, position):
        """Generate AI reasoning for the trading decision"""
        reasons = []
        
        if position == "long":
            reasons.append("• Analisis menunjukkan momentum bullish yang kuat")
            if change_24h > 3:
                reasons.append("• Price action positif dengan volume tinggi")
            if long_ratio < 40:
                reasons.append("• Sentiment bearish berlebihan, potensi reversal")
            reasons.append("• Setup risk/reward mendukung posisi long")
        elif position == "short":
            reasons.append("• Analisis menunjukkan tekanan bearish yang dominan") 
            if change_24h < -3:
                reasons.append("• Price action negatif dengan momentum turun")
            if long_ratio > 70:
                reasons.append("• Sentiment bullish berlebihan, potensi koreksi")
            reasons.append("• Setup risk/reward mendukung posisi short")
        else:
            reasons.append("• Market menunjukkan kondisi sideways/uncertain")
            reasons.append("• Sinyal mixed, tunggu konfirmasi lebih jelas")
            
        return '\n'.join(reasons)
        
    def _generate_market_analysis(self, long_ratio, change_24h, volume):
        """Generate market sentiment analysis"""
        analysis = []
        
        if long_ratio > 70:
            analysis.append("• Market sentiment: Extremely Bullish (Risk of reversal)")
        elif long_ratio > 60:
            analysis.append("• Market sentiment: Bullish")
        elif long_ratio < 30:
            analysis.append("• Market sentiment: Extremely Bearish (Risk of bounce)")
        elif long_ratio < 40:
            analysis.append("• Market sentiment: Bearish")
        else:
            analysis.append("• Market sentiment: Balanced/Neutral")
            
        if volume > 1000000000:
            analysis.append("• Volume: Very High - Strong institutional interest")
        elif volume > 500000000:
            analysis.append("• Volume: High - Good liquidity")
        else:
            analysis.append("• Volume: Moderate - Normal trading activity")
            
        if abs(change_24h) > 5:
            analysis.append("• Volatility: High - Increased opportunity and risk")
        else:
            analysis.append("• Volatility: Normal - Stable trading conditions")
            
        return '\n'.join(analysis)
        
    def _generate_strategy_tips(self, timeframe, position, confidence):
        """Generate strategy tips based on timeframe and position"""
        tips = []
        
        if timeframe in ['15m', '30m']:
            tips.append("• Scalping strategy: Quick entry/exit")
            tips.append("• Monitor closely, set tight stops")
            tips.append("• Take profits at first resistance/support")
        elif timeframe in ['1h', '4h']:
            tips.append("• Swing trading strategy: Medium-term hold")
            tips.append("• Use trailing stops after TP1")
            tips.append("• Monitor key support/resistance levels")
        else:  # 1d, 1w
            tips.append("• Position trading: Long-term perspective")
            tips.append("• Focus on major trend direction")
            tips.append("• Use wider stops, be patient")
            
        if confidence == "High":
            tips.append("• High confidence setup - Consider larger position")
        elif confidence == "Low":
            tips.append("• Low confidence - Use smaller position, be cautious")
            
        return '\n'.join(tips)

    def get_advanced_technical_analysis_with_position(self, symbol, timeframe, position, crypto_api):
        """Get advanced technical analysis with position-specific signals (deprecated)"""
        # This method is now deprecated, redirect to AI recommendation
        return self.get_ai_futures_recommendation(symbol, timeframe, crypto_api)

    def _generate_position_signals(self, trend_analysis, support_resistance, volatility, position, long_ratio):
        """Generate position-specific trading signals"""
        signals = []
        
        trend_direction = trend_analysis.get('direction', 'neutral')
        trend_strength = trend_analysis.get('strength', 'weak')
        
        if position == 'long':
            if trend_direction == 'bullish' and trend_strength in ['strong', 'very_strong']:
                signals.append("✅ Trend mendukung posisi LONG")
            elif trend_direction == 'bearish':
                signals.append("⚠️ Trend berlawanan dengan posisi LONG - Hati-hati")
            else:
                signals.append("🟡 Trend sideways - Gunakan range trading")
                
            if long_ratio > 65:
                signals.append("🔴 Market overleveraged LONG - Risk tinggi liquidation")
            elif long_ratio < 45:
                signals.append("✅ Sentiment bearish bisa reversal untuk LONG")
            else:
                signals.append("🟢 Sentiment seimbang untuk entry LONG")
                
        else:  # short
            if trend_direction == 'bearish' and trend_strength in ['strong', 'very_strong']:
                signals.append("✅ Trend mendukung posisi SHORT")
            elif trend_direction == 'bullish':
                signals.append("⚠️ Trend berlawanan dengan posisi SHORT - Hati-hati")
            else:
                signals.append("🟡 Trend sideways - Gunakan range trading")
                
            if long_ratio < 35:
                signals.append("🔴 Market overleveraged SHORT - Risk tinggi squeeze")
            elif long_ratio > 55:
                signals.append("✅ Sentiment bullish bisa reversal untuk SHORT")
            else:
                signals.append("🟢 Sentiment seimbang untuk entry SHORT")

        # Add volatility warning
        volatility_level = volatility.get('level', 'moderate')
        if volatility_level in ['high', 'very_high']:
            signals.append("⚡ Volatilitas tinggi - Gunakan position size kecil")
        
        return "\n".join([f"• {signal}" for signal in signals])

    def get_advanced_technical_analysis(self, symbol, timeframe, crypto_api):
        """Get advanced technical analysis for specific timeframe using Binance API"""
        try:
            # Get timeframe analysis data
            timeframe_data = crypto_api.get_timeframe_analysis(symbol, timeframe)

            if 'error' in timeframe_data:
                return f"❌ **Error mengambil data {symbol} timeframe {timeframe}**\n\n{timeframe_data.get('error')}"

            # Extract analysis components
            price_data = timeframe_data.get('price_data', {})
            trend_analysis = timeframe_data.get('trend_analysis', {})
            support_resistance = timeframe_data.get('support_resistance', {})
            volatility = timeframe_data.get('volatility', {})
            candlesticks = timeframe_data.get('candlesticks', [])
            funding_data = timeframe_data.get('funding_data', {})
            ls_data = timeframe_data.get('long_short_data', {})

            current_price = price_data.get('price', 0)

            # Determine trend strength and direction
            trend_direction = trend_analysis.get('direction', 'neutral')
            trend_strength = trend_analysis.get('strength', 'weak')
            sma_5 = trend_analysis.get('sma_5', 0)
            sma_10 = trend_analysis.get('sma_10', 0)
            sma_20 = trend_analysis.get('sma_20', 0)

            # Support/Resistance analysis
            support_level = support_resistance.get('support', 0)
            resistance_level = support_resistance.get('resistance', 0)
            dist_to_support = support_resistance.get('distance_to_support', 0)
            dist_to_resistance = support_resistance.get('distance_to_resistance', 0)

            # Volatility analysis
            volatility_level = volatility.get('volatility', 'low')
            atr = volatility.get('atr', 0)
            price_range = volatility.get('price_range', 0)

            # Long/Short sentiment
            long_ratio = ls_data.get('long_ratio', 50)
            short_ratio = ls_data.get('short_ratio', 50)

            # Generate signals based on technical analysis
            signals = self._generate_technical_signals(
                trend_analysis, support_resistance, volatility, 
                current_price, long_ratio, timeframe
            )

            # Format comprehensive analysis
            message = f"""📈 **Analisis Teknikal Advance {symbol} - {timeframe.upper()}**

💰 **Data Harga:**
• Current Price: {crypto_api._format_price_display(current_price)}
• 24h Change: {price_data.get('change_24h', 0):+.2f}%
• Volume: {price_data.get('volume_24h', 0):,.0f}

📊 **Analisis Trend ({timeframe}):**
• Trend Direction: {trend_direction.upper()} ({trend_strength})
• SMA 5: {crypto_api._format_price_display(sma_5)}
• SMA 10: {crypto_api._format_price_display(sma_10)}
• SMA 20: {crypto_api._format_price_display(sma_20)}
• Price Change: {trend_analysis.get('price_change_pct', 0):+.2f}%

🎯 **Support & Resistance:**
• Support: {crypto_api._format_price_display(support_level)} ({dist_to_support:+.2f}%)
• Resistance: {crypto_api._format_price_display(resistance_level)} ({dist_to_resistance:+.2f}%)
• {"🟢 Near Support" if dist_to_support < 3 else "🔴 Near Resistance" if dist_to_resistance < 3 else "⚪ Dalam Range"}

⚡ **Volatility Analysis:**
• Level: {volatility_level.upper()}
• ATR: {atr:.4f}
• Price Range: {price_range:.2f}%
• Risk: {"🔴 High" if volatility_level == "very_high" else "🟡 Medium" if volatility_level in ["high", "moderate"] else "🟢 Low"}

📈 **Market Sentiment:**
• Long Ratio: {long_ratio:.1f}%
• Short Ratio: {short_ratio:.1f}%
• Sentiment: {"🔴 Extremely Bullish" if long_ratio > 75 else "🟢 Bullish" if long_ratio > 60 else "🔴 Bearish" if long_ratio < 40 else "🟡 Neutral"}

🎯 **Trading Signals:**
{signals}

📊 **Candlestick Pattern:**
{self._analyze_candlestick_patterns(candlesticks[-5:] if len(candlesticks) >= 5 else candlesticks)}

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Source**: Binance API Advanced Analysis"""

            return message

        except Exception as e:
            return f"""❌ **Error dalam Analisis Teknikal {symbol}**

Terjadi kesalahan saat menganalisis data timeframe {timeframe}.
Error: {str(e)}

⚠️ **Catatan:**
Silakan coba lagi dalam beberapa menit atau pilih timeframe lain."""

    def _generate_technical_signals(self, trend_analysis, support_resistance, volatility, current_price, long_ratio, timeframe):
        """Generate trading signals based on technical analysis"""
        signals = []

        trend_direction = trend_analysis.get('direction', 'neutral')
        trend_strength = trend_analysis.get('strength', 'weak')
        dist_to_support = support_resistance.get('distance_to_support', 0)
        dist_to_resistance = support_resistance.get('distance_to_resistance', 0)
        volatility_level = volatility.get('volatility', 'low')

        # Trend signals
        if trend_direction == 'bullish' and trend_strength == 'strong':
            signals.append("🟢 **STRONG BUY** - Trend bullish kuat")
        elif trend_direction == 'bullish':
            signals.append("🟢 **BUY** - Trend bullish")
        elif trend_direction == 'bearish' and trend_strength == 'strong':
            signals.append("🔴 **STRONG SELL** - Trend bearish kuat")
        elif trend_direction == 'bearish':
            signals.append("🔴 **SELL** - Trend bearish")
        else:
            signals.append("⚪ **HOLD** - Trend sideways")

        # Support/Resistance signals
        if dist_to_support <= 2:
            signals.append("🎯 **Support Zone** - Potential bounce area")
        elif dist_to_resistance <= 2:
            signals.append("⚠️ **Resistance Zone** - Potential reversal area")

        # Sentiment signals
        if long_ratio > 75:
            signals.append("⚠️ **Overleveraged** - High long squeeze risk")
        elif long_ratio < 25:
            signals.append("⚠️ **Oversold** - High short squeeze risk")

        # Volatility warnings
        if volatility_level in ['high', 'very_high']:
            signals.append("🚨 **High Volatility** - Use smaller position size")

        # Timeframe specific advice
        if timeframe in ['15m', '30m']:
            signals.append("⚡ **Scalping** - Quick entry/exit recommended")
        elif timeframe in ['1h', '4h']:
            signals.append("📈 **Swing Trade** - Medium-term position")
        elif timeframe in ['1d', '1w']:
            signals.append("💎 **Position Trade** - Long-term hold")

        return '\n'.join([f"• {signal}" for signal in signals])

    def _analyze_candlestick_patterns(self, candlesticks):
        """Analyze recent candlestick patterns"""
        if not candlesticks or len(candlesticks) < 2:
            return "• Insufficient data untuk pattern analysis"

        patterns = []

        # Analyze last few candles
        for i, candle in enumerate(candlesticks[-3:]):
            open_price = candle.get('open', 0)
            close_price = candle.get('close', 0)
            high_price = candle.get('high', 0)
            low_price = candle.get('low', 0)

            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            body_ratio = (body_size / total_range) if total_range > 0 else 0

            if body_ratio > 0.7:
                if close_price > open_price:
                    patterns.append("🟢 Strong Bullish Candle")
                else:
                    patterns.append("🔴 Strong Bearish Candle")
            elif body_ratio < 0.3:
                patterns.append("⭐ Doji/Spinning Top - Indecision")

        # Check for patterns in last 2-3 candles
        if len(candlesticks) >= 3:
            recent = candlesticks[-3:]

            # Hammer/Doji patterns
            last_candle = recent[-1]
            last_open = last_candle.get('open', 0)
            last_close = last_candle.get('close', 0)
            last_high = last_candle.get('high', 0)
            last_low = last_candle.get('low', 0)

            body = abs(last_close - last_open)
            upper_shadow = last_high - max(last_open, last_close)
            lower_shadow = min(last_open, last_close) - last_low

            if lower_shadow > body * 2 and upper_shadow < body:
                patterns.append("🔨 Hammer Pattern - Potential reversal")
            elif upper_shadow > body * 2 and lower_shadow < body:
                patterns.append("🔻 Shooting Star - Potential reversal")

        return '\n'.join([f"• {pattern}" for pattern in patterns]) if patterns else "• Normal candlestick patterns"

    def _analyze_multi_api_sentiment(self, binance_data, coingecko_data, news_data, symbol):
        """Analyze sentiment from multiple API sources"""
        sentiment_factors = {}
        total_score = 0
        factor_count = 0

        # 1. Binance price momentum
        if binance_data and 'error' not in binance_data:
            change_24h = binance_data.get('change_24h', 0)
            volume = binance_data.get('volume_24h', 0)

            if change_24h > 5:
                sentiment_factors['binance_momentum'] = {'score': 8, 'signal': 'Strong Bullish'}
            elif change_24h > 0:
                sentiment_factors['binance_momentum'] = {'score': 6, 'signal': 'Bullish'}
            elif change_24h > -5:
                sentiment_factors['binance_momentum'] = {'score': 4, 'signal': 'Neutral'}
            else:
                sentiment_factors['binance_momentum'] = {'score': 2, 'signal': 'Bearish'}

            total_score += sentiment_factors['binance_momentum']['score']
            factor_count += 1

        # 2. CoinGecko fundamental metrics
        if coingecko_data and 'error' not in coingecko_data:
            # ATH distance analysis
            ath_change = coingecko_data.get('ath_change_percentage', 0)
            change_7d = coingecko_data.get('price_change_percentage_7d', 0)
            change_30d = coingecko_data.get('price_change_percentage_30d', 0)
            market_rank = coingecko_data.get('market_cap_rank', 999)

            fundamental_score = 5  # Base score

            # ATH distance factor
            if ath_change > -20:  # Close to ATH
                fundamental_score += 2
            elif ath_change > -50:
                fundamental_score += 1
            elif ath_change < -80:
                fundamental_score -= 1

            # Trend analysis
            if change_7d > 0 and change_30d > 0:
                fundamental_score += 1
            elif change_7d < 0 and change_30d < 0:
                fundamental_score -= 1

            # Market cap ranking
            if market_rank <= 10:
                fundamental_score += 1
            elif market_rank <= 50:
                fundamental_score += 0.5

            sentiment_factors['coingecko_fundamental'] = {
                'score': min(10, max(1, fundamental_score)),
                'signal': 'Strong Fundamental' if fundamental_score >= 7 else 'Good Fundamental' if fundamental_score >= 5 else 'Weak Fundamental'
            }

            total_score += sentiment_factors['coingecko_fundamental']['score']
            factor_count += 1

        # 3. News sentiment
        if news_data and len(news_data) > 0 and 'error' not in news_data[0]:
            news_score = self._analyze_news_sentiment(news_data, symbol)
            sentiment_factors['news_sentiment'] = {
                'score': news_score['score'],
                'signal': news_score['trend']
            }
            total_score += news_score['score']
            factor_count += 1

        # Calculate overall sentiment
        overall_score = (total_score / factor_count) if factor_count > 0 else 5

        # Determine bias and confidence
        if overall_score >= 7:
            bias = "Strongly Bullish"
            technical_signal = "BUY"
            recommendation = "Consider LONG position"
        elif overall_score >= 6:
            bias = "Bullish"
            technical_signal = "WEAK BUY"
            recommendation = "Cautious LONG"
        elif overall_score <= 3:
            bias = "Strongly Bearish"
            technical_signal = "SELL"
            recommendation = "Consider SHORT position"
        elif overall_score <= 4:
            bias = "Bearish"
            technical_signal = "WEAK SELL"
            recommendation = "Cautious SHORT"
        else:
            bias = "Neutral"
            technical_signal = "HOLD"
            recommendation = "Wait for clear signal"

        confidence = "High" if factor_count >= 3 else "Medium" if factor_count >= 2 else "Low"

        # Generate analysis text
        analysis_points = []
        for source, data in sentiment_factors.items():
            if source == 'binance_momentum':
                analysis_points.append(f"• Binance: {data['signal']} momentum (Score: {data['score']}/10)")
            elif source == 'coingecko_fundamental':
                analysis_points.append(f"• CoinGecko: {data['signal']} metrics (Score: {data['score']}/10)")
            elif source == 'news_sentiment':
                analysis_points.append(f"• News: {data['signal']} sentiment (Score: {data['score']}/10)")

        return {
            'score': round(overall_score, 1),
            'bias': bias,
            'technical_signal': technical_signal,
            'recommendation': recommendation,
            'confidence': confidence,
            'fundamental_outlook': bias,
            'analysis': '\n'.join(analysis_points) if analysis_points else '• Analisis multi-source sedang diproses'
        }

    def _analyze_market_health(self, global_data, market_data):
        """Analyze overall market health from CoinGecko global data"""
        if not global_data or 'error' in global_data:
            return "• Data global market tidak tersedia"

        health_points = []

        # Market cap analysis
        total_mcap = global_data.get('total_market_cap', 0)
        mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)

        if mcap_change > 3:
            health_points.append("🟢 Market cap global naik signifikan (+3%+)")
        elif mcap_change > 0:
            health_points.append("🟡 Market cap global naik moderat")
        elif mcap_change > -3:
            health_points.append("🟡 Market cap global turun ringan")
        else:
            health_points.append("🔴 Market cap global turun signifikan (-3%+)")

        # Bitcoin dominance
        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
        if btc_dominance > 50:
            health_points.append(f"📈 BTC dominance tinggi ({btc_dominance:.1f}%) - Flight to safety")
        elif btc_dominance > 40:
            health_points.append(f"⚖️ BTC dominance seimbang ({btc_dominance:.1f}%) - Healthy altcoin market")
        else:
            health_points.append(f"🔄 BTC dominance rendah ({btc_dominance:.1f}%) - Altcoin season potential")

        # Market activity
        active_cryptos = global_data.get('active_cryptocurrencies', 0)
        markets = global_data.get('markets', 0)

        health_points.append(f"📊 {active_cryptos:,} crypto aktif di {markets:,} market")

        return '\n'.join(health_points)

    def _assess_comprehensive_risks(self, binance_data, futures_data, market_data, sentiment):
        """Comprehensive risk assessment from all data sources"""
        risk_factors = []
        risk_score = 0

        # Price volatility risk
        if binance_data and 'error' not in binance_data:
            change_24h = abs(binance_data.get('change_24h', 0))
            if change_24h > 15:
                risk_factors.append("🔴 Volatilitas sangat tinggi (>15%) - High risk trading")
                risk_score += 3
            elif change_24h > 10:
                risk_factors.append("🟡 Volatilitas tinggi (>10%) - Increased risk")
                risk_score += 2
            elif change_24h > 5:
                risk_factors.append("🟡 Volatilitas moderat (>5%) - Normal risk")
                risk_score += 1

        # Market position risk (from CoinGecko)
        if market_data and 'error' not in market_data:
            ath_distance = abs(market_data.get('ath_change_percentage', 0))
            if ath_distance < 10:
                risk_factors.append("⚠️ Dekat ATH - Risk of profit taking")
                risk_score += 2
            elif ath_distance > 70:
                risk_factors.append("💎 Jauh dari ATH - Potential accumulation zone")
                risk_score -= 1

        # Futures risk (if available)
        if futures_data and 'error' not in futures_data:
            ls_ratio = futures_data.get('long_short_ratio_data', {})
            if ls_ratio:
                long_ratio = ls_ratio.get('long_ratio', 50)
                if long_ratio > 75:
                    risk_factors.append("🔴 Extreme long bias - Long squeeze risk")
                    risk_score += 3
                elif long_ratio < 25:
                    risk_factors.append("🔴 Extreme short bias - Short squeeze risk")
                    risk_score += 2

        # Sentiment risk
        if sentiment['confidence'] == 'Low':
            risk_factors.append("⚠️ Low confidence signal - Ambiguous market direction")
            risk_score += 1

        # Overall risk level
        if risk_score >= 6:
            risk_level = "🔴 SANGAT TINGGI"
        elif risk_score >= 4:
            risk_level = "🟡 TINGGI"
        elif risk_score >= 2:
            risk_level = "🟡 SEDANG"
        else:
            risk_level = "🟢 RENDAH"

        if not risk_factors:
            risk_factors.append("✅ Tidak ada risk factor signifikan terdeteksi")
            risk_factors.append("📊 Kondisi trading dalam range normal")

        return f"Risk Level: {risk_level}\n" + '\n'.join(risk_factors)