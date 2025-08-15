import requests
import os
import httpx
from typing import Dict, Any, List, Optional

class BinanceProvider:
    def __init__(self):
        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_API_SECRET")
        self.base_url = "https://api.binance.com"
        self.client = httpx.Client(headers={"X-MBX-APIKEY": self.api_key})

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker price for a given symbol."""
        try:
            response = self.client.get(f"{self.base_url}/api/v3/ticker/price", params={"symbol": symbol})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return {}
        except httpx.RequestError as e:
            print(f"Request error fetching ticker for {symbol}: {e}")
            return {}

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            # Note: Requires authenticated requests, typically using a signed endpoint
            # This is a simplified example and might need proper signature generation
            response = self.client.get(f"{self.base_url}/api/v3/account")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching account info: {e}")
            return {}
        except httpx.RequestError as e:
            print(f"Request error fetching account info: {e}")
            return {}

    def get_historical_klines(self, symbol: str, interval: str, start_str: str, end_str: str = None) -> List[List[Any]]:
        """
        Get historical klines data for a given symbol, interval, and time range.
        interval: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        start_str: Start time in milliseconds or 'yyyy-MM-dd HH:mm:ss'
        end_str: End time in milliseconds or 'yyyy-MM-dd HH:mm:ss'
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_str,
            "limit": 1000  # Max limit is 1000
        }
        if end_str:
            params["endTime"] = end_str

        klines = []
        try:
            while True:
                response = self.client.get(f"{self.base_url}/api/v3/klines", params=params)
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                klines.extend(data)
                # Prepare for next request: use the timestamp of the last kline as the new start time
                params["startTime"] = data[-1][0] + 1 # Add 1 millisecond to avoid duplicate
                if end_str and params["startTime"] > int(end_str):
                    break
                if len(data) < 1000: # If fewer than limit, it's the last batch
                    break
        except httpx.HTTPStatusError as e:
            print(f"Error fetching historical klines for {symbol}: {e}")
            return []
        except httpx.RequestError as e:
            print(f"Request error fetching historical klines for {symbol}: {e}")
            return []
        return klines


class AnalysisService:
    def __init__(self, binance_provider: BinanceProvider):
        self.binance_provider = binance_provider

    def get_ohlcv(self, symbol: str, interval: str, days: int) -> List[Dict[str, Any]]:
        """
        Fetches OHLCV data for a given symbol, interval, and number of past days.
        Converts the Binance API response format into a list of dictionaries.
        """
        end_time_ms = int(httpx.request("GET", "https://api.binance.com").elapsed.total_seconds() * 1000) # Placeholder for current time
        start_time_ms = end_time_ms - (days * 24 * 60 * 60 * 1000)

        klines = self.binance_provider.get_historical_klines(
            symbol,
            interval,
            start_time_ms,
            end_time_ms
        )

        ohlcv_data = []
        for kline in klines:
            ohlcv_data.append({
                "timestamp": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
            })
        return ohlcv_data


class AI_Assistant:
    def __init__(self):
        self.analysis_service = None # Will be set by the main application

    def set_analysis_service(self, analysis_service: AnalysisService):
        self.analysis_service = analysis_service

    def generate_futures_signals(self, top_coins: List[str], confidence_threshold: float = 0.75) -> List[Dict[str, Any]]:
        """
        Generates futures trading signals for a list of top coins.
        Analyzes the last 1 day of 1-hour interval data.
        """
        signals = []
        for coin in top_coins:
            try:
                ohlcv_data = self.analysis_service.get_ohlcv(coin, "1h", 1)

                if not ohlcv_data:
                    print(f"No OHLCV data for {coin}")
                    continue

                # Simple example logic: if the last closing price is significantly higher than the opening price
                # This is a placeholder for actual sophisticated AI analysis
                latest_data = ohlcv_data[-1]
                if latest_data["close"] > latest_data["open"] * 1.05: # Example: 5% increase
                    confidence = 0.80 # Placeholder confidence
                    if confidence >= confidence_threshold:
                        signals.append({
                            "symbol": coin,
                            "signal": "BUY",
                            "confidence": confidence,
                            "price": latest_data["close"]
                        })
                elif latest_data["close"] < latest_data["open"] * 0.95: # Example: 5% decrease
                    confidence = 0.80 # Placeholder confidence
                    if confidence >= confidence_threshold:
                        signals.append({
                            "symbol": coin,
                            "signal": "SELL",
                            "confidence": confidence,
                            "price": latest_data["close"]
                        })
            except Exception as e:
                print(f"Error generating signal for {coin}: {e}")
        return signals

if __name__ == "__main__":
    # Example Usage
    binance_provider = BinanceProvider()
    analysis_service = AnalysisService(binance_provider)
    ai_assistant = AI_Assistant()
    ai_assistant.set_analysis_service(analysis_service)

    # Get top 30 coins by volume (this is a placeholder, actual implementation might involve fetching this list)
    top_30_coins = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "DOTUSDT",
        "MATICUSDT", "LINKUSDT", "TRXUSDT", "LTCUSDT", "UNIUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT",
        "VETUSDT", "XLMUSDT", "THETAUSDT", "AAVEUSDT", "ICPUSDT", "MANAUSDT", "LDOUSDT", "EOSUSDT",
        "FILUSDT", "CAKEUSDT", "XTZUSDT", "BNXUSDT", "KCSUSDT", "SUSHIUSDT"
    ]

    # Mocking get_historical_klines to return dummy data for demonstration
    # In a real scenario, you'd remove this mocking and use the actual Binance API calls.
    def mock_get_historical_klines(self, symbol: str, interval: str, start_str: str, end_str: str = None) -> List[List[Any]]:
        print(f"Mocking get_historical_klines for {symbol} with interval {interval}")
        # Dummy data simulating a price increase
        now = int(httpx.request("GET", "https://api.binance.com").elapsed.total_seconds() * 1000)
        dummy_klines = []
        for i in range(24): # 24 hours of data
            timestamp = now - (24 - i) * 3600 * 1000
            open_price = 10000 + i * 10
            close_price = open_price + 50 + (i % 5) * 5 # Simulate some fluctuation
            high_price = close_price + 5
            low_price = open_price - 5
            volume = 1000 + i * 100
            dummy_klines.append([timestamp, str(open_price), str(high_price), str(low_price), str(close_price), str(volume), timestamp + 3599000, str(volume), 100, str(volume * 0.1), str(volume * 0.1)])
        return dummy_klines

    BinanceProvider.get_historical_klines = mock_get_historical_klines


    signals = ai_assistant.generate_futures_signals(top_30_coins)

    print("\n--- Generated Futures Signals ---")
    if signals:
        for signal in signals:
            print(f"Symbol: {signal['symbol']}, Signal: {signal['signal']}, Confidence: {signal['confidence']:.2f}, Price: {signal['price']}")
    else:
        print("No signals generated.")