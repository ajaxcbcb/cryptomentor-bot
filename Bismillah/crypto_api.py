import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.providers.binance_provider import get_price, fetch_klines, normalize_symbol

class CryptoAPI:
    """
    Crypto API provider menggunakan Binance API sebagai pengganti CoinMarketCap
    Mempertahankan interface yang sama untuk kompatibilitas
    """

    def __init__(self):
        self.binance_available = True
        self._cache = {}
        self._cache_timeout = 60  # Reduced to 1 minute for market data freshness
        self._market_cache_timeout = 30  # 30 seconds for market overview (even faster)
        
        logging.info("CryptoAPI initialized with Binance provider - Optimized for concurrent users")

    def _make_request(self, url: str, headers: dict, params: dict = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Generic request method - sekarang menggunakan Binance provider
        """
        # This method is kept for compatibility but uses Binance internally
        return {'status': 'using_binance_provider'}

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto dari Binance API dengan akurasi tinggi dan validasi berlapis
        """
        try:
            # Check cache first
            cache_key = f"price_{symbol.upper()}"
            if not force_refresh and cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (time.time() - timestamp) < self._cache_timeout:
                    return cached_data

            # Enhanced symbol variants with priority ordering
            symbol_variants = self._get_enhanced_symbol_variants(symbol)
            
            best_result = None
            validation_errors = []

            # Try each symbol variant with enhanced validation
            for variant in symbol_variants:
                try:
                    # Get spot price with validation
                    spot_price = get_price(variant, futures=False)
                    
                    # Enhanced price validation
                    if not self._validate_price_data(spot_price):
                        validation_errors.append(f"{variant}: Invalid price {spot_price}")
                        continue

                    # Get comprehensive 24h ticker data
                    ticker_data = self._get_enhanced_ticker_data(variant)
                    
                    if ticker_data.get('error'):
                        validation_errors.append(f"{variant}: Ticker error - {ticker_data['error']}")
                        continue

                    # Cross-validate price consistency
                    ticker_price = ticker_data.get('price', 0)
                    price_diff_percent = abs((spot_price - ticker_price) / ticker_price * 100) if ticker_price > 0 else 0
                    
                    if price_diff_percent > 5.0:  # More than 5% difference is suspicious
                        validation_errors.append(f"{variant}: Price inconsistency {price_diff_percent:.2f}%")
                        continue

                    # Calculate accuracy score
                    accuracy_score = self._calculate_accuracy_score(ticker_data, spot_price)
                    
                    result = {
                        'symbol': symbol.upper().replace('USDT', '').replace('BUSD', '').replace('USDC', ''),
                        'price': spot_price,
                        'change_24h': ticker_data.get('change_24h', 0),
                        'volume_24h': ticker_data.get('volume_24h', 0),
                        'high_24h': ticker_data.get('high_24h', spot_price),
                        'low_24h': ticker_data.get('low_24h', spot_price),
                        'market_cap': self._calculate_enhanced_market_cap(symbol, spot_price),
                        'last_updated': datetime.now().isoformat(),
                        'source': 'binance_enhanced',
                        'pair_used': variant,
                        'accuracy_score': accuracy_score,
                        'validation_passed': True
                    }

                    # Keep the best result (highest accuracy score)
                    if not best_result or accuracy_score > best_result.get('accuracy_score', 0):
                        best_result = result

                except Exception as e:
                    validation_errors.append(f"{variant}: {str(e)}")
                    continue

            # Return best result if found
            if best_result:
                # Cache the result
                self._cache[cache_key] = (best_result, time.time())
                logging.info(f"✅ Enhanced price data for {symbol}: ${best_result['price']:.6f} (accuracy: {best_result['accuracy_score']:.1f}%)")
                return best_result

            # Enhanced error response with diagnostics
            available_symbols = self._get_available_symbols_sample()
            return {
                'error': f'No reliable data found for {symbol}',
                'symbol': symbol.upper(),
                'variants_tried': symbol_variants,
                'validation_errors': validation_errors,
                'diagnostics': {
                    'total_variants_tried': len(symbol_variants),
                    'validation_failures': len(validation_errors),
                    'suggested_alternatives': self._get_similar_symbols(symbol)
                },
                'available_coins': available_symbols
            }

        except Exception as e:
            logging.error(f"Critical error getting crypto price for {symbol}: {e}")
            return {'error': f'Critical system error for {symbol}: {str(e)}'}

    def _get_enhanced_symbol_variants(self, symbol: str) -> List[str]:
        """Generate enhanced symbol variants with intelligent priority ordering"""
        base = symbol.upper().strip()
        variants = []
        
        # Remove common suffixes
        clean_base = base.replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        
        # Priority 1: Most common USDT pairs
        variants.extend([
            f"{clean_base}USDT",
            f"{clean_base}BUSD", 
            f"{clean_base}USDC"
        ])
        
        # Priority 2: Major crypto pairs
        if clean_base not in ['BTC', 'ETH']:
            variants.extend([
                f"{clean_base}BTC",
                f"{clean_base}ETH"
            ])
        
        # Priority 3: Alternative stablecoins
        variants.extend([
            f"{clean_base}FDUSD",
            f"{clean_base}TUSD"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen and variant != clean_base:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants[:6]  # Limit to top 6 variants

    def _get_enhanced_ticker_data(self, symbol: str) -> Dict[str, Any]:
        """Get enhanced 24h ticker data with comprehensive validation"""
        try:
            from app.providers.binance_provider import _http, _base_url
            
            ticker_url = f"{_base_url(False)}/api/v3/ticker/24hr"
            response = _http.get(ticker_url, params={'symbol': symbol})
            
            if response.status_code != 200:
                return {'error': f'HTTP {response.status_code}'}
                
            ticker_data = response.json()
            
            # Enhanced data validation
            required_fields = ['lastPrice', 'priceChangePercent', 'volume', 'highPrice', 'lowPrice']
            for field in required_fields:
                if field not in ticker_data:
                    return {'error': f'Missing field: {field}'}
            
            # Convert and validate numeric data
            try:
                price = float(ticker_data['lastPrice'])
                change_24h = float(ticker_data['priceChangePercent'])
                volume = float(ticker_data['volume'])
                high_24h = float(ticker_data['highPrice'])
                low_24h = float(ticker_data['lowPrice'])
                
                # Sanity checks
                if not (low_24h <= price <= high_24h):
                    return {'error': f'Price {price} not within daily range [{low_24h}, {high_24h}]'}
                
                if volume < 0:
                    return {'error': f'Invalid volume: {volume}'}
                    
                # Calculate volume in USD
                volume_24h = volume * price
                
                return {
                    'price': price,
                    'change_24h': change_24h,
                    'volume_24h': volume_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'raw_volume': volume,
                    'count': int(ticker_data.get('count', 0)),  # Trade count
                    'openTime': ticker_data.get('openTime'),
                    'closeTime': ticker_data.get('closeTime')
                }
                
            except (ValueError, TypeError) as e:
                return {'error': f'Data conversion error: {e}'}
                
        except Exception as e:
            return {'error': f'Ticker request failed: {e}'}

    def _validate_price_data(self, price: Any) -> bool:
        """Validate price data with comprehensive checks"""
        try:
            # Type and value validation
            if not isinstance(price, (int, float)):
                return False
                
            price_float = float(price)
            
            # Range validation
            if price_float <= 0:
                return False
                
            # Reasonable range check (between 0.000001 and 10,000,000)
            if not (0.000001 <= price_float <= 10000000):
                return False
                
            # Check for NaN or infinite values
            if not (price_float == price_float):  # NaN check
                return False
                
            if price_float == float('inf') or price_float == float('-inf'):
                return False
                
            return True
            
        except (ValueError, TypeError, OverflowError):
            return False

    def _calculate_accuracy_score(self, ticker_data: Dict, spot_price: float) -> float:
        """Calculate accuracy score based on data quality metrics"""
        score = 100.0
        
        # Price consistency check
        ticker_price = ticker_data.get('price', 0)
        if ticker_price > 0:
            price_diff = abs((spot_price - ticker_price) / ticker_price * 100)
            score -= min(price_diff * 10, 50)  # Penalize up to 50 points for price inconsistency
        
        # Volume validation (higher volume = more reliable)
        volume = ticker_data.get('volume_24h', 0)
        if volume < 1000:  # Very low volume
            score -= 30
        elif volume < 10000:  # Low volume  
            score -= 15
        elif volume > 1000000:  # High volume bonus
            score += 5
        
        # Trade count validation
        trade_count = ticker_data.get('count', 0)
        if trade_count < 100:  # Very few trades
            score -= 20
        elif trade_count > 10000:  # Many trades bonus
            score += 5
        
        # Spread validation (high-low range)
        high = ticker_data.get('high_24h', 0)
        low = ticker_data.get('low_24h', 0)
        if high > 0 and low > 0:
            spread_percent = ((high - low) / low) * 100
            if spread_percent > 50:  # Extremely high volatility
                score -= 15
            elif spread_percent > 25:  # High volatility
                score -= 5
        
        return max(0.0, min(100.0, score))

    def _calculate_enhanced_market_cap(self, symbol: str, price: float) -> float:
        """Calculate enhanced market cap with updated supply data"""
        # Updated supply estimates with more accurate data
        supply_estimates = {
            'BTC': 19700000,    # ~19.7M BTC
            'ETH': 120300000,   # ~120.3M ETH  
            'BNB': 160000000,   # ~160M BNB
            'SOL': 580000000,   # ~580M SOL
            'XRP': 54000000000, # ~54B XRP (updated from 100B)
            'ADA': 35000000000, # ~35B ADA
            'DOT': 1300000000,  # ~1.3B DOT
            'MATIC': 10000000000, # ~10B MATIC
            'AVAX': 400000000,  # ~400M AVAX
            'UNI': 750000000,   # ~750M UNI
            'LINK': 1000000000, # ~1B LINK
            'LTC': 75000000,    # ~75M LTC
            'ATOM': 390000000,  # ~390M ATOM
            'ICP': 500000000,   # ~500M ICP
            'NEAR': 1100000000, # ~1.1B NEAR
            'APT': 1000000000,  # ~1B APT
            'FTM': 3200000000,  # ~3.2B FTM
            'ALGO': 10000000000, # ~10B ALGO
            'VET': 86000000000, # ~86B VET
            'FLOW': 1400000000  # ~1.4B FLOW
        }
        
        base_symbol = symbol.upper().replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        estimated_supply = supply_estimates.get(base_symbol, 1000000000)  # Default 1B tokens
        
        return price * estimated_supply

    def _get_similar_symbols(self, symbol: str) -> List[str]:
        """Get similar symbols for better error suggestions"""
        symbol_upper = symbol.upper()
        
        # Common symbol alternatives and corrections
        alternatives = {
            'BITCOIN': ['BTC'],
            'ETHEREUM': ['ETH'], 
            'BINANCE': ['BNB'],
            'SOLANA': ['SOL'],
            'RIPPLE': ['XRP'],
            'CARDANO': ['ADA'],
            'POLKADOT': ['DOT'],
            'POLYGON': ['MATIC'],
            'AVALANCHE': ['AVAX'],
            'UNISWAP': ['UNI'],
            'CHAINLINK': ['LINK'],
            'LITECOIN': ['LTC']
        }
        
        # Check if symbol is a full name
        for full_name, symbols in alternatives.items():
            if full_name in symbol_upper or symbol_upper in full_name:
                return symbols
                
        # Check for partial matches
        matches = []
        common_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI']
        for common in common_symbols:
            if common in symbol_upper or symbol_upper in common:
                matches.append(common)
                
        return matches[:3]  # Return top 3 matches

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures dari Binance
        """
        try:
            normalized_symbol = normalize_symbol(symbol)

            # Get futures price
            futures_price = get_price(normalized_symbol, futures=True)

            if futures_price <= 0:
                return {'error': f'Invalid futures data for {symbol}'}

            # Get futures 24h ticker
            try:
                from app.providers.binance_provider import _http, _base_url

                ticker_url = f"{_base_url(True)}/fapi/v1/ticker/24hr"
                response = _http.get(ticker_url, params={'symbol': normalized_symbol})
                ticker_data = response.json()

                change_24h = float(ticker_data.get('priceChangePercent', 0))
                volume_24h = float(ticker_data.get('volume', 0)) * futures_price

            except Exception as e:
                logging.warning(f"Could not get futures 24h stats for {symbol}: {e}")
                change_24h = 0
                volume_24h = 0

            return {
                'symbol': symbol.upper().replace('USDT', ''),
                'futures_price': futures_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'source': 'binance_futures',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"Error getting futures data for {symbol}: {e}")
            return {'error': f'Failed to get futures data for {symbol}: {str(e)}'}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Ultra-optimized market overview for concurrent users - cached and streamlined
        """
        try:
            # Check market-specific cache first
            market_cache_key = "market_overview_fast"
            if market_cache_key in self._cache:
                cached_data, timestamp = self._cache[market_cache_key]
                if (time.time() - timestamp) < self._market_cache_timeout:
                    logging.info("📦 Market overview cache hit")
                    return cached_data

            # Ultra-fast approach: Only get BTC and ETH for market estimation
            # This represents ~70% of total market cap but with 90% less API calls
            essential_symbols = ['BTC', 'ETH']  # Reduced from 10 to 2
            
            total_market_cap = 0
            total_volume_24h = 0
            total_change = 0
            successful_requests = 0

            for symbol in essential_symbols:
                try:
                    # Use cached data if available for speed
                    price_data = self.get_crypto_price(symbol, force_refresh=False)
                    if 'error' not in price_data:
                        total_market_cap += price_data.get('market_cap', 0)
                        total_volume_24h += price_data.get('volume_24h', 0)
                        total_change += price_data.get('change_24h', 0)
                        successful_requests += 1
                except Exception:
                    continue

            if successful_requests == 0:
                # Ultra-fast fallback with reasonable estimates
                result = {
                    'success': True,
                    'global_metrics': {
                        'total_market_cap': 2500000000000,  # $2.5T estimate
                        'total_volume_24h': 100000000000,   # $100B estimate
                        'market_cap_change_24h': 1.5,       # Neutral estimate
                        'btc_dominance': 58.5,
                        'eth_dominance': 14.2,
                        'active_cryptocurrencies': 9500,
                        'active_exchanges': 500
                    },
                    'timestamp': datetime.now().isoformat(),
                    'source': 'binance_fallback_estimates'
                }
                # Cache fallback too
                self._cache[market_cache_key] = (result, time.time())
                return result

            avg_change = total_change / successful_requests

            # Quick BTC dominance calculation
            btc_market_cap = 0
            if successful_requests > 0:
                # Get BTC market cap from our fetched data
                btc_data = None
                try:
                    btc_data = self.get_crypto_price('BTC', force_refresh=False)
                    if 'error' not in btc_data:
                        btc_market_cap = btc_data.get('market_cap', 0)
                except:
                    pass

            # Extrapolate total market from BTC+ETH (they represent ~70% of market)
            extrapolated_total_cap = total_market_cap * 1.43  # Scale up from 70% to 100%
            btc_dominance = (btc_market_cap / extrapolated_total_cap * 100) if btc_market_cap > 0 and extrapolated_total_cap > 0 else 58.5

            result = {
                'success': True,
                'global_metrics': {
                    'total_market_cap': extrapolated_total_cap,
                    'total_volume_24h': total_volume_24h * 1.5,  # Scale volume too
                    'market_cap_change_24h': avg_change,
                    'btc_dominance': btc_dominance,
                    'eth_dominance': 14.2,  # Reasonable estimate
                    'active_cryptocurrencies': 9500,
                    'active_exchanges': 500
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'binance_ultra_fast'
            }

            # Cache the result for other concurrent users
            self._cache[market_cache_key] = (result, time.time())
            logging.info(f"✅ Ultra-fast market overview generated and cached")
            
            return result

        except Exception as e:
            logging.error(f"Error in ultra-fast market overview: {e}")
            # Return cached data if available, even if expired
            if market_cache_key in self._cache:
                cached_data, _ = self._cache[market_cache_key]
                logging.info("📦 Using stale cache due to error")
                return cached_data
                
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto (data terbatas dari Binance)
        """
        try:
            # Get basic price data
            price_data = self.get_crypto_price(symbol, force_refresh=True)

            if 'error' in price_data:
                return price_data

            # Return basic info (Binance doesn't provide detailed coin info)
            return {
                'symbol': symbol.upper().replace('USDT', ''),
                'name': self._get_coin_name(symbol),
                'description': f'Trading data for {symbol} from Binance',
                'price': price_data.get('price', 0),
                'change_24h': price_data.get('change_24h', 0),
                'volume_24h': price_data.get('volume_24h', 0),
                'market_cap': price_data.get('market_cap', 0),
                'source': 'binance_basic_info',
                'timestamp': datetime.now().isoformat(),
                'success': True
            }

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def _get_symbol_variants(self, symbol: str) -> List[str]:
        """Generate multiple symbol variants to try"""
        base = symbol.upper().strip()
        variants = []
        
        # Remove common suffixes first
        clean_base = base.replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        
        # Special symbol mappings for coins with different symbols on Binance
        # Note: ASTER and ASTR are different cryptocurrencies
        symbol_mappings = {
            # Add other legitimate mappings here if needed
        }
        
        # Apply symbol mapping if needed
        mapped_base = symbol_mappings.get(clean_base, clean_base)
        
        # Add variants in order of likelihood
        variants.extend([
            f"{clean_base}USDT",     # Most common - use original symbol
            f"{clean_base}BUSD",     # Alternative stablecoin  
            f"{clean_base}USDC",     # Another stablecoin
            f"{clean_base}BTC",      # BTC pair
            f"{clean_base}ETH",      # ETH pair
            clean_base,              # Original without pair
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants[:8]  # Limit to 8 attempts

    def _get_available_symbols_sample(self) -> List[str]:
        """Get a sample of available symbols"""
        try:
            from app.providers.binance_provider import exchange_info
            
            # Get exchange info
            info = exchange_info()
            symbols = []
            
            if 'symbols' in info:
                # Extract base assets from active USDT pairs
                for symbol_info in info['symbols'][:50]:  # Limit to first 50
                    if (symbol_info.get('status') == 'TRADING' and 
                        symbol_info.get('symbol', '').endswith('USDT')):
                        base = symbol_info['symbol'].replace('USDT', '')
                        if len(base) <= 6:  # Reasonable length
                            symbols.append(base)
                
                return symbols[:20]  # Return top 20
            
        except Exception as e:
            logging.warning(f"Could not get exchange symbols: {e}")
        
        # Fallback list
        return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI', 
                'LINK', 'LTC', 'ATOM', 'ICP', 'NEAR', 'APT', 'FTM', 'ALGO', 'VET', 'FLOW']

    def _get_coin_name(self, symbol: str) -> str:
        """Get coin name mapping"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum', 
            'BNB': 'BNB',
            'SOL': 'Solana',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'DOT': 'Polkadot',
            'MATIC': 'Polygon',
            'AVAX': 'Avalanche',
            'UNI': 'Uniswap',
            'ASTER': 'Aster Token',  # Different from ASTR
            'ASTAR': 'Astar Network',
            'ASTR': 'Astar Network'
        }
        return names.get(symbol.upper().replace('USDT', ''), symbol.upper())

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke Binance API
        """
        results = {}

        try:
            # Test Binance Spot
            btc_price = get_price('BTCUSDT', futures=False)
            success = isinstance(btc_price, (int, float)) and btc_price > 0
            results['Binance Spot'] = {
                'success': success, 
                'error': None if success else 'Invalid price returned',
                'sample_price': btc_price if success else None
            }
        except Exception as e:
            results['Binance Spot'] = {'success': False, 'error': str(e)}

        try:
            # Test Binance Futures  
            btc_futures_price = get_price('BTCUSDT', futures=True)
            success = isinstance(btc_futures_price, (int, float)) and btc_futures_price > 0
            results['Binance Futures'] = {
                'success': success,
                'error': None if success else 'Invalid futures price returned',
                'sample_price': btc_futures_price if success else None
            }
        except Exception as e:
            results['Binance Futures'] = {'success': False, 'error': str(e)}

        # Overall status
        successful_apis = sum(1 for result in results.values() if result.get('success'))
        total_apis = len(results)

        overall_status = 'excellent' if successful_apis == total_apis else 'good' if successful_apis > 0 else 'poor'

        return {
            'timestamp': datetime.now().isoformat(),
            'apis': results,
            'overall_status': overall_status,
            'working_apis': successful_apis,
            'total_apis': total_apis,
            'provider': 'binance_only'
        }

# Global instance
crypto_api = CryptoAPI()