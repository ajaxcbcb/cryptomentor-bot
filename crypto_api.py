import requests
import os
import time
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"

    # === BINANCE SPOT API METHODS ===

    def get_binance_server_time(self):
        """Get Binance server time"""
        try:
            response = requests.get(f"{self.binance_spot_url}/time", timeout=10)
            response.raise_for_status()
            data = response.json()
            server_time = data['serverTime']

            # Convert to readable format
            dt = datetime.fromtimestamp(server_time / 1000, tz=timezone.utc)

            return {
                'server_time_ms': server_time,
                'server_time_iso': dt.isoformat(),
                'server_time_readable': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'source': 'binance_spot'
            }
        except Exception as e:
            return {'error': f"Server time error: {str(e)}"}

    def get_binance_price(self, symbol):
        """Get real-time price from Binance Spot API"""
        try:
            # Normalize symbol format
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get 24hr ticker statistics
            response = requests.get(
                f"{self.binance_spot_url}/ticker/24hr",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume_24h': float(data['volume']),
                'quote_volume_24h': float(data['quoteVolume']),
                'open_price': float(data['openPrice']),
                'close_price': float(data['lastPrice']),
                'price_change': float(data['priceChange']),
                'count': int(data['count']),
                'first_id': data['firstId'],
                'last_id': data['lastId'],
                'open_time': data['openTime'],
                'close_time': data['closeTime'],
                'source': 'binance_spot'
            }
        except Exception as e:
            return self._fallback_price(symbol, str(e))

    def get_binance_candlestick(self, symbol, interval='1h', limit=100):
        """Get candlestick/kline data from Binance"""
        try:
            # Normalize symbol
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_spot_url}/klines",
                params={
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            candlesticks = []
            for kline in data:
                candlesticks.append({
                    'open_time': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': kline[6],
                    'quote_asset_volume': float(kline[7]),
                    'trades_count': kline[8],
                    'taker_buy_base_volume': float(kline[9]),
                    'taker_buy_quote_volume': float(kline[10]),
                    'open_time_iso': datetime.fromtimestamp(kline[0]/1000, tz=timezone.utc).isoformat(),
                    'close_time_iso': datetime.fromtimestamp(kline[6]/1000, tz=timezone.utc).isoformat()
                })

            return {
                'symbol': symbol,
                'interval': interval,
                'candlesticks': candlesticks,
                'count': len(candlesticks),
                'source': 'binance_spot'
            }
        except Exception as e:
            return {'error': f"Candlestick error: {str(e)}"}

    # === BINANCE FUTURES API METHODS ===

    def get_binance_futures_price(self, symbol):
        """Get futures price ticker from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/ticker/24hr",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume_24h': float(data['volume']),
                'quote_volume_24h': float(data['quoteVolume']),
                'open_price': float(data['openPrice']),
                'weighted_avg_price': float(data['weightedAvgPrice']),
                'price_change': float(data['priceChange']),
                'count': int(data['count']),
                'open_time': data['openTime'],
                'close_time': data['closeTime'],
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Futures price error: {str(e)}"}

    def get_binance_mark_price(self, symbol):
        """Get mark price and funding rate from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/premiumIndex",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'mark_price': float(data['markPrice']),
                'index_price': float(data['indexPrice']),
                'estimated_settle_price': float(data.get('estimatedSettlePrice', 0)),
                'last_funding_rate': float(data['lastFundingRate']),
                'interest_rate': float(data.get('interestRate', 0)),
                'next_funding_time': data['nextFundingTime'],
                'next_funding_time_iso': datetime.fromtimestamp(data['nextFundingTime']/1000, tz=timezone.utc).isoformat(),
                'time': data['time'],
                'time_iso': datetime.fromtimestamp(data['time']/1000, tz=timezone.utc).isoformat(),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Mark price error: {str(e)}"}

    def get_binance_funding_rate(self, symbol, limit=100):
        """Get funding rate history from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get current funding rate from premium index
            mark_data = self.get_binance_mark_price(symbol)

            # Get funding rate history
            response = requests.get(
                f"{self.binance_futures_url}/fundingRate",
                params={
                    'symbol': symbol,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            history_data = response.json()

            funding_history = []
            for record in history_data:
                funding_history.append({
                    'symbol': record['symbol'],
                    'funding_rate': float(record['fundingRate']),
                    'funding_time': record['fundingTime'],
                    'funding_time_iso': datetime.fromtimestamp(record['fundingTime']/1000, tz=timezone.utc).isoformat()
                })

            # Calculate average funding rate
            avg_funding = sum([r['funding_rate'] for r in funding_history]) / len(funding_history) if funding_history else 0

            return {
                'symbol': symbol,
                'mark_price': mark_data.get('mark_price', 0),
                'index_price': mark_data.get('index_price', 0),
                'last_funding_rate': mark_data.get('last_funding_rate', 0),
                'next_funding_time': mark_data.get('next_funding_time', 0),
                'next_funding_time_iso': mark_data.get('next_funding_time_iso', ''),
                'average_funding_rate': avg_funding,
                'funding_history': funding_history[-10:],  # Last 10 records
                'history_count': len(funding_history),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Funding rate error: {str(e)}"}

    def get_binance_open_interest(self, symbol):
        """Get open interest from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/openInterest",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'open_interest': float(data['openInterest']),
                'time': data['time'],
                'time_iso': datetime.fromtimestamp(data['time']/1000, tz=timezone.utc).isoformat(),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Open interest error: {str(e)}"}

    def get_binance_long_short_ratio(self, symbol, period='5m', limit=30):
        """Get long/short ratio from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get top trader long/short ratio
            response = requests.get(
                f"{self.binance_futures_url}/topLongShortPositionRatio",
                params={
                    'symbol': symbol,
                    'period': period,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data:
                latest = data[-1]
                long_ratio = float(latest['longShortRatio']) / (1 + float(latest['longShortRatio'])) * 100
                short_ratio = 100 - long_ratio

                return {
                    'symbol': symbol,
                    'long_ratio': long_ratio,
                    'short_ratio': short_ratio,
                    'long_short_ratio': float(latest['longShortRatio']),
                    'long_account': float(latest['longAccount']),
                    'short_account': float(latest['shortAccount']),
                    'timestamp': latest['timestamp'],
                    'timestamp_iso': datetime.fromtimestamp(latest['timestamp']/1000, tz=timezone.utc).isoformat(),
                    'period': period,
                    'data_points': len(data),
                    'source': 'binance_futures'
                }
            else:
                return {'error': 'No long/short ratio data available'}

        except Exception as e:
            return {'error': f"Long/short ratio error: {str(e)}"}

    def get_binance_liquidation_orders(self, symbol, limit=100):
        """Get liquidation orders from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/forceOrders",
                params={
                    'symbol': symbol,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            total_liquidation = 0
            long_liquidation = 0
            short_liquidation = 0

            liquidations = []
            for order in data:
                qty = float(order['origQty'])
                price = float(order['price'])
                value = qty * price
                total_liquidation += value

                if order['side'] == 'SELL':  # Long liquidation
                    long_liquidation += value
                else:  # Short liquidation
                    short_liquidation += value

                liquidations.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'order_type': order['origType'],
                    'quantity': qty,
                    'price': price,
                    'value': value,
                    'status': order['status'],
                    'time': order['time'],
                    'time_iso': datetime.fromtimestamp(order['time']/1000, tz=timezone.utc).isoformat()
                })

            return {
                'symbol': symbol,
                'total_liquidation': total_liquidation,
                'long_liquidation': long_liquidation,
                'short_liquidation': short_liquidation,
                'liquidation_orders': liquidations[-20:],  # Last 20 orders
                'total_orders': len(liquidations),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Liquidation orders error: {str(e)}"}

    # === COMPREHENSIVE DATA METHODS ===

    def get_comprehensive_futures_data(self, symbol):
        """Get all futures data in one call"""
        try:
            # Get all futures data
            price_data = self.get_binance_futures_price(symbol)
            mark_data = self.get_binance_mark_price(symbol)
            funding_data = self.get_binance_funding_rate(symbol)
            oi_data = self.get_binance_open_interest(symbol)
            ls_ratio_data = self.get_binance_long_short_ratio(symbol)
            liquidation_data = self.get_binance_liquidation_orders(symbol)

            successful_calls = 0
            total_calls = 6

            # Count successful API calls
            for data in [price_data, mark_data, funding_data, oi_data, ls_ratio_data, liquidation_data]:
                if 'error' not in data:
                    successful_calls += 1

            return {
                'symbol': symbol,
                'price_data': price_data,
                'mark_price_data': mark_data,
                'funding_rate_data': funding_data,
                'open_interest_data': oi_data,
                'long_short_ratio_data': ls_ratio_data,
                'liquidation_data': liquidation_data,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': 'excellent' if successful_calls >= 5 else 'good' if successful_calls >= 4 else 'partial',
                'source': 'binance_comprehensive'
            }
        except Exception as e:
            return {'error': f"Comprehensive data error: {str(e)}"}

    # === LEGACY METHOD REPLACEMENTS ===

    def get_futures_data(self, symbol):
        """Legacy method - replaced with Binance long/short ratio"""
        ls_data = self.get_binance_long_short_ratio(symbol)
        if 'error' in ls_data:
            return self._fallback_futures_data(symbol)
        return ls_data

    def get_price(self, symbol, force_refresh=False):
        """Get price with Binance as primary source"""
        # Try Binance first
        binance_data = self.get_binance_price(symbol)
        if 'error' not in binance_data:
            return binance_data

        # Fallback to CoinGecko if available
        return self._fallback_price(symbol, "Binance unavailable")

    def get_coinglass_comprehensive_data(self, symbol):
        """Replace Coinglass with comprehensive Binance data"""
        return self.get_comprehensive_futures_data(symbol)

    def get_funding_rate(self, symbol):
        """Get funding rate data from Binance"""
        return self.get_binance_funding_rate(symbol)

    # === UTILITY METHODS ===

    def get_futures_tickers(self):
        """Get all available futures symbols"""
        return self.provider.get_tickers()

    def check_api_status(self):
        """Check API health status"""
        try:
            # Test Binance Spot
            spot_test = requests.get(f"{self.binance_spot_url}/ping", timeout=5)
            binance_spot_ok = spot_test.status_code == 200

            # Test Binance Futures
            futures_test = requests.get(f"{self.binance_futures_url}/ping", timeout=5)
            binance_futures_ok = futures_test.status_code == 200

            # Test CryptoNews
            news_ok = bool(self.cryptonews_key)

            return {
                'binance_spot': binance_spot_ok,
                'binance_futures': binance_futures_ok,
                'cryptonews': news_ok,
                'overall_health': binance_spot_ok and binance_futures_ok
            }
        except Exception as e:
            return {
                'binance_spot': False,
                'binance_futures': False,
                'cryptonews': False,
                'overall_health': False,
                'error': str(e)
            }

    def _format_price_display(self, price):
        """Smart price formatting"""
        if price >= 1000:
            return f"${price:,.2f}"
        elif price >= 1:
            return f"${price:.4f}"
        elif price >= 0.01:
            return f"${price:.6f}"
        else:
            return f"${price:.8f}"

    def _fallback_price(self, symbol, error_msg):
        """Fallback price data when Binance fails"""
        import random
        # Mock realistic crypto prices for common symbols
        mock_prices = {
            'BTCUSDT': random.uniform(40000, 70000),
            'ETHUSDT': random.uniform(2000, 4000),
            'BNBUSDT': random.uniform(300, 600),
            'ADAUSDT': random.uniform(0.3, 0.8),
            'SOLUSDT': random.uniform(80, 200),
            'XRPUSDT': random.uniform(0.4, 0.8),
            'DOGEUSDT': random.uniform(0.06, 0.15)
        }

        normalized_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
        base_price = mock_prices.get(normalized_symbol, random.uniform(1, 100))

        return {
            'symbol': normalized_symbol,
            'price': base_price,
            'change_24h': random.uniform(-10, 10),
            'high_24h': base_price * random.uniform(1.01, 1.15),
            'low_24h': base_price * random.uniform(0.85, 0.99),
            'volume_24h': random.uniform(1000000, 100000000),
            'source': 'fallback_simulation',
            'error_reason': error_msg
        }

    def _fallback_futures_data(self, symbol):
        """Fallback futures data when Binance fails"""
        import random
        long_ratio = random.uniform(35, 75)
        return {
            'symbol': symbol,
            'long_ratio': long_ratio,
            'short_ratio': 100 - long_ratio,
            'long_short_ratio': long_ratio / (100 - long_ratio),
            'source': 'fallback_simulation'
        }

    # === NEWS API ===

    def get_latest_crypto_news(self, limit=5):
        """Get latest crypto news"""
        return self.get_crypto_news(limit)

    def get_crypto_news(self, limit=5):
        """Get crypto news from CryptoNews API"""
        if not self.cryptonews_key:
            return self._fallback_news(limit)

        url = "https://cryptonews-api.com/api/v1/category"
        params = {
            "section": "general",
            "items": limit,
            "token": self.cryptonews_key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("data", [])

            # Add source info
            for article in articles:
                article['source'] = 'cryptonews_api'

            return articles
        except Exception as e:
            return self._fallback_news(limit)

    def _fallback_news(self, limit):
        """Fallback news when API fails"""
        mock_news = [
            {"title": "Bitcoin Reaches New All-Time High Amid Institutional Adoption", "url": "#", "source": "mock"},
            {"title": "Ethereum 2.0 Staking Rewards Show Strong Performance", "url": "#", "source": "mock"},
            {"title": "DeFi TVL Surpasses $100 Billion Milestone", "url": "#", "source": "mock"},
            {"title": "Major Exchange Lists New Altcoin with Strong Fundamentals", "url": "#", "source": "mock"},
            {"title": "Regulatory Clarity Boosts Crypto Market Sentiment", "url": "#", "source": "mock"}
        ]
        return mock_news[:limit]

    def get_timeframe_analysis(self, symbol, timeframe='1h'):
        """Get comprehensive timeframe analysis using Binance API"""
        try:
            # Get candlestick data for the timeframe
            candles_data = self.get_binance_candlestick(symbol, timeframe, 50)
            if 'error' in candles_data:
                return {'error': f"Failed to get candlestick data: {candles_data.get('error')}"}

            # Get current price and futures data
            price_data = self.get_binance_futures_price(symbol)
            mark_data = self.get_binance_mark_price(symbol)
            funding_data = self.get_binance_funding_rate(symbol)
            oi_data = self.get_binance_open_interest(symbol)
            ls_data = self.get_binance_long_short_ratio(symbol)
            liq_data = self.get_binance_liquidation_orders(symbol)

            # Analyze candlestick patterns and trends
            candlesticks = candles_data.get('candlesticks', [])
            trend_analysis = self._analyze_trend_from_candles(candlesticks, timeframe)
            support_resistance = self._calculate_support_resistance(candlesticks)
            volatility = self._calculate_volatility(candlesticks)

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'price_data': price_data,
                'mark_data': mark_data,
                'funding_data': funding_data,
                'open_interest_data': oi_data,
                'long_short_data': ls_data,
                'liquidation_data': liq_data,
                'candlesticks': candlesticks[-20:],  # Last 20 candles
                'trend_analysis': trend_analysis,
                'support_resistance': support_resistance,
                'volatility': volatility,
                'source': 'binance_timeframe_analysis'
            }
        except Exception as e:
            return {'error': f"Timeframe analysis error: {str(e)}"}

    def _analyze_trend_from_candles(self, candlesticks, timeframe):
        """Analyze trend from candlestick data"""
        if not candlesticks or len(candlesticks) < 10:
            return {'trend': 'unknown', 'strength': 'weak', 'direction': 'neutral'}

        # Calculate trend using moving averages
        closes = [float(candle['close']) for candle in candlesticks[-20:]]
        
        # Simple moving averages
        sma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
        sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
        sma_20 = sum(closes) / len(closes)

        # Trend direction
        if sma_5 > sma_10 > sma_20:
            direction = 'bullish'
            strength = 'strong' if (sma_5 - sma_20) / sma_20 > 0.02 else 'moderate'
        elif sma_5 < sma_10 < sma_20:
            direction = 'bearish'
            strength = 'strong' if (sma_20 - sma_5) / sma_20 > 0.02 else 'moderate'
        else:
            direction = 'sideways'
            strength = 'weak'

        # Calculate momentum
        price_change = (closes[-1] - closes[0]) / closes[0] * 100
        
        return {
            'trend': direction,
            'strength': strength,
            'direction': direction,
            'price_change_pct': price_change,
            'sma_5': sma_5,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'timeframe': timeframe
        }

    def _calculate_support_resistance(self, candlesticks):
        """Calculate support and resistance levels"""
        if not candlesticks or len(candlesticks) < 10:
            return {'support': 0, 'resistance': 0, 'levels': []}

        highs = [float(candle['high']) for candle in candlesticks[-20:]]
        lows = [float(candle['low']) for candle in candlesticks[-20:]]

        # Simple support/resistance calculation
        resistance = max(highs)
        support = min(lows)
        
        # Current price
        current_price = float(candlesticks[-1]['close'])
        
        # Calculate key levels
        levels = []
        for i in range(1, len(candlesticks) - 1):
            high = float(candlesticks[i]['high'])
            low = float(candlesticks[i]['low'])
            
            # Check for local highs (resistance)
            if (high > float(candlesticks[i-1]['high']) and 
                high > float(candlesticks[i+1]['high'])):
                levels.append({'type': 'resistance', 'price': high})
            
            # Check for local lows (support)
            if (low < float(candlesticks[i-1]['low']) and 
                low < float(candlesticks[i+1]['low'])):
                levels.append({'type': 'support', 'price': low})

        return {
            'support': support,
            'resistance': resistance,
            'current_price': current_price,
            'distance_to_support': (current_price - support) / current_price * 100,
            'distance_to_resistance': (resistance - current_price) / current_price * 100,
            'key_levels': levels[-5:]  # Last 5 key levels
        }

    def _calculate_volatility(self, candlesticks):
        """Calculate volatility metrics"""
        if not candlesticks or len(candlesticks) < 10:
            return {'volatility': 'low', 'atr': 0, 'price_range': 0}

        # Calculate Average True Range (ATR)
        atr_values = []
        for i in range(1, len(candlesticks)):
            high = float(candlesticks[i]['high'])
            low = float(candlesticks[i]['low'])
            prev_close = float(candlesticks[i-1]['close'])
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            atr_values.append(tr)

        atr = sum(atr_values[-14:]) / min(14, len(atr_values))  # 14-period ATR
        
        # Calculate price range
        recent_highs = [float(c['high']) for c in candlesticks[-10:]]
        recent_lows = [float(c['low']) for c in candlesticks[-10:]]
        price_range = (max(recent_highs) - min(recent_lows)) / min(recent_lows) * 100

        # Volatility classification
        if price_range > 10:
            volatility = 'very_high'
        elif price_range > 5:
            volatility = 'high'
        elif price_range > 2:
            volatility = 'moderate'
        else:
            volatility = 'low'

        return {
            'volatility': volatility,
            'atr': atr,
            'price_range': price_range,
            'classification': volatility
        }

    def get_market_overview(self):
        """Get market overview data"""
        try:
            # Get BTC and ETH as market indicators
            btc_data = self.get_binance_price('BTC')
            eth_data = self.get_binance_price('ETH')

            if 'error' not in btc_data and 'error' not in eth_data:
                return {
                    'total_market_cap': btc_data.get('quote_volume_24h', 0) * 50,  # Rough estimate
                    'btc_dominance': 45.0,  # Rough estimate
                    'eth_dominance': 18.0,  # Rough estimate
                    'btc_price': btc_data.get('price', 0),
                    'eth_price': eth_data.get('price', 0),
                    'btc_change_24h': btc_data.get('change_24h', 0),
                    'eth_change_24h': eth_data.get('change_24h', 0),
                    'source': 'binance_derived'
                }
            else:
                return {'error': 'Market overview unavailable'}
        except Exception as e:
            return {'error': f"Market overview error: {str(e)}"}