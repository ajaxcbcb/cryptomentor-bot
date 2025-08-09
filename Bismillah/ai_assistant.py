# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
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

        # Initialize Supabase connection with validation
        self.supabase = self._init_supabase()
        self.supabase_connected = self._validate_supabase_connection()

        # Admin logging system - ensure this is always initialized
        self.admin_log = []

        # Enhanced configuration
        self.auto_signal_enabled = True
        self.auto_signal_task = None
        self.signal_cooldown = 3600  # 1 hour cooldown
        self.scan_interval = 5 * 60  # 5 minutes scan interval
        self.min_confidence_threshold = 75  # Minimum 75% confidence

        # Target symbols for futures analysis
        self.target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

        # Signal tracking
        self.last_signals = {}

        # Timeframes for multi-timeframe analysis
        self.timeframes = {
            '15m': '15MIN',
            '1h': '1HRS',
            '4h': '4HRS',
            '1d': '1DAY'
        }

        print(f"✅ CryptoMentor AI initialized - Professional Trading Assistant")

    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            # Try Supabase first
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = <REDACTED_SUPABASE_KEY>

            # Try Replit PostgreSQL
            database_url = os.environ.get("DATABASE_URL")

            if supabase_url and supabase_anon_key:
                supabase: Client = create_client(supabase_url, supabase_anon_key)
                print("✅ Supabase client initialized successfully")
                return supabase
            elif database_url:
                print("✅ Replit PostgreSQL detected - creating Supabase client")
                # For Replit PostgreSQL, we'd need to adapt or use direct postgres connection
                # For now, just log that it's available
                print("💡 PostgreSQL available but Supabase client needs direct DB connection")
                return None
            else:
                print("⚠️ No database credentials found - using SQLite fallback")
                return None

        except Exception as e:
            print(f"⚠️ Database initialization failed: {e} - using SQLite fallback")
            return None

    def _validate_supabase_connection(self):
        """Validate Supabase connection"""
        try:
            if not self.supabase:
                print("⚠️ Supabase client not available - using SQLite fallback")
                return False

            # Simple connection test - don't fail if tables don't exist yet
            test_result = self.supabase.from_('users').select('*').limit(1).execute()
            print("✅ Supabase connection validated successfully")
            return True
        except Exception as e:
            print(f"⚠️ Supabase connection test failed: {e} - using SQLite fallback")
            return False

    def _log_admin_error(self, command, error_detail):
        """Log errors for admin only"""
        # Initialize admin_log if it doesn't exist
        if not hasattr(self, 'admin_log'):
            self.admin_log = []

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'error': error_detail,
            'supabase_status': bool(self.supabase),
            'supabase_connected': getattr(self, 'supabase_connected', False)
        }
        self.admin_log.append(log_entry)
        # Keep only last 50 entries
        if len(self.admin_log) > 50:
            self.admin_log = self.admin_log[-50:]

    def _escape_markdown_v2(self, text):
        """Escape special characters for MarkdownV2"""
        if not isinstance(text, str):
            return str(text)

        # Characters that need escaping in MarkdownV2
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '{', '}', '.', '!']

        for char in escape_chars:
            text = text.replace(char, f'\\{char}')

        return text

    def _safe_format_price(self, price):
        """Format price safely for Markdown"""
        formatted = self._format_price(price)
        return self._escape_markdown_v2(formatted)

    def _safe_format_percentage(self, value, decimal_places=2):
        """Format percentage safely for Markdown"""
        formatted = self._format_percentage(value, decimal_places)
        return self._escape_markdown_v2(formatted)

    def _check_database_required(self, command_name):
        """Check if database is required and available for command"""
        # Most commands don't actually require database for core functionality
        # Only user-specific features like premium status, credits need database
        if command_name in ['ANALYZE', 'FUTURES', 'FUTURES_SIGNALS', 'MARKET_SENTIMENT']:
            # These commands work fine without database
            return True, None

        if not self.supabase_connected:
            print(f"⚠️ Database not available for {command_name} - continuing with limited functionality")
            return True, None  # Don't block execution
        return True, None

    def _get_database_error_message(self):
        """Get user-friendly database error message"""
        return """⚠️ Database tidak tersedia saat ini\\. 

✅ Analisis tetap berfungsi normal\\!
💡 Fitur premium dan riwayat mungkin terbatas\\."""

    def _validate_markdown_output(self, text):
        """Validate if text is safe for Markdown parsing"""
        try:
            # Simple validation - check for common problematic patterns
            if not isinstance(text, str):
                return False

            # Check for unescaped special characters in problematic contexts
            problematic_patterns = [
                r'[^\\]_[^\\]',  # Unescaped underscores
                r'[^\\]\*[^\\]',  # Unescaped asterisks
                r'[^\\]\[[^\\]',  # Unescaped brackets
            ]

            import re
            for pattern in problematic_patterns:
                if re.search(pattern, text):
                    return False

            return True
        except Exception:
            return False

    def _safe_output(self, text, fallback_plain=True):
        """Ensure output is safe for Telegram"""
        try:
            if self._validate_markdown_output(text):
                return text, 'MarkdownV2'
            elif fallback_plain:
                # Remove all markdown formatting for plain text
                import re
                plain_text = re.sub(r'\\(.)', r'\1', text)  # Remove escape characters
                plain_text = re.sub(r'[*_`\[\]()~>#+\-={}\.!]', '', plain_text)  # Remove formatting
                return plain_text, None
            else:
                return text, None
        except Exception as e:
            self._log_admin_error("SAFE_OUTPUT", f"Format validation failed: {e}")
            return "Terjadi kesalahan format pesan. Hubungi admin.", None

    def _get_wib_time(self):
        """Get current time in WIB (Asia/Jakarta)"""
        try:
            wib_tz = timezone(timedelta(hours=7))
            return datetime.now(wib_tz).strftime('%H:%M:%S WIB')
        except:
            return datetime.now().strftime('%H:%M:%S WIB')

    def _normalize_data(self, data, field_aliases):
        """Normalize data fields using aliases"""
        if not isinstance(data, dict):
            return None

        for alias in field_aliases:
            if alias in data and data[alias] is not None:
                try:
                    return float(data[alias]) if isinstance(data[alias], (str, int, float)) else data[alias]
                except (ValueError, TypeError):
                    continue
        return None

    def _format_price(self, price):
        """Format price display based on value"""
        if price is None or price == 0:
            return "N/A"
        try:
            price = float(price)
            if price < 0.000001:
                return f"${price:.8f}"
            elif price < 0.01:
                return f"${price:.6f}"
            elif price < 1:
                return f"${price:.4f}"
            elif price < 100:
                return f"${price:.2f}"
            else:
                return f"${price:,.2f}"
        except:
            return "N/A"

    def _format_percentage(self, value, decimal_places=2):
        """Format percentage values"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):+.{decimal_places}f}%"
        except:
            return "N/A"

    def _calculate_confidence_score(self, technical_data, market_data, futures_data):
        """Calculate confidence score with breakdown"""
        try:
            # Initialize scores
            tf_score = 0  # Multi-timeframe alignment (35%)
            indicator_score = 0  # Indicator consensus (30%)
            liquidity_score = 0  # Futures metrics (20%)
            freshness_score = 15  # Data freshness (15%) - assume good

            # Multi-timeframe alignment (35 points max)
            if technical_data:
                ema_50 = self._normalize_data(technical_data, ['ema_50', 'EMA50', 'ema50'])
                ema_200 = self._normalize_data(technical_data, ['ema_200', 'EMA200', 'ema200'])

                if ema_50 and ema_200:
                    if ema_50 > ema_200:  # Bullish alignment
                        tf_score = 35
                    elif ema_50 < ema_200:  # Bearish alignment
                        tf_score = 25
                    else:
                        tf_score = 15

            # Indicator consensus (30 points max)
            if technical_data:
                rsi = self._normalize_data(technical_data, ['rsi', 'RSI'])
                macd = self._normalize_data(technical_data, ['macd_histogram', 'macd', 'MACD'])

                if rsi:
                    if 40 <= rsi <= 60:  # Normal range
                        indicator_score += 15
                    elif 30 <= rsi <= 70:  # Acceptable range
                        indicator_score += 10

                if macd:
                    if abs(macd) > 0.001:  # Strong MACD signal
                        indicator_score += 15
                    else:
                        indicator_score += 5

            # Liquidity/Futures metrics (20 points max)
            if futures_data:
                oi = self._normalize_data(futures_data, ['open_interest', 'oi', 'openInterest'])
                funding = self._normalize_data(futures_data, ['funding_rate', 'funding', 'fundingRate'])

                if oi and oi > 0:
                    liquidity_score += 10

                if funding and abs(funding) < 0.1:  # Normal funding rate
                    liquidity_score += 10

            total_score = tf_score + indicator_score + liquidity_score + freshness_score

            return {
                'total': min(total_score, 100),
                'breakdown': {
                    'timeframe': tf_score,
                    'indicators': indicator_score,
                    'liquidity': liquidity_score,
                    'freshness': freshness_score
                }
            }

        except Exception as e:
            return {
                'total': 50,
                'breakdown': {
                    'timeframe': 0,
                    'indicators': 0,
                    'liquidity': 0,
                    'freshness': 0
                },
                'error': str(e)
            }

    def get_coinapi_ohlcv_data(self, symbol, timeframe='1HRS', limit=200):
        """Get OHLCV data from CoinAPI"""
        try:
            if not self.coinapi_key:
                return {'error': 'CoinAPI key required'}

            # Symbol mapping
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
                if data and len(data) > 20:
                    df = pd.DataFrame(data)
                    df['time_period_start'] = pd.to_datetime(df['time_period_start'])
                    df = df.sort_values('time_period_start')

                    return {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'data': df,
                        'count': len(data),
                        'source': 'coinapi',
                        'success': True
                    }
                else:
                    return {'error': 'Insufficient data', 'success': False}
            else:
                return {'error': f'API error: {response.status_code}', 'success': False}

        except Exception as e:
            return {'error': f'Request failed: {str(e)}', 'success': False}

    def calculate_technical_indicators(self, df):
        """Calculate technical indicators from OHLCV data"""
        try:
            if df is None or len(df) < 50:
                return {'error': 'Insufficient data'}

            # Ensure numeric columns
            for col in ['price_close', 'price_high', 'price_low', 'volume_traded']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            indicators = {}

            # EMA calculations
            indicators['ema_50'] = df['price_close'].ewm(span=50).mean().iloc[-1]
            indicators['ema_200'] = df['price_close'].ewm(span=min(200, len(df))).mean().iloc[-1]
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

            # Store recent volumes for volume trend analysis
            indicators['recent_volumes'] = df['volume_traded'].tolist()

            return indicators

        except Exception as e:
            return {'error': f'Calculation failed: {str(e)}'}

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
                        'timestamp': self._get_wib_time(),
                        'source': 'coinmarketcap',
                        'success': True
                    }
                else:
                    return {'error': 'API response error', 'success': False}
            else:
                return {'error': f'HTTP error: {response.status_code}', 'success': False}

        except Exception as e:
            return {'error': f'Request failed: {str(e)}', 'success': False}

    def save_user(self, user_id, username=""):
        """Save user to database"""
        try:
            if not self.supabase:
                return False

            existing_user = self.supabase.table('users').select('*').eq('id', str(user_id)).execute()
            if existing_user.data:
                return True

            user_data = {
                'id': str(user_id),
                'username': username,
                'joined_at': datetime.now().isoformat(),
                'status': 'free'
            }

            result = self.supabase.table('users').insert(user_data).execute()
            return bool(result.data)

        except Exception as e:
            print(f"❌ Error saving user: {e}")
            return False

    def greet(self):
        return f"Halo! Saya {self.name}, asisten trading crypto profesional dengan analisis multi-timeframe dan supply/demand zones."

    def help_message(self):
        return """🤖 **CryptoMentor AI - Professional Trading Assistant**

📊 **ANALISIS KOMPREHENSIF:**
• `/analyze <symbol>` - Multi-timeframe + Supply/Demand analysis
• `/futures <symbol> [timeframe]` - Futures analysis spesifik
• `/futures_signals` - Scan sinyal high-confidence multi-aset

💰 **MARKET OVERVIEW:**
• `/market` - Global market conditions
• `/price <symbol>` - Real-time price check

🎯 **FITUR UNGGULAN:**
• Multi-timeframe confirmation (1h, 4h, Daily)
• Supply & Demand zones identification
• Professional confidence scoring
• Futures metrics integration

📡 **Data Sources**: CoinAPI + CoinMarketCap + Binance
🔄 **Update**: Real-time dengan normalisasi data

⚠️ **Disclaimer**: Bukan saran investasi. Gunakan manajemen risiko yang tepat."""

    # ============ MAIN COMMAND HANDLERS ============

    def get_comprehensive_analysis(self, symbol, snd_data={}, price_data={}, language='id', crypto_api=None):
        """Enhanced comprehensive analysis matching professional futures format"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("ANALYZE")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()
            symbol = symbol.upper()

            # Get current price data with extended info
            if crypto_api:
                price_info = crypto_api.get_crypto_price(symbol, force_refresh=True)
                futures_data = crypto_api.get_futures_data(symbol)
                coin_info = crypto_api.get_coin_info(symbol) if hasattr(crypto_api, 'get_coin_info') else {}
            else:
                price_info = {'error': 'API unavailable'}
                futures_data = {}
                coin_info = {}

            if 'error' in price_info or not price_info.get('success'):
                return self._error_fallback(symbol, "price data")

            current_price = self._normalize_data(price_info, ['price', 'current_price', 'last', 'close'])
            change_24h = self._normalize_data(price_info, ['change_24h', 'price_change_24h', 'percent_change_24h'])
            volume_24h = self._normalize_data(price_info, ['volume_24h', 'volume', 'total_volume'])
            market_cap = self._normalize_data(price_info, ['market_cap', 'marketCap'])

            if not current_price:
                return self._error_fallback(symbol, "price normalization")

            # Multi-timeframe technical analysis
            timeframes_data = {}
            main_indicators = {}

            for tf_name, tf_api in [('1h', '1HRS'), ('4h', '4HRS'), ('1d', '1DAY')]:
                ohlcv = self.get_coinapi_ohlcv_data(symbol, tf_api, 100)
                if ohlcv.get('success'):
                    indicators = self.calculate_technical_indicators(ohlcv['data'])
                    if 'error' not in indicators:
                        timeframes_data[tf_name] = indicators
                        if tf_name == '1h':  # Use 1h as main timeframe
                            main_indicators = indicators

            if not main_indicators:
                return self._error_fallback(symbol, "technical analysis")

            # Enhanced signal generation with confidence
            signal_data = self._generate_enhanced_trading_signal(
                main_indicators, timeframes_data.get('4h', {}), futures_data, current_price, {}
            )

            # Enhanced Supply & Demand zones (2 levels each)
            enhanced_snd_zones = self._get_enhanced_supply_demand_zones(symbol, current_price, main_indicators, crypto_api)

            # Trading levels calculation
            trading_levels = self._calculate_advanced_trading_levels(
                current_price, signal_data, main_indicators, enhanced_snd_zones
            )

            # Market conditions and global metrics
            market_data = self.get_cmc_global_metrics()

            # Get coin fundamentals if available
            coin_fundamentals = self._get_coin_fundamentals(symbol, price_info, coin_info)

            # Determine confidence level description
            confidence = signal_data['confidence']
            if confidence >= 85:
                confidence_desc = "🔥 Very High"
                confidence_emoji = "🔥"
            elif confidence >= 75:
                confidence_desc = "⚡ High"
                confidence_emoji = "⚡"
            elif confidence >= 65:
                confidence_desc = "💡 Medium"
                confidence_emoji = "💡"
            else:
                confidence_desc = "⚠️ Low"
                confidence_emoji = "⚠️"

            # Direction formatting
            direction_emoji = "🟢" if signal_data['direction'] in ['BUY', 'LONG'] else "🔴" if signal_data['direction'] in ['SELL', 'SHORT'] else "🟡"

            # Technical indicators formatting
            rsi_value = main_indicators.get('rsi', 0)
            rsi_condition = "Oversold" if rsi_value < 30 else "Overbought" if rsi_value > 70 else "Normal"

            macd_value = main_indicators.get('macd_histogram', 0)
            macd_condition = "Bullish" if macd_value > 0 else "Bearish"

            # Format comprehensive analysis matching futures style
            analysis = f"""🔍 **PROFESSIONAL COMPREHENSIVE ANALYSIS - {symbol}**

🕐 **Analysis Time**: {current_time}
💰 **Current Price**: ${current_price:,.6f}
📊 **24h Change**: {change_24h:+.2f}%

{direction_emoji} **TRADING SIGNAL**: {signal_data['direction']}
{confidence_emoji} **Confidence**: {confidence:.1f}% ({confidence_desc})
🎯 **Strategy**: {signal_data.get('strategy', 'Technical Analysis')}
⚡ **Time Horizon**: {signal_data.get('time_horizon', '4-24 hours')}

"""

            # Add enhanced S&D zones
            analysis += f"""
🎯 **ENHANCED SUPPLY & DEMAND ZONES**:
• 🔴 Supply Zone 1: ${enhanced_snd_zones.get('supply_1', current_price * 1.02):,.6f} ({((enhanced_snd_zones.get('supply_1', current_price * 1.02)/current_price-1)*100):+.1f}%)
• 🔴 Supply Zone 2: ${enhanced_snd_zones.get('supply_2', current_price * 1.04):,.6f} ({((enhanced_snd_zones.get('supply_2', current_price * 1.04)/current_price-1)*100):+.1f}%)
• 🟢 Demand Zone 1: ${enhanced_snd_zones.get('demand_1', current_price * 0.98):,.6f} ({((enhanced_snd_zones.get('demand_1', current_price * 0.98)/current_price-1)*100):+.1f}%)
• 🟢 Demand Zone 2: ${enhanced_snd_zones.get('demand_2', current_price * 0.96):,.6f} ({((enhanced_snd_zones.get('demand_2', current_price * 0.96)/current_price-1)*100):+.1f}%)
• 📍 Current Position: {enhanced_snd_zones.get('position', 'Between zones')}
• 💪 Zone Strength: {enhanced_snd_zones.get('strength', 'Medium')}"""

            # Add futures metrics if available
            analysis += "\n\n🔮 **FUTURES MARKET METRICS**:"
            if futures_data and futures_data.get('success'):
                data = futures_data.get('data', {})
                long_short = data.get('long_short', {})
                funding_details = data.get('funding_details', {})
                open_interest = data.get('open_interest', {})

                long_ratio = long_short.get('long_ratio', 50)
                funding_rate = funding_details.get('current_rate', 0)
                oi_total = open_interest.get('total', 0)
                sentiment = long_short.get('sentiment', 'Neutral')

                funding_condition = "Bullish Bias" if funding_rate < -0.01 else "Bearish Bias" if funding_rate > 0.01 else "Balanced"

                analysis += f"""
• 📊 Long/Short Ratio: {long_ratio:.1f}% Long | {100-long_ratio:.1f}% Short
• 💰 Funding Rate: {funding_rate*100:.4f}% ({funding_condition})
• 🌊 Open Interest: ${oi_total:,.0f}
• 🧠 Market Sentiment: {sentiment}
• ⚖️ Futures Bias: {self._get_futures_bias(long_ratio, funding_rate)}"""
            else:
                analysis += """
• Futures metrics based on spot market analysis
• Technical indicators show market structure"""

            # Higher timeframe confirmation
            if timeframes_data.get('4h'):
                htf_indicators = timeframes_data['4h']
                htf_trend = "Bullish" if htf_indicators.get('ema_50', 0) > htf_indicators.get('ema_200', 0) else "Bearish"
                analysis += f"""

📈 **HIGHER TIMEFRAME (4H) CONFIRMATION**:
• 🎯 4H Trend: {htf_trend}
• 📊 4H EMA50 vs EMA200: {htf_trend} alignment
• ✅ Multi-TF Confirmation: {signal_data.get('mtf_confirmation', 'Partial')}"""

            # Advanced insights and risk management
            analysis += f"""

💡 **ADVANCED TRADING INSIGHTS**:
{self._get_advanced_trading_insights(signal_data, trading_levels, confidence)}

⚠️ **RISK MANAGEMENT PROTOCOL**:
• Gunakan proper position sizing (1-3% per trade)
• Set stop loss sebelum entry
• Take profit secara bertahap
• Monitor market conditions
• DYOR sebelum trading

🎯 **EXECUTION CHECKLIST**:
• ✅ Confirm price action at entry zone
• ✅ Monitor volume for confirmation
• ✅ Set stop loss BEFORE entry
• ✅ Prepare for partial profit taking
• ✅ Watch for news/events impact

📡 **Data Sources**: CoinAPI OHLCV + Binance Futures + SnD Analysis + Fundamentals
🔄 **Update Frequency**: Real-time price + Multi-timeframe technical refresh"""

            return analysis

        except Exception as e:
            return self._error_fallback(symbol, f"comprehensive analysis: {str(e)[:50]}")

    async def get_futures_analysis(self, symbol, timeframe='15m', language='id', crypto_api=None):
        """Enhanced futures analysis with comprehensive breakdown"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("FUTURES")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()
            symbol = symbol.upper()

            # Get comprehensive data
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                futures_data = crypto_api.get_futures_data(symbol)
                snd_data = crypto_api.analyze_supply_demand(symbol, timeframe)
            else:
                return self._error_fallback(symbol, "API connection")

            if 'error' in price_data or not price_data.get('success'):
                return self._error_fallback(symbol, "price data")

            current_price = self._normalize_data(price_data, ['price', 'current_price'])
            change_24h = self._normalize_data(price_data, ['change_24h', 'price_change_24h', 'percent_change_24h'])

            # Multi-timeframe technical analysis
            timeframe_mapping = {
                '15m': '15MIN', '30m': '30MIN', '1h': '1HRS',
                '4h': '4HRS', '1d': '1DAY', '1w': '1WEK'
            }
            api_timeframe = timeframe_mapping.get(timeframe, '1HRS')

            # Get multiple timeframes for better analysis
            primary_ohlcv = self.get_coinapi_ohlcv_data(symbol, api_timeframe, 100)
            higher_tf_ohlcv = self.get_coinapi_ohlcv_data(symbol, '4HRS', 100)

            if not primary_ohlcv.get('success'):
                return self._error_fallback(symbol, f"OHLCV data for {timeframe}")

            primary_indicators = self.calculate_technical_indicators(primary_ohlcv['data'])
            higher_tf_indicators = {}
            if higher_tf_ohlcv.get('success'):
                higher_tf_indicators = self.calculate_technical_indicators(higher_tf_ohlcv['data'])

            if 'error' in primary_indicators:
                return self._error_fallback(symbol, "technical indicators")

            # Enhanced signal generation with multiple timeframe confirmation
            signal_data = self._generate_enhanced_trading_signal(
                primary_indicators, higher_tf_indicators, futures_data, current_price, snd_data
            )

            # Advanced trading levels calculation
            trading_levels = self._calculate_advanced_trading_levels(
                current_price, signal_data, primary_indicators, snd_data
            )

            # Determine confidence level description
            confidence = signal_data['confidence']
            if confidence >= 85:
                confidence_desc = "🔥 Very High"
                confidence_emoji = "🔥"
            elif confidence >= 75:
                confidence_desc = "⚡ High"
                confidence_emoji = "⚡"
            elif confidence >= 65:
                confidence_desc = "💡 Medium"
                confidence_emoji = "💡"
            else:
                confidence_desc = "⚠️ Low"
                confidence_emoji = "⚠️"

            # Direction formatting
            direction_emoji = "🟢" if signal_data['direction'] in ['BUY', 'LONG'] else "🔴" if signal_data['direction'] in ['SELL', 'SHORT'] else "🟡"

            # Technical indicators formatting
            rsi_value = primary_indicators.get('rsi', 0)
            rsi_condition = "Oversold" if rsi_value < 30 else "Overbought" if rsi_value > 70 else "Normal"

            macd_value = primary_indicators.get('macd_histogram', 0)
            macd_condition = "Bullish" if macd_value > 0 else "Bearish"

            # Create comprehensive analysis
            analysis = f"""🔍 **PROFESSIONAL FUTURES ANALYSIS - {symbol} ({timeframe})**

🕐 **Analysis Time**: {current_time}
💰 **Current Price**: ${current_price:,.6f}
📊 **24h Change**: {change_24h:+.2f}%

{direction_emoji} **TRADING SIGNAL**: {signal_data['direction']}
{confidence_emoji} **Confidence**: {confidence:.1f}% ({confidence_desc})
🎯 **Strategy**: {signal_data.get('strategy', 'Swing Trading')}
⚡ **Time Horizon**: {signal_data.get('time_horizon', '4-24 hours')}

```
💰 DETAILED TRADING SETUP:
• Entry Zone: ${trading_levels['entry_min']:.6f} - ${trading_levels['entry_max']:.6f}
• Optimal Entry: ${trading_levels['entry']:.6f}
• Stop Loss: ${trading_levels['stop_loss']:.6f}
• TP1 (50%): ${trading_levels['tp1']:.6f}
• TP2 (30%): ${trading_levels['tp2']:.6f} 
• TP3 (20%): ${trading_levels['tp3']:.6f}
• Risk/Reward: {trading_levels['rr_ratio']:.1f}:1
• Max Risk: {trading_levels['risk_percentage']:.1f}% per position
```

```
🔬 TECHNICAL ANALYSIS ({timeframe}):
• EMA50: ${primary_indicators.get('ema_50', 0):,.4f}
• EMA200: ${primary_indicators.get('ema_200', 0):,.4f}
• RSI(14): {rsi_value:.1f} ({rsi_condition})
• MACD: {macd_value:.4f} ({macd_condition})
• ATR: ${primary_indicators.get('atr', 0):,.4f}
• Volume Trend: {signal_data.get('volume_trend', 'Normal')}
```

🎯 **SUPPLY & DEMAND ZONES**:"""

            # Add Supply & Demand analysis if available
            if snd_data.get('success'):
                supply_1 = snd_data.get('Supply 1', current_price * 1.02)
                demand_1 = snd_data.get('Demand 1', current_price * 0.98)
                analysis += f"""
• 🔴 Supply Zone 1: ${supply_1:,.6f} ({((supply_1/current_price-1)*100):+.1f}%)
• 🟢 Demand Zone 1: ${demand_1:,.6f} ({((demand_1/current_price-1)*100):+.1f}%)
• 📍 Current Position: {self._get_zone_position(current_price, supply_1, demand_1)}
• 💪 Zone Strength: {snd_data.get('zone_strength', 'Medium')}"""
            else:
                analysis += """
• Supply/Demand analysis temporarily unavailable
• Using technical levels for zone identification"""

            # Add futures metrics
            analysis += "\n\n🔮 **FUTURES MARKET METRICS**:"
            if futures_data and futures_data.get('success'):
                # Extract futures data safely
                data = futures_data.get('data', {})
                long_short = data.get('long_short', {})
                funding_details = data.get('funding_details', {})
                open_interest = data.get('open_interest', {})

                long_ratio = long_short.get('long_ratio', 50)
                funding_rate = funding_details.get('current_rate', 0)
                oi_total = open_interest.get('total', 0)
                sentiment = long_short.get('sentiment', 'Neutral')

                # Funding rate analysis
                funding_condition = "Bullish Bias" if funding_rate < -0.01 else "Bearish Bias" if funding_rate > 0.01 else "Balanced"

                analysis += f"""
• 📊 Long/Short Ratio: {long_ratio:.1f}% Long | {100-long_ratio:.1f}% Short
• 💰 Funding Rate: {funding_rate*100:.4f}% ({funding_condition})
• 🌊 Open Interest: ${oi_total:,.0f}
• 🧠 Market Sentiment: {sentiment}
• ⚖️ Futures Bias: {self._get_futures_bias(long_ratio, funding_rate)}"""
            else:
                analysis += """
• Futures metrics temporarily unavailable
• Analysis based on spot market data"""

            # Higher timeframe confirmation
            if higher_tf_indicators:
                htf_trend = "Bullish" if higher_tf_indicators.get('ema_50', 0) > higher_tf_indicators.get('ema_200', 0) else "Bearish"
                analysis += f"""

📈 **HIGHER TIMEFRAME (4H) CONFIRMATION**:
• 🎯 4H Trend: {htf_trend}
• 📊 4H EMA50 vs EMA200: {htf_trend} alignment
• ✅ Multi-TF Confirmation: {signal_data.get('mtf_confirmation', 'Partial')}"""

            analysis += f"""

💡 **ADVANCED TRADING INSIGHTS**:
{self._get_advanced_trading_insights(signal_data, trading_levels, confidence)}

⚠️ **RISK MANAGEMENT PROTOCOL**:
• Gunakan proper position sizing (1-3% per trade)
• Set stop loss sebelum entry
• Take profit secara bertahap
• Monitor market conditions
• DYOR sebelum trading

🎯 **EXECUTION CHECKLIST**:
• ✅ Confirm price action at entry zone
• ✅ Monitor volume for confirmation
• ✅ Set stop loss BEFORE entry
• ✅ Prepare for partial profit taking
• ✅ Watch for news/events impact

📡 **Data Sources**: CoinAPI OHLCV + Binance Futures + SnD Analysis
🔄 **Update Frequency**: Real-time price + 15min technical refresh"""

            return analysis

        except Exception as e:
            return self._error_fallback(symbol, f"enhanced futures analysis: {str(e)[:50]}")

    async def generate_futures_signals(self, language='id', crypto_api=None, query_args=None):
        """Generate futures signals following system prompt template"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("FUTURES_SIGNALS")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()

            # Get global market conditions
            market_data = self.get_cmc_global_metrics()
            market_conditions = self._format_market_conditions(market_data)

            # Target symbols for scanning - use more symbols for better signal detection
            target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

            # If specific symbol requested, use that
            if query_args and len(query_args) > 0:
                first_arg = query_args[0].upper()
                if len(first_arg) <= 5:
                    target_symbols = [first_arg]

            high_confidence_signals = []

            # Scan symbols for signals with improved logic
            for symbol in target_symbols:
                try:
                    signal = await self._enhanced_scan_symbol_for_signal(symbol, crypto_api)
                    if signal and signal.get('confidence', 0) >= 75:  # Minimum 75% confidence
                        high_confidence_signals.append(signal)
                        print(f"✅ Found signal: {symbol} - {signal['confidence']}% ({signal['direction']})")
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
                    continue

            # Sort by confidence and take only the best signal
            if high_confidence_signals:
                high_confidence_signals = sorted(high_confidence_signals, key=lambda x: x.get('confidence', 0), reverse=True)[:1]

            # Format response with safe markdown
            if not high_confidence_signals:
                no_signals_msg = f"""🚨 **FUTURES SIGNALS SCAN**

🕐 **Scan Time**: {self._escape_markdown_v2(current_time)}
🌍 **Market Conditions**: {self._escape_markdown_v2(market_conditions)}

❌ **No High\\-Confidence Signals Found**

📊 **Symbols Scanned**: {self._escape_markdown_v2(', '.join(target_symbols))}
⚠️ **Status**: Tidak ada setup trading yang jelas saat ini

💡 **Kemungkinan Penyebab**:
• Market dalam kondisi consolidation
• Volatilitas rendah saat ini
• Menunggu momentum yang lebih jelas

🔄 **Alternatif**:
• Coba `/futures btc` untuk analisis spesifik
• Gunakan `/analyze eth` untuk analisis fundamental
• Monitor kondisi market dengan `/market`"""

                safe_text, parse_mode = self._safe_output(no_signals_msg)
                return safe_text

            # Format signals found with safe markdown
            message = f"""🚨 **AUTO SIGNALS - SUPPLY & DEMAND ANALYSIS**

🕐 **Scan Time**: {self._escape_markdown_v2(current_time)}
📊 **Signals Found**: {len(high_confidence_signals)}

"""

            for i, signal in enumerate(high_confidence_signals, 1):
                direction_emoji = "🟢" if signal['direction'] in ['LONG', 'BUY'] else "🔴"

                # Get price data for 24h change
                symbol = signal['symbol']
                price_data = crypto_api.get_crypto_price(symbol) if crypto_api else {}
                change_24h = price_data.get('change_24h', 0) if price_data.get('success') else 0

                message += f"""{i}. {signal['symbol']} {direction_emoji} {signal['direction']}
⭐️ Confidence: {signal['confidence']:.1f}%
💰 Entry: {self._format_price(signal['entry'])}
🛑 Stop Loss: {self._format_price(signal['sl'])}
🎯 TP1: {self._format_price(signal['tp1'])}
🎯 TP2: {self._format_price(signal['tp2'])}
📊 R/R Ratio: {signal.get('rr', '2.0:1')}
🔄 Trend: {signal.get('primary_trend', 'Bullish' if signal['direction'] in ['LONG', 'BUY'] else 'Bearish')}
⚡️ Structure: {signal.get('structure', signal['direction'])} Bias
🧠 Reason: {signal.get('reason', 'Technical analysis with confluence')}
📈 24h Change: {self._format_percentage(change_24h)}

"""

            message += f"""⚠️ **TRADING DISCLAIMER**:
• Signals berbasis Supply & Demand analysis
• Gunakan proper risk management
• Position sizing sesuai risk level
• DYOR sebelum trading

🎯 Futures signals dengan confidence 75%+ only
📡 Next scan in 30 minutes"""

            # Validate and return safe output
            safe_text, parse_mode = self._safe_output(message)
            return safe_text

        except Exception as e:
            return self._error_fallback("FUTURES_SIGNALS", f"scan process: {str(e)[:50]}")

    # ============ HELPER METHODS ============

    def _analyze_trend(self, timeframes_data, current_price):
        """Enhanced trend analysis across multiple timeframes with strength assessment"""
        try:
            trends = []
            trend_strengths = []

            for tf, data in timeframes_data.items():
                ema_50 = data.get('ema_50')
                ema_200 = data.get('ema_200')
                rsi = data.get('rsi', 50)
                macd = data.get('macd_histogram', 0)

                if ema_50 and ema_200:
                    # Basic trend direction
                    if ema_50 > ema_200:
                        trends.append('BULLISH')
                        # Calculate trend strength
                        ema_distance = ((ema_50 - ema_200) / ema_200) * 100
                        strength = min(100, max(0, ema_distance * 50))  # Scale to 0-100
                    else:
                        trends.append('BEARISH')
                        ema_distance = ((ema_200 - ema_50) / ema_50) * 100
                        strength = min(100, max(0, ema_distance * 50))

                    # Adjust strength based on RSI and MACD
                    if trends[-1] == 'BULLISH':
                        if rsi > 60 and macd > 0:
                            strength *= 1.2  # Strong bullish confluence
                        elif rsi < 40 or macd < 0:
                            strength *= 0.7  # Weakening bullish trend
                    else:  # BEARISH
                        if rsi < 40 and macd < 0:
                            strength *= 1.2  # Strong bearish confluence
                        elif rsi > 60 or macd > 0:
                            strength *= 0.7  # Weakening bearish trend

                    trend_strengths.append(min(100, strength))

            # Determine overall trend with strength
            if not trends:
                return {
                    'trend': 'SIDEWAYS',
                    'trend_emoji': '🟡',
                    'reasoning': 'Insufficient data untuk trend analysis',
                    'strength': 0
                }

            bullish_count = trends.count('BULLISH')
            bearish_count = trends.count('BEARISH')
            avg_strength = sum(trend_strengths) / len(trend_strengths) if trend_strengths else 0

            if bullish_count > bearish_count:
                strength_text = "Strong" if avg_strength > 70 else "Moderate" if avg_strength > 40 else "Weak"
                return {
                    'trend': 'BULLISH',
                    'trend_emoji': '🟢',
                    'reasoning': f'{strength_text} bullish trend - EMA50 > EMA200 di {bullish_count}/{len(trends)} timeframes',
                    'strength': avg_strength
                }
            elif bearish_count > bullish_count:
                strength_text = "Strong" if avg_strength > 70 else "Moderate" if avg_strength > 40 else "Weak"
                return {
                    'trend': 'BEARISH',
                    'trend_emoji': '🔴',
                    'reasoning': f'{strength_text} bearish trend - EMA50 < EMA200 di {bearish_count}/{len(trends)} timeframes',
                    'strength': avg_strength
                }
            else:
                return {
                    'trend': 'SIDEWAYS',
                    'trend_emoji': '🟡',
                    'reasoning': 'Mixed signals antar timeframes - trend belum jelas',
                    'strength': avg_strength
                }

        except Exception as e:
            return {
                'trend': 'SIDEWAYS',
                'trend_emoji': '🟡',
                'reasoning': 'Error dalam enhanced trend analysis',
                'strength': 0
            }

    def _get_supply_demand_zones(self, symbol, current_price, crypto_api):
        """Get supply and demand zones"""
        try:
            if crypto_api:
                snd_data = crypto_api.analyze_supply_demand(symbol, '1h')
                if snd_data.get('success'):
                    supply_1 = snd_data.get('Supply 1', current_price * 1.025)
                    demand_1 = snd_data.get('Demand 1', current_price * 0.975)

                    # Determine position
                    if current_price > supply_1:
                        position = "Above supply zone - momentum bullish"
                    elif current_price < demand_1:
                        position = "Below demand zone - momentum bearish"
                    else:
                        position = "Between key zones - range-bound"

                    return {
                        'supply_1': supply_1,
                        'demand_1': demand_1,
                        'position': position
                    }

            # Fallback calculation
            return {
                'supply_1': current_price * 1.025,
                'demand_1': current_price * 0.975,
                'position': 'SnD zones calculated from price levels'
            }

        except Exception as e:
            return {
                'supply_1': current_price * 1.025 if current_price else 0,
                'demand_1': current_price * 0.975 if current_price else 0,
                'position': 'SnD analysis unavailable'
            }

    def _get_enhanced_supply_demand_zones(self, symbol, current_price, indicators, crypto_api):
        """Get enhanced supply and demand zones with multiple levels"""
        try:
            # Get basic SnD data
            basic_snd = self._get_supply_demand_zones(symbol, current_price, crypto_api)

            # Calculate enhanced zones using technical indicators
            atr = indicators.get('atr', current_price * 0.02)
            ema_50 = indicators.get('ema_50', current_price)
            ema_200 = indicators.get('ema_200', current_price)

            # Calculate multiple resistance and support levels
            # Supply zones (resistance levels)
            supply_1 = max(basic_snd.get('supply_1', current_price * 1.02), ema_50 * 1.015)
            supply_2 = supply_1 + (atr * 2)

            # Demand zones (support levels)  
            demand_1 = min(basic_snd.get('demand_1', current_price * 0.98), ema_50 * 0.985)
            demand_2 = demand_1 - (atr * 2)

            # Determine current position relative to zones
            if current_price > supply_1:
                position = "Above Supply Zone 1 - Strong Bullish Momentum"
                strength = "Strong"
            elif current_price > demand_1:
                if current_price > ema_50:
                    position = "Between Zones - Bullish Bias"
                    strength = "Medium"
                else:
                    position = "Between Zones - Bearish Bias"  
                    strength = "Medium"
            elif current_price < demand_2:
                position = "Below Demand Zone 2 - Strong Bearish Momentum"
                strength = "Strong"
            else:
                position = "Near Demand Zone 1 - Support Testing"
                strength = "Medium"

            return {
                'supply_1': supply_1,
                'supply_2': supply_2,
                'demand_1': demand_1,
                'demand_2': demand_2,
                'position': position,
                'strength': strength,
                'atr_based': True
            }

        except Exception as e:
            # Fallback to basic calculation
            return {
                'supply_1': current_price * 1.025,
                'supply_2': current_price * 1.05,
                'demand_1': current_price * 0.975,
                'demand_2': current_price * 0.95,
                'position': 'Enhanced SnD analysis unavailable',
                'strength': 'Unknown',
                'error': str(e)
            }

    def _get_coin_fundamentals(self, symbol, price_info, coin_info):
        """Get coin fundamental information"""
        try:
            # Extract basic info
            market_cap = self._normalize_data(price_info, ['market_cap', 'marketCap'])
            volume_24h = self._normalize_data(price_info, ['volume_24h', 'volume'])
            rank = self._normalize_data(price_info, ['rank', 'cmc_rank', 'market_cap_rank'])

            # Format market cap
            if market_cap and market_cap > 0:
                if market_cap > 1e12:
                    mc_format = f"${market_cap/1e12:.2f}T"
                elif market_cap > 1e9:
                    mc_format = f"${market_cap/1e9:.2f}B"
                elif market_cap > 1e6:
                    mc_format = f"${market_cap/1e6:.2f}M"
                else:
                    mc_format = f"${market_cap:,.0f}"
            else:
                mc_format = "N/A"

            # Format volume
            if volume_24h and volume_24h > 0:
                if volume_24h > 1e9:
                    vol_format = f"${volume_24h/1e9:.2f}B"
                elif volume_24h > 1e6:
                    vol_format = f"${volume_24h/1e6:.1f}M"
                else:
                    vol_format = f"${volume_24h:,.0f}"
            else:
                vol_format = "N/A"

            fundamentals = f"""• 🏆 Market Cap Rank: #{rank if rank else 'N/A'}
• 💰 Market Cap: {mc_format}
• 📊 24h Volume: {vol_format}"""

            # Add coin info if available
            if coin_info and isinstance(coin_info, dict):
                name = coin_info.get('name', symbol)
                category = coin_info.get('category', 'N/A')
                tags = coin_info.get('tags', [])

                if name and name != symbol:
                    fundamentals += f"\n• 📝 Full Name: {name}"
                if category and category != 'N/A':
                    fundamentals += f"\n• 🏷️ Category: {category}"
                if tags and len(tags) > 0:
                    top_tags = tags[:3]  # Show top 3 tags
                    fundamentals += f"\n• 🔖 Tags: {', '.join(top_tags)}"

            # Add market cap category
            if market_cap and market_cap > 0:
                if market_cap > 200e9:
                    cap_category = "Large Cap (Blue Chip)"
                elif market_cap > 10e9:
                    cap_category = "Mid Cap"
                elif market_cap > 1e9:
                    cap_category = "Small Cap"
                else:
                    cap_category = "Micro Cap (High Risk)"

                fundamentals += f"\n• 📈 Cap Category: {cap_category}"

            return fundamentals

        except Exception as e:
            return f"• Fundamental data: Analysis in progress\n• Error: {str(e)[:50]}..."

    def _format_market_conditions(self, market_data):
        """Enhanced market conditions formatting with sentiment analysis"""
        try:
            if market_data.get('success'):
                market_cap_change = market_data.get('market_cap_change_24h', 0)
                btc_dominance = market_data.get('btc_dominance', 0)
                eth_dominance = market_data.get('eth_dominance', 0)
                total_market_cap = market_data.get('total_market_cap', 0)
                total_volume = market_data.get('total_volume_24h', 0)

                # Market sentiment based on market cap change
                if market_cap_change > 3:
                    sentiment = "🚀 Very Bullish"
                elif market_cap_change > 1:
                    sentiment = "📈 Bullish"
                elif market_cap_change > -1:
                    sentiment = "😐 Neutral"
                elif market_cap_change > -3:
                    sentiment = "📉 Bearish"
                else:
                    sentiment = "💥 Very Bearish"

                # Format market cap and volume
                if total_market_cap > 1e12:
                    mc_format = f"${total_market_cap/1e12:.2f}T"
                elif total_market_cap > 1e9:
                    mc_format = f"${total_market_cap/1e9:.2f}B"
                else:
                    mc_format = "N/A"

                if total_volume > 1e9:
                    vol_format = f"${total_volume/1e9:.1f}B"
                elif total_volume > 1e6:
                    vol_format = f"${total_volume/1e6:.1f}M"
                else:
                    vol_format = "N/A"

                return f"{sentiment} | MarketCap: {mc_format} ({self._format_percentage(market_cap_change)}) | Volume: {vol_format} | BTC Dom: {btc_dominance:.1f}% | ETH Dom: {eth_dominance:.1f}%"
            else:
                return "Market data temporarily unavailable - using technical analysis"
        except Exception as e:
            return f"Market analysis in progress - {str(e)[:30]}..."

    def _generate_trading_signal(self, indicators, futures_data, current_price):
        """Generate trading signal with confidence"""
        try:
            confidence_calc = self._calculate_confidence_score(indicators, {}, futures_data)
            confidence = confidence_calc['total']

            # Simple signal logic
            ema_50 = indicators.get('ema_50', 0)
            ema_200 = indicators.get('ema_200', 0)
            rsi = indicators.get('rsi', 50)

            if ema_50 > ema_200 and rsi < 70 and confidence >= 60:
                direction = 'BUY'
            elif ema_50 < ema_200 and rsi > 30 and confidence >= 60:
                direction = 'SELL'
            else:
                direction = 'NEUTRAL'

            return {
                'direction': direction,
                'confidence': confidence,
                'breakdown': confidence_calc['breakdown']
            }

        except Exception as e:
            return {
                'direction': 'NEUTRAL',
                'confidence': 50,
                'breakdown': {},
                'error': str(e)
            }

    def _calculate_trading_levels(self, current_price, direction, atr):
        """Calculate entry, stop loss, and take profit levels"""
        try:
            if direction == 'BUY':
                entry = current_price * 0.999
                stop_loss = current_price - (atr * 2)
                tp1 = current_price + (atr * 1.5)
                tp2 = current_price + (atr * 3)
            elif direction == 'SELL':
                entry = current_price * 1.001
                stop_loss = current_price + (atr * 2)
                tp1 = current_price - (atr * 1.5)
                tp2 = current_price - (atr * 3)
            else:  # NEUTRAL
                return {
                    'entry': current_price,
                    'stop_loss': current_price,
                    'tp1': current_price,
                    'tp2': current_price,
                    'rr_ratio': 0
                }

            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(tp2 - entry)
            rr_ratio = reward / risk if risk > 0 else 0

            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'rr_ratio': rr_ratio
            }

        except Exception as e:
            return {
                'entry': current_price,
                'stop_loss': current_price,
                'tp1': current_price,
                'tp2': current_price,
                'rr_ratio': 0
            }

    async def _scan_symbol_for_signal(self, symbol, crypto_api):
        """Scan individual symbol for trading signal"""
        try:
            if not crypto_api:
                return None

            # Get price and futures data
            price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            futures_data = crypto_api.get_futures_data(symbol)

            if 'error' in price_data or not price_data.get('success'):
                return None

            current_price = self._normalize_data(price_data, ['price', 'current_price'])
            if not current_price:
                return None

            # Get 1h technical analysis
            ohlcv = self.get_coinapi_ohlcv_data(symbol, '1HRS', 50)
            if not ohlcv.get('success'):
                return None

            indicators = self.calculate_technical_indicators(ohlcv['data'])
            if 'error' in indicators:
                return None

            # Generate signal
            signal_data = self._generate_trading_signal(indicators, futures_data, current_price)

            if signal_data['direction'] == 'NEUTRAL' or signal_data['confidence'] < 75:
                return None

            # Calculate trading levels
            atr = indicators.get('atr', current_price * 0.02)
            levels = self._calculate_trading_levels(current_price, signal_data['direction'], atr)

            return {
                'symbol': symbol,
                'direction': signal_data['direction'],
                'confidence': signal_data['confidence'],
                'entry': levels['entry'],
                'sl': levels['stop_loss'],
                'tp': levels['tp2'],
                'rr': f"{levels['rr_ratio']:.1f}:1"
            }

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            return None

    async def _enhanced_scan_symbol_for_signal(self, symbol, crypto_api):
        """Enhanced scan for trading signal with more detailed logic"""
        try:
            if not crypto_api:
                return None

            # Get price and futures data
            price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            futures_data = crypto_api.get_futures_data(symbol)

            if 'error' in price_data or not price_data.get('success'):
                return None

            current_price = self._normalize_data(price_data, ['price', 'current_price'])
            if not current_price:
                return None

            # Get 1h and 4h technical analysis
            timeframes_to_scan = {
                '1h': self.get_coinapi_ohlcv_data(symbol, '1HRS', 100),
                '4h': self.get_coinapi_ohlcv_data(symbol, '4HRS', 100)
            }

            all_indicators = {}
            for tf, ohlcv_data in timeframes_to_scan.items():
                if ohlcv_data and ohlcv_data.get('success'):
                    indicators = self.calculate_technical_indicators(ohlcv_data['data'])
                    if 'error' not in indicators:
                        all_indicators[tf] = indicators

            if not all_indicators.get('1h'):
                return None # Need at least 1h indicators

            indicators = all_indicators['1h'] # Primary indicators from 1h timeframe

            # Generate signal with enhanced logic
            signal_data = self._generate_enhanced_trading_signal(
                indicators, all_indicators.get('4h', {}), futures_data, current_price, {}
            )

            # Ensure confidence is within bounds (75-100%)
            confidence = max(75, min(100, signal_data['confidence']))

            if signal_data['direction'] == 'NEUTRAL' or confidence < 75:
                return None

            # Calculate trading levels
            atr = indicators.get('atr', current_price * 0.02)
            levels = self._calculate_advanced_trading_levels(current_price, signal_data, indicators, {})

            # Determine trend and structure
            ema_50 = indicators.get('ema_50', 0)
            ema_200 = indicators.get('ema_200', 0)
            primary_trend = 'Bullish' if ema_50 > ema_200 else 'Bearish'

            # Determine reason based on technical indicators
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd_histogram', 0)

            if signal_data['direction'] in ['BUY', 'LONG']:
                if rsi < 50 and macd > 0:
                    reason = 'Oversold bounce with momentum'
                elif ema_50 > ema_200 and rsi > 40:
                    reason = 'Trend continuation setup'
                else:
                    reason = 'Technical confluence detected'
            else:
                if rsi > 50 and macd < 0:
                    reason = 'Overbought rejection with momentum'
                elif ema_50 < ema_200 and rsi < 60:
                    reason = 'Trend continuation setup'
                else:
                    reason = 'Technical confluence detected'

            return {
                'symbol': symbol,
                'direction': signal_data['direction'],
                'confidence': confidence,
                'entry': levels['entry'],
                'sl': levels['stop_loss'],
                'tp1': levels['tp1'],
                'tp2': levels['tp2'],
                'rr': f"{levels.get('rr_ratio', 2.0):.1f}:1",
                'primary_trend': primary_trend,
                'structure': signal_data['direction'],
                'reason': reason
            }

        except Exception as e:
            print(f"Error enhanced scanning {symbol}: {e}")
            return None

    def _get_confidence_level(self, confidence):
        """Get confidence level description"""
        if confidence >= 75:
            return "High"
        elif confidence >= 50:
            return "Medium"
        else:
            return "Low"

    def _generate_enhanced_trading_signal(self, primary_indicators, higher_tf_indicators, futures_data, current_price, snd_data):
        """Generate enhanced trading signal with multiple confirmations"""
        try:
            # Base confidence calculation
            confidence_calc = self._calculate_confidence_score(primary_indicators, {}, futures_data)
            base_confidence = confidence_calc['total']

            # Enhanced signal logic
            ema_50 = primary_indicators.get('ema_50', 0)
            ema_200 = primary_indicators.get('ema_200', 0)
            rsi = primary_indicators.get('rsi', 50)
            macd = primary_indicators.get('macd_histogram', 0)

            # Primary trend determination
            primary_trend = 'BULLISH' if ema_50 > ema_200 else 'BEARISH'

            # Higher timeframe confirmation
            htf_confirmation = 'NEUTRAL'
            if higher_tf_indicators:
                htf_ema_50 = higher_tf_indicators.get('ema_50', 0)
                htf_ema_200 = higher_tf_indicators.get('ema_200', 0)
                htf_trend = 'BULLISH' if htf_ema_50 > htf_ema_200 else 'BEARISH'

                if htf_trend == primary_trend:
                    htf_confirmation = 'CONFIRMED'
                    base_confidence += 15
                else:
                    htf_confirmation = 'DIVERGENT'
                    base_confidence -= 10

            # RSI and MACD confirmation
            rsi_signal = 'NEUTRAL'
            if primary_trend == 'BULLISH' and rsi < 70 and macd > 0:
                rsi_signal = 'BULLISH'
                base_confidence += 10
            elif primary_trend == 'BEARISH' and rsi > 30 and macd < 0:
                rsi_signal = 'BEARISH'
                base_confidence += 10

            # Supply & Demand confirmation
            snd_signal = 'NEUTRAL'
            if snd_data.get('success'):
                supply_1 = snd_data.get('Supply 1', current_price * 1.02)
                demand_1 = snd_data.get('Demand 1', current_price * 0.98)

                if current_price <= demand_1 * 1.005 and primary_trend == 'BULLISH':
                    snd_signal = 'BULLISH'
                    base_confidence += 12
                elif current_price >= supply_1 * 0.995 and primary_trend == 'BEARISH':
                    snd_signal = 'BEARISH' 
                    base_confidence += 12

            # Final signal determination
            if (primary_trend == 'BULLISH' and htf_confirmation in ['CONFIRMED', 'NEUTRAL'] and 
                rsi < 70 and base_confidence >= 60):
                direction = 'LONG'
                strategy = 'Trend Following'
            elif (primary_trend == 'BEARISH' and htf_confirmation in ['CONFIRMED', 'NEUTRAL'] and 
                  rsi > 30 and base_confidence >= 60):
                direction = 'SHORT'
                strategy = 'Trend Following'
            elif snd_signal != 'NEUTRAL':
                direction = 'LONG' if snd_signal == 'BULLISH' else 'SHORT'
                strategy = 'Supply/Demand Reversal'
            else:
                direction = 'NEUTRAL'
                strategy = 'Wait for Setup'

            # Time horizon based on confidence and setup
            if base_confidence >= 80:
                time_horizon = '1-4 hours'
            elif base_confidence >= 65:
                time_horizon = '4-12 hours'
            else:
                time_horizon = '12-24 hours'

            # Volume trend analysis
            volume_trend = 'Normal'
            try:
                recent_volumes = primary_indicators.get('recent_volumes', [])
                if recent_volumes and len(recent_volumes) >= 5:
                    avg_volume = sum(recent_volumes[-5:]) / 5
                    current_volume = recent_volumes[-1]
                    if current_volume > avg_volume * 1.5:
                        volume_trend = 'High'
                        base_confidence += 5
                    elif current_volume < avg_volume * 0.7:
                        volume_trend = 'Low'
                        base_confidence -= 3
            except:
                pass

            # Market condition assessment
            volatility = primary_indicators.get('atr', 0) / current_price * 100
            if volatility > 5:
                market_condition = 'High Volatility'
            elif volatility > 2:
                market_condition = 'Normal Volatility'
            else:
                market_condition = 'Low Volatility'

            return {
                'direction': direction,
                'confidence': max(30, min(95, base_confidence)),
                'strategy': strategy,
                'time_horizon': time_horizon,
                'volume_trend': volume_trend,
                'market_condition': market_condition,
                'mtf_confirmation': htf_confirmation,
                'primary_trend': primary_trend,
                'rsi_signal': rsi_signal,
                'snd_signal': snd_signal,
                'breakdown': confidence_calc['breakdown']
            }

        except Exception as e:
            return {
                'direction': 'NEUTRAL',
                'confidence': 50,
                'strategy': 'Wait for Setup',
                'time_horizon': '24+ hours',
                'volume_trend': 'Unknown',
                'market_condition': 'Unknown',
                'mtf_confirmation': 'UNKNOWN',
                'error': str(e)
            }

    def _calculate_advanced_trading_levels(self, current_price, signal_data, indicators, snd_data):
        """Calculate advanced trading levels with multiple TP levels"""
        try:
            direction = signal_data['direction']
            confidence = signal_data['confidence']
            atr = indicators.get('atr', current_price * 0.02)

            # Base calculations
            if direction == 'LONG':
                entry = current_price * 0.998
                entry_min = current_price * 0.995
                entry_max = current_price * 1.001
                stop_loss = current_price - (atr * 2.5)

                # Multiple TP levels
                tp1 = current_price + (atr * 1.5)
                tp2 = current_price + (atr * 2.5)
                tp3 = current_price + (atr * 4.0)

            elif direction == 'SHORT':
                entry = current_price * 1.002
                entry_min = current_price * 0.999
                entry_max = current_price * 1.005
                stop_loss = current_price + (atr * 2.5)

                # Multiple TP levels
                tp1 = current_price - (atr * 1.5)
                tp2 = current_price - (atr * 2.5)
                tp3 = current_price - (atr * 4.0)

            else:  # NEUTRAL
                return {
                    'entry': current_price, 'entry_min': current_price, 'entry_max': current_price,
                    'stop_loss': current_price, 'tp1': current_price, 'tp2': current_price, 'tp3': current_price,
                    'rr_ratio': 0, 'risk_percentage': 0, 'position_size': 0,
                    'entry_method': 'Wait', 'stop_type': 'None'
                }

            # Adjust based on Supply/Demand if available
            if snd_data.get('success'):
                supply_1 = snd_data.get('Supply 1', current_price * 1.02)
                demand_1 = snd_data.get('Demand 1', current_price * 0.98)

                if direction == 'LONG' and demand_1 < current_price:
                    stop_loss = max(stop_loss, demand_1 * 0.995)
                elif direction == 'SHORT' and supply_1 > current_price:
                    stop_loss = min(stop_loss, supply_1 * 1.005)

            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(tp3 - entry)
            rr_ratio = reward / risk if risk > 0 else 2.0

            # Position sizing based on confidence
            if confidence >= 85:
                position_size = 3.0
                risk_percentage = 2.5
            elif confidence >= 75:
                position_size = 2.5
                risk_percentage = 2.0
            elif confidence >= 65:
                position_size = 2.0
                risk_percentage = 1.5
            else:
                position_size = 1.0
                risk_percentage = 1.0

            # Entry method based on quality
            entry_method = 'Market Order' if confidence >= 80 else 'Limit Order at Zone'
            stop_type = 'ATR-Based Stop' if confidence >= 70 else 'Support/Resistance Stop'

            return {
                'entry': entry,
                'entry_min': entry_min,
                'entry_max': entry_max,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'rr_ratio': rr_ratio,
                'risk_percentage': risk_percentage,
                'position_size': position_size,
                'entry_method': entry_method,
                'stop_type': stop_type
            }

        except Exception as e:
            return {
                'entry': current_price, 'entry_min': current_price, 'entry_max': current_price,
                'stop_loss': current_price, 'tp1': current_price, 'tp2': current_price, 'tp3': current_price,
                'rr_ratio': 1.0, 'risk_percentage': 1.0, 'position_size': 1.0,
                'entry_method': 'Manual', 'stop_type': 'Manual', 'error': str(e)
            }

    def _get_zone_position(self, current_price, supply_zone, demand_zone):
        """Determine position relative to S&D zones"""
        if current_price >= supply_zone:
            return "Above Supply - Bearish Pressure"
        elif current_price <= demand_zone:
            return "Below Demand - Bullish Support"
        else:
            return "Between Zones - Range Bound"

    def _get_futures_bias(self, long_ratio, funding_rate):
        """Determine futures market bias"""
        if long_ratio > 70 and funding_rate > 0.01:
            return "Extreme Long Squeeze Risk"
        elif long_ratio < 30 and funding_rate < -0.01:
            return "Extreme Short Squeeze Risk"
        elif long_ratio > 60:
            return "Long Heavy - Contrarian Short"
        elif long_ratio < 40:
            return "Short Heavy - Contrarian Long"
        else:
            return "Balanced Positioning"

    def _get_advanced_trading_insights(self, signal_data, trading_levels, confidence):
        """Generate advanced trading insights"""
        insights = []

        direction = signal_data['direction']
        strategy = signal_data.get('strategy', 'Unknown')

        if confidence >= 85:
            insights.append("• 🔥 Extremely high probability setup - Consider larger position")
            insights.append("• ⚡ Strong confluence of multiple signals")
        elif confidence >= 75:
            insights.append("• 🎯 High probability setup with good risk/reward")
            insights.append("• 📊 Multiple timeframe alignment confirmed")
        elif confidence >= 65:
            insights.append("• 💡 Moderate setup - Standard position sizing")
            insights.append("• ⚠️ Monitor for additional confirmation")
        else:
            insights.append("• 🚫 Low confidence - Consider paper trading first")
            insights.append("• 🔍 Wait for better setup or additional confluence")

        if direction in ['LONG', 'SHORT']:
            insights.append(f"• 🎪 {strategy} approach recommended")
            if trading_levels['rr_ratio'] > 3:
                insights.append("• 💰 Excellent risk/reward ratio - High profit potential")
            elif trading_levels['rr_ratio'] > 2:
                insights.append("• ✅ Good risk/reward - Acceptable trade setup")

        mtf_confirmation = signal_data.get('mtf_confirmation', 'UNKNOWN')
        if mtf_confirmation == 'CONFIRMED':
            insights.append("• 📈 Higher timeframe strongly supports this direction")
        elif mtf_confirmation == 'DIVERGENT':
            insights.append("• ⚠️ Higher timeframe shows divergence - Trade with caution")

        volume_trend = signal_data.get('volume_trend', 'Normal')
        if volume_trend == 'High':
            insights.append("• 🌊 High volume supports the move - Strong momentum")
        elif volume_trend == 'Low':
            insights.append("• 📉 Low volume - Watch for volume confirmation")

        return "\n".join(insights)

    def _error_fallback(self, symbol, error_context):
        """Generate user-friendly error message"""
        return f"""❌ **Terjadi kesalahan mengambil data untuk {symbol}**

💡 **Coba alternatif**:
• `/price {symbol.lower()}` - Cek harga basic
• Tunggu beberapa menit dan coba lagi
• Hubungi admin jika masalah berlanjut

🔄 **Error context**: {error_context}
🕐 **Time**: {self._get_wib_time()}"""

    # ============ LEGACY COMPATIBILITY METHODS ============

    def get_ai_response(self, text, language='id', user_id=None):
        """AI response for general queries"""
        if user_id:
            self.save_user(user_id)

        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal', 'signal']):
            return """📊 **CryptoMentor AI - Professional Analysis**

🎯 **Multi-Timeframe Analysis**:
• `/analyze btc` - Comprehensive analysis dengan SND zones
• `/futures btc 15m` - Futures analysis dengan confidence scoring

🔬 **Technical Features**:
• EMA50/200 trend confirmation
• RSI momentum analysis
• MACD histogram signals
• Supply/Demand zone identification

🌍 **Market Integration**:
• Global market cap monitoring
• BTC dominance analysis
• Professional confidence scoring

Gunakan command di atas untuk analisis profesional!"""

        return f"""🤖 **CryptoMentor AI Professional**

Saya menggunakan:
• 📡 **CoinAPI**: Multi-timeframe OHLCV data
• 🌍 **CoinMarketCap**: Global market metrics
• 🎯 **Advanced Scoring**: Technical + Market confidence
• ⏰ **Multi-TF Confirmation**: 1h, 4h, Daily alignment

Coba `/analyze btc` untuk analisis komprehensif!"""

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get comprehensive market analysis with detailed breakdown"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("MARKET_SENTIMENT")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()
            market_data = self.get_cmc_global_metrics()

            if not market_data.get('success'):
                return self._error_fallback("MARKET", "global data")

            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            eth_dominance = market_data.get('eth_dominance', 0)
            total_market_cap = market_data.get('total_market_cap', 0)
            total_volume = market_data.get('total_volume_24h', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)

            # Determine sentiment with confidence
            confidence = 75
            if market_cap_change > 3:
                sentiment = "🚀 VERY BULLISH"
                confidence = 90
                trend = "Strong Uptrend"
            elif market_cap_change > 1:
                sentiment = "📈 BULLISH"
                confidence = 80
                trend = "Bullish Momentum"
            elif market_cap_change > -1:
                sentiment = "😐 NEUTRAL"
                confidence = 60
                trend = "Sideways Consolidation"
            elif market_cap_change > -3:
                sentiment = "📉 BEARISH"
                confidence = 80
                trend = "Bearish Pressure"
            else:
                sentiment = "💥 VERY BEARISH"
                confidence = 90
                trend = "Strong Downtrend"

            # Get top crypto analysis
            top_cryptos_analysis = self._get_top_cryptos_analysis(crypto_api)

            # Fear & Greed equivalent based on metrics
            fear_greed_score = self._calculate_fear_greed_score(market_cap_change, btc_dominance, total_volume)

            # Market structure analysis
            market_structure = self._analyze_market_structure(btc_dominance, eth_dominance, market_cap_change)

            # Create comprehensive analysis
            analysis = f"""🌍 **COMPREHENSIVE MARKET ANALYSIS**

🕐 **Analysis Time**: {current_time}
📊 **Global Sentiment**: {sentiment}
⭐ **Confidence**: {confidence}%

```
💰 GLOBAL METRICS:
• Total Market Cap: ${total_market_cap/1e12:.2f}T
• 24h Market Change: {self._format_percentage(market_cap_change)}
• Total Volume 24h: ${total_volume/1e9:.1f}B
• Active Cryptocurrencies: {active_cryptos:,}
• BTC Dominance: {btc_dominance:.1f}%
• ETH Dominance: {eth_dominance:.1f}%
```

🔬 **MARKET STRUCTURE ANALYSIS**:
🔄 **Trend**: {trend}
⚡ **Structure**: {market_structure['structure']}
🧠 **Reasoning**: {market_structure['reasoning']}
📊 **Fear & Greed**: {fear_greed_score['level']} ({fear_greed_score['score']}/100)

📈 **TOP CRYPTOCURRENCIES PERFORMANCE**:

{top_cryptos_analysis}

💡 **TRADING IMPLICATIONS**:
{self._get_enhanced_trading_implications(market_cap_change, btc_dominance, eth_dominance, confidence)}

🎯 **MARKET OPPORTUNITIES**:
{self._get_market_opportunities(market_cap_change, btc_dominance)}

⚠️ **RISK ASSESSMENT**:
{self._get_risk_assessment(market_cap_change, confidence)}

🚨 **KEY LEVELS TO WATCH**:
• BTC Dominance Support: {btc_dominance-2:.1f}%
• BTC Dominance Resistance: {btc_dominance+2:.1f}%
• Market Cap Key Level: ${(total_market_cap*0.95)/1e12:.2f}T - ${(total_market_cap*1.05)/1e12:.2f}T

📡 **Data Sources**: CoinMarketCap Global Metrics + Multi-API Analysis
⏰ **Next Update**: Setiap 15 menit untuk data real-time"""

            return analysis

        except Exception as e:
            return self._error_fallback("MARKET", f"comprehensive analysis: {str(e)[:50]}")

    def _get_trading_implications(self, market_cap_change, btc_dominance):
        """Get trading implications from market data"""
        implications = []

        if market_cap_change > 1:
            implications.append("• 🟢 Strong momentum - Consider LONG positions")
        elif market_cap_change < -1:
            implications.append("• 🔴 Bearish pressure - Be cautious with LONG")
        else:
            implications.append("• 🟡 Sideways market - Wait for clear direction")

        if btc_dominance > 45:
            implications.append(f"• 🪙 BTC dominance high - Money flowing to BTC")
        else:
            implications.append(f"• 🏛️ Alt season potential - BTC dominance low")

        return "\n".join(implications)

    def _get_enhanced_trading_implications(self, market_cap_change, btc_dominance, eth_dominance, confidence):
        """Get enhanced trading implications with detailed analysis"""
        implications = []

        # Market momentum analysis
        if market_cap_change > 3:
            implications.append("• 🚀 Extremely bullish conditions - High probability LONG setups")
            implications.append("• 💰 Consider increasing position sizes (within risk limits)")
        elif market_cap_change > 1:
            implications.append("• 📈 Bullish momentum confirmed - Look for LONG opportunities")
            implications.append("• ⚡ Scalping and swing trades favorable")
        elif market_cap_change > -1:
            implications.append("• 😐 Neutral market - Range trading strategies optimal")
            implications.append("• 🎯 Focus on support/resistance levels")
        elif market_cap_change > -3:
            implications.append("• 📉 Bearish pressure building - SHORT bias recommended")
            implications.append("• 🛡️ Reduce LONG exposure, tighten stop losses")
        else:
            implications.append("• 💥 Severe bearish conditions - Avoid LONG positions")
            implications.append("• 🔴 Focus on SHORT opportunities with tight risk management")

        # Dominance analysis
        if btc_dominance > 50:
            implications.append("• 🟠 BTC leading market - Trade major pairs (BTC, ETH)")
            implications.append("• ⚠️ Altcoins may underperform - Be selective")
        elif btc_dominance < 40:
            implications.append("• 🌟 Altcoin season active - Diversify into quality alts")
            implications.append("• 💎 DeFi and Layer-1 tokens may outperform")
        else:
            implications.append("• ⚖️ Balanced market - Both BTC and alts showing strength")

        # ETH dominance insights
        if eth_dominance > 18:
            implications.append("• 🔷 Ethereum ecosystem strong - Consider ETH and ERC-20 tokens")
        elif eth_dominance < 12:
            implications.append("• 🔻 ETH weakness - Monitor for reversal opportunities")

        # Confidence-based recommendations
        if confidence > 85:
            implications.append("• ✅ High confidence signals - Increase position sizing")
        elif confidence < 60:
            implications.append("• ⚠️ Low confidence period - Reduce risk exposure")

        return "\n".join(implications)

    def _get_market_opportunities(self, market_cap_change, btc_dominance):
        """Identify specific market opportunities"""
        opportunities = []

        if market_cap_change > 2:
            opportunities.append("• 🎯 Momentum breakout trades in major cryptos")
            opportunities.append("• 📊 Long positions in DeFi and Layer-1 tokens")
        elif market_cap_change < -2:
            opportunities.append("• 🔻 Short selling opportunities in overbought assets")
            opportunities.append("• 💰 Value accumulation for long-term positions")
        else:
            opportunities.append("• 🏃 Range trading between key support/resistance")
            opportunities.append("• ⚡ Scalping opportunities in high-volume pairs")

        if btc_dominance > 55:
            opportunities.append("• 🟠 Bitcoin maximalist strategy - Focus on BTC/ETH")
        elif btc_dominance < 35:
            opportunities.append("• 🌈 Altcoin diversification strategy optimal")

        opportunities.append("• 🔄 Cross-exchange arbitrage opportunities")
        opportunities.append("• 📈 Futures vs spot price discrepancies")

        return "\n".join(opportunities)

    def _get_risk_assessment(self, market_cap_change, confidence):
        """Provide risk assessment based on market conditions"""
        risks = []

        if abs(market_cap_change) > 3:
            risks.append("• ⚠️ HIGH VOLATILITY - Use smaller position sizes")
            risks.append("• 🛑 Set tight stop losses (2-3% maximum)")
        elif abs(market_cap_change) > 1:
            risks.append("• ⚡ MODERATE VOLATILITY - Standard risk management")
            risks.append("• 🎯 Stop losses at 3-5% from entry")
        else:
            risks.append("• 😴 LOW VOLATILITY - May increase position sizes slightly")
            risks.append("• 📊 Wider stops acceptable (5-7%)")

        if confidence < 70:
            risks.append("• 🔍 Uncertain market conditions - Wait for clarity")
            risks.append("• 💡 Paper trade strategies before live execution")

        risks.append("• 📱 Monitor news and regulatory developments")
        risks.append("• ⏰ Set alerts for key support/resistance breaks")

        return "\n".join(risks)

    def _calculate_fear_greed_score(self, market_cap_change, btc_dominance, volume):
        """Calculate a fear & greed equivalent score"""
        score = 50  # Neutral starting point

        # Market cap change influence (40% weight)
        if market_cap_change > 5:
            score += 25
        elif market_cap_change > 2:
            score += 15
        elif market_cap_change > 0:
            score += 5
        elif market_cap_change > -2:
            score -= 5
        elif market_cap_change > -5:
            score -= 15
        else:
            score -= 25

        # BTC dominance influence (30% weight)
        if btc_dominance > 55:
            score -= 10  # High dominance can indicate fear in alts
        elif btc_dominance < 40:
            score += 15  # Low dominance indicates greed in alts

        # Volume influence (30% weight)
        if volume > 100e9:  # High volume
            score += 10
        elif volume < 50e9:  # Low volume
            score -= 10

        score = max(0, min(100, score))

        if score >= 80:
            level = "🔥 Extreme Greed"
        elif score >= 65:
            level = "😤 Greed"
        elif score >= 45:
            level = "😐 Neutral"
        elif score >= 25:
            level = "😨 Fear"
        else:
            level = "💀 Extreme Fear"

        return {"score": score, "level": level}

    def _analyze_market_structure(self, btc_dominance, eth_dominance, market_cap_change):
        """Analyze overall market structure"""
        if market_cap_change > 2 and btc_dominance < 45:
            structure = "Altcoin Bull Market"
            reasoning = "Strong market growth with declining BTC dominance indicates altcoin season"
        elif market_cap_change > 2 and btc_dominance > 50:
            structure = "Bitcoin-Led Bull Market" 
            reasoning = "Market growth driven primarily by Bitcoin strength"
        elif market_cap_change < -2 and btc_dominance > 50:
            structure = "Flight to BTC Safety"
            reasoning = "Market decline with BTC dominance increase shows risk-off behavior"
        elif market_cap_change < -2:
            structure = "Bear Market Conditions"
            reasoning = "Broad market decline affecting all cryptocurrencies"
        elif btc_dominance > 55:
            structure = "BTC Dominance Phase"
            reasoning = "Bitcoin consolidating market share, alts underperforming"
        elif btc_dominance < 40:
            structure = "Altcoin Rotation Phase" 
            reasoning = "Capital flowing from BTC to alternative cryptocurrencies"
        else:
            structure = "Balanced Market"
            reasoning = "Healthy distribution of capital across crypto ecosystem"

        return {"structure": structure, "reasoning": reasoning}

    def _get_top_cryptos_analysis(self, crypto_api):
        """Get analysis of top cryptocurrencies performance"""
        if not crypto_api:
            return "• Top crypto data temporarily unavailable"

        top_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        analysis_lines = []

        try:
            for i, symbol in enumerate(top_symbols[:5], 1):
                price_data = crypto_api.get_crypto_price(symbol)
                if price_data.get('success'):
                    price = price_data.get('price', 0)
                    change_24h = price_data.get('change_24h', 0)

                    if change_24h > 5:
                        emoji = "🚀"
                        trend = "Strong Bull"
                    elif change_24h > 2:
                        emoji = "📈" 
                        trend = "Bullish"
                    elif change_24h > -2:
                        emoji = "😐"
                        trend = "Neutral"
                    elif change_24h > -5:
                        emoji = "📉"
                        trend = "Bearish"
                    else:
                        emoji = "💥"
                        trend = "Strong Bear"

                    analysis_lines.append(f"{i}. {symbol} {emoji} ${price:,.2f} ({change_24h:+.1f}%) - {trend}")
                else:
                    analysis_lines.append(f"{i}. {symbol} - Data unavailable")

        except Exception as e:
            return f"• Top crypto analysis error: {str(e)[:50]}"

        return "\n".join(analysis_lines) if analysis_lines else "• Top crypto data processing..."

    def get_admin_logs(self, last_n=10):
        """Get recent admin logs for debugging"""
        return self.admin_log[-last_n:] if self.admin_log else []

    def get_system_status(self):
        """Get system status for admin"""
        return {
            'supabase_connected': self.supabase_connected,
            'coinapi_key_available': bool(self.coinapi_key),
            'cmc_key_available': bool(self.cmc_api_key),
            'recent_errors': len(self.admin_log),
            'last_error': self.admin_log[-1] if self.admin_log else None
        }

    # Compatibility aliases for bot.py
    def analyze_text(self, text):
        """Simple text analysis"""
        return self.get_ai_response(text)

    async def analyze_futures_enhanced(self, symbol, user_id=None):
        """Enhanced futures analysis wrapper"""
        return await self.get_futures_analysis(symbol, '15m')

    async def generate_futures_signals_enhanced(self, language='id', crypto_api=None, query_args=None):
        """Enhanced futures signals wrapper"""
        return await self.generate_futures_signals(language, crypto_api, query_args)