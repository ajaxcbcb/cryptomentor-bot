"""
Alternative Klines Provider
Menggunakan Bitunix, CryptoCompare, dan CoinGecko sebagai sumber data OHLCV.
Prioritas: Bitunix (exchange utama) → CryptoCompare → CoinGecko
"""
import os
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class AlternativeKlinesProvider:
    """Provider OHLCV data dengan fallback multi-source"""
    
    def __init__(self):
        self.bitunix_api      = os.getenv('BITUNIX_BASE_URL', 'https://fapi.bitunix.com')
        self.coingecko_api    = "https://api.coingecko.com/api/v3"
        self.cryptocompare_api = "https://min-api.cryptocompare.com/data/v2"
        self.cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
        
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List:
        """
        Get OHLCV data — prioritas Bitunix, fallback ke CryptoCompare/CoinGecko.
        Returns list of klines in Binance format: [timestamp, open, high, low, close, volume, ...]
        """
        clean_symbol = symbol.upper().replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        full_symbol  = clean_symbol + "USDT"

        # 1. Bitunix (prioritas utama — data futures langsung)
        klines = self._get_from_bitunix(full_symbol, interval, limit)
        if klines:
            return klines

        # 2. CryptoCompare
        if self.cryptocompare_key:
            klines = self._get_from_cryptocompare(clean_symbol, interval, limit)
            if klines:
                print(f"✅ Got {len(klines)} candles from CryptoCompare for {symbol}")
                return klines

        # 3. CoinGecko
        klines = self._get_from_coingecko(clean_symbol, interval, limit)
        if klines:
            print(f"✅ Got {len(klines)} candles from CoinGecko for {symbol}")
            return klines

        print(f"❌ Failed to get klines for {symbol} from all sources")
        return []

    def _get_from_bitunix(self, symbol: str, interval: str, limit: int) -> List:
        """Get OHLCV dari Bitunix futures API — tidak perlu auth, public endpoint."""
        try:
            # Bitunix interval mapping (sudah sama dengan standar)
            # Supported: 1m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h',
                '8h': '8h', '12h': '12h', '1d': '1d', '1w': '1w',
            }
            bx_interval = interval_map.get(interval)
            if not bx_interval:
                return []

            # Bitunix max limit per request = 200
            fetch_limit = min(limit, 200)

            url = f"{self.bitunix_api}/api/v1/futures/market/kline"
            params = {
                'symbol':   symbol,
                'interval': bx_interval,
                'limit':    fetch_limit,
            }

            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return []

            data = resp.json()
            if data.get('code') != 0 or not data.get('data'):
                return []

            raw = data['data']
            # Bitunix response: [{open, high, low, close, time, quoteVol, baseVol, type}, ...]
            # Sort ascending by time
            raw.sort(key=lambda x: x.get('time', 0))

            klines = []
            for c in raw:
                ts     = int(c.get('time', 0))
                open_  = str(c.get('open', 0))
                high   = str(c.get('high', 0))
                low    = str(c.get('low', 0))
                close  = str(c.get('close', 0))
                vol    = str(c.get('baseVol', 0))   # coin volume
                qvol   = str(c.get('quoteVol', 0))  # USDT volume
                klines.append([
                    ts, open_, high, low, close, vol,
                    ts + 1, qvol, 0, "0", "0", "0"
                ])

            if len(klines) >= 10:
                print(f"✅ Got {len(klines)} candles from Bitunix for {symbol}")
                return klines

            return []

        except Exception as e:
            print(f"Bitunix klines error ({symbol}): {e}")
            return []
    
    def _get_from_cryptocompare(self, symbol: str, interval: str, limit: int) -> List:
        """Get OHLCV from CryptoCompare"""
        try:
            # Map interval to CryptoCompare format
            interval_map = {
                '1h': ('histohour', 1),
                '4h': ('histohour', 4),
                '1d': ('histoday', 1),
                '15m': ('histominute', 15),
                '30m': ('histominute', 30)
            }
            
            if interval not in interval_map:
                return []
            
            endpoint, aggregate = interval_map[interval]
            
            url = f"{self.cryptocompare_api}/{endpoint}"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': limit,
                'aggregate': aggregate
            }
            
            if self.cryptocompare_key:
                params['api_key'] = self.cryptocompare_key
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('Response') == 'Success' and 'Data' in data:
                    ohlcv_data = data['Data'].get('Data', [])
                    
                    # Convert to Binance format
                    klines = []
                    for candle in ohlcv_data:
                        # Binance format: [timestamp, open, high, low, close, volume, close_time, ...]
                        klines.append([
                            candle['time'] * 1000,  # timestamp in ms
                            str(candle['open']),
                            str(candle['high']),
                            str(candle['low']),
                            str(candle['close']),
                            str(candle['volumefrom']),
                            candle['time'] * 1000 + 3600000,  # close_time (approx)
                            str(candle['volumeto']),
                            0,  # number of trades (not available)
                            "0",  # taker buy base asset volume
                            "0",  # taker buy quote asset volume
                            "0"   # ignore
                        ])
                    
                    return klines
            
            return []
        
        except Exception as e:
            print(f"CryptoCompare error: {e}")
            return []
    
    def _get_from_coingecko(self, symbol: str, interval: str, limit: int) -> List:
        """Get OHLCV from CoinGecko"""
        try:
            # Map symbol to CoinGecko ID
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'MATIC': 'matic-network',
                'AVAX': 'avalanche-2',
                'UNI': 'uniswap',
                'LINK': 'chainlink',
                'LTC': 'litecoin',
                'ATOM': 'cosmos',
                'ICP': 'internet-computer',
                'NEAR': 'near',
                'APT': 'aptos',
                'FTM': 'fantom',
                'ALGO': 'algorand',
                'VET': 'vechain',
                'FLOW': 'flow'
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                return []
            
            # Calculate days based on interval and limit
            interval_hours = {
                '1h': 1,
                '4h': 4,
                '1d': 24,
                '15m': 0.25,
                '30m': 0.5
            }
            
            hours = interval_hours.get(interval, 1)
            days = max(1, int((limit * hours) / 24))
            
            url = f"{self.coingecko_api}/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': min(days, 90)  # CoinGecko limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                ohlc_data = response.json()
                
                if isinstance(ohlc_data, list) and len(ohlc_data) > 0:
                    # Convert to Binance format
                    klines = []
                    for candle in ohlc_data[-limit:]:  # Get last 'limit' candles
                        # CoinGecko format: [timestamp, open, high, low, close]
                        timestamp = candle[0]
                        open_price = candle[1]
                        high_price = candle[2]
                        low_price = candle[3]
                        close_price = candle[4]
                        
                        # Estimate volume (not provided by CoinGecko OHLC)
                        volume = (high_price + low_price) / 2 * 1000  # Rough estimate
                        
                        klines.append([
                            timestamp,
                            str(open_price),
                            str(high_price),
                            str(low_price),
                            str(close_price),
                            str(volume),
                            timestamp + 3600000,  # close_time
                            str(volume * close_price),
                            0,
                            "0",
                            "0",
                            "0"
                        ])
                    
                    return klines
            
            return []
        
        except Exception as e:
            print(f"CoinGecko error: {e}")
            return []

# Global instance
alternative_klines_provider = AlternativeKlinesProvider()
