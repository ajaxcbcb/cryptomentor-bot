
import pandas as pd
import numpy as np

def to_df(ohlcv):
    import pandas as pd
    return pd.DataFrame(ohlcv).astype({"open": "float64", "high": "float64", "low": "float64", "close": "float64", "volume": "float64"})

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0)
    down = (-d.clip(upper=0))
    rs = up.ewm(com=n-1, adjust=False).mean() / (down.ewm(com=n-1, adjust=False).mean() + 1e-9)
    return 100 - (100 / (1 + rs))

def macd(s, fast=12, slow=26, signal=9):
    m = ema(s, fast) - ema(s, slow)
    sig = ema(m, signal)
    return m, sig, m - sig

def atr(df, n=14):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n).mean()
