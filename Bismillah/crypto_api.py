import requests
import os
import time
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.coingecko_key = os.getenv("COINGECKO_API_KEY")
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"
        self.coingecko_base_url = "https://pro-api.coingecko.com/api/v3" if self.coingecko_key else "https://api.coingecko.com/api/v3"

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
                timeout=15
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

    # === COINGECKO API METHODS ===

    def get_coingecko_price(self, symbol):
        """Get price data from CoinGecko API"""
        try:
            # Convert symbol to CoinGecko ID format
            symbol_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'ADA': 'cardano', 'SOL': 'solana', 'XRP': 'ripple',
                'DOT': 'polkadot', 'DOGE': 'dogecoin', 'MATIC': 'polygon',
                'AVAX': 'avalanche-2', 'LINK': 'chainlink', 'LTC': 'litecoin',
                'UNI': 'uniswap', 'ATOM': 'cosmos', 'FIL': 'filecoin',
                'TRX': 'tron', 'ETC': 'ethereum-classic', 'XLM': 'stellar',
                'AAVE': 'aave', 'ALGO': 'algorand', 'VET': 'vechain'
            }

            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            headers = {}
            if self.coingecko_key:
                headers['x-cg-pro-api-key'] = self.coingecko_key

            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
                'include_last_updated_at': 'true'
            }

            response = requests.get(
                f"{self.coingecko_base_url}/simple/price",
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if coin_id in data:
                coin_data = data[coin_id]
                return {
                    'symbol': symbol.upper(),
                    'coin_id': coin_id,
                    'price': coin_data.get('usd', 0),
                    'change_24h': coin_data.get('usd_24h_change', 0),
                    'volume_24h': coin_data.get('usd_24h_vol', 0),
                    'market_cap': coin_data.get('usd_market_cap', 0),
                    'last_updated': coin_data.get('last_updated_at', 0),
                    'source': 'coingecko_pro' if self.coingecko_key else 'coingecko_free'
                }
            else:
                return {'error': f"Symbol {symbol} not found in CoinGecko"}

        except Exception as e:
            return {'error': f"CoinGecko API error: {str(e)}"}

    def get_coingecko_market_data(self, symbol):
        """Get comprehensive market data from CoinGecko"""
        try:
            symbol_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'ADA': 'cardano', 'SOL': 'solana', 'XRP': 'ripple',
                'DOT': 'polkadot', 'DOGE': 'dogecoin', 'MATIC': 'polygon'
            }

            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            headers = {}
            if self.coingecko_key:
                headers['x-cg-pro-api-key'] = self.coingecko_key

            response = requests.get(
                f"{self.coingecko_base_url}/coins/{coin_id}",
                params={
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                },
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            market_data = data.get('market_data', {})
            
            return {
                'symbol': symbol.upper(),
                'coin_id': coin_id,
                'name': data.get('name', ''),
                'current_price': market_data.get('current_price', {}).get('usd', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'market_cap_rank': market_data.get('market_cap_rank', 0),
                'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                'high_24h': market_data.get('high_24h', {}).get('usd', 0),
                'low_24h': market_data.get('low_24h', {}).get('usd', 0),
                'price_change_24h': market_data.get('price_change_24h', 0),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                'price_change_percentage_7d': market_data.get('price_change_percentage_7d', 0),
                'price_change_percentage_30d': market_data.get('price_change_percentage_30d', 0),
                'circulating_supply': market_data.get('circulating_supply', 0),
                'total_supply': market_data.get('total_supply', 0),
                'max_supply': market_data.get('max_supply', 0),
                'ath': market_data.get('ath', {}).get('usd', 0),
                'ath_change_percentage': market_data.get('ath_change_percentage', {}).get('usd', 0),
                'ath_date': market_data.get('ath_date', {}).get('usd', ''),
                'atl': market_data.get('atl', {}).get('usd', 0),
                'atl_change_percentage': market_data.get('atl_change_percentage', {}).get('usd', 0),
                'atl_date': market_data.get('atl_date', {}).get('usd', ''),
                'last_updated': data.get('last_updated', ''),
                'source': 'coingecko_pro' if self.coingecko_key else 'coingecko_free'
            }

        except Exception as e:
            return {'error': f"CoinGecko market data error: {str(e)}"}

    def get_coingecko_global_data(self):
        """Get global crypto market data from CoinGecko"""
        try:
            headers = {}
            if self.coingecko_key:
                headers['x-cg-pro-api-key'] = self.coingecko_key

            response = requests.get(
                f"{self.coingecko_base_url}/global",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            global_data = data.get('data', {})
            
            return {
                'total_market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
                'total_volume': global_data.get('total_volume', {}).get('usd', 0),
                'market_cap_percentage': global_data.get('market_cap_percentage', {}),
                'market_cap_change_percentage_24h_usd': global_data.get('market_cap_change_percentage_24h_usd', 0),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                'upcoming_icos': global_data.get('upcoming_icos', 0),
                'ongoing_icos': global_data.get('ongoing_icos', 0),
                'ended_icos': global_data.get('ended_icos', 0),
                'markets': global_data.get('markets', 0),
                'updated_at': global_data.get('updated_at', 0),
                'source': 'coingecko_global'
            }

        except Exception as e:
            return {'error': f"CoinGecko global data error: {str(e)}"}

    # === MULTI-API INTEGRATION METHODS ===

    def get_multi_api_price(self, symbol, force_refresh=False):
        """Get price from multiple APIs and combine the best data"""
        price_sources = {}

        # 1. Try Binance first (fastest and most accurate for real-time)
        try:
            binance_data = self.get_binance_price(symbol)
            if 'error' not in binance_data and binance_data.get('price', 0) > 0:
                price_sources['binance'] = binance_data
                print(f"✅ Real-time Binance data for {symbol}: ${binance_data.get('price', 0):,.2f}")
                # Return immediately if Binance works to ensure real-time
                return self._combine_price_data(symbol, price_sources)
        except Exception as e:
            print(f"⚠️ Binance API error for {symbol}: {e}")
            pass

        # 2. Try CoinGecko (comprehensive market data)
        try:
            coingecko_data = self.get_coingecko_price(symbol)
            if 'error' not in coingecko_data and coingecko_data.get('price', 0) > 0:
                price_sources['coingecko'] = coingecko_data
        except:
            pass

        # 3. Try CoinGecko market data for additional insights
        try:
            market_data = self.get_coingecko_market_data(symbol)
            if 'error' not in market_data and market_data.get('current_price', 0) > 0:
                price_sources['coingecko_market'] = market_data
        except:
            pass

        # Combine best data from multiple sources
        if price_sources:
            return self._combine_price_data(symbol, price_sources)
        else:
            return self._fallback_price(symbol, "All APIs unavailable")

    def _combine_price_data(self, symbol, price_sources):
        """Combine price data from multiple sources intelligently"""
        combined_data = {
            'symbol': symbol.upper(),
            'sources_used': list(price_sources.keys()),
            'data_quality': 'excellent' if len(price_sources) >= 2 else 'good'
        }

        # Priority: Binance for real-time price, CoinGecko for market data
        if 'binance' in price_sources:
            binance = price_sources['binance']
            combined_data.update({
                'price': binance.get('price', 0),
                'change_24h': binance.get('change_24h', 0),
                'volume_24h': binance.get('volume_24h', 0),
                'high_24h': binance.get('high_24h', 0),
                'low_24h': binance.get('low_24h', 0),
                'primary_source': 'binance'
            })

        # Add CoinGecko market insights
        if 'coingecko_market' in price_sources:
            cg_market = price_sources['coingecko_market']
            combined_data.update({
                'market_cap': cg_market.get('market_cap', 0),
                'market_cap_rank': cg_market.get('market_cap_rank', 0),
                'circulating_supply': cg_market.get('circulating_supply', 0),
                'max_supply': cg_market.get('max_supply', 0),
                'ath': cg_market.get('ath', 0),
                'ath_change_percentage': cg_market.get('ath_change_percentage', 0),
                'price_change_7d': cg_market.get('price_change_percentage_7d', 0),
                'price_change_30d': cg_market.get('price_change_percentage_30d', 0),
                'market_data_source': 'coingecko'
            })

            # Use CoinGecko price if Binance not available
            if 'price' not in combined_data:
                combined_data.update({
                    'price': cg_market.get('current_price', 0),
                    'change_24h': cg_market.get('price_change_percentage_24h', 0),
                    'primary_source': 'coingecko'
                })

        # Add simple CoinGecko data if available
        if 'coingecko' in price_sources and 'price' not in combined_data:
            cg_simple = price_sources['coingecko']
            combined_data.update({
                'price': cg_simple.get('price', 0),
                'change_24h': cg_simple.get('change_24h', 0),
                'volume_24h': cg_simple.get('volume_24h', 0),
                'primary_source': 'coingecko'
            })

        return combined_data

    def get_comprehensive_analysis_data(self, symbol):
        """Get comprehensive data from all APIs for analysis"""
        analysis_data = {
            'symbol': symbol.upper(),
            'timestamp': datetime.now().isoformat(),
            'data_sources': {},
            'successful_calls': 0,
            'total_calls': 0
        }

        # 1. Binance price data
        try:
            binance_price = self.get_binance_price(symbol)
            analysis_data['data_sources']['binance_price'] = binance_price
            analysis_data['total_calls'] += 1
            if 'error' not in binance_price:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 2. Binance futures data
        try:
            binance_futures = self.get_comprehensive_futures_data(symbol)
            analysis_data['data_sources']['binance_futures'] = binance_futures
            analysis_data['total_calls'] += 1
            if 'error' not in binance_futures:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 3. CoinGecko market data
        try:
            coingecko_market = self.get_coingecko_market_data(symbol)
            analysis_data['data_sources']['coingecko_market'] = coingecko_market
            analysis_data['total_calls'] += 1
            if 'error' not in coingecko_market:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 4. CoinGecko global data
        try:
            global_data = self.get_coingecko_global_data()
            analysis_data['data_sources']['coingecko_global'] = global_data
            analysis_data['total_calls'] += 1
            if 'error' not in global_data:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 5. Crypto news
        try:
            news_data = self.get_crypto_news(5)
            analysis_data['data_sources']['crypto_news'] = news_data
            analysis_data['total_calls'] += 1
            if news_data and 'error' not in (news_data[0] if news_data else {}):
                analysis_data['successful_calls'] += 1
        except:
            pass

        # Calculate data quality score
        success_rate = (analysis_data['successful_calls'] / analysis_data['total_calls']) if analysis_data['total_calls'] > 0 else 0
        
        if success_rate >= 0.8:
            analysis_data['data_quality'] = 'excellent'
        elif success_rate >= 0.6:
            analysis_data['data_quality'] = 'good'
        elif success_rate >= 0.4:
            analysis_data['data_quality'] = 'fair'
        else:
            analysis_data['data_quality'] = 'poor'

        return analysis_data

    # === LEGACY METHOD REPLACEMENTS ===

    def get_futures_data(self, symbol):
        """Legacy method - replaced with Binance long/short ratio"""
        ls_data = self.get_binance_long_short_ratio(symbol)
        if 'error' in ls_data:
            return self._fallback_futures_data(symbol)
        return ls_data

    def get_price(self, symbol, force_refresh=False):
        """Get price with multi-API integration"""
        return self.get_multi_api_price(symbol, force_refresh)

    

    def get_funding_rate(self, symbol):
        """Get funding rate data from Binance"""
        return self.get_binance_funding_rate(symbol)

    def get_open_interest(self, symbol):
        """Get open interest data from Binance"""
        return self.get_binance_open_interest(symbol)

    def get_liquidation_data(self, symbol):
        """Get liquidation data from Binance"""
        return self.get_binance_liquidation_orders(symbol)

    # === UTILITY METHODS ===

    def get_futures_tickers(self):
        """Get all available futures symbols"""
        return self.provider.get_tickers()

    def get_advanced_futures_analytics(self, symbol):
        """Get advanced futures analytics using multiple Binance endpoints"""
        try:
            # Get comprehensive data
            analytics = {}
            
            # 1. Get price and volume metrics
            price_data = self.get_binance_futures_price(symbol)
            analytics['price_metrics'] = price_data
            
            # 2. Get funding rate trends
            funding_data = self.get_binance_funding_rate(symbol, limit=50)
            analytics['funding_trends'] = funding_data
            
            # 3. Get open interest analytics
            oi_data = self.get_binance_open_interest(symbol)
            analytics['open_interest'] = oi_data
            
            # 4. Get long/short sentiment over time
            ls_data = self.get_binance_long_short_ratio(symbol, period='1h', limit=24)
            analytics['sentiment_trends'] = ls_data
            
            # 5. Get recent liquidation patterns
            liq_data = self.get_binance_liquidation_orders(symbol, limit=200)
            analytics['liquidation_patterns'] = liq_data
            
            # 6. Calculate advanced metrics
            analytics['advanced_metrics'] = self._calculate_advanced_metrics(
                price_data, funding_data, oi_data, ls_data, liq_data
            )
            
            return {
                'symbol': symbol,
                'analytics': analytics,
                'timestamp': datetime.now().isoformat(),
                'source': 'binance_advanced_analytics'
            }
            
        except Exception as e:
            return {'error': f"Advanced analytics error: {str(e)}"}

    def _calculate_advanced_metrics(self, price_data, funding_data, oi_data, ls_data, liq_data):
        """Calculate advanced trading metrics"""
        try:
            metrics = {}
            
            # Price momentum score
            if 'error' not in price_data:
                change_24h = price_data.get('change_24h', 0)
                volume_24h = price_data.get('volume_24h', 0)
                
                momentum_score = abs(change_24h) * (volume_24h / 1000000000)  # Weighted by volume
                metrics['momentum_score'] = min(momentum_score, 100)  # Cap at 100
            
            # Funding rate pressure
            if 'error' not in funding_data:
                avg_funding = funding_data.get('average_funding_rate', 0)
                last_funding = funding_data.get('last_funding_rate', 0)
                
                funding_pressure = abs(last_funding) * 1000  # Convert to basis points
                metrics['funding_pressure'] = funding_pressure
            
            # Open interest health
            if 'error' not in oi_data:
                oi_value = oi_data.get('open_interest', 0)
                # Normalize OI (this is simplified)
                oi_health = min(oi_value / 100000000, 10)  # Scale factor
                metrics['oi_health'] = oi_health
            
            # Sentiment extremes
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                sentiment_extreme = abs(long_ratio - 50)  # Distance from neutral
                metrics['sentiment_extreme'] = sentiment_extreme
            
            # Liquidation risk
            if 'error' not in liq_data:
                total_liq = liq_data.get('total_liquidation', 0)
                liq_risk = min(total_liq / 1000000000, 10)  # Scale factor
                metrics['liquidation_risk'] = liq_risk
            
            return metrics
            
        except Exception as e:
            return {'error': f"Metrics calculation error: {str(e)}"}

    def check_api_status(self):
        """Check API health status with enhanced Binance coverage"""
        try:
            # Test Binance Spot
            spot_test = requests.get(f"{self.binance_spot_url}/ping", timeout=5)
            binance_spot_ok = spot_test.status_code == 200

            # Test Binance Futures
            futures_test = requests.get(f"{self.binance_futures_url}/ping", timeout=5)
            binance_futures_ok = futures_test.status_code == 200

            # Test CryptoNews
            news_ok = bool(self.cryptonews_key)

            # Test advanced futures endpoints
            try:
                test_symbol = 'BTCUSDT'
                oi_test = self.get_binance_open_interest(test_symbol)
                funding_test = self.get_binance_funding_rate(test_symbol)
                advanced_ok = 'error' not in oi_test and 'error' not in funding_test
            except:
                advanced_ok = False

            return {
                'binance_spot': binance_spot_ok,
                'binance_futures': binance_futures_ok,
                'binance_advanced': advanced_ok,
                'cryptonews': news_ok,
                'overall_health': binance_spot_ok and binance_futures_ok and advanced_ok,
                'primary_source': 'binance_comprehensive'
            }
        except Exception as e:
            return {
                'binance_spot': False,
                'binance_futures': False,
                'binance_advanced': False,
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
        # Try CoinGecko as backup before using mock data
        try:
            coingecko_data = self.get_coingecko_price(symbol)
            if 'error' not in coingecko_data and coingecko_data.get('price', 0) > 0:
                print(f"✅ Using CoinGecko fallback for {symbol}")
                return {
                    'symbol': symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper(),
                    'price': coingecko_data.get('price', 0),
                    'change_24h': coingecko_data.get('change_24h', 0),
                    'volume_24h': coingecko_data.get('volume_24h', 0),
                    'source': 'coingecko_fallback',
                    'error_reason': f"Binance failed: {error_msg}"
                }
        except Exception as e:
            print(f"⚠️ CoinGecko fallback also failed: {e}")

        # Only use mock data as last resort
        import random
        mock_prices = {
            'BTCUSDT': random.uniform(65000, 75000),
            'ETHUSDT': random.uniform(3000, 4000),
            'BNBUSDT': random.uniform(500, 700),
            'ADAUSDT': random.uniform(0.4, 0.6),
            'SOLUSDT': random.uniform(150, 250),
            'XRPUSDT': random.uniform(0.5, 0.7),
            'DOGEUSDT': random.uniform(0.08, 0.12)
        }

        normalized_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
        base_price = mock_prices.get(normalized_symbol, random.uniform(1, 100))

        return {
            'symbol': normalized_symbol,
            'price': base_price,
            'change_24h': random.uniform(-5, 5),
            'high_24h': base_price * random.uniform(1.01, 1.05),
            'low_24h': base_price * random.uniform(0.95, 0.99),
            'volume_24h': random.uniform(10000000, 100000000),
            'source': 'fallback_simulation',
            'error_reason': error_msg,
            'warning': 'SIMULATION DATA - Check API connection'
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

    def get_multiple_prices(self, symbols):
        """Get prices for multiple symbols"""
        prices_data = {}
        
        for symbol in symbols:
            try:
                price_data = self.get_binance_price(symbol)
                if 'error' not in price_data:
                    prices_data[symbol] = {
                        'price': price_data.get('price', 0),
                        'change_24h': price_data.get('change_24h', 0),
                        'volume_24h': price_data.get('volume_24h', 0),
                        'source': price_data.get('source', 'binance')
                    }
            except Exception as e:
                print(f"Error getting price for {symbol}: {e}")
                continue
                
        return prices_data if prices_data else {'error': 'No price data available'}

    def get_market_overview(self):
        """Get enhanced market overview data using multiple APIs"""
        try:
            # Try CoinGecko global data first (most comprehensive)
            global_data = self.get_coingecko_global_data()
            
            if 'error' not in global_data:
                # Use real CoinGecko global data
                return {
                    'total_market_cap': global_data.get('total_market_cap', 0),
                    'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0),
                    'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                    'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                    'total_volume': global_data.get('total_volume', 0),
                    'markets': global_data.get('markets', 0),
                    'source': 'coingecko_global',
                    'last_updated': global_data.get('updated_at', 0)
                }
            else:
                # Fallback to Binance-based estimation
                major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']
                prices_data = self.get_multiple_prices(major_symbols)
                
                if 'error' not in prices_data:
                    # Calculate market metrics from available data
                    btc_data = prices_data.get('BTC', {})
                    eth_data = prices_data.get('ETH', {})
                    
                    # Estimate market cap and dominance
                    total_volume = sum(data.get('volume_24h', 0) for data in prices_data.values())
                    btc_volume = btc_data.get('volume_24h', 0)
                    
                    btc_dominance = (btc_volume / total_volume * 100) if total_volume > 0 else 45.0
                    
                    # Calculate average market change
                    changes = [data.get('change_24h', 0) for data in prices_data.values() if 'change_24h' in data]
                    avg_change = sum(changes) / len(changes) if changes else 0
                    
                    return {
                        'total_market_cap': total_volume * 15,  # Better estimate
                        'market_cap_change_24h': avg_change,
                        'btc_dominance': btc_dominance,
                        'eth_dominance': 18.0,
                        'btc_price': btc_data.get('price', 0),
                        'eth_price': eth_data.get('price', 0),
                        'btc_change_24h': btc_data.get('change_24h', 0),
                        'eth_change_24h': eth_data.get('change_24h', 0),
                        'active_cryptocurrencies': len(prices_data),
                        'source': 'binance_fallback'
                    }
                else:
                    return {'error': 'Market overview unavailable'}
        except Exception as e:
            return {'error': f"Market overview error: {str(e)}"}