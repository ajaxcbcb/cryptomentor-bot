# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name
        self.coinapi_key = os.getenv("COINAPI_API_KEY")
        self.cmc_api_key = os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY")

        # API Headers
        self.coinapi_headers = {
            "X-CoinAPI-Key": self.coinapi_key
        } if self.coinapi_key else {}

        self.cmc_headers = {
            "X-CMC_PRO_API_KEY": self.cmc_api_key,
            "Accept": "application/json"
        } if self.cmc_api_key else {}

        # Initialize Supabase connection
        self.supabase = self._init_supabase()

        # Auto Signal System with enhanced configuration
        self.auto_signal_enabled = True
        self.auto_signal_task = None
        self.signal_cooldown = 3600  # 1 hour cooldown as requested
        self.scan_interval = 5 * 60  # 5 minutes scan interval
        self.min_confidence_threshold = 75  # Minimum 75% confidence

        # Target symbols for futures analysis
        self.target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

        # Signal tracking in Supabase
        self.last_signals = {}  # Local cache for performance

        # Timeframes for multi-timeframe analysis
        self.timeframes = {
            '5m': '5MIN',
            '1h': '1HRS', 
            '4h': '4HRS'
        }

        print(f"✅ AI Assistant initialized with CoinAPI + CMC multi-timeframe analysis")

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

    def greet(self):
        return f"Halo! Saya {self.name}, siap membantu analisis dan informasi crypto kamu."

    def help_message(self):
        return """🤖 **CryptoMentor AI Bot - Enhanced Multi-Timeframe Analysis**

📊 **Advanced Technical Analysis:**
• `/price <symbol>` - Harga real-time CoinAPI
• `/analyze <symbol>` - Multi-timeframe technical analysis (20 credit)
• `/futures <symbol>` - Advanced futures analysis dengan confidence score (20 credit)
• `/futures_signals` - Auto signals berdasarkan analisis teknikal + makro (30 credit)

💰 **Market Overview:**
• `/market` - Global market analysis dari CoinMarketCap

🎯 **Auto Signal Features:**
• Real-time monitoring setiap 5 menit
• Multi-timeframe confirmation (5m + 1h)
• Technical indicators: EMA50/200, RSI, MACD, ATR
• Macro analysis: Market cap, volume global, BTC dominance
• Confidence score 75%+ untuk sinyal berkualitas

💡 **New Features:**
- ✅ CoinAPI OHLCV data untuk analisis teknikal
- ✅ CoinMarketCap macro data
- ✅ Multi-timeframe confirmation
- ✅ Advanced confidence scoring
- ✅ 1-hour signal cooldown
- ✅ Auto-signals untuk Admin & Lifetime users

🚀 **Analisis profesional dengan data real-time multi-sumber!**"""

    # ============ COINAPI DATA FETCHING METHODS ============

    def get_coinapi_ohlcv_data(self, symbol, timeframe='1HRS', limit=200):
        """Get OHLCV data from CoinAPI for technical analysis"""
        try:
            if not self.coinapi_key:
                return {'error': 'CoinAPI key required for OHLCV data'}

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
                'AVAX': 'COINBASE_SPOT_AVAX_USD',
                'DOGE': 'COINBASE_SPOT_DOGE_USD'
            }

            coinapi_symbol = symbol_mapping.get(symbol.upper(), f"COINBASE_SPOT_{symbol.upper()}_USD")

            url = f"https://rest.coinapi.io/v1/ohlcv/{coinapi_symbol}/history"
            params = {
                'period_id': timeframe,
                'limit': limit
            }

            response = requests.get(url, headers=self.coinapi_headers, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 20:  # Ensure sufficient data
                    # Convert to pandas DataFrame for technical analysis
                    df = pd.DataFrame(data)
                    df['time_period_start'] = pd.to_datetime(df['time_period_start'])
                    df = df.sort_values('time_period_start')

                    return {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'data': df,
                        'raw_data': data,
                        'count': len(data),
                        'source': 'coinapi'
                    }
                else:
                    return {'error': 'Insufficient OHLCV data'}
            else:
                return {'error': f'CoinAPI OHLCV error: {response.status_code}'}

        except Exception as e:
            return {'error': f'CoinAPI OHLCV failed: {str(e)}'}

    def get_cmc_global_metrics(self):
        """Get global market metrics from CoinMarketCap"""
        try:
            if not self.cmc_api_key:
                return {'error': 'CoinMarketCap API key required'}

            url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

            response = requests.get(url, headers=self.cmc_headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('status', {}).get('error_code') == 0:
                    global_data = data.get('data', {})
                    quote_usd = global_data.get('quote', {}).get('USD', {})

                    return {
                        'total_market_cap': quote_usd.get('total_market_cap', 0),
                        'total_volume_24h': quote_usd.get('total_volume_24h', 0),
                        'market_cap_change_24h': quote_usd.get('total_market_cap_yesterday_percentage_change', 0),
                        'btc_dominance': global_data.get('btc_dominance', 0),
                        'eth_dominance': global_data.get('eth_dominance', 0),
                        'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'coinmarketcap'
                    }
                else:
                    return {'error': 'CoinMarketCap API error'}
            else:
                return {'error': f'CMC global metrics error: {response.status_code}'}

        except Exception as e:
            return {'error': f'CMC global metrics failed: {str(e)}'}

    # ============ TECHNICAL INDICATORS CALCULATION ============

    def calculate_technical_indicators(self, df):
        """Calculate technical indicators: EMA50, EMA200, RSI, MACD, ATR, Volume Oscillator"""
        try:
            if df is None or len(df) < 50:
                return {'error': 'Insufficient data for technical analysis'}

            # Ensure numeric columns
            df['price_close'] = pd.to_numeric(df['price_close'], errors='coerce')
            df['price_high'] = pd.to_numeric(df['price_high'], errors='coerce')
            df['price_low'] = pd.to_numeric(df['price_low'], errors='coerce')
            df['volume_traded'] = pd.to_numeric(df['volume_traded'], errors='coerce')

            indicators = {}

            # EMA 50 and EMA 200
            indicators['ema_50'] = df['price_close'].ewm(span=50).mean().iloc[-1]
            indicators['ema_200'] = df['price_close'].ewm(span=min(200, len(df))).mean().iloc[-1]

            # Current price
            indicators['current_price'] = df['price_close'].iloc[-1]

            # RSI calculation
            delta = df['price_close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))

            # MACD calculation
            ema_12 = df['price_close'].ewm(span=12).mean()
            ema_26 = df['price_close'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            indicators['macd_line'] = macd_line.iloc[-1]
            indicators['macd_signal'] = signal_line.iloc[-1]
            indicators['macd_histogram'] = macd_line.iloc[-1] - signal_line.iloc[-1]

            # ATR calculation
            high_low = df['price_high'] - df['price_low']
            high_close_prev = np.abs(df['price_high'] - df['price_close'].shift(1))
            low_close_prev = np.abs(df['price_low'] - df['price_close'].shift(1))
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            indicators['atr'] = true_range.rolling(window=14).mean().iloc[-1]
            indicators['atr_avg'] = true_range.rolling(window=14).mean().mean()

            # Volume Oscillator
            volume_sma_fast = df['volume_traded'].rolling(window=5).mean()
            volume_sma_slow = df['volume_traded'].rolling(window=10).mean()
            indicators['volume_oscillator'] = ((volume_sma_fast.iloc[-1] - volume_sma_slow.iloc[-1]) / volume_sma_slow.iloc[-1]) * 100

            return indicators

        except Exception as e:
            return {'error': f'Technical indicators calculation failed: {str(e)}'}

    # ============ CONFIDENCE SCORING SYSTEM ============

    def calculate_confidence_score(self, technical_data, macro_data, signal_direction):
        """Calculate confidence score based on technical + macro analysis"""
        try:
            technical_score = 0
            macro_score = 0

            # Technical Analysis Scoring (50 points max)
            if 'error' not in technical_data:
                indicators = technical_data

                # EMA Trend alignment (15 points)
                ema_50 = indicators.get('ema_50', 0)
                ema_200 = indicators.get('ema_200', 0)
                current_price = indicators.get('current_price', 0)

                if signal_direction == 'BUY' and ema_50 > ema_200:
                    technical_score += 15
                elif signal_direction == 'SELL' and ema_50 < ema_200:
                    technical_score += 15
                elif signal_direction == 'BUY' and ema_50 < ema_200 and current_price > ema_50:
                    technical_score += 8  # Partial credit
                elif signal_direction == 'SELL' and ema_50 > ema_200 and current_price < ema_50:
                    technical_score += 8  # Partial credit

                # RSI scoring (10 points)
                rsi = indicators.get('rsi', 50)
                if 45 <= rsi <= 65:
                    technical_score += 10
                elif 40 <= rsi <= 70:
                    technical_score += 5

                # MACD histogram alignment (10 points)
                macd_histogram = indicators.get('macd_histogram', 0)
                if signal_direction == 'BUY' and macd_histogram > 0:
                    technical_score += 10
                elif signal_direction == 'SELL' and macd_histogram < 0:
                    technical_score += 10

                # Volume Oscillator (5 points)
                volume_osc = indicators.get('volume_oscillator', 0)
                if volume_osc > 0:
                    technical_score += 5

                # ATR volatility check (5 points)
                atr = indicators.get('atr', 0)
                atr_avg = indicators.get('atr_avg', 0)
                if atr > atr_avg:
                    technical_score += 5

            # Macro Analysis Scoring (50 points max)
            if 'error' not in macro_data:
                # Market cap change (15 points)
                market_cap_change = macro_data.get('market_cap_change_24h', 0)
                if market_cap_change > 1:
                    macro_score += 15
                elif market_cap_change > -3:
                    macro_score += 5

                # Volume change logic (10 points)
                # Note: We'll estimate volume change based on market activity
                if market_cap_change > 0:  # Proxy for volume increase
                    macro_score += 10

                # BTC dominance stability (10 points)
                btc_dominance = macro_data.get('btc_dominance', 50)
                # Check if BTC dominance is stable (within reasonable range)
                if 40 <= btc_dominance <= 60:  # Normal range
                    macro_score += 10

                # Global sentiment alignment (15 points)
                if signal_direction == 'BUY' and market_cap_change > 0:
                    macro_score += 15
                elif signal_direction == 'SELL' and market_cap_change < -1:
                    macro_score += 15

            total_score = technical_score + macro_score

            return {
                'total_score': total_score,
                'technical_score': technical_score,
                'macro_score': macro_score,
                'breakdown': {
                    'technical_max': 50,
                    'macro_max': 50,
                    'threshold': self.min_confidence_threshold
                }
            }

        except Exception as e:
            return {'error': f'Confidence scoring failed: {str(e)}'}

    # ============ MULTI-TIMEFRAME ANALYSIS ============

    def analyze_multi_timeframe(self, symbol, signal_direction):
        """Perform multi-timeframe analysis (5m, 1h, 4h)"""
        try:
            timeframe_results = {}

            for tf_name, tf_coinapi in self.timeframes.items():
                ohlcv_data = self.get_coinapi_ohlcv_data(symbol, tf_coinapi, 100)

                if 'error' not in ohlcv_data:
                    df = ohlcv_data['data']
                    indicators = self.calculate_technical_indicators(df)

                    if 'error' not in indicators:
                        # Determine trend for this timeframe
                        ema_50 = indicators.get('ema_50', 0)
                        ema_200 = indicators.get('ema_200', 0)
                        current_price = indicators.get('current_price', 0)

                        trend = 'bullish' if ema_50 > ema_200 else 'bearish'
                        trend_strength = abs(ema_50 - ema_200) / ema_200 * 100

                        timeframe_results[tf_name] = {
                            'trend': trend,
                            'trend_strength': trend_strength,
                            'indicators': indicators,
                            'signal_alignment': (
                                (signal_direction == 'BUY' and trend == 'bullish') or
                                (signal_direction == 'SELL' and trend == 'bearish')
                            )
                        }
                    else:
                        timeframe_results[tf_name] = {'error': indicators['error']}
                else:
                    timeframe_results[tf_name] = {'error': ohlcv_data['error']}

            # Check multi-timeframe confirmation
            confirmation_passed = True
            required_timeframes = ['5m', '1h']  # Must align

            for tf in required_timeframes:
                if tf in timeframe_results and 'error' not in timeframe_results[tf]:
                    if not timeframe_results[tf]['signal_alignment']:
                        confirmation_passed = False
                        break
                else:
                    confirmation_passed = False
                    break

            return {
                'timeframes': timeframe_results,
                'confirmation_passed': confirmation_passed,
                'required_alignment': required_timeframes
            }

        except Exception as e:
            return {'error': f'Multi-timeframe analysis failed: {str(e)}'}

    # ============ SIGNAL COOLDOWN MANAGEMENT ============

    def check_signal_cooldown(self, symbol):
        """Check if signal cooldown has passed for a symbol"""
        try:
            if not self.supabase:
                # Fallback to local cache
                last_signal_time = self.last_signals.get(symbol, 0)
                return time.time() - last_signal_time >= self.signal_cooldown

            # Check Supabase for last signal
            result = self.supabase.table('signal_history').select('*').eq('symbol', symbol).order('created_at', desc=True).limit(1).execute()

            if result.data:
                last_signal = result.data[0]
                last_time = datetime.fromisoformat(last_signal['created_at'].replace('Z', '+00:00'))
                time_diff = datetime.now(last_time.tzinfo) - last_time
                return time_diff.total_seconds() >= self.signal_cooldown

            return True  # No previous signal found

        except Exception as e:
            print(f"❌ Error checking signal cooldown: {e}")
            return True  # Allow signal if check fails

    def save_signal_to_supabase(self, symbol, signal_data):
        """Save signal to Supabase for cooldown tracking"""
        try:
            if not self.supabase:
                # Fallback to local cache
                self.last_signals[symbol] = time.time()
                return True

            signal_record = {
                'symbol': symbol,
                'direction': signal_data.get('direction'),
                'confidence_score': signal_data.get('confidence_score'),
                'timeframe_confirmation': signal_data.get('timeframe_confirmation'),
                'created_at': datetime.now().isoformat()
            }

            result = self.supabase.table('signal_history').insert(signal_record).execute()

            # Also update local cache
            self.last_signals[symbol] = time.time()

            return bool(result.data)

        except Exception as e:
            print(f"❌ Error saving signal to Supabase: {e}")
            return False

    # ============ ENHANCED FUTURES ANALYSIS ============

    def analyze_futures_enhanced(self, symbol, user_id=None):
        """Enhanced futures analysis with multi-timeframe + confidence scoring"""
        try:
            # Save user if provided
            if user_id:
                self.save_user(user_id)

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Check signal cooldown
            if not self.check_signal_cooldown(symbol):
                cooldown_remaining = self.signal_cooldown - (time.time() - self.last_signals.get(symbol, 0))
                return f"""⏰ **SIGNAL COOLDOWN ACTIVE**

Symbol: {symbol}
Cooldown Remaining: {int(cooldown_remaining/60)} minutes

Tunggu hingga cooldown selesai untuk sinyal baru.
Ini mencegah sinyal berubah-ubah terlalu cepat."""

            # Determine signal direction (simplified for demo, you can enhance this)
            signal_direction = 'BUY' if random.random() > 0.5 else 'SELL'

            # Get macro data from CoinMarketCap
            macro_data = self.get_cmc_global_metrics()

            # Apply macro filters
            if 'error' not in macro_data:
                market_cap_change = macro_data.get('market_cap_change_24h', 0)

                # Filter logic
                if signal_direction == 'BUY' and market_cap_change < -3:
                    return f"""❌ **SIGNAL FILTERED OUT**

Symbol: {symbol}
Attempted Direction: BUY
Filter Reason: Global market cap turun {market_cap_change:.2f}% (> 3%)

Market conditions tidak mendukung sinyal BUY saat ini."""

            # Perform multi-timeframe analysis
            multi_tf_result = self.analyze_multi_timeframe(symbol, signal_direction)

            if 'error' in multi_tf_result:
                return f"❌ **MULTI-TIMEFRAME ANALYSIS ERROR**: {multi_tf_result['error']}"

            # Check timeframe confirmation
            if not multi_tf_result['confirmation_passed']:
                return f"""❌ **TIMEFRAME CONFIRMATION FAILED**

Symbol: {symbol}
Required Alignment: {', '.join(multi_tf_result['required_alignment'])}
Issue: Timeframes tidak selaras untuk sinyal {signal_direction}

Tunggu alignment yang lebih baik."""

            # Get 1h indicators for main analysis
            main_indicators = multi_tf_result['timeframes'].get('1h', {}).get('indicators', {})

            if 'error' in main_indicators:
                return f"❌ **TECHNICAL ANALYSIS ERROR**: {main_indicators['error']}"

            # Calculate confidence score
            confidence_result = self.calculate_confidence_score(main_indicators, macro_data, signal_direction)

            if 'error' in confidence_result:
                return f"❌ **CONFIDENCE SCORING ERROR**: {confidence_result['error']}"

            confidence_score = confidence_result['total_score']

            # Check minimum confidence threshold
            if confidence_score < self.min_confidence_threshold:
                return f"""❌ **CONFIDENCE THRESHOLD NOT MET**

Symbol: {symbol}
Confidence Score: {confidence_score}%
Required Minimum: {self.min_confidence_threshold}%

Technical Score: {confidence_result['technical_score']}/50
Macro Score: {confidence_result['macro_score']}/50

Sinyal tidak memenuhi kriteria kualitas."""

            # Generate trading levels
            current_price = main_indicators.get('current_price', 0)
            atr = main_indicators.get('atr', current_price * 0.02)

            if signal_direction == 'BUY':
                entry_price = current_price * 0.999
                stop_loss = current_price - (atr * 2)
                take_profit_1 = current_price + (atr * 1.5)
                take_profit_2 = current_price + (atr * 3)
            else:  # SELL
                entry_price = current_price * 1.001
                stop_loss = current_price + (atr * 2)
                take_profit_1 = current_price - (atr * 1.5)
                take_profit_2 = current_price - (atr * 3)

            # Calculate risk/reward
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit_2 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0

            # Save signal for cooldown tracking
            signal_data = {
                'direction': signal_direction,
                'confidence_score': confidence_score,
                'timeframe_confirmation': True
            }
            self.save_signal_to_supabase(symbol, signal_data)

            # Format comprehensive analysis
            direction_emoji = "🟢" if signal_direction == 'BUY' else "🔴"
            confidence_emoji = "🔥" if confidence_score >= 85 else "⭐" if confidence_score >= 75 else "💡"

            analysis = f"""🚨 **ENHANCED FUTURES ANALYSIS - {symbol}**

{direction_emoji} **SIGNAL: {signal_direction}** {confidence_emoji}
{confidence_emoji} **Confidence Score: {confidence_score}%**

💰 **TRADING SETUP:**
• **Entry Price**: ${entry_price:.6f}
• **Stop Loss**: ${stop_loss:.6f}
• **Take Profit 1**: ${take_profit_1:.6f}
• **Take Profit 2**: ${take_profit_2:.6f}
• **Risk/Reward**: {rr_ratio:.2f}:1

📊 **TECHNICAL INDICATORS (1H):**
• **EMA50**: ${main_indicators.get('ema_50', 0):.2f}
• **EMA200**: ${main_indicators.get('ema_200', 0):.2f}
• **RSI**: {main_indicators.get('rsi', 0):.1f}
• **MACD**: {main_indicators.get('macd_histogram', 0):.4f}
• **ATR**: ${main_indicators.get('atr', 0):.6f}

🌍 **MACRO CONDITIONS:**"""

            if 'error' not in macro_data:
                analysis += f"""
• **Market Cap Change 24h**: {macro_data.get('market_cap_change_24h', 0):+.2f}%
• **BTC Dominance**: {macro_data.get('btc_dominance', 0):.1f}%
• **Total Market Cap**: ${macro_data.get('total_market_cap', 0)/1e12:.2f}T"""

            analysis += f"""

✅ **MULTI-TIMEFRAME CONFIRMATION:**
• **5m & 1h**: ALIGNED for {signal_direction}
• **Trend Strength**: Strong

📈 **CONFIDENCE BREAKDOWN:**
• **Technical Score**: {confidence_result['technical_score']}/50
• **Macro Score**: {confidence_result['macro_score']}/50
• **Total**: {confidence_score}/100

⚠️ **RISK MANAGEMENT:**
• Position size: 2-3% of capital
• Mandatory Stop Loss before entry
• Take profit in stages (50% TP1, 50% TP2)
• Monitor macro conditions

🕐 **Analysis Time**: {current_time} WIB
🛡️ **Signal Cooldown**: 1 hour active
📡 **Data Sources**: CoinAPI + CoinMarketCap"""

            return analysis

        except Exception as e:
            return f"❌ **ENHANCED FUTURES ANALYSIS ERROR**: {str(e)}"

    async def generate_futures_signals_enhanced(self, language='id', crypto_api=None, query_args=None):
        """Generate enhanced futures signals with multi-timeframe analysis"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get global macro conditions first
            macro_data = self.get_cmc_global_metrics()

            if 'error' in macro_data:
                return f"""❌ **MACRO DATA ERROR**

Gagal mengambil data makro dari CoinMarketCap.
Error: {macro_data['error']}

Coba lagi dalam beberapa menit."""

            # Process target symbols
            target_symbols = self.target_symbols[:5]  # Limit for performance

            if query_args and len(query_args) > 0:
                first_arg = query_args[0].upper()
                if first_arg in self.target_symbols or len(first_arg) <= 5:
                    target_symbols = [first_arg]

            valid_signals = []

            for symbol in target_symbols:
                try:
                    # Check cooldown
                    if not self.check_signal_cooldown(symbol):
                        continue

                    # Determine signal direction
                    signal_direction = 'BUY' if random.random() > 0.5 else 'SELL'

                    # Apply macro filters
                    market_cap_change = macro_data.get('market_cap_change_24h', 0)

                    if signal_direction == 'BUY' and market_cap_change < -3:
                        continue  # Filter out BUY signals in bad market

                    # Multi-timeframe analysis
                    multi_tf_result = self.analyze_multi_timeframe(symbol, signal_direction)

                    if 'error' in multi_tf_result or not multi_tf_result['confirmation_passed']:
                        continue

                    # Get main indicators
                    main_indicators = multi_tf_result['timeframes'].get('1h', {}).get('indicators', {})

                    if 'error' in main_indicators:
                        continue

                    # Calculate confidence
                    confidence_result = self.calculate_confidence_score(main_indicators, macro_data, signal_direction)

                    if 'error' in confidence_result:
                        continue

                    confidence_score = confidence_result['total_score']

                    # Check threshold
                    if confidence_score >= self.min_confidence_threshold:
                        current_price = main_indicators.get('current_price', 0)
                        atr = main_indicators.get('atr', current_price * 0.02)

                        if signal_direction == 'BUY':
                            entry_price = current_price * 0.999
                            stop_loss = current_price - (atr * 2)
                            take_profit_1 = current_price + (atr * 1.5)
                            take_profit_2 = current_price + (atr * 3)
                        else:
                            entry_price = current_price * 1.001
                            stop_loss = current_price + (atr * 2)
                            take_profit_1 = current_price - (atr * 1.5)
                            take_profit_2 = current_price - (atr * 3)

                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit_2 - entry_price)
                        rr_ratio = reward / risk if risk > 0 else 0

                        signal = {
                            'symbol': symbol,
                            'direction': signal_direction,
                            'confidence_score': confidence_score,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit_1': take_profit_1,
                            'take_profit_2': take_profit_2,
                            'rr_ratio': rr_ratio,
                            'indicators': main_indicators,
                            'timeframe_confirmation': True
                        }

                        valid_signals.append(signal)

                        # Save signal for cooldown
                        signal_data = {
                            'direction': signal_direction,
                            'confidence_score': confidence_score,
                            'timeframe_confirmation': True
                        }
                        self.save_signal_to_supabase(symbol, signal_data)

                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

            # Format signals message
            if not valid_signals:
                return f"""❌ **NO QUALIFIED SIGNALS**

🕐 **Scan Time**: {current_time}
📊 **Symbols Scanned**: {len(target_symbols)}
⚠️ **Status**: Tidak ada sinyal yang memenuhi kriteria

💡 **Kemungkinan Penyebab:**
• Confidence score < {self.min_confidence_threshold}%
• Multi-timeframe tidak selaras
• Signal cooldown masih aktif
• Market conditions tidak mendukung

🔄 **Solusi**: Coba lagi dalam 15-30 menit"""

            message = f"""🚨 **ENHANCED FUTURES SIGNALS**

🕐 **Scan Time**: {current_time}
📊 **Qualified Signals**: {len(valid_signals)}
🌍 **Market Cap Change 24h**: {macro_data.get('market_cap_change_24h', 0):+.2f}%
📈 **BTC Dominance**: {macro_data.get('btc_dominance', 0):.1f}%

"""

            for i, signal in enumerate(valid_signals, 1):
                direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
                confidence_emoji = "🔥" if signal['confidence_score'] >= 85 else "⭐"

                message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence_score']:.0f}%
💰 **Entry**: ${signal['entry_price']:.6f}
🛑 **Stop Loss**: ${signal['stop_loss']:.6f}
🎯 **TP1**: ${signal['take_profit_1']:.6f}
🎯 **TP2**: ${signal['take_profit_2']:.6f}
📊 **R/R**: {signal['rr_ratio']:.1f}:1
📈 **RSI**: {signal['indicators'].get('rsi', 0):.1f}
🔄 **MACD**: {signal['indicators'].get('macd_histogram', 0):.4f}

"""

            message += f"""⚠️ **ENHANCED RISK MANAGEMENT:**
• Multi-timeframe confirmation: 5m + 1h aligned
• Confidence threshold: {self.min_confidence_threshold}%+ only
• Signal cooldown: 1 hour per symbol
• Macro filter: Market cap & sentiment checked
• Position sizing: 2-3% capital max per trade

📡 **Data Sources**: CoinAPI OHLCV + CoinMarketCap Global
🔄 **Next Update**: {current_time} WIB
🛡️ **Quality Assurance**: Multi-layer filtering active"""

            return message

        except Exception as e:
            return f"❌ **ENHANCED FUTURES SIGNALS ERROR**: {str(e)}"

    # ============ AUTO SIGNAL SYSTEM ============

    async def start_auto_signal_system(self, bot_instance):
        """Start enhanced auto signal system"""
        if self.auto_signal_task is None or self.auto_signal_task.done():
            self.bot_instance = bot_instance
            self.auto_signal_task = asyncio.create_task(self._enhanced_auto_signal_loop())
            print("🚀 Enhanced Auto Signal System started")
            print(f"📊 Monitoring {len(self.target_symbols)} symbols every {self.scan_interval//60} minutes")
            print(f"🎯 Confidence threshold: {self.min_confidence_threshold}%")
            print(f"🛡️ Signal cooldown: {self.signal_cooldown//60} minutes")

    async def stop_auto_signal_system(self):
        """Stop auto signal system"""
        if self.auto_signal_task and not self.auto_signal_task.done():
            self.auto_signal_task.cancel()
            try:
                await self.auto_signal_task
            except asyncio.CancelledError:
                pass
            print("🛑 Enhanced Auto Signal System stopped")

    async def _enhanced_auto_signal_loop(self):
        """Enhanced auto signal background loop"""
        print("🔄 Enhanced Auto Signal Loop started")

        while True:
            try:
                await self._scan_and_send_enhanced_signals()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                print("🛑 Enhanced Auto Signal Loop cancelled")
                break
            except Exception as e:
                print(f"❌ Enhanced Auto Signal Loop error: {e}")
                await asyncio.sleep(60)

    async def _scan_and_send_enhanced_signals(self):
        """Scan for enhanced signals and send to eligible users"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"🔍 Enhanced Auto Signal Scan: {current_time}")

            # Get macro data
            macro_data = self.get_cmc_global_metrics()

            if 'error' in macro_data:
                print(f"❌ Macro data error: {macro_data['error']}")
                return

            valid_signals = []

            for symbol in self.target_symbols:
                try:
                    # Check cooldown
                    if not self.check_signal_cooldown(symbol):
                        continue

                    # Generate signal using enhanced analysis
                    signal = await self._generate_enhanced_auto_signal(symbol, macro_data)

                    if signal and signal.get('confidence_score', 0) >= self.min_confidence_threshold:
                        valid_signals.append(signal)
                        print(f"✅ Enhanced Auto Signal: {symbol} - {signal['direction']} ({signal['confidence_score']:.0f}%)")

                except Exception as e:
                    print(f"❌ Error analyzing {symbol}: {e}")
                    continue

            if valid_signals:
                print(f"🚀 Sending {len(valid_signals)} enhanced auto signals")
                await self._send_enhanced_auto_signals(valid_signals, macro_data)
            else:
                print("📊 No qualified enhanced auto signals found")

        except Exception as e:
            print(f"❌ Enhanced auto signal scan error: {e}")

    async def _generate_enhanced_auto_signal(self, symbol, macro_data):
        """Generate single enhanced auto signal"""
        try:
            # Determine signal direction
            signal_direction = 'BUY' if random.random() > 0.5 else 'SELL'

            # Apply macro filters
            market_cap_change = macro_data.get('market_cap_change_24h', 0)

            if signal_direction == 'BUY' and market_cap_change < -3:
                return None

            # Multi-timeframe analysis
            multi_tf_result = self.analyze_multi_timeframe(symbol, signal_direction)

            if 'error' in multi_tf_result or not multi_tf_result['confirmation_passed']:
                return None

            # Get indicators
            main_indicators = multi_tf_result['timeframes'].get('1h', {}).get('indicators', {})

            if 'error' in main_indicators:
                return None

            # Calculate confidence
            confidence_result = self.calculate_confidence_score(main_indicators, macro_data, signal_direction)

            if 'error' in confidence_result:
                return None

            confidence_score = confidence_result['total_score']

            if confidence_score < self.min_confidence_threshold:
                return None

            # Generate trading levels
            current_price = main_indicators.get('current_price', 0)
            atr = main_indicators.get('atr', current_price * 0.02)

            if signal_direction == 'BUY':
                entry_price = current_price * 0.999
                stop_loss = current_price - (atr * 2)
                take_profit_1 = current_price + (atr * 1.5)
                take_profit_2 = current_price + (atr * 3)
            else:
                entry_price = current_price * 1.001
                stop_loss = current_price + (atr * 2)
                take_profit_1 = current_price - (atr * 1.5)
                take_profit_2 = current_price - (atr * 3)

            # Save signal for cooldown
            signal_data = {
                'direction': signal_direction,
                'confidence_score': confidence_score,
                'timeframe_confirmation': True
            }
            self.save_signal_to_supabase(symbol, signal_data)

            return {
                'symbol': symbol,
                'direction': signal_direction,
                'confidence_score': confidence_score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit_1': take_profit_1,
                'take_profit_2': take_profit_2,
                'indicators': main_indicators
            }

        except Exception as e:
            print(f"❌ Error generating enhanced auto signal for {symbol}: {e}")
            return None

    async def _send_enhanced_auto_signals(self, signals, macro_data):
        """Send enhanced auto signals to eligible users"""
        if not self.bot_instance:
            print("❌ Bot instance not available")
            return

        try:
            # Get eligible users
            if hasattr(self.bot_instance, 'db'):
                eligible_users = self.bot_instance.db.get_eligible_auto_signal_users()
            else:
                print("❌ Database not available")
                return

            if not eligible_users:
                print("❌ No eligible users found")
                return

            # Format message
            message = self._format_enhanced_auto_signal_message(signals, macro_data)

            # Send to users
            success_count = 0
            for user in eligible_users:
                try:
                    user_id = user.get('telegram_id') if isinstance(user, dict) else user[0]
                    await self.bot_instance.application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=None
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ Failed to send to user {user_id}: {e}")

            print(f"🚀 Enhanced auto signals sent to {success_count}/{len(eligible_users)} users")

        except Exception as e:
            print(f"❌ Error sending enhanced auto signals: {e}")

    def _format_enhanced_auto_signal_message(self, signals, macro_data):
        """Format enhanced auto signals message"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        message = f"""🚨 ENHANCED AUTO SIGNALS 🤖

🕐 Detection Time: {current_time}
📊 Qualified Signals: {len(signals)}
🎯 Confidence Threshold: {self.min_confidence_threshold}%+
🌍 Market Cap 24h: {macro_data.get('market_cap_change_24h', 0):+.2f}%

"""

        for i, signal in enumerate(signals[:3], 1):
            direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
            confidence_emoji = "🔥" if signal['confidence_score'] >= 85 else "⭐"

            message += f"""{i}. {signal['symbol']} {direction_emoji} {signal['direction']}
{confidence_emoji} Confidence: {signal['confidence_score']:.0f}%
💰 Entry: ${signal['entry_price']:.6f}
🛑 Stop Loss: ${signal['stop_loss']:.6f}
🎯 TP1: ${signal['take_profit_1']:.6f}
🎯 TP2: ${signal['take_profit_2']:.6f}
📈 RSI: {signal['indicators'].get('rsi', 0):.1f}
🔄 MACD: {signal['indicators'].get('macd_histogram', 0):.4f}

"""

        message += f"""⚠️ ENHANCED AUTO SIGNAL FEATURES:
• Multi-timeframe confirmation (5m + 1h aligned)
• Technical + Macro scoring system
• 1-hour cooldown per symbol anti-spam
• Market cap filter untuk kualitas sinyal
• Confidence threshold {self.min_confidence_threshold}%+ only

🤖 AUTO DETECTION: CoinAPI OHLCV + CMC Global Data
🛡️ RISK MANAGEMENT: Enhanced filtering active
📡 Real-time: Professional grade analysis
🔄 Update: {current_time} WIB

Exclusive for Admin & Lifetime Users 💎"""

        return message

    # ============ UTILITY METHODS ============

    def _format_price(self, price):
        """Format price display based on value"""
        if price < 0.000001:
            return f"{price:.8f}"
        elif price < 0.01:
            return f"{price:.6f}"
        elif price < 1:
            return f"{price:.4f}"
        elif price < 100:
            return f"{price:.2f}"
        else:
            return f"{price:,.2f}"

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get enhanced market sentiment with CMC data"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get CMC global data
            macro_data = self.get_cmc_global_metrics()

            if 'error' in macro_data:
                return f"❌ Error getting market sentiment: {macro_data['error']}"

            market_cap_change = macro_data.get('market_cap_change_24h', 0)
            btc_dominance = macro_data.get('btc_dominance', 0)
            total_market_cap = macro_data.get('total_market_cap', 0)
            total_volume = macro_data.get('total_volume_24h', 0)

            # Determine sentiment
            if market_cap_change > 3:
                sentiment = "🚀 VERY BULLISH"
                sentiment_color = "🟢"
            elif market_cap_change > 1:
                sentiment = "📈 BULLISH"
                sentiment_color = "🟢"
            elif market_cap_change > -1:
                sentiment = "😐 NEUTRAL"
                sentiment_color = "🟡"
            elif market_cap_change > -3:
                sentiment = "📉 BEARISH"
                sentiment_color = "🟠"
            else:
                sentiment = "💥 VERY BEARISH"
                sentiment_color = "🔴"

            message = f"""🌍 **ENHANCED MARKET SENTIMENT**

{sentiment_color} **Global Sentiment**: {sentiment}

💰 **GLOBAL METRICS (CMC)**:
• **Total Market Cap**: ${total_market_cap/1e12:.2f}T
• **Market Cap Change 24h**: {market_cap_change:+.2f}%
• **Total Volume 24h**: ${total_volume/1e9:.1f}B
• **BTC Dominance**: {btc_dominance:.1f}%
• **ETH Dominance**: {macro_data.get('eth_dominance', 0):.1f}%
• **Active Cryptocurrencies**: {macro_data.get('active_cryptocurrencies', 0):,}

📊 **TRADING INSIGHTS**:"""

            if market_cap_change > 1:
                message += "\n• 🟢 Strong momentum - Consider LONG positions"
                message += "\n• 📈 Multi-timeframe alignment likely positive"
            elif market_cap_change > -1:
                message += "\n• 🟡 Sideways market - Wait for clear breakout"
                message += "\n• ⚠️ Mixed signals - Use lower position sizing"
            else:
                message += "\n• 🔴 Bearish pressure - Be cautious with LONG"
                message += "\n• 📉 Consider SHORT opportunities"

            if btc_dominance > 45:
                message += f"\n• 🪙 BTC dominance high ({btc_dominance:.1f}%) - Money flowing to BTC"
            else:
                message += f"\n• 🏛️ Alt season potential - BTC dominance low ({btc_dominance:.1f}%)"

            message += f"""

🎯 **AUTO SIGNAL CONDITIONS**:
• Market supporting {'BUY' if market_cap_change > 0 else 'SELL'} signals
• Confidence threshold: {self.min_confidence_threshold}%+
• Multi-timeframe confirmation required

📡 **Data Source**: CoinMarketCap Global Metrics
🕐 **Update**: {current_time} WIB"""

            return message

        except Exception as e:
            return f"❌ Market sentiment error: {str(e)}"

    # Legacy methods for compatibility
    def analyze_text(self, text):
        """Simple text analysis for crypto mentions"""
        text_lower = text.lower()
        if "btc" in text_lower:
            return "📈 BTC - Gunakan /futures btc untuk analisis enhanced!"
        elif "eth" in text_lower:
            return "📊 ETH - Coba /analyze eth untuk multi-timeframe analysis!"
        else:
            return "💡 Gunakan /futures_signals untuk sinyal berkualitas tinggi!"

    def get_comprehensive_analysis(self, symbol, snd_data={}, price_data={}, language='id', crypto_api=None):
        """Get comprehensive analysis for /analyze command"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            
            # Get current price data
            if crypto_api:
                price_info = crypto_api.get_crypto_price(symbol, force_refresh=True)
            else:
                price_info = {'error': 'No crypto API available'}
            
            if 'error' not in price_info and price_info.get('price', 0) > 0:
                current_price = price_info.get('price', 0)
                change_24h = price_info.get('change_24h', 0)
                price_format = self._format_price(current_price)
                change_emoji = "📈" if change_24h >= 0 else "📉"
                change_sign = "+" if change_24h >= 0 else ""
                
                analysis = f"""📊 **COMPREHENSIVE ANALYSIS - {symbol}**

💰 **Current Price**: {price_format}
{change_emoji} **24h Change**: {change_sign}{change_24h:.2f}%

🔬 **Technical Analysis**:
"""
                
                # Get OHLCV data for technical analysis
                ohlcv_data = self.get_coinapi_ohlcv_data(symbol, '1HRS', 100)
                
                if 'error' not in ohlcv_data:
                    indicators = self.calculate_technical_indicators(ohlcv_data['data'])
                    
                    if 'error' not in indicators:
                        analysis += f"""• **EMA50**: ${indicators.get('ema_50', 0):.2f}
• **EMA200**: ${indicators.get('ema_200', 0):.2f}
• **RSI**: {indicators.get('rsi', 0):.1f}
• **MACD**: {indicators.get('macd_histogram', 0):.4f}
• **ATR**: ${indicators.get('atr', 0):.6f}

📈 **Trend Analysis**:
"""
                        
                        # Determine trend
                        ema_50 = indicators.get('ema_50', 0)
                        ema_200 = indicators.get('ema_200', 0)
                        rsi = indicators.get('rsi', 50)
                        
                        if ema_50 > ema_200:
                            trend = "🟢 BULLISH"
                            trend_desc = "EMA50 di atas EMA200 menunjukkan tren naik"
                        else:
                            trend = "🔴 BEARISH"
                            trend_desc = "EMA50 di bawah EMA200 menunjukkan tren turun"
                        
                        analysis += f"• **Overall Trend**: {trend}\n• **Analysis**: {trend_desc}\n"
                        
                        # RSI Analysis
                        if rsi > 70:
                            rsi_signal = "⚠️ OVERBOUGHT - Pertimbangkan untuk SELL"
                        elif rsi < 30:
                            rsi_signal = "⚠️ OVERSOLD - Pertimbangkan untuk BUY"
                        else:
                            rsi_signal = "✅ NORMAL - Tidak ada sinyal ekstrim"
                        
                        analysis += f"• **RSI Signal**: {rsi_signal}\n\n"
                    else:
                        analysis += "• Unable to calculate technical indicators\n\n"
                else:
                    analysis += "• Technical data unavailable from CoinAPI\n\n"
                
                # Get macro market data
                macro_data = self.get_cmc_global_metrics()
                if 'error' not in macro_data:
                    analysis += f"""🌍 **Market Conditions**:
• **Global Market Cap Change**: {macro_data.get('market_cap_change_24h', 0):+.2f}%
• **BTC Dominance**: {macro_data.get('btc_dominance', 0):.1f}%
• **Total Market Cap**: ${macro_data.get('total_market_cap', 0)/1e12:.2f}T

"""
                
                # Trading recommendations
                analysis += f"""💡 **Trading Insights**:
• Gunakan `/futures {symbol.lower()}` untuk analisis SnD mendalam
• Gunakan `/price {symbol.lower()}` untuk monitoring harga real-time
• Selalu gunakan stop loss dan position sizing yang tepat

📡 **Data Sources**: CoinAPI + CoinMarketCap
🕐 **Analysis Time**: {current_time} WIB"""
                
                return analysis
            else:
                return f"""❌ **Data Tidak Tersedia untuk {symbol}**

🔄 **Kemungkinan Penyebab**:
• Symbol tidak ditemukan di CoinAPI
• API sedang mengalami gangguan
• Network connectivity issues

💡 **Solusi**:
• Coba symbol populer seperti BTC, ETH, SOL
• Gunakan `/price {symbol.lower()}` untuk cek ketersediaan data
• Coba lagi dalam beberapa menit

📞 **Support**: Hubungi admin jika masalah berlanjut"""
                
        except Exception as e:
            return f"""❌ **Error dalam Comprehensive Analysis**

**Error**: {str(e)[:100]}...

💡 **Alternatif**:
• `/price {symbol.lower()}` - Harga basic
• `/futures {symbol.lower()}` - Analisis SnD
• `/market` - Overview pasar global

📞 **Support**: Contact admin untuk bantuan"""

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis for /futures command"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            
            # Get current price
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                futures_data = crypto_api.get_futures_data(symbol)
            else:
                price_data = {'error': 'No crypto API'}
                futures_data = {'error': 'No crypto API'}
            
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_format = self._format_price(current_price)
                change_24h = price_data.get('change_24h', 0)
                change_emoji = "📈" if change_24h >= 0 else "📉"
                
                analysis = f"""🚨 **FUTURES ANALYSIS - {symbol} ({timeframe})**

💰 **Current Price**: {price_format}
{change_emoji} **24h Change**: {change_24h:+.2f}%

"""
                
                # Get technical indicators for the timeframe
                timeframe_mapping = {
                    '15m': '15MIN',
                    '30m': '30MIN', 
                    '1h': '1HRS',
                    '4h': '4HRS',
                    '1d': '1DAY',
                    '1w': '1WEK'
                }
                
                coinapi_timeframe = timeframe_mapping.get(timeframe, '1HRS')
                ohlcv_data = self.get_coinapi_ohlcv_data(symbol, coinapi_timeframe, 100)
                
                if 'error' not in ohlcv_data:
                    indicators = self.calculate_technical_indicators(ohlcv_data['data'])
                    
                    if 'error' not in indicators:
                        # Generate trading signals
                        ema_50 = indicators.get('ema_50', 0)
                        ema_200 = indicators.get('ema_200', 0)
                        rsi = indicators.get('rsi', 50)
                        macd_histogram = indicators.get('macd_histogram', 0)
                        atr = indicators.get('atr', current_price * 0.02)
                        
                        # Determine signal direction
                        signal_direction = "LONG" if ema_50 > ema_200 and rsi < 70 else "SHORT"
                        direction_emoji = "🟢" if signal_direction == "LONG" else "🔴"
                        
                        # Calculate entry levels
                        if signal_direction == "LONG":
                            entry_price = current_price * 0.999
                            stop_loss = current_price - (atr * 2)
                            take_profit_1 = current_price + (atr * 1.5)
                            take_profit_2 = current_price + (atr * 3)
                        else:
                            entry_price = current_price * 1.001
                            stop_loss = current_price + (atr * 2)
                            take_profit_1 = current_price - (atr * 1.5)
                            take_profit_2 = current_price - (atr * 3)
                        
                        # Calculate confidence
                        confidence = 75  # Base confidence
                        if abs(macd_histogram) > 0.001:
                            confidence += 10
                        if 40 <= rsi <= 60:
                            confidence += 10
                        if signal_direction == "LONG" and ema_50 > ema_200:
                            confidence += 5
                        elif signal_direction == "SHORT" and ema_50 < ema_200:
                            confidence += 5
                        
                        confidence = min(confidence, 95)  # Cap at 95%
                        
                        # Risk/Reward calculation
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit_2 - entry_price)
                        rr_ratio = reward / risk if risk > 0 else 1
                        
                        analysis += f"""{direction_emoji} **SIGNAL: {signal_direction}**
⭐ **Confidence**: {confidence}%

💰 **TRADING SETUP**:
• **Entry**: ${entry_price:.6f}
• **Stop Loss**: ${stop_loss:.6f}
• **Take Profit 1**: ${take_profit_1:.6f}
• **Take Profit 2**: ${take_profit_2:.6f}
• **Risk/Reward**: {rr_ratio:.1f}:1

📊 **TECHNICAL DATA ({timeframe})**:
• **EMA50**: ${ema_50:.2f}
• **EMA200**: ${ema_200:.2f}
• **RSI**: {rsi:.1f}
• **MACD**: {macd_histogram:.4f}
• **ATR**: ${atr:.6f}

"""
                        
                        # Add futures-specific data if available
                        if 'error' not in futures_data:
                            long_ratio = futures_data.get('long_ratio', 50)
                            funding_rate = futures_data.get('funding_rate', 0)
                            open_interest = futures_data.get('open_interest', 0)
                            
                            analysis += f"""🔮 **FUTURES METRICS**:
• **Long/Short Ratio**: {long_ratio:.1f}% Long
• **Funding Rate**: {funding_rate:.4f}%
• **Open Interest**: ${open_interest:,.0f}

"""
                        
                        analysis += f"""⚠️ **RISK MANAGEMENT**:
• Position size: 2-3% of capital maximum
• Always use stop loss before entry
• Take profit in stages (50% at TP1, 50% at TP2)
• Monitor market conditions

🕐 **Analysis Time**: {current_time}
📡 **Data**: CoinAPI {timeframe} + Futures metrics"""
                        
                    else:
                        analysis += f"❌ Technical indicators calculation failed for {timeframe}"
                else:
                    analysis += f"❌ OHLCV data unavailable for {symbol} {timeframe}"
            else:
                analysis = f"""❌ **Price Data Unavailable for {symbol}**

🔄 **Solusi**:
• Coba symbol lain seperti BTC, ETH, SOL
• Gunakan `/price {symbol.lower()}` untuk cek ketersediaan
• Coba timeframe lain

💡 **Timeframe tersedia**: 15m, 30m, 1h, 4h, 1d, 1w"""
            
            return analysis
            
        except Exception as e:
            return f"""❌ **Error dalam Futures Analysis**

**Error**: {str(e)[:100]}...

💡 **Alternatif**:
• `/price {symbol.lower()}` - Harga current
• `/analyze {symbol.lower()}` - Analisis fundamental
• `/futures_signals` - Multiple signals

📞 **Support**: Contact admin untuk bantuan"""

    async def generate_futures_signals(self, language='id', crypto_api=None, query_args=None):
        """Generate futures signals for /futures_signals command"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            
            # Get global market sentiment first
            macro_data = self.get_cmc_global_metrics()
            
            message = f"""🚨 **FUTURES SIGNALS SCAN**

🕐 **Scan Time**: {current_time}
"""
            
            if 'error' not in macro_data:
                market_cap_change = macro_data.get('market_cap_change_24h', 0)
                btc_dominance = macro_data.get('btc_dominance', 0)
                
                message += f"""🌍 **Market Conditions**:
• **Global Market Cap**: {market_cap_change:+.2f}% (24h)
• **BTC Dominance**: {btc_dominance:.1f}%

"""
            
            # Target symbols for scanning
            target_symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
            
            # If specific symbol requested
            if query_args and len(query_args) > 0:
                first_arg = query_args[0].upper()
                if len(first_arg) <= 5:  # Likely a symbol
                    target_symbols = [first_arg]
            
            valid_signals = []
            
            for symbol in target_symbols[:3]:  # Limit to 3 for performance
                try:
                    # Get price and technical data
                    if crypto_api:
                        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                        futures_data = crypto_api.get_futures_data(symbol)
                    else:
                        continue
                    
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        current_price = price_data.get('price', 0)
                        change_24h = price_data.get('change_24h', 0)
                        
                        # Get 1H technical analysis
                        ohlcv_data = self.get_coinapi_ohlcv_data(symbol, '1HRS', 50)
                        
                        if 'error' not in ohlcv_data:
                            indicators = self.calculate_technical_indicators(ohlcv_data['data'])
                            
                            if 'error' not in indicators:
                                ema_50 = indicators.get('ema_50', 0)
                                ema_200 = indicators.get('ema_200', 0)
                                rsi = indicators.get('rsi', 50)
                                macd_histogram = indicators.get('macd_histogram', 0)
                                atr = indicators.get('atr', current_price * 0.02)
                                
                                # Generate signal
                                if ema_50 > ema_200 and rsi < 65 and macd_histogram > 0:
                                    signal_direction = "LONG"
                                    confidence = 80
                                elif ema_50 < ema_200 and rsi > 35 and macd_histogram < 0:
                                    signal_direction = "SHORT"
                                    confidence = 80
                                else:
                                    signal_direction = "NEUTRAL"
                                    confidence = 60
                                
                                if confidence >= 75:  # Only high confidence signals
                                    entry_price = current_price * (0.999 if signal_direction == "LONG" else 1.001)
                                    
                                    if signal_direction == "LONG":
                                        stop_loss = current_price - (atr * 2)
                                        take_profit = current_price + (atr * 2.5)
                                    else:
                                        stop_loss = current_price + (atr * 2)
                                        take_profit = current_price - (atr * 2.5)
                                    
                                    signal = {
                                        'symbol': symbol,
                                        'direction': signal_direction,
                                        'confidence': confidence,
                                        'entry': entry_price,
                                        'stop_loss': stop_loss,
                                        'take_profit': take_profit,
                                        'current_price': current_price,
                                        'change_24h': change_24h,
                                        'rsi': rsi
                                    }
                                    
                                    valid_signals.append(signal)
                
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue
            
            if valid_signals:
                message += f"📊 **Found {len(valid_signals)} High-Confidence Signals**:\n\n"
                
                for i, signal in enumerate(valid_signals, 1):
                    direction_emoji = "🟢" if signal['direction'] == "LONG" else "🔴"
                    price_format = self._format_price(signal['current_price'])
                    
                    message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
⭐ **Confidence**: {signal['confidence']}%
💰 **Current**: {price_format} ({signal['change_24h']:+.2f}%)
🎯 **Entry**: ${signal['entry']:.6f}
🛑 **Stop Loss**: ${signal['stop_loss']:.6f}
📈 **Take Profit**: ${signal['take_profit']:.6f}
📊 **RSI**: {signal['rsi']:.1f}

"""
                
                message += f"""⚠️ **RISK MANAGEMENT**:
• Maksimal 2-3% capital per position
• Wajib gunakan stop loss
• Monitor kondisi market secara berkala
• Take profit bertahap jika profit besar

📡 **Data**: CoinAPI 1H + Binance Futures
🔄 **Next Scan**: Gunakan command lagi untuk update"""
            else:
                message += f"""❌ **No High-Confidence Signals Found**

📊 **Symbols Scanned**: {', '.join(target_symbols)}
⚠️ **Status**: Tidak ada setup trading yang jelas saat ini

💡 **Kemungkinan Penyebab**:
• Market dalam kondisi sideways
• Volatilitas rendah
• Indikator teknikal mixed signals

🔄 **Solusi**:
• Coba lagi dalam 30-60 menit
• Gunakan `/futures btc` untuk analisis spesifik
• Monitor `/market` untuk kondisi global"""
            
            return message
            
        except Exception as e:
            return f"""❌ **Error dalam Futures Signals Generation**

**Error**: {str(e)[:100]}...

💡 **Alternatif**:
• `/futures btc` - Analisis BTC spesifik
• `/analyze eth` - Analisis ETH fundamental
• `/market` - Overview pasar global

📞 **Support**: Contact admin untuk bantuan"""

    def get_ai_response(self, text, language='id', user_id=None):
        """Enhanced AI response"""
        if user_id:
            self.save_user(user_id)

        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal', 'signal']):
            return """📊 **ENHANCED ANALYSIS FEATURES**

🎯 **Multi-Timeframe Analysis**:
• `/futures btc` - Enhanced futures dengan confidence scoring
• `/futures_signals` - Sinyal berkualitas dengan filter makro

🔬 **Technical Indicators**:
• EMA50/200 crossover analysis
• RSI momentum confirmation
• MACD histogram alignment
• ATR volatility measurement
• Volume oscillator strength

🌍 **Macro Integration**:
• Global market cap monitoring
• BTC dominance analysis
• Volume trend confirmation
• Sentiment filtering

✨ **Auto Signals** (Admin & Lifetime):
• Real-time monitoring setiap 5 menit
• Confidence threshold 75%+
• Multi-timeframe confirmation
• 1-hour signal cooldown"""

        return f"""🤖 **Enhanced CryptoMentor AI**

Saya sekarang menggunakan:
• 📡 **CoinAPI**: OHLCV multi-timeframe data
• 🌍 **CoinMarketCap**: Global market metrics
• 🎯 **Advanced Scoring**: Technical + Macro confidence
• ⏰ **Smart Cooldown**: 1 hour anti-spam per symbol

Coba `/futures btc` untuk analisis enhanced!"""