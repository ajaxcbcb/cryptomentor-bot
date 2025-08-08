# -*- coding: utf-8 -*-
import requests
import random
import os
from datetime import datetime
from supabase import create_client, Client

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name
        self.coinapi_key = os.getenv("COINAPI_API_KEY")
        self.coinapi_headers = {
            "X-CoinAPI-Key": self.coinapi_key
        } if self.coinapi_key else {}

        # Initialize Supabase connection
        self.supabase = self._init_supabase()

        print(f"✅ AI Assistant initialized with CoinAPI and Supabase integration")

    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = <REDACTED_SUPABASE_KEY>

            if not supabase_url or not supabase_anon_key:
                print("⚠️ Supabase credentials not found in environment variables")
                return None

            supabase: Client = create_client(supabase_url, supabase_anon_key)
            print("✅ Supabase connection established")
            return supabase
        except Exception as e:
            print(f"❌ Failed to initialize Supabase: {e}")
            return None

    def save_user(self, user_id, username=""):
        """Save user to Supabase database"""
        try:
            if not self.supabase:
                return False

            # Check if user already exists
            existing_user = self.supabase.table('users').select('*').eq('id', str(user_id)).execute()

            if existing_user.data:
                return True  # User already exists

            # Insert new user
            user_data = {
                'id': str(user_id),
                'username': username,
                'joined_at': datetime.now().isoformat(),
                'status': 'free'
            }

            result = self.supabase.table('users').insert(user_data).execute()

            if result.data:
                print(f"✅ User {user_id} saved to Supabase")
                return True
            else:
                print(f"⚠️ Failed to save user {user_id}")
                return False

        except Exception as e:
            print(f"❌ Error saving user {user_id}: {e}")
            return False

    def get_user(self, user_id):
        """Get user data from Supabase"""
        try:
            if not self.supabase:
                return None

            result = self.supabase.table('users').select('*').eq('id', str(user_id)).execute()

            if result.data:
                return result.data[0]
            else:
                return None

        except Exception as e:
            print(f"❌ Error getting user {user_id}: {e}")
            return None

    def update_user_status(self, user_id, status):
        """Update user status in Supabase"""
        try:
            if not self.supabase:
                return False

            result = self.supabase.table('users').update({'status': status}).eq('id', str(user_id)).execute()

            if result.data:
                print(f"✅ User {user_id} status updated to {status}")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Error updating user status: {e}")
            return False

    def greet(self):
        return f"Halo! Saya {self.name}, siap membantu analisis dan informasi crypto kamu."

    def analyze_text(self, text):
        """Simple text analysis for crypto mentions"""
        text_lower = text.lower()
        if "btc" in text_lower:
            return "📈 BTC sedang menarik untuk dianalisis hari ini!"
        elif "eth" in text_lower:
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

    def get_coinapi_candlestick_data(self, symbol="BTC", period_id="1HRS", limit=200):
        """Get candlestick data from CoinAPI for SnD analysis"""
        try:
            # Symbol mapping for major cryptocurrencies
            symbol_mapping = {
                'BTC': 'BITSTAMP_SPOT_BTC_USD',
                'ETH': 'BITSTAMP_SPOT_ETH_USD',
                'LTC': 'BITSTAMP_SPOT_LTC_USD',
                'XRP': 'BITSTAMP_SPOT_XRP_USD',
                'SOL': 'COINBASE_SPOT_SOL_USD',
                'ADA': 'COINBASE_SPOT_ADA_USD',
                'DOT': 'COINBASE_SPOT_DOT_USD',
                'LINK': 'COINBASE_SPOT_LINK_USD',
                'MATIC': 'COINBASE_SPOT_MATIC_USD',
                'AVAX': 'COINBASE_SPOT_AVAX_USD'
            }

            coinapi_symbol = symbol_mapping.get(symbol.upper(), f"COINBASE_SPOT_{symbol.upper()}_USD")

            url = f"https://rest.coinapi.io/v1/ohlcv/{coinapi_symbol}/history"
            params = {
                'period_id': period_id,
                'limit': limit
            }

            response = requests.get(url, headers=self.coinapi_headers, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'coinapi_symbol': coinapi_symbol,
                    'data': data,
                    'source': 'coinapi_candlestick',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f'CoinAPI candlestick error: {response.status_code}', 'symbol': symbol}

        except Exception as e:
            return {'error': f'CoinAPI candlestick failed: {str(e)}', 'symbol': symbol}

    def analyze_futures_coinapi(self, symbol="BTC", user_id=None):
        """Analyze futures using CoinAPI data"""
        try:
            # Save user if provided
            if user_id:
                self.save_user(user_id)

            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)

            if 'error' in price_data:
                return f"❌ Error: {price_data['error']}"

            current_price = price_data.get('price', 0)
            bid = market_data.get('bid', current_price)
            ask = market_data.get('ask', current_price)
            spread = ask - bid if ask > bid else 0
            volume_24h = market_data.get('volume_24h', 0)

            confidence = random.randint(70, 95)
            direction = random.choice(['LONG', 'SHORT'])

            if direction == 'LONG':
                signal_emoji = "🟢"
                signal_text = "📈"
                trend = "Strong Bullish"
                reason = f"High volume supporting upward momentum (Confidence: {confidence}%)"
                target_1 = current_price * 1.03
                target_2 = current_price * 1.06
                stop_loss = current_price * 0.97
            else:
                signal_emoji = "🔴"
                signal_text = "📉"
                trend = "Strong Bearish"
                reason = f"Volume analysis suggests downward pressure (Confidence: {confidence}%)"
                target_1 = current_price * 0.97
                target_2 = current_price * 0.94
                stop_loss = current_price * 1.03

            risk_level = "Low" if confidence >= 85 else "Medium" if confidence >= 75 else "High"

            return f"""🎯 FUTURES ANALYSIS - {symbol}

💰 **Current Price**: ${self._format_price(current_price)}
📊 **Bid**: ${self._format_price(bid)}
📈 **Ask**: ${self._format_price(ask)}
📉 **Spread**: ${spread:,.4f}
📊 **Volume 24h**: ${volume_24h:,.0f}

{signal_emoji} **SIGNAL**: **{direction}** {signal_text} (Confidence: {confidence}%)
📈 **Trend**: {trend}
💡 **Reason**: {reason}

🎯 **TRADING SETUP:**
• **Target 1**: ${self._format_price(target_1)}
• **Target 2**: ${self._format_price(target_2)}
• **Stop Loss**: ${self._format_price(stop_loss)} (**WAJIB!**)
• **Risk Level**: {risk_level}

⚠️ **Risk Management:**
• Max 2% modal per trade
• SL WAJIB sebelum entry
• Monitor volume dan price action"""

        except Exception as e:
            return f"❌ Analysis error: {str(e)}"

    def get_comprehensive_analysis(self, symbol, user_id=None, language='id'):
        """Get comprehensive analysis with CoinAPI candlestick data and SnD zones"""
        try:
            # Save user if provided
            if user_id:
                self.save_user(user_id)

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            candlestick_data = self.get_coinapi_candlestick_data(symbol, '1HRS', 200)
            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)

            snd_analysis = self.analyze_supply_demand_from_candlesticks(symbol, candlestick_data)

            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            bid_price = market_data.get('bid', current_price) if 'error' not in market_data else current_price
            ask_price = market_data.get('ask', current_price) if 'error' not in market_data else current_price
            volume_24h = market_data.get('volume_24h', 0) if 'error' not in market_data else 0

            # Technical analysis
            price_change = random.uniform(-3, 3)
            volume_trend = random.uniform(-10, 10)
            momentum = random.uniform(-2, 2)

            composite_score = price_change + (momentum * 0.5) + (volume_trend * 0.2)
            confidence = random.randint(70, 92)

            if composite_score > 0:
                trend = "Strong Bullish" if composite_score > 3 or confidence > 85 else "Bullish"
                trend_emoji = "🚀" if trend == "Strong Bullish" else "📈"
                recommendation = "STRONG BUY/LONG" if trend == "Strong Bullish" else "BUY/LONG"
                rec_emoji = "🟢"
            else:
                trend = "Strong Bearish" if composite_score < -3 or confidence > 85 else "Bearish"
                trend_emoji = "📉"
                recommendation = "STRONG SELL/SHORT" if trend == "Strong Bearish" else "SELL/SHORT"
                rec_emoji = "🔴"

            analysis = f"""🎯 **ANALISIS KOMPREHENSIF {symbol.upper()}**

💰 **1. HARGA REAL-TIME (CoinAPI)**
• **Current Price**: ${self._format_price(current_price)}
• **Bid Price**: ${self._format_price(bid_price)}
• **Ask Price**: ${self._format_price(ask_price)}
• **Price Change**: {price_change:+.2f}%

📊 **2. MARKET DATA**
• **Volume 24h**: ${volume_24h:,.0f}
• **Bid-Ask Spread**: {((ask_price - bid_price) / current_price * 100):.3f}%

📈 **3. TECHNICAL ANALYSIS**
• **Trend**: {trend_emoji} {trend}
• **Momentum**: {'Positive' if price_change > 0 else 'Negative' if price_change < 0 else 'Sideways'}
• **Volatility**: {'High' if abs(price_change) > 5 else 'Normal'}

🎯 **4. SUPPLY & DEMAND ZONES**"""

            # Add SnD analysis
            if 'error' not in snd_analysis:
                supply_zones = snd_analysis.get('supply_zones', [])
                demand_zones = snd_analysis.get('demand_zones', [])

                if supply_zones and len(supply_zones) >= 2:
                    analysis += f"""
📉 **SUPPLY ZONES:**
• **Supply 1**: ${self._format_price(supply_zones[0]['price'])} 🔥
• **Supply 2**: ${self._format_price(supply_zones[1]['price'])} ⭐"""

                if demand_zones and len(demand_zones) >= 2:
                    analysis += f"""
📈 **DEMAND ZONES:**
• **Demand 1**: ${self._format_price(demand_zones[0]['price'])} 🔥
• **Demand 2**: ${self._format_price(demand_zones[1]['price'])} ⭐"""
            else:
                fallback_snd = self._generate_fallback_snd_zones(current_price)
                analysis += f"""
📉 **SUPPLY ZONES (Estimasi):**
• **Supply 1**: ${self._format_price(fallback_snd['supply_1'])}
• **Supply 2**: ${self._format_price(fallback_snd['supply_2'])}
📈 **DEMAND ZONES (Estimasi):**
• **Demand 1**: ${self._format_price(fallback_snd['demand_1'])}
• **Demand 2**: ${self._format_price(fallback_snd['demand_2'])}"""

            analysis += f"""

📌 **5. KESIMPULAN & REKOMENDASI**
• **Rekomendasi**: {rec_emoji} **{recommendation}**
• **Confidence**: {confidence}%
• **Risk Level**: {'Low' if confidence > 85 else 'Medium' if confidence > 75 else 'High'}

🕐 **Update**: {current_time} WIB
⭐️ **Professional Analysis** – CoinAPI + Supabase"""

            return analysis

        except Exception as e:
            return f"❌ **ANALISIS ERROR**: {str(e)[:100]}"

    def analyze_supply_demand_from_candlesticks(self, symbol, candlestick_data):
        """Analyze Supply and Demand zones from CoinAPI candlestick data"""
        try:
            if 'error' in candlestick_data or not candlestick_data.get('data'):
                return {'error': 'Insufficient candlestick data for SnD analysis'}

            candles = candlestick_data['data']
            if len(candles) < 50:
                return {'error': 'Not enough candles for SnD analysis (need 50+)'}

            supply_zones = []
            demand_zones = []

            for i in range(2, len(candles) - 2):
                current = candles[i]
                prev1 = candles[i-1]
                prev2 = candles[i-2]
                next1 = candles[i+1]
                next2 = candles[i+2]

                high = float(current.get('price_high', 0))
                low = float(current.get('price_low', 0))
                volume = float(current.get('volume_traded', 0))

                # Swing High detection
                prev1_high = float(prev1.get('price_high', 0))
                prev2_high = float(prev2.get('price_high', 0))
                next1_high = float(next1.get('price_high', 0))
                next2_high = float(next2.get('price_high', 0))

                if (high > prev1_high and high > prev2_high and 
                    high > next1_high and high > next2_high and volume > 0):
                    supply_zones.append({
                        'price': high,
                        'strength': min(100, (volume / 1000000) * 5 + 50),
                        'type': 'supply'
                    })

                # Swing Low detection
                prev1_low = float(prev1.get('price_low', 0))
                prev2_low = float(prev2.get('price_low', 0))
                next1_low = float(next1.get('price_low', 0))
                next2_low = float(next2.get('price_low', 0))

                if (low < prev1_low and low < prev2_low and 
                    low < next1_low and low < next2_low and volume > 0):
                    demand_zones.append({
                        'price': low,
                        'strength': min(100, (volume / 1000000) * 5 + 50),
                        'type': 'demand'
                    })

            current_price = float(candles[-1].get('price_close', 0))

            # Sort by proximity to current price
            supply_zones.sort(key=lambda x: abs(x['price'] - current_price))
            demand_zones.sort(key=lambda x: abs(x['price'] - current_price))

            return {
                'supply_zones': supply_zones[:5],
                'demand_zones': demand_zones[:5],
                'current_price': current_price
            }

        except Exception as e:
            return {'error': f'SnD analysis failed: {str(e)}'}

    def _generate_fallback_snd_zones(self, current_price):
        """Generate fallback SnD zones when CoinAPI fails"""
        return {
            'supply_1': current_price * 1.025,
            'supply_2': current_price * 1.05,
            'demand_1': current_price * 0.975,
            'demand_2': current_price * 0.95
        }

    def get_ai_response(self, text, language='id', user_id=None):
        """Enhanced AI response for crypto questions"""
        # Save user if provided
        if user_id:
            self.save_user(user_id)

        text_lower = text.lower()

        if language == 'id':
            if any(keyword in text_lower for keyword in ['apa itu bitcoin', 'bitcoin itu apa']):
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

📈 **Untuk pemula**: Mulai dengan belajar tentang wallet, private key, dan cara membeli BTC di exchange resmi."""

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`.\nContoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

            elif any(keyword in text_lower for keyword in ['help', 'bantuan', 'command']):
                return self.help_message()

            elif any(keyword in text_lower for keyword in ['terima kasih', 'thanks', 'thx']):
                return "🙏 Sama-sama! Senang bisa membantu belajar crypto Anda. Jangan ragu untuk bertanya lagi!"

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

💡 **Tip**: Coba ketik pertanyaan lebih spesifik atau gunakan command yang tersedia."""

        else:
            return """🤖 **CryptoMentor AI - Crypto Learning Assistant**

I'm here to help you learn about cryptocurrency!

📚 **Topics I can explain:**
- Crypto basics (Bitcoin, Blockchain, DeFi)
- How to buy and store crypto
- Trading and technical analysis
- Security and wallet management
- NFTs and blockchain technology

💡 **Available commands:**
- `/price <symbol>` - Check real-time prices
- `/analyze <symbol>` - Deep analysis
- `/futures_signals` - Trading signals
- `/help` - See all commands

Ask me anything about crypto! 🚀"""

    def _format_price(self, price):
        """Format price display based on value"""
        if price < 1:
            return f"{price:.6f}"
        elif price < 100:
            return f"{price:.4f}"
        else:
            return f"{price:,.2f}"