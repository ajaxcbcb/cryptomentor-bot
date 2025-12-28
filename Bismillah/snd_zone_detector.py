"""
Supply & Demand Zone Detection Engine
Uses only Binance Klines (OHLCV) data
Deterministic and Explainable signals
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import requests


@dataclass
class Zone:
    """Represents a Supply or Demand zone"""
    zone_type: str  # 'DEMAND' or 'SUPPLY'
    high: float
    low: float
    strength: float  # 0-100, based on confirmations
    formation_candle_index: int
    is_valid: bool = True
    break_price: Optional[float] = None
    
    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2
    
    def __repr__(self):
        emoji = "📍" if self.zone_type == "DEMAND" else "🎯"
        return f"{emoji} {self.zone_type} {self.low:.8g}-{self.high:.8g} (Strength: {self.strength:.0f}%)"


class SnDZoneDetector:
    """
    Supply & Demand Zone Detection Algorithm
    
    Algorithm:
    1. IMPULSIVE MOVE: Identify large candles (high volume relative change)
    2. BASE: Find consolidation after impulsive move
    3. DEPARTURE: Detect breakout from consolidation
    4. ZONE FORMATION: Create zone from base (consolidation area)
    5. VALIDATION: Check for zone revisits and breaks
    """
    
    BINANCE_SPOT_URL = "https://api.binance.com/api/v3"
    BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"
    
    # Timeframe mappings
    VALID_TIMEFRAMES = {
        '1h': '1h',
        '4h': '4h',
        '1H': '1h',
        '4H': '4h'
    }
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h", use_futures: bool = False):
        self.symbol = symbol.upper()
        self.timeframe = self.VALID_TIMEFRAMES.get(timeframe, "1h")
        self.use_futures = use_futures
        self.base_url = self.BINANCE_FUTURES_URL if use_futures else self.BINANCE_SPOT_URL
        
    def detect_snd_zones(self, limit: int = 100) -> Dict:
        """
        Main function: Detect Supply & Demand zones
        
        Args:
            limit: Number of candles to analyze (default 100)
            
        Returns:
            {
                'demand_zones': [Zone, ...],
                'supply_zones': [Zone, ...],
                'current_price': float,
                'closest_demand': Optional[Zone],
                'closest_supply': Optional[Zone],
                'entry_signal': Optional[str],  # 'BUY' | 'SELL' | None
                'explanation': str
            }
        """
        try:
            # Fetch klines
            klines = self._fetch_klines(limit)
            if not klines or len(klines) < 20:
                return {'error': f'Insufficient data: {len(klines)} candles'}
            
            # Extract OHLCV
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[7]) for k in klines]  # Quote asset volume
            
            current_price = closes[-1]
            
            # Detect zones
            demand_zones = self._detect_demand_zones(opens, highs, lows, closes, volumes)
            supply_zones = self._detect_supply_zones(opens, highs, lows, closes, volumes)
            
            # Filter valid zones
            demand_zones = [z for z in demand_zones if z.is_valid]
            supply_zones = [z for z in supply_zones if z.is_valid]
            
            # Find closest zones to current price
            closest_demand = self._find_closest_zone(demand_zones, current_price, below=True)
            closest_supply = self._find_closest_zone(supply_zones, current_price, below=False)
            
            # Generate entry signal
            entry_signal = self._generate_entry_signal(
                current_price, closest_demand, closest_supply, closes
            )
            
            return {
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'current_price': current_price,
                'demand_zones': demand_zones,
                'supply_zones': supply_zones,
                'closest_demand': closest_demand,
                'closest_supply': closest_supply,
                'entry_signal': entry_signal,
                'explanation': self._generate_explanation(
                    current_price, closest_demand, closest_supply, entry_signal
                )
            }
            
        except Exception as e:
            return {'error': f'Detection failed: {str(e)}'}
    
    def _fetch_klines(self, limit: int) -> List:
        """Fetch candlestick data from Binance"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': self.symbol,
                'interval': self.timeframe,
                'limit': min(limit, 1000)
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Kline fetch error: {e}")
            return []
    
    def _detect_demand_zones(self, opens, highs, lows, closes, volumes) -> List[Zone]:
        """
        Detect DEMAND zones (support areas)
        
        Rules:
        1. Find impulsive DOWN move (large candle breaking down)
        2. Identify base (consolidation after impulse)
        3. Mark base low as demand zone
        4. Validate with volume and price action
        """
        zones = []
        n = len(closes)
        
        for i in range(5, n - 3):
            # 1. IMPULSIVE MOVE: Large downward candle
            candle_range = highs[i] - lows[i]
            avg_range = sum(highs[max(0, i-5):i] - lows[max(0, i-5):i]) / 5
            volume_spike = volumes[i] > sum(volumes[max(0, i-5):i]) / 5 * 1.3
            
            is_impulsive_down = (
                closes[i] < opens[i] and  # Bearish candle
                candle_range > avg_range * 1.5 and  # Large range
                volume_spike  # Volume confirmation
            )
            
            if not is_impulsive_down:
                continue
            
            # 2. BASE: Find consolidation after impulse
            base_start = i + 1
            base_end = min(i + 8, n - 1)
            
            if base_end - base_start < 2:
                continue
            
            base_highs = highs[base_start:base_end]
            base_lows = lows[base_start:base_end]
            base_low = min(base_lows)
            base_high = max(base_highs)
            base_range = base_high - base_low
            
            # Consolidation check: range should be small
            consolidating = base_range < (closes[i] - lows[i]) * 0.5
            
            if not consolidating:
                continue
            
            # 3. DEPARTURE: Check for breakout after base
            departure_start = base_end
            departure_end = min(base_end + 4, n - 1)
            
            if departure_end - departure_start < 1:
                continue
            
            departure_closes = closes[departure_start:departure_end]
            departure_high = max(departure_closes)
            
            # Breakout above base
            if departure_high > base_high * 1.001:
                # Strong demand zone confirmed
                strength = self._calculate_zone_strength(
                    base_low, base_high, volumes[base_start:base_end]
                )
                
                zone = Zone(
                    zone_type='DEMAND',
                    high=base_high,
                    low=base_low,
                    strength=strength,
                    formation_candle_index=i
                )
                zones.append(zone)
        
        return zones
    
    def _detect_supply_zones(self, opens, highs, lows, closes, volumes) -> List[Zone]:
        """
        Detect SUPPLY zones (resistance areas)
        
        Rules:
        1. Find impulsive UP move (large candle breaking up)
        2. Identify base (consolidation after impulse)
        3. Mark base high as supply zone
        4. Validate with volume and price action
        """
        zones = []
        n = len(closes)
        
        for i in range(5, n - 3):
            # 1. IMPULSIVE MOVE: Large upward candle
            candle_range = highs[i] - lows[i]
            avg_range = sum(highs[max(0, i-5):i] - lows[max(0, i-5):i]) / 5
            volume_spike = volumes[i] > sum(volumes[max(0, i-5):i]) / 5 * 1.3
            
            is_impulsive_up = (
                closes[i] > opens[i] and  # Bullish candle
                candle_range > avg_range * 1.5 and  # Large range
                volume_spike  # Volume confirmation
            )
            
            if not is_impulsive_up:
                continue
            
            # 2. BASE: Find consolidation after impulse
            base_start = i + 1
            base_end = min(i + 8, n - 1)
            
            if base_end - base_start < 2:
                continue
            
            base_highs = highs[base_start:base_end]
            base_lows = lows[base_start:base_end]
            base_low = min(base_lows)
            base_high = max(base_highs)
            base_range = base_high - base_low
            
            # Consolidation check: range should be small
            consolidating = base_range < (highs[i] - closes[i]) * 0.5
            
            if not consolidating:
                continue
            
            # 3. DEPARTURE: Check for breakout after base
            departure_start = base_end
            departure_end = min(base_end + 4, n - 1)
            
            if departure_end - departure_start < 1:
                continue
            
            departure_closes = closes[departure_start:departure_end]
            departure_low = min(departure_closes)
            
            # Breakdown below base
            if departure_low < base_low * 0.999:
                # Strong supply zone confirmed
                strength = self._calculate_zone_strength(
                    base_low, base_high, volumes[base_start:base_end]
                )
                
                zone = Zone(
                    zone_type='SUPPLY',
                    high=base_high,
                    low=base_low,
                    strength=strength,
                    formation_candle_index=i
                )
                zones.append(zone)
        
        return zones
    
    def _calculate_zone_strength(self, zone_low: float, zone_high: float, 
                                 base_volumes: List[float]) -> float:
        """
        Calculate zone strength (0-100)
        Based on volume consistency and range
        """
        if not base_volumes:
            return 50
        
        avg_volume = sum(base_volumes) / len(base_volumes)
        volume_consistency = sum(1 for v in base_volumes if v > avg_volume * 0.7) / len(base_volumes)
        
        # Strength: 50-85 range based on volume consistency
        strength = 50 + (volume_consistency * 35)
        return min(100, max(50, strength))
    
    def _find_closest_zone(self, zones: List[Zone], current_price: float, 
                          below: bool = True) -> Optional[Zone]:
        """Find closest zone to current price"""
        if not zones:
            return None
        
        if below:
            # Demand: zones below current price
            relevant = [z for z in zones if z.high < current_price]
            if relevant:
                return max(relevant, key=lambda z: z.high)
        else:
            # Supply: zones above current price
            relevant = [z for z in zones if z.low > current_price]
            if relevant:
                return min(relevant, key=lambda z: z.low)
        
        return None
    
    def _generate_entry_signal(self, current_price: float, 
                              closest_demand: Optional[Zone],
                              closest_supply: Optional[Zone],
                              closes: List[float]) -> Optional[str]:
        """
        Generate entry signal based on zone proximity
        
        Rules:
        - BUY: Price within 0.5% of demand zone + trending up
        - SELL: Price within 0.5% of supply zone + trending down
        """
        trend = 'up' if closes[-1] > closes[-5] else 'down'
        
        # Check demand zone proximity
        if closest_demand:
            distance = current_price - closest_demand.high
            distance_pct = (distance / current_price) * 100
            
            if 0 <= distance_pct <= 0.5 and trend == 'up':
                return 'BUY'
        
        # Check supply zone proximity
        if closest_supply:
            distance = closest_supply.low - current_price
            distance_pct = (distance / current_price) * 100
            
            if 0 <= distance_pct <= 0.5 and trend == 'down':
                return 'SELL'
        
        return None
    
    def _generate_explanation(self, current_price: float,
                             closest_demand: Optional[Zone],
                             closest_supply: Optional[Zone],
                             entry_signal: Optional[str]) -> str:
        """Generate readable explanation of the analysis"""
        lines = []
        
        lines.append(f"Current Price: ${current_price:,.8g}")
        
        if closest_demand:
            distance = ((current_price - closest_demand.high) / current_price) * 100
            lines.append(f"\n📍 Closest Demand: ${closest_demand.low:,.8g} - ${closest_demand.high:,.8g}")
            lines.append(f"   Distance: {distance:+.3f}% | Strength: {closest_demand.strength:.0f}%")
        else:
            lines.append("\n📍 No demand zones detected")
        
        if closest_supply:
            distance = ((closest_supply.low - current_price) / current_price) * 100
            lines.append(f"\n🎯 Closest Supply: ${closest_supply.low:,.8g} - ${closest_supply.high:,.8g}")
            lines.append(f"   Distance: {distance:+.3f}% | Strength: {closest_supply.strength:.0f}%")
        else:
            lines.append("\n🎯 No supply zones detected")
        
        if entry_signal == 'BUY':
            lines.append(f"\n✅ ENTRY SIGNAL: BUY at demand zone revisit")
        elif entry_signal == 'SELL':
            lines.append(f"\n✅ ENTRY SIGNAL: SELL at supply zone revisit")
        else:
            lines.append(f"\n⏳ No entry signal: Waiting for zone revisit")
        
        return '\n'.join(lines)


def detect_snd_zones(symbol: str, timeframe: str = "1h", limit: int = 100,
                     use_futures: bool = False) -> Dict:
    """
    Convenience function: Detect Supply & Demand zones
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
        timeframe: '1h' or '4h' only
        limit: Number of candles to analyze
        use_futures: Use Binance Futures instead of Spot
        
    Returns:
        Dictionary with zones and entry signals
    """
    detector = SnDZoneDetector(symbol, timeframe, use_futures)
    return detector.detect_snd_zones(limit)


# Example usage
if __name__ == "__main__":
    # Test the detector
    result = detect_snd_zones("BTCUSDT", "1h", limit=100)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n{result['symbol']} ({result['timeframe']})")
        print("=" * 60)
        print(result['explanation'])
        print("\n📊 Demand Zones:")
        for zone in result['demand_zones']:
            print(f"  {zone}")
        print("\n📊 Supply Zones:")
        for zone in result['supply_zones']:
            print(f"  {zone}")
