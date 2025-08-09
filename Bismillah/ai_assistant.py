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
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = <REDACTED_SUPABASE_KEY>

            if not supabase_url or not supabase_anon_key:
                self._log_admin_error("SUPABASE_INIT", "Missing SUPABASE_URL or SUPABASE_ANON_KEY")
                return None

            supabase: Client = create_client(supabase_url, supabase_anon_key)
            return supabase
        except Exception as e:
            self._log_admin_error("SUPABASE_INIT", f"Initialization failed: {e}")
            return None

    def _validate_supabase_connection(self):
        """Validate Supabase connection"""
        try:
            if not self.supabase:
                return False
            
            # Test connection with a simple query
            test_result = self.supabase.table('users').select('count', count='exact').limit(1).execute()
            if test_result:
                return True
            return False
        except Exception as e:
            self._log_admin_error("SUPABASE_CONNECTION", f"Connection test failed: {e}")
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
        if not self.supabase_connected:
            self._log_admin_error(command_name, "Database required but not connected")
            return False, self._get_database_error_message()
        return True, None

    def _get_database_error_message(self):
        """Get user-friendly database error message"""
        return """❌ Gagal terhubung ke database\\.

💡 Periksa koneksi Supabase atau hubungi admin\\."""

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
        """Comprehensive analysis following system prompt template"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("ANALYZE")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()
            symbol = symbol.upper()

            # Get current price data
            if crypto_api:
                price_info = crypto_api.get_crypto_price(symbol, force_refresh=True)
            else:
                price_info = {'error': 'API unavailable'}

            if 'error' in price_info or not price_info.get('success'):
                return self._error_fallback(symbol, "price data")

            current_price = self._normalize_data(price_info, ['price', 'current_price', 'last', 'close'])
            change_24h = self._normalize_data(price_info, ['change_24h', 'price_change_24h', 'percent_change_24h'])

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

            # Determine overall trend
            trend_analysis = self._analyze_trend(timeframes_data, current_price)

            # Supply & Demand zones
            snd_zones = self._get_supply_demand_zones(symbol, current_price, crypto_api)

            # Market conditions
            market_data = self.get_cmc_global_metrics()

            # Format comprehensive analysis with safe markdown
            rsi_value = main_indicators.get('rsi', 'N/A')
            rsi_display = f"{rsi_value:.1f}" if isinstance(rsi_value, (int, float)) else 'N/A'
            
            macd_value = main_indicators.get('macd_histogram', 'N/A')
            macd_display = f"{macd_value:.4f}" if isinstance(macd_value, (int, float)) else 'N/A'

            analysis = f"""📊 **COMPREHENSIVE ANALYSIS \\- {self._escape_markdown_v2(symbol)}**

💰 **Current Price**: {self._safe_format_price(current_price)}
📉 **24h Change**: {self._safe_format_percentage(change_24h)}

```
🔬 Technical Summary:
• EMA50: {self._format_price(main_indicators.get('ema_50'))}
• EMA200: {self._format_price(main_indicators.get('ema_200'))}
• RSI: {rsi_display}
• MACD: {macd_display}
• ATR: {self._format_price(main_indicators.get('atr'))}
```

📈 **Trend Analysis**:
• **Overall Trend**: {trend_analysis['trend_emoji']} {self._escape_markdown_v2(trend_analysis['trend'])}
• **Reasoning**: {self._escape_markdown_v2(trend_analysis['reasoning'])}

```
🎯 SUPPLY & DEMAND ZONES:
• Supply Zone 1 (R): {self._format_price(snd_zones.get('supply_1'))}
• Demand Zone 1 (S): {self._format_price(snd_zones.get('demand_1'))}
• Position: {snd_zones.get('position', 'Analysis pending')}
```

🌍 **Market Conditions**: {self._escape_markdown_v2(self._format_market_conditions(market_data))}

⚠️ **Disclaimer**: Analisis teknikal untuk edukasi\\. Gunakan manajemen risiko yang tepat\\.

🕐 **Analysis Time**: {self._escape_markdown_v2(current_time)}
📡 **Data Sources**: CoinAPI \\+ CMC \\+ Binance SnD"""

            # Validate and return safe output
            safe_text, parse_mode = self._safe_output(analysis)
            return safe_text

        except Exception as e:
            return self._error_fallback(symbol, f"comprehensive analysis: {str(e)[:50]}")

    async def get_futures_analysis(self, symbol, timeframe='15m', language='id', crypto_api=None):
        """Futures analysis following system prompt template"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("FUTURES")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()
            symbol = symbol.upper()

            # Get current price
            if crypto_api:
                price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
                futures_data = crypto_api.get_futures_data(symbol)
            else:
                return self._error_fallback(symbol, "API connection")

            if 'error' in price_data or not price_data.get('success'):
                return self._error_fallback(symbol, "price data")

            current_price = self._normalize_data(price_data, ['price', 'current_price'])
            change_24h = self._normalize_data(price_data, ['change_24h', 'price_change_24h', 'percent_change_24h'])

            # Technical analysis for specific timeframe
            timeframe_mapping = {
                '15m': '15MIN', '30m': '30MIN', '1h': '1HRS',
                '4h': '4HRS', '1d': '1DAY', '1w': '1WEK'
            }
            api_timeframe = timeframe_mapping.get(timeframe, '1HRS')

            ohlcv = self.get_coinapi_ohlcv_data(symbol, api_timeframe, 100)
            if not ohlcv.get('success'):
                return self._error_fallback(symbol, f"OHLCV data for {timeframe}")

            indicators = self.calculate_technical_indicators(ohlcv['data'])
            if 'error' in indicators:
                return self._error_fallback(symbol, "technical indicators")

            # Generate signal and confidence
            signal_data = self._generate_trading_signal(indicators, futures_data, current_price)

            # Calculate trading levels
            trading_levels = self._calculate_trading_levels(
                current_price,
                signal_data['direction'],
                indicators.get('atr', current_price * 0.02)
            )

            # Format futures analysis with safe markdown
            direction_emoji = "🟢" if signal_data['direction'] in ['BUY', 'LONG'] else "🔴" if signal_data['direction'] in ['SELL', 'SHORT'] else "🟡"
            
            rsi_value = indicators.get('rsi', 'N/A')
            rsi_display = f"{rsi_value:.1f}" if isinstance(rsi_value, (int, float)) else 'N/A'

            analysis = f"""🔍 **FUTURES ANALYSIS \\- {self._escape_markdown_v2(symbol)} \\({self._escape_markdown_v2(timeframe)}\\)**

💰 **Current Price**: {self._safe_format_price(current_price)}
📉 **24h Change**: {self._safe_format_percentage(change_24h)}

{direction_emoji} **SIGNAL**: {self._escape_markdown_v2(signal_data['direction'])}
⭐ **Confidence**: {signal_data['confidence']}% \\({self._escape_markdown_v2(self._get_confidence_level(signal_data['confidence']))}\\)

```
💰 TRADING SETUP:
• Entry: {self._format_price(trading_levels['entry'])}
• Stop Loss: {self._format_price(trading_levels['stop_loss'])}
• TP1: {self._format_price(trading_levels['tp1'])} | TP2: {self._format_price(trading_levels['tp2'])}
• RR: {trading_levels['rr_ratio']:.1f}:1
```

```
📊 TECHNICAL ({timeframe}):
• EMA50: {self._format_price(indicators.get('ema_50'))}
• EMA200: {self._format_price(indicators.get('ema_200'))}
• RSI: {rsi_display}
• ATR: {self._format_price(indicators.get('atr'))}
```

🔮 **FUTURES METRICS**:"""

            # Add futures metrics if available
            if futures_data and futures_data.get('success'):
                long_ratio = self._normalize_data(futures_data, ['long_ratio', 'longPercentage', 'longs_pct'])
                funding_rate = self._normalize_data(futures_data, ['funding_rate', 'funding', 'fundingRate'])
                open_interest = self._normalize_data(futures_data, ['open_interest', 'oi', 'openInterest'])

                analysis += f"""
• **Long/Short Ratio**: {long_ratio:.1f}% Long" if long_ratio else "N/A"
• **Funding Rate**: {self._format_percentage(funding_rate, 4) if funding_rate else "N/A"}
• **Open Interest**: {self._format_price(open_interest) if open_interest else "N/A"}"""
            else:
                analysis += "\n• Futures metrics temporarily unavailable"

            analysis += f"""

⚠️ **Risk Management**:
• Position size: 1\\-3% of capital maximum
• Always use stop loss before entry
• Monitor market conditions

🕐 **Analysis Time**: {self._escape_markdown_v2(current_time)}
📡 **Data Sources**: CoinAPI \\+ Binance Futures"""

            # Validate and return safe output
            safe_text, parse_mode = self._safe_output(analysis)
            return safe_text

        except Exception as e:
            return self._error_fallback(symbol, f"futures analysis: {str(e)[:50]}")

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
                    if signal and signal.get('confidence', 0) >= 70:  # Lower threshold for better detection
                        high_confidence_signals.append(signal)
                        print(f"✅ Found signal: {symbol} - {signal['confidence']}% ({signal['direction']})")
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
                    continue

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
            message = f"""🚨 **FUTURES SIGNALS SCAN**

🕐 **Scan Time**: {self._escape_markdown_v2(current_time)}
🌍 **Market Conditions**: {self._escape_markdown_v2(market_conditions)}

📈 **HIGH\\-CONFIDENCE SIGNALS** \\({len(high_confidence_signals)} found\\):

"""

            for i, signal in enumerate(high_confidence_signals[:8], 1):  # Limit to top 8 signals
                direction_emoji = "🟢" if signal['direction'] in ['LONG', 'BUY'] else "🔴"
                confidence_level = "🔥" if signal['confidence'] >= 80 else "⚡"

                message += f"""```
{i}. {signal['symbol']} {direction_emoji} {signal['direction']} {confidence_level}
Entry: {self._format_price(signal['entry'])}
TP1: {self._format_price(signal['tp1'])} | TP2: {self._format_price(signal['tp2'])}
SL: {self._format_price(signal['sl'])}
Confidence: {signal['confidence']}% | RR: {signal.get('rr', 'N/A')}
```

"""

            message += f"""⚠️ **TRADING RULES**:
• Maksimal 2% risk per position
• Entry dengan konfirmasi price action
• Gunakan stop loss sebelum entry
• Take profit bertahap \\(50% di TP1, 50% di TP2\\)

🕐 **Analysis Time**: {self._escape_markdown_v2(current_time)}
📡 **Data Sources**: CoinAPI Real\\-time \\+ Binance Futures"""

            # Validate and return safe output
            safe_text, parse_mode = self._safe_output(message)
            return safe_text

        except Exception as e:
            return self._error_fallback("FUTURES_SIGNALS", f"scan process: {str(e)[:50]}")

    # ============ HELPER METHODS ============

    def _analyze_trend(self, timeframes_data, current_price):
        """Analyze trend across multiple timeframes"""
        try:
            trends = []
            for tf, data in timeframes_data.items():
                ema_50 = data.get('ema_50')
                ema_200 = data.get('ema_200')
                if ema_50 and ema_200:
                    if ema_50 > ema_200:
                        trends.append('BULLISH')
                    else:
                        trends.append('BEARISH')

            # Determine overall trend
            if not trends:
                return {
                    'trend': 'SIDEWAYS',
                    'trend_emoji': '🟡',
                    'reasoning': 'Insufficient data untuk trend analysis'
                }

            bullish_count = trends.count('BULLISH')
            bearish_count = trends.count('BEARISH')

            if bullish_count > bearish_count:
                return {
                    'trend': 'BULLISH',
                    'trend_emoji': '🟢',
                    'reasoning': f'EMA50 > EMA200 di {bullish_count}/{len(trends)} timeframes'
                }
            elif bearish_count > bullish_count:
                return {
                    'trend': 'BEARISH',
                    'trend_emoji': '🔴',
                    'reasoning': f'EMA50 < EMA200 di {bearish_count}/{len(trends)} timeframes'
                }
            else:
                return {
                    'trend': 'SIDEWAYS',
                    'trend_emoji': '🟡',
                    'reasoning': 'Mixed signals antar timeframes'
                }

        except Exception as e:
            return {
                'trend': 'SIDEWAYS',
                'trend_emoji': '🟡',
                'reasoning': 'Error dalam trend analysis'
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

    def _format_market_conditions(self, market_data):
        """Format market conditions string"""
        if market_data.get('success'):
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            return f"MarketCap {self._format_percentage(market_cap_change)} | BTC Dom: {btc_dominance:.1f}%"
        else:
            return "Market data unavailable"

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
            signal_data = self._generate_trading_signal(indicators, futures_data, current_price)

            # Check for stronger confirmation from 4h timeframe if available
            if all_indicators.get('4h'):
                ema_50_4h = all_indicators['4h'].get('ema_50')
                ema_200_4h = all_indicators['4h'].get('ema_200')
                if ema_50_4h and ema_200_4h:
                    if signal_data['direction'] in ['BUY', 'LONG'] and ema_50_4h < ema_200_4h:
                        signal_data['confidence'] = max(0, signal_data['confidence'] - 20) # Reduce confidence if 4h trend is opposite
                    elif signal_data['direction'] in ['SELL', 'SHORT'] and ema_50_4h > ema_200_4h:
                        signal_data['confidence'] = max(0, signal_data['confidence'] - 20)

            if signal_data['direction'] == 'NEUTRAL' or signal_data['confidence'] < 70: # Lowered threshold for more signals
                return None

            # Calculate trading levels
            atr = indicators.get('atr', current_price * 0.02)
            levels = self._calculate_trading_levels(current_price, signal_data['direction'], atr)

            # Adjust TP based on confidence and RR
            tp_multiplier = 1.0
            if signal_data['confidence'] >= 85:
                tp_multiplier = 1.3
            elif signal_data['confidence'] >= 75:
                tp_multiplier = 1.1

            rr_ratio = levels.get('rr_ratio', 0)
            if rr_ratio < 1.5: # Ensure a minimum RR
                rr_ratio = 1.5

            tp1 = levels['entry'] + (levels['entry'] - levels['stop_loss']) * 0.6 * tp_multiplier if signal_data['direction'] in ['BUY', 'LONG'] else levels['entry'] - (levels['stop_loss'] - levels['entry']) * 0.6 * tp_multiplier
            tp2 = levels['entry'] + (levels['entry'] - levels['stop_loss']) * 1.2 * tp_multiplier if signal_data['direction'] in ['BUY', 'LONG'] else levels['entry'] - (levels['stop_loss'] - levels['entry']) * 1.2 * tp_multiplier


            return {
                'symbol': symbol,
                'direction': signal_data['direction'],
                'confidence': signal_data['confidence'],
                'entry': levels['entry'],
                'sl': levels['stop_loss'],
                'tp1': tp1,
                'tp2': tp2,
                'rr': f"{rr_ratio:.1f}:1"
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
        """Get market sentiment analysis"""
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
            total_market_cap = market_data.get('total_market_cap', 0)

            # Determine sentiment
            if market_cap_change > 3:
                sentiment = "🚀 VERY BULLISH"
            elif market_cap_change > 1:
                sentiment = "📈 BULLISH"
            elif market_cap_change > -1:
                sentiment = "😐 NEUTRAL"
            elif market_cap_change > -3:
                sentiment = "📉 BEARISH"
            else:
                sentiment = "💥 VERY BEARISH"

            sentiment_analysis = f"""🌍 **MARKET SENTIMENT ANALYSIS**

📊 **Global Sentiment**: {self._escape_markdown_v2(sentiment)}

```
💰 Key Metrics:
• Total Market Cap: ${total_market_cap/1e12:.2f}T
• 24h Change: {self._format_percentage(market_cap_change)}
• BTC Dominance: {btc_dominance:.1f}%
```

📈 **Trading Implications**:
{self._escape_markdown_v2(self._get_trading_implications(market_cap_change, btc_dominance))}

🕐 **Update**: {self._escape_markdown_v2(current_time)}
📡 **Source**: CoinMarketCap Global Metrics"""

            # Validate and return safe output
            safe_text, parse_mode = self._safe_output(sentiment_analysis)
            return safe_text

        except Exception as e:
            return self._error_fallback("MARKET", f"sentiment analysis: {str(e)[:50]}")

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