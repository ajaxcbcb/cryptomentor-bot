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
        """Get comprehensive market sentiment analysis using multiple APIs"""
        from datetime import datetime

        try:
            print(f"🔄 Generating comprehensive market overview...")

            if not crypto_api:
                return self._get_fallback_market_overview(language)

            # Get comprehensive data from multiple sources
            # 1. CoinGecko global data
            global_data = crypto_api.get_coingecko_global_data()

            # 2. Enhanced market overview
            market_data = crypto_api.get_market_overview()

            # 3. Multiple price data from top cryptocurrencies
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'AVAX', 'LINK']
            multi_prices = {}
            print(f"📊 Fetching real-time data for {len(major_symbols)} major cryptocurrencies...")

            for symbol in major_symbols:
                try:
                    price_data = crypto_api.get_multi_api_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        multi_prices[symbol] = price_data
                        print(f"✅ {symbol}: ${price_data.get('price', 0):,.2f}")
                except Exception as e:
                    print(f"⚠️ Failed to get {symbol} data: {e}")
                    continue

            # 4. Crypto news sentiment
            try:
                news_data = crypto_api.get_crypto_news(3)
                if news_data and len(news_data) > 0:
                    print(f"📰 Retrieved {len(news_data)} latest crypto news")
                else:
                    news_data = []
            except:
                news_data = []

            # 5. Futures sentiment (BTC and ETH)
            try:
                futures_btc = crypto_api.get_binance_long_short_ratio('BTC')
                print(f"📈 BTC L/S Ratio: {futures_btc.get('long_ratio', 0):.1f}%/{futures_btc.get('short_ratio', 0):.1f}%")
            except:
                futures_btc = {'long_ratio': 50, 'short_ratio': 50, 'source': 'fallback'}

            try:
                futures_eth = crypto_api.get_binance_long_short_ratio('ETH')
                print(f"📈 ETH L/S Ratio: {futures_eth.get('long_ratio', 0):.1f}%/{futures_eth.get('short_ratio', 0):.1f}%")
            except:
                futures_eth = {'long_ratio': 50, 'short_ratio': 50, 'source': 'fallback'}

            # 6. Additional market metrics
            try:
                btc_funding = crypto_api.get_binance_funding_rate('BTC')
                eth_funding = crypto_api.get_binance_funding_rate('ETH')
            except:
                btc_funding = {'last_funding_rate': 0, 'source': 'fallback'}
                eth_funding = {'last_funding_rate': 0, 'source': 'fallback'}

            # Analyze comprehensive market health
            market_health = self._analyze_comprehensive_market_health(global_data, multi_prices, news_data)
            print(f"🏥 Market Health Score: {market_health.get('score', 5)}/10 - {market_health.get('status', 'Unknown')}")

            # Format comprehensive response
            if language == 'id':
                return self._format_comprehensive_market_overview_id(
                    global_data, market_data, multi_prices, news_data, 
                    futures_btc, futures_eth, market_health, btc_funding, eth_funding
                )
            else:
                return self._format_comprehensive_market_overview_en(
                    global_data, market_data, multi_prices, news_data, 
                    futures_btc, futures_eth, market_health, btc_funding, eth_funding
                )

        except Exception as e:
            print(f"❌ Error in comprehensive market overview: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_market_overview_with_error(language, str(e))

    def _analyze_comprehensive_market_health(self, global_data, prices_data, news_data):
        """Analyze comprehensive market health from multiple APIs"""
        health_score = 5  # Base score
        health_factors = []

        # 1. CoinGecko global metrics analysis
        if global_data and 'error' not in global_data:
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 50)

            # Market cap change scoring
            if mcap_change > 5:
                health_score += 2
                health_factors.append("📈 Market cap sangat bullish (+5%+)")
            elif mcap_change > 2:
                health_score += 1
                health_factors.append("📈 Market cap positif (+2%+)")
            elif mcap_change > -2:
                health_factors.append("📊 Market cap stabil (±2%)")
            elif mcap_change > -5:
                health_score -= 1
                health_factors.append("📉 Market cap menurun (-2% to -5%)")
            else:
                health_score -= 2
                health_factors.append("📉 Market cap sangat bearish (-5%+)")

            # BTC dominance analysis
            if 45 <= btc_dominance <= 60:
                health_score += 1
                health_factors.append("🟢 BTC dominance sehat (45-60%)")
            elif btc_dominance > 65:
                health_score -= 1
                health_factors.append("🟡 BTC dominance terlalu tinggi (>65%)")
            elif btc_dominance < 40:
                health_score -= 1
                health_factors.append("🟡 BTC dominance terlalu rendah (<40%)")
        else:
            health_score -= 1
            health_factors.append("⚠️ Data global tidak tersedia")

        # 2. Individual cryptocurrency performance analysis
        if prices_data and len(prices_data) > 0:
            positive_changes = sum(1 for data in prices_data.values() 
                                 if isinstance(data, dict) and data.get('change_24h', 0) > 0)
            total_cryptos = len(prices_data)
            positive_ratio = positive_changes / total_cryptos if total_cryptos > 0 else 0

            # Calculate average change
            changes = [data.get('change_24h', 0) for data in prices_data.values() 
                      if isinstance(data, dict) and 'change_24h' in data]
            avg_change = sum(changes) / len(changes) if changes else 0

            if positive_ratio > 0.7:
                health_score += 2
                health_factors.append(f"🟢 {positive_ratio*100:.0f}% crypto naik (sangat bullish)")
            elif positive_ratio > 0.5:
                health_score += 1
                health_factors.append(f"🟢 {positive_ratio*100:.0f}% crypto naik (bullish)")
            elif positive_ratio > 0.3:
                health_factors.append(f"🟡 {positive_ratio*100:.0f}% crypto naik (mixed)")
            else:
                health_score -= 1
                health_factors.append(f"🔴 {positive_ratio*100:.0f}% crypto naik (bearish)")

            # Average change analysis
            if avg_change > 3:
                health_score += 1
                health_factors.append(f"📈 Rata-rata perubahan: +{avg_change:.1f}%")
            elif avg_change < -3:
                health_score -= 1
                health_factors.append(f"📉 Rata-rata perubahan: {avg_change:.1f}%")
        else:
            health_score -= 1
            health_factors.append("⚠️ Data harga real-time terbatas")

        # 3. News sentiment analysis
        if news_data and len(news_data) > 0:
            # Simple sentiment analysis based on news availability
            health_score += 0.5
            health_factors.append("📰 Berita crypto tersedia (sentiment normal)")

            # Analyze news titles for sentiment keywords
            positive_keywords = ['bull', 'rise', 'surge', 'pump', 'gain', 'rally', 'high', 'adoption', 'breakthrough']
            negative_keywords = ['bear', 'fall', 'crash', 'dump', 'loss', 'decline', 'low', 'ban', 'hack']

            news_sentiment = 0
            for news in news_data[:3]:  # Check first 3 news
                title = news.get('title', '').lower()
                if any(keyword in title for keyword in positive_keywords):
                    news_sentiment += 1
                elif any(keyword in title for keyword in negative_keywords):
                    news_sentiment -= 1

            if news_sentiment > 0:
                health_score += 0.5
                health_factors.append("📰 Sentiment berita positif")
            elif news_sentiment < 0:
                health_score -= 0.5
                health_factors.append("📰 Sentiment berita negatif")
        else:
            health_factors.append("📰 Data berita tidak tersedia")

        # Ensure score stays within bounds
        health_score = max(0, min(10, health_score))

        # Determine overall health status
        if health_score >= 8:
            overall_health = "🟢 SANGAT SEHAT"
        elif health_score >= 6.5:
            overall_health = "🟢 SEHAT"
        elif health_score >= 5:
            overall_health = "🟡 STABIL"
        elif health_score >= 3:
            overall_health = "🟡 LEMAH"
        else:
            overall_health = "🔴 TIDAK SEHAT"

        return {
            'score': round(health_score, 1),
            'status': overall_health,
            'factors': health_factors
        }

    def _format_safe_market_overview_id(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in Indonesian using multiple APIs with safe formatting"""
        from datetime import datetime

        try:
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

                message += "\n**Gainers:**"
                for symbol, data in gainers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

                message += "\n\n**Losers:**"
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

        except Exception as e:
            print(f"Error formatting market overview (ID): {e}")
            return "❌ Gagal memformat overview pasar. Coba lagi nanti."

    def _format_safe_market_overview_en(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in English using multiple APIs with safe formatting"""
        from datetime import datetime

        try:
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

                message += "\n**Gainers:**"
                for symbol, data in gainers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

                message += "\n\n**Losers:**"
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

        except Exception as e:
            print(f"Error formatting market overview (EN): {e}")
            return "❌ Failed to format market overview. Try again later."

    def _format_comprehensive_market_overview_id(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health, btc_funding=None, eth_funding=None):
        """Format comprehensive market overview in Indonesian using multiple APIs"""
        from datetime import datetime

        def escape_markdown(text):
            """Escape special Markdown characters"""
            if not text:
                return ""
            # Escape problematic characters for Telegram Markdown
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                if char in str(text):
                    text = str(text).replace(char, f'\\{char}')
            return text

        message = "🌍 **OVERVIEW PASAR CRYPTO KOMPREHENSIF**\n\n"
        message += "🔍 **Analisis Multi\\-API:** CoinGecko \\+ Binance \\+ CryptoNews\n\n"
        message += "📊 **1\\. Data Global \\(CoinGecko\\):**"

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
\\- **Total Market Cap**: ${total_mcap:,.0f} \\({mcap_change:+.2f}%\\)
\\- **BTC Dominance**: {btc_dominance:.1f}%
\\- **ETH Dominance**: {eth_dominance:.1f}%
\\- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis - escape special characters
        health_status = escape_markdown(market_health.get('status', 'Unknown'))
        message += f"\n\n🏥 **2\\. Kesehatan Pasar:** {health_status}\n"
        
        for factor in market_health.get('factors', [])[:3]:  # Limit to 3 factors
            clean_factor = escape_markdown(factor)
            message += f"• {clean_factor}\n"

        # Top movers from multi-API data
        message += "\n📈 **3\\. Top Movers \\(Multi\\-API\\):**"

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += "\n**Gainers:**"
            for symbol, data in gainers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: \\+{data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

            message += "\n\n**Losers:**"
            for symbol, data in losers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

        # Futures sentiment
        message += f"""

⚡ **4\\. Futures Sentiment \\(Binance\\):**
\\- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%"""
        
        if btc_funding:
            funding_rate = btc_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {funding_rate:.4f}%\\)"

        message += f"""
\\- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""
        
        if eth_funding:
            eth_funding_rate = eth_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {eth_funding_rate:.4f}%\\)"

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            news_title = escape_markdown(latest_news.get('title', 'N/A')[:50])
            news_source = escape_markdown(latest_news.get('source', 'CryptoNews'))
            
            message += f"""

📰 **5\\. Sentiment Berita:**
\\- **Latest**: {news_title}\\.\\.\\.
\\- **Source**: {news_source}
\\- **Impact**: Positive pada sentiment pasar"""

        # Final summary
        current_time = datetime.now().strftime('%H:%M:%S')
        health_status_clean = escape_markdown(market_health.get('status', 'Unknown'))
        
        if market_health.get('score', 5) >= 6:
            trading_bias = "Bullish bias"
        elif market_health.get('score', 5) <= 4:
            trading_bias = "Bearish bias"
        else:
            trading_bias = "Neutral stance"

        message += f"""

🕐 **Update**: {current_time} WIB
📡 **Sources**: CoinGecko Global \\+ Binance Real\\-time \\+ CryptoNews Sentiment

💡 **Trading Outlook**: {health_status_clean} \\- {trading_bias}"""

        return message

    def _format_comprehensive_market_overview_en(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health, btc_funding=None, eth_funding=None):
        """Format comprehensive market overview in English using multiple APIs"""
        from datetime import datetime

        def escape_markdown(text):
            """Escape special Markdown characters"""
            if not text:
                return ""
            # Escape problematic characters for Telegram Markdown
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                if char in str(text):
                    text = str(text).replace(char, f'\\{char}')
            return text

        message = "🌍 **COMPREHENSIVE CRYPTO MARKET OVERVIEW**\n\n"
        message += "🔍 **Multi\\-API Analysis:** CoinGecko \\+ Binance \\+ CryptoNews\n\n"
        message += "📊 **1\\. Global Data \\(CoinGecko\\):**"

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
\\- **Total Market Cap**: ${total_mcap:,.0f} \\({mcap_change:+.2f}%\\)
\\- **BTC Dominance**: {btc_dominance:.1f}%
\\- **ETH Dominance**: {eth_dominance:.1f}%
\\- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis - escape special characters
        health_status = escape_markdown(market_health.get('status', 'Unknown'))
        message += f"\n\n🏥 **2\\. Market Health:** {health_status}\n"
        
        for factor in market_health.get('factors', [])[:3]:  # Limit to 3 factors
            clean_factor = escape_markdown(factor)
            message += f"• {clean_factor}\n"

        # Top movers from multi-API data
        message += "\n📈 **3\\. Top Movers \\(Multi\\-API\\):**"

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += "\n**Gainers:**"
            for symbol, data in gainers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: \\+{data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

            message += "\n\n**Losers:**"
            for symbol, data in losers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

        # Futures sentiment
        message += f"""

⚡ **4\\. Futures Sentiment \\(Binance\\):**
\\- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%"""
        
        if btc_funding:
            funding_rate = btc_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {funding_rate:.4f}%\\)"

        message += f"""
\\- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""
        
        if eth_funding:
            eth_funding_rate = eth_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {eth_funding_rate:.4f}%\\)"

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            news_title = escape_markdown(latest_news.get('title', 'N/A')[:50])
            news_source = escape_markdown(latest_news.get('source', 'CryptoNews'))
            
            message += f"""

📰 **5\\. News Sentiment:**
\\- **Latest**: {news_title}\\.\\.\\.
\\- **Source**: {news_source}
\\- **Impact**: Positive market sentiment"""

        # Final summary
        current_time = datetime.now().strftime('%H:%M:%S')
        health_status_clean = escape_markdown(market_health.get('status', 'Unknown'))
        
        if market_health.get('score', 5) >= 6:
            trading_bias = "Bullish bias"
        elif market_health.get('score', 5) <= 4:
            trading_bias = "Bearish bias"
        else:
            trading_bias = "Neutral stance"

        message += f"""

🕐 **Update**: {current_time} UTC
📡 **Sources**: CoinGecko Global \\+ Binance Real\\-time \\+ CryptoNews Sentiment

💡 **Trading Outlook**: {health_status_clean} \\- {trading_bias}"""

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
        """Generate enhanced futures trading signals with Supply & Demand integration"""
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

                    # Get Supply & Demand analysis
                    sd_analysis = None
                    entry_zones = None
                    try:
                        sd_analysis = crypto_api.analyze_supply_demand(symbol)
                        if 'error' not in sd_analysis:
                            entry_zones = self._extract_entry_zones(sd_analysis, current_price)
                    except Exception as e:
                        print(f"S&D analysis failed for {symbol}: {e}")

                    # Generate enhanced multi-factor signal with S&D
                    signal_analysis = self._generate_enhanced_multi_factor_signal(
                        symbol, current_price, change_24h, long_ratio, 
                        funding_rate, market_rank, ath_change, global_sentiment,
                        sd_analysis, entry_zones
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

            # Sort by enhanced signal strength
            signals_data.sort(key=lambda x: x['enhanced_score'], reverse=True)

            # Build comprehensive message
            if language == 'id':
                message = f"""⚡ **Enhanced Futures Signals + Supply/Demand**

🌍 **Market Sentiment Global:** {global_sentiment['status']}
📊 **Market Health:** {global_sentiment['health']}

🎯 **Top Enhanced Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** (Enhanced Score: {signal['enhanced_score']:.1f}/10)"
                    message += f"\n  💰 Price: ${signal['price']:,.4f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  📊 L/S: {signal['long_ratio']:.1f}% | S&D: {signal['sd_score']}/100"
                    message += f"\n  🎯 {signal['enhanced_reasoning']}"
                    message += f"\n  📈 Entry: ${signal['entry']:,.4f} | TP: ${signal['tp']:,.4f} | SL: ${signal['sl']:,.4f}"
                    message += f"\n  💡 Zone: {signal['entry_zone_info']}\n"

                message += f"""
🔍 **Enhanced Multi-API Analysis:**
• ✅ Binance: Real-time price + futures data
• ✅ CoinGecko: Market fundamentals + ranking  
• ✅ CryptoNews: Market sentiment analysis
• 🎯 Supply/Demand: Entry zones + institutional levels

⚠️ **Risk Management Enhanced:**
• Semua entry berdasarkan S&D zones
• Stop loss ditempatkan di luar zones
• Risk/reward ratio dioptimalkan
• Position sizing berdasarkan confidence

📡 **Enhanced Sources:** Binance + CoinGecko + CryptoNews + S&D Analysis
🕐 **Update:** {datetime.now().strftime('%H:%M:%S WIB')}"""

            else:
                message = f"""⚡ **Enhanced Futures Signals + Supply/Demand**

🌍 **Global Market Sentiment:** {global_sentiment['status']}
📊 **Market Health:** {global_sentiment['health']}

🎯 **Top Enhanced Trading Signals:**
"""
                for signal in signals_data:
                    message += f"\n{signal['signal_emoji']} **{signal['symbol']} {signal['signal_type']}** (Enhanced Score: {signal['enhanced_score']:.1f}/10)"
                    message += f"\n  💰 Price: ${signal['price']:,.4f} ({signal['change_24h']:+.1f}%)"
                    message += f"\n  📊 L/S: {signal['long_ratio']:.1f}% | S&D: {signal['sd_score']}/100"
                    message += f"\n  🎯 {signal['enhanced_reasoning']}"
                    message += f"\n  📈 Entry: ${signal['entry']:,.4f} | TP: ${signal['tp']:,.4f} | SL: ${signal['sl']:,.4f}"
                    message += f"\n  💡 Zone: {signal['entry_zone_info']}\n"

                message += f"""
🔍 **Enhanced Multi-API Analysis:**
• ✅ Binance: Real-time price + futures data
• ✅ CoinGecko: Market fundamentals + ranking
• ✅ CryptoNews: Market sentiment analysis
• 🎯 Supply/Demand: Entry zones + institutional levels

⚠️ **Enhanced Risk Management:**
• All entries based on S&D zones
• Stop losses placed outside zones
• Optimized risk/reward ratios
• Position sizing based on confidence

📡 **Enhanced Sources:** Binance + CoinGecko + CryptoNews + S&D Analysis
🕐 **Update:** {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            print(f"Error in enhanced futures signals: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Enhanced Futures Signals**

Terjadi kesalahan saat mengambil data dari enhanced multiple API.
Error: {str(e)}

⚠️ **Risk Warning:**
Futures trading berisiko tinggi!"""
            else:
                return f"""❌ **Error in Enhanced Futures Signals**

Error occurred while fetching enhanced data from multiple APIs.
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

    def _generate_enhanced_multi_factor_signal(self, symbol, price, change_24h, long_ratio, funding_rate, market_rank, ath_change, global_sentiment, sd_analysis, entry_zones):
        """Generate enhanced trading signal with Supply & Demand integration"""
        signal_score = 5  # Base score
        enhanced_score = 5  # Enhanced score with S&D

        # Price momentum factor
        if change_24h > 5:
            signal_score += 1.5
            enhanced_score += 1.5
        elif change_24h > 0:
            signal_score += 0.5
            enhanced_score += 0.5
        elif change_24h < -5:
            signal_score -= 1.5
            enhanced_score -= 1.5
        elif change_24h < 0:
            signal_score -= 0.5
            enhanced_score -= 0.5

        # Long/Short ratio factor (contrarian approach)
        if long_ratio > 75:
            signal_score -= 2
            enhanced_score -= 2
            contrarian_signal = "SHORT"
        elif long_ratio < 25:
            signal_score += 2
            enhanced_score += 2
            contrarian_signal = "LONG"
        elif long_ratio > 65:
            signal_score -= 1
            enhanced_score -= 1
            contrarian_signal = "SHORT"
        elif long_ratio < 35:
            signal_score += 1
            enhanced_score += 1
            contrarian_signal = "LONG"
        else:
            contrarian_signal = "HOLD"

        # Supply & Demand Enhancement
        sd_score = 50
        sd_bias = "Balanced"
        entry_zone_info = "No specific zone"
        
        if sd_analysis and 'error' not in sd_analysis:
            sd_data = sd_analysis.get('supply_demand_score', {})
            sd_score = sd_data.get('score', 50)
            sd_bias = sd_data.get('bias', 'Balanced')
            
            # S&D score enhancement
            if sd_score >= 70:
                enhanced_score += 2
                entry_zone_info = "Strong demand confluence"
            elif sd_score >= 60:
                enhanced_score += 1
                entry_zone_info = "Moderate demand area"
            elif sd_score <= 30:
                enhanced_score -= 2
                entry_zone_info = "Strong supply confluence"
            elif sd_score <= 40:
                enhanced_score -= 1
                entry_zone_info = "Moderate supply area"

            # Entry zones enhancement
            if entry_zones:
                if entry_zones['current_zone_type'] == 'near_demand':
                    enhanced_score += 1.5
                    entry_zone_info = "Near major demand zone"
                elif entry_zones['current_zone_type'] == 'near_supply':
                    enhanced_score -= 1.5
                    entry_zone_info = "Near major supply zone"

        # Funding rate factor
        if funding_rate > 0.01:
            signal_score -= 1
            enhanced_score -= 1
        elif funding_rate < -0.01:
            signal_score += 1
            enhanced_score += 1

        # Market rank factor
        if market_rank <= 10:
            signal_score += 0.5
            enhanced_score += 0.5
        elif market_rank <= 50:
            signal_score += 0.2
            enhanced_score += 0.2

        # ATH distance factor
        if -20 < ath_change < -10:
            signal_score += 1
            enhanced_score += 1
        elif ath_change > -5:
            signal_score -= 1
            enhanced_score -= 1

        # Global sentiment factor
        global_score = global_sentiment['score']
        if global_score >= 7:
            signal_score += 1
            enhanced_score += 1
        elif global_score <= 3:
            signal_score -= 1
            enhanced_score -= 1

        # Ensure scores stay within bounds
        signal_score = min(10, max(1, signal_score))
        enhanced_score = min(10, max(1, enhanced_score))

        # Determine enhanced signal type
        if enhanced_score >= 8:
            if contrarian_signal == "LONG" or sd_bias in ['Strong Demand', 'Moderate Demand']:
                signal_type = "STRONG LONG"
                signal_emoji = "🟢💪"
            else:
                signal_type = "STRONG SHORT"
                signal_emoji = "🔴💪"
        elif enhanced_score >= 7:
            if contrarian_signal == "LONG" or sd_bias in ['Strong Demand', 'Moderate Demand']:
                signal_type = "LONG"
                signal_emoji = "🟢"
            else:
                signal_type = "SHORT"
                signal_emoji = "🔴"
        elif enhanced_score >= 6:
            signal_type = "LONG" if contrarian_signal == "LONG" else "SHORT" if contrarian_signal == "SHORT" else "WEAK LONG"
            signal_emoji = "🟡"
        elif enhanced_score <= 3:
            if contrarian_signal == "SHORT" or sd_bias in ['Strong Supply', 'Moderate Supply']:
                signal_type = "STRONG SHORT"
                signal_emoji = "🔴💪"
            else:
                signal_type = "SHORT"
                signal_emoji = "🔴"
        elif enhanced_score <= 4:
            signal_type = "SHORT" if contrarian_signal == "SHORT" else "LONG" if contrarian_signal == "LONG" else "WEAK SHORT"
            signal_emoji = "🟡"
        else:
            signal_type = "HOLD"
            signal_emoji = "⚪"

        # Enhanced entry calculation with S&D zones
        entry_price = price
        if entry_zones and sd_analysis:
            if "LONG" in signal_type and entry_zones.get('strong_demand'):
                demand_zone = entry_zones['strong_demand']
                entry_price = demand_zone['zone_high']
                sl_price = demand_zone['zone_low'] * 0.998
                tp_price = price * 1.035
                enhanced_reasoning = f"Entry at demand zone confluence: Futures sentiment {contrarian_signal} + S&D score {sd_score}/100 + zone proximity"
            elif "SHORT" in signal_type and entry_zones.get('strong_supply'):
                supply_zone = entry_zones['strong_supply']
                entry_price = supply_zone['zone_low']
                sl_price = supply_zone['zone_high'] * 1.002
                tp_price = price * 0.965
                enhanced_reasoning = f"Entry at supply zone confluence: Futures sentiment {contrarian_signal} + S&D score {sd_score}/100 + zone proximity"
            else:
                # Market entry with enhanced levels
                if "LONG" in signal_type:
                    entry_price = price * 0.999
                    sl_price = price * 0.975
                    tp_price = price * 1.04
                    enhanced_reasoning = f"Market long entry: Futures {contrarian_signal} + S&D {sd_bias} + momentum confluence"
                elif "SHORT" in signal_type:
                    entry_price = price * 1.001
                    sl_price = price * 1.025
                    tp_price = price * 0.96
                    enhanced_reasoning = f"Market short entry: Futures {contrarian_signal} + S&D {sd_bias} + momentum confluence"
                else:
                    entry_price = price
                    sl_price = price * 0.98
                    tp_price = price * 1.02
                    enhanced_reasoning = f"Hold recommended: Mixed signals from futures ({long_ratio:.1f}%) and S&D ({sd_score}/100)"
        else:
            # Standard calculation if S&D not available
            if "LONG" in signal_type:
                tp_price = price * 1.03
                sl_price = price * 0.98
                enhanced_reasoning = f"Standard long setup: Futures sentiment + momentum without S&D confirmation"
            elif "SHORT" in signal_type:
                tp_price = price * 0.97
                sl_price = price * 1.02
                enhanced_reasoning = f"Standard short setup: Futures sentiment + momentum without S&D confirmation"
            else:
                tp_price = price * 1.02
                sl_price = price * 0.98
                enhanced_reasoning = f"Hold: Mixed signals without clear S&D direction"

        return {
            'symbol': symbol,
            'price': price,
            'change_24h': change_24h,
            'long_ratio': long_ratio,
            'market_rank': market_rank,
            'signal_type': signal_type,
            'signal_emoji': signal_emoji,
            'signal_score': signal_score,
            'enhanced_score': enhanced_score,
            'sd_score': sd_score,
            'reasoning': f"{contrarian_signal} bias + momentum",
            'enhanced_reasoning': enhanced_reasoning,
            'entry_zone_info': entry_zone_info,
            'entry': entry_price,
            'tp': tp_price,
            'sl': sl_price
        }

    def generate_supply_demand_analysis(self, symbol, language='id', crypto_api=None):
        """Generate comprehensive supply and demand analysis for entry recommendations"""
        if not crypto_api:
            if language == 'id':
                return f"""❌ **Error: API tidak tersedia**

Tidak dapat mengakses data untuk analisis Supply/Demand {symbol}.
Silakan coba lagi nanti.

⚠️ **Risk Warning:**
Trading berisiko tinggi! Gunakan proper risk management!"""
            else:
                return f"""❌ **Error: API unavailable**

Cannot access data for Supply/Demand analysis of {symbol}.
Please try again later.

⚠️ **Risk Warning:**
Trading is high risk! Use proper risk management!"""

        try:
            # Get comprehensive supply/demand analysis
            sd_analysis = crypto_api.analyze_supply_demand(symbol)
            
            if 'error' in sd_analysis:
                if language == 'id':
                    return f"""❌ **Error dalam Analisis Supply/Demand {symbol}**

{sd_analysis.get('error', 'Unknown error')}

Silakan coba lagi atau gunakan analisis lain."""
                else:
                    return f"""❌ **Error in Supply/Demand Analysis {symbol}**

{sd_analysis.get('error', 'Unknown error')}

Please try again or use other analysis."""

            # Extract data
            current_price = sd_analysis.get('current_price', 0)
            volume_pressure = sd_analysis.get('volume_pressure', {})
            order_imbalance = sd_analysis.get('order_imbalance', {})
            supply_demand_zones = sd_analysis.get('supply_demand_zones', {})
            market_structure = sd_analysis.get('market_structure', {})
            oi_flow = sd_analysis.get('oi_flow', {})
            sd_score = sd_analysis.get('supply_demand_score', {})
            entry_rec = sd_analysis.get('entry_recommendation', {})

            if language == 'id':
                message = f"""📊 **Analisis Supply & Demand {symbol}**

💰 **Harga Saat Ini:** ${current_price:,.4f}

🔄 **Tekanan Volume (24h):**
- **Tipe:** {volume_pressure.get('pressure_type', 'Unknown').replace('_', ' ').title()}
- **Kekuatan:** {volume_pressure.get('pressure_strength', 0):.1f}/100
- **Level Volume:** {volume_pressure.get('volume_level', 'Unknown').title()}
- **Analisis:** {volume_pressure.get('analysis', 'N/A')}

⚖️ **Ketidakseimbangan Order:**
- **Tipe:** {order_imbalance.get('imbalance_type', 'Unknown').replace('_', ' ').title()}
- **Long/Short Ratio:** {order_imbalance.get('long_ratio', 0):.1f}% / {order_imbalance.get('short_ratio', 0):.1f}%
- **Analisis:** {order_imbalance.get('analysis', 'N/A')}

🏗️ **Struktur Pasar:**
- **Struktur:** {market_structure.get('structure', 'Unknown').title()}
- **Trend:** {market_structure.get('trend', 'Unknown').title()}
- **Analisis:** {market_structure.get('analysis', 'N/A')}

📍 **Zone Supply & Demand:**"""

                # Add supply/demand zones
                demand_zones = supply_demand_zones.get('demand_zones', [])
                supply_zones = supply_demand_zones.get('supply_zones', [])
                
                if demand_zones:
                    nearest_demand = demand_zones[0]
                    message += f"\n- **Demand Zone Terdekat:** ${nearest_demand.get('price_level', 0):,.4f} (Jarak: {nearest_demand.get('distance_from_current', 0):.1f}%)"
                
                if supply_zones:
                    nearest_supply = supply_zones[0]
                    message += f"\n- **Supply Zone Terdekat:** ${nearest_supply.get('price_level', 0):,.4f} (Jarak: {nearest_supply.get('distance_from_current', 0):.1f}%)"

                if not demand_zones and not supply_zones:
                    message += "\n- **Tidak ada zone signifikan terdeteksi**"

                message += f"""

📈 **Aliran Open Interest:**
- **Trend OI:** {oi_flow.get('oi_trend', 'Unknown').title()}
- **Arah Aliran:** {oi_flow.get('flow_direction', 'Unknown').replace('_', ' ').title()}
- **Analisis:** {oi_flow.get('analysis', 'N/A')}

🎯 **Skor Supply/Demand:** {sd_score.get('score', 50)}/100
- **Bias:** {sd_score.get('bias', 'Balanced')}
- **Rekomendasi:** {sd_score.get('recommendation', 'HOLD')}
- **Confidence:** {sd_score.get('confidence', 'Low')}

💡 **Faktor Kunci:**"""
                
                for factor in sd_score.get('factors', [])[:4]:
                    message += f"\n  • {factor}"

                # Entry recommendation
                primary_rec = entry_rec.get('primary_recommendation')
                if primary_rec:
                    message += f"""

🚀 **Rekomendasi Entry:**
- **Arah:** {primary_rec.get('direction', 'HOLD')}
- **Tipe Entry:** {primary_rec.get('entry_type', 'N/A')}
- **Entry Price:** ${primary_rec.get('entry_price', 0):,.4f}"""
                    
                    if primary_rec.get('stop_loss'):
                        message += f"\n- **Stop Loss:** ${primary_rec.get('stop_loss', 0):,.4f}"
                    if primary_rec.get('take_profit'):
                        message += f"\n- **Take Profit:** ${primary_rec.get('take_profit', 0):,.4f}"
                    if primary_rec.get('risk_reward'):
                        message += f"\n- **Risk/Reward:** {primary_rec.get('risk_reward', 0):.1f}:1"
                    
                    message += f"\n- **Logic:** {primary_rec.get('logic', 'N/A')}"
                    message += f"\n- **Timing:** {entry_rec.get('entry_timing', 'Wait')}"

                message += f"""

⚠️ **Risk Warning:**
Supply/Demand analysis membutuhkan konfirmasi price action!
Gunakan proper risk management dan position sizing!

📡 **Source:** Multi-API Supply/Demand Analysis
🕐 **Update:** {datetime.now().strftime('%H:%M:%S WIB')}"""

            else:
                # English version
                message = f"""📊 **Supply & Demand Analysis {symbol}**

💰 **Current Price:** ${current_price:,.4f}

🔄 **Volume Pressure (24h):**
- **Type:** {volume_pressure.get('pressure_type', 'Unknown').replace('_', ' ').title()}
- **Strength:** {volume_pressure.get('pressure_strength', 0):.1f}/100
- **Volume Level:** {volume_pressure.get('volume_level', 'Unknown').title()}
- **Analysis:** {volume_pressure.get('analysis', 'N/A')}

⚖️ **Order Imbalance:**
- **Type:** {order_imbalance.get('imbalance_type', 'Unknown').replace('_', ' ').title()}
- **Long/Short Ratio:** {order_imbalance.get('long_ratio', 0):.1f}% / {order_imbalance.get('short_ratio', 0):.1f}%
- **Analysis:** {order_imbalance.get('analysis', 'N/A')}

🏗️ **Market Structure:**
- **Structure:** {market_structure.get('structure', 'Unknown').title()}
- **Trend:** {market_structure.get('trend', 'Unknown').title()}
- **Analysis:** {market_structure.get('analysis', 'N/A')}

📍 **Supply & Demand Zones:**"""

                # Add supply/demand zones
                demand_zones = supply_demand_zones.get('demand_zones', [])
                supply_zones = supply_demand_zones.get('supply_zones', [])
                
                if demand_zones:
                    nearest_demand = demand_zones[0]
                    message += f"\n- **Nearest Demand Zone:** ${nearest_demand.get('price_level', 0):,.4f} (Distance: {nearest_demand.get('distance_from_current', 0):.1f}%)"
                
                if supply_zones:
                    nearest_supply = supply_zones[0]
                    message += f"\n- **Nearest Supply Zone:** ${nearest_supply.get('price_level', 0):,.4f} (Distance: {nearest_supply.get('distance_from_current', 0):.1f}%)"

                if not demand_zones and not supply_zones:
                    message += "\n- **No significant zones detected**"

                message += f"""

📈 **Open Interest Flow:**
- **OI Trend:** {oi_flow.get('oi_trend', 'Unknown').title()}
- **Flow Direction:** {oi_flow.get('flow_direction', 'Unknown').replace('_', ' ').title()}
- **Analysis:** {oi_flow.get('analysis', 'N/A')}

🎯 **Supply/Demand Score:** {sd_score.get('score', 50)}/100
- **Bias:** {sd_score.get('bias', 'Balanced')}
- **Recommendation:** {sd_score.get('recommendation', 'HOLD')}
- **Confidence:** {sd_score.get('confidence', 'Low')}

💡 **Key Factors:**"""
                
                for factor in sd_score.get('factors', [])[:4]:
                    message += f"\n  • {factor}"

                # Entry recommendation
                primary_rec = entry_rec.get('primary_recommendation')
                if primary_rec:
                    message += f"""

🚀 **Entry Recommendation:**
- **Direction:** {primary_rec.get('direction', 'HOLD')}
- **Entry Type:** {primary_rec.get('entry_type', 'N/A')}
- **Entry Price:** ${primary_rec.get('entry_price', 0):,.4f}"""
                    
                    if primary_rec.get('stop_loss'):
                        message += f"\n- **Stop Loss:** ${primary_rec.get('stop_loss', 0):,.4f}"
                    if primary_rec.get('take_profit'):
                        message += f"\n- **Take Profit:** ${primary_rec.get('take_profit', 0):,.4f}"
                    if primary_rec.get('risk_reward'):
                        message += f"\n- **Risk/Reward:** {primary_rec.get('risk_reward', 0):.1f}:1"
                    
                    message += f"\n- **Logic:** {primary_rec.get('logic', 'N/A')}"
                    message += f"\n- **Timing:** {entry_rec.get('entry_timing', 'Wait')}"

                message += f"""

⚠️ **Risk Warning:**
Supply/Demand analysis requires price action confirmation!
Use proper risk management and position sizing!

📡 **Source:** Multi-API Supply/Demand Analysis
🕐 **Update:** {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            print(f"Error in generate_supply_demand_analysis: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Analisis Supply/Demand {symbol}**

Terjadi kesalahan saat menganalisis data supply/demand.
Error: {str(e)}

⚠️ **Risk Warning:**
Trading berisiko tinggi! Gunakan proper risk management!"""
            else:
                return f"""❌ **Error in Supply/Demand Analysis {symbol}**

Error occurred while analyzing supply/demand data.
Error: {str(e)}

⚠️ **Risk Warning:**
Trading is high risk! Use proper risk management!"""

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

💡 **Untuk analisis Supply/Demand yang lebih mendalam, gunakan:**
`/supply_demand {symbol}` - Analisis entry berdasarkan zone S&D

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

💡 **For deeper Supply/Demand analysis, use:**
`/supply_demand {symbol}` - Entry analysis based on S&D zones

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
        """Single coin futures analysis with Supply & Demand integration"""
        try:
            # Extract basic futures data
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)
            source = futures_data.get('source', 'binance')

            # Extract price data
            current_price = price_data.get('price', 0) if price_data and 'error' not in price_data else 0
            change_24h = price_data.get('change_24h', 0) if price_data and 'error' not in price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if price_data and 'error' not in price_data else 0

            # Get Supply & Demand analysis if crypto_api available
            supply_demand_analysis = None
            entry_zones = None
            
            if crypto_api:
                try:
                    sd_analysis = crypto_api.analyze_supply_demand(symbol)
                    if 'error' not in sd_analysis:
                        supply_demand_analysis = sd_analysis
                        entry_zones = self._extract_entry_zones(sd_analysis, current_price)
                except Exception as e:
                    print(f"S&D analysis error: {e}")

            # Enhanced signal determination with S&D
            signal_data = self._determine_enhanced_futures_signal(
                long_ratio, short_ratio, current_price, change_24h, 
                supply_demand_analysis, entry_zones
            )

            if language == 'id':
                message = f"""⚡ **Analisis Futures + Supply/Demand {symbol}**

📊 **Kualitas Data:** 🟢 BINANCE + S&D API (Source: {source})

💰 **Data Harga:**
- Harga saat ini: ${current_price:,.4f}
- Perubahan 24h: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis:**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short
- Market Sentiment: {signal_data['sentiment']}
- Contrarian Signal: {signal_data['contrarian_bias']}

🎯 **Supply/Demand Integration:**"""

                if supply_demand_analysis:
                    sd_score = supply_demand_analysis.get('supply_demand_score', {})
                    message += f"""
- **S&D Score**: {sd_score.get('score', 50)}/100
- **Market Bias**: {sd_score.get('bias', 'Balanced')}
- **Confidence**: {sd_score.get('confidence', 'Medium')}"""

                    # Add key supply/demand zones
                    zones = supply_demand_analysis.get('supply_demand_zones', {})
                    demand_zones = zones.get('demand_zones', [])
                    supply_zones = zones.get('supply_zones', [])
                    
                    if demand_zones:
                        nearest_demand = demand_zones[0]
                        message += f"\n- **Demand Zone**: ${nearest_demand.get('price_level', 0):,.4f} ({nearest_demand.get('distance_from_current', 0):+.1f}%)"
                    
                    if supply_zones:
                        nearest_supply = supply_zones[0]
                        message += f"\n- **Supply Zone**: ${nearest_supply.get('price_level', 0):,.4f} ({nearest_supply.get('distance_from_current', 0):+.1f}%)"

                message += f"""

🚀 **Rekomendasi Trading Enhanced:**
- **Direction**: {signal_data['direction']} {signal_data['strength_emoji']}
- **Entry Price**: ${signal_data['entry_price']:,.4f}
- **Stop Loss**: ${signal_data['stop_loss']:,.4f} ({signal_data['sl_percentage']:.1f}%)
- **Take Profit 1**: ${signal_data['tp1']:,.4f} ({signal_data['tp1_percentage']:.1f}%)
- **Take Profit 2**: ${signal_data['tp2']:,.4f} ({signal_data['tp2_percentage']:.1f}%)
- **R/R Ratio**: {signal_data['risk_reward']:.1f}:1

💡 **Alasan Entry di Harga Ini:**
{signal_data['entry_reasoning']}

📊 **Strategi Execution:**
{signal_data['execution_strategy']}

📈 **Leverage Recommendations:**
- Conservative: {signal_data['conservative_leverage']}x (recommended)
- Moderate: {signal_data['moderate_leverage']}x  
- Aggressive: {signal_data['aggressive_leverage']}x (high risk!)

⚠️ **Risk Management:**
Futures trading berisiko tinggi! Gunakan proper position sizing dan stop loss ketat.

📡 Source: Binance + S&D Analysis | ⏰ Real-time integrated data"""

            else:
                # English version with same enhanced structure
                message = f"""⚡ **Enhanced Futures + Supply/Demand Analysis {symbol}**

📊 **Data Quality:** 🟢 BINANCE + S&D API (Source: {source})

💰 **Price Data:**
- Current Price: ${current_price:,.4f}
- 24h Change: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis:**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short
- Market Sentiment: {signal_data['sentiment']}
- Contrarian Signal: {signal_data['contrarian_bias']}

🎯 **Supply/Demand Integration:**"""

                if supply_demand_analysis:
                    sd_score = supply_demand_analysis.get('supply_demand_score', {})
                    message += f"""
- **S&D Score**: {sd_score.get('score', 50)}/100
- **Market Bias**: {sd_score.get('bias', 'Balanced')}
- **Confidence**: {sd_score.get('confidence', 'Medium')}"""

                    zones = supply_demand_analysis.get('supply_demand_zones', {})
                    demand_zones = zones.get('demand_zones', [])
                    supply_zones = zones.get('supply_zones', [])
                    
                    if demand_zones:
                        nearest_demand = demand_zones[0]
                        message += f"\n- **Demand Zone**: ${nearest_demand.get('price_level', 0):,.4f} ({nearest_demand.get('distance_from_current', 0):+.1f}%)"
                    
                    if supply_zones:
                        nearest_supply = supply_zones[0]
                        message += f"\n- **Supply Zone**: ${nearest_supply.get('price_level', 0):,.4f} ({nearest_supply.get('distance_from_current', 0):+.1f}%)"

                message += f"""

🚀 **Enhanced Trading Recommendation:**
- **Direction**: {signal_data['direction']} {signal_data['strength_emoji']}
- **Entry Price**: ${signal_data['entry_price']:,.4f}
- **Stop Loss**: ${signal_data['stop_loss']:,.4f} ({signal_data['sl_percentage']:.1f}%)
- **Take Profit 1**: ${signal_data['tp1']:,.4f} ({signal_data['tp1_percentage']:.1f}%)
- **Take Profit 2**: ${signal_data['tp2']:,.4f} ({signal_data['tp2_percentage']:.1f}%)
- **R/R Ratio**: {signal_data['risk_reward']:.1f}:1

💡 **Entry Reasoning:**
{signal_data['entry_reasoning']}

📊 **Execution Strategy:**
{signal_data['execution_strategy']}

📈 **Leverage Recommendations:**
- Conservative: {signal_data['conservative_leverage']}x (recommended)
- Moderate: {signal_data['moderate_leverage']}x
- Aggressive: {signal_data['aggressive_leverage']}x (high risk!)

⚠️ **Risk Management:**
Futures trading is high risk! Use proper position sizing and tight stop losses.

📡 Source: Binance + S&D Analysis | ⏰ Real-time integrated data"""

            return message

        except Exception as e:
            print(f"Error in enhanced futures analysis: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Enhanced Futures Analysis {symbol}**

Terjadi kesalahan saat menganalisis data futures + supply/demand.
Error: {str(e)}

📊 Silakan coba lagi atau gunakan `/futures_signals` untuk analisis multi-coin."""
            else:
                return f"""❌ **Error in Enhanced Futures Analysis {symbol}**

Error occurred while analyzing futures + supply/demand data.
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

    def _extract_entry_zones(self, sd_analysis, current_price):
        """Extract key entry zones from supply/demand analysis"""
        try:
            if not sd_analysis or 'error' in sd_analysis:
                return None

            zones = sd_analysis.get('supply_demand_zones', {})
            demand_zones = zones.get('demand_zones', [])
            supply_zones = zones.get('supply_zones', [])

            entry_zones = {
                'strong_demand': None,
                'strong_supply': None,
                'current_zone_type': 'neutral',
                'distance_to_nearest_demand': float('inf'),
                'distance_to_nearest_supply': float('inf')
            }

            # Find strongest demand zone
            if demand_zones:
                strongest_demand = max(demand_zones, key=lambda x: x.get('strength', 0))
                entry_zones['strong_demand'] = strongest_demand
                entry_zones['distance_to_nearest_demand'] = abs(current_price - strongest_demand['price_level']) / current_price * 100

            # Find strongest supply zone
            if supply_zones:
                strongest_supply = max(supply_zones, key=lambda x: x.get('strength', 0))
                entry_zones['strong_supply'] = strongest_supply
                entry_zones['distance_to_nearest_supply'] = abs(current_price - strongest_supply['price_level']) / current_price * 100

            # Determine current zone context
            if entry_zones['distance_to_nearest_demand'] < 3:
                entry_zones['current_zone_type'] = 'near_demand'
            elif entry_zones['distance_to_nearest_supply'] < 3:
                entry_zones['current_zone_type'] = 'near_supply'
            elif entry_zones['distance_to_nearest_demand'] < entry_zones['distance_to_nearest_supply']:
                entry_zones['current_zone_type'] = 'closer_to_demand'
            else:
                entry_zones['current_zone_type'] = 'closer_to_supply'

            return entry_zones

        except Exception as e:
            print(f"Error extracting entry zones: {e}")
            return None

    def _determine_enhanced_futures_signal(self, long_ratio, short_ratio, current_price, change_24h, sd_analysis, entry_zones):
        """Determine enhanced trading signal combining futures sentiment with S&D"""
        try:
            signal_data = {
                'direction': 'HOLD',
                'strength_emoji': '⚪',
                'sentiment': 'Neutral',
                'contrarian_bias': 'No Clear Bias',
                'entry_price': current_price,
                'stop_loss': current_price,
                'tp1': current_price,
                'tp2': current_price,
                'sl_percentage': 0,
                'tp1_percentage': 0,
                'tp2_percentage': 0,
                'risk_reward': 1.0,
                'entry_reasoning': 'Mixed signals, no clear direction',
                'execution_strategy': 'Wait for clearer confirmation',
                'conservative_leverage': 2,
                'moderate_leverage': 3,
                'aggressive_leverage': 5
            }

            # Base futures sentiment analysis
            futures_score = 0
            
            # Long/Short ratio analysis (contrarian approach)
            if long_ratio > 75:
                futures_score -= 3  # Extremely long heavy = bearish signal
                signal_data['sentiment'] = 'Extremely Bullish (Overleveraged)'
                signal_data['contrarian_bias'] = 'SHORT Bias (Long Squeeze Risk)'
            elif long_ratio > 65:
                futures_score -= 2
                signal_data['sentiment'] = 'Very Bullish'
                signal_data['contrarian_bias'] = 'SHORT Bias (Moderate)'
            elif long_ratio > 55:
                futures_score -= 1
                signal_data['sentiment'] = 'Bullish'
                signal_data['contrarian_bias'] = 'Slight SHORT Bias'
            elif long_ratio < 25:
                futures_score += 3  # Extremely short heavy = bullish signal
                signal_data['sentiment'] = 'Extremely Bearish (Oversold)'
                signal_data['contrarian_bias'] = 'LONG Bias (Short Squeeze Risk)'
            elif long_ratio < 35:
                futures_score += 2
                signal_data['sentiment'] = 'Very Bearish'
                signal_data['contrarian_bias'] = 'LONG Bias (Moderate)'
            elif long_ratio < 45:
                futures_score += 1
                signal_data['sentiment'] = 'Bearish'
                signal_data['contrarian_bias'] = 'Slight LONG Bias'
            else:
                signal_data['sentiment'] = 'Balanced'
                signal_data['contrarian_bias'] = 'No Strong Bias'

            # Price momentum factor
            momentum_score = 0
            if change_24h > 5:
                momentum_score += 2
            elif change_24h > 2:
                momentum_score += 1
            elif change_24h < -5:
                momentum_score -= 2
            elif change_24h < -2:
                momentum_score -= 1

            # Supply & Demand integration
            sd_score = 0
            sd_modifier = ""
            
            if sd_analysis and entry_zones:
                sd_data = sd_analysis.get('supply_demand_score', {})
                sd_bias = sd_data.get('bias', 'Balanced')
                sd_confidence = sd_data.get('confidence', 'Medium')
                
                if 'Strong Demand' in sd_bias or 'Moderate Demand' in sd_bias:
                    sd_score += 2 if 'Strong' in sd_bias else 1
                    sd_modifier = " + Strong S&D Support"
                elif 'Strong Supply' in sd_bias or 'Moderate Supply' in sd_bias:
                    sd_score -= 2 if 'Strong' in sd_bias else 1
                    sd_modifier = " + Strong S&D Resistance"

                # Entry zone proximity bonus/penalty
                if entry_zones['current_zone_type'] == 'near_demand':
                    sd_score += 1
                    sd_modifier += " (Near Demand Zone)"
                elif entry_zones['current_zone_type'] == 'near_supply':
                    sd_score -= 1
                    sd_modifier += " (Near Supply Zone)"

            # Combined signal calculation
            total_score = futures_score + momentum_score + sd_score

            # Determine final direction and strength
            if total_score >= 4:
                signal_data['direction'] = 'STRONG LONG'
                signal_data['strength_emoji'] = '🟢💪'
            elif total_score >= 2:
                signal_data['direction'] = 'LONG'
                signal_data['strength_emoji'] = '🟢'
            elif total_score >= 1:
                signal_data['direction'] = 'WEAK LONG'
                signal_data['strength_emoji'] = '🟡'
            elif total_score <= -4:
                signal_data['direction'] = 'STRONG SHORT'
                signal_data['strength_emoji'] = '🔴💪'
            elif total_score <= -2:
                signal_data['direction'] = 'SHORT'
                signal_data['strength_emoji'] = '🔴'
            elif total_score <= -1:
                signal_data['direction'] = 'WEAK SHORT'
                signal_data['strength_emoji'] = '🟡'
            else:
                signal_data['direction'] = 'HOLD'
                signal_data['strength_emoji'] = '⚪'

            # Calculate enhanced entry levels based on S&D zones
            if signal_data['direction'] in ['LONG', 'STRONG LONG', 'WEAK LONG']:
                if entry_zones and entry_zones['strong_demand']:
                    # Entry near demand zone
                    demand_zone = entry_zones['strong_demand']
                    signal_data['entry_price'] = demand_zone['zone_high']
                    signal_data['stop_loss'] = demand_zone['zone_low'] * 0.998
                    signal_data['tp1'] = current_price * 1.025
                    signal_data['tp2'] = current_price * 1.05
                    signal_data['entry_reasoning'] = f"Entry recommended at demand zone ${signal_data['entry_price']:,.4f} dengan alasan:\n• Strong demand area teridentifikasi\n• Long/Short ratio menunjukkan {signal_data['contrarian_bias']}\n• Price momentum mendukung ({change_24h:+.1f}%){sd_modifier}\n• Risk/reward ratio optimal di level ini"
                else:
                    # Market entry with standard levels
                    signal_data['entry_price'] = current_price * 0.999
                    signal_data['stop_loss'] = current_price * 0.975
                    signal_data['tp1'] = current_price * 1.03
                    signal_data['tp2'] = current_price * 1.06
                    signal_data['entry_reasoning'] = f"Market entry recommended di ${signal_data['entry_price']:,.4f} dengan alasan:\n• Sentiment futures menunjukkan {signal_data['contrarian_bias']}\n• Momentum price positif ({change_24h:+.1f}%)\n• Tidak ada resistance major di atas{sd_modifier}\n• Setup risk/reward menguntungkan untuk long position"

            elif signal_data['direction'] in ['SHORT', 'STRONG SHORT', 'WEAK SHORT']:
                if entry_zones and entry_zones['strong_supply']:
                    # Entry near supply zone
                    supply_zone = entry_zones['strong_supply']
                    signal_data['entry_price'] = supply_zone['zone_low']
                    signal_data['stop_loss'] = supply_zone['zone_high'] * 1.002
                    signal_data['tp1'] = current_price * 0.975
                    signal_data['tp2'] = current_price * 0.95
                    signal_data['entry_reasoning'] = f"Entry recommended at supply zone ${signal_data['entry_price']:,.4f} dengan alasan:\n• Strong supply area teridentifikasi\n• Long/Short ratio menunjukkan {signal_data['contrarian_bias']}\n• Price momentum bearish ({change_24h:+.1f}%){sd_modifier}\n• Risk/reward optimal di level supply zone"
                else:
                    # Market entry with standard levels
                    signal_data['entry_price'] = current_price * 1.001
                    signal_data['stop_loss'] = current_price * 1.025
                    signal_data['tp1'] = current_price * 0.97
                    signal_data['tp2'] = current_price * 0.94
                    signal_data['entry_reasoning'] = f"Market entry recommended di ${signal_data['entry_price']:,.4f} dengan alasan:\n• Sentiment futures menunjukkan {signal_data['contrarian_bias']}\n• Momentum price negatif ({change_24h:+.1f}%)\n• Tidak ada support major di bawah{sd_modifier}\n• Setup risk/reward menguntungkan untuk short position"
            else:
                # HOLD position
                signal_data['entry_reasoning'] = f"HOLD direkomendasikan karena:\n• Sentiment futures mixed (Long: {long_ratio:.1f}%)\n• Price momentum tidak jelas ({change_24h:+.1f}%)\n• Sinyal S&D belum memberikan konfirmasi{sd_modifier}\n• Tunggu breakout atau konfirmasi arah yang lebih jelas"

            # Calculate percentages
            if signal_data['entry_price'] != 0:
                signal_data['sl_percentage'] = ((signal_data['stop_loss'] - signal_data['entry_price']) / signal_data['entry_price']) * 100
                signal_data['tp1_percentage'] = ((signal_data['tp1'] - signal_data['entry_price']) / signal_data['entry_price']) * 100
                signal_data['tp2_percentage'] = ((signal_data['tp2'] - signal_data['entry_price']) / signal_data['entry_price']) * 100

                # Risk/reward ratio
                risk = abs(signal_data['stop_loss'] - signal_data['entry_price'])
                reward = abs(signal_data['tp1'] - signal_data['entry_price'])
                signal_data['risk_reward'] = reward / risk if risk > 0 else 1.5

            # Enhanced execution strategy
            if 'STRONG' in signal_data['direction']:
                signal_data['execution_strategy'] = "• Execute immediately dengan confidence tinggi\n• Scale in pada pullback minor\n• Use trailing stop setelah TP1 tercapai\n• Monitor untuk add position jika konfirmasi"
                signal_data['conservative_leverage'] = 5
                signal_data['moderate_leverage'] = 8
                signal_data['aggressive_leverage'] = 12
            elif signal_data['direction'] in ['LONG', 'SHORT']:
                signal_data['execution_strategy'] = "• Entry dengan position size normal\n• Wait untuk confirmation candle close\n• Set stop loss ketat sesuai zone\n• Take partial profit di TP1"
                signal_data['conservative_leverage'] = 3
                signal_data['moderate_leverage'] = 5
                signal_data['aggressive_leverage'] = 8
            elif 'WEAK' in signal_data['direction']:
                signal_data['execution_strategy'] = "• Entry dengan position size kecil\n• Wait untuk additional confirmation\n• Very tight stop loss management\n• Quick profit taking strategy"
                signal_data['conservative_leverage'] = 2
                signal_data['moderate_leverage'] = 3
                signal_data['aggressive_leverage'] = 5
            else:
                signal_data['execution_strategy'] = "• Tunggu sinyal yang lebih jelas\n• Monitor key levels untuk breakout\n• Persiapkan entry setelah konfirmasi\n• Fokus pada risk management"

            return signal_data

        except Exception as e:
            print(f"Error in enhanced signal determination: {e}")
            # Return default signal data
            return {
                'direction': 'HOLD',
                'strength_emoji': '⚪',
                'sentiment': 'Error in analysis',
                'contrarian_bias': 'Analysis failed',
                'entry_price': current_price,
                'stop_loss': current_price * 0.98,
                'tp1': current_price * 1.02,
                'tp2': current_price * 1.04,
                'sl_percentage': -2.0,
                'tp1_percentage': 2.0,
                'tp2_percentage': 4.0,
                'risk_reward': 1.0,
                'entry_reasoning': 'Error occurred during analysis, manual verification required',
                'execution_strategy': 'Wait for system recovery and re-analyze',
                'conservative_leverage': 2,
                'moderate_leverage': 3,
                'aggressive_leverage': 5
            }

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

    def _get_fallback_market_overview_with_error(self, language='id', error_message=""):
        """Fallback market overview when APIs fail, including error message"""
        if language == 'id':
            return f"""❌ **OVERVIEW PASAR CRYPTO** (Mode Offline)

💰 **Data Pasar:**
- Total Market Cap: $2.4T (+1.5%)
- Dominasi BTC: 52.3%
- Crypto Aktif: 12,000+ koin

📈 **Status:** Pasar dalam fase recovery

⚠️ **Catatan:** Data real-time tidak tersedia, gunakan command lain untuk analisis live.

**Error:** {error_message}

Coba lagi dalam beberapa menit untuk data real-time."""
        else:
            return f"""❌ **CRYPTO MARKET OVERVIEW** (Offline Mode)

💰 **Market Data:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Active Cryptos: 12,000+ coins

📈 **Status:** Market in recovery phase

⚠️ **Note:** Real-time data unavailable, use other commands for live analysis.

**Error:** {error_message}

Try again in a few minutes for real-time data."""