"""
Crypto API Module - Provides cryptocurrency market data
"""

try:
    from app.simple_crypto_api import SimpleCryptoAPI
except ImportError:
    try:
        from app.multi_crypto_api import MultiCryptoAPI as SimpleCryptoAPI
    except ImportError:
        # Fallback implementation
        class SimpleCryptoAPI:
            def get_crypto_price(self, symbol, force_refresh=False):
                return {"error": "Crypto API not available"}

# Create global instance
crypto_api = SimpleCryptoAPI()

def get_crypto_price(symbol, force_refresh=False):
    """Get cryptocurrency price data"""
    return crypto_api.get_crypto_price(symbol, force_refresh)

def get_market_data(symbols=None):
    """Get market data for multiple symbols"""
    if symbols is None:
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
    
    market_data = {}
    for symbol in symbols:
        try:
            data = crypto_api.get_crypto_price(symbol)
            if 'error' not in data:
                market_data[symbol] = data
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
    
    return market_data

class CryptoAPI:
    """Crypto API class for compatibility"""
    
    def __init__(self):
        self.api = SimpleCryptoAPI()
    
    def get_crypto_price(self, symbol, force_refresh=False):
        return self.api.get_crypto_price(symbol, force_refresh)
    
    def get_market_overview(self):
        return get_market_data()
