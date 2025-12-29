
"""
Enhanced Supply & Demand Zone Detection Engine
Uses only Binance Klines (OHLCV) data
Deterministic and Explainable signals with proper entry logic
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import requests
import time


@dataclass
class Zone:
    """Represents a Supply or Demand zone with validation"""
    zone_type: str  # 'DEMAND' or 'SUPPLY'
    high: float
    low: float
    strength: float  # 0-100, based on volume and structure
    formation_candle_index: int
    entry_price: float  # Optimal entry price within zone
    is_valid: bool = True
    break_price: Optional[float] = None
    volume_confirmation: bool = False
    
    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2
    
    @property
    def zone_width(self) -> float:
        return abs(self.high - self.low)
    
    def is_price_in_zone(self, price: float, tolerance: float = 0.001) -> bool:
        """Check if price is within zone with tolerance"""
        return (self.low * (1 - tolerance)) <= price <= (self.high * (1 + tolerance))
    
    def distance_from_zone(self, price: float) -> float:
        """Calculate distance from price to nearest zone boundary"""
        if price < self.low:
            return (self.low - price) / price
        elif price > self.high:
            return (price - self.high) / price
        else:
            return 0.0  # Price is inside zone
    
    def __repr__(self):
        emoji = "🟢" if self.zone_type == "DEMAND" else "🔴"
        status = "✅" if self.is_valid else "❌"
        return f"{emoji} {status} {self.zone_type} {self.low:.6f}-{self.high:.6f} (S:{self.strength:.0f}%)"


class SnDZoneDetector:
    """
    Enhanced Supply & Demand Zone Detection Algorithm
    
    ALGORITHM:
    1. SCAN for impulsive moves (large candles with volume spikes)
    2. IDENTIFY consolidation base after impulse
    3. CONFIRM departure/breakout from base
    4. CREATE zone from consolidation area
    5. VALIDATE zone strength and entry conditions
    """
    
    BINANCE_SPOT_URL = "https://api.binance.com/api/v3"
    BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"
    
    # Enhanced timeframe configuration
    VALID_TIMEFRAMES = {
        '1h': '1h', '4h': '4h',
        '1H': '1h', '4H': '4h'  # Accept both formats
    }
    
    # Algorithm parameters
    IMPULSE_THRESHOLD = 1.8  # Candle must be 1.8x average range
    VOLUME_SPIKE_THRESHOLD = 1.4  # Volume must be 1.4x average
    CONSOLIDATION_RATIO = 0.4  # Base range should be <40% of impulse
    MIN_BASE_CANDLES = 3  # Minimum consolidation period
    MAX_BASE_CANDLES = 8  # Maximum consolidation period
    ZONE_VALIDITY_PERIODS = {'1h': 24, '4h': 12}  # Max candles before zone expires
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h", use_futures: bool = False):
        self.symbol = symbol.upper()
        self.timeframe = self.VALID_TIMEFRAMES.get(timeframe, "1h")
        self.use_futures = use_futures
        self.base_url = self.BINANCE_FUTURES_URL if use_futures else self.BINANCE_SPOT_URL
        
    def detect_snd_zones(self, limit: int = 100) -> Dict:
        """
        Main function: Detect Supply & Demand zones with enhanced logic
        
        Returns:
            {
                'symbol': str,
                'timeframe': str,
                'current_price': float,
                'demand_zones': [Zone, ...],
                'supply_zones': [Zone, ...],
                'active_demand': Optional[Zone],
                'active_supply': Optional[Zone],
                'entry_signal': Optional[str],  # 'BUY_DEMAND' | 'SELL_SUPPLY' | None
                'signal_strength': float,  # 0-100
                'explanation': str,
                'zone_analysis': Dict
            }
        """
        try:
            # Fetch enhanced klines data
            klines = self._fetch_klines(limit + 20)  # Get extra data for better analysis
            if not klines or len(klines) < 50:
                return {'error': f'Insufficient data: {len(klines) if klines else 0} candles'}
            
            # Extract OHLCV with validation
            ohlcv_data = self._extract_ohlcv_data(klines)
            if not ohlcv_data:
                return {'error': 'Invalid OHLCV data extraction'}
            
            opens, highs, lows, closes, volumes = ohlcv_data
            current_price = closes[-1]
            
            # Enhanced zone detection
            demand_zones = self._detect_enhanced_demand_zones(opens, highs, lows, closes, volumes)
            supply_zones = self._detect_enhanced_supply_zones(opens, highs, lows, closes, volumes)
            
            # Filter and validate zones
            valid_demand_zones = self._filter_valid_zones(demand_zones, current_price, 'DEMAND')
            valid_supply_zones = self._filter_valid_zones(supply_zones, current_price, 'SUPPLY')
            
            # Find active zones (closest to current price)
            active_demand = self._find_active_zone(valid_demand_zones, current_price, 'DEMAND')
            active_supply = self._find_active_zone(valid_supply_zones, current_price, 'SUPPLY')
            
            # Generate entry signal with enhanced logic
            signal_data = self._generate_entry_signal(
                current_price, active_demand, active_supply, closes[-10:]
            )
            
            # Zone analysis for transparency
            zone_analysis = self._analyze_zone_quality(
                valid_demand_zones, valid_supply_zones, current_price
            )
            
            return {
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'current_price': current_price,
                'demand_zones': valid_demand_zones,
                'supply_zones': valid_supply_zones,
                'active_demand': active_demand,
                'active_supply': active_supply,
                'entry_signal': signal_data['signal'],
                'signal_strength': signal_data['strength'],
                'entry_price': signal_data['entry_price'],
                'stop_loss': signal_data['stop_loss'],
                'take_profit': signal_data['take_profit'],
                'explanation': self._generate_detailed_explanation(
                    current_price, active_demand, active_supply, signal_data
                ),
                'zone_analysis': zone_analysis,
                'algorithm_version': '2.0_enhanced'
            }
            
        except Exception as e:
            return {'error': f'SnD detection failed: {str(e)}'}
    
    def _extract_ohlcv_data(self, klines) -> Optional[Tuple]:
        """Extract and validate OHLCV data from klines"""
        try:
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[7]) for k in klines]  # Quote asset volume for better analysis
            
            # Validation checks
            if len(opens) != len(highs) or len(opens) != len(closes):
                return None
            
            # Sanity checks
            for i in range(len(opens)):
                if not (lows[i] <= opens[i] <= highs[i] and lows[i] <= closes[i] <= highs[i]):
                    return None
                if volumes[i] < 0:
                    return None
            
            return (opens, highs, lows, closes, volumes)
        except (ValueError, TypeError, IndexError):
            return None
    
    def _detect_enhanced_demand_zones(self, opens, highs, lows, closes, volumes) -> List[Zone]:
        """
        Enhanced DEMAND zone detection with proper algorithm
        
        PATTERN: Downward Impulse → Consolidation → Upward Departure
        """
        zones = []
        n = len(closes)
        
        # Calculate dynamic thresholds
        avg_ranges = [highs[i] - lows[i] for i in range(max(0, n-20), n)]
        avg_range = sum(avg_ranges) / len(avg_ranges) if avg_ranges else 0.01
        
        avg_volumes = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_volume = sum(avg_volumes) / len(avg_volumes) if avg_volumes else 1
        
        for i in range(10, n - 8):  # Leave room for base and departure analysis
            # PHASE 1: IDENTIFY IMPULSIVE DOWN MOVE
            candle_range = highs[i] - lows[i]
            is_bearish = closes[i] < opens[i]
            is_large_candle = candle_range > avg_range * self.IMPULSE_THRESHOLD
            has_volume_spike = volumes[i] > avg_volume * self.VOLUME_SPIKE_THRESHOLD
            
            # Additional impulse validation
            price_drop = (opens[i] - closes[i]) / opens[i] if opens[i] > 0 else 0
            significant_drop = price_drop > 0.02  # At least 2% drop
            
            if not (is_bearish and is_large_candle and has_volume_spike and significant_drop):
                continue
            
            # PHASE 2: FIND CONSOLIDATION BASE
            base_start = i + 1
            base_end = min(i + self.MAX_BASE_CANDLES + 1, n - 3)
            
            if base_end - base_start < self.MIN_BASE_CANDLES:
                continue
            
            # Analyze consolidation quality
            base_highs = highs[base_start:base_end]
            base_lows = lows[base_start:base_end]
            base_volumes = volumes[base_start:base_end]
            
            if not (base_highs and base_lows and base_volumes):
                continue
                
            base_high = max(base_highs)
            base_low = min(base_lows)
            base_range = base_high - base_low
            
            # Consolidation validation
            impulse_range = highs[i] - lows[i]
            is_tight_consolidation = base_range < impulse_range * self.CONSOLIDATION_RATIO
            avg_base_volume = sum(base_volumes) / len(base_volumes)
            has_consistent_volume = avg_base_volume > avg_volume * 0.7
            
            if not (is_tight_consolidation and has_consistent_volume):
                continue
            
            # PHASE 3: CONFIRM DEPARTURE (UPWARD BREAKOUT)
            departure_start = base_end
            departure_end = min(departure_start + 4, n)
            
            if departure_end - departure_start < 2:
                continue
            
            departure_highs = highs[departure_start:departure_end]
            departure_volumes = volumes[departure_start:departure_end]
            
            if not departure_highs:
                continue
                
            breakout_high = max(departure_highs)
            breakout_volume = max(departure_volumes) if departure_volumes else 0
            
            # Departure validation
            clear_breakout = breakout_high > base_high * 1.005  # Clear break above base
            volume_confirmation = breakout_volume > avg_volume * 1.2
            
            if clear_breakout and volume_confirmation:
                # ZONE CREATION: Use consolidation area as demand zone
                strength = self._calculate_zone_strength(
                    base_low, base_high, base_volumes, volumes[i], breakout_volume
                )
                
                # Optimal entry price (closer to base_low for better R:R)
                entry_price = base_low + (base_range * 0.25)  # 25% into the zone
                
                zone = Zone(
                    zone_type='DEMAND',
                    high=base_high,
                    low=base_low,
                    strength=strength,
                    formation_candle_index=i,
                    entry_price=entry_price,
                    volume_confirmation=True
                )
                zones.append(zone)
        
        return zones
    
    def _detect_enhanced_supply_zones(self, opens, highs, lows, closes, volumes) -> List[Zone]:
        """
        Enhanced SUPPLY zone detection with proper algorithm
        
        PATTERN: Upward Impulse → Consolidation → Downward Departure
        """
        zones = []
        n = len(closes)
        
        # Calculate dynamic thresholds
        avg_ranges = [highs[i] - lows[i] for i in range(max(0, n-20), n)]
        avg_range = sum(avg_ranges) / len(avg_ranges) if avg_ranges else 0.01
        
        avg_volumes = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_volume = sum(avg_volumes) / len(avg_volumes) if avg_volumes else 1
        
        for i in range(10, n - 8):
            # PHASE 1: IDENTIFY IMPULSIVE UP MOVE
            candle_range = highs[i] - lows[i]
            is_bullish = closes[i] > opens[i]
            is_large_candle = candle_range > avg_range * self.IMPULSE_THRESHOLD
            has_volume_spike = volumes[i] > avg_volume * self.VOLUME_SPIKE_THRESHOLD
            
            # Additional impulse validation
            price_rise = (closes[i] - opens[i]) / opens[i] if opens[i] > 0 else 0
            significant_rise = price_rise > 0.02  # At least 2% rise
            
            if not (is_bullish and is_large_candle and has_volume_spike and significant_rise):
                continue
            
            # PHASE 2: FIND CONSOLIDATION BASE
            base_start = i + 1
            base_end = min(i + self.MAX_BASE_CANDLES + 1, n - 3)
            
            if base_end - base_start < self.MIN_BASE_CANDLES:
                continue
            
            # Analyze consolidation quality
            base_highs = highs[base_start:base_end]
            base_lows = lows[base_start:base_end]
            base_volumes = volumes[base_start:base_end]
            
            if not (base_highs and base_lows and base_volumes):
                continue
                
            base_high = max(base_highs)
            base_low = min(base_lows)
            base_range = base_high - base_low
            
            # Consolidation validation
            impulse_range = highs[i] - lows[i]
            is_tight_consolidation = base_range < impulse_range * self.CONSOLIDATION_RATIO
            avg_base_volume = sum(base_volumes) / len(base_volumes)
            has_consistent_volume = avg_base_volume > avg_volume * 0.7
            
            if not (is_tight_consolidation and has_consistent_volume):
                continue
            
            # PHASE 3: CONFIRM DEPARTURE (DOWNWARD BREAKDOWN)
            departure_start = base_end
            departure_end = min(departure_start + 4, n)
            
            if departure_end - departure_start < 2:
                continue
            
            departure_lows = lows[departure_start:departure_end]
            departure_volumes = volumes[departure_start:departure_end]
            
            if not departure_lows:
                continue
                
            breakdown_low = min(departure_lows)
            breakdown_volume = max(departure_volumes) if departure_volumes else 0
            
            # Departure validation
            clear_breakdown = breakdown_low < base_low * 0.995  # Clear break below base
            volume_confirmation = breakdown_volume > avg_volume * 1.2
            
            if clear_breakdown and volume_confirmation:
                # ZONE CREATION: Use consolidation area as supply zone
                strength = self._calculate_zone_strength(
                    base_low, base_high, base_volumes, volumes[i], breakdown_volume
                )
                
                # Optimal entry price (closer to base_high for better R:R)
                entry_price = base_high - (base_range * 0.25)  # 75% into the zone
                
                zone = Zone(
                    zone_type='SUPPLY',
                    high=base_high,
                    low=base_low,
                    strength=strength,
                    formation_candle_index=i,
                    entry_price=entry_price,
                    volume_confirmation=True
                )
                zones.append(zone)
        
        return zones
    
    def _calculate_zone_strength(self, zone_low: float, zone_high: float, 
                                 base_volumes: List[float], impulse_volume: float,
                                 departure_volume: float) -> float:
        """
        Enhanced zone strength calculation (0-100)
        Based on volume profile, range analysis, and breakout strength
        """
        if not base_volumes:
            return 50
        
        try:
            # Volume analysis (40% weight)
            avg_base_volume = sum(base_volumes) / len(base_volumes)
            volume_consistency = sum(1 for v in base_volumes if v > avg_base_volume * 0.6) / len(base_volumes)
            impulse_strength = min(impulse_volume / avg_base_volume, 3.0) / 3.0  # Cap at 3x
            departure_strength = min(departure_volume / avg_base_volume, 3.0) / 3.0
            
            volume_score = (volume_consistency * 0.4 + impulse_strength * 0.3 + departure_strength * 0.3) * 40
            
            # Range analysis (30% weight)
            zone_range = zone_high - zone_low
            zone_mid = (zone_high + zone_low) / 2
            range_ratio = zone_range / zone_mid if zone_mid > 0 else 0
            
            # Prefer tighter zones (better precision)
            if range_ratio < 0.01:  # Very tight zone
                range_score = 30
            elif range_ratio < 0.02:  # Good zone
                range_score = 25
            elif range_ratio < 0.04:  # Acceptable zone
                range_score = 20
            else:  # Wide zone
                range_score = 15
            
            # Consolidation quality (30% weight)
            volume_variance = sum((v - avg_base_volume) ** 2 for v in base_volumes) / len(base_volumes)
            volume_std = volume_variance ** 0.5
            consolidation_quality = max(0, 1 - (volume_std / avg_base_volume)) if avg_base_volume > 0 else 0
            consolidation_score = consolidation_quality * 30
            
            # Final strength calculation
            total_strength = volume_score + range_score + consolidation_score
            return min(100, max(50, total_strength))  # Ensure 50-100 range
            
        except (ZeroDivisionError, ValueError):
            return 60  # Default strength
    
    def _filter_valid_zones(self, zones: List[Zone], current_price: float, zone_type: str) -> List[Zone]:
        """Filter zones based on validity rules and current price position"""
        valid_zones = []
        
        for zone in zones:
            # Check if zone is broken (invalidated)
            if zone_type == 'DEMAND':
                # Demand zone invalid if price closes significantly below zone low
                if current_price < zone.low * 0.995:  # 0.5% buffer
                    zone.is_valid = False
                    zone.break_price = current_price
            else:  # SUPPLY
                # Supply zone invalid if price closes significantly above zone high
                if current_price > zone.high * 1.005:  # 0.5% buffer
                    zone.is_valid = False
                    zone.break_price = current_price
            
            # Only keep zones with minimum strength
            if zone.is_valid and zone.strength >= 60:
                valid_zones.append(zone)
        
        # Sort by strength (strongest first)
        valid_zones.sort(key=lambda z: z.strength, reverse=True)
        
        # Return top zones only (max 3 per type)
        return valid_zones[:3]
    
    def _find_active_zone(self, zones: List[Zone], current_price: float, zone_type: str) -> Optional[Zone]:
        """Find the most relevant active zone for current price"""
        if not zones:
            return None
        
        # Filter zones by proximity and relevance
        relevant_zones = []
        
        for zone in zones:
            distance = zone.distance_from_zone(current_price)
            
            if zone_type == 'DEMAND':
                # For demand, price should be at or near the zone from above
                if current_price >= zone.low * 0.99 and distance <= 0.05:  # Within 5%
                    relevant_zones.append((zone, distance))
            else:  # SUPPLY
                # For supply, price should be at or near the zone from below
                if current_price <= zone.high * 1.01 and distance <= 0.05:  # Within 5%
                    relevant_zones.append((zone, distance))
        
        if not relevant_zones:
            return None
        
        # Return closest high-strength zone
        relevant_zones.sort(key=lambda x: (x[1], -x[0].strength))  # Sort by distance, then by strength desc
        return relevant_zones[0][0]
    
    def _generate_entry_signal(self, current_price: float, 
                              active_demand: Optional[Zone],
                              active_supply: Optional[Zone],
                              recent_closes: List[float]) -> Dict:
        """
        Generate entry signal based on SnD zone analysis
        
        RULES:
        - BUY_DEMAND: Price at demand zone + bullish momentum
        - SELL_SUPPLY: Price at supply zone + bearish momentum  
        - No signal if no active zones or conflicting signals
        """
        
        # Momentum analysis
        if len(recent_closes) >= 3:
            recent_momentum = (recent_closes[-1] - recent_closes[-3]) / recent_closes[-3]
            trend_strength = abs(recent_momentum) * 100
        else:
            recent_momentum = 0
            trend_strength = 0
        
        signal_data = {
            'signal': None,
            'strength': 0,
            'entry_price': current_price,
            'stop_loss': current_price,
            'take_profit': current_price,
            'reason': 'No valid setup'
        }
        
        # DEMAND ZONE ANALYSIS
        if active_demand and active_demand.is_price_in_zone(current_price, tolerance=0.01):
            bullish_momentum = recent_momentum > 0.001  # Slight bullish bias required
            zone_strength_factor = active_demand.strength / 100
            
            if bullish_momentum or trend_strength < 2:  # Accept if momentum is weak (potential reversal)
                signal_strength = (
                    active_demand.strength * 0.6 +  # Zone quality
                    (1 - active_demand.distance_from_zone(current_price)) * 20 +  # Price position
                    min(trend_strength * 2, 20)  # Momentum component
                )
                
                if signal_strength >= 70:  # High threshold for quality
                    # Calculate R:R targets
                    zone_range = active_demand.zone_width
                    stop_loss = active_demand.low - (zone_range * 0.5)  # Stop below zone
                    take_profit = current_price + (zone_range * 3)  # 3:1 R:R minimum
                    
                    signal_data.update({
                        'signal': 'BUY_DEMAND',
                        'strength': signal_strength,
                        'entry_price': active_demand.entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'reason': f'Price at demand zone (strength: {active_demand.strength:.0f}%)'
                    })
        
        # SUPPLY ZONE ANALYSIS  
        elif active_supply and active_supply.is_price_in_zone(current_price, tolerance=0.01):
            bearish_momentum = recent_momentum < -0.001  # Slight bearish bias required
            zone_strength_factor = active_supply.strength / 100
            
            if bearish_momentum or trend_strength < 2:  # Accept if momentum is weak (potential reversal)
                signal_strength = (
                    active_supply.strength * 0.6 +  # Zone quality
                    (1 - active_supply.distance_from_zone(current_price)) * 20 +  # Price position
                    min(trend_strength * 2, 20)  # Momentum component
                )
                
                if signal_strength >= 70:  # High threshold for quality
                    # Calculate R:R targets
                    zone_range = active_supply.zone_width
                    stop_loss = active_supply.high + (zone_range * 0.5)  # Stop above zone
                    take_profit = current_price - (zone_range * 3)  # 3:1 R:R minimum
                    
                    signal_data.update({
                        'signal': 'SELL_SUPPLY',
                        'strength': signal_strength,
                        'entry_price': active_supply.entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'reason': f'Price at supply zone (strength: {active_supply.strength:.0f}%)'
                    })
        
        return signal_data
    
    def _analyze_zone_quality(self, demand_zones: List[Zone], supply_zones: List[Zone], 
                             current_price: float) -> Dict:
        """Analyze overall zone quality for transparency"""
        return {
            'total_demand_zones': len(demand_zones),
            'total_supply_zones': len(supply_zones),
            'avg_demand_strength': sum(z.strength for z in demand_zones) / len(demand_zones) if demand_zones else 0,
            'avg_supply_strength': sum(z.strength for z in supply_zones) / len(supply_zones) if supply_zones else 0,
            'nearest_demand_distance': min([z.distance_from_zone(current_price) for z in demand_zones], default=999),
            'nearest_supply_distance': min([z.distance_from_zone(current_price) for z in supply_zones], default=999),
            'algorithm_confidence': 'HIGH' if (demand_zones or supply_zones) else 'LOW'
        }
    
    def _generate_detailed_explanation(self, current_price: float,
                                     active_demand: Optional[Zone],
                                     active_supply: Optional[Zone],
                                     signal_data: Dict) -> str:
        """Generate detailed explanation of the analysis"""
        
        lines = [f"📊 **SnD ANALYSIS - {self.symbol} ({self.timeframe})**\n"]
        lines.append(f"💰 Current Price: ${current_price:,.8g}")
        
        # Zone analysis
        if active_demand:
            distance_pct = active_demand.distance_from_zone(current_price) * 100
            lines.append(f"\n🟢 **ACTIVE DEMAND ZONE:**")
            lines.append(f"   Range: ${active_demand.low:,.8g} - ${active_demand.high:,.8g}")
            lines.append(f"   Entry: ${active_demand.entry_price:,.8g}")
            lines.append(f"   Strength: {active_demand.strength:.0f}%")
            lines.append(f"   Distance: {distance_pct:.2f}%")
        else:
            lines.append(f"\n🟢 No active demand zone detected")
        
        if active_supply:
            distance_pct = active_supply.distance_from_zone(current_price) * 100
            lines.append(f"\n🔴 **ACTIVE SUPPLY ZONE:**")
            lines.append(f"   Range: ${active_supply.low:,.8g} - ${active_supply.high:,.8g}")
            lines.append(f"   Entry: ${active_supply.entry_price:,.8g}")
            lines.append(f"   Strength: {active_supply.strength:.0f}%")
            lines.append(f"   Distance: {distance_pct:.2f}%")
        else:
            lines.append(f"\n🔴 No active supply zone detected")
        
        # Signal analysis
        lines.append(f"\n🎯 **TRADING SIGNAL:**")
        if signal_data['signal']:
            lines.append(f"   Signal: **{signal_data['signal']}**")
            lines.append(f"   Strength: {signal_data['strength']:.1f}%")
            lines.append(f"   Entry: ${signal_data['entry_price']:,.8g}")
            lines.append(f"   Stop Loss: ${signal_data['stop_loss']:,.8g}")
            lines.append(f"   Take Profit: ${signal_data['take_profit']:,.8g}")
            lines.append(f"   Reason: {signal_data['reason']}")
        else:
            lines.append(f"   **NO SIGNAL** - {signal_data['reason']}")
            lines.append(f"   Wait for price to reach valid SnD zone")
        
        lines.append(f"\n📋 **ALGORITHM NOTES:**")
        lines.append(f"• Uses Binance klines (OHLCV) only")
        lines.append(f"• Pattern: Impulse → Consolidation → Departure")
        lines.append(f"• Entry only at zone revisits with confirmation")
        lines.append(f"• Zones invalidated when broken")
        
        return '\n'.join(lines)
    
    def _fetch_klines(self, limit: int) -> List:
        """Fetch candlestick data from Binance with error handling"""
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


def detect_snd_zones(symbol: str, timeframe: str = "1h", limit: int = 100,
                     use_futures: bool = False) -> Dict:
    """
    Convenience function: Detect Supply & Demand zones with enhanced algorithm
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
        timeframe: '1h' or '4h' only
        limit: Number of candles to analyze (50-200 recommended)
        use_futures: Use Binance Futures instead of Spot
        
    Returns:
        Dictionary with enhanced zone analysis and entry signals
    """
    detector = SnDZoneDetector(symbol, timeframe, use_futures)
    return detector.detect_snd_zones(limit)


# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced detector
    print("🧪 Testing Enhanced SnD Zone Detection...")
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"📊 Testing {symbol}")
        print('='*60)
        
        result = detect_snd_zones(symbol, "1h", limit=100)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        print(result['explanation'])
        
        print(f"\n📈 Demand Zones Found: {len(result['demand_zones'])}")
        for zone in result['demand_zones']:
            print(f"  {zone}")
        
        print(f"\n📉 Supply Zones Found: {len(result['supply_zones'])}")
        for zone in result['supply_zones']:
            print(f"  {zone}")
        
        if result['entry_signal']:
            print(f"\n🚨 **SIGNAL DETECTED: {result['entry_signal']}**")
            print(f"   Strength: {result['signal_strength']:.1f}%")
            print(f"   Entry: ${result['entry_price']:,.6f}")
            print(f"   Stop: ${result['stop_loss']:,.6f}")
            print(f"   Target: ${result['take_profit']:,.6f}")
        else:
            print(f"\n⏳ No entry signal - Wait for zone revisit")
        
        time.sleep(1)  # Respect API rate limits
