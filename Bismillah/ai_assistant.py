# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
# TODO: Add database client import after setup
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

__all__ = ["CryptoMentorAI"]

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

        # TODO: Initialize database connection after setup
        self.supabase = None
        self.supabase_connected = False

        # Admin logging system - ensure this is always initialized
        self.admin_log = []

        # Connection monitoring
        self.connection_status = {
            'last_check': datetime.now(),
            'consecutive_failures': 0,
            'total_reconnections': 0
        }

        # Enhanced configuration
        self.auto_signal_enabled = True
        self.auto_signal_task = None
        self.signal_cooldown = 3600  # 1 hour cooldown
        self.scan_interval = 5 * 60  # 5 minutes scan interval
        self.min_confidence_threshold = 75  # Minimum 75% confidence

        # Target symbols for futures analysis


        self.target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

    def check_connection_health(self):
        """Periodic health check for Supabase connection"""
        try:
            current_time = datetime.now()

            # Check if we need to perform health check (every 5 minutes)
            if (current_time - self.connection_status['last_check']).total_seconds() < 300:
                return self.supabase_connected

            print("🏥 Performing Supabase connection health check...")

            if self._test_supabase_connection():
                self.connection_status['consecutive_failures'] = 0
                self.supabase_connected = True
                print("✅ Connection health check passed")
            else:
                self.connection_status['consecutive_failures'] += 1
                print(f"❌ Connection health check failed (failures: {self.connection_status['consecutive_failures']})")

                # Auto-reconnect after 2 consecutive failures
                if self.connection_status['consecutive_failures'] >= 2:
                    print("🔄 Triggering auto-reconnection due to health check failures")
                    if self._reconnect_supabase():
                        self.connection_status['total_reconnections'] += 1
                        self.supabase_connected = True
                    else:
                        self.supabase_connected = False

            self.connection_status['last_check'] = current_time
            return self.supabase_connected

        except Exception as e:
            print(f"❌ Health check error: {e}")
            self.supabase_connected = False
            return False

    def get_connection_stats(self):
        """Get connection statistics for monitoring"""
        return {
            'connected': self.supabase_connected,
            'last_user_count': AIAssistant._last_user_count,
            'consecutive_failures': self.connection_status['consecutive_failures'],
            'total_reconnections': self.connection_status['total_reconnections'],
            'last_check': self.connection_status['last_check'].isoformat(),
            'retry_count': AIAssistant._connection_retry_count
        }


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

    _supabase_instance = None
    _last_user_count = None
    _connection_retry_count = 0
    _max_retries = 3

    def _init_supabase(self):
        """TODO: Initialize database client after setup"""
        return None

    def _test_supabase_connection(self):
        """TODO: Implement database connection test"""
        return False

    def _reconnect_supabase(self):
        """TODO: Implement database reconnection"""
        return False

    def _validate_data_integrity(self):
        """TODO: Implement data integrity validation"""
        return False

    def _ensure_supabase_connection(self):
        """TODO: Implement connection verification"""
        return False

    def _validate_supabase_connection(self):
        """TODO: Implement connection validation"""
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
        # Perform periodic health check
        self.check_connection_health()

        # Most commands don't actually require database for core functionality
        # Only user-specific features like premium status, credits need database
        if command_name in ['ANALYZE', 'FUTURES', 'FUTURES_SIGNALS', 'MARKET_SENTIMENT']:
            # These commands work fine without database
            return True, None

        if not self.supabase_connected:
            print(f"⚠️ Database not available for {command_name} - continuing with limited functionality")
            # Try one more reconnection attempt for critical operations
            if command_name in ['USER_MANAGEMENT', 'PREMIUM_CHECK']:
                self._reconnect_supabase()
            return True, None  # Don't block execution
        return True, None

    def _get_database_error_message(self):
        """Get user-friendly database error message"""
        return """⚠️ Database tidak tersedia saat ini. 

✅ Analisis tetap berfungsi normal!
💡 Fitur premium dan riwayat mungkin terbatas."""

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
            elif price < 1000:
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

    def _supabase_query(self, query_func, operation_name="query"):
        """TODO: Implement database query method"""
        return None

    def save_user(self, user_id, username=""):
        """TODO: Implement user save method"""
        return False

    def get_user_count(self):
        """TODO: Implement user count method"""
        return 0

    def get_premium_users_count(self):
        """TODO: Implement premium user count method"""
        return 0

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
💰 **Current Price**: ${current_price:,.2f}
📊 **24h Change**: {change_24h:+.2f}%

{direction_emoji} **TRADING SIGNAL**: {signal_data['direction']}
{confidence_emoji} **Confidence**: {confidence:.1f}% ({confidence_desc})
🎯 **Strategy**: {signal_data.get('strategy', 'Technical Analysis')}
⚡ **Time Horizon**: {signal_data.get('time_horizon', '4-24 hours')}

💰 **DETAILED TRADING SETUP:**
• Entry: ${trading_levels['entry']:,.6f}
• Stop Loss: ${trading_levels['stop_loss']:,.6f}
• TP1 (50%): ${trading_levels['tp1']:,.6f}
• TP2 (30%): ${trading_levels['tp2']:,.6f} 
• TP3 (20%): ${trading_levels['tp3']:,.6f}
• Risk/Reward: {trading_levels['rr_ratio']:.1f}:1
• Max Risk: {trading_levels['risk_percentage']:.1f}% per position

"""

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
        """Enhanced futures analysis with comprehensive breakdown - Fixed async function"""
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

💰 **DETAILED TRADING SETUP:**
• Entry: ${trading_levels['entry']:.2f}
• Stop Loss: ${trading_levels['stop_loss']:.2f}
• TP1 (50%): ${trading_levels['tp1']:.2f}
• TP2 (30%): ${trading_levels['tp2']:.2f} 
• TP3 (20%): ${trading_levels['tp3']:.2f}
• Risk/Reward: {trading_levels.get('rr_ratio', 2.0):.1f}:1
• Max Risk: {trading_levels['risk_percentage']:.1f}% per position

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

    def _generate_enhanced_trading_signal(self, primary_indicators, higher_tf_indicators, futures_data, current_price, snd_data):
        """Generate enhanced trading signal with multiple timeframe confirmation - Helper function"""
        try:
            # Base signal logic with enhanced features
            confidence = 0
            direction = 'NEUTRAL'
            
            # Primary timeframe indicators
            ema_50 = primary_indicators.get('ema_50', 0)
            ema_200 = primary_indicators.get('ema_200', 0)
            rsi = primary_indicators.get('rsi', 50)
            macd = primary_indicators.get('macd_histogram', 0)
            
            # Trend determination
            if ema_50 > ema_200:
                confidence += 30
                if rsi < 70:
                    confidence += 15
                if macd > 0:
                    confidence += 15
                direction = 'LONG'
            elif ema_50 < ema_200:
                confidence += 30
                if rsi > 30:
                    confidence += 15
                if macd < 0:
                    confidence += 15
                direction = 'SHORT'
            else:
                confidence += 10
                
            # Higher timeframe confirmation
            if higher_tf_indicators:
                htf_ema_50 = higher_tf_indicators.get('ema_50', 0)
                htf_ema_200 = higher_tf_indicators.get('ema_200', 0)
                if htf_ema_50 > htf_ema_200 and direction == 'LONG':
                    confidence += 20
                elif htf_ema_50 < htf_ema_200 and direction == 'SHORT':
                    confidence += 20
                    
            # Futures data confirmation
            if futures_data and futures_data.get('success'):
                funding_rate = futures_data.get('funding_rate', 0)
                if abs(funding_rate) < 0.01:  # Normal funding
                    confidence += 10
                    
            return {
                'direction': direction,
                'confidence': min(confidence, 100),
                'strategy': 'Multi-Timeframe Analysis',
                'time_horizon': '4-24 hours',
                'mtf_confirmation': 'Strong' if confidence > 80 else 'Partial',
                'volume_trend': 'Normal'
            }
            
        except Exception as e:
            return {
                'direction': 'NEUTRAL',
                'confidence': 50,
                'strategy': 'Basic Analysis',
                'time_horizon': '4-24 hours',
                'error': str(e)
            }

    def _calculate_advanced_trading_levels(self, current_price, signal_data, indicators, snd_data):
        """Calculate advanced trading levels with proper risk management - Helper function"""
        try:
            atr = indicators.get('atr', current_price * 0.02)
            direction = signal_data['direction']
            
            if direction == 'LONG':
                entry = current_price * 0.999
                stop_loss = current_price - (atr * 2.5)
                tp1 = current_price + (atr * 1.5)
                tp2 = current_price + (atr * 3)
                tp3 = current_price + (atr * 4.5)
            elif direction == 'SHORT':
                entry = current_price * 1.001
                stop_loss = current_price + (atr * 2.5)
                tp1 = current_price - (atr * 1.5)
                tp2 = current_price - (atr * 3)
                tp3 = current_price - (atr * 4.5)
            else:
                return {
                    'entry': current_price,
                    'stop_loss': current_price,
                    'tp1': current_price,
                    'tp2': current_price,
                    'tp3': current_price,
                    'rr_ratio': 0,
                    'risk_percentage': 2.5
                }
                
            # Calculate risk/reward ratio
            risk = abs(entry - stop_loss)
            reward = abs(tp2 - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'rr_ratio': rr_ratio,
                'risk_percentage': 2.5
            }
            
        except Exception as e:
            return {
                'entry': current_price,
                'stop_loss': current_price,
                'tp1': current_price,
                'tp2': current_price,
                'tp3': current_price,
                'rr_ratio': 0,
                'risk_percentage': 2.5
            }

    def _get_futures_bias(self, long_ratio, funding_rate):
        """Get futures bias based on long/short ratio and funding rate - Helper function"""
        try:
            if long_ratio > 60 and funding_rate > 0.01:
                return "Bullish Overheated"
            elif long_ratio > 55:
                return "Bullish"
            elif long_ratio < 40 and funding_rate < -0.01:
                return "Bearish Oversold"
            elif long_ratio < 45:
                return "Bearish"
            else:
                return "Neutral"
        except:
            return "Neutral"

    def _get_zone_position(self, current_price, supply_zone, demand_zone):
        """Determine current position relative to supply/demand zones - Helper function"""
        try:
            if current_price > supply_zone:
                return "Above Supply Zone"
            elif current_price < demand_zone:
                return "Below Demand Zone"
            else:
                return "Between Zones"
        except:
            return "Unknown Position"

    def _get_advanced_trading_insights(self, signal_data, trading_levels, confidence):
        """Generate advanced trading insights - Helper function"""
        try:
            insights = []
            
            if confidence >= 80:
                insights.append("• High probability setup dengan multiple confirmations")
            elif confidence >= 70:
                insights.append("• Setup trading solid dengan konfirmasi cukup")
            else:
                insights.append("• Setup berisiko, gunakan position size kecil")
                
            rr_ratio = trading_levels.get('rr_ratio', 0)
            if rr_ratio > 2:
                insights.append("• Risk/Reward ratio menguntungkan untuk swing trading")
            elif rr_ratio > 1:
                insights.append("• Risk/Reward ratio acceptable untuk day trading")
            else:
                insights.append("• Risk/Reward ratio kurang ideal, pertimbangkan skip")
                
            direction = signal_data.get('direction', 'NEUTRAL')
            if direction != 'NEUTRAL':
                insights.append(f"• Bias market mendukung posisi {direction}")
            else:
                insights.append("• Market dalam kondisi sideways, tunggu breakout")
                
            return "\n".join(insights)
            
        except Exception as e:
            return "• Analisis insight temporarily unavailable"

    def _filter_and_format_signals(self, all_signals):
        """Filter and format signals for display - Helper function"""
        try:
            # Filter signals with confidence >= 75%
            filtered = [s for s in all_signals if s.get('confidence', 0) >= 75]
            
            # Sort by confidence (highest first)
            filtered.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Take top 10 signals to avoid spam
            return filtered[:10]
            
        except Exception as e:
            return []

    def _error_fallback(self, symbol, error_context):
        """Generate error fallback message - Helper function"""
        return f"❌ Error in {error_context} for {symbol}\n\n💡 Alternatif:\n• `/price {symbol.lower()}` untuk harga basic\n• Contact admin jika masalah berlanjut"

    async def generate_futures_signals(self, language='id', crypto_api=None, query_args=None):
        """Generate futures signals with proper formatting and filtering"""
        try:
            # Check database connection for user-related operations
            db_available, db_error = self._check_database_required("FUTURES_SIGNALS")
            if not db_available:
                return db_error

            current_time = self._get_wib_time()

            # Target symbols for scanning - expanded list for variety
            all_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK', 
                          'BNB', 'TRX', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT', 'ATOM', 'FIL', 'ETC',
                          'ALGO', 'VET', 'MANA', 'SAND', 'SHIB']

            # If specific symbol requested, use that
            if query_args and len(query_args) > 0:
                first_arg = query_args[0].upper()
                if len(first_arg) <= 5:
                    target_symbols = [first_arg]
                else:
                    # Randomize symbol selection for variety each time
                    import random
                    target_symbols = random.sample(all_symbols, min(15, len(all_symbols)))
            else:
                # Randomize symbol selection for variety each time
                import random
                target_symbols = random.sample(all_symbols, min(15, len(all_symbols)))

            all_signals = []

            # Scan symbols for signals
            for symbol in target_symbols:
                try:
                    signal = await self._enhanced_scan_symbol_for_signal(symbol, crypto_api)
                    if signal:
                        all_signals.append(signal)
                        print(f"✅ Found signal: {symbol} - {signal['confidence']:.2f}% ({signal['direction']})")
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
                    continue

            # Apply filtering and formatting rules
            filtered_signals = self._filter_and_format_signals(all_signals)

            # Format response
            if not filtered_signals:
                return f"""🚨 FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS

🕐 Scan Time: {current_time}
📊 Signals Found: 0 (Confidence ≥ 75.00%)

❌ Tidak ada sinyal memenuhi syarat

📊 Symbols Scanned: {', '.join(target_symbols)}
⚠️ Status: Tidak ada setup trading yang jelas saat ini

💡 Kemungkinan Penyebab:
• Market dalam kondisi consolidation
• Volatilitas rendah saat ini
• Menunggu momentum yang lebih jelas

🔄 Alternatif:
• Coba /futures btc untuk analisis spesifik
• Gunakan /analyze eth untuk analisis fundamental
• Monitor kondisi market dengan /market

📡 Next scan akan mengacak koin berbeda"""

            # Get global market metrics for header
            global_metrics = self.get_cmc_global_metrics()

            # Format header with global metrics
            if global_metrics.get('success'):
                total_market_cap = global_metrics.get('total_market_cap', 0)
                market_cap_change = global_metrics.get('market_cap_change_24h', 0)
                total_volume = global_metrics.get('total_volume_24h', 0)
                active_cryptos = global_metrics.get('active_cryptocurrencies', 0)
                btc_dominance = global_metrics.get('btc_dominance', 0)
                eth_dominance = global_metrics.get('eth_dominance', 0)

                header_metrics = f"""💰 **GLOBAL METRICS:**
• Total Market Cap: ${total_market_cap/1e12:.2f}T
• 24h Market Change: {market_cap_change:+.2f}%
• Total Volume 24h: ${total_volume/1e9:.1f}B
• Active Cryptocurrencies: {active_cryptos:,}
• BTC Dominance: {btc_dominance:.1f}%
• ETH Dominance: {eth_dominance:.1f}%

"""
            else:
                header_metrics = ""

            # Format signals message
            message = f"""🚨 **FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS**

🕐 **Scan Time**: {current_time}
📊 **Signals Found**: {len(filtered_signals)} (Confidence ≥ 75.00%)

{header_metrics}"""

            for i, signal in enumerate(filtered_signals, 1):
                direction_emoji = "🟢" if signal['direction'] in ['LONG', 'BUY'] else "🔴"

                # Get 24h change data
                symbol = signal['symbol']
                price_data = crypto_api.get_crypto_price(symbol) if crypto_api else {}
                change_24h = price_data.get('change_24h', 0) if price_data.get('success') else 0

                message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
⭐️ Confidence: {signal['confidence']:.2f}%
💰 Entry: ${signal['entry']:.2f}
🛑 Stop Loss: ${signal['sl']:.2f}
🎯 TP1: ${signal['tp1']:.2f}
🎯 TP2: ${signal['tp2']:.2f}
📊 R/R Ratio: {signal['rr_ratio']}
🔄 Trend: {signal['trend']}
⚡️ Structure: {signal['structure']} Bias
🧠 Reason: {signal['reason']}
📈 24h Change: {change_24h:+.2f}%

"""

            message += """⚠️ TRADING DISCLAIMER:
• Signals berbasis Supply & Demand analysis
• Gunakan proper risk management
• Position sizing sesuai risk level
• DYOR sebelum trading

📡 Next scan akan mengacak koin berbeda
🔄 Jalankan ulang untuk variasi sinyal"""

            return message

        except Exception as e:
            return self._error_fallback("FUTURES_SIGNALS", f"scan process: {str(e)[:50]}")

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get comprehensive market sentiment analysis - Non-async function"""
        try:
            current_time = self._get_wib_time()
            
            # Get global market metrics
            global_metrics = self.get_cmc_global_metrics()
            
            if not global_metrics.get('success'):
                return self._get_basic_market_fallback()
                
            # Extract key metrics
            total_market_cap = global_metrics.get('total_market_cap', 0)
            market_cap_change = global_metrics.get('market_cap_change_24h', 0)
            total_volume = global_metrics.get('total_volume_24h', 0)
            active_cryptos = global_metrics.get('active_cryptocurrencies', 0)
            btc_dominance = global_metrics.get('btc_dominance', 0)
            eth_dominance = global_metrics.get('eth_dominance', 0)

            # Market sentiment analysis
            if market_cap_change > 3:
                sentiment = "🚀 Very Bullish"
                sentiment_desc = "Market sangat bullish dengan pertumbuhan kuat"
            elif market_cap_change > 1:
                sentiment = "📈 Bullish"
                sentiment_desc = "Market bullish dengan tren positif"
            elif market_cap_change > -1:
                sentiment = "😐 Neutral"
                sentiment_desc = "Market dalam kondisi sideways"
            elif market_cap_change > -3:
                sentiment = "📉 Bearish"
                sentiment_desc = "Market bearish dengan tekanan jual"
            else:
                sentiment = "💥 Very Bearish"
                sentiment_desc = "Market sangat bearish dengan penurunan tajam"

            # Format market analysis
            analysis = f"""🌍 **OVERVIEW PASAR CRYPTO GLOBAL**

🕐 **Analysis Time**: {current_time}
🎯 **Market Sentiment**: {sentiment}

💰 **GLOBAL METRICS:**
• Total Market Cap: ${total_market_cap/1e12:.2f}T
• 24h Market Change: {market_cap_change:+.2f}%
• Total Volume 24h: ${total_volume/1e9:.1f}B
• Active Cryptocurrencies: {active_cryptos:,}
• BTC Dominance: {btc_dominance:.1f}%
• ETH Dominance: {eth_dominance:.1f}%

📊 **MARKET ANALYSIS:**
• 🎭 **Sentiment**: {sentiment_desc}
• 📈 **Dominance**: {"BTC masih mendominasi" if btc_dominance > 50 else "Altseason potential"}
• 💹 **Volume**: {"Tinggi" if total_volume > 50e9 else "Normal" if total_volume > 30e9 else "Rendah"}
• 🌊 **Trend**: {"Uptrend" if market_cap_change > 1 else "Downtrend" if market_cap_change < -1 else "Sideways"}

💡 **TRADING RECOMMENDATIONS:**
{self._get_market_trading_recommendations(market_cap_change, btc_dominance)}

📡 **Data Sources**: CoinMarketCap Global Metrics
🔄 **Update Frequency**: Real-time market data refresh"""

            return analysis
            
        except Exception as e:
            return self._get_basic_market_fallback()

    def _get_market_trading_recommendations(self, market_change, btc_dominance):
        """Get trading recommendations based on market conditions - Helper function"""
        try:
            recommendations = []
            
            if market_change > 2:
                recommendations.append("• 🚀 Consider long positions pada major coins")
                recommendations.append("• 📈 Altcoins berpotensi follow BTC momentum")
            elif market_change > 0:
                recommendations.append("• 🎯 Selective long pada coins dengan strong fundamentals")
                recommendations.append("• ⚖️ Risk management tetap prioritas")
            elif market_change < -2:
                recommendations.append("• 🛡️ Defensive strategy, consider short positions")
                recommendations.append("• 💰 DCA opportunities pada major dips")
            else:
                recommendations.append("• 🕐 Wait and see approach")
                recommendations.append("• 📊 Focus on technical analysis untuk entry points")
                
            if btc_dominance > 55:
                recommendations.append("• 👑 BTC dominance tinggi, focus pada BTC trades")
            elif btc_dominance < 45:
                recommendations.append("• 🌈 Altseason potential, consider altcoin positions")
                
            return "\n".join(recommendations)
            
        except:
            return "• Analisis rekomendasi temporarily unavailable"

    def _get_basic_market_fallback(self):
        """Get basic market fallback when APIs fail - Helper function"""
        return """🌍 **OVERVIEW PASAR CRYPTO**

⚠️ **Data global sementara tidak tersedia**

💡 **Alternatif analisis:**
• `/price btc` - Cek harga Bitcoin real-time
• `/price eth` - Cek harga Ethereum real-time  
• `/analyze btc` - Analisis fundamental Bitcoin
• `/futures_signals` - Scan sinyal trading

🔄 **Coba command `/market` lagi dalam beberapa menit**

📡 **Info**: Menggunakan analisis teknikal sebagai backup"""

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

💰 **GLOBAL METRICS:**
• Total Market Cap: ${total_market_cap/1e12:.2f}T
• 24h Market Change: {self._format_percentage(market_cap_change)}
• Total Volume 24h: ${total_volume/1e9:.1f}B
• Active Cryptocurrencies: {active_cryptos:,}
• BTC Dominance: {btc_dominance:.1f}%
• ETH Dominance: {eth_dominance:.1f}%

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


@dataclass
class CryptoMentorAI:
    """
    Minimal AI helper untuk bot. Menyediakan API sync & async yang umum dipakai:
      - handle(text, user=None)        -> str
      - respond(text, user=None)       -> str
      - __call__(text, user=None)      -> str
      - ahandle(text, user=None)       -> awaitable[str]
      - arespond(text, user=None)      -> awaitable[str]

    Ganti implementasi 'generate_reply' sesuai kebutuhan (mis. pakai OpenAI).
    """
    config: Dict[str, Any] = field(default_factory=dict)

    def generate_reply(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        # TODO: integrasikan ke pipeline sebenarnya (OpenAI, rules, dsb).
        # Untuk sekarang, kasih jawaban dummy agar import dan wiring tidak error.
        text = (text or "").strip()
        if not text:
            return "Hi! CryptoMentorAI is ready ✅"
        return f"🤖 CryptoMentorAI received: {text}"

    # --- Sync APIs ---
    def handle(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        return self.generate_reply(text, user)

    def respond(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        return self.generate_reply(text, user)

    def __call__(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        return self.generate_reply(text, user)

    # --- Async wrappers (untuk handler yang awaitable) ---
    async def ahandle(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        return self.generate_reply(text, user)

    async def arespond(self, text: str, user: Optional[Dict[str, Any]] = None) -> str:
        return self.generate_reply(text, user)

# Jika proyek punya kelas lama bernama berbeda, buka alias agar tetap kompatibel:
try:
    # contoh: kalau sebelumnya ada `class CryptoMentor: ...`
    CryptoMentor  # type: ignore[name-defined]
    # buat alias supaya `from ai_assistant import CryptoMentorAI` tetap berhasil
    CryptoMentorAI = CryptoMentor  # type: ignore[assignment]
except Exception:
    pass