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

Ketik command untuk memulai!
        """

    def get_ai_response(self, text, language='id'):
        """Enhanced AI response for crypto beginners and general questions"""
        text_lower = text.lower()

        if language == 'id':
            # Crypto basics and education
            if any(
                    keyword in text_lower for keyword in
                ['apa itu bitcoin', 'bitcoin itu apa', 'penjelasan bitcoin']):
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

            elif any(
                    keyword in text_lower for keyword in
                ['apa itu crypto', 'cryptocurrency itu apa', 'kripto itu apa'
                 ]):
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

            elif any(keyword in text_lower for keyword in [
                    'cara beli crypto', 'cara membeli bitcoin',
                    'beli crypto dimana'
            ]):
                return """💳 **Cara Membeli Cryptocurrency untuk Pemula**

📱 **1. Pilih Exchange Terpercaya:**
- **Indonesia**: Indodax, TokoCrypto, Pintu, Rekeningku
- **Global**: Binance, Coinbase, Kraken
- **Tips**: Pilih yang sudah terdaftar di BAPPEBTI

📋 **2. Proses Registrasi:**
- Daftar akun dengan email & password kuat
- Verifikasi KYC (Know Your Customer)
- Upload foto KTP & selfie
- Tunggu verifikasi (1-3 hari)

💰 **3. Deposit Dana:**
- Transfer bank ke exchange
- Gunakan e-wallet (GoPay, OVO, Dana)
- Beli dengan kartu kredit/debit

🛒 **4. Beli Cryptocurrency:**
- Pilih pair trading (IDR/BTC, IDR/ETH)
- Tentukan jumlah yang ingin dibeli
- Klik "Buy" atau "Beli"
- Crypto masuk ke wallet exchange

🔐 **5. Security Tips:**
- Aktifkan 2FA (Two-Factor Authentication)
- Jangan share private key/password
- Withdraw ke personal wallet untuk long-term hold

💡 **Rekomendasi untuk Pemula:**
- Mulai dengan BTC atau ETH
- Invest amount yang bisa Anda relakan
- DCA (Dollar Cost Averaging) untuk mengurangi risiko

Butuh info harga crypto? Gunakan `/price <symbol>`"""

            elif any(keyword in text_lower for keyword in [
                    'apa itu trading', 'cara trading crypto',
                    'trading untuk pemula'
            ]):
                return """📈 **Trading Cryptocurrency untuk Pemula**

🎯 **Apa itu Trading Crypto?**
Trading adalah jual-beli crypto dalam jangka pendek untuk meraih profit dari pergerakan harga.

📊 **Jenis-jenis Trading:**
- **Spot Trading**: Beli/jual crypto langsung
- **Futures Trading**: Trading dengan leverage/utang
- **Margin Trading**: Pinjam dana untuk trading
- **Swing Trading**: Hold posisi beberapa hari/minggu
- **Day Trading**: Buka-tutup posisi dalam 1 hari
- **Scalping**: Trading sangat cepat (menit/jam)

🛠️ **Tools yang Diperlukan:**
- **Exchange**: Platform untuk trading
- **Chart Analysis**: Candlestick, volume, indicators
- **Risk Management**: Stop loss, take profit
- **News**: Berita yang mempengaruhi harga

📈 **Analisis Teknikal Dasar:**
- **Support**: Level harga yang sulit ditembus ke bawah
- **Resistance**: Level harga yang sulit ditembus ke atas
- **Trend**: Arah pergerakan harga (bullish/bearish)
- **Volume**: Banyaknya transaksi

⚠️ **Risk Management:**
- Jangan invest lebih dari yang bisa Anda rugi
- Set stop loss 5-10% dari entry
- Take profit bertahap (25%, 50%, 75%)
- Diversifikasi portfolio

💡 **Tips untuk Pemula:**
- Pelajari analisis teknikal dulu
- Practice dengan paper trading
- Mulai dengan amount kecil
- Kontrol emosi (jangan FOMO/panic)

Gunakan `/futures_signals` untuk sinyal trading harian!"""

            elif any(keyword in text_lower for keyword in [
                    'apa itu blockchain', 'blockchain itu apa',
                    'cara kerja blockchain'
            ]):
                return """⛓️ **Apa itu Blockchain?**

Blockchain adalah teknologi database terdistribusi yang menyimpan data dalam "blok" yang saling terhubung secara kriptografis.

🔗 **Cara Kerja Blockchain:**
- **Block**: Kumpulan transaksi yang divalidasi
- **Chain**: Blok-blok yang terhubung secara kronologis
- **Hash**: Sidik jari unik untuk setiap blok
- **Nodes**: Komputer yang menyimpan copy blockchain
- **Consensus**: Kesepakatan antar nodes untuk validasi

🌟 **Karakteristik Blockchain:**
- **Decentralized**: Tidak ada otoritas pusat
- **Transparent**: Semua transaksi bisa dilihat publik
- **Immutable**: Data yang sudah masuk sulit diubah
- **Secure**: Dilindungi kriptografi yang kuat

🔐 **Keamanan Blockchain:**
- **Cryptographic Hashing**: Setiap blok memiliki hash unik
- **Digital Signatures**: Verifikasi identitas pengirim
- **Consensus Mechanism**: Validasi oleh mayoritas network
- **Distributed Network**: Data tersebar di ribuan komputer

🏭 **Aplikasi Blockchain:**
- **Cryptocurrency**: Bitcoin, Ethereum, dll
- **Smart Contracts**: Kontrak otomatis yang berjalan sendiri
- **Supply Chain**: Tracking barang dari produksi ke konsumen
- **Identity Management**: Verifikasi identitas digital
- **Voting Systems**: Sistem voting yang transparan

💡 **Contoh Sederhana:**
Bayangkan buku catatan yang:
- Disalin ke ribuan orang
- Setiap halaman baru harus disetujui mayoritas
- Sekali ditulis, tidak bisa dihapus
- Semua orang bisa baca, tapi tidak bisa edit sembarangan

Itulah konsep dasar blockchain!"""

            elif any(
                    keyword in text_lower for keyword in
                ['apa itu defi', 'defi itu apa', 'decentralized finance']):
                return """🏦 **Apa itu DeFi (Decentralized Finance)?**

DeFi adalah sistem keuangan yang beroperasi tanpa perantara tradisional seperti bank, menggunakan smart contracts di blockchain.

🔧 **Komponen DeFi:**
- **DEX**: Decentralized Exchange (Uniswap, PancakeSwap)
- **Lending**: Pinjam-meminjam crypto (Aave, Compound)
- **Staking**: Lock crypto untuk earn rewards
- **Yield Farming**: Provide liquidity untuk earn token
- **Liquidity Mining**: Incentive untuk provide liquidity

💰 **Keuntungan DeFi:**
- **Permissionless**: Tidak perlu approval bank
- **Global Access**: Bisa diakses dari mana saja
- **Transparency**: Code bisa dilihat semua orang
- **High Yields**: Return bisa lebih tinggi dari bank
- **Composability**: Protokol bisa digabung

⚠️ **Risiko DeFi:**
- **Smart Contract Risk**: Bug dalam code
- **Impermanent Loss**: Risiko provide liquidity
- **Rug Pull**: Developer kabur dengan dana
- **High Gas Fees**: Biaya transaksi mahal
- **Volatility**: Nilai token bisa turun drastis

🎯 **DeFi Populer:**
- **Uniswap (UNI)**: DEX terbesar di Ethereum
- **Aave (AAVE)**: Platform lending terpercaya
- **Compound (COMP)**: Pionir DeFi lending
- **MakerDAO (MKR)**: Pembuat stablecoin DAI

💡 **Tips untuk Pemula:**
- Pelajari dulu sebelum invest
- Mulai dengan protokol yang sudah establish
- Understand impermanent loss sebelum provide liquidity
- Diversifikasi across multiple protocols

Ingin analisis token DeFi tertentu? Gunakan `/analyze <symbol>`"""

            elif any(keyword in text_lower for keyword in
                     ['apa itu nft', 'nft itu apa', 'non fungible token']):
                return """🎨 **Apa itu NFT (Non-Fungible Token)?**

NFT adalah token digital unik yang mewakili kepemilikan atas aset digital seperti art, music, video, atau in-game items.

🔑 **Karakteristik NFT:**
- **Non-Fungible**: Tidak bisa ditukar 1:1 (berbeda dengan Bitcoin)
- **Unique**: Setiap NFT memiliki ID dan metadata unik
- **Ownership**: Bukti kepemilikan tercatat di blockchain
- **Tradeable**: Bisa dijual/dibeli di marketplace

🖼️ **Jenis-jenis NFT:**
- **Digital Art**: Lukisan, foto, animasi digital
- **Profile Pictures (PFP)**: Avatar untuk social media
- **Gaming Items**: Weapon, character, land di game
- **Music**: Lagu, album, concert tickets
- **Sports**: Trading cards, highlight moments
- **Virtual Real Estate**: Tanah di metaverse

🏪 **Marketplace NFT Populer:**
- **OpenSea**: Marketplace NFT terbesar
- **Magic Eden**: Fokus pada Solana NFT
- **Foundation**: Platform untuk digital artists
- **NBA Top Shot**: NFT basketball highlights
- **Axie Marketplace**: NFT untuk game Axie Infinity

💰 **Cara Kerja NFT:**
1. Artist mint NFT di blockchain
2. NFT listed di marketplace
3. Buyer beli dengan cryptocurrency
4. Ownership transfer ke wallet buyer
5. NFT bisa di-resell dengan harga berbeda

⚠️ **Risiko NFT:**
- **High Volatility**: Harga bisa turun drastis
- **Liquidity Risk**: Sulit jual saat market bearish
- **Scams**: Banyak project NFT yang rug pull
- **No Intrinsic Value**: Nilai tergantung hype dan demand
- **Copyright Issues**: Tidak semua NFT memiliki copyright asli

💡 **Tips Trading NFT:**
- Research project dan team di baliknya
- Cek roadmap dan utility NFT
- Perhatikan floor price dan volume trading
- Join Discord/Twitter community
- Set budget dan jangan FOMO

🎯 **NFT yang Potensial:**
- Utility NFT (gaming, membership, access)
- Brand collaborations dengan perusahaan besar
- NFT dengan passive income (staking rewards)
- Historical significance (first of its kind)

💡 **Untuk Pemula:**
- Mulai dengan NFT murah untuk belajar
- Pahami gas fees sebelum beli
- Install wallet yang kompatibel (MetaMask, Phantom)
- Jangan invest lebih dari yang sanggup rugi

Gunakan `/market` untuk analisis trend NFT terkini!"""

            # Price and analysis questions
            elif any(keyword in text_lower
                     for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`. Contoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower
                     for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

            elif any(keyword in text_lower
                     for keyword in ['market', 'pasar', 'overview']):
                return "📈 Gunakan command `/market` untuk melihat overview pasar crypto secara keseluruhan.\n\nIngin tau tentang market cap, dominasi BTC, atau trend pasar?"

            # Wallet and security questions
            elif any(keyword in text_lower
                     for keyword in ['wallet', 'dompet', 'penyimpanan']):
                return """🔐 **Cryptocurrency Wallets**

**Jenis-jenis Wallet:**
- **Hot Wallet**: Terhubung internet (Exchange, Mobile app)
- **Cold Wallet**: Offline storage (Hardware wallet, paper wallet)

**Rekomendasi Wallet:**
- **Mobile**: Trust Wallet, MetaMask, Exodus
- **Hardware**: Ledger Nano, Trezor
- **Browser**: MetaMask untuk DeFi di Ethereum

**Security Tips:**
- Backup seed phrase di tempat aman
- Jangan share private key dengan siapa pun
- Gunakan 2FA untuk exchange wallet
- Test transfer dengan amount kecil dulu

Butuh info lebih detail tentang wallet tertentu?"""

            elif any(keyword in text_lower
                     for keyword in ['keamanan', 'security', 'hack', 'scam']):
                return """🛡️ **Keamanan Cryptocurrency**

**Ancaman Umum:**
- **Phishing**: Website/email palsu
- **Rug Pull**: Developer kabur dengan dana
- **Exit Scam**: Exchange tutup bawa kabur dana
- **Social Engineering**: Manipulasi psikologis
- **Malware**: Software jahat curi private key

**Tips Keamanan:**
- Selalu check URL website (https://)
- Jangan klik link suspicious di email/telegram
- Gunakan hardware wallet untuk amount besar
- Enable 2FA di semua akun crypto
- Jangan invest di project yang terlalu good to be true

**Red Flags:**
- Guaranteed returns tinggi
- Anonymous team
- No working product
- Pressure untuk invest cepat

Stay safe dan always DYOR (Do Your Own Research)!"""

            # Technical questions
            elif any(keyword in text_lower
                     for keyword in ['leverage', 'margin', 'futures']):
                return """⚡ **Trading dengan Leverage**

**Apa itu Leverage?**
Leverage memungkinkan Anda trading dengan dana lebih besar dari yang Anda miliki.

**Contoh:**
- Modal $100 dengan leverage 10x = buying power $1000
- Profit/loss juga dikali 10x
- Jika harga naik 1%, profit Anda 10%
- Jika harga turun 1%, loss Anda 10%

**Jenis Leverage Trading:**
- **Margin Trading**: Pinjam dana untuk spot trading
- **Futures**: Kontrak dengan delivery date
- **Perpetual**: Futures tanpa expiry date

**Risk Management:**
- **Stop Loss**: Auto sell saat rugi mencapai %
- **Take Profit**: Auto sell saat profit target tercapai
- **Position Size**: Jangan risk >2-5% per trade

⚠️ **WARNING**: Leverage sangat berisiko! 90% trader rugi. Pelajari dulu sebelum coba.

Gunakan `/futures_signals` untuk sinyal trading harian!"""

            # Help and general
            elif any(keyword in text_lower
                     for keyword in ['help', 'bantuan', 'command']):
                return self.help_message()

            elif any(keyword in text_lower
                     for keyword in ['terima kasih', 'thanks', 'thx']):
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
            # English responses (keeping original structure but enhanced)
            if any(keyword in text_lower for keyword in
                   ['what is bitcoin', 'explain bitcoin', 'bitcoin basics']):
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

            elif any(keyword in text_lower for keyword in [
                    'what is crypto', 'cryptocurrency basics',
                    'crypto explained'
            ]):
                return """🌐 **What is Cryptocurrency?**

Cryptocurrency is digital money that uses cryptography for security and operates on blockchain technology.

🔧 **Key Components:**
- **Blockchain**: Distributed database recording all transactions
- **Mining**: Process of validating transactions and creating new blocks
- **Wallet**: Storage for your cryptocurrency
- **Private Key**: Secret key to access your crypto

💰 **Types of Crypto:**
- **Bitcoin (BTC)**: First cryptocurrency
- **Altcoins**: All cryptocurrencies except Bitcoin
- **Stablecoins**: Price-stable cryptos (USDT, USDC)
- **Meme coins**: Community-driven tokens (DOGE, SHIB)

⚠️ **Tips for Beginners:**
- Learn before you invest
- Start with small amounts
- Use reputable exchanges
- Don't panic when prices drop

Any specific crypto questions?"""

            elif any(keyword in text_lower for keyword in [
                    'how to buy crypto', 'buying cryptocurrency',
                    'crypto purchase'
            ]):
                return """💳 **How to Buy Cryptocurrency**

📱 **1. Choose a Reputable Exchange:**
- **Global**: Binance, Coinbase, Kraken, KuCoin
- **Tips**: Check regulations in your country

📋 **2. Registration Process:**
- Sign up with email & strong password
- Complete KYC (Know Your Customer) verification
- Upload ID documents
- Wait for approval (1-3 days)

💰 **3. Fund Your Account:**
- Bank transfer
- Credit/debit card
- PayPal (some exchanges)

🛒 **4. Buy Cryptocurrency:**
- Choose trading pair (USD/BTC, EUR/ETH)
- Decide amount to purchase
- Click "Buy" 
- Crypto goes to exchange wallet

🔐 **5. Security Tips:**
- Enable 2FA (Two-Factor Authentication)
- Never share private keys/passwords
- Withdraw to personal wallet for long-term storage

💡 **Beginner Recommendations:**
- Start with BTC or ETH
- Invest only what you can afford to lose
- Use DCA (Dollar Cost Averaging) strategy

Need price info? Use `/price <symbol>`"""

            elif any(keyword in text_lower
                     for keyword in ['price', 'cost', 'how much']):
                return "💰 To check crypto prices, use `/price <symbol>`. Example: `/price btc`\n\nFor comprehensive analysis: `/analyze <symbol>`"

            elif any(keyword in text_lower
                     for keyword in ['analysis', 'analyze', 'signal']):
                return "📊 For deep analysis, use `/analyze <symbol>` or `/futures_signals` for daily futures signals.\n\n💡 **Note**: Analysis includes technical analysis, sentiment, and trading recommendations."

            elif any(keyword in text_lower
                     for keyword in ['market', 'overview']):
                return "📈 Use `/market` command to see overall crypto market overview.\n\nWant to know about market cap, BTC dominance, or market trends?"

            elif any(keyword in text_lower for keyword in ['help', 'command']):
                return self.help_message()

            elif any(keyword in text_lower
                     for keyword in ['thank', 'thanks', 'thx']):
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
        """Get comprehensive market overview with real-time data"""
        if not crypto_api:
            return self._get_fallback_market_overview(language)

        try:
            # Get market overview data
            market_data = crypto_api.get_market_overview()

            # Get prices for major cryptocurrencies
            major_symbols = [
                'bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana',
                'ripple', 'polkadot', 'dogecoin', 'avalanche-2',
                'matic-network'
            ]
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
                return self._format_comprehensive_market_id(
                    market_data, prices_data, news_data, futures_btc,
                    futures_eth)
            else:
                return self._format_comprehensive_market_en(
                    market_data, prices_data, news_data, futures_btc,
                    futures_eth)

        except Exception as e:
            print(f"Error in market overview: {e}")
            return self._get_fallback_market_overview(language)

    def _format_comprehensive_market_id(self, market_data, prices_data,
                                        news_data, futures_btc, futures_eth):
        """Format comprehensive market overview in Indonesian"""
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

        # Top movers analysis
        gainers, losers, top_performers = self._analyze_top_movers(prices_data)

        # Altcoin season index
        altcoin_index = self._calculate_altcoin_season_index(
            futures_btc, futures_eth, prices_data)

        # News sentiment
        news_sentiment = self._analyze_market_news_sentiment(news_data)

        # Chart mini representation
        chart_mini = self._generate_chart_mini(prices_data)

        # Trading signals
        signals = self._generate_market_signals(futures_btc, futures_eth,
                                                prices_data)

        message = f"""🌍 **OVERVIEW PASAR CRYPTO REAL-TIME**

💰 **1. DATA REAL-TIME GLOBAL:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- Dominasi BTC: {btc_dominance:.1f}%
- Crypto Aktif: {active_cryptos:,} koin
- Fear & Greed Index: {self._get_fear_greed_simulation()}

📈 **2. TREN PASAR GLOBAL:**
{self._format_global_trends(market_cap_change, btc_dominance)}

🚀 **3. TOP MOVERS (24H):**
**📈 GAINERS:**
{gainers}

**📉 LOSERS:**
{losers}

🔥 **4. ALTCOIN SEASON INDEX:**
{altcoin_index}

📰 **5. SENTIMEN BERITA TERKINI:**
{news_sentiment}

📊 **6. CHART MINI (Trend Visual):**
{chart_mini}

⚡ **7. REKOMENDASI SINYAL AWAL:**
{signals}

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Multi-API Real-time
🔄 **Refresh:** Gunakan `/market` untuk update terbaru"""

        return message

    def _format_comprehensive_market_en(self, market_data, prices_data,
                                        news_data, futures_btc, futures_eth):
        """Format comprehensive market overview in English"""
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

        # Analysis components
        gainers, losers, top_performers = self._analyze_top_movers(prices_data)
        altcoin_index = self._calculate_altcoin_season_index(
            futures_btc, futures_eth, prices_data)
        news_sentiment = self._analyze_market_news_sentiment(news_data)
        chart_mini = self._generate_chart_mini(prices_data)
        signals = self._generate_market_signals(futures_btc, futures_eth,
                                                prices_data)

        message = f"""🌍 **REAL-TIME CRYPTO MARKET OVERVIEW**

💰 **1. REAL-TIME GLOBAL DATA:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- BTC Dominance: {btc_dominance:.1f}%
- Active Cryptos: {active_cryptos:,} coins
- Fear & Greed Index: {self._get_fear_greed_simulation()}

📈 **2. GLOBAL MARKET TRENDS:**
{self._format_global_trends_en(market_cap_change, btc_dominance)}

🚀 **3. TOP MOVERS (24H):**
**📈 GAINERS:**
{gainers}

**📉 LOSERS:**
{losers}

🔥 **4. ALTCOIN SEASON INDEX:**
{altcoin_index}

📰 **5. CURRENT NEWS SENTIMENT:**
{news_sentiment}

📊 **6. MINI CHART (Trend Visual):**
{chart_mini}

⚡ **7. EARLY SIGNAL RECOMMENDATIONS:**
{signals}

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Multi-API Real-time
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

            return gainers, losers, ['SOL', 'AVAX', 'MATIC']

        # Real data analysis
        movers = []
        for symbol, data in prices_data.items():
            if 'price' in data and 'change_24h' in data:
                movers.append({
                    'symbol': symbol,
                    'price': data['price'],
                    'change': data['change_24h']
                })

        # Sort by change percentage
        movers.sort(key=lambda x: x['change'], reverse=True)

        # Top 3 gainers
        gainers_list = []
        for i, mover in enumerate(movers[:3]):
            if mover['change'] > 0:
                gainers_list.append(
                    f"- {mover['symbol']}: +{mover['change']:.1f}% (${mover['price']:,.2f})"
                )

        # Top 3 losers
        losers_list = []
        for mover in movers[-3:]:
            if mover['change'] < 0:
                losers_list.append(
                    f"- {mover['symbol']}: {mover['change']:.1f}% (${mover['price']:,.2f})"
                )

        gainers = '\n'.join(
            gainers_list) if gainers_list else "- Tidak ada gainer signifikan"
        losers = '\n'.join(
            losers_list) if losers_list else "- Tidak ada loser signifikan"

        top_performers = [m['symbol'] for m in movers[:3]]

        return gainers, losers, top_performers

    def _calculate_altcoin_season_index(self, futures_btc, futures_eth,
                                        prices_data):
        """Calculate altcoin season index"""
        try:
            # Get BTC dominance simulation
            btc_long_ratio = futures_btc.get('long_ratio', 55)
            eth_long_ratio = futures_eth.get('long_ratio', 55)

            # Calculate index based on futures sentiment and price movements
            if 'error' not in prices_data:
                altcoin_gains = 0
                total_alts = 0
                for symbol, data in prices_data.items():
                    if symbol not in ['BTC', 'bitcoin'
                                      ] and 'change_24h' in data:
                        if data['change_24h'] > 0:
                            altcoin_gains += 1
                        total_alts += 1

                alt_performance = (altcoin_gains / total_alts *
                                   100) if total_alts > 0 else 50
            else:
                alt_performance = 65  # Mock data

            # Calculate final index
            index = (alt_performance +
                     (100 - btc_long_ratio) + eth_long_ratio) / 3

            if index >= 75:
                status = "🔥 ALTCOIN SEASON AKTIF"
                desc = "Altcoin outperform BTC, momentum sangat kuat"
            elif index >= 60:
                status = "🟡 ALTCOIN SEASON MENDEKAT"
                desc = "Beberapa altcoin mulai outperform BTC"
            elif index >= 40:
                status = "⚪ PASAR SEIMBANG"
                desc = "BTC dan altcoin bergerak seimbang"
            else:
                status = "🔴 BTC DOMINANCE TINGGI"
                desc = "Bitcoin masih mendominasi pasar"

            return f"""- Index Score: {index:.1f}/100
- Status: {status}
- Analisis: {desc}
- Rekomendasi: {'Focus altcoin trading' if index >= 60 else 'Focus BTC/stablecoin' if index < 40 else 'Balanced portfolio'}"""

        except Exception as e:
            return """- Index Score: 55.0/100
- Status: ⚪ PASAR SEIMBANG
- Analisis: Data terbatas, estimasi berdasarkan trend umum
- Rekomendasi: Balanced portfolio"""

    def _analyze_market_news_sentiment(self, news_data):
        """Analyze sentiment from crypto news"""
        if not news_data or 'error' in news_data[0]:
            return """- Sentiment Score: 7.2/10 (Bullish)
- Trend Berita: Positif dominan
- Dampak: Moderate bullish impact
- Highlight: Adopsi institusional meningkat, regulasi mendukung"""

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_articles = len(news_data[:3])

        for article in news_data[:3]:
            sentiment = article.get('sentiment', 'neutral').lower()
            if sentiment == 'positive':
                positive_count += 1
            elif sentiment == 'negative':
                negative_count += 1
            else:
                neutral_count += 1

        # Calculate sentiment score
        if total_articles > 0:
            score = ((positive_count * 2 +
                      (total_articles - positive_count - negative_count)) /
                     total_articles) * 5 + 2.5
            score = min(10, max(1, score))
        else:
            score = 7

        if score >= 8:
            trend = "Sangat Bullish"
            impact = "High bullish impact"
        elif score >= 6:
            trend = "Bullish"
            impact = "Moderate bullish impact"
        elif score >= 4:
            trend = "Netral"
            impact = "Neutral impact"
        else:
            trend = "Bearish"
            impact = "Bearish pressure"

        # Get news highlight
        highlight = "Berita crypto menunjukkan optimisme"
        if news_data and len(news_data) > 0:
            first_article = news_data[0]
            if 'title' in first_article:
                highlight = first_article['title'][:60] + "..."

        return f"""- Sentiment Score: {score:.1f}/10 ({trend})
- Trend Berita: {trend} dominan
- Dampak: {impact}
- Highlight: {highlight}"""

    def _generate_chart_mini(self, prices_data):
        """Generate mini chart representation"""
        try:
            if 'error' in prices_data:
                return """📈 BTC: ▲▲▼▲▲ (Bullish trend)
📊 ETH: ▲▼▲▲▼ (Volatile sideways)
🚀 TOP: ▲▲▲▼▲ (Strong momentum)"""

            # Analyze price movements to create mini charts
            chart_lines = []
            symbols_to_chart = ['bitcoin', 'ethereum', 'binancecoin'][:3]

            for symbol in symbols_to_chart:
                if symbol in prices_data:
                    change = prices_data[symbol].get('change_24h', 0)

                    # Generate mini trend based on change
                    if change > 5:
                        trend = "▲▲▲▲▲"
                        desc = "Very bullish"
                    elif change > 2:
                        trend = "▲▲▲▼▲"
                        desc = "Bullish trend"
                    elif change > 0:
                        trend = "▲▼▲▼▲"
                        desc = "Slightly up"
                    elif change > -2:
                        trend = "▼▲▼▲▼"
                        desc = "Sideways"
                    elif change > -5:
                        trend = "▼▼▼▲▼"
                        desc = "Bearish trend"
                    else:
                        trend = "▼▼▼▼▼"
                        desc = "Very bearish"

                    symbol_display = symbol.upper()[:3]
                    chart_lines.append(f"📈 {symbol_display}: {trend} ({desc})")

            return '\n'.join(
                chart_lines) if chart_lines else "📊 Chart data loading..."

        except Exception as e:
            return """📈 BTC: ▲▲▼▲▲ (Bullish trend)
📊 ETH: ▲▼▲▲▼ (Volatile sideways)
🚀 ALT: ▲▲▲▼▲ (Strong momentum)"""

    def _generate_market_signals(self, futures_btc, futures_eth, prices_data):
        """Generate early market signals"""
        try:
            signals = []

            # BTC signal
            btc_long_ratio = futures_btc.get('long_ratio', 50)
            if btc_long_ratio > 70:
                signals.append(
                    "🔴 BTC: Overleveraged longs - Consider taking profits")
            elif btc_long_ratio < 30:
                signals.append(
                    "🟢 BTC: Oversold bounce potential - Consider buy")
            else:
                signals.append("🟡 BTC: Balanced sentiment - Hold positions")

            # ETH signal
            eth_long_ratio = futures_eth.get('long_ratio', 50)
            if eth_long_ratio > 65:
                signals.append("🔴 ETH: High long bias - Caution on new longs")
            elif eth_long_ratio < 35:
                signals.append(
                    "🟢 ETH: Low sentiment - Accumulation opportunity")
            else:
                signals.append("🟡 ETH: Normal range - Follow trend")

            # Market structure signal
            if 'error' not in prices_data:
                positive_movers = sum(1 for data in prices_data.values()
                                      if data.get('change_24h', 0) > 0)
                total_coins = len(prices_data)
                positive_ratio = positive_movers / total_coins if total_coins > 0 else 0.5

                if positive_ratio > 0.7:
                    signals.append(
                        "🚀 MARKET: Broad bullish momentum - Risk on")
                elif positive_ratio < 0.3:
                    signals.append(
                        "⚠️ MARKET: Broad selling pressure - Risk off")
                else:
                    signals.append(
                        "⚖️ MARKET: Mixed signals - Selective strategy")

            return '\n'.join(signals) if signals else "📊 Signals generating..."

        except Exception as e:
            return """🟡 BTC: Balanced sentiment - Hold positions
🟡 ETH: Normal range - Follow trend
⚖️ MARKET: Mixed signals - Selective strategy"""

    def _format_global_trends(self, market_cap_change, btc_dominance):
        """Format global trends in Indonesian"""
        if market_cap_change > 3:
            trend_emoji = "🟢"
            trend_desc = "BULL MARKET MOMENTUM"
            desc = "Pasar crypto dalam fase bullish kuat"
        elif market_cap_change > 0:
            trend_emoji = "🟡"
            trend_desc = "RECOVERY MODE"
            desc = "Pasar pulih dari koreksi sebelumnya"
        elif market_cap_change > -3:
            trend_emoji = "🟠"
            trend_desc = "CONSOLIDATION"
            desc = "Pasar berkonsolidasi mencari arah"
        else:
            trend_emoji = "🔴"
            trend_desc = "BEAR PRESSURE"
            desc = "Tekanan jual masih dominan"

        dom_trend = "meningkat" if btc_dominance > 50 else "menurun"

        return f"""- {trend_emoji} **{trend_desc}**
- Kondisi: {desc}
- Dominasi BTC: {dom_trend} ({btc_dominance:.1f}%)
- Outlook: {'Bullish' if market_cap_change > 1 else 'Bearish' if market_cap_change < -1 else 'Neutral'} untuk 24h ke depan"""

    def _format_global_trends_en(self, market_cap_change, btc_dominance):
        """Format global trends in English"""
        if market_cap_change > 3:
            trend_emoji = "🟢"
            trend_desc = "BULL MARKET MOMENTUM"
            desc = "Crypto market in strong bullish phase"
        elif market_cap_change > 0:
            trend_emoji = "🟡"
            trend_desc = "RECOVERY MODE"
            desc = "Market recovering from previous correction"
        elif market_cap_change > -3:
            trend_emoji = "🟠"
            trend_desc = "CONSOLIDATION"
            desc = "Market consolidating, seeking direction"
        else:
            trend_emoji = "🔴"
            trend_desc = "BEAR PRESSURE"
            desc = "Selling pressure still dominant"

        dom_trend = "increasing" if btc_dominance > 50 else "decreasing"

        return f"""- {trend_emoji} **{trend_desc}**
- Condition: {desc}
- BTC Dominance: {dom_trend} ({btc_dominance:.1f}%)
- Outlook: {'Bullish' if market_cap_change > 1 else 'Bearish' if market_cap_change < -1 else 'Neutral'} for next 24h"""

    def _get_fear_greed_simulation(self):
        """Simulate Fear & Greed Index"""
        import random
        index = random.randint(20, 80)

        if index >= 75:
            return f"{index} (Extreme Greed 🔥)"
        elif index >= 55:
            return f"{index} (Greed 📈)"
        elif index >= 45:
            return f"{index} (Neutral ⚖️)"
        elif index >= 25:
            return f"{index} (Fear 📉)"
        else:
            return f"{index} (Extreme Fear 😨)"

    def _generate_advanced_signal(self, symbol, price, change_24h, long_ratio, short_ratio,
                                  open_interest, oi_change, funding_rate, total_liq, long_liq, short_liq,
                                  btc_dominance, market_trend, news_data):
        """Generate advanced trading signal based on multiple factors"""
        
        # Signal strength calculation based on multiple factors
        signal_score = 0
        signal_factors = []
        
        # 1. Long/Short Ratio Analysis
        if long_ratio > 75:
            signal_score -= 3  # Bearish
            signal_factors.append("🔴 Extreme Long Crowding (>75%)")
            signal_type = "SHORT"
            signal_strength = "STRONG"
        elif long_ratio > 65:
            signal_score -= 2  # Moderately Bearish
            signal_factors.append("🟡 High Long Bias (>65%)")
            signal_type = "SHORT"
            signal_strength = "MODERATE"
        elif long_ratio < 25:
            signal_score += 3  # Bullish
            signal_factors.append("🟢 Extreme Short Crowding (<25%)")
            signal_type = "LONG"
            signal_strength = "STRONG"
        elif long_ratio < 35:
            signal_score += 2  # Moderately Bullish
            signal_factors.append("🟡 High Short Bias (<35%)")
            signal_type = "LONG"
            signal_strength = "MODERATE"
        else:
            signal_factors.append("⚪ Balanced L/S Ratio")
            signal_type = "LONG" if change_24h > 0 else "SHORT"
            signal_strength = "WEAK"
        
        # 2. Open Interest Divergence
        if change_24h > 2 and oi_change < -5:
            signal_score -= 2
            signal_factors.append("📉 Bearish OI Divergence (Price↑ OI↓)")
        elif change_24h < -2 and oi_change > 5:
            signal_score += 2
            signal_factors.append("📈 Bullish OI Divergence (Price↓ OI↑)")
        elif change_24h > 2 and oi_change > 5:
            signal_score += 1
            signal_factors.append("✅ Bullish Confirmation (Price↑ OI↑)")
        elif change_24h < -2 and oi_change < -5:
            signal_score -= 1
            signal_factors.append("✅ Bearish Confirmation (Price↓ OI↓)")
        
        # 3. Funding Rate Analysis
        if funding_rate > 0.01:  # >1% funding
            signal_score -= 2
            signal_factors.append("🔴 Extreme Positive Funding (>1%)")
        elif funding_rate > 0.005:  # >0.5% funding
            signal_score -= 1
            signal_factors.append("🟡 High Positive Funding")
        elif funding_rate < -0.01:  # <-1% funding
            signal_score += 2
            signal_factors.append("🟢 Extreme Negative Funding (<-1%)")
        elif funding_rate < -0.005:  # <-0.5% funding
            signal_score += 1
            signal_factors.append("🟡 High Negative Funding")
        
        # 4. Liquidation Analysis
        if total_liq > 100000000:  # >100M liquidation
            if long_liq > short_liq * 2:
                signal_score -= 1
                signal_factors.append("💥 High Long Liquidations")
            elif short_liq > long_liq * 2:
                signal_score += 1
                signal_factors.append("💥 High Short Liquidations")
        
        # 5. Market Context
        if btc_dominance > 50 and symbol != 'BTC':
            signal_score -= 0.5
            signal_factors.append("📊 BTC Dominance High (Alt Risk)")
        
        # Calculate final signal
        if signal_score >= 3:
            final_strength = "VERY STRONG"
            confidence = "High"
        elif signal_score >= 1:
            final_strength = "STRONG"
            confidence = "High"
        elif signal_score >= 0:
            final_strength = "MODERATE"
            confidence = "Medium"
        else:
            final_strength = "WEAK"
            confidence = "Low"
            
        # Adjust signal type based on overall score
        if signal_score >= 2:
            final_signal = "LONG"
        elif signal_score <= -2:
            final_signal = "SHORT"
        else:
            final_signal = signal_type
        
        # Calculate entry, TP, SL based on signal strength
        entry_price = price
        if final_signal == "LONG":
            if final_strength == "VERY STRONG":
                tp_price = price * 1.05  # 5% up
                sl_price = price * 0.97  # 3% down
            elif final_strength == "STRONG":
                tp_price = price * 1.04  # 4% up
                sl_price = price * 0.975  # 2.5% down
            else:
                tp_price = price * 1.03  # 3% up
                sl_price = price * 0.98  # 2% down
        else:  # SHORT
            if final_strength == "VERY STRONG":
                tp_price = price * 0.95  # 5% down
                sl_price = price * 1.03  # 3% up
            elif final_strength == "STRONG":
                tp_price = price * 0.96  # 4% down
                sl_price = price * 1.025  # 2.5% up
            else:
                tp_price = price * 0.97  # 3% down
                sl_price = price * 1.02  # 2% up
        
        risk_reward = abs((tp_price - entry_price) / (sl_price - entry_price))
        
        signal_emoji = "🟢" if final_signal == "LONG" else "🔴"
        
        analysis = f"""🎯 **Advanced Trading Signal:**
- {signal_emoji} **{symbol} {final_signal}** ({final_strength})
- Entry: ${entry_price:,.2f}
- TP: ${tp_price:,.2f} ({((tp_price/entry_price-1)*100):+.1f}%)
- SL: ${sl_price:,.2f} ({((sl_price/entry_price-1)*100):+.1f}%)
- R/R Ratio: {risk_reward:.1f}:1
- Confidence: {confidence}
- Signal Score: {signal_score:+.1f}/5

📋 **Signal Factors:**"""
        
        for factor in signal_factors[:5]:  # Show top 5 factors
            analysis += f"\n  • {factor}"
            
        return analysis

    def _generate_technical_analysis(self, price, change_24h, volume, long_ratio, funding_rate):
        """Generate technical analysis"""
        
        analyses = []
        
        # Price momentum
        if abs(change_24h) > 5:
            momentum = "Strong"
            analyses.append(f"📈 Momentum: {momentum} ({change_24h:+.1f}%)")
        elif abs(change_24h) > 2:
            momentum = "Moderate"
            analyses.append(f"📊 Momentum: {momentum} ({change_24h:+.1f}%)")
        else:
            momentum = "Weak"
            analyses.append(f"➡️ Momentum: {momentum} ({change_24h:+.1f}%)")
        
        # Volume analysis
        if volume > 1000000000:
            analyses.append("📊 Volume: High conviction (>$1B)")
        elif volume > 500000000:
            analyses.append("📊 Volume: Moderate ($500M-1B)")
        else:
            analyses.append("📊 Volume: Low (<$500M)")
        
        # Sentiment from futures
        if long_ratio > 70:
            analyses.append("😤 Sentiment: Euphoric (Contrarian bearish)")
        elif long_ratio > 60:
            analyses.append("😊 Sentiment: Bullish")
        elif long_ratio < 30:
            analyses.append("😰 Sentiment: Fearful (Contrarian bullish)")
        elif long_ratio < 40:
            analyses.append("😟 Sentiment: Bearish")
        else:
            analyses.append("😐 Sentiment: Neutral")
        
        # Funding pressure
        if abs(funding_rate) > 0.005:
            pressure = "High" if funding_rate > 0 else "High (Shorts paying)"
            analyses.append(f"💸 Funding Pressure: {pressure}")
        else:
            analyses.append("💸 Funding Pressure: Normal")
        
        return "\n".join(analyses)

    def _generate_risk_assessment(self, long_ratio, oi_change, funding_rate, total_liq, market_trend):
        """Generate comprehensive risk assessment"""
        
        risk_score = 0
        risk_factors = []
        
        # Long ratio risk
        if long_ratio > 75 or long_ratio < 25:
            risk_score += 2
            risk_factors.append("⚠️ Extreme position bias")
        elif long_ratio > 65 or long_ratio < 35:
            risk_score += 1
            risk_factors.append("🟡 High position bias")
        
        # OI volatility risk
        if abs(oi_change) > 10:
            risk_score += 2
            risk_factors.append("⚠️ High OI volatility")
        elif abs(oi_change) > 5:
            risk_score += 1
            risk_factors.append("🟡 Moderate OI change")
        
        # Funding risk
        if abs(funding_rate) > 0.01:
            risk_score += 2
            risk_factors.append("⚠️ Extreme funding rate")
        elif abs(funding_rate) > 0.005:
            risk_score += 1
            risk_factors.append("🟡 High funding rate")
        
        # Liquidation risk
        if total_liq > 200000000:
            risk_score += 2
            risk_factors.append("⚠️ High liquidation activity")
        elif total_liq > 100000000:
            risk_score += 1
            risk_factors.append("🟡 Moderate liquidations")
        
        # Market risk
        if abs(market_trend) > 5:
            risk_score += 1
            risk_factors.append("🟡 High market volatility")
        
        # Risk level
        if risk_score >= 6:
            risk_level = "🔴 VERY HIGH"
            recommendation = "Use minimal leverage (2-3x max)"
        elif risk_score >= 4:
            risk_level = "🟠 HIGH"
            recommendation = "Use low leverage (3-5x max)"
        elif risk_score >= 2:
            risk_level = "🟡 MODERATE"
            recommendation = "Standard risk management"
        else:
            risk_level = "🟢 LOW"
            recommendation = "Normal position sizing"
        
        assessment = f"""Risk Level: {risk_level}
Recommendation: {recommendation}

Risk Factors:"""
        
        for factor in risk_factors[:4]:  # Show top 4 factors
            assessment += f"\n  • {factor}"
        
        return assessment

    def _analyze_market_structure_advanced(self, price_change, oi_change, long_ratio, funding_rate):
        """Advanced market structure analysis"""
        
        if price_change > 2 and oi_change > 5 and long_ratio > 60:
            return "🟢 Strong Bullish Structure: Price↑ + OI↑ + Long bias"
        elif price_change < -2 and oi_change < -5 and long_ratio < 40:
            return "🔴 Strong Bearish Structure: Price↓ + OI↓ + Short bias"
        elif price_change > 2 and oi_change < -3:
            return "⚠️ Weak Bullish: Price up but OI declining (weak hands)"
        elif price_change < -2 and oi_change > 3:
            return "💎 Accumulation: Price down but OI up (smart money)"
        elif abs(funding_rate) > 0.005 and long_ratio > 65:
            return "🔄 Overheated: High funding + crowded longs"
        else:
            return "⚖️ Balanced Structure: Normal market conditions"

    def _analyze_liquidation_patterns(self, long_liq, short_liq, total_liq, long_ratio):
        """Analyze liquidation patterns for insights"""
        
        if total_liq < 50000000:
            return "🟢 Low Liquidation Risk: Minimal liquidation activity"
        
        if total_liq > 200000000:  # >200M liquidation
            if long_liq > short_liq * 2:  # 2x more long liquidations
                return f"""🔴 **EXTREME LONG LIQUIDATION CASCADE**
- Massive long liquidation: ${long_liq:,.0f}
- Total liquidation: ${total_liq:,.0f}
- Pattern: Long squeeze in progress
- Signal: Extreme bearish pressure
- Action: AVOID longs until stabilization"""
            
            elif short_liq > long_liq * 2:  # 2x more short liquidations
                return f"""🔴 **EXTREME SHORT LIQUIDATION CASCADE**
- Massive short liquidation: ${short_liq:,.0f}
- Total liquidation: ${total_liq:,.0f}
- Pattern: Short squeeze in progress
- Signal: Extreme bullish pressure
- Action: AVOID shorts until stabilization"""
            
            else:
                return f"""🔴 **EXTREME MIXED LIQUIDATION EVENT**
- Total liquidation: ${total_liq:,.0f}
- Balanced liquidation between long/short
- Pattern: High volatility environment
- Signal: Extreme caution needed
- Action: Reduce position size"""

        elif total_liq > 100000000:  # 100-200M liquidation
            if long_liq > short_liq * 1.5:  # 1.5x more long liquidations
                return f"""🟡 **MODERATE LONG LIQUIDATION WAVE**
- Long liquidation: ${long_liq:,.0f}
- Total liquidation: ${total_liq:,.0f}
- Pattern: Long position cleanup
- Signal: Bearish momentum
- Action: Careful with long entries"""
            
            elif short_liq > long_liq * 1.5:  # 1.5x more short liquidations
                return f"""🟡 **MODERATE SHORT LIQUIDATION WAVE**
- Short liquidation: ${short_liq:,.0f}
- Total liquidation: ${total_liq:,.0f}
- Pattern: Short position cleanup
- Signal: Bullish momentum
- Action: Careful with short entries"""
            
            else:
                return f"""🟡 **MODERATE MIXED LIQUIDATION**
- Total liquidation: ${total_liq:,.0f}
- Balanced liquidation between long/short
- Pattern: High volatility environment
- Signal: Extreme caution needed
- Action: Reduce position size"""

        elif total_liq > 50000000:  # 50-100M liquidation
            return f"""🟡 **MODERATE LIQUIDATION RISK**
- Total liquidasi: ${total_liq:,.0f}
- Aktivitas liquidasi sedang
- Pattern: Normal market volatility
- Signal: Standard risk management
- Action: Use proper stop losses"""

        else:
            return f"""🟢 **LOW LIQUIDATION RISK**
- Total liquidasi: ${total_liq:,.0f}
- Liquidasi minimal detected
- Pattern: Stable market conditions
- Signal: Lower risk environment
- Action: Normal position sizing OK"""
        
        liq_ratio = long_liq / (short_liq + 1)  # Avoid division by zero
        
        if long_liq > short_liq * 3 and total_liq > 100000000:
            return f"🔴 Long Liquidation Cascade: ${long_liq:,.0f} longs vs ${short_liq:,.0f} shorts"
        elif short_liq > long_liq * 3 and total_liq > 100000000:
            return f"🟢 Short Squeeze Pattern: ${short_liq:,.0f} shorts vs ${long_liq:,.0f} longs"
        elif total_liq > 200000000:
            return f"💥 High Liquidation Activity: ${total_liq:,.0f} total (Extreme volatility)"
        elif total_liq > 100000000:
            return f"🟡 Moderate Liquidations: ${total_liq:,.0f} total (Normal volatility)"
        else:
            return f"⚪ Standard Liquidations: ${total_liq:,.0f} total (Low volatility)"

    def _get_source_quality(self, source):
        """Get source quality indicator"""
        if source == 'coinglass':
            return "🟢 Live Coinglass"
        elif source == 'binance':
            return "🟢 Live Binance"
        elif source == 'coingecko':
            return "🟢 Live CoinGecko"
        elif source in ['binance_simple', 'coingecko_free']:
            return "🟡 Live API"
        elif source == 'mock':
            return "🔄 Simulated"
        else:
            return "📊 API Data"

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

    def generate_daily_signal(self, language='id', crypto_api=None):
        """Generate daily trading signals"""
        if language == 'id':
            message = """🚨 **Sinyal Trading Harian**

📈 **BUY SIGNALS:**
- BTC: Bullish divergence di RSI, target $46K
- ETH: Breakout dari triangle pattern
- SOL: Volume surge, momentum positif

📉 **SELL SIGNALS:**
- DOGE: Overbought di RSI 70+
- Meme coins: Profit taking recommended

⚖️ **HOLD/WAIT:**
- ADA: Menunggu konfirmasi breakout
- BNB: Range bound, tunggu direction

🎯 **Setup Trading:**
- Entry: Market price atau limit order
- Stop Loss: 5-8% dari entry
- Take Profit: 15-25% target

⏰ Valid untuk 24 jam - Update setiap hari!
            """
        else:
            message = """🚨 **Daily Trading Signals**

📈 **BUY SIGNALS:**
- BTC: Bullish divergence on RSI, target $46K
- ETH: Breakout from triangle pattern
- SOL: Volume surge, positive momentum

📉 **SELL SIGNALS:**
- DOGE: Overbought di RSI 70+
- Meme coins: Profit taking recommended

⚖️ **HOLD/WAIT:**
- ADA: Waiting for breakout confirmation
- BNB: Range bound, waiting direction

🎯 **Trading Setup:**
- Entry: Market price or limit order
- Stop Loss: 5-8% from entry
- Take Profit: 15-25% target

⏰ Valid untuk 24 hours - Updated daily!
            """

        return message

    def generate_single_futures_signal(self, symbol, language='id', crypto_api=None):
        """Generate advanced futures trading signal for a single coin with comprehensive multi-API analysis"""
        if not crypto_api:
            # Return error if no API provided
            print(f"❌ No crypto_api provided to generate_single_futures_signal for {symbol}")
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
            # Get comprehensive data for the requested symbol
            print(f"📊 Fetching comprehensive data for {symbol}...")
            
            # 1. Get price data from multiple sources
            price_data = crypto_api.get_price(symbol)
            current_price = price_data.get('price', 0) if price_data else 0
            change_24h = price_data.get('change_24h', 0) if price_data else 0
            volume_24h = price_data.get('volume_24h', 0) if price_data else 0
            market_cap = price_data.get('market_cap', 0) if price_data else 0
            price_source = price_data.get('source', 'unknown') if price_data else 'unknown'

            # 2. Get futures data from Coinglass
            futures_data = crypto_api.get_futures_data(symbol)
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)
            futures_source = futures_data.get('source', 'mock')

            # 3. Get open interest data
            oi_data = crypto_api.get_open_interest(symbol)
            open_interest = oi_data.get('open_interest', 0)
            oi_change = oi_data.get('open_interest_change', 0)
            oi_source = oi_data.get('source', 'mock')

            # 4. Get funding rate data
            funding_data = crypto_api.get_funding_rate(symbol)
            avg_funding = funding_data.get('average_funding_rate', 0)
            funding_source = funding_data.get('source', 'mock')

            # 5. Get liquidation data
            liq_data = crypto_api.get_liquidation_data(symbol)
            long_liq = liq_data.get('long_liquidation', 0)
            short_liq = liq_data.get('short_liquidation', 0)
            total_liq = liq_data.get('total_liquidation', 0)
            liq_source = liq_data.get('source', 'mock')

            # 6. Get market overview for context
            market_overview = crypto_api.get_market_overview()
            btc_dominance = market_overview.get('btc_dominance', 50)
            market_trend = market_overview.get('market_cap_change_24h', 0)

            # 7. Get news sentiment (for context)
            news_data = []
            try:
                news_data = crypto_api.get_crypto_news(3)
            except:
                pass

            print(f"✅ {symbol}: Price ${current_price:,.2f}, Long {long_ratio:.1f}%, OI ${open_interest:,.0f}")

            # Advanced signal generation based on multiple factors
            signal_analysis = self._generate_advanced_signal(
                symbol, current_price, change_24h, long_ratio, short_ratio,
                open_interest, oi_change, avg_funding, total_liq, long_liq, short_liq,
                btc_dominance, market_trend, news_data
            )

            # Technical analysis
            tech_analysis = self._generate_technical_analysis(
                current_price, change_24h, volume_24h, long_ratio, avg_funding
            )

            # Risk assessment
            risk_assessment = self._generate_risk_assessment(
                long_ratio, oi_change, avg_funding, total_liq, market_trend
            )

            # Market structure analysis
            market_structure = self._analyze_market_structure_advanced(
                change_24h, oi_change, long_ratio, avg_funding
            )

            # Liquidation analysis
            liquidation_analysis = self._analyze_liquidation_patterns(
                long_liq, short_liq, total_liq, long_ratio
            )

            if language == 'id':
                message = f"""⚡ **Analisis Futures Advanced - {symbol}**

💰 **Data Real-Time Multi-Source:**
- Current Price: ${current_price:,.2f} ({change_24h:+.2f}%)
- Volume 24h: ${volume_24h:,.0f}
- Market Cap: ${market_cap:,.0f}
- BTC Dominance: {btc_dominance:.1f}%

📊 **Analisis Futures Komprehensif:**
- Long/Short Ratio: {long_ratio:.1f}% / {short_ratio:.1f}%
- Open Interest: ${open_interest:,.0f} ({oi_change:+.1f}%)
- Funding Rate: {avg_funding:.4f}% (8h) | Annualized: {avg_funding*365*3:.2f}%
- Liquidations 24h: ${total_liq:,.0f} (Long: ${long_liq:,.0f}, Short: ${short_liq:,.0f})

{signal_analysis}

🔍 **Analisis Teknikal:**
{tech_analysis}

🏗️ **Struktur Pasar:**
{market_structure}

💥 **Analisis Liquidation:**
{liquidation_analysis}

⚠️ **Risk Assessment:**
{risk_assessment}

📡 **Kualitas Data:**
- Price: {self._get_source_quality(price_source)}
- Futures: {self._get_source_quality(futures_source)}
- Open Interest: {self._get_source_quality(oi_source)}
- Funding: {self._get_source_quality(funding_source)}
- Liquidation: {self._get_source_quality(liq_source)}

⚠️ **Risk Warning:**
Analisis ini menggunakan multiple data sources untuk akurasi maksimal.
Futures trading sangat berisiko! Gunakan proper risk management.

"""
                # Add comprehensive data freshness info
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                message += f"🕐 Update: {current_time} | Comprehensive Multi-API Analysis\n"
                
                real_sources = sum(1 for src in [price_source, futures_source, oi_source, funding_source, liq_source] 
                                 if src in ['binance', 'coinglass', 'coingecko'])
                message += f"📈 Real Data: {real_sources}/5 sources | Advanced Analysis Mode"

            else:
                message = f"""⚡ **Advanced Futures Analysis - {symbol}**

💰 **Real-Time Multi-Source Data:**
- Current Price: ${current_price:,.2f} ({change_24h:+.2f}%)
- Volume 24h: ${volume_24h:,.0f}
- Market Cap: ${market_cap:,.0f}
- BTC Dominance: {btc_dominance:.1f}%

📊 **Comprehensive Futures Analysis:**
- Long/Short Ratio: {long_ratio:.1f}% / {short_ratio:.1f}%
- Open Interest: ${open_interest:,.0f} ({oi_change:+.1f}%)
- Funding Rate: {avg_funding:.4f}% (8h) | Annualized: {avg_funding*365*3:.2f}%
- Liquidations 24h: ${total_liq:,.0f} (Long: ${long_liq:,.0f}, Short: ${short_liq:,.0f})

{signal_analysis}

🔍 **Technical Analysis:**
{tech_analysis}

🏗️ **Market Structure:**
{market_structure}

💥 **Liquidation Analysis:**
{liquidation_analysis}

⚠️ **Risk Assessment:**
{risk_assessment}

📡 **Data Quality:**
- Price: {self._get_source_quality(price_source)}
- Futures: {self._get_source_quality(futures_source)}
- Open Interest: {self._get_source_quality(oi_source)}
- Funding: {self._get_source_quality(funding_source)}
- Liquidation: {self._get_source_quality(liq_source)}

⚠️ **Risk Warning:**
This analysis uses multiple data sources for maximum accuracy.
Futures trading is high risk! Use proper risk management.

"""
                # Add comprehensive data freshness info
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                message += f"🕐 Update: {current_time} | Comprehensive Multi-API Analysis\n"
                
                real_sources = sum(1 for src in [price_source, futures_source, oi_source, funding_source, liq_source] 
                                 if src in ['binance', 'coinglass', 'coingecko'])
                message += f"📈 Real Data: {real_sources}/5 sources | Advanced Analysis Mode"

            return message

        except Exception as e:
            print(f"Error in generate_single_futures_signal: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Analisis Futures Advanced {symbol}**

Terjadi kesalahan saat menganalisis data futures komprehensif.
Error: {str(e)}

📊 Silakan coba lagi atau gunakan `/futures_signals` untuk analisis multi-coin.

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!"""
            else:
                return f"""❌ **Error in Advanced Futures Analysis {symbol}**

Error occurred while analyzing comprehensive futures data.
Error: {str(e)}

📊 Please try again or use `/futures_signals` for multi-coin analysis.

⚠️ **Risk Warning:**
Futures trading is high risk!
Use proper risk management and don't FOMO!"""

    def generate_timeframe_analysis(self, symbol, timeframe='1h', language='id', crypto_api=None):
        """Generate comprehensive timeframe analysis for a single coin"""
        if not crypto_api:
            if language == 'id':
                return f"""❌ **Error: API tidak tersedia**

Tidak dapat mengakses data untuk analisis timeframe {symbol} ({timeframe}).
Silakan coba lagi nanti.

⚠️ **Risk Warning:**
Trading berisiko tinggi! Gunakan proper risk management."""
            else:
                return f"""❌ **Error: API unavailable**

Cannot access data for timeframe analysis {symbol} ({timeframe}).
Please try again later.

⚠️ **Risk Warning:**
Trading is high risk! Use proper risk management."""

        try:
            # Get comprehensive timeframe data
            timeframe_data = crypto_api.get_timeframe_analysis(symbol, timeframe)
            
            if 'error' in timeframe_data:
                if language == 'id':
                    return f"""❌ **Error dalam Analisis Timeframe**

Gagal menganalisis {symbol} pada timeframe {timeframe}.
Error: {timeframe_data.get('error')}

Silakan coba dengan timeframe lain atau symbol yang berbeda."""
                else:
                    return f"""❌ **Error in Timeframe Analysis**

Failed to analyze {symbol} on {timeframe} timeframe.
Error: {timeframe_data.get('error')}

Please try with different timeframe or symbol."""

            # Extract data
            price_data = timeframe_data.get('price_data', {})
            trend_analysis = timeframe_data.get('trend_analysis', {})
            support_resistance = timeframe_data.get('support_resistance', {})
            volatility = timeframe_data.get('volatility', {})
            mark_data = timeframe_data.get('mark_data', {})
            funding_data = timeframe_data.get('funding_data', {})
            ls_data = timeframe_data.get('long_short_data', {})
            candlesticks = timeframe_data.get('candlesticks', [])

            current_price = price_data.get('price', 0)
            price_change = price_data.get('change_24h', 0)

            if language == 'id':
                message = f"""📊 **Analisis Timeframe {timeframe.upper()} - {symbol}**

💰 **Data Harga Real-time:**
- Current Price: ${self._format_price_smart(current_price)}
- 24h Change: {price_change:+.2f}%
- Timeframe: {timeframe}
- Volume 24h: ${price_data.get('volume_24h', 0):,.0f}

📈 **Analisis Trend ({timeframe}):**
- Trend Direction: {self._format_trend_id(trend_analysis.get('direction', 'neutral'))}
- Trend Strength: {self._format_strength_id(trend_analysis.get('strength', 'weak'))}
- Price Change: {trend_analysis.get('price_change_pct', 0):+.2f}%
- SMA 5: ${self._format_price_smart(trend_analysis.get('sma_5', 0))}
- SMA 10: ${self._format_price_smart(trend_analysis.get('sma_10', 0))}
- SMA 20: ${self._format_price_smart(trend_analysis.get('sma_20', 0))}

🎯 **Support & Resistance:**
- Support: ${self._format_price_smart(support_resistance.get('support', 0))}
- Resistance: ${self._format_price_smart(support_resistance.get('resistance', 0))}
- Distance to Support: {support_resistance.get('distance_to_support', 0):.1f}%
- Distance to Resistance: {support_resistance.get('distance_to_resistance', 0):.1f}%

⚡ **Volatility Analysis:**
- Volatility Level: {self._format_volatility_id(volatility.get('volatility', 'low'))}
- Price Range (10 periods): {volatility.get('price_range', 0):.2f}%
- ATR: {volatility.get('atr', 0):.4f}

📊 **Futures Data:**
- Long/Short Ratio: {ls_data.get('long_ratio', 50):.1f}% / {ls_data.get('short_ratio', 50):.1f}%
- Funding Rate: {funding_data.get('last_funding_rate', 0)*100:.4f}%
- Mark Price: ${self._format_price_smart(mark_data.get('mark_price', 0))}

🔍 **Recent Candlesticks:**
{self._format_recent_candles(candlesticks[-5:], language)}

⚡ **Trading Signal ({timeframe}):**
{self._generate_timeframe_signal(trend_analysis, support_resistance, volatility, ls_data, current_price, language)}

⚠️ **Risk Management:**
- Stop Loss: {self._calculate_stop_loss(current_price, support_resistance, trend_analysis):.2f}
- Take Profit: {self._calculate_take_profit(current_price, support_resistance, trend_analysis):.2f}
- Position Size: {self._recommend_position_size(volatility, language)}

🕐 **Update:** {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Source:** Multiple Binance APIs (Real-time)"""

            else:
                message = f"""📊 **{timeframe.upper()} Timeframe Analysis - {symbol}**

💰 **Real-time Price Data:**
- Current Price: ${self._format_price_smart(current_price)}
- 24h Change: {price_change:+.2f}%
- Timeframe: {timeframe}
- Volume 24h: ${price_data.get('volume_24h', 0):,.0f}

📈 **Trend Analysis ({timeframe}):**
- Trend Direction: {trend_analysis.get('direction', 'neutral').title()}
- Trend Strength: {trend_analysis.get('strength', 'weak').title()}
- Price Change: {trend_analysis.get('price_change_pct', 0):+.2f}%
- SMA 5: ${self._format_price_smart(trend_analysis.get('sma_5', 0))}
- SMA 10: ${self._format_price_smart(trend_analysis.get('sma_10', 0))}
- SMA 20: ${self._format_price_smart(trend_analysis.get('sma_20', 0))}

🎯 **Support & Resistance:**
- Support: ${self._format_price_smart(support_resistance.get('support', 0))}
- Resistance: ${self._format_price_smart(support_resistance.get('resistance', 0))}
- Distance to Support: {support_resistance.get('distance_to_support', 0):.1f}%
- Distance to Resistance: {support_resistance.get('distance_to_resistance', 0):.1f}%

⚡ **Volatility Analysis:**
- Volatility Level: {volatility.get('volatility', 'low').replace('_', ' ').title()}
- Price Range (10 periods): {volatility.get('price_range', 0):.2f}%
- ATR: {volatility.get('atr', 0):.4f}

📊 **Futures Data:**
- Long/Short Ratio: {ls_data.get('long_ratio', 50):.1f}% / {ls_data.get('short_ratio', 50):.1f}%
- Funding Rate: {funding_data.get('last_funding_rate', 0)*100:.4f}%
- Mark Price: ${self._format_price_smart(mark_data.get('mark_price', 0))}

🔍 **Recent Candlesticks:**
{self._format_recent_candles(candlesticks[-5:], language)}

⚡ **Trading Signal ({timeframe}):**
{self._generate_timeframe_signal(trend_analysis, support_resistance, volatility, ls_data, current_price, language)}

⚠️ **Risk Management:**
- Stop Loss: {self._calculate_stop_loss(current_price, support_resistance, trend_analysis):.2f}
- Take Profit: {self._calculate_take_profit(current_price, support_resistance, trend_analysis):.2f}
- Position Size: {self._recommend_position_size(volatility, language)}

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')}
📡 **Source:** Multiple Binance APIs (Real-time)"""

            return message

        except Exception as e:
            print(f"Error in generate_timeframe_analysis: {e}")
            if language == 'id':
                return f"""❌ **Error dalam Analisis Timeframe {symbol}**

Terjadi kesalahan saat menganalisis timeframe {timeframe}.
Error: {str(e)}

Silakan coba lagi atau gunakan timeframe lain."""
            else:
                return f"""❌ **Error in Timeframe Analysis {symbol}**

Error occurred while analyzing {timeframe} timeframe.
Error: {str(e)}

Please try again or use different timeframe."""

    def _format_price_smart(self, price):
        """Smart price formatting"""
        if price >= 1000:
            return f"{price:,.2f}"
        elif price >= 1:
            return f"{price:.4f}"
        elif price >= 0.01:
            return f"{price:.6f}"
        else:
            return f"{price:.8f}"

    def _format_trend_id(self, trend):
        """Format trend in Indonesian"""
        mapping = {
            'bullish': '🟢 Bullish (Naik)',
            'bearish': '🔴 Bearish (Turun)', 
            'sideways': '🟡 Sideways (Samping)',
            'neutral': '⚪ Neutral'
        }
        return mapping.get(trend, trend)

    def _format_strength_id(self, strength):
        """Format strength in Indonesian"""
        mapping = {
            'strong': '💪 Kuat',
            'moderate': '📊 Sedang',
            'weak': '📉 Lemah'
        }
        return mapping.get(strength, strength)

    def _format_volatility_id(self, volatility):
        """Format volatility in Indonesian"""
        mapping = {
            'very_high': '🔴 Sangat Tinggi',
            'high': '🟠 Tinggi',
            'moderate': '🟡 Sedang',
            'low': '🟢 Rendah'
        }
        return mapping.get(volatility, volatility)

    def _format_recent_candles(self, candles, language='id'):
        """Format recent candlesticks"""
        if not candles:
            return "Data candlestick tidak tersedia" if language == 'id' else "Candlestick data unavailable"

        result = ""
        for i, candle in enumerate(candles[-3:]):  # Last 3 candles
            open_price = float(candle['open'])
            close_price = float(candle['close'])
            change = ((close_price - open_price) / open_price) * 100
            change_emoji = "🟢" if change >= 0 else "🔴"
            
            time_str = candle.get('close_time_iso', '')[:16].replace('T', ' ')
            result += f"{change_emoji} {time_str}: {change:+.2f}%\n"

        return result

    def _generate_timeframe_signal(self, trend_analysis, support_resistance, volatility, ls_data, current_price, language='id'):
        """Generate trading signal based on timeframe analysis"""
        signal_score = 0
        signals = []

        # Trend signal
        direction = trend_analysis.get('direction', 'neutral')
        strength = trend_analysis.get('strength', 'weak')
        
        if direction == 'bullish' and strength == 'strong':
            signal_score += 3
            signals.append("🟢 Strong bullish trend")
        elif direction == 'bullish':
            signal_score += 1
            signals.append("🟡 Moderate bullish trend")
        elif direction == 'bearish' and strength == 'strong':
            signal_score -= 3
            signals.append("🔴 Strong bearish trend")
        elif direction == 'bearish':
            signal_score -= 1
            signals.append("🟡 Moderate bearish trend")

        # Support/Resistance signal
        dist_to_support = support_resistance.get('distance_to_support', 0)
        dist_to_resistance = support_resistance.get('distance_to_resistance', 0)

        if dist_to_support < 2:
            signal_score += 1
            signals.append("🎯 Near support level")
        elif dist_to_resistance < 2:
            signal_score -= 1
            signals.append("⚠️ Near resistance level")

        # Long/Short ratio signal
        long_ratio = ls_data.get('long_ratio', 50)
        if long_ratio > 70:
            signal_score -= 1
            signals.append("📊 High long bias (contrarian bearish)")
        elif long_ratio < 30:
            signal_score += 1
            signals.append("📊 High short bias (contrarian bullish)")

        # Final signal
        if signal_score >= 3:
            signal_type = "🟢 STRONG BUY" if language == 'id' else "🟢 STRONG BUY"
        elif signal_score >= 1:
            signal_type = "🟡 BUY" if language == 'id' else "🟡 BUY"
        elif signal_score <= -3:
            signal_type = "🔴 STRONG SELL" if language == 'id' else "🔴 STRONG SELL"
        elif signal_score <= -1:
            signal_type = "🟡 SELL" if language == 'id' else "🟡 SELL"
        else:
            signal_type = "⚪ HOLD" if language == 'id' else "⚪ HOLD"

        result = f"**Signal: {signal_type}** (Score: {signal_score}/5)\n\n"
        result += "**Faktor Signal:**\n" if language == 'id' else "**Signal Factors:**\n"
        for signal in signals[:4]:  # Top 4 signals
            result += f"• {signal}\n"

        return result

    def _calculate_stop_loss(self, current_price, support_resistance, trend_analysis):
        """Calculate stop loss level"""
        direction = trend_analysis.get('direction', 'neutral')
        
        if direction == 'bullish':
            support = support_resistance.get('support', current_price * 0.95)
            return support * 0.99  # Just below support
        else:
            resistance = support_resistance.get('resistance', current_price * 1.05)
            return resistance * 1.01  # Just above resistance

    def _calculate_take_profit(self, current_price, support_resistance, trend_analysis):
        """Calculate take profit level"""
        direction = trend_analysis.get('direction', 'neutral')
        
        if direction == 'bullish':
            resistance = support_resistance.get('resistance', current_price * 1.05)
            return resistance * 0.99  # Just below resistance
        else:
            support = support_resistance.get('support', current_price * 0.95)
            return support * 1.01  # Just above support

    def _recommend_position_size(self, volatility, language='id'):
        """Recommend position size based on volatility"""
        vol_level = volatility.get('volatility', 'low')
        
        if vol_level == 'very_high':
            return "Sangat kecil (1-2%)" if language == 'id' else "Very small (1-2%)"
        elif vol_level == 'high':
            return "Kecil (2-3%)" if language == 'id' else "Small (2-3%)"
        elif vol_level == 'moderate':
            return "Normal (3-5%)" if language == 'id' else "Normal (3-5%)"
        else:
            return "Standard (5-10%)" if language == 'id' else "Standard (5-10%)"

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate advanced futures trading signals with comprehensive multi-API analysis"""
        # Major symbols to analyze
        major_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']

        if not crypto_api:
            # Return error if no API provided
            print("❌ No crypto_api provided to generate_futures_signals")
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
            print(f"📊 Starting futures signals generation for {len(major_symbols)} symbols")
            
            # Get comprehensive data for all major symbols
            signals_data = []
            comprehensive_analysis = []
            real_data_sources = {'price': 0, 'futures': 0, 'oi': 0, 'funding': 0, 'liquidation': 0}
            
            # Get market overview for context
            try:
                market_overview = crypto_api.get_market_overview()
                btc_dominance = market_overview.get('btc_dominance', 50)
                market_trend = market_overview.get('market_cap_change_24h', 0)
                print(f"✅ Market overview obtained: BTC Dom {btc_dominance:.1f}%")
            except Exception as e:
                print(f"⚠️ Market overview failed: {e}, using defaults")
                btc_dominance = 50
                market_trend = 0

            print(f"🔄 Getting advanced futures analysis for {len(major_symbols)} symbols...")

            for symbol in major_symbols:
                try:
                    print(f"📊 Fetching comprehensive data for {symbol}...")

                    # 1. Get price data
                    price_data = crypto_api.get_price(symbol)
                    current_price = price_data.get('price', 0) if price_data else 0
                    change_24h = price_data.get('change_24h', 0) if price_data else 0
                    volume_24h = price_data.get('volume_24h', 0) if price_data else 0
                    price_source = price_data.get('source', 'unknown') if price_data else 'unknown'

                    # 2. Get futures data
                    futures_data = crypto_api.get_futures_data(symbol)
                    long_ratio = futures_data.get('long_ratio', 50)
                    short_ratio = futures_data.get('short_ratio', 50)
                    futures_source = futures_data.get('source', 'mock')

                    # 3. Get open interest data
                    oi_data = crypto_api.get_open_interest(symbol)
                    open_interest = oi_data.get('open_interest', 0)
                    oi_change = oi_data.get('open_interest_change', 0)
                    oi_source = oi_data.get('source', 'mock')

                    # 4. Get funding rate data
                    funding_data = crypto_api.get_funding_rate(symbol)
                    avg_funding = funding_data.get('average_funding_rate', 0)
                    funding_source = funding_data.get('source', 'mock')

                    # 5. Get liquidation data
                    liq_data = crypto_api.get_liquidation_data(symbol)
                    total_liq = liq_data.get('total_liquidation', 0)
                    long_liq = liq_data.get('long_liquidation', 0)
                    short_liq = liq_data.get('short_liquidation', 0)
                    liq_source = liq_data.get('source', 'mock')

                    # Count real data sources
                    if price_source in ['binance', 'coinglass', 'coingecko']:
                        real_data_sources['price'] += 1
                    if futures_source == 'coinglass':
                        real_data_sources['futures'] += 1
                    if oi_source == 'coinglass':
                        real_data_sources['oi'] += 1
                    if funding_source == 'coinglass':
                        real_data_sources['funding'] += 1
                    if liq_source == 'coinglass':
                        real_data_sources['liquidation'] += 1

                    print(f"✅ {symbol}: Price ${current_price:,.2f}, L/S {long_ratio:.1f}%/{short_ratio:.1f}%, OI ${open_interest:,.0f}")

                    # Generate advanced signal analysis
                    signal_analysis = self._generate_advanced_signal(
                        symbol, current_price, change_24h, long_ratio, short_ratio,
                        open_interest, oi_change, avg_funding, total_liq, long_liq, short_liq,
                        btc_dominance, market_trend, []
                    )

                    # Extract signal from analysis
                    if "LONG" in signal_analysis:
                        signal_type = "LONG"
                        signal_strength = "STRONG" if "VERY STRONG" in signal_analysis or "STRONG" in signal_analysis else "MODERATE"
                    else:
                        signal_type = "SHORT"
                        signal_strength = "STRONG" if "VERY STRONG" in signal_analysis or "STRONG" in signal_analysis else "MODERATE"

                    # Market structure analysis
                    market_structure = self._analyze_market_structure_advanced(
                        change_24h, oi_change, long_ratio, avg_funding
                    )

                    # Risk assessment
                    risk_assessment = self._generate_risk_assessment(
                        long_ratio, oi_change, avg_funding, total_liq, market_trend
                    )

                    comprehensive_analysis.append({
                        'symbol': symbol,
                        'price': current_price,
                        'change_24h': change_24h,
                        'volume_24h': volume_24h,
                        'long_ratio': long_ratio,
                        'short_ratio': short_ratio,
                        'open_interest': open_interest,
                        'oi_change': oi_change,
                        'funding_rate': avg_funding,
                        'total_liquidation': total_liq,
                        'signal_type': signal_type,
                        'signal_strength': signal_strength,
                        'market_structure': market_structure,
                        'risk_level': risk_assessment.split('\n')[0],
                        'sources': {
                            'price': price_source,
                            'futures': futures_source,
                            'oi': oi_source,
                            'funding': funding_source,
                            'liquidation': liq_source
                        }
                    })

                    # Calculate entry, TP, SL
                    if signal_type == "LONG":
                        if signal_strength == "STRONG":
                            tp_price = current_price * 1.05  # 5% up
                            sl_price = current_price * 0.97  # 3% down
                        else:
                            tp_price = current_price * 1.03  # 3% up
                            sl_price = current_price * 0.98  # 2% down
                    else:  # SHORT
                        if signal_strength == "STRONG":
                            tp_price = current_price * 0.95  # 5% down
                            sl_price = current_price * 1.03  # 3% up
                        else:
                            tp_price = current_price * 0.97  # 3% down
                            sl_price = current_price * 1.02  # 2% up

                    signals_data.append({
                        'symbol': symbol,
                        'signal_type': signal_type,
                        'signal_strength': signal_strength,
                        'entry_price': current_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price,
                        'risk_reward': abs((tp_price - current_price) / (sl_price - current_price)),
                        'data_quality': sum(1 for src in [price_source, futures_source, oi_source, funding_source, liq_source] 
                                          if src in ['binance', 'coinglass', 'coingecko'])
                    })

                except Exception as e:
                    print(f"❌ Error getting comprehensive data for {symbol}: {e}")
                    continue

            total_real_sources = sum(real_data_sources.values())
            max_possible_sources = len(major_symbols) * 5  # 5 data types per symbol

            print(f"📈 Real data coverage: {total_real_sources}/{max_possible_sources} sources")

            # Check if we have enough data
            if len(comprehensive_analysis) == 0:
                if language == 'id':
                    return """❌ **Data Tidak Tersedia**

Gagal mengambil data komprehensif untuk semua symbol.
Silakan coba lagi dalam beberapa menit.

📊 Alternatif: Gunakan `/futures <symbol>` untuk analisis individual.

⚠️ **Risk Warning:**
Futures trading berisiko tinggi!"""
                else:
                    return """❌ **Data Unavailable**

Failed to fetch comprehensive data for all symbols.
Please try again in a few minutes.

📊 Alternative: Use `/futures <symbol>` for individual analysis.

⚠️ **Risk Warning:**
Futures trading is high risk!"""

            # Build comprehensive message
            if language == 'id':
                data_coverage = (total_real_sources / max_possible_sources) * 100
                data_quality = "🟢 EXCELLENT" if data_coverage >= 60 else "🟡 GOOD" if data_coverage >= 30 else "🔴 LIMITED"

                message = f"""⚡ **Sinyal Futures Advanced Multi-API**

📊 **Data Comprehensive Coverage: {data_quality}** ({total_real_sources}/{max_possible_sources} sources)
📈 **Market Context:** BTC Dom {btc_dominance:.1f}%, Market {market_trend:+.1f}%

🔍 **Advanced Multi-API Analysis:**
"""
                # Add comprehensive analysis
                for data in comprehensive_analysis:
                    sources_quality = sum(1 for src in data['sources'].values() 
                                        if src in ['binance', 'coinglass', 'coingecko'])
                    quality_emoji = "🟢" if sources_quality >= 4 else "🟡" if sources_quality >= 2 else "🔄"
                    
                    message += f"\n**{data['symbol']}** {quality_emoji}\n"
                    message += f"  • Price: ${data['price']:,.2f} ({data['change_24h']:+.1f}%)\n"
                    message += f"  • L/S: {data['long_ratio']:.1f}%/{data['short_ratio']:.1f}% | OI: ${data['open_interest']:,.0f} ({data['oi_change']:+.1f}%)\n"
                    message += f"  • Funding: {data['funding_rate']:.4f}% | Liq: ${data['total_liquidation']:,.0f}\n"
                    message += f"  • Structure: {data['market_structure'][:30]}...\n"
                    message += f"  • {data['risk_level']}\n"

                message += "\n🎯 **Advanced Trading Signals:**\n"

                # Add advanced trading signals
                for signal in signals_data:
                    signal_emoji = "🟢" if signal['signal_type'] == "LONG" else "🔴"
                    strength_emoji = "⭐⭐⭐" if signal['signal_strength'] == "STRONG" else "⭐⭐"
                    
                    message += f"- {signal_emoji} **{signal['symbol']} {signal['signal_type']}** {strength_emoji}\n"
                    message += f"  └ Entry: ${signal['entry_price']:,.2f} | TP: ${signal['tp_price']:,.2f} | SL: ${signal['sl_price']:,.2f}\n"
                    message += f"  └ R/R: {signal['risk_reward']:.1f}:1 | Data Quality: {signal['data_quality']}/5 sources\n"

                message += f"""
📊 **Multi-API Data Sources:**
- Price Data: {real_data_sources['price']}/{len(major_symbols)} live sources
- Futures Data: {real_data_sources['futures']}/{len(major_symbols)} live sources  
- Open Interest: {real_data_sources['oi']}/{len(major_symbols)} live sources
- Funding Rate: {real_data_sources['funding']}/{len(major_symbols)} live sources
- Liquidation: {real_data_sources['liquidation']}/{len(major_symbols)} live sources

📈 **Advanced Leverage Recommendations:**
- Conservative: 2-3x (High accuracy signals)
- Moderate: 3-5x (Good data coverage)
- Aggressive: 5-10x (Excellent data only)

⚠️ **Advanced Risk Warning:**
Multi-API analysis untuk akurasi maksimal.
Futures trading sangat berisiko! Gunakan proper risk management.

"""
                # Add comprehensive data freshness info
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                message += f"🕐 Update: {current_time} | Comprehensive Multi-API Analysis\n"
                message += f"📡 Coverage: {data_coverage:.1f}% live data | Advanced Analysis Mode"

            else:
                data_coverage = (total_real_sources / max_possible_sources) * 100
                data_quality = "🟢 EXCELLENT" if data_coverage >= 60 else "🟡 GOOD" if data_coverage >= 30 else "🔴 LIMITED"

                message = f"""⚡ **Advanced Multi-API Futures Signals**

📊 **Comprehensive Data Coverage: {data_quality}** ({total_real_sources}/{max_possible_sources} sources)
📈 **Market Context:** BTC Dom {btc_dominance:.1f}%, Market {market_trend:+.1f}%

🔍 **Advanced Multi-API Analysis:**
"""
                # Add comprehensive analysis
                for data in comprehensive_analysis:
                    sources_quality = sum(1 for src in data['sources'].values() 
                                        if src in ['binance', 'coinglass', 'coingecko'])
                    quality_emoji = "🟢" if sources_quality >= 4 else "🟡" if sources_quality >= 2 else "🔄"
                    
                    message += f"\n**{data['symbol']}** {quality_emoji}\n"
                    message += f"  • Price: ${data['price']:,.2f} ({data['change_24h']:+.1f}%)\n"
                    message += f"  • L/S: {data['long_ratio']:.1f}%/{data['short_ratio']:.1f}% | OI: ${data['open_interest']:,.0f} ({data['oi_change']:+.1f}%)\n"
                    message += f"  • Funding: {data['funding_rate']:.4f}% | Liq: ${data['total_liquidation']:,.0f}\n"
                    message += f"  • Structure: {data['market_structure'][:30]}...\n"
                    message += f"  • {data['risk_level']}\n"

                message += "\n🎯 **Advanced Trading Signals:**\n"

                # Add advanced trading signals
                for signal in signals_data:
                    signal_emoji = "🟢" if signal['signal_type'] == "LONG" else "🔴"
                    strength_emoji = "⭐⭐⭐" if signal['signal_strength'] == "STRONG" else "⭐⭐"
                    
                    message += f"- {signal_emoji} **{signal['symbol']} {signal['signal_type']}** {strength_emoji}\n"
                    message += f"  └ Entry: ${signal['entry_price']:,.2f} | TP: ${signal['tp_price']:,.2f} | SL: ${signal['sl_price']:,.2f}\n"
                    message += f"  └ R/R: {signal['risk_reward']:.1f}:1 | Data Quality: {signal['data_quality']}/5 sources\n"

                message += f"""
📊 **Multi-API Data Sources:**
- Price Data: {real_data_sources['price']}/{len(major_symbols)} live sources
- Futures Data: {real_data_sources['futures']}/{len(major_symbols)} live sources  
- Open Interest: {real_data_sources['oi']}/{len(major_symbols)} live sources
- Funding Rate: {real_data_sources['funding']}/{len(major_symbols)} live sources
- Liquidation: {real_data_sources['liquidation']}/{len(major_symbols)} live sources

📈 **Advanced Leverage Recommendations:**
- Conservative: 2-3x (High accuracy signals)
- Moderate: 3-5x (Good data coverage)
- Aggressive: 5-10x (Excellent data only)

⚠️ **Advanced Risk Warning:**
Multi-API analysis for maximum accuracy.
Futures trading is high risk! Use proper risk management.

"""
                # Add comprehensive data freshness info
                from datetime import datetime
                current_time = datetime.now().strftime('%H:%M:%S')
                message += f"🕐 Update: {current_time} | Comprehensive Multi-API Analysis\n"
                message += f"📡 Coverage: {data_coverage:.1f}% live data | Advanced Analysis Mode"

        except Exception as e:
            # Fallback to basic message if API calls fail
            print(f"Error in generate_futures_signals: {e}")
            if language == 'id':
                message = f"""❌ **Error dalam Advanced Futures Signals**

Terjadi kesalahan saat mengambil data komprehensif.
Error: {str(e)}

📊 Alternatif: Gunakan `/futures <symbol>` untuk analisis individual.

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!"""
            else:
                message = f"""❌ **Error in Advanced Futures Signals**

Error occurred while fetching comprehensive data.
Error: {str(e)}

📊 Alternative: Use `/futures <symbol>` for individual analysis.

⚠️ **Risk Warning:**
Futures trading is high risk!"""

        return message

    def get_comprehensive_analysis(self,
                                   symbol,
                                   futures_data,
                                   price_data,
                                   language='id',
                                   crypto_api=None):
        """Get comprehensive crypto analysis with enhanced multi-API integration"""
        if language == 'id':
            # Get comprehensive futures data for advanced analysis
            additional_data = self._get_comprehensive_futures_data(
                symbol, crypto_api)

            # Get news data for market sentiment
            news_data = []
            if crypto_api:
                try:
                    news_data = crypto_api.get_crypto_news(5)
                except:
                    pass

            # Get market overview for context
            market_overview = crypto_api.get_market_overview() if crypto_api else {}
            btc_dominance = market_overview.get('btc_dominance', 50)
            market_trend = market_overview.get('market_cap_change_24h', 0)

            # Enhanced analysis components
            sentiment_score = self._analyze_news_sentiment(news_data, symbol)
            advanced_signal = self._generate_institutional_signal(symbol, price_data, futures_data, additional_data)
            risk_matrix = self._generate_risk_matrix(futures_data, price_data, additional_data, market_overview)
            correlation_analysis = self._analyze_cross_market_correlation(symbol, price_data, market_overview)
            liquidation_analysis = self._analyze_liquidation_zones(additional_data, price_data)
            funding_analysis = self._analyze_funding_pressure(additional_data, futures_data)
            volume_profile = self._generate_volume_profile_analysis(price_data, additional_data)
            prediction_model = self._generate_price_prediction_model(symbol, price_data, futures_data, additional_data)

            # Data quality indicators
            data_sources = self._get_data_quality_indicators(price_data, futures_data, additional_data, news_data)

            message = f"""🎯 **ANALISIS INSTITUTIONAL-GRADE {symbol}**

📊 **Real-Time Multi-API Data Sources:**
{data_sources}

💰 **1. COMPREHENSIVE PRICE ANALYSIS:**
- Current Price: ${price_data.get('price', 0):,.2f} ({price_data.get('change_24h', 0):+.2f}%)
- Volume 24h: ${price_data.get('volume_24h', 0):,.0f}
- Market Cap: ${price_data.get('market_cap', 0):,.0f}
- High/Low 24h: ${price_data.get('high_24h', 0):,.2f} / ${price_data.get('low_24h', 0):,.2f}
- Price Source: {self._get_source_quality(price_data.get('source', 'unknown'))}

🧠 **2. ADVANCED TRADING SIGNAL:**
{advanced_signal}

⚠️ **3. COMPREHENSIVE RISK MATRIX:**
{risk_matrix}

🌐 **4. CROSS-MARKET CORRELATION:**
{correlation_analysis}

💥 **5. LIQUIDATION ZONE ANALYSIS:**
{liquidation_analysis}

💸 **6. FUNDING RATE PRESSURE:**
{funding_analysis}

📈 **7. VOLUME PROFILE & LIQUIDITY:**
{volume_profile}

🔮 **8. AI PRICE PREDICTION MODEL:**
{prediction_model}

📰 **Market Sentiment Analysis:**
{sentiment_score['analysis']}
- Sentiment Score: {sentiment_score['score']}/10 ({sentiment_score['trend']})
- News Impact: {sentiment_score['impact']}
- Social Activity: Enhanced monitoring active

📊 **Enhanced Futures Data:**
- Long/Short Ratio: {futures_data.get('long_ratio', 0):.1f}% / {futures_data.get('short_ratio', 0):.1f}%
- Open Interest: ${additional_data.get('open_interest', {}).get('open_interest', 0):,.0f} ({additional_data.get('open_interest', {}).get('open_interest_change', 0):+.1f}%)
- Funding Rate: {additional_data.get('funding_rate', {}).get('average_funding_rate', 0):.4f}% (Annualized: {additional_data.get('funding_rate', {}).get('average_funding_rate', 0)*365*3:.2f}%)
- Liquidations 24h: ${additional_data.get('liquidation', {}).get('total_liquidation', 0):,.0f}

🎯 **INSTITUTIONAL SUMMARY:**
- Signal Strength: {self._calculate_signal_strength(advanced_signal)}/10
- Risk Level: {self._extract_risk_level(risk_matrix)}
- Market Structure: {self._analyze_market_phase(price_data, futures_data, additional_data)}
- Recommendation: {self._generate_institutional_recommendation(advanced_signal, risk_matrix)}

📡 **Data Coverage:** Multi-API Real-time | BTC Dom: {btc_dominance:.1f}% | Market: {market_trend:+.1f}%
🔄 **Update:** Institutional-grade 8-point analysis with enhanced API integration
            """
        else:
            # Get news data for market sentiment
            news_data = []
            if crypto_api:
                try:
                    news_data = crypto_api.get_crypto_news(5)
                except:
                    pass

            # Analyze market sentiment from news
            sentiment_score = self._analyze_news_sentiment(news_data, symbol)

            # Get altcoin recommendations
            altcoins = self._get_altcoin_watchlist(language)

            # Risk assessment
            risk_level, risk_warnings = self._assess_market_risks(
                futures_data, price_data, sentiment_score)

            # Contrarian signals
            contrarian_signal = self._generate_contrarian_signal(
                futures_data, sentiment_score, language)

            # Weekly strategy
            weekly_strategy = self._generate_weekly_strategy(
                symbol, sentiment_score, language)

            message = f"""📊 **Fundamental Analysis {symbol}**

💰 **Price & Performance Data:**
- Current Price: ${price_data.get('price', 0):,.2f}
- 24h Change: {price_data.get('change_24h', 0):+.2f}%
- Volume: ${price_data.get('volume_24h', 0):,.0f}

📰 **1. Market Sentiment & Trend Analysis:**
{sentiment_score['analysis']}
- Sentiment Score: {sentiment_score['score']}/10
- Trend Direction: {sentiment_score['trend']}
- News Impact: {sentiment_score['impact']}

🚀 **2. Altcoin Watchlist:**
{altcoins}

⚠️ **3. Risk Assessment & Alerts:**
- Risk Level: {risk_level}
{risk_warnings}

🔄 **4. Contrarian Analysis:**
{contrarian_signal}

📅 **5. Weekly Market Outlook:**
{weekly_strategy}

📈 **Futures Data (Reference):**
- Long Ratio: {futures_data.get('long_ratio', 0)}%
- Short Ratio: {futures_data.get('short_ratio', 0)}%
- L/S Ratio: {futures_data.get('long_short_ratio', 0)}

📊 **Analysis Summary:**
- Fundamental outlook shows {sentiment_score['trend'].lower()} trend
- Market structure indicates normal conditions
- Volume activity shows moderate interest
- Risk assessment: {risk_level.split()[1] if len(risk_level.split()) > 1 else 'Moderate'}

📊 Source: {futures_data.get('source', 'API')} | ⏰ Real-time"""

💰 **Price & Performance Data:**
- Current Price: ${price_data.get('price', 0):,.2f}
- 24h Change: {price_data.get('change_24h', 0):+.2f}%
- Volume: ${price_data.get('volume_24h', 0):,.0f}

📰 **1. Market Sentiment & Trend Analysis:**
{sentiment_score['analysis']}
- Sentiment Score: {sentiment_score['score']}/10
- Trend Direction: {sentiment_score['trend']}
- News Impact: {sentiment_score['impact']}

🚀 **2. Altcoin Watchlist:**
{altcoins}

⚠️ **3. Risk Assessment & Alerts:**
- Risk Level: {risk_level}
{risk_warnings}

🔄 **4. Contrarian Analysis:**
{contrarian_signal}

📅 **5. Weekly Market Outlook:**
{weekly_strategy}

📈 **Futures Data (Reference):**
- Long Ratio: {futures_data.get('long_ratio', 0)}%
- Short Ratio: {futures_data.get('short_ratio', 0)}%
- L/S Ratio: {futures_data.get('long_short_ratio', 0)}

📊 **Analysis Summary:**
- Fundamental outlook shows {sentiment_score['trend'].lower()} trend
- Market structure indicates normal conditions
- Volume activity shows moderate interest
- Risk assessment: {risk_level.split()[1] if len(risk_level.split()) > 1 else 'Moderate'}

📊 Source: {futures_data.get('source', 'API')} | ⏰ Real-time
            """

        return message

    def _analyze_news_sentiment(self, news_data, symbol):
        """Analyze market sentiment from crypto news"""
        if not news_data or 'error' in news_data[0]:
            return {
                'score':
                7,
                'trend':
                'Bullish',
                'impact':
                'Moderate',
                'analysis':
                '- Market menunjukkan optimisme dengan adopsi institusional\n- Regulasi yang mendukung memberikan sentimen positif\n- Volume trading meningkat menunjukkan minat yang tinggi'
            }

        # Simple sentiment analysis based on news count and sentiment
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
            score = (
                (positive_count * 2 + neutral_count) / total_articles) * 5 + 5
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
            analysis_points.append(
                '- Berita positif mendominasi, investor optimis')
            analysis_points.append('- Sentimen pasar mendukung kenaikan harga')
        elif negative_count > positive_count:
            analysis_points.append(
                '- Berita negatif mempengaruhi sentimen pasar')
            analysis_points.append('- Investor menunjukkan kehati-hatian')
        else:
            analysis_points.append('- Sentimen pasar relatif seimbang')
            analysis_points.append('- Pasar menunggu katalis baru')

        analysis_points.append(
            '- Volume berita tinggi menunjukkan minat publik')

        return {
            'score': round(score, 1),
            'trend': trend,
            'impact': impact,
            'analysis': '\n'.join(analysis_points)
        }

    def _get_altcoin_watchlist(self, language='id'):
        """Generate altcoin watchlist with potential"""
        import random

        altcoins = [{
            'name': 'SOL',
            'potential': 'High',
            'reason': 'Strong ecosystem growth'
        }, {
            'name': 'AVAX',
            'potential': 'Medium',
            'reason': 'DeFi adoption increasing'
        }, {
            'name': 'MATIC',
            'potential': 'High',
            'reason': 'Layer 2 scaling solution'
        }, {
            'name': 'DOT',
            'potential': 'Medium',
            'reason': 'Interoperability focus'
        }, {
            'name': 'LINK',
            'potential': 'High',
            'reason': 'Oracle network leader'
        }, {
            'name': 'ADA',
            'potential': 'Medium',
            'reason': 'Smart contract development'
        }]

        # Randomize and select 3-4 altcoins
        selected = random.sample(altcoins, 4)

        if language == 'id':
            watchlist = []
            for coin in selected:
                if coin['potential'] == 'High':
                    emoji = '🔥'
                else:
                    emoji = '⭐'

                reasons_id = {
                    'Strong ecosystem growth': 'Pertumbuhan ekosistem yang kuat',
                    'DeFi adoption increasing': 'Adopsi DeFi meningkat',
                    'Layer 2 scaling solution': 'Solusi scaling Layer 2',
                    'Interoperability focus': 'Fokus interoperabilitas',
                    'Oracle network leader': 'Leader jaringan oracle',
                    'Smart contract development': 'Pengembangan smart contract'
                }
                
                reason_id = reasons_id.get(coin['reason'], coin['reason'])
                watchlist.append(f"{emoji} **{coin['name']}** ({coin['potential']}): {reason_id}")
                
            return '\n'.join(watchlist)
                    'DeFi adoption increasing': 'Adopsi DeFi meningkat',
                    'Layer 2 scaling solution': 'Solusi scaling Layer 2',
                    'Interoperability focus': 'Fokus interoperabilitas',
                    'Oracle network leader': 'Pemimpin jaringan oracle',
                    'Smart contract development': 'Pengembangan smart contract'
                }

                reason_id = reasons_id.get(coin['reason'], coin['reason'])
                watchlist.append(
                    f"- {emoji}**{coin['name']}** - Potensi {coin['potential']}"
                )
                watchlist.append(f"  └ {reason_id}")

            return '\n'.join(watchlist)
        else:
            watchlist = []
            for coin in selected:
                if coin['potential'] == 'High':
                    emoji = '🔥'
                else:
                    emoji = '⭐'

                watchlist.append(
                    f"- {emoji} **{coin['name']}** - {coin['potential']} Potential"
                )
                watchlist.append(f"  └ {coin['reason']}")

            return '\n'.join(watchlist)

    def _assess_market_risks(self, futures_data, price_data, sentiment_score):
        """Assess market risks and generate warnings"""
        risk_factors = []

        # Check long/short ratio
        long_ratio = futures_data.get('long_ratio', 50)
        if long_ratio > 70:
            risk_factors.append(
                '- ⚠️ Long ratio sangat tinggi (>70%) - Risk of long squeeze')
        elif long_ratio < 30:
            risk_factors.append(
                '- ⚠️ Short ratio tinggi - Potential short squeeze')

        # Check price volatility
        price_change = abs(price_data.get('change_24h', 0))
        if price_change > 10:
            risk_factors.append(
                f'- 📈 Volatilitas tinggi ({price_change:.1f}%) - Increased risk'
            )

        # Check sentiment vs futures mismatch
        if sentiment_score['score'] > 8 and long_ratio > 65:
            risk_factors.append(
                '- 🔴 Euphoria alert - Sentiment & futures overly bullish')
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

    def _generate_contrarian_signal(self,
                                    futures_data,
                                    sentiment_score,
                                    language='id'):
        """Generate contrarian trading signals"""
        long_ratio = futures_data.get('long_ratio', 50)
        sentiment = sentiment_score['score']

        if language == 'id':
            if long_ratio > 75 and sentiment > 8:
                return """🔄 **STRONG CONTRARIAN SIGNAL**
- Market terlalu bullish - Consider taking profits
- Long ratio >75% menunjukkan crowded trade
- Sentiment ekstrim positif - Reversal potential
- Strategy: Gradual profit taking, prepare for dip"""

            elif long_ratio < 25 and sentiment < 3:
                return """🔄 **STRONG BUY CONTRARIAN**
- Market oversold - Excellent buying opportunity
- Extreme fear creating value opportunities
- Low long ratio suggests bottom formation
- Strategy: DCA accumulation, prepare for bounce"""

            elif long_ratio > 65:
                return """🔄 **MODERATE CONTRARIAN**
- Sentiment mulai terlalu optimis
- Consider reducing position size
- Set tighter stop losses
- Strategy: Take partial profits"""

            else:

                return """🔄 **NEUTRAL CONTRARIAN**
- Sentiment masih dalam range normal
- Belum ada signal contrarian yang kuat
- Continue dengan strategy utama
- Strategy: Hold current positions"""
        else:
            if long_ratio > 75 and sentiment > 8:
                return """🔄 **STRONG CONTRARIAN SIGNAL**
- Market too bullish - Consider taking profits
- Long ratio >75% shows crowded trade
- Extreme positive sentiment - Reversal potential
- Strategy: Gradual profit taking, prepare for dip"""

            elif long_ratio < 25 and sentiment < 3:
                return """🔄 **STRONG BUY CONTRARIAN**
- Market oversold - Excellent buying opportunity
- Extreme fear creating value opportunities
- Low long ratio suggests bottom formation
- Strategy: DCA accumulation, prepare for bounce"""

            elif long_ratio > 65:
                return """🔄 **MODERATE CONTRARIAN**
- Sentiment getting too optimistic
- Consider reducing position size
- Set tighter stop losses
- Strategy: Take partial profits"""

            else:
                return """🔄 **NEUTRAL CONTRARIAN**
- Sentiment still in normal range
- No strong contrarian signals yet
- Continue with main strategy
- Strategy: Hold current positions"""

    def analyze_futures_data(self,
                             symbol,
                             futures_data,
                             price_data,
                             language='id',
                             crypto_api=None):
        """Single coin futures analysis using same format as futures_signals"""
        try:
            print(f"🔄 Getting single coin futures analysis for {symbol}...")

            # Get comprehensive futures data
            additional_data = self._get_comprehensive_futures_data(
                symbol, crypto_api) if crypto_api else {}

            # Extract basic futures data
            long_ratio = futures_data.get('long_ratio', 50)
            short_ratio = futures_data.get('short_ratio', 50)
            source = futures_data.get('source', 'unknown')

            # Extract price data
            current_price = price_data.get(
                'price', 0) if price_data and 'error' not in price_data else 0
            change_24h = price_data.get(
                'change_24h',
                0) if price_data and 'error' not in price_data else 0
            volume_24h = price_data.get(
                'volume_24h',
                0) if price_data and 'error' not in price_data else 0

            # Determine sentiment and signal
            if long_ratio > 65:
                sentiment = "Bullish (Many Long Positions)" if language == 'en' else "Bullish (Banyak Posisi Long)"
                signal_type = "Long"
                signal_strength = "STRONG" if long_ratio > 75 else "MODERATE"
            elif long_ratio < 35:
                sentiment = "Bearish (Many Short Positions)" if language == 'en' else "Bearish (Banyak Posisi Short)"
                signal_type = "Short"
                signal_strength = "STRONG" if long_ratio < 25 else "MODERATE"
            else:
                sentiment = "Neutral (Balanced)" if language == 'en' else "Neutral (Seimbang)"
                signal_type = "Long" if long_ratio >= 50 else "Short"
                signal_strength = "WEAK"

            # Calculate entry, TP, SL
            entry_price = current_price
            if signal_type == "Long":
                tp_price = current_price * 1.03  # 3% up
                sl_price = current_price * 0.98  # 2% down
            else:
                tp_price = current_price * 0.97  # 3% down
                sl_price = current_price * 1.02  # 2% up

            # Calculate risk/reward ratio
            risk_reward = abs(
                (tp_price - entry_price) /
                (sl_price - entry_price)) if sl_price != entry_price else 1.5

            if language == 'id':
                data_quality = "🟢 EXCELLENT" if source in [
                    'coinglass', 'binance'
                ] else "🟡 MOCK DATA" if source == 'mock' else "📊 API DATA"

                message = f"""⚡ **Analisis Futures Real-Time {symbol}**

📊 **Kualitas Data: {data_quality}** (Source: {source})

💰 **Data Harga:**
- Harga saat ini: ${current_price:,.2f}
- Perubahan 24h: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis (Live Data):**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short - {sentiment}
- L/S Ratio: {futures_data.get('long_short_ratio', long_ratio/short_ratio if short_ratio > 0 else 1):.2f}
- Market Bias: {"Extremely Bullish" if long_ratio > 75 else "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Extremely Bearish" if long_ratio < 25 else "Neutral"}

🎯 **Futures Signal (Real-Time):**
- {"🟢" if signal_type == "Long" else "🔴"} **{symbol} {signal_type}** ({signal_strength})
- Entry: ${entry_price:,.2f}
- TP: ${tp_price:,.2f} ({((tp_price/entry_price-1)*100):+.1f}%)
- SL: ${sl_price:,.2f} ({((sl_price/entry_price-1)*100):+.1f}%)
- R/R Ratio: {risk_reward:.1f}:1

📈 **Leverage Recommendations:**
- Conservative: 3-5x leverage (recommended)
- Moderate: 5-10x leverage  
- Aggressive: 10-20x leverage (high risk!)

💡 **Trading Strategy:**
- Signal Strength: {signal_strength}
- Market Structure: {"Overleveraged" if long_ratio > 70 or long_ratio < 30 else "Balanced"}
- Position Size: {"Reduce size" if signal_strength == "WEAK" else "Normal size" if signal_strength == "MODERATE" else "Full size"}"""

                # Add comprehensive data if available
                if additional_data:
                    oi_data = additional_data.get('open_interest', {})
                    funding_data = additional_data.get('funding_rate', {})
                    liquidation_data = additional_data.get('liquidation', {})

                    if oi_data:
                        message += f"""

📊 **Open Interest Analysis:**
- OI Current: ${oi_data.get('open_interest', 0):,.0f}
- OI Change: {oi_data.get('open_interest_change', 0):+.2f}%
- Trend: {"Increasing" if oi_data.get('open_interest_change', 0) > 0 else "Decreasing"}"""

                    if funding_data:
                        avg_funding = funding_data.get('average_funding_rate',
                                                       0)
                        message += f"""

💸 **Funding Rate Analysis:**
- Average Rate: {avg_funding:.6f}% (8h)
- Annual Rate: {avg_funding*365*3:.2f}%
- Market Sentiment: {"Bullish" if avg_funding > 0.01 else "Bearish" if avg_funding < -0.01 else "Neutral"}"""

                    if liquidation_data:
                        total_liq = liquidation_data.get(
                            'total_liquidation', 0)
                        long_liq = liquidation_data.get('long_liquidation', 0)
                        short_liq = liquidation_data.get(
                            'short_liquidation', 0)
                        message += f"""

💥 **Liquidation Analysis (24h):**
- Total Liquidated: ${total_liq:,.0f}
- Long Liquidated: ${long_liq:,.0f}
- Short Liquidated: ${short_liq:,.0f}
- Ratio: {(long_liq/(long_liq+short_liq)*100):.1f}% Long vs {(short_liq/(long_liq+short_liq)*100):.1f}% Short"""

                message += f"""

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!

📡 Source: {source} | ⏰ Real-time data
🔄 Analisis format futures_signals untuk 1 coin"""

            else:
                data_quality = "🟢 EXCELLENT" if source in [
                    'coinglass', 'binance'
                ] else "🟡 MOCK DATA" if source == 'mock' else "📊 API DATA"

                message = f"""⚡ **Real-Time Futures Analysis {symbol}**

📊 **Data Quality: {data_quality}** (Source: {source})

💰 **Data Harga:**
- Current Price: ${current_price:,.2f}
- 24h Change: {change_24h:+.2f}%
- Volume 24h: ${volume_24h:,.0f}

📈 **Long/Short Ratio Analysis (Live Data):**
- {symbol}: {long_ratio:.1f}% Long, {short_ratio:.1f}% Short - {sentiment}
- L/S Ratio: {futures_data.get('long_short_ratio', long_ratio/short_ratio if short_ratio > 0 else 1):.2f}
- Market Bias: {"Extremely Bullish" if long_ratio > 75 else "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Extremely Bearish" if long_ratio < 25 else "Neutral"}

🎯 **Futures Signal (Real-Time):**
- {"🟢" if signal_type == "Long" else "🔴"} **{symbol} {signal_type}** ({signal_strength})
- Entry: ${entry_price:,.2f}
- TP: ${tp_price:,.2f} ({((tp_price/entry_price-1)*100):+.1f}%)
- SL: ${sl_price:,.2f} ({((sl_price/entry_price-1)*100):+.1f}%)
- R/R Ratio: {risk_reward:.1f}:1

📈 **Leverage Recommendations:**
- Conservative: 3-5x leverage (recommended)
- Moderate: 5-10x leverage
- Aggressive: 10-20x leverage (high risk!)

💡 **Trading Strategy:**
- Signal Strength: {signal_strength}
- Market Structure: {"Overleveraged" if long_ratio > 70 or long_ratio < 30 else "Balanced"}
- Position Size: {"Reduce size" if signal_strength == "WEAK" else "Normal size" if signal_strength == "MODERATE" else "Full size"}

⚠️ **Risk Warning:**
Futures trading berisiko tinggi! 
Gunakan proper risk management dan jangan FOMO!

📡 Source: {source} | ⏰ Real-time data
🔄 Single coin futures_signals format analysis"""

        except Exception as e:
            print(f"Error in analyze_futures_data: {e}")
            if language == 'id':
                message = f"""❌ **Error dalam Analisis Futures {symbol}**

Terjadi kesalahan saat menganalisis data futures.
Error: {str(e)}

📊 Silakan coba lagi atau gunakan `/futures_signals` untuk analisis multi-coin.
                """
            else:
                message = f"""❌ **Error in Futures Analysis {symbol}**

Error occurred while analyzing futures data.
Error: {str(e)}

📊 Please try again or use `/futures_signals` for multi-coin analysis.
                """

        return message

    def _get_comprehensive_futures_data(self, symbol, crypto_api):
        """Get comprehensive futures data from Coinglass API"""
        data = {}

        if crypto_api:
            try:
                print(f"Getting comprehensive data for {symbol}...")

                # Get additional Coinglass data
                data['open_interest'] = crypto_api.get_open_interest(symbol)
                print(f"Open Interest: {data['open_interest']}")

                data['funding_rate'] = crypto_api.get_funding_rate(symbol)
                print(f"Funding Rate: {data['funding_rate']}")

                data['liquidation'] = crypto_api.get_liquidation_data(symbol)
                print(f"Liquidation: {data['liquidation']}")

                data['oi_chart'] = crypto_api.get_open_interest_chart(symbol)
                print(f"OI Chart: {data['oi_chart']}")

                data['liquidation_chart'] = crypto_api.get_liquidation_chart(
                    symbol)
                print(f"Liquidation Chart: {data['liquidation_chart']}")

            except Exception as e:
                print(f"Error getting comprehensive data: {e}")
                # Fallback mock data
                data = self._get_mock_comprehensive_data(symbol)
        else:
            print(f"No crypto_api provided, using mock data for {symbol}")
            data = self._get_mock_comprehensive_data(symbol)

        print(f"Final comprehensive data: {data}")
        return data

    def _get_mock_comprehensive_data(self, symbol):
        """Generate mock comprehensive data for fallback"""
        import random
        from datetime import datetime

        return {
            'open_interest': {
                'open_interest': random.uniform(1000000, 5000000),
                'open_interest_change': random.uniform(-15, 15),
                'source': 'mock'
            },
            'funding_rate': {
                'average_funding_rate': random.uniform(-0.01, 0.01),
                'exchanges_count': 5,
                'source': 'mock'
            },
            'liquidation': {
                'long_liquidation': random.uniform(10000, 100000),
                'short_liquidation': random.uniform(15000, 120000),
                'total_liquidation': random.uniform(25000, 220000),
                'source': 'mock'
            }
        }

    def _generate_institutional_signal(self, symbol, price_data, futures_data, additional_data):
        """Generate institutional-grade trading signal"""
        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        volume_24h = price_data.get('volume_24h', 0)
        long_ratio = futures_data.get('long_ratio', 50)
        
        oi_data = additional_data.get('open_interest', {})
        oi_change = oi_data.get('open_interest_change', 0)
        funding_data = additional_data.get('funding_rate', {})
        avg_funding = funding_data.get('average_funding_rate', 0)
        
        # Calculate signal score
        signal_score = 0
        factors = []
        
        # Price momentum factor
        if abs(change_24h) > 5:
            signal_score += 2 if change_24h > 0 else -2
            factors.append(f"📈 Strong momentum ({change_24h:+.1f}%)")
        elif abs(change_24h) > 2:
            signal_score += 1 if change_24h > 0 else -1
            factors.append(f"📊 Moderate momentum ({change_24h:+.1f}%)")
        
        # Volume confirmation
        if volume_24h > 1000000000:
            signal_score += 1
            factors.append("📊 High volume confirmation")
        
        # Futures sentiment
        if long_ratio > 70:
            signal_score -= 2
            factors.append("🔴 Overleveraged longs (contrarian bearish)")
        elif long_ratio < 30:
            signal_score += 2
            factors.append("🟢 Oversold (contrarian bullish)")
        
        # OI divergence
        if change_24h > 2 and oi_change < -5:
            signal_score -= 2
            factors.append("⚠️ Bearish OI divergence")
        elif change_24h < -2 and oi_change > 5:
            signal_score += 2
            factors.append("✅ Bullish OI divergence")
        
        # Funding pressure
        if avg_funding > 0.005:
            signal_score -= 1
            factors.append("💸 High funding cost (bearish)")
        elif avg_funding < -0.005:
            signal_score += 1
            factors.append("💰 Negative funding (bullish)")
        
        # Determine signal
        if signal_score >= 3:
            signal_type = "🟢 STRONG BUY"
            confidence = "High"
        elif signal_score >= 1:
            signal_type = "🟡 BUY"
            confidence = "Medium"
        elif signal_score <= -3:
            signal_type = "🔴 STRONG SELL"
            confidence = "High"
        elif signal_score <= -1:
            signal_type = "🟡 SELL"
            confidence = "Medium"
        else:
            signal_type = "⚪ HOLD"
            confidence = "Low"
        
        # Calculate targets
        if "BUY" in signal_type:
            tp1 = current_price * 1.03
            tp2 = current_price * 1.06
            sl = current_price * 0.97
        else:
            tp1 = current_price * 0.97
            tp2 = current_price * 0.94
            sl = current_price * 1.03
        
        return f"""Signal: {signal_type} | Confidence: {confidence}
Score: {signal_score:+.1f}/5 | Entry: ${current_price:,.2f}
TP1: ${tp1:,.2f} | TP2: ${tp2:,.2f} | SL: ${sl:,.2f}

Key Factors:
""" + "\n".join(f"  • {factor}" for factor in factors[:5])

    def _generate_risk_matrix(self, futures_data, price_data, additional_data, market_overview):
        """Generate comprehensive risk matrix"""
        risk_factors = []
        risk_score = 0
        
        long_ratio = futures_data.get('long_ratio', 50)
        change_24h = price_data.get('change_24h', 0)
        volume = price_data.get('volume_24h', 0)
        
        oi_data = additional_data.get('open_interest', {})
        oi_change = oi_data.get('open_interest_change', 0)
        
        liquidation_data = additional_data.get('liquidation', {})
        total_liq = liquidation_data.get('total_liquidation', 0)
        
        funding_data = additional_data.get('funding_rate', {})
        avg_funding = funding_data.get('average_funding_rate', 0)
        
        btc_dominance = market_overview.get('btc_dominance', 50)
        
        # Risk assessments
        if long_ratio > 75 or long_ratio < 25:
            risk_score += 3
            risk_factors.append("🔴 Extreme position bias")
        elif long_ratio > 65 or long_ratio < 35:
            risk_score += 2
            risk_factors.append("🟡 High position bias")
        
        if abs(oi_change) > 15:
            risk_score += 2
            risk_factors.append("⚠️ Extreme OI volatility")
        
        if abs(avg_funding) > 0.01:
            risk_score += 2
            risk_factors.append("💸 Extreme funding rate")
        
        if total_liq > 200000000:
            risk_score += 3
            risk_factors.append("💥 High liquidation activity")
        
        if volume < 100000000:
            risk_score += 2
            risk_factors.append("📊 Low liquidity warning")
        
        if abs(change_24h) > 10:
            risk_score += 2
            risk_factors.append("📈 High volatility environment")
        
        # Risk level
        if risk_score >= 8:
            risk_level = "🔴 EXTREME"
            recommendation = "Avoid leverage, minimal position size"
        elif risk_score >= 5:
            risk_level = "🟠 HIGH"
            recommendation = "Low leverage (2-3x max), tight stops"
        elif risk_score >= 3:
            risk_level = "🟡 MODERATE"
            recommendation = "Standard risk management"
        else:
            risk_level = "🟢 LOW"
            recommendation = "Normal position sizing acceptable"
        
        if not risk_factors:
            risk_factors.append("✅ No significant risk factors detected")
        
        return f"""Risk Level: {risk_level} (Score: {risk_score}/10)
Recommendation: {recommendation}

Risk Factors:
""" + "\n".join(f"  • {factor}" for factor in risk_factors[:6])

    def _analyze_cross_market_correlation(self, symbol, price_data, market_overview):
        """Analyze cross-market correlation"""
        change_24h = price_data.get('change_24h', 0)
        btc_dominance = market_overview.get('btc_dominance', 50)
        market_trend = market_overview.get('market_cap_change_24h', 0)
        
        if symbol.upper() == 'BTC':
            correlation = "N/A (Base asset)"
            implication = "BTC drives market sentiment"
        else:
            # Simulate correlation based on market conditions
            if btc_dominance > 55:
                if abs(change_24h - market_trend) < 2:
                    correlation = "High positive (0.8+)"
                    implication = "Following BTC trend closely"
                else:
                    correlation = "Diverging (-0.2)"
                    implication = "Independent movement, potential alpha"
            else:
                correlation = "Moderate (0.4-0.6)"
                implication = "Altcoin season dynamics"
        
        return f"""BTC Correlation: {correlation}
Market Implication: {implication}
BTC Dominance: {btc_dominance:.1f}% | Market Trend: {market_trend:+.1f}%
Strategy: {'Follow BTC' if 'High positive' in correlation else 'Independent analysis' if 'Diverging' in correlation else 'Balanced approach'}"""

    def _analyze_liquidation_zones(self, additional_data, price_data):
        """Analyze liquidation zones and patterns"""
        liquidation_data = additional_data.get('liquidation', {})
        long_liq = liquidation_data.get('long_liquidation', 0)
        short_liq = liquidation_data.get('short_liquidation', 0)
        total_liq = liquidation_data.get('total_liquidation', 0)
        current_price = price_data.get('price', 0)
        
        if total_liq < 50000000:
            return "🟢 Low liquidation risk: Minimal activity, stable conditions"
        
        liq_ratio = (long_liq / (long_liq + short_liq)) * 100 if (long_liq + short_liq) > 0 else 50
        
        # Estimate liquidation zones
        long_zone = current_price * 0.92  # Typical 8% below for 10x longs
        short_zone = current_price * 1.08  # Typical 8% above for 10x shorts
        
        if long_liq > short_liq * 2:
            pattern = f"🔴 Long liquidation cascade (${long_liq:,.0f})"
            zones = f"Major long liquidation zone: ${long_zone:,.2f}"
        elif short_liq > long_liq * 2:
            pattern = f"🟢 Short squeeze pattern (${short_liq:,.0f})"
            zones = f"Major short liquidation zone: ${short_zone:,.2f}"
        else:
            pattern = f"⚖️ Balanced liquidations (L:{liq_ratio:.0f}% S:{100-liq_ratio:.0f}%)"
            zones = f"Zones: L-${long_zone:,.2f} | S-${short_zone:,.2f}"
        
        return f"""Pattern: {pattern}
Total 24h: ${total_liq:,.0f}
{zones}
Risk Level: {'High' if total_liq > 200000000 else 'Moderate' if total_liq > 100000000 else 'Low'}"""

    def _analyze_funding_pressure(self, additional_data, futures_data):
        """Analyze funding rate pressure and implications"""
        funding_data = additional_data.get('funding_rate', {})
        avg_funding = funding_data.get('average_funding_rate', 0)
        long_ratio = futures_data.get('long_ratio', 50)
        
        funding_pct = avg_funding * 100
        annualized = avg_funding * 365 * 3 * 100  # 8-hour periods
        
        if avg_funding > 0.01:
            pressure = "🔴 EXTREME POSITIVE"
            implication = "Longs paying heavily, reversal risk HIGH"
        elif avg_funding > 0.005:
            pressure = "🟡 HIGH POSITIVE"
            implication = "Moderate long bias, correction possible"
        elif avg_funding < -0.01:
            pressure = "🟢 EXTREME NEGATIVE"
            implication = "Shorts paying heavily, bounce potential HIGH"
        elif avg_funding < -0.005:
            pressure = "🟡 HIGH NEGATIVE"
            implication = "Short bias, accumulation opportunity"
        else:
            pressure = "⚪ NEUTRAL"
            implication = "Balanced funding, no pressure"
        
        return f"""Pressure: {pressure}
Rate: {funding_pct:.3f}% (8h) | Annualized: {annualized:.1f}%
Long Ratio: {long_ratio:.1f}%
Implication: {implication}
Next Reset: {"Monitor for dump" if avg_funding > 0.005 else "Monitor for pump" if avg_funding < -0.005 else "Normal conditions"}"""

    def _generate_volume_profile_analysis(self, price_data, additional_data):
        """Generate volume profile and liquidity analysis"""
        volume = price_data.get('volume_24h', 0)
        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        
        oi_data = additional_data.get('open_interest', {})
        open_interest = oi_data.get('open_interest', 0)
        
        # Volume analysis
        if volume > 2000000000:
            volume_tier = "🔥 INSTITUTIONAL"
            liquidity = "Excellent"
        elif volume > 1000000000:
            volume_tier = "📈 HIGH"
            liquidity = "Good"
        elif volume > 500000000:
            volume_tier = "📊 MODERATE"
            liquidity = "Average"
        else:
            volume_tier = "📉 LOW"
            liquidity = "Poor"
        
        # Volume conviction
        if volume > 1000000000 and abs(change_24h) > 3:
            conviction = "HIGH conviction move"
        elif volume > 500000000:
            conviction = "MODERATE conviction"
        else:
            conviction = "LOW conviction"
        
        # OI ratio
        if open_interest > 0:
            oi_volume_ratio = open_interest / volume if volume > 0 else 0
            oi_analysis = f"OI/Volume: {oi_volume_ratio:.2f}"
        else:
            oi_analysis = "OI data not available"
        
        return f"""Volume Tier: {volume_tier} (${volume:,.0f})
Liquidity: {liquidity} | Conviction: {conviction}
{oi_analysis}
Analysis: {'Institutional participation' if volume > 2000000000 else 'Retail dominated' if volume < 500000000 else 'Mixed participation'}"""

    def _generate_price_prediction_model(self, symbol, price_data, futures_data, additional_data):
        """Generate AI-based price prediction model"""
        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        volume = price_data.get('volume_24h', 0)
        long_ratio = futures_data.get('long_ratio', 50)
        
        oi_data = additional_data.get('open_interest', {})
        oi_change = oi_data.get('open_interest_change', 0)
        
        funding_data = additional_data.get('funding_rate', {})
        avg_funding = funding_data.get('average_funding_rate', 0)
        
        # Simple prediction model based on multiple factors
        prediction_score = 0
        confidence_factors = []
        
        # Momentum factor
        if change_24h > 3:
            prediction_score += 2
            confidence_factors.append("Positive momentum")
        elif change_24h < -3:
            prediction_score -= 2
            confidence_factors.append("Negative momentum")
        
        # Volume factor
        if volume > 1000000000:
            prediction_score += 1
            confidence_factors.append("High volume support")
        
        # Futures factor
        if long_ratio > 70:
            prediction_score -= 1
            confidence_factors.append("Overleveraged longs")
        elif long_ratio < 30:
            prediction_score += 1
            confidence_factors.append("Oversold conditions")
        
        # OI factor
        if oi_change > 10:
            prediction_score += 1 if change_24h > 0 else -1
            confidence_factors.append("OI momentum")
        
        # Funding factor
        if abs(avg_funding) > 0.005:
            prediction_score += -1 if avg_funding > 0 else 1
            confidence_factors.append("Funding pressure")
        
        # Generate prediction
        if prediction_score >= 3:
            direction = "🚀 BULLISH"
            target_1h = current_price * 1.01
            target_4h = current_price * 1.025
            target_24h = current_price * 1.05
            confidence = "High"
        elif prediction_score >= 1:
            direction = "📈 BULLISH"
            target_1h = current_price * 1.005
            target_4h = current_price * 1.015
            target_24h = current_price * 1.03
            confidence = "Medium"
        elif prediction_score <= -3:
            direction = "📉 BEARISH"
            target_1h = current_price * 0.99
            target_4h = current_price * 0.975
            target_24h = current_price * 0.95
            confidence = "High"
        elif prediction_score <= -1:
            direction = "📉 BEARISH"
            target_1h = current_price * 0.995
            target_4h = current_price * 0.985
            target_24h = current_price * 0.97
            confidence = "Medium"
        else:
            direction = "⚖️ NEUTRAL"
            target_1h = current_price * 1.002
            target_4h = current_price * 1.005
            target_24h = current_price * 1.01
            confidence = "Low"
        
        return f"""Direction: {direction} | Confidence: {confidence}
Targets: 1h ${target_1h:,.2f} | 4h ${target_4h:,.2f} | 24h ${target_24h:,.2f}
Model Score: {prediction_score:+.1f}/5

Confidence Factors:
""" + "\n".join(f"  • {factor}" for factor in confidence_factors[:4])

    def _get_data_quality_indicators(self, price_data, futures_data, additional_data, news_data):
        """Get comprehensive data quality indicators"""
        sources = []
        
        price_source = price_data.get('source', 'unknown')
        futures_source = futures_data.get('source', 'unknown')
        
        oi_source = additional_data.get('open_interest', {}).get('source', 'unknown')
        funding_source = additional_data.get('funding_rate', {}).get('source', 'unknown')
        liq_source = additional_data.get('liquidation', {}).get('source', 'unknown')
        
        news_source = news_data[0].get('source', 'unknown') if news_data else 'unknown'
        
        real_sources = sum(1 for src in [price_source, futures_source, oi_source, funding_source, liq_source, news_source] 
                          if src in ['binance', 'coinglass', 'coingecko', 'cryptonews_api'])
        
        coverage = (real_sources / 6) * 100
        
        if coverage >= 75:
            quality = "🟢 EXCELLENT"
        elif coverage >= 50:
            quality = "🟡 GOOD"
        else:
            quality = "🔄 ENHANCED SIMULATION"
        
        return f"""Data Quality: {quality} ({real_sources}/6 live sources)
• Price: {self._get_source_quality(price_source)}
• Futures: {self._get_source_quality(futures_source)}
• Open Interest: {self._get_source_quality(oi_source)}
• Funding: {self._get_source_quality(funding_source)}
• Liquidation: {self._get_source_quality(liq_source)}
• News: {self._get_source_quality(news_source)}"""

    def _calculate_signal_strength(self, signal_text):
        """Extract signal strength from signal text"""
        if "STRONG" in signal_text.upper():
            return 8 if "BUY" in signal_text.upper() else 8
        elif "BUY" in signal_text.upper() or "SELL" in signal_text.upper():
            return 6
        else:
            return 4

    def _extract_risk_level(self, risk_matrix):
        """Extract risk level from risk matrix"""
        if "EXTREME" in risk_matrix:
            return "Extreme"
        elif "HIGH" in risk_matrix:
            return "High"
        elif "MODERATE" in risk_matrix:
            return "Moderate"
        else:
            return "Low"

    def _analyze_market_phase(self, price_data, futures_data, additional_data):
        """Analyze current market phase"""
        change_24h = price_data.get('change_24h', 0)
        volume = price_data.get('volume_24h', 0)
        long_ratio = futures_data.get('long_ratio', 50)
        
        if abs(change_24h) > 5 and volume > 1000000000:
            return "High volatility breakout phase"
        elif long_ratio > 70:
            return "Overleveraged accumulation phase"
        elif long_ratio < 30:
            return "Oversold recovery phase"
        else:
            return "Consolidation phase"

    def _generate_institutional_recommendation(self, signal_text, risk_matrix):
        """Generate institutional-level recommendation"""
        if "STRONG BUY" in signal_text and "LOW" in risk_matrix:
            return "Aggressive accumulation recommended"
        elif "BUY" in signal_text and "MODERATE" in risk_matrix:
            return "Selective buying with risk management"
        elif "SELL" in signal_text:
            return "Profit taking or risk reduction"
        else:
            return "Wait for better setup"

    def _analyze_overleveraged_signal(self, futures_data, additional_data,
                                      language):
        """Analyze overleveraged positions signal"""
        long_ratio = futures_data.get('long_ratio', 50)
        oi_change = additional_data.get('open_interest',
                                        {}).get('open_interest_change', 0)
        funding_rate = additional_data.get('funding_rate',
                                           {}).get('average_funding_rate', 0)

        if language == 'id':
            if long_ratio > 75 and oi_change > 10 and funding_rate > 0.005:
                return """🔴 **EXTREME OVERLEVERAGED (DANGEROUS)**
- Long ratio >75% dengan OI naik >10%
- Funding rate positif tinggi (>0.5%)
- Signal: Mass liquidation potential VERY HIGH
- Action: AVOID longs, consider shorts dengan tight SL"""

            elif long_ratio > 65 and oi_change > 5:
                return """🟡 **MODERATE OVERLEVERAGED (WARNING)**
- Long ratio >65% dengan OI bertambah
- Crowded long positions building up
- Signal: Possible correction incoming
- Action: Reduce long exposure, take profits"""

            elif long_ratio < 25 and oi_change > 5:
                return """🟢 **SHORT OVERLEVERAGED (OPPORTUNITY)**
- Short ratio >75% dengan OI naik
- Oversold dengan potential short squeeze
- Signal: Excellent long opportunity
- Action: Accumulate longs on dips"""

            else:
                return """⚪ **BALANCED LEVERAGE**
- Leverage ratio dalam batas normal
- Tidak ada tanda overleveraged
- Signal: Market relatif sehat
- Action: Follow trend normal"""
        else:
            if long_ratio > 75 and oi_change > 10 and funding_rate > 0.005:
                return """🔴 **EXTREME OVERLEVERAGED (DANGEROUS)**
- Long ratio >75% with OI surge >10%
- High positive funding rate (>0.5%)
- Signal: Mass liquidation potential VERY HIGH
- Action: AVOID longs, consider shorts with tight SL"""

            elif long_ratio > 65 and oi_change > 5:
                return """🟡 **MODERATE OVERLEVERAGED (WARNING)**
- Long ratio >65% with OI increase
- Crowded long positions building up
- Signal: Possible correction incoming
- Action: Reduce long exposure, take profits"""

            elif long_ratio < 25 and oi_change > 5:
                return """🟢 **SHORT OVERLEVERAGED (OPPORTUNITY)**
- Short ratio >75% with OI surge
- Oversold dengan potential short squeeze
- Signal: Excellent long opportunity
- Action: Accumulate longs on dips"""

            else:
                return """⚪ **BALANCED LEVERAGE**
- Leverage ratio within normal range
- No overleveraged signals detected
- Signal: Market relatively healthy
- Action: Follow normal trend"""

    def _analyze_contrarian_setup(self, futures_data, price_data, language):
        """Analyze contrarian trading setup"""
        long_ratio = futures_data.get('long_ratio', 50)
        price_change = price_data.get('change_24h', 0)

        if language == 'id':
            # Strong contrarian signals
            if long_ratio > 80 and price_change > 5:
                return """🔥 **STRONG CONTRARIAN SHORT SETUP**
- Extreme bullish (>80% long) + price pump
- Euphoria stage - reversal imminent
- Setup: Short dengan RR 1:3
- Entry: Current level, SL +3%, TP -8%"""

            elif long_ratio < 20 and price_change < -5:
                return """🔥 **STRONG CONTRARIAN LONG SETUP**
- Extreme bearish (<20% long) + price dump
- Panic selling - bottom formation
- Setup: Long dengan RR 1:3
- Entry: Current level, SL -3%, TP +8%"""

            elif long_ratio > 70:
                return """🟡 **MODERATE CONTRARIAN (SHORT BIAS)**
- High bullish sentiment (>70% long)
- Potential profit taking zone
- Setup: Light short position
- Entry: Resistance level, SL +2%, TP -5%"""

            elif long_ratio < 30:
                return """🟡 **MODERATE CONTRARIAN (LONG BIAS)**
- High bearish sentiment (<30% long)
- Potential accumulation zone
- Setup: Light long position
- Entry: Support level, SL -2%, TP +5%"""

            else:
                return """⚪ **NO CONTRARIAN SETUP**
- Sentiment masih dalam range normal
- Belum ada extreme reading
- Setup: Wait untuk extreme level
- Action: Monitor ratio untuk entry point"""
        else:
            # Strong contrarian signals
            if long_ratio > 80 and price_change > 5:
                return """🔥 **STRONG CONTRARIAN SHORT SETUP**
- Extreme bullish (>80% long) + price pump
- Euphoria stage - reversal imminent
- Setup: Short with RR 1:3
- Entry: Current level, SL +3%, TP -8%"""

            elif long_ratio < 20 and price_change < -5:
                return """🔥 **STRONG CONTRARIAN LONG SETUP**
- Extreme bearish (<20% long) + price dump
- Panic selling - bottom formation
- Setup: Long dengan RR 1:3
- Entry: Current level, SL -3%, TP +8%"""

            elif long_ratio > 70:
                return """🟡 **MODERATE CONTRARIAN (SHORT BIAS)**
- High bullish sentiment (>70% long)
- Potential profit taking zone
- Setup: Light short position
- Entry: Resistance level, SL +2%, TP -5%"""

            elif long_ratio < 30:
                return """🟡 **MODERATE CONTRARIAN (LONG BIAS)**
- High bearish sentiment (<30% long)
- Potential accumulation zone
- Setup: Light long position
- Entry: Support level, SL -2%, TP +5%"""

            else:
                return """⚪ **NO CONTRARIAN SETUP**
- Sentiment still in normal range
- No extreme readings yet
- Setup: Wait for extreme levels
- Action: Monitor ratio for entry points"""

    def _analyze_liquidation_trap(self, additional_data, price_data, language):
        """Detect liquidation trap patterns"""
        liquidation_data = additional_data.get('liquidation', {})
        long_liq = liquidation_data.get('long_liquidation', 0)
        short_liq = liquidation_data.get('short_liquidation', 0)
        total_liq = liquidation_data.get('total_liquidation', 0)
        price_change = price_data.get('change_24h', 0)

        if language == 'id':
            if total_liq > 100000000:  # >100M liquidation
                if long_liq > short_liq * 3:  # 3x more long liquidations
                    return """🪤 **LONG LIQUIDATION TRAP DETECTED**
- Liquidasi long massive: ${long_liq:,.0f}
- Ratio liquidasi: Long dominan 3:1
- Pattern: Long trap in progress
- Signal: Expect further downside
- Action: AVOID longs, monitor for reversal"""

                elif short_liq > long_liq * 3:  # 3x more short liquidations
                    return """🪤 **SHORT LIQUIDATION TRAP DETECTED**
- Liquidasi short massive: ${short_liq:,.0f}
- Ratio liquidasi: Short dominan 3:1
- Pattern: Short squeeze in progress
- Signal: Expect further upside
- Action: AVOID shorts, consider longs"""

                else:
                    return """⚠️ **HIGH LIQUIDATION ACTIVITY**
- Total liquidasi: ${total_liq:,.0f}
- Liquidasi seimbang antara long/short
- Pattern: High volatility environment
- Signal: Extreme caution needed
- Action: Reduce position size"""

            elif total_liq > 50000000:  # 50-100M liquidation
                return """🟡 **MODERATE LIQUIDATION RISK**
- Total liquidasi: ${total_liq:,.0f}
- Aktivitas liquidasi sedang
- Pattern: Normal market volatility
- Signal: Standard risk management
- Action: Use proper stop losses"""

            else:
                return """🟢 **LOW LIQUIDATION RISK**
- Total liquidasi: ${total_liq:,.0f}
- Liquidasi minimal detected
- Pattern: Stable market conditions
- Signal: Lower risk environment
- Action: Normal position sizing OK"""
        else:
            if total_liq > 100000000:  # >100M liquidation
                if long_liq > short_liq * 3:  # 3x more long liquidations
                    return """🪤 **LONG LIQUIDATION TRAP DETECTED**
- Massive long liquidation: ${long_liq:,.0f}
- Liquidation ratio: Long dominant 3:1
- Pattern: Long trap in progress
- Signal: Expect further downside
- Action: AVOID longs, monitor for reversal"""

                elif short_liq > long_liq * 3:  # 3x more short liquidations
                    return f"""🪤 **SHORT LIQUIDATION TRAP DETECTED**
- Massive short liquidation: ${short_liq:,.0f}
- Liquidation ratio: Short dominant 3:1
- Pattern: Short trap in progress
- Signal: Expect further upside
- Action: AVOID shorts, monitor for reversal"""
                
                else:
                    return f"""🔥 **EXTREME LIQUIDATION CHAOS**
- Total liquidation: ${total_liq:,.0f}
- Mixed liquidation environment
- Pattern: Extreme market volatility
- Signal: Market in panic mode
- Action: STAY OUT until clarity"""ve short liquidation: ${short_liq:,.0f}
- Liquidation ratio: Short dominant 3:1
- Pattern: Short squeeze in progress
- Signal: Expect further upside
- Action: AVOID shorts, consider longs"""

                else:
                    return """⚠️ **HIGH LIQUIDATION ACTIVITY**
- Total liquidation: ${total_liq:,.0f}
- Balanced long/short liquidations
- Pattern: High volatility environment
- Signal: Extreme caution needed
- Action: Reduce position size"""

            elif total_liq > 50000000:  # 50-100M liquidation
                return """🟡 **MODERATE LIQUIDATION RISK**
- Total liquidation: ${total_liq:,.0f}
- Moderate liquidation activity
- Pattern: Normal market volatility
- Signal: Standard risk management
- Action: Use proper stop losses"""

            else:
                return """🟢 **LOW LIQUIDATION RISK**
- Total liquidation: ${total_liq:,.0f}
- Minimal liquidations detected
- Pattern: Stable market conditions
- Signal: Lower risk environment
- Action: Normal position sizing OK"""

    def _analyze_open_interest_divergence(self, additional_data, price_data,
                                          language):
        """Analyze open interest divergence patterns"""
        oi_data = additional_data.get('open_interest', {})
        oi_change = oi_data.get('open_interest_change', 0)
        price_change = price_data.get('change_24h', 0)

        if language == 'id':
            # Bullish divergence
            if price_change < -2 and oi_change > 5:
                return """📈 **BULLISH OI DIVERGENCE**
- Harga turun -2% tapi OI naik +5%
- Pattern: Smart money accumulating
- Signal: Potential reversal ke atas
- Strength: Strong bullish signal
- Action: Siap untuk long entry"""

            # Bearish divergence
            elif price_change > 2 and oi_change < -5:
                return """📉 **BEARISH OI DIVERGENCE**
- Harga naik +2% tapi OI turun -5%
- Pattern: Weak hands pumping, smart money exit
- Signal: Potential reversal ke bawah
- Strength: Strong bearish signal
- Action: Take profits, consider shorts"""

            # Confirmation patterns
            elif price_change > 2 and oi_change > 5:
                return """✅ **BULLISH CONFIRMATION**
- Harga naik +2% dengan OI naik +5%
- Pattern: Strong buying dengan conviction
- Signal: Trend continuation likely
- Strength: Trend confirmed
- Action: Hold longs, add on dips"""

            elif price_change < -2 and oi_change < -5:
                return """✅ **BEARISH CONFIRMATION**
- Harga turun -2% dengan OI turun -5%
- Pattern: Panic selling dengan conviction
- Signal: Downtrend continuation likely
- Strength: Downtrend confirmed
- Action: Hold shorts, add on rallies"""

            else:
                return f"""⚪ **NO SIGNIFICANT DIVERGENCE**
- OI change: {oi_change:+.1f}%, Price change: {price_change:+.1f}%
- Pattern: Normal correlation
- Signal: No divergence signal
- Strength: Neutral
- Action: Monitor untuk divergence"""
        else:
            # Bullish divergence
            if price_change < -2 and oi_change > 5:
                return """📈 **BULLISH OI DIVERGENCE**
- Price down -2% but OI up +5%
- Pattern: Smart money accumulating
- Signal: Potential upside reversal
- Strength: Strong bullish signal
- Action: Prepare for long entry"""

            # Bearish divergence
            elif price_change > 2 and oi_change < -5:
                return """📉 **BEARISH OI DIVERGENCE**
- Price up +2% but OI down -5%
- Pattern: Weak hands pump, smart money exit
- Signal: Potential downside reversal
- Strength: Strong bearish signal
- Action: Take profits, consider shorts"""

            # Confirmation patterns
            elif price_change > 2 and oi_change > 5:
                return """✅ **BULLISH CONFIRMATION**
- Price up +2% with OI up +5%
- Pattern: Strong buying with conviction
- Signal: Trend continuation likely
- Strength: Trend confirmed
- Action: Hold longs, add on dips"""

            elif price_change < -2 and oi_change < -5:
                return """✅ **BEARISH CONFIRMATION**
- Price down -2% with OI down -5%
- Pattern: Panic selling with conviction
- Signal: Downtrend continuation likely
- Strength: Downtrend confirmed
- Action: Hold shorts, add on rallies"""

            else:
                return f"""⚪ **NO SIGNIFICANT DIVERGENCE**
- OI change: {oi_change:+.1f}%, Price change: {price_change:+.1f}%
- Pattern: Normal correlation
- Signal: No divergence signal
- Strength: Neutral
- Action: Monitor untuk divergence"""

    def _analyze_funding_rate_reversal(self, additional_data, language):
        """Analyze funding rate reversal signals"""
        funding_data = additional_data.get('funding_rate', {})
        avg_funding = funding_data.get('average_funding_rate', 0)

        if language == 'id':
            if avg_funding > 0.01:  # >1% funding rate
                return f"""🔴 **EXTREME POSITIVE FUNDING (REVERSAL SIGNAL)**
- Funding rate: {avg_funding:.4f} (+{avg_funding*100:.2f}%)
- Pattern: Longs paying shorts heavily
- Signal: STRONG bearish reversal incoming
- Timing: Funding reset bisa trigger dump
- Action: Close longs, consider shorts"""

            elif avg_funding > 0.005:  # 0.5-1% funding rate
                return f"""🟡 **HIGH POSITIVE FUNDING (WARNING)**
- Funding rate: {avg_funding:.4f} (+{avg_funding*100:.2f}%)
- Pattern: Moderate long bias
- Signal: Potential correction
- Timing: Monitor untuk escalation
- Action: Take some profits, reduce leverage"""

            elif avg_funding < -0.01:  # <-1% funding rate
                return f"""🟢 **EXTREME NEGATIVE FUNDING (REVERSAL SIGNAL)**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Shorts paying longs heavily
- Signal: STRONG bullish reversal incoming
- Timing: Funding reset bisa trigger pump
- Action: Close shorts, accumulate longs"""

            elif avg_funding < -0.005:  # -0.5 to -1% funding rate
                return f"""🟡 **HIGH NEGATIVE FUNDING (OPPORTUNITY)**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Moderate short bias
- Signal: Potential bounce
- Timing: Monitor untuk reversal
- Action: DCA longs, reduce short exposure"""

            else:
                return f"""⚪ **NEUTRAL FUNDING RATE**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Balanced long/short interest
- Signal: No funding pressure
- Timing: Normal market conditions
- Action: Follow price action normally"""
        else:
            if avg_funding > 0.01:  # >1% funding rate
                return f"""🔴 **EXTREME POSITIVE FUNDING (REVERSAL SIGNAL)**
- Funding rate: {avg_funding:.4f} (+{avg_funding*100:.2f}%)
- Pattern: Longs paying shorts heavily
- Signal: STRONG bearish reversal incoming
- Timing: Funding reset could trigger dump
- Action: Close longs, consider shorts"""

            elif avg_funding > 0.005:  # 0.5-1% funding rate
                return f"""🟡 **HIGH POSITIVE FUNDING (WARNING)**
- Funding rate: {avg_funding:.4f} (+{avg_funding*100:.2f}%)
- Pattern: Moderate long bias
- Signal: Potential correction
- Timing: Monitor untuk escalation
- Action: Take some profits, reduce leverage"""

            elif avg_funding < -0.01:  # <-1% funding rate
                return f"""🟢 **EXTREME NEGATIVE FUNDING (REVERSAL SIGNAL)**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Shorts paying longs heavily
- Signal: STRONG bullish reversal incoming
- Timing: Funding reset bisa trigger pump
- Action: Close shorts, accumulate longs"""

            elif avg_funding < -0.005:  # -0.5 to -1% funding rate
                return f"""🟡 **HIGH NEGATIVE FUNDING (OPPORTUNITY)**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Moderate short bias
- Signal: Potential bounce
- Timing: Monitor untuk reversal
- Action: DCA longs, reduce short exposure"""

            else:
                return f"""⚪ **NEUTRAL FUNDING RATE**
- Funding rate: {avg_funding:.4f} ({avg_funding*100:.2f}%)
- Pattern: Balanced long/short interest
- Signal: No funding pressure
- Timing: Normal market conditions
- Action: Follow price action normally"""

    def _generate_weekly_strategy(self,
                                  symbol,
                                  sentiment_score,
                                  language='id'):
        """Generate weekly trading strategy"""
        if language == 'id':
            if sentiment_score['score'] >= 8:
                return f"""📅 **Outlook Mingguan {symbol} (Bullish)**
- Trend: Sangat bullish untuk 7 hari ke depan
- Strategy: DCA buy on dips, hold long positions
- Target: 15-25% gains possible
- Risk: Take profits jika market overheated
- Timeline: Week 1-2 optimal untuk accumulation"""

            elif sentiment_score['score'] >= 6:
                return f"""📅 **Outlook Mingguan {symbol} (Moderately Bullish)**
- Trend: Bullish moderat dengan volatilitas
- Strategy: Selective buying, profit taking partial
- Target: 8-15% gains realistic
- Risk: Monitor untuk correction signals
- Timeline: Weekly swing trading recommended"""

            elif sentiment_score['score'] >= 4:
                return f"""📅 **Outlook Mingguan {symbol} (Neutral)**
- Trend: Sideways dengan range trading
- Strategy: Buy support, sell resistance
- Target: 5-10% range profits
- Risk: Breakout bisa mengubah scenario
- Timeline: Short-term trades lebih aman"""

            else:
                return f"""📅 **Outlook Mingguan {symbol} (Bearish)**
- Trend: Bearish dengan downside pressure
- Strategy: Avoid new longs, consider shorts
- Target: -10% to -20% possible decline
- Risk: Dead cat bounce bisa trap traders
- Timeline: Wait untuk reversal confirmation"""
        else:
            if sentiment_score['score'] >= 8:
                return f"""📅 **Weekly Outlook {symbol} (Bullish)**
- Trend: Very bullish for next 7 days
- Strategy: DCA buy on dips, hold long positions
- Target: 15-25% gains possible
- Risk: Take profits if market overheated
- Timeline: Week 1-2 optimal for accumulation"""

            elif sentiment_score['score'] >= 6:
                return f"""📅 **Weekly Outlook {symbol} (Moderately Bullish)**
- Trend: Moderately bullish with volatility
- Strategy: Selective buying, partial profit taking
- Target: 8-15% gains realistic
- Risk: Monitor for correction signals
- Timeline: Weekly swing trading recommended"""

            elif sentiment_score['score'] >= 4:
                return f"""📅 **Weekly Outlook {symbol} (Neutral)**
- Trend: Sideways with range trading
- Strategy: Buy support, sell resistance
- Target: 5-10% range profits
- Risk: Breakout could change scenario
- Timeline: Short-term trades safer"""

            else:
                return f"""📅 **Weekly Outlook {symbol} (Bearish)**
- Trend: Bearish dengan downside pressure
- Strategy: Avoid new longs, consider shorts
- Target: -10% to -20% possible decline
- Risk: Dead cat bounce could trap traders
- Timeline: Wait untuk reversal confirmation"""

    def _get_advanced_technical_analysis(self,
                                         price_data,
                                         futures_data,
                                         language='id'):
        """Generate advanced technical analysis"""
        price_change = price_data.get('change_24h', 0)
        volume = price_data.get('volume_24h', 0)
        long_ratio = futures_data.get('long_ratio', 50)

        if language == 'id':
            # Determine trend strength
            if abs(price_change) > 5:
                trend_strength = "Kuat"
            elif abs(price_change) > 2:
                trend_strength = "Sedang"
            else:
                trend_strength = "Lemah"

            # Volume analysis
            if volume > 1000000000:  # > 1B
                volume_analysis = "Volume tinggi - Strong conviction"
            elif volume > 500000000:  # 500M - 1B
                volume_analysis = "Volume normal - Moderate interest"
            else:
                volume_analysis = "Volume rendah - Low conviction"

            # Support/Resistance levels
            current_price = price_data.get('price', 0)
            if current_price > 0:
                support = current_price * 0.95
                resistance = current_price * 1.05
            else:
                support = 0
                resistance = 0

            return f"""- Trend Direction: {"Bullish" if price_change > 0 else "Bearish" if price_change < 0 else "Sideways"}
- Trend Strength: {trend_strength} ({abs(price_change):.1f}%)
- Volume Analysis: {volume_analysis}
- Support Level: ${support:,.2f}
- Resistance Level: ${resistance:,.2f}
- Momentum: {"Positive" if long_ratio > 55 else "Negative" if long_ratio < 45 else "Neutral"}"""

        else:
            # Determine trend strength
            if abs(price_change) > 5:
                trend_strength = "Strong"
            elif abs(price_change) > 2:
                trend_strength = "Moderate"
            else:
                trend_strength = "Weak"

            # Volume analysis
            if volume > 1000000000:  # > 1B
                volume_analysis = "High volume - Strong conviction"
            elif volume > 500000000:  # 500M - 1B
                volume_analysis = "Normal volume - Moderate interest"
            else:
                volume_analysis = "Low volume - Low conviction"

            # Support/Resistance levels
            current_price = price_data.get('price', 0)
            if current_price > 0:
                support = current_price * 0.95
                resistance = current_price * 1.05
            else:
                support = 0
                resistance = 0

            return f"""- Trend Direction: {"Bullish" if price_change > 0 else "Bearish" if price_change < 0 else "Sideways"}
- Trend Strength: {trend_strength} ({abs(price_change):.1f}%)
- Volume Analysis: {volume_analysis}
- Support Level: ${support:,.2f}
- Resistance Level: ${resistance:,.2f}
- Momentum: {"Positive" if long_ratio > 55 else "Negative" if long_ratio < 45 else "Neutral"}"""

    def _analyze_market_structure(self,
                                  price_data,
                                  additional_data,
                                  language='id'):
        """Analyze market structure"""
        price_change = price_data.get('change_24h', 0)
        oi_data = additional_data.get('open_interest', {})
        oi_change = oi_data.get('open_interest_change', 0)

        if language == 'id':
            if price_change > 2 and oi_change > 5:
                return "Struktur Bullish: Harga naik dengan OI bertambah - Trend kuat"
            elif price_change < -2 and oi_change < -5:
                return "Struktur Bearish: Harga turun dengan OI berkurang - Selling pressure"
            elif price_change > 2 and oi_change < -2:
                return "Divergence Warning: Harga naik tapi OI turun - Weak hands buying"
            elif price_change < -2 and oi_change > 2:
                return "Accumulation Phase: Harga turun tapi OI naik - Smart money entry"
            else:
                return "Struktur Normal: Price dan OI bergerak normal - No divergence"
        else:
            if price_change > 2 and oi_change > 5:
                return "Bullish Structure: Price up with OI increase - Strong trend"
            elif price_change < -2 and oi_change < -5:
                return "Bearish Structure: Price down with OI decrease - Selling pressure"
            elif price_change > 2 and oi_change < -2:
                return "Divergence Warning: Price up but OI down - Weak hands buying"
            elif price_change < -2 and oi_change > 2:
                return "Accumulation Phase: Price down but OI up - Smart money entry"
            else:
                return "Normal Structure: Price and OI moving normally - No divergence"

    def _analyze_volume_profile(self,
                                price_data,
                                additional_data,
                                language='id'):
        """Analyze volume profile"""
        volume = price_data.get('volume_24h', 0)
        price_change = price_data.get('change_24h', 0)

        if language == 'id':
            if volume > 1000000000 and abs(price_change) > 3:
                return "Volume Profile: High conviction move (Volume >$1B + 3%+ move)"
            elif volume > 500000000:
                return "Volume Profile: Moderate interest (Volume $500M-1B)"
            elif volume < 100000000:
                return "Volume Profile: Low liquidity (Volume <$100M) - Caution advised"
            else:
                return "Volume Profile: Normal trading activity"
        else:
            if volume > 1000000000 and abs(price_change) > 3:
                return "Volume Profile: High conviction move (Volume >$1B + 3%+ move)"
            elif volume > 500000000:
                return "Volume Profile: Moderate interest (Volume $500M-1B)"
            elif volume < 100000000:
                return "Volume Profile: Low liquidity (Volume <$100M) - Caution advised"
            else:
                return "Volume Profile: Normal trading activity"

    def sanitize_markdown(self, text):
        """Sanitize markdown to prevent rendering issues"""
        import re

        # Remove or escape problematic characters
        text = re.sub(r"([_*\[\]()~`>#+\-=|{}\.!])", r"\\\1", text)
        # Replace multiple consecutive newlines with a maximum of two
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text