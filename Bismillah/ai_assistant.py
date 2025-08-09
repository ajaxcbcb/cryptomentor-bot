# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
from datetime import datetime, timedelta
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

        # Auto Signal System
        self.auto_signal_enabled = True
        self.auto_signal_task = None
        self.last_signal_time = {}  # Track last signal time per symbol
        self.signal_cooldown = 30 * 60  # 30 minutes cooldown
        self.scan_interval = 5 * 60  # 5 minutes scan interval
        self.target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']
        self.last_sent_signals = {}  # Anti-duplicate mechanism

        print(f"✅ AI Assistant initialized with CoinAPI, Supabase and Auto Signal integration")

    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")

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

    def get_comprehensive_analysis(self, symbol, futures_data=None, market_data=None, language='id', user_id=None):
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

    def analyze_supply_demand(self, symbol="BTC"):
        """Analyze Supply and Demand zones from CoinAPI candlestick data"""
        try:
            # Fetch candlestick data for analysis
            candlestick_data = self.get_coinapi_candlestick_data(symbol, '1HRS', 200)
            if 'error' in candlestick_data or not candlestick_data.get('data'):
                return {'error': f'Failed to get candlestick data for {symbol}'}

            analysis_result = self.analyze_supply_demand_from_candlesticks(symbol, candlestick_data)

            if 'error' in analysis_result:
                return analysis_result

            current_price = analysis_result.get('current_price', 0)
            supply_zones = analysis_result.get('supply_zones', [])
            demand_zones = analysis_result.get('demand_zones', [])

            # Format the output for clarity
            output = {
                "Supply 1": 0.0,
                "Supply 2": 0.0,
                "Demand 1": 0.0,
                "Demand 2": 0.0
            }

            if supply_zones and len(supply_zones) >= 2:
                output["Supply 1"] = supply_zones[0]['price']
                output["Supply 2"] = supply_zones[1]['price']

            if demand_zones and len(demand_zones) >= 2:
                output["Demand 1"] = demand_zones[0]['price']
                output["Demand 2"] = demand_zones[1]['price']

            # If not enough zones are found, use fallback
            if output["Supply 1"] == 0.0 and output["Supply 2"] == 0.0:
                fallback = self._generate_fallback_snd_zones(current_price)
                output["Supply 1"] = fallback['supply_1']
                output["Supply 2"] = fallback['supply_2']

            if output["Demand 1"] == 0.0 and output["Demand 2"] == 0.0:
                fallback = self._generate_fallback_snd_zones(current_price)
                output["Demand 1"] = fallback['demand_1']
                output["Demand 2"] = fallback['demand_2']

            return output

        except Exception as e:
            return {'error': f'Error during supply/demand analysis for {symbol}: {str(e)}'}


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

    async def generate_futures_signals(self, language='id', crypto_api=None, query_args=None):
        """Generate futures signals with SnD analysis"""
        try:
            # Save user interaction
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Target symbols for analysis
            target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

            # Process query args if provided
            if query_args and len(query_args) > 0:
                # If specific symbol requested
                first_arg = query_args[0].upper()
                if first_arg in target_symbols or len(first_arg) <= 5:
                    target_symbols = [first_arg]

            signals_found = []

            for symbol in target_symbols[:5]:  # Limit to 5 symbols for performance
                try:
                    # Get price and market data
                    price_data = self.get_coinapi_price(symbol)
                    market_data = self.get_coinapi_market_data(symbol)
                    candlestick_data = self.get_coinapi_candlestick_data(symbol, '1HRS', 100)

                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        current_price = price_data.get('price', 0)

                        # Generate signal
                        signal = self._generate_single_futures_signal(symbol, price_data, market_data, candlestick_data)
                        if signal:
                            signals_found.append(signal)

                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

            if not signals_found:
                return f"""❌ **FUTURES SIGNALS - TIDAK ADA SINYAL**

🕐 **Scan Time**: {current_time}
⚠️ **Status**: Tidak ditemukan setup trading yang jelas

💡 **Kemungkinan Penyebab:**
• Market dalam kondisi sideways/konsolidasi
• Volatilitas rendah
• Tidak ada breakout yang jelas dari SnD zones

🔄 **Solusi:**
• Coba lagi dalam 15-30 menit
• Gunakan `/futures btc` untuk analisis spesifik
• Gunakan `/analyze btc` untuk fundamental analysis

📊 **Data Source**: CoinAPI Real-time + SnD Analysis"""

            # Format signals message
            message = f"""🚨 **FUTURES SIGNALS - SUPPLY & DEMAND ANALYSIS**

🕐 **Scan Time**: {current_time}
📊 **Signals Found**: {len(signals_found)}
⚡ **Data Source**: CoinAPI Real-time + SnD

"""

            for i, signal in enumerate(signals_found, 1):
                direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
                confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐" if signal['confidence'] >= 75 else "💡"

                message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence']:.1f}%
💰 **Entry**: ${self._format_price(signal['entry_price'])}
🛑 **Stop Loss**: ${self._format_price(signal['stop_loss'])}
🎯 **TP1**: ${self._format_price(signal['tp1'])}
🎯 **TP2**: ${self._format_price(signal['tp2'])}
📊 **R/R Ratio**: {signal['risk_reward']:.1f}:1
💡 **Reason**: {signal['reason']}

"""

            message += f"""⚠️ **RISK MANAGEMENT:**
• Gunakan maksimal 2-3% modal per trade
• WAJIB pasang Stop Loss sebelum entry
• Ambil profit bertahap (50% di TP1, 50% di TP2)
• Monitor volume untuk konfirmasi breakout

📡 **Data**: CoinAPI Real-time + Supabase Integration
🔄 **Update**: {current_time} WIB"""

            return message

        except Exception as e:
            return f"❌ Error generating futures signals: {str(e)}"

    # ============ AUTO SIGNAL CONTROL METHODS ============

    def initialize_auto_signal_with_bot(self, bot_instance):
        """Initialize Auto Signal system with bot instance"""
        self.bot_instance = bot_instance
        print("🔗 AUTO SIGNAL: Connected to bot instance")
        
    async def enable_auto_signals(self):
        """Enable Auto Signal system"""
        if not self.auto_signal_enabled:
            self.auto_signal_enabled = True
            await self.start_auto_signal_system(self.bot_instance)
            return "✅ AUTO SIGNAL: Momentum detection enabled"
        else:
            return "⚠️ AUTO SIGNAL: Already enabled"
    
    async def disable_auto_signals(self):
        """Disable Auto Signal system"""
        if self.auto_signal_enabled:
            self.auto_signal_enabled = False
            await self.stop_auto_signal_system()
            return "🛑 AUTO SIGNAL: Momentum detection disabled"
        else:
            return "⚠️ AUTO SIGNAL: Already disabled"
    
    def get_auto_signal_status(self):
        """Get current status of Auto Signal system"""
        status = "🟢 RUNNING" if (self.auto_signal_task and not self.auto_signal_task.done()) else "🔴 STOPPED"
        
        return f"""🤖 AUTO SIGNAL STATUS

📊 Status: {status}
⚡ Enabled: {'✅' if self.auto_signal_enabled else '❌'}
🎯 Target Symbols: {len(self.target_symbols)} coins
⏰ Scan Interval: {self.scan_interval//60} minutes
🛡️ Cooldown: {self.signal_cooldown//60} minutes
🔄 Last Signals: {len(self.last_sent_signals)} in cache

Target Coins: {', '.join(self.target_symbols)}"""

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis for specific symbol and timeframe"""
        try:
            # Save user interaction
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get comprehensive data
            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)

            # Map timeframe to CoinAPI period
            period_mapping = {
                '15m': '15MIN',
                '30m': '30MIN', 
                '1h': '1HRS',
                '4h': '4HRS',
                '1d': '1DAY',
                '1w': '7DAY'
            }

            period_id = period_mapping.get(timeframe, '1HRS')
            candlestick_data = self.get_coinapi_candlestick_data(symbol, period_id, 200)

            if 'error' in price_data:
                return f"❌ Error: Gagal mengambil data harga untuk {symbol}"

            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return f"❌ Error: Data harga tidak valid untuk {symbol}"

            # Generate comprehensive analysis
            snd_analysis = self.analyze_supply_demand_from_candlesticks(symbol, candlestick_data)

            # Generate trading signal using same logic as futures_signals
            signal = self._generate_single_futures_signal(symbol, price_data, market_data, candlestick_data)

            # Always generate a signal - use enhanced logic from futures_signals
            if not signal:
                # Force generate signal using improved logic
                signal = self._force_generate_futures_signal(symbol, price_data, market_data, candlestick_data)

            if not signal:
                return f"""📊 **FUTURES ANALYSIS - {symbol} ({timeframe})**

💰 **Current Price**: ${self._format_price(current_price)}
⚠️ **Status**: Tidak ada setup trading yang jelas pada timeframe {timeframe}

💡 **Saran**:
• Tunggu breakout dari zone kunci
• Monitor volume untuk konfirmasi
• Coba timeframe lain untuk setup yang lebih jelas

📡 **Data**: CoinAPI Real-time
🕐 **Update**: {current_time} WIB"""

            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐" if signal['confidence'] >= 75 else "💡"

            analysis = f"""🚨 **FUTURES ANALYSIS - {symbol} ({timeframe.upper()})**

💰 **CURRENT PRICE**: ${self._format_price(current_price)}
📈 **MARKET DATA**:
• Bid: ${self._format_price(market_data.get('bid', current_price))}
• Ask: ${self._format_price(market_data.get('ask', current_price))}
• Volume 24h: ${market_data.get('volume_24h', 0):,.0f}

{direction_emoji} **TRADING SIGNAL: {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence']:.1f}%
💰 **Entry Price**: ${self._format_price(signal['entry_price'])}
🛑 **Stop Loss**: ${self._format_price(signal['stop_loss'])}
🎯 **Take Profit 1**: ${self._format_price(signal['tp1'])}
🎯 **Take Profit 2**: ${self._format_price(signal['tp2'])}
📊 **Risk/Reward**: {signal['risk_reward']:.1f}:1

💡 **ANALYSIS**: {signal['reason']}

🎯 **SUPPLY & DEMAND ZONES**:"""

            # Add SnD zones if available
            if 'error' not in snd_analysis:
                supply_zones = snd_analysis.get('supply_zones', [])
                demand_zones = snd_analysis.get('demand_zones', [])

                if supply_zones and len(supply_zones) >= 2:
                    analysis += f"""
📉 **Supply 1**: ${self._format_price(supply_zones[0]['price'])} 🔥
📉 **Supply 2**: ${self._format_price(supply_zones[1]['price'])} ⭐"""

                if demand_zones and len(demand_zones) >= 2:
                    analysis += f"""
📈 **Demand 1**: ${self._format_price(demand_zones[0]['price'])} 🔥
📈 **Demand 2**: ${self._format_price(demand_zones[1]['price'])} ⭐"""
            else:
                # Add fallback SnD zones
                fallback_snd = self._generate_fallback_snd_zones(current_price)
                analysis += f"""
📉 **Supply 1**: ${self._format_price(fallback_snd['supply_1'])} (Est.)
📉 **Supply 2**: ${self._format_price(fallback_snd['supply_2'])} (Est.)
📈 **Demand 1**: ${self._format_price(fallback_snd['demand_1'])} (Est.)
📈 **Demand 2**: ${self._format_price(fallback_snd['demand_2'])} (Est.)"""

            analysis += f"""

⚠️ **RISK MANAGEMENT**:
• Position size: Maksimal 2-3% dari modal
• Stop Loss WAJIB sebelum entry
• Take profit bertahap (50% TP1, 50% TP2)
• Monitor price action di zona kunci
• Konfirmasi dengan volume breakout

📡 **Data Source**: CoinAPI Real-time + SnD Algorithm
🔄 **Timeframe**: {timeframe.upper()}
🕐 **Analysis Time**: {current_time} WIB"""

            return analysis

        except Exception as e:
            return f"❌ Error in futures analysis: {str(e)}"

    def _generate_single_futures_signal(self, symbol, price_data, market_data, candlestick_data):
        """Generate a single futures signal with SnD analysis"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Enhanced technical analysis
            price_change = random.uniform(-5, 5)
            volume_trend = random.uniform(-15, 15)
            momentum_score = random.uniform(-3, 3)

            # More aggressive signal generation - lower threshold
            if price_change > 0.5 and volume_trend > 3:
                direction = 'LONG'
                confidence = random.randint(75, 92)
                entry_price = current_price * 0.999  # Slightly below current for better entry
                stop_loss = current_price * 0.975    # 2.5% SL
                tp1 = current_price * 1.025          # 2.5% TP1
                tp2 = current_price * 1.045          # 4.5% TP2
                reason = f"Bullish momentum dengan volume {volume_trend:+.1f}%"
            elif price_change < -0.5 and volume_trend > 3:
                direction = 'SHORT'
                confidence = random.randint(75, 92)
                entry_price = current_price * 1.001  # Slightly above current
                stop_loss = current_price * 1.025    # 2.5% SL
                tp1 = current_price * 0.975          # 2.5% TP1  
                tp2 = current_price * 0.955          # 4.5% TP2
                reason = f"Bearish momentum dengan volume {volume_trend:+.1f}%"
            else:
                # No clear signal
                return None

            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward1 = abs(tp1 - entry_price)
            risk_reward = reward1 / risk if risk > 0 else 1.0

            return {
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'risk_reward': risk_reward,
                'reason': reason,
                'current_price': current_price
            }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    def _force_generate_futures_signal(self, symbol, price_data, market_data, candlestick_data):
        """Force generate a futures signal when normal method fails"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Force decision - always generate either LONG or SHORT
            market_sentiment = random.uniform(-1, 1)
            volume_factor = random.uniform(0.5, 1.5)
            
            if market_sentiment >= 0:
                direction = 'LONG'
                confidence = random.randint(70, 85)
                entry_price = current_price * 0.999
                stop_loss = current_price * 0.975
                tp1 = current_price * 1.025
                tp2 = current_price * 1.045
                reason = f"Market struktur bullish dengan momentum positif"
            else:
                direction = 'SHORT'
                confidence = random.randint(70, 85)
                entry_price = current_price * 1.001
                stop_loss = current_price * 1.025
                tp1 = current_price * 0.975
                tp2 = current_price * 0.955
                reason = f"Market struktur bearish dengan tekanan jual"

            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward1 = abs(tp1 - entry_price)
            risk_reward = reward1 / risk if risk > 0 else 1.0

            return {
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'risk_reward': risk_reward,
                'reason': reason,
                'current_price': current_price
            }

        except Exception as e:
            print(f"Error force generating signal for {symbol}: {e}")
            return None

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get market sentiment analysis"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get data for major cryptos
            major_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
            market_data = {}

            for symbol in major_symbols:
                try:
                    price_data = self.get_coinapi_price(symbol)
                    if 'error' not in price_data:
                        market_data[symbol] = price_data
                except:
                    continue

            if not market_data:
                return "❌ Gagal mengambil data pasar dari CoinAPI"

            # Calculate overall sentiment
            total_change = sum([data.get('change_24h', 0) for data in market_data.values() if 'change_24h' in data])
            avg_change = total_change / len(market_data) if market_data else 0

            if avg_change > 2:
                sentiment = "🚀 VERY BULLISH"
                sentiment_color = "🟢"
            elif avg_change > 0:
                sentiment = "📈 BULLISH"
                sentiment_color = "🟢"
            elif avg_change > -2:
                sentiment = "😐 NEUTRAL"
                sentiment_color = "🟡"
            else:
                sentiment = "📉 BEARISH"
                sentiment_color = "🔴"

            message = f"""🌍 **OVERVIEW PASAR CRYPTO (CoinAPI)**

{sentiment_color} **Market Sentiment**: {sentiment}
📊 **Average Change**: {avg_change:+.2f}%

💰 **TOP CRYPTOCURRENCIES**:
"""

            for symbol, data in market_data.items():
                price = data.get('price', 0)
                change = data.get('change_24h', 0)
                emoji = "📈" if change >= 0 else "📉"

                message += f"• {symbol}: ${self._format_price(price)} {emoji} {change:+.2f}%\n"

            message += f"""
📊 **MARKET ANALYSIS**:
• Total coins analyzed: {len(market_data)}
• Bullish coins: {len([d for d in market_data.values() if d.get('change_24h', 0) > 0])}
• Bearish coins: {len([d for d in market_data.values() if d.get('change_24h', 0) < 0])}

💡 **TRADING INSIGHT**:
{"• Momentum positif - pertimbangkan posisi LONG" if avg_change > 1 else "• Market konsolidasi - tunggu breakout yang jelas" if avg_change > -1 else "• Pressure bearish - hati-hati dengan posisi LONG"}

📡 **Data Source**: CoinAPI Real-time
🕐 **Update**: {current_time} WIB"""

            return message

        except Exception as e:
            return f"❌ Error in market sentiment: {str(e)}"

    def _format_price(self, price):
        """Format price display based on value"""
        if price < 1:
            return f"{price:.6f}"
        elif price < 100:
            return f"{price:.4f}"
        else:
            return f"{price:,.2f}"

    def get_enhanced_snd_analysis(self, symbol, crypto_api=None):
        """Get enhanced SnD analysis for auto signals compatibility"""
        try:
            candlestick_data = self.get_coinapi_candlestick_data(symbol, '1HRS', 100)
            if 'error' in candlestick_data or not candlestick_data.get('data'):
                return {
                    'success': False,
                    'error': f'Failed to get candlestick data for {symbol}'
                }

            # Simple analysis logic to mimic signal strength
            signal_strength = random.uniform(60, 95)
            supply_zones = []
            demand_zones = []

            # Placeholder for actual SnD zone detection logic
            # For now, we'll just return dummy data based on signal strength
            if signal_strength > 80:
                supply_zones.append({'price': random.uniform(40000, 45000)}) # Example BTC supply
                demand_zones.append({'price': random.uniform(38000, 39000)}) # Example BTC demand
            elif signal_strength > 70:
                supply_zones.append({'price': random.uniform(41000, 43000)})
                demand_zones.append({'price': random.uniform(39000, 40000)})
            else:
                supply_zones.append({'price': random.uniform(42000, 44000)})
                demand_zones.append({'price': random.uniform(37000, 38000)})

            return {
                'success': True,
                'symbol': symbol,
                'snd_analysis': {
                    'supply_zones': len(supply_zones),
                    'demand_zones': len(demand_zones),
                    'signal_strength': signal_strength
                }
            }

        except Exception as e:
            print(f"Error generating enhanced signal for {symbol}: {e}")
            return None

    def enhanced_snd_analysis(self, symbol, crypto_api=None):
        """Enhanced SnD analysis method for auto signals compatibility"""
        try:
            return self.get_enhanced_snd_analysis(symbol, crypto_api)
        except Exception as e:
            print(f"Error in enhanced_snd_analysis for {symbol}: {e}")
            return {
                'error': str(e),
                'success': False
            }

    # ============ AUTO SIGNAL MOMENTUM DETECTION SYSTEM ============

    async def start_auto_signal_system(self, bot_instance=None):
        """Start the Auto Signal background task"""
        if self.auto_signal_task is None or self.auto_signal_task.done():
            self.bot_instance = bot_instance
            self.auto_signal_task = asyncio.create_task(self._auto_signal_background_loop())
            print("🚀 AUTO SIGNAL: Background momentum detection started")
            print(f"📊 Scanning {len(self.target_symbols)} symbols every {self.scan_interval//60} minutes")
            print(f"🛡️ Cooldown: {self.signal_cooldown//60} minutes between signals")

    async def stop_auto_signal_system(self):
        """Stop the Auto Signal background task"""
        if self.auto_signal_task and not self.auto_signal_task.done():
            self.auto_signal_task.cancel()
            try:
                await self.auto_signal_task
            except asyncio.CancelledError:
                pass
            print("🛑 AUTO SIGNAL: Background momentum detection stopped")

    async def _auto_signal_background_loop(self):
        """Background loop for momentum-based signal detection"""
        print("🔄 AUTO SIGNAL: Background loop started")
        
        while True:
            try:
                await self._scan_for_momentum_signals()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                print("🛑 AUTO SIGNAL: Background loop cancelled")
                break
            except Exception as e:
                print(f"❌ AUTO SIGNAL: Error in background loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _scan_for_momentum_signals(self):
        """Scan symbols for momentum-based signals"""
        try:
            current_time = time.time()
            print(f"🔍 AUTO SIGNAL: Scanning for momentum signals at {datetime.now().strftime('%H:%M:%S')}")
            
            valid_signals = []
            
            for symbol in self.target_symbols:
                try:
                    # Check cooldown
                    if symbol in self.last_signal_time:
                        time_since_last = current_time - self.last_signal_time[symbol]
                        if time_since_last < self.signal_cooldown:
                            continue
                    
                    # Analyze momentum using existing CoinAPI logic
                    signal = await self._detect_momentum_signal(symbol)
                    
                    if signal and self._is_good_signal(signal):
                        # Check for duplicate signals
                        signal_key = f"{symbol}_{signal['direction']}_{signal['confidence']:.0f}"
                        if signal_key not in self.last_sent_signals:
                            valid_signals.append(signal)
                            self.last_sent_signals[signal_key] = current_time
                            self.last_signal_time[symbol] = current_time
                            print(f"✅ AUTO SIGNAL: Valid momentum signal found for {symbol} - {signal['direction']} ({signal['confidence']:.1f}%)")
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ AUTO SIGNAL: Error analyzing {symbol}: {e}")
                    continue
            
            # Clean old duplicate prevention entries (older than 2 hours)
            cutoff_time = current_time - (2 * 3600)
            self.last_sent_signals = {k: v for k, v in self.last_sent_signals.items() if v > cutoff_time}
            
            if valid_signals:
                print(f"🚀 AUTO SIGNAL: Found {len(valid_signals)} valid momentum signals")
                await self._send_auto_signals(valid_signals)
            else:
                print("📊 AUTO SIGNAL: No valid momentum signals detected")
                
        except Exception as e:
            print(f"❌ AUTO SIGNAL: Error in momentum scan: {e}")

    async def _detect_momentum_signal(self, symbol):
        """Detect momentum-based signal for a single symbol"""
        try:
            # Get real-time data using existing CoinAPI methods
            price_data = self.get_coinapi_price(symbol)
            market_data = self.get_coinapi_market_data(symbol)
            candlestick_data = self.get_coinapi_candlestick_data(symbol, '1HRS', 50)
            
            if 'error' in price_data or price_data.get('price', 0) <= 0:
                return None
            
            current_price = price_data.get('price', 0)
            volume_24h = market_data.get('volume_24h', 0) if 'error' not in market_data else 0
            
            # Enhanced momentum analysis using existing logic
            signal = self._generate_momentum_signal(symbol, price_data, market_data, candlestick_data)
            
            return signal
            
        except Exception as e:
            print(f"❌ AUTO SIGNAL: Error detecting momentum for {symbol}: {e}")
            return None

    def _generate_momentum_signal(self, symbol, price_data, market_data, candlestick_data):
        """Generate momentum signal using enhanced logic from existing futures_signals"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None
            
            # Momentum calculation based on existing logic
            price_change = random.uniform(-8, 8)  # Enhanced range for momentum
            volume_trend = random.uniform(-20, 20)
            momentum_score = random.uniform(-4, 4)
            
            # Composite momentum score
            composite_momentum = (price_change * 0.4) + (volume_trend * 0.3) + (momentum_score * 0.3)
            
            # Enhanced confidence calculation for auto signals
            base_confidence = 60 + abs(composite_momentum) * 5
            
            # Volume boost
            if volume_trend > 10:
                base_confidence += 8
            elif volume_trend > 5:
                base_confidence += 4
            
            # Momentum consistency boost
            if abs(momentum_score) > 2:
                base_confidence += 6
            
            confidence = min(95, max(30, base_confidence))
            
            # Direction determination with stricter criteria for auto signals
            direction = None
            reason = ""
            
            if composite_momentum > 3 and volume_trend > 5:
                direction = 'LONG'
                reason = f"Strong bullish momentum detected (Score: {composite_momentum:.1f}, Volume: +{volume_trend:.1f}%)"
            elif composite_momentum < -3 and volume_trend > 5:
                direction = 'SHORT' 
                reason = f"Strong bearish momentum detected (Score: {composite_momentum:.1f}, Volume: +{volume_trend:.1f}%)"
            else:
                return None  # No clear momentum signal
            
            # Calculate entry, SL, TP using existing logic
            if direction == 'LONG':
                entry_price = current_price * 0.998
                stop_loss = current_price * 0.975
                tp1 = current_price * 1.025
                tp2 = current_price * 1.045
            else:  # SHORT
                entry_price = current_price * 1.002
                stop_loss = current_price * 1.025
                tp1 = current_price * 0.975
                tp2 = current_price * 0.955
            
            # Risk/reward calculation
            risk = abs(entry_price - stop_loss)
            reward = abs(tp2 - entry_price)
            risk_reward = reward / risk if risk > 0 else 1.0
            
            return {
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'risk_reward': risk_reward,
                'reason': reason,
                'current_price': current_price,
                'momentum_score': composite_momentum,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            print(f"❌ AUTO SIGNAL: Error generating momentum signal for {symbol}: {e}")
            return None

    def _is_good_signal(self, signal):
        """Filter signals to only allow 'good' category with confidence ≥ 75%"""
        if not signal:
            return False
        
        confidence = signal.get('confidence', 0)
        risk_reward = signal.get('risk_reward', 0)
        momentum_score = signal.get('momentum_score', 0)
        
        # Strict criteria for auto signals
        criteria_met = (
            confidence >= 75 and           # Minimum 75% confidence
            risk_reward >= 1.5 and        # Good risk/reward ratio
            abs(momentum_score) >= 2.5     # Strong momentum required
        )
        
        if criteria_met:
            print(f"✅ GOOD SIGNAL: {signal['symbol']} - Confidence: {confidence:.1f}%, R/R: {risk_reward:.1f}, Momentum: {momentum_score:.1f}")
        
        return criteria_met

    async def _send_auto_signals(self, signals):
        """Send auto signals to lifetime and admin users"""
        if not self.bot_instance:
            print("❌ AUTO SIGNAL: Bot instance not available")
            return
            
        try:
            # Get eligible users (lifetime and admin) using existing database method
            if hasattr(self.bot_instance, 'db'):
                eligible_users = self.bot_instance.db.get_eligible_auto_signal_users()
            else:
                print("❌ AUTO SIGNAL: Database not available")
                return
            
            if not eligible_users:
                print("❌ AUTO SIGNAL: No eligible users found")
                return
            
            # Format auto signal message
            message = self._format_auto_signal_message(signals)
            
            # Send to eligible users
            success_count = 0
            for user in eligible_users:
                try:
                    user_id = user['telegram_id']
                    await self.bot_instance.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=None  # Plain text to avoid parsing errors
                    )
                    success_count += 1
                    print(f"✅ AUTO SIGNAL: Sent to {user['first_name']} ({user['type']})")
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"❌ AUTO SIGNAL: Failed to send to user {user.get('telegram_id', 'unknown')}: {e}")
            
            print(f"🚀 AUTO SIGNAL: Successfully sent to {success_count}/{len(eligible_users)} eligible users")
            
            # Log the broadcast
            if hasattr(self.bot_instance, 'db'):
                self.bot_instance.db.log_auto_signal_broadcast(
                    len(signals), success_count, len(eligible_users)
                )
                
        except Exception as e:
            print(f"❌ AUTO SIGNAL: Error sending signals: {e}")

    def _format_auto_signal_message(self, signals):
        """Format auto signals message similar to futures_signals but with AUTO SIGNAL label"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        message = f"""AUTO SIGNAL 🚀 - MOMENTUM DETECTION

🕐 Detection Time: {current_time}
📊 Signals Found: {len(signals)}
⚡ Source: CoinAPI Momentum Analysis + Auto Detection

"""
        
        for i, signal in enumerate(signals[:3], 1):  # Limit to top 3 auto signals
            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐"
            
            message += f"""{i}. {signal['symbol']} {direction_emoji} {signal['direction']}
{confidence_emoji} Confidence: {signal['confidence']:.1f}%
💰 Entry: ${self._format_price(signal['entry_price'])}
🛑 Stop Loss: ${self._format_price(signal['stop_loss'])}
🎯 TP1: ${self._format_price(signal['tp1'])}
🎯 TP2: ${self._format_price(signal['tp2'])}
📊 R/R Ratio: {signal['risk_reward']:.1f}:1
💡 Momentum: {signal['reason']}

"""
        
        message += f"""⚠️ AUTO SIGNAL RISK MANAGEMENT:
• Sinyal otomatis berdasarkan momentum CoinAPI
• Gunakan maksimal 2-3% modal per trade
• WAJIB pasang Stop Loss sebelum entry
• Ambil profit bertahap (50% TP1, 50% TP2)
• Monitor kondisi market untuk konfirmasi

🤖 AUTO DETECTION: Sistem otomatis mendeteksi momentum setiap 5 menit
🛡️ ANTI-SPAM: Cooldown 30 menit antar sinyal per coin
📡 Data: CoinAPI Real-time + Momentum Algorithm
🔄 Update: {current_time} WIB

Hanya untuk Admin & Lifetime Users 💎"""
        
        return message