
from typing import Dict, Any, List
import asyncio
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.utils.async_tools import gather_safe
except ImportError:
    # Fallback implementation if utils not available
    async def gather_safe(tasks):
        return await asyncio.gather(*tasks, return_exceptions=True)

def _trend_label(df: pd.DataFrame) -> str:
    """Determine trend from EMA crossover"""
    try:
        if len(df) < 200:
            # Use shorter EMAs for limited data
            e20 = df["close"].ewm(span=20).mean()
            e50 = df["close"].ewm(span=min(50, len(df))).mean()
        else:
            e50 = df["close"].ewm(span=50).mean()
            e200 = df["close"].ewm(span=200).mean()
            
        if len(df) < 200:
            if e20.iloc[-1] > e50.iloc[-1]:
                return "up"
            elif e20.iloc[-1] < e50.iloc[-1]:
                return "down"
        else:
            if e50.iloc[-1] > e200.iloc[-1]:
                return "up"
            elif e50.iloc[-1] < e200.iloc[-1]:
                return "down"
        return "sideways"
    except:
        return "sideways"

def _calculate_rsi(series, period=14):
    """Calculate RSI"""
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([50] * len(series), index=series.index)

def _calculate_macd(series):
    """Calculate MACD"""
    try:
        ema_12 = series.ewm(span=12).mean()
        ema_26 = series.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    except:
        return pd.Series([0] * len(series)), pd.Series([0] * len(series)), pd.Series([0] * len(series))

def _calculate_atr(df, period=14):
    """Calculate ATR"""
    try:
        high_low = df['high'] - df['low']
        high_close_prev = abs(df['high'] - df['close'].shift(1))
        low_close_prev = abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    except:
        return pd.Series([0.02] * len(df), index=df.index)

def _single_entry_point(df: pd.DataFrame) -> float:
    """Calculate single entry point based on trend and ATR"""
    try:
        last_close = float(df["close"].iloc[-1])
        
        # Calculate EMA50
        if len(df) >= 50:
            e50 = df["close"].ewm(span=50).mean().iloc[-1]
        else:
            e50 = df["close"].ewm(span=min(20, len(df))).mean().iloc[-1]
            
        # Calculate ATR
        a14 = _calculate_atr(df, 14).iloc[-1]
        if pd.isna(a14) or a14 == 0:
            a14 = last_close * 0.02  # Fallback 2% ATR
            
        trend = _trend_label(df)
        
        if trend == "up":
            return float(min(e50, last_close - 0.5 * a14))
        elif trend == "down":
            return float(max(e50, last_close + 0.5 * a14))
        else:
            return float(last_close - 0.2 * a14)
    except Exception as e:
        # Fallback to current price
        return float(df["close"].iloc[-1])

def _prepare_dataframe(ohlcv_data):
    """Convert OHLCV data to DataFrame"""
    try:
        if isinstance(ohlcv_data, dict) and 'data' in ohlcv_data:
            data = ohlcv_data['data']
        else:
            data = ohlcv_data
            
        if not data:
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Handle different column formats
        if 'close' in df.columns:
            # Already in correct format
            pass
        elif len(df.columns) >= 5:
            # Assume OHLCV format
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'][:len(df.columns)]
        else:
            return None
            
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # Drop NaN rows
        df = df.dropna()
        
        return df if len(df) > 10 else None
        
    except Exception as e:
        print(f"Error preparing dataframe: {e}")
        return None

async def analyze_coin_futures(coin: str, crypto_api=None) -> Dict[str, Any]:
    """
    Analisis khusus futures (perp) dan kembalikan dict siap pakai, bukan coroutine.
    """
    try:
        if not crypto_api:
            return {"coin": coin.upper(), "error": "No crypto_api provided"}
            
        # Get OHLCV data - use proper await
        ohlcv_data = await crypto_api.get_ohlcv_data(coin, period="5MIN", limit=300, market="perp")
        
        if not ohlcv_data or not ohlcv_data.get('success'):
            return {"coin": coin.upper(), "error": "Failed to get OHLCV data"}
            
        # Prepare DataFrame
        df = _prepare_dataframe(ohlcv_data)
        if df is None or len(df) < 10:
            return {"coin": coin.upper(), "error": "Insufficient data"}
            
        # Calculate indicators
        trend = _trend_label(df)
        rsi = _calculate_rsi(df["close"])
        macd_line, signal_line, macd_hist = _calculate_macd(df["close"])
        atr = _calculate_atr(df)
        
        # Get latest values safely
        current_price = float(df["close"].iloc[-1])
        current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        current_macd_hist = float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else 0.0
        current_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else current_price * 0.02
        
        res: Dict[str, Any] = {
            "coin": coin.upper(),
            "price": current_price,
            "trend": trend,
            "rsi": current_rsi,
            "macd_hist": current_macd_hist,
            "atr": current_atr,
            "entry": _single_entry_point(df),
        }
        
        # Generate signal
        res["ok"] = (res["trend"] == "up") and (res["macd_hist"] > 0) and (40 < res["rsi"] < 70)
        
        return res
        
    except Exception as e:
        return {"coin": coin.upper(), "error": str(e)}

async def futures_signals(coins: List[str], crypto_api=None) -> List[Dict[str, Any]]:
    """
    Scan koin futures secara concurrent & aman.
    HASIL = list of dict (bukan coroutine), sehingga formatter .get() aman.
    """
    try:
        coins_up = [c.upper() for c in coins]
        tasks = [analyze_coin_futures(c, crypto_api) for c in coins_up]
        results = await gather_safe(tasks)
        
        out: List[Dict[str, Any]] = []
        for c, r in zip(coins_up, results):
            if isinstance(r, Exception):
                out.append({"coin": c, "error": str(r)})
            else:
                # r sudah dict siap .get()
                out.append(r)
        return out
        
    except Exception as e:
        return [{"coin": "ERROR", "error": f"Futures signals failed: {str(e)}"}]
