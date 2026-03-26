#!/usr/bin/env python3
"""
Smart Money Concepts (SMC) Analyzer
Detects: Order Blocks, FVG, Market Structure, Week High/Low, EMA 21
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class OrderBlock:
    """Order Block structure"""
    type: str  # 'bullish' or 'bearish'
    high: float
    low: float
    time: datetime
    strength: float  # 0-100

@dataclass
class FVG:
    """Fair Value Gap structure"""
    type: str  # 'bullish' or 'bearish'
    top: float
    bottom: float
    time: datetime
    filled: bool = False

@dataclass
class MarketStructure:
    """Market Structure (HH/HL or LH/LL)"""
    trend: str  # 'uptrend', 'downtrend', 'ranging'
    last_high: float
    last_low: float
    structure_points: List[Tuple[str, float, datetime]]  # (type, price, time)

class SMCAnalyzer:
    """Smart Money Concepts Analyzer"""
    
    def __init__(self):
        self.min_ob_strength = 60  # Minimum order block strength
        self.min_fvg_size = 0.001  # Minimum FVG size (0.1%)
        
    def analyze(self, symbol: str, timeframe: str = '1h', limit: int = 200) -> Dict:
        """
        Comprehensive SMC analysis
        
        Returns:
            Dict with OB, FVG, structure, week high/low, EMA 21
        """
        try:
            # Get klines data — try Binance first, fallback to alternative
            klines = self._fetch_klines_with_fallback(symbol, timeframe, limit)
            if not klines or len(klines) < 50:
                return {'error': 'Insufficient data'}
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate indicators
            current_price = float(df['close'].iloc[-1])
            
            # 1. Order Blocks
            order_blocks = self._detect_order_blocks(df)
            
            # 2. Fair Value Gaps
            fvgs = self._detect_fvg(df)
            
            # 3. Market Structure
            structure = self._analyze_market_structure(df)
            
            # 4. Week High/Low
            week_high, week_low = self._get_week_high_low(df)
            
            # 5. EMA 21
            ema_21 = self._calculate_ema(df['close'], 21)
            
            return {
                'success': True,
                'symbol': symbol,
                'timeframe': timeframe,
                'current_price': current_price,
                'order_blocks': order_blocks,
                'fvgs': fvgs,
                'structure': structure,
                'week_high': week_high,
                'week_low': week_low,
                'ema_21': ema_21,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _fetch_klines_with_fallback(self, symbol: str, timeframe: str, limit: int) -> list:
        """Fetch klines from Binance, fallback to CryptoCompare/CoinGecko on 451/error"""
        # Try Binance first
        try:
            from app.providers.binance_provider import fetch_klines
            klines = fetch_klines(symbol, timeframe, limit=limit)
            if klines and len(klines) >= 50:
                print(f"✅ Binance klines OK for {symbol}", flush=True)
                return klines
        except Exception as e:
            print(f"⚠️ Binance klines failed for {symbol}: {e} — trying fallback", flush=True)

        # Fallback to alternative provider (CryptoCompare / CoinGecko)
        try:
            from app.providers.alternative_klines_provider import alternative_klines_provider
            klines = alternative_klines_provider.get_klines(symbol, timeframe, limit)
            if klines and len(klines) >= 50:
                print(f"✅ Alternative klines OK for {symbol}", flush=True)
                return klines
        except Exception as e:
            print(f"❌ Alternative klines also failed for {symbol}: {e}", flush=True)

        return []

    def _detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """Detect bullish and bearish order blocks"""
        order_blocks = []
        
        try:
            # Look for strong moves (>2% in one candle)
            df['body'] = abs(df['close'] - df['open'])
            df['range'] = df['high'] - df['low']
            df['body_pct'] = (df['body'] / df['open']) * 100
            
            # Bullish OB: Strong green candle followed by continuation
            for i in range(10, len(df) - 5):
                if df['body_pct'].iloc[i] > 1.5 and df['close'].iloc[i] > df['open'].iloc[i]:
                    # Check if price came back and bounced
                    future_low = df['low'].iloc[i+1:i+6].min()
                    if future_low <= df['low'].iloc[i] and df['close'].iloc[-1] > df['close'].iloc[i]:
                        strength = min(100, df['body_pct'].iloc[i] * 30)
                        order_blocks.append(OrderBlock(
                            type='bullish',
                            high=df['high'].iloc[i],
                            low=df['low'].iloc[i],
                            time=df['timestamp'].iloc[i],
                            strength=strength
                        ))
            
            # Bearish OB: Strong red candle followed by continuation
            for i in range(10, len(df) - 5):
                if df['body_pct'].iloc[i] > 1.5 and df['close'].iloc[i] < df['open'].iloc[i]:
                    # Check if price came back and rejected
                    future_high = df['high'].iloc[i+1:i+6].max()
                    if future_high >= df['high'].iloc[i] and df['close'].iloc[-1] < df['close'].iloc[i]:
                        strength = min(100, df['body_pct'].iloc[i] * 30)
                        order_blocks.append(OrderBlock(
                            type='bearish',
                            high=df['high'].iloc[i],
                            low=df['low'].iloc[i],
                            time=df['timestamp'].iloc[i],
                            strength=strength
                        ))
            
            # Sort by strength and return top 3
            order_blocks.sort(key=lambda x: x.strength, reverse=True)
            return order_blocks[:3]
            
        except Exception as e:
            print(f"Error detecting order blocks: {e}")
            return []
    
    def _detect_fvg(self, df: pd.DataFrame) -> List[FVG]:
        """Detect Fair Value Gaps (imbalance zones)"""
        fvgs = []
        
        try:
            # FVG = gap between candle 1 high and candle 3 low (or vice versa)
            for i in range(2, len(df)):
                # Bullish FVG: candle 1 high < candle 3 low
                if df['high'].iloc[i-2] < df['low'].iloc[i]:
                    gap_size = (df['low'].iloc[i] - df['high'].iloc[i-2]) / df['high'].iloc[i-2]
                    if gap_size > self.min_fvg_size:
                        fvgs.append(FVG(
                            type='bullish',
                            top=df['low'].iloc[i],
                            bottom=df['high'].iloc[i-2],
                            time=df['timestamp'].iloc[i-1]
                        ))
                
                # Bearish FVG: candle 1 low > candle 3 high
                if df['low'].iloc[i-2] > df['high'].iloc[i]:
                    gap_size = (df['low'].iloc[i-2] - df['high'].iloc[i]) / df['low'].iloc[i-2]
                    if gap_size > self.min_fvg_size:
                        fvgs.append(FVG(
                            type='bearish',
                            top=df['low'].iloc[i-2],
                            bottom=df['high'].iloc[i],
                            time=df['timestamp'].iloc[i-1]
                        ))
            
            # Return last 3 unfilled FVGs
            current_price = df['close'].iloc[-1]
            unfilled_fvgs = []
            for fvg in reversed(fvgs):
                if fvg.type == 'bullish' and current_price < fvg.top:
                    unfilled_fvgs.append(fvg)
                elif fvg.type == 'bearish' and current_price > fvg.bottom:
                    unfilled_fvgs.append(fvg)
                
                if len(unfilled_fvgs) >= 3:
                    break
            
            return unfilled_fvgs
            
        except Exception as e:
            print(f"Error detecting FVG: {e}")
            return []
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> MarketStructure:
        """Analyze market structure (HH/HL or LH/LL)"""
        try:
            # Find swing highs and lows
            swing_points = []
            window = 5
            
            for i in range(window, len(df) - window):
                # Swing high
                if df['high'].iloc[i] == df['high'].iloc[i-window:i+window+1].max():
                    swing_points.append(('high', df['high'].iloc[i], df['timestamp'].iloc[i]))
                
                # Swing low
                if df['low'].iloc[i] == df['low'].iloc[i-window:i+window+1].min():
                    swing_points.append(('low', df['low'].iloc[i], df['timestamp'].iloc[i]))
            
            # Determine trend
            if len(swing_points) < 4:
                return MarketStructure('ranging', 0, 0, [])
            
            # Get last 4 swing points
            recent_swings = swing_points[-4:]
            highs = [p[1] for p in recent_swings if p[0] == 'high']
            lows = [p[1] for p in recent_swings if p[0] == 'low']
            
            # Check for HH/HL (uptrend)
            if len(highs) >= 2 and len(lows) >= 2:
                if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
                    trend = 'uptrend'
                elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
                    trend = 'downtrend'
                else:
                    trend = 'ranging'
            else:
                trend = 'ranging'
            
            last_high = highs[-1] if highs else 0
            last_low = lows[-1] if lows else 0
            
            return MarketStructure(trend, last_high, last_low, recent_swings)
            
        except Exception as e:
            print(f"Error analyzing market structure: {e}")
            return MarketStructure('ranging', 0, 0, [])
    
    def _get_week_high_low(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Get weekly high and low"""
        try:
            # Get last 7 days of data
            week_ago = datetime.now() - timedelta(days=7)
            week_data = df[df['timestamp'] >= week_ago]
            
            if len(week_data) == 0:
                week_data = df.tail(168)  # Fallback: last 168 hours (7 days)
            
            week_high = float(week_data['high'].max())
            week_low = float(week_data['low'].min())
            
            return week_high, week_low
            
        except Exception as e:
            print(f"Error getting week high/low: {e}")
            return 0, 0
    
    def _calculate_ema(self, series: pd.Series, period: int) -> float:
        """Calculate EMA"""
        try:
            ema = series.ewm(span=period, adjust=False).mean()
            return float(ema.iloc[-1])
        except Exception as e:
            print(f"Error calculating EMA: {e}")
            return 0

# Global instance
smc_analyzer = SMCAnalyzer()