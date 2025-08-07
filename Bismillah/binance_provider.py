import requests
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from config import get_binance_headers, BINANCE_ENDPOINTS

class BinanceFuturesProvider:
    def __init__(self):
        self.futures_base_url = "https://fapi.binance.com/fapi/v1"
        self.spot_base_url = "https://api.binance.com/api/v3"

    def get_tickers(self) -> List[str]:
        """Get list of all available USDT-margined futures symbols"""
        url = f"{self.futures_base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [
                symbol['symbol']
                for symbol in data['symbols']
                if symbol['contractType'] == 'PERPETUAL' and symbol['quoteAsset'] == 'USDT'
            ]
        except Exception as e:
            logging.error(f"Error fetching Binance tickers: {e}")
            return []

    def get_spot_tickers(self) -> List[str]:
        """Get list of all available spot trading symbols"""
        url = f"{self.spot_base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [
                symbol['symbol']
                for symbol in data['symbols']
                if symbol['status'] == 'TRADING' and symbol['quoteAsset'] == 'USDT'
            ]
        except Exception as e:
            logging.error(f"Error fetching Binance spot tickers: {e}")
            return []

    def get_futures_exchange_info(self):
        """Get futures exchange information"""
        url = f"{self.futures_base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching futures exchange info: {e}")
            return {}

    def get_spot_exchange_info(self):
        """Get spot exchange information"""
        url = f"{self.spot_base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching spot exchange info: {e}")
            return {}

    def ping_futures(self):
        """Test Binance Futures connectivity"""
        url = f"{self.futures_base_url}/ping"
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Futures ping failed: {e}")
            return False

    def ping_spot(self):
        """Test Binance Spot connectivity"""
        url = f"{self.spot_base_url}/ping"
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Spot ping failed: {e}")
            return False

    def get_server_time(self):
        """Get Binance server time"""
        url = f"{self.spot_base_url}/time"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            server_time = data['serverTime']
            dt = datetime.fromtimestamp(server_time / 1000, tz=timezone.utc)

            return {
                'server_time_ms': server_time,
                'server_time_iso': dt.isoformat(),
                'server_time_readable': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'local_time_ms': int(datetime.now().timestamp() * 1000),
                'time_diff_ms': server_time - int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            logging.error(f"Error getting server time: {e}")
            return {}

    def get_all_futures_symbols(self):
        """Get comprehensive list of futures symbols with details"""
        url = f"{self.futures_base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            symbols_info = []
            for symbol in data['symbols']:
                if symbol['contractType'] == 'PERPETUAL' and symbol['quoteAsset'] == 'USDT':
                    symbols_info.append({
                        'symbol': symbol['symbol'],
                        'base_asset': symbol['baseAsset'],
                        'quote_asset': symbol['quoteAsset'],
                        'status': symbol['status'],
                        'contract_type': symbol['contractType'],
                        'delivery_date': symbol.get('deliveryDate'),
                        'onboard_date': symbol.get('onboardDate'),
                        'maintenance_margin_percent': symbol.get('maintMarginPercent'),
                        'required_margin_percent': symbol.get('requiredMarginPercent'),
                        'price_precision': symbol.get('pricePrecision'),
                        'quantity_precision': symbol.get('quantityPrecision')
                    })

            return symbols_info
        except Exception as e:
            logging.error(f"Error fetching detailed futures symbols: {e}")
            return []

    def check_symbol_validity(self, symbol):
        """Check if a symbol is valid for futures trading"""
        valid_symbols = self.get_tickers()
        normalized_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
        return normalized_symbol in valid_symbols

    def get_symbol_info(self, symbol):
        """Get detailed information about a specific symbol"""
        exchange_info = self.get_futures_exchange_info()
        symbols = exchange_info.get('symbols', [])

        normalized_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()

        for sym in symbols:
            if sym['symbol'] == normalized_symbol:
                return sym

        return None