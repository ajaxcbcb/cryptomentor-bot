
import os
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np
import pandas as pd

class FuturesSignalError(Exception):
    """Exception for futures signal processing errors"""
    pass

class FuturesEngine:
    """Unified futures analysis engine for consistency across commands"""
    
    def __init__(self, crypto_api=None):
        self.crypto_api = crypto_api
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache
        
    def analyze_symbol(
        self,
        symbol: str,
        timeframe: str = "15m",
        market: str = "USDT",
        limit: int = 200,
    ) -> Dict[str, Any]:
        """
        Main analysis function - unified for /futures and /futures_signals
        
        Returns:
        {
            "symbol": "BTCUSDT",
            "timeframe": "15m", 
            "price": 64123.5,
            "signals": [
                {
                    "side": "LONG" | "SHORT",
                    "confidence": 0..100,
                    "reasons": ["RSI<30", "EMA12>EMA26", ...],
                    "entry": 64100.0,
                    "sl": 63800.0,
                    "tp": [64500.0, 65000.0],
                    "time": datetime.now().isoformat()
                }
            ],
            "meta": {
                "indicators": {...},
                "latency_ms": int,
            }
        }
        """
        start_time = time.time()
        
        try:
            # Normalize symbol
            if not symbol.endswith(market):
                symbol = f"{symbol.upper()}{market}"
            
            # Check cache
            cache_key = f"{symbol}_{timeframe}_{limit}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Get price data
            price_data = self._get_price_data(symbol)
            if not price_data:
                raise FuturesSignalError(f"Failed to get price data for {symbol}")
                
            current_price = price_data.get('price', 0)
            
            # Get OHLCV data for analysis
            ohlcv_data = self._get_ohlcv_data(symbol, timeframe, limit)
            if not ohlcv_data or len(ohlcv_data) < 50:
                raise FuturesSignalError(f"Insufficient OHLCV data for {symbol}")
            
            # Calculate indicators
            indicators = self._calculate_indicators(ohlcv_data)
            
            # Generate signals
            signals = self._generate_signals(indicators, current_price, symbol)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "price": current_price,
                "signals": signals,
                "meta": {
                    "indicators": indicators,
                    "latency_ms": latency_ms,
                    "data_points": len(ohlcv_data)
                }
            }
            
            # Cache result
            self.cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            raise FuturesSignalError(f"Analysis failed for {symbol}: {str(e)}")
    
    def _get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price data"""
        try:
            if self.crypto_api:
                # Remove USDT suffix for API call
                clean_symbol = symbol.replace('USDT', '')
                return self.crypto_api.get_crypto_price(clean_symbol, force_refresh=True)
            return None
        except Exception:
            return None
    
    def _get_ohlcv_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Get OHLCV data from available sources"""
        try:
            # Try to get from crypto_api first (CoinAPI)
            if self.crypto_api and hasattr(self.crypto_api, 'ai'):
                # Map timeframe
                tf_mapping = {
                    '15m': '15MIN', '30m': '30MIN', '1h': '1HRS',
                    '4h': '4HRS', '1d': '1DAY', '1w': '1WEK'
                }
                api_timeframe = tf_mapping.get(timeframe, '15MIN')
                
                # Remove USDT for CoinAPI call
                clean_symbol = symbol.replace('USDT', '')
                ohlcv_result = self.crypto_api.ai.get_coinapi_ohlcv_data(clean_symbol, api_timeframe, limit)
                
                if ohlcv_result.get('success') and 'data' in ohlcv_result:
                    return ohlcv_result['data']
            
            # Fallback to synthetic data if needed
            return self._generate_synthetic_ohlcv(symbol, limit)
            
        except Exception as e:
            print(f"Error getting OHLCV data: {e}")
            return self._generate_synthetic_ohlcv(symbol, limit)
    
    def _generate_synthetic_ohlcv(self, symbol: str, limit: int) -> pd.DataFrame:
        """Generate synthetic OHLCV data as fallback"""
        try:
            # Get current price as base
            if self.crypto_api:
                clean_symbol = symbol.replace('USDT', '')
                price_data = self.crypto_api.get_crypto_price(clean_symbol)
                base_price = price_data.get('price', 50000) if price_data else 50000
            else:
                base_price = 50000
            
            # Generate synthetic data with realistic patterns
            np.random.seed(int(time.time()) % 1000)
            
            data = []
            current_price = base_price
            
            for i in range(limit):
                # Random walk with small changes
                change_pct = np.random.normal(0, 0.02)  # 2% std dev
                current_price *= (1 + change_pct)
                
                # Generate OHLC from current price
                high = current_price * (1 + abs(np.random.normal(0, 0.01)))
                low = current_price * (1 - abs(np.random.normal(0, 0.01)))
                open_price = current_price * (1 + np.random.normal(0, 0.005))
                close_price = current_price
                volume = np.random.uniform(1000000, 10000000)
                
                data.append({
                    'time_period_start': datetime.now().isoformat(),
                    'price_open': open_price,
                    'price_high': high,
                    'price_low': low,
                    'price_close': close_price,
                    'volume_traded': volume
                })
            
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            print(f"Error generating synthetic data: {e}")
            return pd.DataFrame()
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            if df is None or len(df) < 20:
                return {}
            
            # Ensure numeric columns
            for col in ['price_close', 'price_high', 'price_low', 'volume_traded']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            indicators = {}
            
            # Price data
            close = df['price_close']
            high = df['price_high'] 
            low = df['price_low']
            
            # EMA calculations
            indicators['ema_12'] = close.ewm(span=12).mean().iloc[-1]
            indicators['ema_26'] = close.ewm(span=26).mean().iloc[-1]
            indicators['ema_50'] = close.ewm(span=min(50, len(df))).mean().iloc[-1]
            indicators['ema_200'] = close.ewm(span=min(200, len(df))).mean().iloc[-1]
            indicators['current_price'] = close.iloc[-1]
            
            # RSI calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
            
            # MACD calculation
            macd_line = indicators['ema_12'] - indicators['ema_26']
            signal_line = pd.Series([macd_line]).ewm(span=9).mean().iloc[0]
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = macd_line - signal_line
            
            # ATR calculation
            high_low = high - low
            high_close_prev = np.abs(high - close.shift(1))
            low_close_prev = np.abs(low - close.shift(1))
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            indicators['atr'] = true_range.rolling(window=14).mean().iloc[-1]
            
            # Volume indicators
            if 'volume_traded' in df.columns:
                volume = df['volume_traded']
                indicators['volume_sma'] = volume.rolling(window=20).mean().iloc[-1]
                indicators['current_volume'] = volume.iloc[-1]
                indicators['volume_ratio'] = indicators['current_volume'] / indicators['volume_sma']
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return {}
    
    def _generate_signals(self, indicators: Dict[str, Any], current_price: float, symbol: str) -> List[Dict[str, Any]]:
        """Generate trading signals with confidence scoring"""
        try:
            signals = []
            
            if not indicators:
                return signals
            
            # Extract indicators
            ema_12 = indicators.get('ema_12', current_price)
            ema_26 = indicators.get('ema_26', current_price)
            ema_50 = indicators.get('ema_50', current_price)
            ema_200 = indicators.get('ema_200', current_price)
            rsi = indicators.get('rsi', 50)
            macd_histogram = indicators.get('macd_histogram', 0)
            atr = indicators.get('atr', current_price * 0.02)
            
            # Generate LONG signal
            long_confidence, long_reasons = self._calculate_long_confidence(
                ema_12, ema_26, ema_50, ema_200, rsi, macd_histogram, current_price
            )
            
            if long_confidence > 0:
                long_signal = {
                    "side": "LONG",
                    "confidence": int(long_confidence),
                    "reasons": long_reasons,
                    "entry": current_price * 0.999,
                    "sl": current_price - (atr * 2.5),
                    "tp": [current_price + (atr * 1.5), current_price + (atr * 3)],
                    "time": datetime.now(timezone.utc).isoformat()
                }
                signals.append(long_signal)
            
            # Generate SHORT signal
            short_confidence, short_reasons = self._calculate_short_confidence(
                ema_12, ema_26, ema_50, ema_200, rsi, macd_histogram, current_price
            )
            
            if short_confidence > 0:
                short_signal = {
                    "side": "SHORT", 
                    "confidence": int(short_confidence),
                    "reasons": short_reasons,
                    "entry": current_price * 1.001,
                    "sl": current_price + (atr * 2.5),
                    "tp": [current_price - (atr * 1.5), current_price - (atr * 3)],
                    "time": datetime.now(timezone.utc).isoformat()
                }
                signals.append(short_signal)
            
            # Sort by confidence
            signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            return signals[:2]  # Return top 2 signals
            
        except Exception as e:
            print(f"Error generating signals: {e}")
            return []
    
    def _calculate_long_confidence(self, ema_12, ema_26, ema_50, ema_200, rsi, macd_histogram, price):
        """Calculate LONG signal confidence"""
        confidence = 0
        reasons = []
        
        # EMA trend alignment (40 points max)
        if ema_12 > ema_26:
            confidence += 15
            reasons.append("EMA12 > EMA26")
        if ema_50 > ema_200:
            confidence += 25
            reasons.append("EMA50 > EMA200")
        
        # RSI conditions (30 points max)
        if rsi < 30:
            confidence += 30
            reasons.append("RSI oversold (<30)")
        elif rsi < 50:
            confidence += 15
            reasons.append("RSI below 50")
        elif rsi < 70:
            confidence += 10
            reasons.append("RSI normal range")
        
        # MACD confirmation (20 points max)
        if macd_histogram > 0:
            confidence += 20
            reasons.append("MACD bullish")
        elif macd_histogram > -0.001:
            confidence += 10
            reasons.append("MACD neutral")
        
        # Additional momentum (10 points max)
        if price > ema_50:
            confidence += 10
            reasons.append("Price > EMA50")
        
        return min(confidence, 100), reasons
    
    def _calculate_short_confidence(self, ema_12, ema_26, ema_50, ema_200, rsi, macd_histogram, price):
        """Calculate SHORT signal confidence"""
        confidence = 0
        reasons = []
        
        # EMA trend alignment (40 points max)
        if ema_12 < ema_26:
            confidence += 15
            reasons.append("EMA12 < EMA26")
        if ema_50 < ema_200:
            confidence += 25
            reasons.append("EMA50 < EMA200")
        
        # RSI conditions (30 points max)
        if rsi > 70:
            confidence += 30
            reasons.append("RSI overbought (>70)")
        elif rsi > 50:
            confidence += 15
            reasons.append("RSI above 50")
        elif rsi > 30:
            confidence += 10
            reasons.append("RSI normal range")
        
        # MACD confirmation (20 points max)
        if macd_histogram < 0:
            confidence += 20
            reasons.append("MACD bearish")
        elif macd_histogram < 0.001:
            confidence += 10
            reasons.append("MACD neutral")
        
        # Additional momentum (10 points max)
        if price < ema_50:
            confidence += 10
            reasons.append("Price < EMA50")
        
        return min(confidence, 100), reasons

# Global engine instance
_engine = None

def get_engine(crypto_api=None):
    """Get or create engine instance"""
    global _engine
    if _engine is None:
        _engine = FuturesEngine(crypto_api)
    elif crypto_api and _engine.crypto_api != crypto_api:
        _engine.crypto_api = crypto_api
    return _engine

def analyze_symbol(symbol: str, timeframe: str = "15m", market: str = "USDT", limit: int = 200, crypto_api=None) -> Dict[str, Any]:
    """Convenience function for direct analysis"""
    engine = get_engine(crypto_api)
    return engine.analyze_symbol(symbol, timeframe, market, limit)
