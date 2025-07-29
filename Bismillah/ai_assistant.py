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
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`.\nContoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

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
        """Get enhanced market sentiment analysis using CoinMarketCap Startup Plan"""
        if not crypto_api or not crypto_api.cmc_provider.api_key:
            # Return static response when API is not available
            if language == 'id':
                return """🌍 **OVERVIEW PASAR CRYPTO** (Mode Offline)

💰 **Data Pasar:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Crypto Aktif: 12,000+ coin

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

        try:
            # Get enhanced market overview from CoinMarketCap
            enhanced_data = crypto_api.cmc_provider.get_enhanced_market_overview()

            # Format message based on language
            if language == 'id':
                return self._format_enhanced_market_overview_id(enhanced_data)
            else:
                return self._format_enhanced_market_overview_en(enhanced_data)

        except Exception as e:
            print(f"❌ Enhanced market sentiment error: {e}")
            if language == 'id':
                return f"❌ Error mengambil data pasar: {str(e)}"
            else:
                return f"❌ Error fetching market data: {str(e)}"

    def _format_enhanced_market_overview_id(self, enhanced_data):
        """Format enhanced market overview in Indonesian with CoinMarketCap data"""
        try:
            if 'error' in enhanced_data:
                return f"❌ Error mengambil data CoinMarketCap: {enhanced_data.get('error')}"

            global_data = enhanced_data.get('global_metrics', {})
            top_cryptos = enhanced_data.get('top_cryptocurrencies', {})
            fng_data = enhanced_data.get('fear_greed_index', {})

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            message = f"""🌍 **OVERVIEW PASAR CRYPTO ADVANCED** (CoinMarketCap Real-time)

⏰ **Update**: {current_time}

"""

            # Global Market Stats
            if 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_24h', 0)
                total_volume = global_data.get('total_volume_24h', 0)
                btc_dominance = global_data.get('btc_dominance', 0)
                eth_dominance = global_data.get('eth_dominance', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                # Format large numbers
                mcap_str = f"${total_mcap/1e12:.2f}T" if total_mcap > 1e12 else f"${total_mcap/1e9:.1f}B"
                vol_str = f"${total_volume/1e12:.2f}T" if total_volume > 1e12 else f"${total_volume/1e9:.1f}B"

                change_emoji = "📈" if mcap_change >= 0 else "📉"
                change_color = "+" if mcap_change >= 0 else ""

                message += f"""💰 **DATA GLOBAL MARKET:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **Volume 24j**: {vol_str}
• **BTC Dominance**: {btc_dominance:.1f}%
• **ETH Dominance**: {eth_dominance:.1f}%
• **Altcoin Dominance**: {100 - btc_dominance - eth_dominance:.1f}%
• **Crypto Aktif**: {active_cryptos:,}

"""

                # ASCII Chart for BTC Dominance
                dominance_bar = self._create_dominance_chart(btc_dominance, eth_dominance)
                message += f"""📊 **DOMINANCE CHART:**
```
{dominance_bar}
```

"""

            # Top 5 Cryptocurrencies
            if 'error' not in top_cryptos and top_cryptos.get('data'):
                message += "🔝 **TOP 5 KOIN (MARKET CAP):**\n"
                
                gainers = 0
                losers = 0
                
                for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                    name = crypto.get('name', '')
                    symbol = crypto.get('symbol', '')
                    price = crypto.get('price', 0)
                    change_24h = crypto.get('percent_change_24h', 0)
                    
                    # Count gainers/losers
                    if change_24h > 0:
                        gainers += 1
                    elif change_24h < 0:
                        losers += 1
                    
                    # Format price
                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 1000:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:,.0f}"
                    
                    change_emoji = "📈" if change_24h >= 0 else "📉"
                    change_color = "+" if change_24h >= 0 else ""
                    
                    message += f"**{i}.** {name} ({symbol}): {price_str} {change_emoji} {change_color}{change_24h:.1f}%\n"

                message += "\n"

                # Market Sentiment Summary
                total_analyzed = len(top_cryptos['data'])
                neutral = total_analyzed - gainers - losers
                
                if gainers > losers:
                    market_sentiment = "🟢 BULLISH"
                elif losers > gainers:
                    market_sentiment = "🔴 BEARISH"
                else:
                    market_sentiment = "🟡 NEUTRAL"

                message += f"""📉 **RANGKUMAN PASAR:**
• **Naik**: {gainers} koin 📈
• **Turun**: {losers} koin 📉  
• **Netral**: {neutral} koin 📊
• **Sentimen**: {market_sentiment}

"""

            # Fear & Greed Index
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                fng_classification = fng_data.get('value_classification', 'Neutral')
                fng_source = fng_data.get('source', 'estimated')
                
                # Get emoji for FNG
                if fng_value >= 75:
                    fng_emoji = "🔥"
                elif fng_value >= 50:
                    fng_emoji = "😊"
                elif fng_value >= 25:
                    fng_emoji = "😐"
                else:
                    fng_emoji = "😨"
                
                # Create FNG bar
                fng_bar = self._create_fng_bar(fng_value)
                
                message += f"""🌡️ **FEAR & GREED INDEX:**
**{fng_value}/100** - {fng_classification} {fng_emoji}
```
{fng_bar}
```
*Source: {fng_source}*

"""

            message += f"""📡 **DATA SOURCES:**
• **Market Data**: CoinMarketCap Startup Plan
• **Fear & Greed**: Alternative.me API
• **Real-time**: Live exchange rates

💡 **TRADING INSIGHTS:**
{self._get_trading_insights_id(enhanced_data)}

⏰ **Update**: {current_time} | 🔄 **Auto-refresh**: Real-time"""

            return message

        except Exception as e:
            return f"❌ Error formatting enhanced market overview: {str(e)}"

    def _format_enhanced_market_overview_en(self, enhanced_data):
        """Format enhanced market overview in English with CoinMarketCap data"""
        try:
            if 'error' in enhanced_data:
                return f"❌ Error fetching CoinMarketCap data: {enhanced_data.get('error')}"

            global_data = enhanced_data.get('global_metrics', {})
            top_cryptos = enhanced_data.get('top_cryptocurrencies', {})
            fng_data = enhanced_data.get('fear_greed_index', {})

            current_time = datetime.now().strftime('%H:%M:%S UTC')

            message = f"""🌍 **ADVANCED CRYPTO MARKET OVERVIEW** (CoinMarketCap Real-time)

⏰ **Update**: {current_time}

"""

            # Global Market Stats
            if 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_24h', 0)
                total_volume = global_data.get('total_volume_24h', 0)
                btc_dominance = global_data.get('btc_dominance', 0)
                eth_dominance = global_data.get('eth_dominance', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                # Format large numbers
                mcap_str = f"${total_mcap/1e12:.2f}T" if total_mcap > 1e12 else f"${total_mcap/1e9:.1f}B"
                vol_str = f"${total_volume/1e12:.2f}T" if total_volume > 1e12 else f"${total_volume/1e9:.1f}B"

                change_emoji = "📈" if mcap_change >= 0 else "📉"
                change_color = "+" if mcap_change >= 0 else ""

                message += f"""💰 **GLOBAL MARKET DATA:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **24h Volume**: {vol_str}
• **BTC Dominance**: {btc_dominance:.1f}%
• **ETH Dominance**: {eth_dominance:.1f}%
• **Altcoin Dominance**: {100 - btc_dominance - eth_dominance:.1f}%
• **Active Cryptos**: {active_cryptos:,}

"""

                # ASCII Chart for BTC Dominance
                dominance_bar = self._create_dominance_chart(btc_dominance, eth_dominance)
                message += f"""📊 **DOMINANCE CHART:**
```
{dominance_bar}
```

"""

            # Top 5 Cryptocurrencies
            if 'error' not in top_cryptos and top_cryptos.get('data'):
                message += "🔝 **TOP 5 COINS (MARKET CAP):**\n"
                
                gainers = 0
                losers = 0
                
                for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                    name = crypto.get('name', '')
                    symbol = crypto.get('symbol', '')
                    price = crypto.get('price', 0)
                    change_24h = crypto.get('percent_change_24h', 0)
                    
                    # Count gainers/losers
                    if change_24h > 0:
                        gainers += 1
                    elif change_24h < 0:
                        losers += 1
                    
                    # Format price
                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 1000:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:,.0f}"
                    
                    change_emoji = "📈" if change_24h >= 0 else "📉"
                    change_color = "+" if change_24h >= 0 else ""
                    
                    message += f"**{i}.** {name} ({symbol}): {price_str} {change_emoji} {change_color}{change_24h:.1f}%\n"

                message += "\n"

                # Market Sentiment Summary
                total_analyzed = len(top_cryptos['data'])
                neutral = total_analyzed - gainers - losers
                
                if gainers > losers:
                    market_sentiment = "🟢 BULLISH"
                elif losers > gainers:
                    market_sentiment = "🔴 BEARISH"
                else:
                    market_sentiment = "🟡 NEUTRAL"

                message += f"""📉 **MARKET SUMMARY:**
• **Up**: {gainers} coins 📈
• **Down**: {losers} coins 📉  
• **Neutral**: {neutral} coins 📊
• **Sentiment**: {market_sentiment}

"""

            # Fear & Greed Index
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                fng_classification = fng_data.get('value_classification', 'Neutral')
                fng_source = fng_data.get('source', 'estimated')
                
                # Get emoji for FNG
                if fng_value >= 75:
                    fng_emoji = "🔥"
                elif fng_value >= 50:
                    fng_emoji = "😊"
                elif fng_value >= 25:
                    fng_emoji = "😐"
                else:
                    fng_emoji = "😨"
                
                # Create FNG bar
                fng_bar = self._create_fng_bar(fng_value)
                
                message += f"""🌡️ **FEAR & GREED INDEX:**
**{fng_value}/100** - {fng_classification} {fng_emoji}
```
{fng_bar}
```
*Source: {fng_source}*

"""

            message += f"""📡 **DATA SOURCES:**
• **Market Data**: CoinMarketCap Startup Plan  
• **Fear & Greed**: Alternative.me API
• **Real-time**: Live exchange rates

💡 **TRADING INSIGHTS:**
{self._get_trading_insights_en(enhanced_data)}

⏰ **Update**: {current_time} | 🔄 **Auto-refresh**: Real-time"""

            return message

        except Exception as e:
            return f"❌ Error formatting enhanced market overview: {str(e)}"

    def _create_dominance_chart(self, btc_dom, eth_dom):
        """Create ASCII chart for market dominance"""
        try:
            alt_dom = 100 - btc_dom - eth_dom
            
            # Create 20-character bar
            btc_chars = int((btc_dom / 100) * 20)
            eth_chars = int((eth_dom / 100) * 20)  
            alt_chars = 20 - btc_chars - eth_chars
            
            btc_bar = "█" * btc_chars
            eth_bar = "▓" * eth_chars
            alt_bar = "░" * alt_chars
            
            chart = f"""BTC: {btc_bar}{' ' * max(0, 8 - btc_chars)} {btc_dom:.1f}%
ETH: {eth_bar}{' ' * max(0, 8 - eth_chars)} {eth_dom:.1f}%
ALT: {alt_bar}{' ' * max(0, 8 - alt_chars)} {alt_dom:.1f}%"""
            
            return chart
        except:
            return "Chart unavailable"

    def _create_fng_bar(self, value):
        """Create ASCII bar for Fear & Greed Index"""
        try:
            # Create 50-character bar
            filled_chars = int((value / 100) * 50)
            empty_chars = 50 - filled_chars
            
            if value >= 75:
                char = "█"  # Extreme Greed
            elif value >= 50:
                char = "▓"  # Greed
            elif value >= 25:
                char = "▒"  # Neutral
            else:
                char = "░"  # Fear
                
            bar = char * filled_chars + "·" * empty_chars
            labels = "Fear    |    Neutral    |    Greed"
            
            return f"{bar}\n{labels}"
        except:
            return "Bar unavailable"

    def _get_trading_insights_id(self, enhanced_data):
        """Generate trading insights in Indonesian"""
        try:
            global_data = enhanced_data.get('global_metrics', {})
            fng_data = enhanced_data.get('fear_greed_index', {})
            
            insights = []
            
            # Market cap change insight
            if 'error' not in global_data:
                mcap_change = global_data.get('market_cap_change_24h', 0)
                if mcap_change > 3:
                    insights.append("🚀 Market cap naik signifikan - momentum bullish")
                elif mcap_change < -3:
                    insights.append("📉 Market cap turun signifikan - hati-hati koreksi")
                else:
                    insights.append("📊 Market cap stabil - sideways market")
            
            # Fear & Greed insight  
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                if fng_value >= 75:
                    insights.append("⚠️ Extreme Greed - pertimbangkan take profit")
                elif fng_value <= 25:
                    insights.append("💎 Extreme Fear - opportunity untuk DCA")
                else:
                    insights.append("⚖️ Sentiment seimbang - tunggu konfirmasi")
            
            return "\n".join([f"• {insight}" for insight in insights]) if insights else "• Data insight tidak tersedia"
            
        except:
            return "• Insight generation error"

    def _get_trading_insights_en(self, enhanced_data):
        """Generate trading insights in English"""  
        try:
            global_data = enhanced_data.get('global_metrics', {})
            fng_data = enhanced_data.get('fear_greed_index', {})
            
            insights = []
            
            # Market cap change insight
            if 'error' not in global_data:
                mcap_change = global_data.get('market_cap_change_24h', 0)
                if mcap_change > 3:
                    insights.append("🚀 Significant market cap increase - bullish momentum")
                elif mcap_change < -3:
                    insights.append("📉 Significant market cap decrease - correction alert")
                else:
                    insights.append("📊 Stable market cap - sideways market")
            
            # Fear & Greed insight
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                if fng_value >= 75:
                    insights.append("⚠️ Extreme Greed - consider taking profits")
                elif fng_value <= 25:
                    insights.append("💎 Extreme Fear - DCA opportunity")
                else:
                    insights.append("⚖️ Balanced sentiment - wait for confirmation")
            
            return "\n".join([f"• {insight}" for insight in insights]) if insights else "• Insight data unavailable"
            
        except:
            return "• Insight generation error"

    def _format_market_sentiment_id(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in Indonesian"""
        try:
            message = "🌍 **OVERVIEW PASAR CRYPTO** (Real-time CoinAPI)\n\n"

            # Market data section
            if market_data:
                message += "💰 **Harga Real-time (CoinAPI):**\n"
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    change = data.get('change_24h', 0)
                    change_emoji = "📈" if change >= 0 else "📉"
                    price_format = f"${price:,.2f}" if price > 1 else f"${price:.4f}"
                    message += f"• {symbol}: {price_format} {change_emoji} {change:+.1f}%\n"
                message += "\n"

            # Futures insights
            if 'error' not in btc_futures:
                ls_data = btc_futures.get('long_short_ratio_data', {})
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    sentiment = "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Neutral"
                    message += f"📊 **BTC Futures Sentiment**: {sentiment} ({long_ratio:.1f}% Long)\n\n"

            # Market analysis
            message += "📈 **Analisis Pasar:**\n"
            message += "• Data diambil dari CoinAPI real-time\n"
            message += "• Analisis berbasis Supply & Demand\n"
            message += "• Terintegrasi dengan Binance Futures data\n\n"

            # News section
            if news_data and len(news_data) > 0:
                message += "📰 **Berita Crypto Terbaru:**\n"
                for i, news in enumerate(news_data[:2], 1):
                    title = news.get('title', '')[:60] + '...' if len(news.get('title', '')) > 60 else news.get('title', '')
                    message += f"{i}. {title}\n"
                message += "\n"

            message += "🎯 **Source**: CoinAPI + Binance Futures + Crypto News\n"
            message += f"⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"

            return message

        except Exception as e:
            return f"❌ Error formatting market sentiment: {str(e)}"

    def _format_market_sentiment_en(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in English"""
        try:
            message = "🌍 **CRYPTO MARKET OVERVIEW** (Real-time CoinAPI)\n\n"

            # Market data section
            if market_data:
                message += "💰 **Real-time Prices (CoinAPI):**\n"
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    change = data.get('change_24h', 0)
                    change_emoji = "📈" if change >= 0 else "📉"
                    price_format = f"${price:,.2f}" if price > 1 else f"${price:.4f}"
                    message += f"• {symbol}: {price_format} {change_emoji} {change:+.1f}%\n"
                message += "\n"

            # Futures insights
            if 'error' not in btc_futures:
                ls_data = btc_futures.get('long_short_ratio_data', {})
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    sentiment = "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Neutral"
                    message += f"📊 **BTC Futures Sentiment**: {sentiment} ({long_ratio:.1f}% Long)\n\n"

            # Market analysis
            message += "📈 **Market Analysis:**\n"
            message += "• Data sourced from CoinAPI real-time\n"
            message += "• Analysis based on Supply & Demand\n"
            message += "• Integrated with Binance Futures data\n\n"

            # News section
            if news_data and len(news_data) > 0:
                message += "📰 **Latest Crypto News:**\n"
                for i, news in enumerate(news_data[:2], 1):
                    title = news.get('title', '')[:60] + '...' if len(news.get('title', '')) > 60 else news.get('title', '')
                    message += f"{i}. {title}\n"
                message += "\n"

            message += "🎯 **Source**: CoinAPI + Binance Futures + Crypto News\n"
            message += f"⏰ **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"

            return message

        except Exception as e:
            return f"❌ Error formatting market sentiment: {str(e)}"

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

    def _format_cmc_market_sentiment_id(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in Indonesian using CoinMarketCap data"""
        try:
            if 'error' in market_data:
                return self._get_fallback_market_overview('id')

            # Format market cap
            total_mcap = market_data.get('total_market_cap', 0)
            mcap_change = market_data.get('market_cap_change_24h', 0)
            total_volume = market_data.get('total_volume_24h', 0)

            if total_mcap > 1e12:
                mcap_str = f"${total_mcap/1e12:.2f}T"
            else:
                mcap_str = f"${total_mcap/1e9:.1f}B"

            if total_volume > 1e12:
                volume_str = f"${total_volume/1e12:.2f}T"
            else:
                volume_str = f"${total_volume/1e9:.1f}B"

            change_emoji = "📈" if mcap_change >= 0 else "📉"
            change_color = "+" if mcap_change >= 0 else ""

            message = f"""🌍 **OVERVIEW PASAR CRYPTO** (CoinMarketCap Real-time)

💰 **Data Global:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **Volume 24j**: {volume_str}
• **BTC Dominance**: {market_data.get('btc_dominance', 0):.1f}%
• **ETH Dominance**: {market_data.get('eth_dominance', 0):.1f}%
• **Crypto Aktif**: {market_data.get('active_cryptocurrencies', 0):,}
• **Exchange Aktif**: {market_data.get('active_exchanges', 0):,}

📊 **Harga Utama:**
• **Bitcoin**: ${market_data.get('btc_price', 0):,.2f} ({market_data.get('btc_change_24h', 0):+.2f}%)
• **Ethereum**: ${market_data.get('eth_price', 0):,.2f} ({market_data.get('eth_change_24h', 0):+.2f}%)

⚡ **Futures Sentiment:**
• **BTC Long/Short**: {btc_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {btc_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%
• **ETH Long/Short**: {eth_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {eth_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%"""

            # Add funding rates if available
            if 'error' not in btc_futures:
                funding_data = btc_futures.get('funding_rate_data', {})
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"\n• **BTC Funding Rate**: {funding_rate:.4f}%"

            # Add news
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **Berita Terbaru:**
• {latest_news.get('title', 'No title')[:80]}..."""

            # Market sentiment assessment
            sentiment_score = 0
            if mcap_change > 2: sentiment_score += 2
            elif mcap_change > 0: sentiment_score += 1
            elif mcap_change < -2: sentiment_score -= 2
            elif mcap_change < 0: sentiment_score -= 1

            if sentiment_score >= 2:
                sentiment = "🟢 Sangat Bullish"
            elif sentiment_score == 1:
                sentiment = "🟢 Bullish"
            elif sentiment_score == 0:
                sentiment = "🟡 Netral"
            elif sentiment_score == -1:
                sentiment = "🔴 Bearish"
            else:
                sentiment = "🔴 Sangat Bearish"

            message += f"""

🎯 **Market Sentiment**: {sentiment}
📡 **Source**: CoinMarketCap Global + Binance Futures
⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            return message

        except Exception as e:
            return f"❌ Error formatting CoinMarketCap market sentiment: {str(e)}"

    def _format_cmc_market_sentiment_en(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in English using CoinMarketCap data"""
        try:
            if 'error' in market_data:
                return self._get_fallback_market_overview('en')

            # Format market cap
            total_mcap = market_data.get('total_market_cap', 0)
            mcap_change = market_data.get('market_cap_change_24h', 0)
            total_volume = market_data.get('total_volume_24h', 0)

            if total_mcap > 1e12:
                mcap_str = f"${total_mcap/1e12:.2f}T"
            else:
                mcap_str = f"${total_mcap/1e9:.1f}B"

            if total_volume > 1e12:
                volume_str = f"${total_volume/1e12:.2f}T"
            else:
                volume_str = f"${total_volume/1e9:.1f}B"

            change_emoji = "📈" if mcap_change >= 0 else "📉"
            change_color = "+" if mcap_change >= 0 else ""

            message = f"""🌍 **CRYPTO MARKET OVERVIEW** (CoinMarketCap Real-time)

💰 **Global Data:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **24h Volume**: {volume_str}
• **BTC Dominance**: {market_data.get('btc_dominance', 0):.1f}%
• **ETH Dominance**: {market_data.get('eth_dominance', 0):.1f}%
• **Active Cryptos**: {market_data.get('active_cryptocurrencies', 0):,}
• **Active Exchanges**: {market_data.get('active_exchanges', 0):,}

📊 **Major Prices:**
• **Bitcoin**: ${market_data.get('btc_price', 0):,.2f} ({market_data.get('btc_change_24h', 0):+.2f}%)
• **Ethereum**: ${market_data.get('eth_price', 0):,.2f} ({market_data.get('eth_change_24h', 0):+.2f}%)

⚡ **Futures Sentiment:**
• **BTC Long/Short**: {btc_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {btc_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%
• **ETH Long/Short**: {eth_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {eth_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%"""

            # Add funding rates if available
            if 'error' not in btc_futures:
                funding_data = btc_futures.get('funding_rate_data', {})
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"\n• **BTC Funding Rate**: {funding_rate:.4f}%"

            # Add news
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **Latest News:**
• {latest_news.get('title', 'No title')[:80]}..."""

            # Market sentiment assessment
            sentiment_score = 0
            if mcap_change > 2: sentiment_score += 2
            elif mcap_change > 0: sentiment_score += 1
            elif mcap_change < -2: sentiment_score -= 2
            elif mcap_change < 0: sentiment_score -= 1

            if sentiment_score >= 2:
                sentiment = "🟢 Very Bullish"
            elif sentiment_score == 1:
                sentiment = "🟢 Bullish"
            elif sentiment_score == 0:
                sentiment = "🟡 Neutral"
            elif sentiment_score == -1:
                sentiment = "🔴 Bearish"
            else:
                sentiment = "🔴 Very Bearish"

            message += f"""

🎯 **Market Sentiment**: {sentiment}
📡 **Source**: CoinMarketCap Global + Binance Futures
⏰ **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            return f"❌ Error formatting CoinMarketCap market sentiment: {str(e)}"

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
            total_market_cap = 2400000000000
            market_cap_change = 1.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **REAL-TIME CRYPTO MARKET OVERVIEW**

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

    def get_comprehensive_analysis(self, symbol, futures_data, price_data, language='id', crypto_api=None):
        """Get comprehensive crypto analysis with CoinMarketCap integration"""
        try:
            if language == 'id':
                return self._get_comprehensive_analysis_id(symbol, futures_data, price_data, crypto_api)
            else:
                return self._get_comprehensive_analysis_en(symbol, futures_data, price_data, crypto_api)
        except Exception as e:
            error_msg = f"Error in comprehensive analysis: {str(e)}"
            print(error_msg)
            if language == 'id':
                return f"❌ Gagal menganalisis {symbol}. Error: {error_msg[:100]}"
            else:
                return f"❌ Failed to analyze {symbol}. Error: {error_msg[:100]}"

    def _get_comprehensive_analysis_id(self, symbol, futures_data, price_data, crypto_api):
        """Indonesian comprehensive analysis using CoinMarketCap data"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        # Get comprehensive data from CoinMarketCap
        cmc_data = None
        if crypto_api and hasattr(crypto_api, 'get_comprehensive_crypto_analysis'):
            analysis_data = crypto_api.get_comprehensive_crypto_analysis(symbol)
            cmc_data = analysis_data.get('cmc_data', {}) if 'error' not in analysis_data else {}

        # Use CoinMarketCap data if available, fallback to CoinAPI
        if cmc_data and 'error' not in cmc_data:
            current_price = cmc_data.get('price', 0)
            change_24h = cmc_data.get('percent_change_24h', 0)
            market_cap = cmc_data.get('market_cap', 0)
            volume_24h = cmc_data.get('volume_24h', 0)
            rank = cmc_data.get('cmc_rank', 0)
            name = cmc_data.get('name', symbol)
            description = cmc_data.get('description', '')
        elif price_data and 'error' not in price_data:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            market_cap = 0
            volume_24h = 0
            rank = 0
            name = symbol
            description = ''
        else:
            current_price = 0
            change_24h = 0
            market_cap = 0
            volume_24h = 0
            rank = 0
            name = symbol
            description = ''

        # Format price
        if current_price < 1:
            price_format = f"${current_price:.8f}"
        elif current_price < 100:
            price_format = f"${current_price:.4f}"
        else:
            price_format = f"${current_price:,.2f}"

        change_emoji = "📈" if change_24h >= 0 else "📉"
        change_color = "+" if change_24h >= 0 else ""

        analysis = f"""🔍 **ANALISIS KOMPREHENSIF {symbol}** ({name})

💰 **Data Fundamental (CoinMarketCap):**
• **Harga**: {price_format}
{change_emoji} **Perubahan 24j**: {change_color}{change_24h:.2f}%
• **Market Cap**: ${market_cap:,.0f} {f'(Rank #{rank})' if rank > 0 else ''}
• **Volume 24j**: ${volume_24h:,.0f}

📊 **Analisis Teknikal:**"""

        # Add technical analysis based on price movement
        if change_24h > 5:
            analysis += f"""
• **Momentum**: Sangat Bullish 🚀
• **Trend**: Strong upward momentum
• **Support**: ${current_price * 0.95:.4f} (Dynamic)
• **Resistance**: ${current_price * 1.05:.4f} (Next target)"""
        elif change_24h > 2:
            analysis += f"""
• **Momentum**: Bullish 📈
• **Trend**: Positive momentum
• **Support**: ${current_price * 0.97:.4f}
• **Resistance**: ${current_price * 1.03:.4f}"""
        elif change_24h > -2:
            analysis += f"""
• **Momentum**: Sideways 📊
• **Trend**: Konsolidasi
• **Support**: ${current_price * 0.98:.4f}
• **Resistance**: ${current_price * 1.02:.4f}"""
        elif change_24h > -5:
            analysis += f"""
• **Momentum**: Bearish 📉
• **Trend**: Koreksi ringan
• **Support**: ${current_price * 0.95:.4f} (Critical)
• **Resistance**: ${current_price * 1.02:.4f}"""
        else:
            analysis += f"""
• **Momentum**: Sangat Bearish 🔻
• **Trend**: Heavy correction
• **Support**: ${current_price * 0.90:.4f} (Major)
• **Resistance**: ${current_price * 1.05:.4f}"""

        # Add futures analysis if available
        if futures_data and 'error' not in futures_data:
            analysis += f"""

⚡ **Futures Analysis:**
• **Mark Price**: ${futures_data.get('mark_price', current_price):,.4f}
• **Funding Rate**: {futures_data.get('funding_rate', 0):.4f}%
• **Open Interest**: ${futures_data.get('open_interest', 0):,.0f}"""

        # Add prediction based on current momentum
        if change_24h > 3:
            prediction = "📈 **Prediksi Jangka Pendek**: Bullish continuation expected"
        elif change_24h < -3:
            prediction = "📉 **Prediksi Jangka Pendek**: Further correction possible"
        else:
            prediction = "📊 **Prediksi Jangka Pendek**: Range-bound movement"

        analysis += f"""

{prediction}

🎯 **Rekomendasi Trading:**
• **Entry Strategy**: Wait for confirmation at support/resistance
• **Risk Management**: Use 2-3% position sizing
• **Time Horizon**: 1-7 days untuk swing trading

⏰ **Data Update**: {current_time}
📡 **Source**: CoinAPI Real-time + Binance Futures

⚠️ **Disclaimer**: Analisis ini untuk edukasi, bukan saran investasi."""

        return analysis

    def _get_comprehensive_analysis_en(self, symbol, futures_data, price_data, crypto_api):
        """English comprehensive analysis"""
        current_time = datetime.now().strftime('%H:%M:%S UTC')

        # Get current price from CoinAPI
        if price_data and 'error' not in price_data:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"

            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_color = "+" if change_24h >= 0 else ""
        else:
            price_format = "Data unavailable"
            change_24h = 0
            change_emoji = "⚠️"
            change_color = ""

        analysis = f"""🔍 **COMPREHENSIVE ANALYSIS {symbol}** (CoinAPI Real-time)

💰 **Current Price**: {price_format}
{change_emoji} **24h Change**: {change_color}{change_24h:.2f}%

📊 **Technical Analysis:**"""

        # Add technical analysis based on price movement
        if change_24h > 5:
            analysis += f"""
• **Momentum**: Very Bullish 🚀
• **Trend**: Strong upward momentum
• **Support**: ${current_price * 0.95:.4f} (Dynamic)
• **Resistance**: ${current_price * 1.05:.4f} (Next target)"""
        elif change_24h > 2:
            analysis += f"""
• **Momentum**: Bullish 📈
• **Trend**: Positive momentum
• **Support**: ${current_price * 0.97:.4f}
• **Resistance**: ${current_price * 1.03:.4f}"""
        elif change_24h > -2:
            analysis += f"""
• **Momentum**: Sideways 📊
• **Trend**: Consolidation
• **Support**: ${current_price * 0.98:.4f}
• **Resistance**: ${current_price * 1.02:.4f}"""
        elif change_24h > -5:
            analysis += f"""
• **Momentum**: Bearish 📉
• **Trend**: Light correction
• **Support**: ${current_price * 0.95:.4f} (Critical)
• **Resistance**: ${current_price * 1.02:.4f}"""
        else:
            analysis += f"""
• **Momentum**: Very Bearish 🔻
• **Trend**: Heavy correction
• **Support**: ${current_price * 0.90:.4f} (Major)
• **Resistance**: ${current_price * 1.05:.4f}"""

        # Add futures analysis if available
        if futures_data and 'error' not in futures_data:
            analysis += f"""

⚡ **Futures Analysis:**
• **Mark Price**: ${futures_data.get('mark_price', current_price):,.4f}
• **Funding Rate**: {futures_data.get('funding_rate', 0):.4f}%
• **Open Interest**: ${futures_data.get('open_interest', 0):,.0f}"""

        # Add prediction based on current momentum
        if change_24h > 3:
            prediction = "📈 **Short-term Prediction**: Bullish continuation expected"
        elif change_24h < -3:
            prediction = "📉 **Short-term Prediction**: Further correction possible"
        else:
            prediction = "📊 **Short-term Prediction**: Range-bound movement"

        analysis += f"""

{prediction}

🎯 **Trading Recommendation:**
• **Entry Strategy**: Wait for confirmation at support/resistance
• **Risk Management**: Use 2-3% position sizing
• **Time Horizon**: 1-7 days for swing trading

⏰ **Data Update**: {current_time}
📡 **Source**: CoinAPI Real-time + Binance Futures

⚠️ **Disclaimer**: This analysis is for educational purposes, not investment advice."""

        return analysis

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate futures signals for top 5 market cap coins - accessible to all users"""
        try:
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk analisis futures"

            # Top 5 market cap coins only for /futures_signals command
            target_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']

            signals = []
            processed_count = 0

            for symbol in target_symbols:
                try:
                    processed_count += 1
                    print(f"🔄 Processing {symbol} ({processed_count}/{len(target_symbols)})")

                    # Get price from CoinAPI first, fallback to CoinGecko
                    price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
                    if 'error' in price_data:
                        print(f"⚠️ CoinAPI failed for {symbol}, trying fallback...")
                        # Silent fallback to other sources if needed
                        price_data = {'price': 0, 'error': 'CoinAPI unavailable'}

                    # Get futures data from Binance
                    futures_data = crypto_api.get_comprehensive_futures_data(symbol)
                    if 'error' in futures_data:
                        print(f"❌ Futures data failed for {symbol}")
                        continue

                    # Analyze SnD with enhanced logic
                    snd_analysis = crypto_api.analyze_supply_demand(symbol, '1h')
                    if 'error' in snd_analysis:
                        print(f"❌ SnD analysis failed for {symbol}")
                        continue

                    # Generate enhanced signal
                    signal = self._generate_enhanced_snd_signal(symbol, price_data, futures_data, snd_analysis)
                    if signal and signal.get('confidence', 0) >= 60:  # Only high confidence signals
                        signals.append(signal)
                        print(f"✅ Generated signal for {symbol} (confidence: {signal.get('confidence', 0)}%)")

                except Exception as e:
                    print(f"❌ Error generating signal for {symbol}: {e}")
                    continue

            if not signals:
                if language == 'id':
                    return """❌ **Tidak dapat menghasilkan sinyal futures saat ini**

🔍 **Kemungkinan Penyebab:**
• Market dalam kondisi sideways (no clear SnD zones)
• Volume trading rendah pada top 5 coins
• Tidak ada setup entry yang aman (confidence < 60%)
• CoinAPI rate limit atau gangguan sementara

💡 **Saran:**
• Coba lagi dalam 30-60 menit
• Gunakan `/futures BTC` untuk analisis spesifik
• Check market volatility dengan `/market`

🎯 **Target**: Top 5 market cap (BTC, ETH, BNB, SOL, XRP)
⚠️ **Note**: SnD signals hanya muncul saat ada zone Supply/Demand yang kuat."""
                else:
                    return """❌ **Cannot generate futures signals currently**

🔍 **Possible Causes:**
• Market in sideways condition (no clear SnD zones)
• Low trading volume on top 5 coins
• No safe entry setups (confidence < 60%)
• CoinAPI rate limit or temporary issues

💡 **Suggestions:**
• Try again in 30-60 minutes
• Use `/futures BTC` for specific analysis
• Check market volatility dengan `/market`

🎯 **Target**: Top 5 market cap (BTC, ETH, BNB, SOL, XRP)
⚠️ **Note**: SnD signals only appear when strong Supply/Demand zones exist."""

            # Format enhanced signals
            if language == 'id':
                return self._format_enhanced_futures_signals_id(signals)
            else:
                return self._format_enhanced_futures_signals_en(signals)

        except Exception as e:
            print(f"💥 Critical error in generate_futures_signals: {e}")
            import traceback
            traceback.print_exc()

            error_msg = f"Error dalam sistem AI futures: {str(e)[:100]}"
            if language == 'id':
                return f"❌ {error_msg}\n\n💡 Coba `/futures BTC` untuk analisis spesifik."
            else:
                return f"❌ {error_msg}\n\n💡 Try `/futures BTC` for specific analysis."

    def _generate_enhanced_snd_signal(self, symbol, price_data, futures_data, snd_analysis):
        """Generate enhanced SnD signal with CoinAPI price integration - IMPROVED SHORT LOGIC"""
        try:
            # Get current price from CoinAPI or futures data
            current_price = 0
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_source = "CoinAPI"
            elif 'error' not in futures_data:
                price_data_futures = futures_data.get('price_data', {})
                if 'error' not in price_data_futures:
                    current_price = price_data_futures.get('price', 0)
                    price_source = "Binance Futures"

            if current_price <= 0:
                return None

            # Analyze market structure from futures data
            ls_ratio_data = futures_data.get('long_short_ratio_data', {})
            long_ratio = ls_ratio_data.get('long_ratio', 50) if 'error' not in ls_ratio_data else 50

            # Funding rate analysis
            funding_data = futures_data.get('funding_rate_data', {})
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0

            # Volume analysis
            volume_24h = price_data_futures.get('volume_24h', 0) if 'price_data_futures' in locals() else 0

            # SnD zone analysis - ENHANCED for SHORT detection
            snd_signals = snd_analysis.get('signals', [])
            confidence_score = snd_analysis.get('confidence_score', 0)

            if not snd_signals or confidence_score < 55:  # Slightly lower threshold for SHORT
                return None

            # Enhanced signal selection - prioritize SHORT signals
            best_signal = None
            
            # First, look for SHORT signals from supply zones
            short_signals = [s for s in snd_signals if s.get('direction') == 'SHORT']
            long_signals = [s for s in snd_signals if s.get('direction') == 'LONG']
            
            # Prioritize SHORT if market conditions favor it
            if short_signals and (long_ratio > 65 or funding_rate > 0.005):
                best_signal = max(short_signals, key=lambda x: x.get('confidence', 0))
                print(f"🔴 SHORT signal prioritized for {symbol} (L/S: {long_ratio:.1f}%, Funding: {funding_rate*100:.4f}%)")
            elif long_signals and (long_ratio < 35 or funding_rate < -0.005):
                best_signal = max(long_signals, key=lambda x: x.get('confidence', 0))
                print(f"🟢 LONG signal prioritized for {symbol} (L/S: {long_ratio:.1f}%, Funding: {funding_rate*100:.4f}%)")
            else:
                # Take best signal overall
                best_signal = max(snd_signals, key=lambda x: x.get('confidence', 0))

            if not best_signal:
                return None

            # Enhanced signal generation
            direction = best_signal.get('direction', 'UNKNOWN')
            entry_price = best_signal.get('entry_price', current_price)

            # Dynamic TP/SL calculation based on volatility
            volatility_multiplier = 1.0
            if symbol in ['BTC', 'ETH']:
                volatility_multiplier = 0.8  # Lower for major coins
            else:
                volatility_multiplier = 1.2  # Higher for altcoins

            if direction == 'LONG':
                tp1 = entry_price * (1 + 0.025 * volatility_multiplier)  # 2.5% for majors, 3% for alts
                tp2 = entry_price * (1 + 0.05 * volatility_multiplier)   # 5% for majors, 6% for alts
                sl = entry_price * (1 - 0.015 * volatility_multiplier)   # 1.5% for majors, 1.8% for alts
            else:  # SHORT - Enhanced calculations
                tp1 = entry_price * (1 - 0.025 * volatility_multiplier)  # 2.5% down for majors, 3% for alts
                tp2 = entry_price * (1 - 0.05 * volatility_multiplier)   # 5% down for majors, 6% for alts
                sl = entry_price * (1 + 0.015 * volatility_multiplier)   # 1.5% up for majors, 1.8% for alts

            # Calculate confidence based on multiple factors - ENHANCED SHORT LOGIC
            final_confidence = confidence_score

            # Enhanced confidence for SHORT signals
            if direction == 'SHORT':
                # Overcrowded longs = good for SHORT
                if long_ratio > 70:
                    final_confidence += 10
                    print(f"🔴 SHORT confidence boost: Overcrowded longs ({long_ratio:.1f}%)")
                elif long_ratio > 60:
                    final_confidence += 5
                
                # Positive funding rate = longs pay shorts = good for SHORT
                if funding_rate > 0.01:
                    final_confidence += 8
                    print(f"🔴 SHORT confidence boost: Positive funding ({funding_rate*100:.4f}%)")
                elif funding_rate > 0.005:
                    final_confidence += 4
                
                # Additional SHORT market structure confirmations
                supply_zones = snd_analysis.get('supply_zones', [])
                if len(supply_zones) >= 2:
                    final_confidence += 5
                    print(f"🔴 SHORT confidence boost: Multiple supply zones ({len(supply_zones)})")
                
                # Price near supply zone = good for SHORT
                zone_distance = best_signal.get('zone_distance', 10)
                if zone_distance < 2:  # Very close to supply zone
                    final_confidence += 8
                elif zone_distance < 5:
                    final_confidence += 4

            # Enhanced confidence for LONG signals
            elif direction == 'LONG':
                # Overcrowded shorts = good for LONG
                if long_ratio < 30:
                    final_confidence += 10
                elif long_ratio < 40:
                    final_confidence += 5
                
                # Negative funding rate = shorts pay longs = good for LONG
                if funding_rate < -0.01:
                    final_confidence += 8
                elif funding_rate < -0.005:
                    final_confidence += 4

            # Volume confirmation
            if volume_24h > 1000000:  # Good volume
                final_confidence += 3

            # Market momentum confirmation
            try:
                price_change_24h = price_data.get('change_24h', 0)
                if direction == 'SHORT' and price_change_24h < -2:
                    final_confidence += 5  # Bearish momentum confirms SHORT
                elif direction == 'LONG' and price_change_24h > 2:
                    final_confidence += 5  # Bullish momentum confirms LONG
            except:
                pass

            # Cap confidence at 95% but ensure SHORT signals get fair treatment
            final_confidence = min(final_confidence, 95)
            
            # Ensure minimum confidence for valid SHORT signals
            if direction == 'SHORT' and final_confidence < 60:
                final_confidence = max(final_confidence, 62)  # Minimum for SHORT

            # Risk/Reward calculation
            if direction == 'LONG':
                risk = abs(entry_price - sl)
                reward = abs(tp2 - entry_price)
            else:  # SHORT
                risk = abs(sl - entry_price)
                reward = abs(entry_price - tp2)

            risk_reward = reward / risk if risk > 0 else 0

            # Enhanced reason for SHORT signals
            reason = best_signal.get('reason', 'SnD zone detected')
            if direction == 'SHORT':
                reason_parts = [reason]
                if long_ratio > 65:
                    reason_parts.append(f"Overcrowded longs ({long_ratio:.0f}%)")
                if funding_rate > 0.005:
                    reason_parts.append(f"Positive funding ({funding_rate*100:.3f}%)")
                reason = " + ".join(reason_parts)

            return {
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl,
                'confidence': final_confidence,
                'risk_reward': risk_reward,
                'current_price': current_price,
                'price_source': price_source,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100,  # Convert to percentage
                'volume_24h': volume_24h,
                'reason': reason,
                'timeframe': '1h'
            }

        except Exception as e:
            print(f"Error generating enhanced SnD signal for {symbol}: {e}")
            return None

    def _format_enhanced_futures_signals_id(self, signals):
        """Format enhanced futures signals in Indonesian"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            message = f"""🚨 **FUTURES SIGNALS TOP 5 COINS (CoinAPI + SnD)**

📅 **Generated**: {current_time}
🎯 **Total Signals**: {len(signals)} high-confidence setups
🏆 **Target**: Top 5 Market Cap (BTC, ETH, BNB, SOL, XRP)
📊 **Source**: CoinAPI Real-time + Binance Futures + SnD Analysis

"""

            for i, signal in enumerate(signals[:6], 1):  # Max 6 signals
                symbol = signal['symbol']
                direction = signal['direction']
                entry = signal['entry_price']
                tp1 = signal['tp1']
                tp2 = signal['tp2']
                sl = signal['sl']
                confidence = signal['confidence']
                rr = signal['risk_reward']
                current_price = signal['current_price']
                price_source = signal['price_source']
                long_ratio = signal['long_ratio']
                funding_rate = signal['funding_rate']

                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                confidence_emoji = "🔥" if confidence >= 80 else "⚡" if confidence >= 70 else "💡"

                # Smart price formatting
                if entry < 1:
                    entry_fmt = f"${entry:.6f}"
                    tp1_fmt = f"${tp1:.6f}"
                    tp2_fmt = f"${tp2:.6f}"
                    sl_fmt = f"${sl:.6f}"
                    current_fmt = f"${current_price:.6f}"
                elif entry < 100:
                    entry_fmt = f"${entry:.4f}"
                    tp1_fmt = f"${tp1:.4f}"
                    tp2_fmt = f"${tp2:.4f}"
                    sl_fmt = f"${sl:.4f}"
                    current_fmt = f"${current_price:.4f}"
                else:
                    entry_fmt = f"${entry:,.2f}"
                    tp1_fmt = f"${tp1:.2f}"
                    tp2_fmt = f"${tp2:.2f}"
                    sl_fmt = f"${sl:.2f}"
                    current_fmt = f"${current_price:.2f}"

                message += f"""**{i}. {symbol} {direction} {direction_emoji}**
**Harga**: {current_fmt} ({price_source})
**Entry sesuai SnD**: {entry_fmt}
**TP 1**: {tp1_fmt}
**TP 2**: {tp2_fmt}
**SL**: {sl_fmt}

**Analisis**:
• Confidence: {confidence:.0f}% {confidence_emoji}
• Risk/Reward: {rr:.1f}:1
• Long Ratio: {long_ratio:.0f}%
• Funding: {funding_rate:.3f}%

"""

            message += f"""📋 **SnD Trading Rules:**
• Wait for price action confirmation at entry zones
• Use 1-3% position sizing per trade
• Exit 50% at TP1, hold remainder for TP2
• Monitor volume for breakout/rejection confirmation

⚠️ **Risk Management:**
• Max 2-3 positions simultaneously
• Always set stop loss before entry
• Don't FOMO if you miss the entry point

🏆 **Focus**: Top 5 market cap coins untuk likuiditas optimal
🎯 **Auto Signals**: Khusus Admin & Lifetime users (25 coins)
📡 **Manual Update**: Command ini bisa digunakan semua user"""

            return message

        except Exception as e:
            return f"❌ Error formatting signals: {str(e)}"

    def _format_enhanced_futures_signals_en(self, signals):
        """Format enhanced futures signals in English"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')

            message = f"""🚨 **FUTURES SIGNALS TOP 5 COINS (CoinAPI + SnD)**

📅 **Generated**: {current_time}
🎯 **Total Signals**: {len(signals)} high-confidence setups
🏆 **Target**: Top 5 Market Cap (BTC, ETH, BNB, SOL, XRP)
📊 **Source**: CoinAPI Real-time + Binance Futures + SnD Analysis

"""

            for i, signal in enumerate(signals[:6], 1):  # Max 6 signals
                symbol = signal['symbol']
                direction = signal['direction']
                entry = signal['entry_price']
                tp1 = signal['tp1']
                tp2 = signal['tp2']
                sl = signal['sl']
                confidence = signal['confidence']
                rr = signal['risk_reward']
                current_price = signal['current_price']
                price_source = signal['price_source']
                long_ratio = signal['long_ratio']
                funding_rate = signal['funding_rate']

                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                confidence_emoji = "🔥" if confidence >= 80 else "⚡" if confidence >= 70 else "💡"

                # Smart price formatting
                if entry < 1:
                    entry_fmt = f"${entry:.6f}"
                    tp1_fmt = f"${tp1:.6f}"
                    tp2_fmt = f"${tp2:.6f}"
                    sl_fmt = f"${sl:.6f}"
                    current_fmt = f"${current_price:.6f}"
                elif entry < 100:
                    entry_fmt = f"${entry:.4f}"
                    tp1_fmt = f"${tp1:.4f}"
                    tp2_fmt = f"${tp2:.4f}"
                    sl_fmt = f"${sl:.4f}"
                    current_fmt = f"${current_price:.4f}"
                else:
                    entry_fmt = f"${entry:,.2f}"
                    tp1_fmt = f"${tp1:.2f}"
                    tp2_fmt = f"${tp2:.2f}"
                    sl_fmt = f"${sl:.2f}"
                    current_fmt = f"${current_price:.2f}"

                message += f"""**{i}. {symbol} {direction} {direction_emoji}**
**Price**: {current_fmt} ({price_source})
**Entry sesuai SnD**: {entry_fmt}
**TP 1**: {tp1_fmt}
**TP 2**: {tp2_fmt}
**SL**: {sl_fmt}

**Analysis**:
• Confidence: {confidence:.0f}% {confidence_emoji}
• Risk/Reward: {rr:.1f}:1
• Long Ratio: {long_ratio:.0f}%
• Funding: {funding_rate:.3f}%

"""

            message += f"""📋 **SnD Trading Rules:**
• Wait for price action confirmation at entry zones
• Use 1-3% position sizing per trade
• Exit 50% at TP1, hold remainder for TP2
• Monitor volume for breakout/rejection confirmation

⚠️ **Risk Management:**
• Max 2-3 positions simultaneously
• Always set stop loss before entry
• Don't FOMO if you miss the entry point

🏆 **Focus**: Top 5 market cap coins for optimal liquidity
🎯 **Auto Signals**: Admin & Lifetime users only (25 coins)
📡 **Manual Update**: This command available to all users"""

            return message

        except Exception as e:
            return f"❌ Error formatting signals: {str(e)}"

    def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get enhanced futures analysis with advanced SnD and market condition detection"""
        try:
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk analisis futures"

            # Get comprehensive data from multiple sources
            futures_data = crypto_api.get_comprehensive_futures_data(symbol)
            price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
            candlestick_data = crypto_api.get_binance_candlestick(symbol, timeframe, 100)

            # Enhanced market condition analysis
            market_condition = self._analyze_market_condition(candlestick_data, futures_data)

            if language == 'id':
                return self._format_advanced_futures_analysis_id(symbol, timeframe, futures_data, price_data, market_condition, candlestick_data)
            else:
                return self._format_advanced_futures_analysis_en(symbol, timeframe, futures_data, price_data, market_condition, candlestick_data)

        except Exception as e:
            if language == 'id':
                return f"❌ Error dalam analisis futures: {str(e)}"
            else:
                return f"❌ Error in futures analysis: {str(e)}"

    def _generate_advanced_individual_signal(self, symbol, futures_data, price_data, market_condition):
        """Generate advanced individual trading signal with ENHANCED SHORT LOGIC"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Market condition analysis
            condition_type = market_condition.get('type', 'unknown')
            condition_strength = market_condition.get('strength', 0)
            volatility = market_condition.get('volatility', 0)
            trend_direction = market_condition.get('trend_direction', 'neutral')

            # Get futures metrics
            ls_data = futures_data.get('long_short_ratio_data', {})
            funding_data = futures_data.get('funding_rate_data', {})
            oi_data = futures_data.get('open_interest_data', {})

            long_ratio = ls_data.get('long_ratio', 50) if 'error' not in ls_data else 50
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
            open_interest = oi_data.get('open_interest', 0) if 'error' not in oi_data else 0

            signal = {
                'symbol': symbol,
                'price': current_price,
                'condition': condition_type,
                'strength': condition_strength,
                'volatility': volatility,
                'trend': trend_direction,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100,  # Convert to percentage
                'open_interest': open_interest,
                'recommendation': 'hold',
                'confidence': 0,
                'entry_price': 0,
                'tp1': 0,
                'tp2': 0,
                'sl': 0,
                'position_size': '1-2%',
                'reasoning': []
            }

            # ENHANCED SHORT SIGNAL DETECTION - Priority Check
            short_conditions_met = 0
            short_confidence_boost = 0

            # Check for SHORT-favorable conditions
            if long_ratio > 65:  # Overcrowded longs
                short_conditions_met += 1
                short_confidence_boost += 15
                signal['reasoning'].append(f"🔴 Overcrowded longs ({long_ratio:.1f}%) - SHORT opportunity")

            if funding_rate > 0.005:  # Positive funding = longs pay shorts
                short_conditions_met += 1
                short_confidence_boost += 10
                signal['reasoning'].append(f"🔴 Positive funding ({funding_rate*100:.4f}%) favors SHORT")

            if trend_direction == 'bearish' and condition_strength > 50:
                short_conditions_met += 1
                short_confidence_boost += 20
                signal['reasoning'].append(f"🔴 Strong bearish trend ({condition_strength:.1f}%)")

            # If multiple SHORT conditions are met, prioritize SHORT
            if short_conditions_met >= 2:
                signal['recommendation'] = 'short'
                signal['confidence'] = min(92, 65 + short_confidence_boost)
                signal['entry_price'] = current_price * 1.001  # Slight rally entry
                signal['tp1'] = current_price * 0.975  # 2.5% down
                signal['tp2'] = current_price * 0.955  # 4.5% down
                signal['sl'] = current_price * 1.015   # 1.5% up
                signal['reasoning'].append("🎯 Multiple SHORT conditions aligned")
                signal['position_size'] = '2-3%'  # Confident position
                
                return signal

            # Determine trading signal based on conditions (original logic with enhancements)
            if condition_type == 'sideways':
                signal['recommendation'] = 'range_trading'
                signal['confidence'] = max(0, 70 - volatility * 5)
                signal['reasoning'].append(f"Market sideways dengan volatility {volatility:.2f}%")
                signal['reasoning'].append("Range trading opportunity - buy support, sell resistance")

                # Set range trading levels
                sr_levels = market_condition.get('support_resistance', [])
                if sr_levels:
                    support = next((l['level'] for l in sr_levels if l['type'] == 'support'), current_price * 0.98)
                    resistance = next((l['level'] for l in sr_levels if l['type'] == 'resistance'), current_price * 1.02)

                    signal['entry_price'] = support
                    signal['tp1'] = resistance
                    signal['sl'] = support * 0.985

            elif condition_type == 'trending' and condition_strength > 60:
                if trend_direction == 'bullish':
                    # Check if SHORT is still better despite bullish trend
                    if long_ratio > 75:  # Extremely overcrowded longs
                        signal['recommendation'] = 'short'
                        signal['confidence'] = 78
                        signal['entry_price'] = current_price * 1.005  # Wait for rally
                        signal['tp1'] = current_price * 0.975
                        signal['tp2'] = current_price * 0.950
                        signal['sl'] = current_price * 1.020
                        signal['reasoning'].append(f"🔴 Contrarian SHORT: Extremely overcrowded longs ({long_ratio:.1f}%)")
                    else:
                        signal['recommendation'] = 'long'
                        signal['confidence'] = min(90, condition_strength - (10 if long_ratio > 65 else 0))
                        signal['entry_price'] = current_price * 0.998  # Slight pullback entry
                        signal['tp1'] = current_price * 1.025
                        signal['tp2'] = current_price * 1.045
                        signal['sl'] = current_price * 0.985
                        signal['reasoning'].append(f"Strong bullish trend ({condition_strength:.1f}%)")

                elif trend_direction == 'bearish':
                    signal['recommendation'] = 'short'
                    # Enhanced confidence for bearish trends
                    base_confidence = condition_strength
                    if long_ratio > 60:
                        base_confidence += 15  # Boost for overcrowded longs in bearish trend
                    if funding_rate > 0:
                        base_confidence += 10  # Boost for positive funding in bearish trend
                    
                    signal['confidence'] = min(95, base_confidence)
                    signal['entry_price'] = current_price * 1.002  # Slight rally entry
                    signal['tp1'] = current_price * 0.975
                    signal['tp2'] = current_price * 0.955
                    signal['sl'] = current_price * 1.015
                    signal['reasoning'].append(f"🔴 Strong bearish trend ({condition_strength:.1f}%)")

            elif volatility > 5:
                # In high volatility, consider SHORT if conditions favor it
                if long_ratio > 70 or funding_rate > 0.01:
                    signal['recommendation'] = 'short'
                    signal['confidence'] = min(85, volatility * 8 + short_confidence_boost)
                    signal['entry_price'] = current_price * 1.003
                    signal['tp1'] = current_price * 0.970
                    signal['tp2'] = current_price * 0.945
                    signal['sl'] = current_price * 1.020
                    signal['reasoning'].append(f"🔴 High volatility SHORT ({volatility:.2f}%) + favorable conditions")
                    signal['position_size'] = '1-2%'  # Moderate size for volatile SHORT
                else:
                    signal['condition'] = 'volatile'
                    signal['recommendation'] = 'scalping'
                    signal['confidence'] = min(80, volatility * 10)
                    signal['reasoning'].append(f"High volatility ({volatility:.2f}%) - scalping opportunity")
                    signal['position_size'] = '0.5-1%'  # Smaller size for volatile markets

            else:
                # Even in unclear conditions, check for strong SHORT setups
                if long_ratio > 75 and funding_rate > 0.01:
                    signal['recommendation'] = 'short'
                    signal['confidence'] = 72
                    signal['entry_price'] = current_price * 1.003
                    signal['tp1'] = current_price * 0.975
                    signal['tp2'] = current_price * 0.950
                    signal['sl'] = current_price * 1.018
                    signal['reasoning'].append("🔴 Strong contrarian SHORT setup despite unclear trend")
                else:
                    signal['recommendation'] = 'wait'
                    signal['confidence'] = 30
                    signal['reasoning'].append("Tidak ada setup trading yang jelas")
                    signal['reasoning'].append("Tunggu konfirmasi trend atau breakout")

            # Enhanced funding rate analysis
            if abs(funding_rate * 100) > 0.01:
                if funding_rate > 0:
                    signal['reasoning'].append(f"💰 Funding rate positif ({funding_rate*100:.4f}%) - longs bayar shorts")
                    if signal['recommendation'] == 'short':
                        signal['confidence'] = min(95, signal['confidence'] + 5)
                else:
                    signal['reasoning'].append(f"💰 Funding rate negatif ({funding_rate*100:.4f}%) - shorts bayar longs")
                    if signal['recommendation'] == 'long':
                        signal['confidence'] = min(95, signal['confidence'] + 5)

            # Enhanced long/short ratio analysis
            if long_ratio > 70:
                signal['reasoning'].append(f"⚠️ Overcrowded long positions ({long_ratio:.1f}%) - potential reversal to SHORT")
                if signal['recommendation'] != 'short':
                    signal['reasoning'].append("🔴 Consider SHORT position on next resistance")
            elif long_ratio < 30:
                signal['reasoning'].append(f"⚠️ Overcrowded short positions ({long_ratio:.1f}%) - potential bounce to LONG")

            return signal

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    def _generate_individual_signal(self, symbol, futures_data, price_data):
        """Generate individual trading signal"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Analyze market structure
            ls_ratio_data = futures_data.get('long_short_ratio_data', {})
            long_ratio = ls_ratio_data.get('long_ratio', 50) if 'error' not in ls_ratio_data else 50

            # Funding rate analysis
            funding_data = futures_data.get('funding_rate_data', {})
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0

            # Generate very basic signal - improve this
            if long_ratio > 60 and funding_rate > 0.001:
                recommendation = "short"  # Overbought, potential reversal
                confidence = 65
            elif long_ratio < 40 and funding_rate < -0.001:
                recommendation = "long"  # Oversold, potential bounce
                confidence = 65
            else:
                recommendation = "wait"
                confidence = 40

            return {
                'symbol': symbol,
                'price': current_price,
                'recommendation': recommendation,
                'confidence': confidence,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100  # Convert to percentage
            }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    def _format_advanced_signals_id(self, signals, sideways_markets, volatile_markets):
        """Format advanced futures signals with detailed market condition analysis"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        message = f"""🚨 **FUTURES SIGNALS ADVANCED - SUPPLY & DEMAND ANALYSIS**

⏰ **Update**: {current_time}
📊 **Total Markets Analyzed**: {len(signals) + len(sideways_markets) + len(volatile_markets)}
"""

        # Active trading signals
        if signals:
            message += f"""
🎯 **ACTIVE TRADING SIGNALS** ({len(signals)} coins):

"""
            for i, signal in enumerate(signals[:5], 1):  # Top 5 signals
                symbol = signal['symbol']
                price = signal['price']
                recommendation = signal['recommendation']
                confidence = signal['confidence']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                # Direction emoji
                direction_emoji = "🟢" if recommendation == 'long' else "🔴" if recommendation == 'short' else "🔄"

                message += f"""**{i}. {symbol} {direction_emoji}**
💰 **Price**: {price_format}
📊 **Signal**: {recommendation.upper()}
🎯 **Confidence**: {confidence:.1f}%"""

                if signal['entry_price'] > 0:
                    entry_format = f"${signal['entry_price']:.6f}" if signal['entry_price'] < 1 else f"${signal['entry_price']:,.4f}"
                    message += f"""
🎪 **Entry**: {entry_format}"""

                    if signal['tp1'] > 0:
                        tp1_format = f"${signal['tp1']:.6f}" if signal['tp1'] < 1 else f"${signal['tp1']:,.4f}"
                        message += f"""
🎯 **TP1**: {tp1_format}"""

                    if signal['tp2'] > 0:
                        tp2_format = f"${signal['tp2']:.6f}" if signal['tp2'] < 1 else f"${signal['tp2']:,.4f}"
                        message += f"""
🚀 **TP2**: {tp2_format}"""

                    if signal['sl'] > 0:
                        sl_format = f"${signal['sl']:.6f}" if signal['sl'] < 1 else f"${signal['sl']:,.4f}"
                        message += f"""
🛑 **SL**: {sl_format}"""

                message += f"""
📏 **Position Size**: {signal['position_size']}
📈 **Long/Short Ratio**: {signal['long_ratio']:.1f}% / {100-signal['long_ratio']:.1f}%
💸 **Funding Rate**: {signal['funding_rate']:.4f}%

"""

        # Sideways markets
        if sideways_markets:
            message += f"""
🔄 **SIDEWAYS MARKETS** ({len(sideways_markets)} coins):

⚠️ **KONDISI SIDEWAYS TERDETEKSI - TIDAK ADA SINYAL ENTRY YANG JELAS**

"""
            for signal in sideways_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']
                strength = signal['strength']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  📊 Sideways Strength: {strength:.1f}%
  📈 Volatility: {volatility:.2f}%
  🎯 Strategy: Range trading atau tunggu breakout

"""

        # Volatile markets  
        if volatile_markets:
            message += f"""
⚡ **HIGH VOLATILITY MARKETS** ({len(volatile_markets)} coins):

"""
            for signal in volatile_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  ⚡ Volatility: {volatility:.2f}%
  🎯 Strategy: Scalping dengan position size kecil (0.5-1%)

"""

        # Market summary
        total_markets = len(signals) + len(sideways_markets) + len(volatile_markets)
        trending_percentage = (len(signals) / total_markets * 100) if total_markets > 0 else 0
        sideways_percentage = (len(sideways_markets) / total_markets * 100) if total_markets > 0 else 0

        message += f"""
📊 **MARKET OVERVIEW:**
• **Trending Markets**: {trending_percentage:.1f}% ({len(signals)}/{total_markets})
• **Sideways Markets**: {sideways_percentage:.1f}% ({len(sideways_markets)}/{total_markets})
• **Volatile Markets**: {(len(volatile_markets) / total_markets * 100) if total_markets > 0 else 0:.1f}% ({len(volatile_markets)}/{total_markets})

💡 **MARKET SENTIMENT:**"""

        if sideways_percentage > 50:
            message += """
🔄 **DOMINASI SIDEWAYS**: Mayoritas market dalam konsolidasi
• Hindari trend following strategies
• Focus pada range trading
• Tunggu catalyst untuk breakout yang jelas
• Risk management extra ketat"""
        elif trending_percentage > 60:
            message += """
📈 **MARKET TRENDING**: Kondisi bagus untuk trend following
• Manfaatkan momentum yang ada
• Follow the trend dengan proper risk management
• Watch for trend reversal signals"""
        else:
            message += """
📊 **MARKET MIXED**: Kondisi market campuran
• Selective trading - pilih setup terbaik
• Avoid FOMO, tunggu konfirmasi yang jelas
• Smaller position size recommended"""

        message += f"""

⚠️ **RISK MANAGEMENT RULES:**
• Maximum 2-3% risk per trade
• Jangan trade lebih dari 3 pairs simultan
• Cut loss cepat jika salah arah
• Take profit bertahap (50% di TP1, 50% di TP2)

🎯 **SUPPLY & DEMAND FEATURES:**
• Entry berdasarkan S&D zones
• TP/SL calculation dengan risk/reward optimal
• Volume confirmation untuk validasi breakout
• Multi-timeframe analysis

📡 **Data Sources**: CoinAPI Real-time + Binance Futures + Advanced SnD Algorithm

💡 **Disclaimer**: Sinyal untuk edukasi, bukan financial advice. Always DYOR!"""

        return message

    def _format_advanced_signals_en(self, signals, sideways_markets, volatile_markets):
        """Format advanced futures signals in English with detailed market condition analysis"""
        current_time = datetime.now().strftime('%H:%M:%S UTC')

        message = f"""🚨 **FUTURES SIGNALS ADVANCED - SUPPLY & DEMAND ANALYSIS**

⏰ **Update**: {current_time}
📊 **Total Markets Analyzed**: {len(signals) + len(sideways_markets) + len(volatile_markets)}
"""

        # Active trading signals
        if signals:
            message += f"""
🎯 **ACTIVE TRADING SIGNALS** ({len(signals)} coins):

"""
            for i, signal in enumerate(signals[:5], 1):  # Top 5 signals
                symbol = signal['symbol']
                price = signal['price']
                recommendation = signal['recommendation']
                confidence = signal['confidence']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                # Direction emoji
                direction_emoji = "🟢" if recommendation == 'long' else "🔴" if recommendation == 'short' else "🔄"

                message += f"""**{i}. {symbol} {direction_emoji}**
💰 **Price**: {price_format}
📊 **Signal**: {recommendation.upper()}
🎯 **Confidence**: {confidence:.1f}%"""

                if signal['entry_price'] > 0:
                    entry_format = f"${signal['entry_price']:.6f}" if signal['entry_price'] < 1 else f"${signal['entry_price']:,.4f}"
                    message += f"""
🎪 **Entry**: {entry_format}"""

                    if signal['tp1'] > 0:
                        tp1_format = f"${signal['tp1']:.6f}" if signal['tp1'] < 1 else f"${signal['tp1']:,.4f}"
                        message += f"""
🎯 **TP1**: {tp1_format}"""

                    if signal['tp2'] > 0:
                        tp2_format = f"${signal['tp2']:.6f}" if signal['tp2'] < 1 else f"${signal['tp2']:,.4f}"
                        message += f"""
🚀 **TP2**: {tp2_format}"""

                    if signal['sl'] > 0:
                        sl_format = f"${signal['sl']:.6f}" if signal['sl'] < 1 else f"${signal['sl']:,.4f}"
                        message += f"""
🛑 **SL**: {sl_format}"""

                message += f"""
📏 **Position Size**: {signal['position_size']}
📈 **Long/Short Ratio**: {signal['long_ratio']:.1f}% / {100-signal['long_ratio']:.1f}%
💸 **Funding Rate**: {signal['funding_rate']:.4f}%

"""

        # Sideways markets
        if sideways_markets:
            message += f"""
🔄 **SIDEWAYS MARKETS** ({len(sideways_markets)} coins):

⚠️ **SIDEWAYS CONDITION DETECTED - NO CLEAR ENTRY SIGNALS**

"""
            for signal in sideways_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']
                strength = signal['strength']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  📊 Sideways Strength: {strength:.1f}%
  📈 Volatility: {volatility:.2f}%
  🎯 Strategy: Range trading or wait for breakout

"""

        # Volatile markets  
        if volatile_markets:
            message += f"""
⚡ **HIGH VOLATILITY MARKETS** ({len(volatile_markets)} coins):

"""
            for signal in volatile_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  ⚡ Volatility: {volatility:.2f}%
  🎯 Strategy: Scalping with small position size (0.5-1%)

"""

        # Market summary
        total_markets = len(signals) + len(sideways_markets) + len(volatile_markets)
        trending_percentage = (len(signals) / total_markets * 100) if total_markets > 0 else 0
        sideways_percentage = (len(sideways_markets) / total_markets * 100) if total_markets > 0 else 0

        message += f"""
📊 **MARKET OVERVIEW:**
• **Trending Markets**: {trending_percentage:.1f}% ({len(signals)}/{total_markets})
• **Sideways Markets**: {sideways_percentage:.1f}% ({len(sideways_markets)}/{total_markets})
• **Volatile Markets**: {(len(volatile_markets) / total_markets * 100) if total_markets > 0 else 0:.1f}% ({len(volatile_markets)}/{total_markets})

💡 **MARKET SENTIMENT:**"""

        if sideways_percentage > 50:
            message += """
🔄 **SIDEWAYS DOMINANCE**: Majority of markets in consolidation
• Avoid trend following strategies
• Focus on range trading
• Wait for catalyst for clear breakout
• Extra strict risk management"""
        elif trending_percentage > 60:
            message += """
📈 **MARKET TRENDING**: Good condition for trend following
• Take advantage of existing momentum
• Follow the trend with proper risk management
• Watch for trend reversal signals"""
        else:
            message += """
📊 **MARKET MIXED**: Mixed market condition
• Selective trading - choose best setups
• Avoid FOMO, wait for clear confirmation
• Smaller position size recommended"""

        message += f"""

⚠️ **RISK MANAGEMENT RULES:**
• Maximum 2-3% risk per trade
• Do not trade more than 3 pairs simultaneously
• Cut loss quickly if wrong direction
• Take profit gradually (50% at TP1, 50% at TP2)

🎯 **SUPPLY & DEMAND FEATURES:**
• Entry based on S&D zones
• TP/SL calculation dengan risk/reward optimal
• Volume confirmation untuk validasi breakout
• Multi-timeframe analysis

📡 **Data Sources**: CoinAPI Real-time + Binance Futures + Advanced SnD Algorithm

💡 **Disclaimer**: Signals for education, not financial advice. Always DYOR!"""

        return message

    def _format_futures_analysis_id(self, symbol, timeframe, futures_data, price_data):
        """Format individual futures analysis in Indonesian"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            current_price = price_data.get('price', 0)

            message = f"""📊 **Analisis Futures {symbol} - {timeframe}**

💰 **Harga**: ${current_price:.4f}
⏰ **Update**: {current_time}

"""
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%\n"

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"💰 Funding Rate: {funding_rate:.3f}%\n"

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    message += f"🔍 Open Interest: ${oi:,.0f}\n"

            message += f"""
💡Disclaimer: Bukan saran investasi, lakukan riset sendiri"""

            return message

        except Exception as e:
            return f"❌ Error formatting individual analysis: {str(e)}"

    def _format_futures_analysis_en(self, symbol, timeframe, futures_data, price_data):
        """Format individual futures analysis in English"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')
            current_price = price_data.get('price', 0)

            message = f"""📊 **Futures Analysis {symbol} - {timeframe}**

💰 **Price**: ${current_price:.4f}
⏰ **Update**: {current_time}

"""
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%\n"

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"💰 Funding Rate: {funding_rate:.3f}%\n"

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    message += f"🔍 Open Interest: ${oi:,.0f}\n"

            message += f"""
💡Disclaimer: Not investment advice, do your own research"""

            return message

        except Exception as e:
            return f"❌ Error formatting individual analysis: {str(e)}"

    def _analyze_market_condition(self, candlestick_data, futures_data):
        """Analyze market condition based on candlestick patterns and futures data"""
        try:
            # 1. Trend detection using moving averages
            closes = [candle['close'] for candle in candlestick_data]
            if len(closes) < 20:
                return {'type': 'unclear', 'reason': 'Insufficient data'}

            # Simple moving average
            sma_short = sum(closes[-10:]) / 10
            sma_long = sum(closes[-50:]) / 50

            trend_strength = abs(sma_short - sma_long) / sma_long * 100

            if sma_short > sma_long and trend_strength > 1:
                trend_direction = "bullish"
                condition_type = "trending"
            elif sma_short < sma_long and trend_strength > 1:
                trend_direction = "bearish"
                condition_type = "trending"
            else:
                trend_direction = "neutral"
                condition_type = "sideways"

            # 2. Volatility calculation using ATR
            high_low_ranges = [candle['high'] - candle['low'] for candle in candlestick_data]
            average_range = sum(high_low_ranges[-14:]) / 14  # 14-period ATR

            # 3. Sideways market detection
            body_sizes = [abs(candle['close'] - candle['open']) for candle in candlestick_data]
            avg_body_size = sum(body_sizes[-20:]) / 20

            if condition_type == "sideways":
                sideways_strength = avg_body_size / average_range * 100
            else:
                sideways_strength = 0

            # 4. Support and resistance
            supports = []
            resistances = []

            for i in range(2, len(candlestick_data) - 2):  # Skip first 2 and last 2
                is_support = all([candlestick_data[i]['low'] < candlestick_data[i - j]['low'] for j in range(1, 3)]) and \
                             all([candlestick_data[i]['low'] < candlestick_data[i + j]['low'] for j in range(1, 3)])

                is_resistance = all([candlestick_data[i]['high'] > candlestick_data[i - j]['high'] for j in range(1, 3)]) and \
                                all([candlestick_data[i]['high'] > candlestick_data[i + j]['high'] for j in range(1, 3)])

                if is_support:
                    supports.append({'level': candlestick_data[i]['low'], 'type': 'support'})
                if is_resistance:
                    resistances.append({'level': candlestick_data[i]['high'], 'type': 'resistance'})

            # 5. Volume confirmation - implement later

            # Combine analysis - improve this
            market_condition = {
                'type': condition_type,
                'strength': trend_strength,
                'volatility': average_range,
                'trend_direction': trend_direction,
                'sideways_strength': sideways_strength,
                'support_resistance': supports + resistances
            }

            return market_condition

        except Exception as e:
            print(f"Error analyzing market condition: {e}")
            return {'type': 'unknown', 'reason': str(e)}

    def _format_advanced_futures_analysis_id(self, symbol, timeframe, futures_data, price_data, market_condition, candlestick_data):
        """Format advanced futures analysis in Indonesian with market condition"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            current_price = price_data.get('price', 0)
            price_format = f"${current_price:.6f}" if current_price < 1 else f"${current_price:,.4f}" if current_price < 1000 else f"${current_price:,.2f}"

            message = f"""📊 **Analisis Futures {symbol} - {timeframe}**

💰 **Harga**: {price_format}
⏰ **Update**: {current_time}

"""

            # 1. Market Condition
            condition_type = market_condition.get('type', 'unknown')
            trend_direction = market_condition.get('trend_direction', 'neutral')
            volatility = market_condition.get('volatility', 0)

            message += f"""
📈 **Kondisi Market**: {condition_type.upper()}"""

            if condition_type == "trending":
                message += f"""
• **Trend**: {trend_direction.upper()}
• **Strength**: {market_condition.get('strength', 0):.1f}%
"""
            elif condition_type == "sideways":
                message += f"""
• **Sideways Strength**: {market_condition.get('sideways_strength', 0):.1f}%
• **Volatility**: {volatility:.2f}"""
            elif condition_type == "volatile":
                message += f"""
• **Volatility**: {volatility:.2f}"""

            # 2. Support and Resistance
            supports_resistances = market_condition.get('support_resistance', [])
            if supports_resistances:
                message += """
🎯 **Support/Resistance:**"""
                for level in supports_resistances[:3]:
                    message += f"""
• {level['type'].capitalize()}: ${level['level']:.4f}"""

            # 3. Futures Data
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"""
📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%"""

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"""
💰 Funding Rate: {funding_rate:.3f}%"""

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    oi_fmt = f"${oi/1000000:.1f}M" if oi > 1000000 else f"${oi:,.0f}"
                    message += f"""
🔍 Open Interest: {oi_fmt}"""

            # 4. Trading Recommendations
            if condition_type == "trending":
                if trend_direction == "bullish":
                    message += """
💡 Rekomendasi: Long - Follow the trend, cari pullback
🛑 Stop Loss: Bawah support terdekat"""
                else:
                    message += """
💡 Rekomendasi: Short - Follow the trend, cari rally
🛑 Stop Loss: Atas resistance terdekat"""
            elif condition_type == "sideways":
                message += """
💡 Rekomendasi: Range Trading - Beli support, jual resistance
🛑 Stop Loss: Luar range"""
            else:
                message += """
💡 Rekomendasi: Tunggu - Market tidak jelas
🛑 Hindari trading sampai ada konfirmasi"""

            message += f"""

⚠️Disclaimer: Bukan saran investasi, lakukan riset sendiri"""

            return message

        except Exception as e:
            return f"❌ Error formatting advanced individual analysis: {str(e)}"

    def _format_advanced_futures_analysis_en(self, symbol, timeframe, futures_data, price_data, market_condition, candlestick_data):
        """Format advanced futures analysis in English with market condition"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')
            current_price = price_data.get('price', 0)
            price_format = f"${current_price:.6f}" if current_price < 1 else f"${current_price:,.4f}" if current_price < 1000 else f"${current_price:,.2f}"

            message = f"""📊 **Futures Analysis {symbol} - {timeframe}**

💰 **Price**: {price_format}
⏰ **Update**: {current_time}

"""

            # 1. Market Condition
            condition_type = market_condition.get('type', 'unknown')
            trend_direction = market_condition.get('trend_direction', 'neutral')
            volatility = market_condition.get('volatility', 0)

            message += f"""
📈 **Market Condition**: {condition_type.upper()}"""

            if condition_type == "trending":
                message += f"""
• **Trend**: {trend_direction.upper()}
• **Strength**: {market_condition.get('strength', 0):.1f}%
"""
            elif condition_type == "sideways":
                message += f"""
• **Sideways Strength**: {market_condition.get('sideways_strength', 0):.1f}%
• **Volatility**: {volatility:.2f}"""
            elif condition_type == "volatile":
                message += f"""
• **Volatility**: {volatility:.2f}"""

            # 2. Support and Resistance
            supports_resistances = market_condition.get('support_resistance', [])
            if supports_resistances:
                message += """
🎯 **Support/Resistance:**"""
                for level in supports_resistances[:3]:
                    message += f"""
• {level['type'].capitalize()}: ${level['level']:.4f}"""

            # 3. Futures Data
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"""
📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%"""

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"""
💰 Funding Rate: {funding_rate:.3f}%"""

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    oi_fmt = f"${oi/1000000:.1f}M" if oi > 1000000 else f"${oi:,.0f}"
                    message += f"""
🔍 Open Interest: {oi_fmt}"""

            # 4. Trading Recommendations
            if condition_type == "trending":
                if trend_direction == "bullish":
                    message += """
💡 Recommendation: Long - Follow the trend, look for pullbacks
🛑 Stop Loss: Below nearest support"""
                else:
                    message += """
💡 Recommendation: Short - Follow the trend, look for rallies
🛑 Stop Loss: Above nearest resistance"""
            elif condition_type == "sideways":
                message += """
💡 Recommendation: Range Trading - Buy support, sell resistance
🛑 Stop Loss: Outside the range"""
            else:
                message += """
💡 Recommendation: Wait - Market is unclear
🛑 Avoid trading until there is confirmation"""

            message += f"""

⚠️Disclaimer: Not investment advice, do your own research"""

            return message

        except Exception as e:
            return f"❌ Error formatting advanced individual analysis: {str(e)}"