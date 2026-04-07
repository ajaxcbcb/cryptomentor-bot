"""
Market Sentiment Detector
Automatically detects market condition (sideways vs trending) and recommends optimal trading mode
"""

import logging
from typing import Dict, Literal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


MarketCondition = Literal["SIDEWAYS", "TRENDING", "VOLATILE", "UNKNOWN"]


class MarketSentimentDetector:
    """
    Detects market sentiment to determine optimal trading mode
    
    Indicators:
    - ADX (Average Directional Index): Trend strength
    - Bollinger Band Width: Volatility
    - ATR: Average True Range
    - Price action: Range vs breakout
    """
    
    def __init__(self):
        self.cache = {}  # Cache results for 5 minutes
        self.cache_duration = 300  # 5 minutes
    
    def detect_market_condition(self, symbol: str = "BTC") -> Dict:
        """
        Detect current market condition for a symbol
        
        Returns:
            {
                'condition': 'SIDEWAYS' | 'TRENDING' | 'VOLATILE',
                'confidence': 0-100,
                'recommended_mode': 'scalping' | 'swing',
                'indicators': {
                    'adx': float,
                    'bb_width': float,
                    'atr_pct': float,
                    'range_bound': bool
                },
                'reason': str
            }
        """
        # Check cache
        cache_key = f"{symbol}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            from app.providers.alternative_klines_provider import alternative_klines_provider
            import numpy as np
            
            # Fetch 1H data for analysis
            klines = alternative_klines_provider.get_klines(symbol, interval='1h', limit=100)
            
            if not klines or len(klines) < 50:
                logger.warning(f"[MarketSentiment] Insufficient data for {symbol}")
                return self._default_response()
            
            # Extract price data
            closes = np.array([float(k[4]) for k in klines])
            highs = np.array([float(k[2]) for k in klines])
            lows = np.array([float(k[3]) for k in klines])
            
            # Calculate indicators
            adx = self._calculate_adx(highs, lows, closes, period=14)
            bb_width = self._calculate_bb_width(closes, period=20)
            atr_pct = self._calculate_atr_pct(highs, lows, closes, period=14)
            range_bound = self._is_range_bound(closes, period=50)
            
            # Determine market condition
            condition, confidence, reason = self._classify_market(
                adx, bb_width, atr_pct, range_bound
            )
            
            # Recommend trading mode
            recommended_mode = "scalping" if condition == "SIDEWAYS" else "swing"
            
            result = {
                'condition': condition,
                'confidence': confidence,
                'recommended_mode': recommended_mode,
                'indicators': {
                    'adx': round(adx, 2),
                    'bb_width': round(bb_width, 4),
                    'atr_pct': round(atr_pct, 2),
                    'range_bound': range_bound
                },
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            logger.info(
                f"[MarketSentiment:{symbol}] {condition} (confidence: {confidence}%) "
                f"→ Recommend: {recommended_mode.upper()}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[MarketSentiment] Error detecting market condition: {e}")
            return self._default_response()
    
    def _calculate_adx(self, highs, lows, closes, period=14):
        """
        Calculate Average Directional Index (ADX)
        ADX < 25 = Weak trend (sideways)
        ADX 25-50 = Strong trend
        ADX > 50 = Very strong trend
        """
        try:
            import numpy as np
            
            # Calculate True Range
            tr1 = highs[1:] - lows[1:]
            tr2 = np.abs(highs[1:] - closes[:-1])
            tr3 = np.abs(lows[1:] - closes[:-1])
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate Directional Movement
            up_move = highs[1:] - highs[:-1]
            down_move = lows[:-1] - lows[1:]
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            # Smooth with EMA
            atr = self._ema(tr, period)
            plus_di = 100 * self._ema(plus_dm, period) / atr
            minus_di = 100 * self._ema(minus_dm, period) / atr
            
            # Calculate DX and ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            adx = self._ema(dx, period)
            
            return float(adx[-1]) if len(adx) > 0 else 20.0
            
        except Exception as e:
            logger.warning(f"[MarketSentiment] ADX calculation error: {e}")
            return 20.0  # Default neutral value
    
    def _calculate_bb_width(self, closes, period=20):
        """
        Calculate Bollinger Band Width
        Low width = Low volatility (sideways)
        High width = High volatility (trending)
        """
        try:
            import numpy as np
            
            sma = np.convolve(closes, np.ones(period)/period, mode='valid')
            std = np.array([np.std(closes[i:i+period]) for i in range(len(closes)-period+1)])
            
            bb_width = (4 * std) / sma
            
            return float(bb_width[-1]) if len(bb_width) > 0 else 0.05
            
        except Exception as e:
            logger.warning(f"[MarketSentiment] BB Width calculation error: {e}")
            return 0.05  # Default neutral value
    
    def _calculate_atr_pct(self, highs, lows, closes, period=14):
        """
        Calculate ATR as percentage of price
        Low ATR% = Low volatility
        High ATR% = High volatility
        """
        try:
            import numpy as np
            
            tr1 = highs[1:] - lows[1:]
            tr2 = np.abs(highs[1:] - closes[:-1])
            tr3 = np.abs(lows[1:] - closes[:-1])
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            atr = self._ema(tr, period)
            atr_pct = 100 * atr / closes[1:]
            
            return float(atr_pct[-1]) if len(atr_pct) > 0 else 1.0
            
        except Exception as e:
            logger.warning(f"[MarketSentiment] ATR% calculation error: {e}")
            return 1.0  # Default neutral value
    
    def _is_range_bound(self, closes, period=50):
        """
        Check if price is range-bound (sideways)
        """
        try:
            import numpy as np
            
            recent = closes[-period:]
            price_range = (np.max(recent) - np.min(recent)) / np.mean(recent)
            
            # If price range < 10% over 50 periods, it's range-bound
            return price_range < 0.10
            
        except Exception as e:
            logger.warning(f"[MarketSentiment] Range check error: {e}")
            return False
    
    def _ema(self, data, period):
        """Calculate Exponential Moving Average"""
        import numpy as np
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def _classify_market(self, adx, bb_width, atr_pct, range_bound):
        """
        Classify market condition based on indicators
        
        Returns: (condition, confidence, reason)
        """
        score_sideways = 0
        score_trending = 0
        reasons = []
        
        # ADX Analysis
        if adx < 20:
            score_sideways += 40
            reasons.append(f"ADX {adx:.1f} < 20 (very weak trend)")
        elif adx < 25:
            score_sideways += 25
            reasons.append(f"ADX {adx:.1f} < 25 (weak trend)")
        elif adx < 40:
            score_trending += 30
            reasons.append(f"ADX {adx:.1f} (moderate trend)")
        else:
            score_trending += 40
            reasons.append(f"ADX {adx:.1f} > 40 (strong trend)")
        
        # Bollinger Band Width
        if bb_width < 0.03:
            score_sideways += 30
            reasons.append(f"BB Width {bb_width:.4f} (low volatility)")
        elif bb_width > 0.08:
            score_trending += 30
            reasons.append(f"BB Width {bb_width:.4f} (high volatility)")
        
        # ATR Percentage
        if atr_pct < 0.8:
            score_sideways += 20
            reasons.append(f"ATR {atr_pct:.2f}% (low volatility)")
        elif atr_pct > 2.0:
            score_trending += 20
            reasons.append(f"ATR {atr_pct:.2f}% (high volatility)")
        
        # Range Bound Check
        if range_bound:
            score_sideways += 10
            reasons.append("Price range-bound")
        else:
            score_trending += 10
            reasons.append("Price breaking ranges")
        
        # Determine condition
        total_score = score_sideways + score_trending
        if total_score == 0:
            return "UNKNOWN", 50, "Insufficient data"
        
        sideways_pct = (score_sideways / total_score) * 100
        trending_pct = (score_trending / total_score) * 100
        
        if sideways_pct > 55:
            return "SIDEWAYS", int(sideways_pct), " | ".join(reasons)
        elif trending_pct > 55:
            return "TRENDING", int(trending_pct), " | ".join(reasons)
        else:
            # VOLATILE (mixed signals) - default to SIDEWAYS for more trading opportunities
            return "SIDEWAYS", 50, "Mixed signals (defaulting to scalping): " + " | ".join(reasons)
    
    def _default_response(self):
        """Default response when detection fails"""
        return {
            'condition': 'UNKNOWN',
            'confidence': 0,
            'recommended_mode': 'swing',  # Default to swing for safety
            'indicators': {
                'adx': 0,
                'bb_width': 0,
                'atr_pct': 0,
                'range_bound': False
            },
            'reason': 'Detection failed - using default mode',
            'timestamp': datetime.utcnow().isoformat()
        }


# Singleton instance
_detector = MarketSentimentDetector()


def detect_market_condition(symbol: str = "BTC") -> Dict:
    """
    Convenience function to detect market condition
    
    Usage:
        result = detect_market_condition("BTC")
        if result['recommended_mode'] == 'scalping':
            # Use scalping mode
        else:
            # Use swing mode
    """
    return _detector.detect_market_condition(symbol)
