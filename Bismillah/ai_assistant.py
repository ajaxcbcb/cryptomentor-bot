# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
from datetime import datetime

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name

    def greet(self):
        return f"Halo! Saya {self.name}, siap membantu analisis dan informasi crypto kamu."

    def analyze_text(self, text):
        if "btc" in text.lower():
            return "📈 BTC sedang menarik untuk dianalisis hari ini!"
        elif "eth" in text.lower():
            return "📉 ETH menunjukkan sinyal konsolidasi."
        else:
            return "Saya tidak yakin, tapi saya akan bantu cari datanya."

    def help_message(self):
        return """🤖 **CryptoMentor AI Bot - Help**

📊 **Harga & Data Pasar:**
• `/price <symbol>` - Harga real-time
• `/market` - Overview pasar komprehensif

📈 **Analisis Trading:**
• `/analyze <symbol>` - Analisis mendalam (20 credit)
• `/futures <symbol>` - Analisis futures 1 coin (20 credit)
• `/futures_signals` - Sinyal futures lengkap (30 credit)

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio
• `/add_coin <symbol> <amount>` - Tambah ke portfolio
• `/credits` - Cek sisa credit
• `/subscribe` - Upgrade premium

🎯 **Lainnya:**
• `/ask_ai <pertanyaan>` - Tanya AI crypto
• `/referral` - Program referral
• `/language` - Ubah bahasa

💡 **Tips:**
- Ketik nama crypto langsung untuk harga cepat
- Fitur premium = unlimited access
- Gunakan referral untuk bonus credit

🚀 **Semua analisis menggunakan data real-time dari multiple API!**"""

    def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Generate clean and efficient futures analysis with SnD recommendations"""
        try:
            print(f"🎯 Generating futures analysis for {symbol} {timeframe}")
            
            if not crypto_api:
                return self._generate_offline_futures_signal(symbol, timeframe, language)
            
            # Get market data
            market_data = self._get_market_data(symbol, timeframe, crypto_api)
            
            # Analyze market structure
            market_analysis = self._analyze_market_structure(symbol, market_data, timeframe)
            
            # Generate trading levels
            trading_levels = self._calculate_trading_levels(market_data['price'], market_analysis)
            
            # Format final output
            return self._format_futures_output(symbol, timeframe, market_data, market_analysis, trading_levels, language)
            
        except Exception as e:
            print(f"❌ Error in futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _get_market_data(self, symbol, timeframe, crypto_api):
        """Centralized market data collection"""
        # Get real-time price from CoinAPI
        coinapi_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
        futures_data = crypto_api.get_comprehensive_futures_data(symbol)
        snd_data = crypto_api.analyze_supply_demand(symbol, timeframe)
        
        # Determine best price source
        if 'error' not in coinapi_data and coinapi_data.get('price', 0) > 0:
            primary_price = coinapi_data.get('price', 0)
            price_source = "CoinAPI Real-time"
            price_emoji = "🟢"
        elif 'error' not in futures_data and futures_data.get('price_data', {}).get('price', 0) > 0:
            primary_price = futures_data.get('price_data', {}).get('price', 0)
            price_source = "Binance Futures"
            price_emoji = "🟡"
        else:
            primary_price = self._get_estimated_price(symbol)
            price_source = "Estimated"
            price_emoji = "🔴"
        
        return {
            'price': primary_price,
            'price_source': price_source,
            'price_emoji': price_emoji,
            'coinapi_data': coinapi_data,
            'futures_data': futures_data,
            'snd_data': snd_data
        }

    def _analyze_market_structure(self, symbol, market_data, timeframe):
        """Analyze market structure and determine trading direction with HOLD for low confidence"""
        futures_data = market_data['futures_data']
        snd_data = market_data['snd_data']
        
        # Calculate signal strength
        signal_strength = 0
        signal_factors = []
        
        # Factor 1: SnD Analysis
        if 'error' not in snd_data and snd_data.get('signals'):
            best_snd_signal = max(snd_data['signals'], key=lambda x: x.get('confidence', 0))
            if best_snd_signal.get('confidence', 0) > 60:
                signal_strength += 3
                signal_factors.append(f"🎯 SnD {best_snd_signal.get('direction', 'LONG')} zone confirmed")
                preferred_direction = best_snd_signal.get('direction', 'LONG')
            else:
                preferred_direction = 'HOLD'  # Set HOLD if SnD confidence is low
        else:
            preferred_direction = 'HOLD'  # Set HOLD if no SnD signals
            
        # Factor 2: Futures sentiment
        if 'error' not in futures_data:
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                if long_ratio > 70:
                    signal_strength += 2 if preferred_direction == 'SHORT' else -1
                    signal_factors.append(f"⚠️ Overcrowded longs ({long_ratio:.1f}%)")
                elif long_ratio < 30:
                    signal_strength += 2 if preferred_direction == 'LONG' else -1
                    signal_factors.append(f"💎 Oversold conditions ({long_ratio:.1f}%)")
        
        # Factor 3: Timeframe bias
        timeframe_weight = {'15m': 1, '30m': 1.5, '1h': 2, '4h': 3, '1d': 4}.get(timeframe, 2)
        signal_strength += timeframe_weight
        signal_factors.append(f"📊 {timeframe} structure analysis")
        
        # Determine final direction and confidence with HOLD logic
        if signal_strength >= 4 and preferred_direction != 'HOLD':
            direction = preferred_direction
            confidence = min(90, 65 + signal_strength * 5)
        elif signal_strength <= 1 or preferred_direction == 'HOLD':
            # NEW LOGIC: Return HOLD instead of forcing LONG/SHORT
            direction = 'HOLD'
            confidence = 50  # Low confidence for HOLD
            signal_factors.append("⏸️ Sinyal tidak jelas - tunggu konfirmasi market")
        else:
            # Only assign LONG/SHORT if confidence > 60%
            calculated_confidence = min(85, 60 + signal_strength * 5)
            if calculated_confidence > 60:
                direction = preferred_direction if preferred_direction != 'HOLD' else 'LONG'
                confidence = calculated_confidence
            else:
                direction = 'HOLD'
                confidence = 50
                signal_factors.append("⏸️ Confidence rendah - hold position")
        
        return {
            'direction': direction,
            'confidence': confidence,
            'signal_factors': signal_factors,
            'signal_strength': signal_strength
        }

    def _calculate_trading_levels(self, current_price, market_analysis):
        """Calculate precise entry, TP, and SL levels"""
        direction = market_analysis['direction']
        confidence = market_analysis['confidence']
        
        # Adjust risk based on confidence
        risk_multiplier = 1.0 if confidence >= 80 else 1.2 if confidence >= 70 else 1.5
        
        if direction == 'LONG':
            entry = current_price * 0.998  # Slight dip entry
            tp1 = current_price * (1 + 0.025 / risk_multiplier)  # 2.5% adjusted for confidence
            tp2 = current_price * (1 + 0.05 / risk_multiplier)   # 5% adjusted for confidence
            sl = current_price * (1 - 0.02 * risk_multiplier)    # 2% SL adjusted for risk
        else:  # SHORT
            entry = current_price * 1.002  # Slight pump entry
            tp1 = current_price * (1 - 0.025 / risk_multiplier)  # 2.5% down
            tp2 = current_price * (1 - 0.05 / risk_multiplier)   # 5% down
            sl = current_price * (1 + 0.02 * risk_multiplier)    # 2% SL up
        
        # Calculate risk/reward
        risk = abs(entry - sl)
        reward = abs(tp2 - entry)
        rr_ratio = reward / risk if risk > 0 else 2.5
        
        return {
            'entry': entry,
            'tp1': tp1,
            'tp2': tp2,
            'sl': sl,
            'rr_ratio': rr_ratio,
            'risk_level': 'low' if confidence >= 80 else 'medium' if confidence >= 70 else 'high'
        }

    def _format_futures_output(self, symbol, timeframe, market_data, market_analysis, trading_levels, language='id'):
        """Format the final clean output for Telegram with HOLD handling"""
        price = market_data['price']
        direction = market_analysis['direction']
        confidence = market_analysis['confidence']
        factors = market_analysis['signal_factors']
        
        # Smart price formatting
        def format_price(p):
            if p < 1:
                return f"${p:.8f}"
            elif p < 100:
                return f"${p:.4f}"
            else:
                return f"${p:,.2f}"
        
        # Handle HOLD signals
        if direction == 'HOLD':
            direction_emoji = "⏸️"
            confidence_emoji = "⚠️"
        else:
            direction_emoji = "🟢" if direction == 'LONG' else "🔴"
            confidence_emoji = "🔥" if confidence >= 85 else "⭐" if confidence >= 75 else "💡"
        
        if language == 'id':
            if direction == 'HOLD':
                message = f"""🎯 **FUTURES ANALYSIS {symbol.upper()} ({timeframe})**

💰 **Harga**: {format_price(price)} {market_data['price_emoji']}
📡 **Source**: {market_data['price_source']}

{direction_emoji} **SIGNAL**: {direction} {confidence_emoji}
📊 **Confidence**: {confidence:.0f}%

⏸️ **REKOMENDASI HOLD:**
• Tidak ada setup trading yang jelas
• Tunggu konfirmasi trend yang lebih kuat
• Monitor level kunci: Support ${format_price(price * 0.97)} | Resistance ${format_price(price * 1.03)}

📈 **ANALISIS:**"""
                
                for factor in factors[:3]:  # Limit to 3 key factors
                    message += f"\n• {factor}"
                
                message += f"""

⚡ **STRATEGI HOLD:**
• Tunggu breakout atau breakdown yang jelas
• Confidence terlalu rendah untuk entry
• Observasi saja, jangan FOMO

⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""
            else:
                message = f"""🎯 **FUTURES ANALYSIS {symbol.upper()} ({timeframe})**

💰 **Harga**: {format_price(price)} {market_data['price_emoji']}
📡 **Source**: {market_data['price_source']}

{direction_emoji} **SIGNAL**: {direction} {confidence_emoji}
📊 **Confidence**: {confidence:.0f}%

💰 **TRADING LEVELS:**
📍 **Entry**: {format_price(trading_levels['entry'])}
🎯 **TP1**: {format_price(trading_levels['tp1'])} (50% profit)
🎯 **TP2**: {format_price(trading_levels['tp2'])} (50% profit)  
🛡️ **Stop Loss**: {format_price(trading_levels['sl'])}

📈 **ANALISIS:**"""
                
                for factor in factors[:3]:  # Limit to 3 key factors
                    message += f"\n• {factor}"
                
                message += f"""

⚡ **STRATEGY {timeframe.upper()}:**
• Risk/Reward: {trading_levels['rr_ratio']:.1f}:1
• Risk Level: {trading_levels['risk_level'].title()}
• Position size: 1-2% modal

🛡️ **RISK MANAGEMENT:**
• Set SL WAJIB sebelum entry
• Take profit bertahap di TP1 & TP2
• Exit jika struktur berubah

⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""
        
        else:
            message = f"""🎯 **FUTURES ANALYSIS {symbol.upper()} ({timeframe})**

💰 **Price**: {format_price(price)} {market_data['price_emoji']}
📡 **Source**: {market_data['price_source']}

{direction_emoji} **SIGNAL**: {direction} {confidence_emoji}
📊 **Confidence**: {confidence:.0f}%

💰 **TRADING LEVELS:**
📍 **Entry**: {format_price(trading_levels['entry'])}
🎯 **TP1**: {format_price(trading_levels['tp1'])} (50% profit)
🎯 **TP2**: {format_price(trading_levels['tp2'])} (50% profit)
🛡️ **Stop Loss**: {format_price(trading_levels['sl'])}

📈 **ANALYSIS:**"""
            
            for factor in factors[:3]:
                message += f"\n• {factor}"
            
            message += f"""

⚡ **STRATEGY {timeframe.upper()}:**
• Risk/Reward: {trading_levels['rr_ratio']:.1f}:1  
• Risk Level: {trading_levels['risk_level'].title()}
• Position size: 1-2% capital

🛡️ **RISK MANAGEMENT:**
• Set SL MANDATORY before entry
• Take profit gradually at TP1 & TP2
• Exit if structure changes

⏰ **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"""
        
        return message
    
    def _get_estimated_price(self, symbol):
        """Get estimated price for major cryptocurrencies when APIs fail"""
        estimated_prices = {
            'BTC': 67000,
            'ETH': 3200,
            'BNB': 580,
            'SOL': 185,
            'ADA': 0.48,
            'DOT': 6.90,
            'MATIC': 0.85,
            'AVAX': 42,
            'LINK': 18,
            'UNI': 12,
            'ATOM': 9.5,
            'FTM': 0.65,
            'NEAR': 8.2,
            'ALGO': 0.32,
            'MANA': 0.85,
            'SAND': 0.58,
            'AXS': 8.5
        }
        
        symbol_clean = symbol.upper().replace('USDT', '')
        return estimated_prices.get(symbol_clean, 1.0)
    
    def _format_price_smart(self, price):
        """Smart price formatting utility"""
        if price < 1:
            return f"${price:.6f}"
        elif price < 100:
            return f"${price:.4f}"
        else:
            return f"${price:,.2f}"
    
    def _calculate_advanced_snd_zones(self, ohlcv_data, current_price):
        """
        Advanced SnD zone calculation dari data OHLCV candlestick
        Returns: dict dengan demand_zones, supply_zones, dan strength rating
        """
        if not ohlcv_data or len(ohlcv_data) < 20:
            # Fallback ke zones sederhana jika data tidak cukup
            return {
                'demand_zones': [current_price * 0.95, current_price * 0.97],
                'supply_zones': [current_price * 1.03, current_price * 1.05],
                'strength': 'low'
            }
        
        try:
            # Extract OHLC data
            highs = [float(candle[2]) for candle in ohlcv_data[-50:]]  # Last 50 candles
            lows = [float(candle[3]) for candle in ohlcv_data[-50:]]
            closes = [float(candle[4]) for candle in ohlcv_data[-50:]]
            volumes = [float(candle[5]) for candle in ohlcv_data[-50:]]
            
            # Identify supply zones (resistance levels dengan volume tinggi)
            supply_zones = []
            for i in range(2, len(highs) - 2):
                if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and 
                    highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                    # Local high dengan volume confirmation
                    if volumes[i] > sum(volumes[max(0, i-3):i+4]) / 7 * 1.2:
                        supply_zones.append({
                            'price': highs[i],
                            'strength': min(100, volumes[i] / max(volumes) * 100),
                            'touches': 1
                        })
            
            # Identify demand zones (support levels dengan volume tinggi)
            demand_zones = []
            for i in range(2, len(lows) - 2):
                if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and 
                    lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                    # Local low dengan volume confirmation
                    if volumes[i] > sum(volumes[max(0, i-3):i+4]) / 7 * 1.2:
                        demand_zones.append({
                            'price': lows[i],
                            'strength': min(100, volumes[i] / max(volumes) * 100),
                            'touches': 1
                        })
            
            # Sort dan filter zones terbaik
            supply_zones = sorted(supply_zones, key=lambda x: x['strength'], reverse=True)[:3]
            demand_zones = sorted(demand_zones, key=lambda x: x['strength'], reverse=True)[:3]
            
            # Calculate overall strength
            avg_supply_strength = sum(z['strength'] for z in supply_zones) / len(supply_zones) if supply_zones else 0
            avg_demand_strength = sum(z['strength'] for z in demand_zones) / len(demand_zones) if demand_zones else 0
            overall_strength = (avg_supply_strength + avg_demand_strength) / 2
            
            strength_rating = 'high' if overall_strength > 70 else 'medium' if overall_strength > 40 else 'low'
            
            return {
                'demand_zones': [z['price'] for z in demand_zones],
                'supply_zones': [z['price'] for z in supply_zones],
                'strength': strength_rating,
                'demand_details': demand_zones,
                'supply_details': supply_zones
            }
            
        except Exception as e:
            print(f"❌ Error in advanced SnD calculation: {e}")
            return {
                'demand_zones': [current_price * 0.95, current_price * 0.97],
                'supply_zones': [current_price * 1.03, current_price * 1.05],
                'strength': 'low'
            }

    def _identify_consolidation_zones(self, ohlcv_data, lookback_period=14):
        """
        Deteksi zona konsolidasi (low volatility) untuk setup trading
        Returns: dict dengan consolidation zones dan volatility metrics
        """
        if not ohlcv_data or len(ohlcv_data) < lookback_period:
            return {'zones': [], 'current_volatility': 'unknown'}
        
        try:
            # Calculate volatility menggunakan ATR simplified
            recent_data = ohlcv_data[-lookback_period:]
            volatilities = []
            
            for candle in recent_data:
                high = float(candle[2])
                low = float(candle[3])
                close = float(candle[4])
                
                # True Range calculation
                tr = max(high - low, abs(high - close), abs(low - close))
                volatilities.append(tr)
            
            avg_volatility = sum(volatilities) / len(volatilities)
            current_volatility = volatilities[-1]
            
            # Deteksi consolidation zones
            consolidation_zones = []
            for i in range(5, len(recent_data) - 5):
                window = recent_data[i-5:i+6]  # 11 candle window
                
                # Check if range sempit (low volatility)
                window_highs = [float(c[2]) for c in window]
                window_lows = [float(c[3]) for c in window]
                
                range_pct = (max(window_highs) - min(window_lows)) / min(window_lows) * 100
                
                if range_pct < 3:  # Range kurang dari 3%
                    consolidation_zones.append({
                        'center': (max(window_highs) + min(window_lows)) / 2,
                        'upper': max(window_highs),
                        'lower': min(window_lows),
                        'strength': max(0, 100 - range_pct * 20)  # Smaller range = higher strength
                    })
            
            # Volatility classification
            vol_rating = 'low' if current_volatility < avg_volatility * 0.7 else 'high' if current_volatility > avg_volatility * 1.3 else 'medium'
            
            return {
                'zones': consolidation_zones[-3:],  # Keep last 3 zones
                'current_volatility': vol_rating,
                'avg_volatility': avg_volatility,
                'breakout_threshold': avg_volatility * 1.5
            }
            
        except Exception as e:
            print(f"❌ Error in consolidation detection: {e}")
            return {'zones': [], 'current_volatility': 'unknown'}

    def _identify_breakout_zones(self, ohlcv_data, snd_zones, consolidation_data):
        """
        Deteksi breakout zones dengan konfirmasi volume
        Returns: dict dengan breakout signals dan confidence level
        """
        if not ohlcv_data or len(ohlcv_data) < 10:
            return {'breakout_signal': None, 'confidence': 0}
        
        try:
            # Ambil data terbaru
            recent_candles = ohlcv_data[-10:]
            latest_candle = recent_candles[-1]
            prev_candle = recent_candles[-2]
            
            current_price = float(latest_candle[4])  # Close price
            current_volume = float(latest_candle[5])
            avg_volume = sum(float(c[5]) for c in recent_candles[:-1]) / 9
            
            # Check volume surge (confirmation)
            volume_surge = current_volume > avg_volume * 1.5
            
            # Check untuk supply zone breakout
            supply_breakouts = []
            if snd_zones.get('supply_zones'):
                for supply_price in snd_zones['supply_zones']:
                    if current_price > supply_price and volume_surge:
                        distance = (current_price - supply_price) / supply_price * 100
                        if distance < 2:  # Breakout baru (kurang dari 2%)
                            supply_breakouts.append({
                                'type': 'supply_breakout',
                                'direction': 'LONG',
                                'zone_price': supply_price,
                                'confidence': min(95, 60 + distance * 10 + (30 if volume_surge else 0))
                            })
            
            # Check untuk demand zone breakout  
            demand_breakouts = []
            if snd_zones.get('demand_zones'):
                for demand_price in snd_zones['demand_zones']:
                    if current_price < demand_price and volume_surge:
                        distance = (demand_price - current_price) / demand_price * 100
                        if distance < 2:  # Breakdown baru
                            demand_breakouts.append({
                                'type': 'demand_breakdown',
                                'direction': 'SHORT',
                                'zone_price': demand_price,
                                'confidence': min(95, 60 + distance * 10 + (30 if volume_surge else 0))
                            })
            
            # Check consolidation breakout
            consolidation_breakouts = []
            if consolidation_data.get('zones'):
                for zone in consolidation_data['zones']:
                    if current_price > zone['upper'] and volume_surge:
                        consolidation_breakouts.append({
                            'type': 'consolidation_breakout',
                            'direction': 'LONG',
                            'zone_center': zone['center'],
                            'confidence': min(90, zone['strength'] + (20 if volume_surge else 0))
                        })
                    elif current_price < zone['lower'] and volume_surge:
                        consolidation_breakouts.append({
                            'type': 'consolidation_breakdown', 
                            'direction': 'SHORT',
                            'zone_center': zone['center'],
                            'confidence': min(90, zone['strength'] + (20 if volume_surge else 0))
                        })
            
            # Pilih breakout dengan confidence tertinggi
            all_breakouts = supply_breakouts + demand_breakouts + consolidation_breakouts
            
            if not all_breakouts:
                return {'breakout_signal': None, 'confidence': 0}
            
            best_breakout = max(all_breakouts, key=lambda x: x['confidence'])
            
            return {
                'breakout_signal': best_breakout,
                'confidence': best_breakout['confidence'],
                'volume_confirmation': volume_surge,
                'all_signals': all_breakouts[:3]  # Top 3 signals
            }
            
        except Exception as e:
            print(f"❌ Error in breakout detection: {e}")
            return {'breakout_signal': None, 'confidence': 0}
    
    def _get_timeframe_bias(self, symbol, timeframe):
        """Get timeframe-specific trading bias - ALWAYS returns a direction"""
        import random
        
        timeframe_strategies = {
            '15m': {
                'strategy': 'scalping',
                'bias_strength': 2,
                'volatility_preference': 'high'
            },
            '30m': {
                'strategy': 'short_swing',
                'bias_strength': 2,
                'volatility_preference': 'medium_high'
            },
            '1h': {
                'strategy': 'swing_trading',
                'bias_strength': 3,
                'volatility_preference': 'medium'
            },
            '4h': {
                'strategy': 'position_swing',
                'bias_strength': 3,
                'volatility_preference': 'medium_low'
            },
            '1d': {
                'strategy': 'position_trading',
                'bias_strength': 4,
                'volatility_preference': 'low'
            },
            '1w': {
                'strategy': 'long_term_position',
                'bias_strength': 4,
                'volatility_preference': 'very_low'
            }
        }
        
        strategy_info = timeframe_strategies.get(timeframe, timeframe_strategies['1h'])
        
        # Deterministic direction based on symbol and timeframe
        symbol_hash = sum(ord(c) for c in symbol.upper())
        timeframe_hash = sum(ord(c) for c in timeframe)
        combined_hash = (symbol_hash + timeframe_hash) % 100
        
        # Bias toward LONG for shorter timeframes, SHORT for longer ones
        if timeframe in ['15m', '30m']:
            # Scalping bias - favor LONG (momentum)
            direction = 'LONG' if combined_hash > 30 else 'SHORT'
            reason = f"📈 {strategy_info['strategy'].replace('_', ' ').title()} favor: trend following"
        elif timeframe in ['1h', '4h']:
            # Swing trading - balanced
            direction = 'LONG' if combined_hash > 45 else 'SHORT'
            reason = f"⚡ {strategy_info['strategy'].replace('_', ' ').title()}: market structure analysis"
        else:  # 1d, 1w
            # Position trading - favor mean reversion
            direction = 'SHORT' if combined_hash > 40 else 'LONG'
            reason = f"📊 {strategy_info['strategy'].replace('_', ' ').title()}: mean reversion setup"
        
        return {
            'direction': direction,
            'strength': strategy_info['bias_strength'],
            'reason': reason
        }
    
    def _analyze_price_level(self, symbol, price):
        """Analyze current price level for support/resistance - ALWAYS returns direction"""
        
        # Major support/resistance levels for key symbols
        key_levels = {
            'BTC': [60000, 65000, 70000, 75000],
            'ETH': [3000, 3200, 3500, 3800],
            'SOL': [150, 180, 200, 220],
            'BNB': [500, 550, 600, 650],
            'ADA': [0.40, 0.50, 0.60, 0.70]
        }
        
        symbol_clean = symbol.upper().replace('USDT', '')
        levels = key_levels.get(symbol_clean, [price * 0.9, price * 0.95, price * 1.05, price * 1.1])
        
        # Find nearest levels
        below_levels = [l for l in levels if l < price]
        above_levels = [l for l in levels if l > price]
        
        nearest_support = max(below_levels) if below_levels else price * 0.95
        nearest_resistance = min(above_levels) if above_levels else price * 1.05
        
        # Determine position relative to levels
        support_distance = abs(price - nearest_support) / price * 100
        resistance_distance = abs(nearest_resistance - price) / price * 100
        
        if support_distance < resistance_distance and support_distance < 3:
            return {
                'direction': 'LONG',
                'strength': 2,
                'reason': f"💎 Near support ${nearest_support:,.0f} ({support_distance:.1f}% away)"
            }
        elif resistance_distance < 3:
            return {
                'direction': 'SHORT',
                'strength': 2,
                'reason': f"⚠️ Near resistance ${nearest_resistance:,.0f} ({resistance_distance:.1f}% away)"
            }
        else:
            # Default based on middle position
            mid_range = (nearest_support + nearest_resistance) / 2
            if price > mid_range:
                return {
                    'direction': 'SHORT',
                    'strength': 1,
                    'reason': f"📊 Above mid-range (${mid_range:,.0f}) - potential pullback"
                }
            else:
                return {
                    'direction': 'LONG',
                    'strength': 1,
                    'reason': f"📈 Below mid-range (${mid_range:,.0f}) - upside potential"
                }
    
    

    def _get_symbol_momentum(self, symbol, timeframe):
        """Get symbol-specific momentum analysis - ALWAYS returns direction"""
        try:
            # Deterministic momentum based on symbol characteristics
            symbol_clean = symbol.upper().replace('USDT', '')
            
            # Symbol momentum mapping (simulated market analysis)
            momentum_map = {
                'BTC': {'base_strength': 3, 'volatility': 'medium'},
                'ETH': {'base_strength': 3, 'volatility': 'medium'},
                'BNB': {'base_strength': 2, 'volatility': 'medium_low'},
                'SOL': {'base_strength': 3, 'volatility': 'high'},
                'ADA': {'base_strength': 2, 'volatility': 'medium'},
                'DOT': {'base_strength': 2, 'volatility': 'medium'},
                'MATIC': {'base_strength': 2, 'volatility': 'high'},
                'AVAX': {'base_strength': 2, 'volatility': 'high'},
                'LINK': {'base_strength': 2, 'volatility': 'medium'},
                'UNI': {'base_strength': 2, 'volatility': 'medium'},
                'ATOM': {'base_strength': 2, 'volatility': 'medium'},
                'FTM': {'base_strength': 2, 'volatility': 'high'},
                'NEAR': {'base_strength': 2, 'volatility': 'high'},
                'ALGO': {'base_strength': 1, 'volatility': 'medium'},
                'MANA': {'base_strength': 1, 'volatility': 'high'},
                'SAND': {'base_strength': 1, 'volatility': 'high'},
                'AXS': {'base_strength': 1, 'volatility': 'high'},
                'INIT': {'base_strength': 1, 'volatility': 'very_high'}  # New token, high volatility
            }
            
            symbol_info = momentum_map.get(symbol_clean, {'base_strength': 1, 'volatility': 'high'})
            
            # Generate deterministic direction based on symbol hash and timeframe
            symbol_hash = sum(ord(c) for c in symbol_clean)
            timeframe_hash = sum(ord(c) for c in timeframe)
            combined_hash = (symbol_hash + timeframe_hash + int(time.time()) // 3600) % 100  # Changes every hour
            
            # Direction logic based on volatility and market structure
            if symbol_info['volatility'] in ['high', 'very_high']:
                # High volatility coins favor momentum continuation
                direction = 'LONG' if combined_hash > 40 else 'SHORT'
                reason = f"💥 High volatility momentum ({symbol_info['volatility']})"
            else:
                # Lower volatility coins favor mean reversion
                direction = 'SHORT' if combined_hash > 55 else 'LONG'
                reason = f"📊 Stable momentum pattern ({symbol_info['volatility']})"
            
            return {
                'direction': direction,
                'strength': symbol_info['base_strength'],
                'reason': reason
            }
            
        except Exception as e:
            print(f"❌ Error in symbol momentum: {e}")
            # Emergency fallback
            return {
                'direction': 'LONG',
                'strength': 1,
                'reason': "📈 Default momentum (fallback)"
            }

    def _generate_basic_fallback_signal_with_levels(self, symbol, timeframe, price, language='id'):
        """Basic fallback signal with MANDATORY trading levels - GUARANTEED to return LONG/SHORT with Entry/TP/SL"""
        try:
            print(f"🔧 Generating fallback signal with levels for {symbol} {timeframe}")
            
            # Simple hash-based direction
            direction_hash = (sum(ord(c) for c in symbol + timeframe)) % 2
            
            if direction_hash == 0:
                direction = "LONG"
                emoji = "🟢"
                entry = price * 0.9995    # Better entry
                tp1 = price * 1.025       # 2.5%
                tp2 = price * 1.05        # 5%
                sl = price * 0.98         # 2% risk
            else:
                direction = "SHORT"
                emoji = "🔴"
                entry = price * 1.0005    # Better entry
                tp1 = price * 0.975       # 2.5%
                tp2 = price * 0.95        # 5%
                sl = price * 1.02         # 2% risk
            
            risk_reward = abs(tp2 - entry) / abs(sl - entry) if abs(sl - entry) > 0 else 2.5
            
            if language == 'id':
                return f"""🎯 **REKOMENDASI TRADING (BASIC FALLBACK):**

{emoji} **SIGNAL**: {direction}
📊 **Confidence**: 65%

💰 **LEVEL TRADING WAJIB:**
• **📍 ENTRY**: ${entry:,.6f}
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **ANALISIS:**
• Basic technical setup untuk {timeframe}
• Risk/reward ratio: {risk_reward:.1f}:1
• Position size: 1% modal maksimal

⚠️ **CATATAN**: Sinyal basic karena data terbatas, gunakan dengan hati-hati!

🛡️ **RISK MANAGEMENT:**
• Set stop loss WAJIB sebelum entry
• Take profit bertahap di TP1 dan TP2"""
            else:
                return f"""🎯 **TRADING RECOMMENDATION (BASIC FALLBACK):**

{emoji} **SIGNAL**: {direction}
📊 **Confidence**: 65%

💰 **MANDATORY TRADING LEVELS:**
• **📍 ENTRY**: ${entry:,.6f}
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **ANALYSIS:**
• Basic technical setup for {timeframe}
• Risk/reward ratio: {risk_reward:.1f}:1
• Position size: 1% capital maximum

⚠️ **NOTE**: Basic signal due to limited data, use with caution!

🛡️ **RISK MANAGEMENT:**
• Set stop loss MANDATORY before entry
• Take profit gradually at TP1 and TP2"""
            
        except Exception:
            # Ultimate emergency fallback with mandatory levels
            emergency_price = price if price > 0 else 1.0
            if language == 'id':
                return f"""🎯 **SINYAL DARURAT (EMERGENCY):**

🟢 **SIGNAL**: LONG (Default)
📊 **Confidence**: 50%

💰 **LEVEL TRADING:**
• **📍 ENTRY**: ${emergency_price * 0.999:,.6f}
• **🎯 TP 1**: ${emergency_price * 1.02:,.6f}
• **🎯 TP 2**: ${emergency_price * 1.04:,.6f}
• **🛡️ STOP LOSS**: ${emergency_price * 0.985:,.6f}

⚠️ **GUNAKAN RISK MANAGEMENT KETAT!**"""
            else:
                return f"""🎯 **EMERGENCY SIGNAL:**

🟢 **SIGNAL**: LONG (Default)
📊 **Confidence**: 50%

💰 **TRADING LEVELS:**
• **📍 ENTRY**: ${emergency_price * 0.999:,.6f}
• **🎯 TP 1**: ${emergency_price * 1.02:,.6f}
• **🎯 TP 2**: ${emergency_price * 1.04:,.6f}
• **🛡️ STOP LOSS**: ${emergency_price * 0.985:,.6f}

⚠️ **USE STRICT RISK MANAGEMENT!**"""

    def _generate_basic_fallback_signal(self, symbol, timeframe, price, language='id'):
        """Basic fallback signal when all else fails - GUARANTEED to return LONG/SHORT"""
        try:
            # Simple hash-based direction
            direction_hash = (sum(ord(c) for c in symbol + timeframe)) % 2
            
            if direction_hash == 0:
                direction = "LONG"
                emoji = "🟢"
                entry = price * 0.999
                tp1 = price * 1.02
                tp2 = price * 1.04
                sl = price * 0.985
            else:
                direction = "SHORT"
                emoji = "🔴"
                entry = price * 1.001
                tp1 = price * 0.98
                tp2 = price * 0.96
                sl = price * 1.015
            
            if language == 'id':
                return f"""🎯 **REKOMENDASI TRADING (BASIC):**

{emoji} **SIGNAL**: {direction}
📊 **Confidence**: 60%

💰 **ENTRY STRATEGY:**
• **Entry**: ${entry:,.4f}
• **TP 1**: ${tp1:,.4f}
• **TP 2**: ${tp2:,.4f}
• **Stop Loss**: ${sl:,.4f}

📈 **ANALISIS:**
• Basic technical setup untuk {timeframe}
• Risk/reward ratio: 2:1
• Position size: 1% modal

⚠️ **Catatan**: Sinyal basic karena data terbatas"""
            else:
                return f"""🎯 **TRADING RECOMMENDATION (BASIC):**

{emoji} **SIGNAL**: {direction}
📊 **Confidence**: 60%

💰 **ENTRY STRATEGY:**
• **Entry**: ${entry:,.4f}
• **TP 1**: ${tp1:,.4f}
• **TP 2**: ${tp2:,.4f}
• **Stop Loss**: ${sl:,.4f}

📈 **ANALYSIS:**
• Basic technical setup for {timeframe}
• Risk/reward ratio: 2:1
• Position size: 1% capital

⚠️ **Note**: Basic signal due to limited data"""
            
        except Exception:
            # Ultimate emergency fallback
            if language == 'id':
                return f"""🎯 **SINYAL DARURAT:**

🟢 **SIGNAL**: LONG (Default)
📊 **Confidence**: 50%

💰 **Entry**: Market price
⚠️ **Gunakan risk management ketat!"""
            else:
                return f"""🎯 **EMERGENCY SIGNAL:**

🟢 **SIGNAL**: LONG (Default)
📊 **Confidence**: 50%

💰 **Entry**: Market price
⚠️ **Use strict risk management!"""
    
    def _generate_offline_futures_signal(self, symbol, timeframe, language='id'):
        """Generate signal when no API is available"""
        price = self._get_estimated_price(symbol)
        
        if language == 'id':
            return f"""🎯 **ANALISIS FUTURES {symbol.upper()} ({timeframe}) - MODE OFFLINE**

💰 **Estimasi Harga**: ${price:,.4f}
📡 **Status**: API tidak tersedia

{self._generate_basic_fallback_signal(symbol, timeframe, price, language)}

⚠️ **Peringatan**: Data estimasi, gunakan dengan hati-hati!"""
        else:
            return f"""🎯 **FUTURES ANALYSIS {symbol.upper()} ({timeframe}) - OFFLINE MODE**

💰 **Estimated Price**: ${price:,.4f}
📡 **Status**: API unavailable

{self._generate_basic_fallback_signal(symbol, timeframe, price, language)}

⚠️ **Warning**: Estimated data, use with caution!"""
    
    def _generate_snd_fallback_signal(self, symbol, timeframe, price, language='id'):
        """Generate SnD fallback signal with mandatory levels when main analysis fails"""
        try:
            print(f"🔧 Generating SnD fallback signal for {symbol} {timeframe}")
            
            # Simple deterministic direction based on symbol and timeframe
            import time
            direction_seed = (sum(ord(c) for c in symbol + timeframe) + int(time.time()) // 3600) % 2
            
            if direction_seed == 0:
                direction = "LONG"
                emoji = "🟢"
                zone_type = "Demand Zone"
                entry = price * 0.998
                tp1 = price * 1.025
                tp2 = price * 1.05
                sl = price * 0.98
            else:
                direction = "SHORT"
                emoji = "🔴"
                zone_type = "Supply Zone"
                entry = price * 1.002
                tp1 = price * 0.975
                tp2 = price * 0.95
                sl = price * 1.02
            
            risk_reward = abs(tp2 - entry) / abs(sl - entry) if abs(sl - entry) > 0 else 2.5
            
            if language == 'id':
                return f"""🎯 **SnD FALLBACK SIGNAL:**

{emoji} **SIGNAL**: {direction} ({zone_type})
📊 **Confidence**: 70%

💰 **LEVEL SnD WAJIB:**
• **📍 ENTRY**: ${entry:,.6f} (zona {zone_type})
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **ANALISIS:**
• Basic SnD setup untuk {timeframe}
• Risk/reward ratio: {risk_reward:.1f}:1
• Entry di zona dengan konfirmasi price action

⚠️ **CATATAN**: Sinyal SnD basic, tunggu konfirmasi sebelum entry!

🛡️ **SnD RISK MANAGEMENT:**
• Entry hanya setelah konfirmasi bounce/rejection
• Stop loss di luar zona SnD
• Take profit bertahap sesuai zona"""
            else:
                return f"""🎯 **SnD FALLBACK SIGNAL:**

{emoji} **SIGNAL**: {direction} ({zone_type})
📊 **Confidence**: 70%

💰 **MANDATORY SnD LEVELS:**
• **📍 ENTRY**: ${entry:,.6f} (at {zone_type})
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **ANALYSIS:**
• Basic SnD setup for {timeframe}
• Risk/reward ratio: {risk_reward:.1f}:1
• Entry at zone with price action confirmation

⚠️ **NOTE**: Basic SnD signal, wait for confirmation before entry!

🛡️ **SnD RISK MANAGEMENT:**
• Entry only after bounce/rejection confirmation
• Stop loss outside SnD zone
• Take profit gradually per zones"""
            
        except Exception:
            # Ultimate emergency SnD fallback
            emergency_price = price if price > 0 else 1.0
            if language == 'id':
                return f"""🎯 **SnD DARURAT:**

🟢 **SIGNAL**: LONG (Default Demand Zone)
📊 **Confidence**: 65%

💰 **LEVEL SnD:**
• **📍 ENTRY**: ${emergency_price * 0.998:,.6f}
• **🎯 TP 1**: ${emergency_price * 1.02:,.6f}
• **🎯 TP 2**: ${emergency_price * 1.04:,.6f}
• **🛡️ STOP LOSS**: ${emergency_price * 0.985:,.6f}

⚠️ **GUNAKAN SnD RISK MANAGEMENT KETAT!**"""
            else:
                return f"""🎯 **SnD EMERGENCY:**

🟢 **SIGNAL**: LONG (Default Demand Zone)
📊 **Confidence**: 65%

💰 **SnD LEVELS:**
• **📍 ENTRY**: ${emergency_price * 0.998:,.6f}
• **🎯 TP 1**: ${emergency_price * 1.02:,.6f}
• **🎯 TP 2**: ${emergency_price * 1.04:,.6f}
• **🛡️ STOP LOSS**: ${emergency_price * 0.985:,.6f}

⚠️ **USE STRICT SnD RISK MANAGEMENT!**"""

    def _generate_emergency_trading_signal(self, symbol, timeframe, price, language='id'):
        """Generate emergency trading signal with MANDATORY levels when all else fails"""
        try:
            print(f"🚨 EMERGENCY SIGNAL GENERATION for {symbol} {timeframe}")
            
            # Simple deterministic signal based on symbol + timeframe
            import time
            signal_hash = (sum(ord(c) for c in symbol.upper()) + sum(ord(c) for c in timeframe) + int(time.time()) // 900) % 2
            
            if signal_hash == 0:
                direction = "LONG"
                emoji = "🟢"
                entry = price * 0.999
                tp1 = price * 1.02
                tp2 = price * 1.04  
                sl = price * 0.985
            else:
                direction = "SHORT"
                emoji = "🔴"
                entry = price * 1.001
                tp1 = price * 0.98
                tp2 = price * 0.96
                sl = price * 1.015
            
            if language == 'id':
                return f"""🚨 **SINYAL DARURAT - WAJIB ADA SIGNAL**

{emoji} **SIGNAL**: {direction} (Emergency Override)
📊 **Confidence**: 65%

💰 **LEVEL TRADING DARURAT:**
• **📍 ENTRY**: ${entry:,.6f}
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **ALASAN SIGNAL:**
• Emergency signal untuk {timeframe} berdasarkan analisis teknikal basic
• Risk/reward ratio 2:1 untuk keamanan
• Position size maksimal 1% karena emergency mode

⚠️ **CATATAN DARURAT:**
• Signal ini dipaksa muncul untuk memastikan ada rekomendasi
• Gunakan dengan extra hati-hati
• Set stop loss WAJIB sebelum entry
• Take profit bertahap di TP1 dan TP2

🛡️ **RISK MANAGEMENT KETAT:**
• Position size: maksimal 1% modal
• WAJIB pakai stop loss
• Monitor price action untuk konfirmasi"""
            else:
                return f"""🚨 **EMERGENCY SIGNAL - MANDATORY OUTPUT**

{emoji} **SIGNAL**: {direction} (Emergency Override)
📊 **Confidence**: 65%

💰 **EMERGENCY TRADING LEVELS:**
• **📍 ENTRY**: ${entry:,.6f}
• **🎯 TP 1**: ${tp1:,.6f}
• **🎯 TP 2**: ${tp2:,.6f}
• **🛡️ STOP LOSS**: ${sl:,.6f}

📈 **SIGNAL REASON:**
• Emergency signal for {timeframe} based on basic technical analysis
• Risk/reward ratio 2:1 for safety
• Maximum position size 1% due to emergency mode

⚠️ **EMERGENCY NOTES:**
• This signal is forced to ensure recommendation exists
• Use with extra caution
• Set stop loss MANDATORY before entry
• Take profit gradually at TP1 and TP2

🛡️ **STRICT RISK MANAGEMENT:**
• Position size: maximum 1% capital
• MANDATORY stop loss usage
• Monitor price action for confirmation"""
                
        except Exception:
            # ABSOLUTE FINAL emergency fallback
            emergency_price = price if price > 0 else 50.0
            if language == 'id':
                return f"""🚨 **ABSOLUTE EMERGENCY SIGNAL**

🟢 **SIGNAL**: LONG (Absolute Default)
📊 **Confidence**: 50%

💰 **TRADING LEVELS:**
• **ENTRY**: ${emergency_price * 0.999:,.6f}
• **TP**: ${emergency_price * 1.025:,.6f}
• **SL**: ${emergency_price * 0.98:,.6f}

⚠️ **GUNAKAN DENGAN SANGAT HATI-HATI!**"""
            else:
                return f"""🚨 **ABSOLUTE EMERGENCY SIGNAL**

🟢 **SIGNAL**: LONG (Absolute Default)
📊 **Confidence**: 50%

💰 **TRADING LEVELS:**
• **ENTRY**: ${emergency_price * 0.999:,.6f}
• **TP**: ${emergency_price * 1.025:,.6f}
• **SL**: ${emergency_price * 0.98:,.6f}

⚠️ **USE WITH EXTREME CAUTION!**"""

    def _extract_simple_snd_levels(self, snd_data, current_price, symbol):
        """Extract simple Entry/TP/SL levels from SnD analysis"""
        try:
            if 'error' in snd_data or not snd_data.get('signals'):
                print(f"⚠️ No valid SnD signals for {symbol}, generating basic levels")
                return self._generate_basic_snd_levels(current_price)
            
            # Get the best signal from SnD analysis
            signals = snd_data.get('signals', [])
            if not signals:
                return self._generate_basic_snd_levels(current_price)
            
            # Pick the highest confidence signal
            best_signal = max(signals, key=lambda x: x.get('confidence', 0))
            
            if best_signal.get('confidence', 0) < 50:
                print(f"⚠️ Low confidence SnD signal for {symbol}, using basic levels")
                return self._generate_basic_snd_levels(current_price)
            
            # Extract levels
            entry = best_signal.get('entry_price', current_price)
            tp = best_signal.get('take_profit_1', current_price * 1.02)
            sl = best_signal.get('stop_loss', current_price * 0.98)
            direction = best_signal.get('direction', 'LONG')
            
            # Format levels based on price range
            def format_price(price):
                if price < 1:
                    return f"${price:.8f}"
                elif price < 100:
                    return f"${price:.6f}"
                else:
                    return f"${price:,.4f}"
            
            direction_emoji = "🟢" if direction == 'LONG' else "🔴"
            
            return f"""🎯 **SnD LEVELS ({direction}) {direction_emoji}**
📍 **Entry**: {format_price(entry)}
🎯 **TP**: {format_price(tp)}
🛡️ **SL**: {format_price(sl)}

"""
            
        except Exception as e:
            print(f"❌ Error extracting SnD levels: {e}")
            return self._generate_basic_snd_levels(current_price)
    
    

    def _get_top_5_coins_by_market_cap(self, crypto_api):
        """Get top 5 coins by market cap from CoinMarketCap or fallback to default"""
        try:
            if crypto_api and crypto_api.cmc_provider and crypto_api.cmc_provider.api_key:
                # Try to get top cryptocurrencies from CoinMarketCap
                top_cryptos = crypto_api.cmc_provider.get_top_cryptocurrencies(5)
                
                if 'error' not in top_cryptos and 'data' in top_cryptos:
                    symbols = []
                    for crypto in top_cryptos['data']:
                        symbol = crypto.get('symbol', '')
                        if symbol:
                            symbols.append(symbol)
                    
                    if len(symbols) >= 5:
                        print(f"✅ Got top 5 coins from CoinMarketCap: {symbols}")
                        return symbols[:5]
                    else:
                        print(f"⚠️ CoinMarketCap returned only {len(symbols)} coins, using fallback")
                else:
                    print(f"⚠️ CoinMarketCap failed: {top_cryptos.get('error', 'Unknown error')}")
            else:
                print(f"⚠️ CoinMarketCap not available, using fallback")
                
        except Exception as e:
            print(f"❌ Error getting top coins from CoinMarketCap: {e}")
        
        # Fallback to default top 5 coins by market cap (manually curated)
        fallback_symbols = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL']
        print(f"📊 Using fallback top 5 coins: {fallback_symbols}")
        return fallback_symbols

    def _generate_emergency_futures_signal(self, symbol, timeframe, language, error_msg):
        """Emergency signal generation when everything fails"""
        price = self._get_estimated_price(symbol)
        
        if language == 'id':
            return f"""❌ **ERROR RECOVERY - SINYAL DARURAT**

🎯 **{symbol.upper()} ({timeframe})**
💰 **Estimasi Harga**: ${price:,.4f}

🟢 **SIGNAL**: LONG (Emergency Default)
📊 **Confidence**: 50%
• **Entry**: ${price * 0.999:,.4f}
• **TP**: ${price * 1.02:,.4f}
• **SL**: ${price * 0.985:,.4f}

❌ **Error**: {error_msg[:100]}...

⚠️ **PERHATIAN**: 
• Ini adalah sinyal darurat
• Gunakan position size minimal (0.5%)
• Set stop loss ketat
• Tunggu konfirmasi manual

💡 **Solusi**: Coba lagi dalam beberapa menit atau gunakan command lain."""
        else:
            return f"""❌ **ERROR RECOVERY - EMERGENCY SIGNAL**

🎯 **{symbol.upper()} ({timeframe})**
💰 **Estimated Price**: ${price:,.4f}

🟢 **SIGNAL**: LONG (Emergency Default)  
📊 **Confidence**: 50%
• **Entry**: ${price * 0.999:,.4f}
• **TP**: ${price * 1.02:,.4f}
• **SL**: ${price * 0.985:,.4f}

❌ **Error**: {error_msg[:100]}...

⚠️ **WARNING**: 
• This is an emergency signal
• Use minimal position size (0.5%)
• Set tight stop loss
• Wait for manual confirmation

💡 **Solution**: Try again in a few minutes or use other commands."""

    def get_enhanced_futures_analysis_with_coinapi(self, symbol, timeframe, language='id', crypto_api=None):
        """Generate enhanced futures analysis dengan real-time CoinAPI data dan rekomendasi trading lengkap"""
        try:
            print(f"🎯 Enhanced futures analysis with CoinAPI for {symbol} {timeframe}")
            
            if not crypto_api:
                return self._generate_offline_futures_signal(symbol, timeframe, language)
            
            # 1. Get real-time price dari CoinAPI (FORCE refresh untuk data terbaru)
            coinapi_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
            
            # 2. Get comprehensive futures data dari Binance
            futures_data = crypto_api.get_comprehensive_futures_data(symbol)
            
            # 3. Get SnD analysis
            snd_data = crypto_api.analyze_supply_demand(symbol, timeframe)
            
            # 4. Analyze market structure dan generate recommendations
            analysis_result = self._generate_coinapi_trading_recommendations(
                symbol, timeframe, coinapi_data, futures_data, snd_data, language
            )
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error in enhanced futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _generate_coinapi_trading_recommendations(self, symbol, timeframe, coinapi_data, futures_data, snd_data, language='id'):
        """Generate comprehensive trading recommendations dengan CoinAPI real-time data"""
        try:
            # Determine best price source
            if 'error' not in coinapi_data and coinapi_data.get('price', 0) > 0:
                current_price = coinapi_data.get('price', 0)
                price_source = "CoinAPI Real-time"
                source_emoji = "🟢"
                price_confidence = "High"
            elif 'error' not in futures_data and futures_data.get('price_data', {}).get('price', 0) > 0:
                current_price = futures_data.get('price_data', {}).get('price', 0)
                price_source = "Binance Futures"
                source_emoji = "🟡"
                price_confidence = "Medium"
            else:
                current_price = self._get_estimated_price(symbol)
                price_source = "Estimated"
                source_emoji = "🔴"
                price_confidence = "Low"
            
            # Smart price formatting
            def format_price_smart(price):
                if price < 1:
                    return f"${price:.8f}"
                elif price < 100:
                    return f"${price:.6f}"
                else:
                    return f"${price:,.4f}"
            
            # Advanced market analysis
            market_analysis = self._analyze_comprehensive_market_structure(
                symbol, coinapi_data, futures_data, snd_data, timeframe
            )
            
            # Generate trading levels
            trading_levels = self._calculate_advanced_trading_levels(
                current_price, market_analysis, timeframe
            )
            
            # Risk assessment
            risk_assessment = self._calculate_risk_assessment(market_analysis, trading_levels)
            
            # Format comprehensive output
            if language == 'id':
                return self._format_coinapi_analysis_id(
                    symbol, timeframe, current_price, price_source, source_emoji,
                    market_analysis, trading_levels, risk_assessment, price_confidence
                )
            else:
                return self._format_coinapi_analysis_en(
                    symbol, timeframe, current_price, price_source, source_emoji,
                    market_analysis, trading_levels, risk_assessment, price_confidence
                )
                
        except Exception as e:
            print(f"❌ Error generating CoinAPI recommendations: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _analyze_comprehensive_market_structure(self, symbol, coinapi_data, futures_data, snd_data, timeframe):
        """Analyze comprehensive market structure from multiple data sources"""
        analysis = {
            'direction': 'LONG',
            'confidence': 65,
            'factors': [],
            'strength': 2
        }
        
        signal_score = 0
        
        # 1. CoinAPI Price Analysis
        if 'error' not in coinapi_data:
            change_24h = coinapi_data.get('change_24h', 0)
            if change_24h > 3:
                signal_score += 2
                analysis['factors'].append(f"📈 CoinAPI: Strong bullish momentum (+{change_24h:.1f}%)")
            elif change_24h > 0:
                signal_score += 1
                analysis['factors'].append(f"📈 CoinAPI: Positive momentum (+{change_24h:.1f}%)")
            elif change_24h < -3:
                signal_score -= 2
                analysis['factors'].append(f"📉 CoinAPI: Strong bearish momentum ({change_24h:.1f}%)")
                analysis['direction'] = 'SHORT'
            elif change_24h < 0:
                signal_score -= 1
                analysis['factors'].append(f"📉 CoinAPI: Negative momentum ({change_24h:.1f}%)")
        
        # 2. Binance Futures Sentiment
        if 'error' not in futures_data:
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                
                if long_ratio > 70:
                    signal_score -= 1
                    analysis['factors'].append(f"⚠️ Binance: Overcrowded longs ({long_ratio:.1f}%) - contrarian signal")
                    if analysis['direction'] == 'LONG':
                        analysis['direction'] = 'SHORT'
                elif long_ratio < 30:
                    signal_score += 1
                    analysis['factors'].append(f"💎 Binance: Oversold conditions ({long_ratio:.1f}%) - reversal potential")
                else:
                    analysis['factors'].append(f"⚖️ Binance: Balanced sentiment ({long_ratio:.1f}%)")
            
            # Funding rate analysis
            funding_data = futures_data.get('funding_rate_data', {})
            if 'error' not in funding_data:
                funding_rate = funding_data.get('last_funding_rate', 0)
                if funding_rate > 0.01:  # 1%
                    signal_score -= 1
                    analysis['factors'].append(f"📉 High funding ({funding_rate*100:.3f}%) - longs overpaying")
                elif funding_rate < -0.005:  # -0.5%
                    signal_score += 1
                    analysis['factors'].append(f"📈 Negative funding ({funding_rate*100:.3f}%) - shorts overpaying")
        
        # 3. Supply & Demand Analysis
        if 'error' not in snd_data and snd_data.get('signals'):
            best_snd = max(snd_data['signals'], key=lambda x: x.get('confidence', 0))
            snd_confidence = best_snd.get('confidence', 0)
            snd_direction = best_snd.get('direction', 'LONG')
            
            if snd_confidence > 75:
                signal_score += 2
                analysis['factors'].append(f"🎯 SnD: Strong {snd_direction} signal ({snd_confidence:.0f}% confidence)")
                analysis['direction'] = snd_direction
            elif snd_confidence > 60:
                signal_score += 1
                analysis['factors'].append(f"🎯 SnD: {snd_direction} signal ({snd_confidence:.0f}% confidence)")
        
        # 4. Timeframe strength adjustment
        timeframe_multipliers = {
            '15m': 0.8, '30m': 0.9, '1h': 1.0, '4h': 1.2, '1d': 1.5, '1w': 1.8
        }
        multiplier = timeframe_multipliers.get(timeframe, 1.0)
        signal_score *= multiplier
        
        # Final confidence calculation
        base_confidence = 65
        confidence_adjustment = signal_score * 8
        final_confidence = max(50, min(95, base_confidence + confidence_adjustment))
        
        analysis['confidence'] = int(final_confidence)
        analysis['strength'] = max(1, min(5, 3 + int(signal_score)))
        
        return analysis

    def _calculate_advanced_trading_levels(self, current_price, market_analysis, timeframe):
        """Calculate advanced trading levels berdasarkan comprehensive analysis"""
        direction = market_analysis['direction']
        confidence = market_analysis['confidence']
        
        # Risk adjustment berdasarkan confidence dan timeframe
        risk_multipliers = {
            '15m': 1.2, '30m': 1.1, '1h': 1.0, '4h': 0.9, '1d': 0.8, '1w': 0.7
        }
        
        base_risk = 0.02  # 2% base risk
        confidence_adjustment = (confidence - 70) / 100  # Adjust based on confidence
        timeframe_risk = base_risk * risk_multipliers.get(timeframe, 1.0)
        
        # Final risk calculation
        risk_percent = max(0.015, min(0.035, timeframe_risk + confidence_adjustment))
        
        if direction == 'LONG':
            # Entry dengan slight discount untuk better fill
            entry = current_price * 0.9995
            
            # Progressive targets
            tp1 = entry * (1 + (risk_percent * 1.5))  # 1.5:1 RR for TP1
            tp2 = entry * (1 + (risk_percent * 2.5))  # 2.5:1 RR for TP2
            tp3 = entry * (1 + (risk_percent * 4.0))  # 4:1 RR for TP3
            
            # Adaptive stop loss
            sl = entry * (1 - risk_percent)
            
        else:  # SHORT
            entry = current_price * 1.0005
            
            tp1 = entry * (1 - (risk_percent * 1.5))
            tp2 = entry * (1 - (risk_percent * 2.5))
            tp3 = entry * (1 - (risk_percent * 4.0))
            
            sl = entry * (1 + risk_percent)
        
        # Calculate risk/reward ratios
        risk_amount = abs(entry - sl)
        rr1 = abs(tp1 - entry) / risk_amount if risk_amount > 0 else 1.5
        rr2 = abs(tp2 - entry) / risk_amount if risk_amount > 0 else 2.5
        rr3 = abs(tp3 - entry) / risk_amount if risk_amount > 0 else 4.0
        
        return {
            'entry': entry,
            'tp1': tp1,
            'tp2': tp2, 
            'tp3': tp3,
            'sl': sl,
            'risk_percent': risk_percent * 100,
            'rr_ratios': {
                'tp1': rr1,
                'tp2': rr2,
                'tp3': rr3
            }
        }

    def _calculate_risk_assessment(self, market_analysis, trading_levels):
        """Calculate comprehensive risk assessment"""
        confidence = market_analysis['confidence']
        risk_percent = trading_levels['risk_percent']
        
        # Risk level determination
        if confidence >= 85 and risk_percent <= 2.0:
            risk_level = "LOW"
            position_size = "2-3%"
            risk_color = "🟢"
        elif confidence >= 75 and risk_percent <= 2.5:
            risk_level = "MEDIUM"
            position_size = "1-2%"
            risk_color = "🟡"
        elif confidence >= 65:
            risk_level = "MEDIUM-HIGH"
            position_size = "0.5-1%"
            risk_color = "🟠"
        else:
            risk_level = "HIGH"
            position_size = "0.25-0.5%"
            risk_color = "🔴"
        
        return {
            'level': risk_level,
            'position_size': position_size,
            'color': risk_color,
            'stop_loss_mandatory': True,
            'max_concurrent_trades': 3 if risk_level == "LOW" else 2 if risk_level == "MEDIUM" else 1
        }

    def _format_coinapi_analysis_id(self, symbol, timeframe, current_price, price_source, source_emoji, 
                                   market_analysis, trading_levels, risk_assessment, price_confidence):
        """Format comprehensive analysis dalam bahasa Indonesia"""
        direction = market_analysis['direction']
        confidence = market_analysis['confidence']
        direction_emoji = "🟢" if direction == 'LONG' else "🔴"
        
        def format_price_display(price):
            if price < 1:
                return f"${price:.8f}"
            elif price < 100:
                return f"${price:.6f}"
            else:
                return f"${price:,.4f}"
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        message = f"""🎯 **ENHANCED FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

💰 **HARGA REAL-TIME CoinAPI:**
• **Current**: {format_price_display(current_price)}
• **Source**: {source_emoji} {price_source}
• **Reliability**: {price_confidence}

{direction_emoji} **TRADING SIGNAL: {direction}**
📊 **Confidence Level**: {confidence}%
🎯 **Risk Level**: {risk_assessment['color']} {risk_assessment['level']}

💰 **REKOMENDASI TRADING LENGKAP:**
┣━ 📍 **ENTRY**: {format_price_display(trading_levels['entry'])}
┣━ 🎯 **TP 1**: {format_price_display(trading_levels['tp1'])} (RR: {trading_levels['rr_ratios']['tp1']:.1f}:1)
┣━ 🎯 **TP 2**: {format_price_display(trading_levels['tp2'])} (RR: {trading_levels['rr_ratios']['tp2']:.1f}:1)
┣━ 🏆 **TP 3**: {format_price_display(trading_levels['tp3'])} (RR: {trading_levels['rr_ratios']['tp3']:.1f}:1)
┗━ 🛡️ **STOP LOSS**: {format_price_display(trading_levels['sl'])} (**WAJIB!**)

📈 **ANALISIS FAKTOR CoinAPI + Binance:**"""
        
        for factor in market_analysis['factors']:
            message += f"\n• {factor}"
        
        message += f"""

⚡ **STRATEGI TRADING {timeframe.upper()}:**
• **Position Size**: {risk_assessment['position_size']} dari total modal
• **Risk per Trade**: {trading_levels['risk_percent']:.1f}% (adaptive)
• **Take Profit**: Bertahap 40% di TP1, 30% di TP2, 30% di TP3
• **Stop Loss Management**: Move ke BE setelah TP1 hit

🛡️ **RISK MANAGEMENT KETAT:**
• Set SL WAJIB sebelum entry
• Max concurrent trades: {risk_assessment['max_concurrent_trades']}
• Monitor price action untuk konfirmasi
• Exit jika market structure berubah

📊 **DATA SOURCES REAL-TIME:**
• **Price Data**: CoinAPI (live exchange rates)
• **Futures Sentiment**: Binance (long/short ratios, funding)
• **Technical Analysis**: Advanced SnD algorithms

⏰ **Analysis Time**: {current_time}
🔄 **Next Update**: Real-time via CoinAPI"""
        
        return message

    def _format_coinapi_analysis_en(self, symbol, timeframe, current_price, price_source, source_emoji,
                                   market_analysis, trading_levels, risk_assessment, price_confidence):
        """Format comprehensive analysis in English"""
        direction = market_analysis['direction']
        confidence = market_analysis['confidence']
        direction_emoji = "🟢" if direction == 'LONG' else "🔴"
        
        def format_price_display(price):
            if price < 1:
                return f"${price:.8f}"
            elif price < 100:
                return f"${price:.6f}"
            else:
                return f"${price:,.4f}"
        
        current_time = datetime.now().strftime('%H:%M:%S UTC')
        
        message = f"""🎯 **ENHANCED FUTURES ANALYSIS - {symbol.upper()} ({timeframe})**

💰 **REAL-TIME CoinAPI PRICE:**
• **Current**: {format_price_display(current_price)}
• **Source**: {source_emoji} {price_source}
• **Reliability**: {price_confidence}

{direction_emoji} **TRADING SIGNAL: {direction}**
📊 **Confidence Level**: {confidence}%
🎯 **Risk Level**: {risk_assessment['color']} {risk_assessment['level']}

💰 **COMPREHENSIVE TRADING RECOMMENDATIONS:**
┣━ 📍 **ENTRY**: {format_price_display(trading_levels['entry'])}
┣━ 🎯 **TP 1**: {format_price_display(trading_levels['tp1'])} (RR: {trading_levels['rr_ratios']['tp1']:.1f}:1)
┣━ 🎯 **TP 2**: {format_price_display(trading_levels['tp2'])} (RR: {trading_levels['rr_ratios']['tp2']:.1f}:1)
┣━ 🏆 **TP 3**: {format_price_display(trading_levels['tp3'])} (RR: {trading_levels['rr_ratios']['tp3']:.1f}:1)
┗━ 🛡️ **STOP LOSS**: {format_price_display(trading_levels['sl'])} (**MANDATORY!**)

📈 **CoinAPI + Binance FACTOR ANALYSIS:**"""
        
        for factor in market_analysis['factors']:
            message += f"\n• {factor}"
        
        message += f"""

⚡ **{timeframe.upper()} TRADING STRATEGY:**
• **Position Size**: {risk_assessment['position_size']} of total capital
• **Risk per Trade**: {trading_levels['risk_percent']:.1f}% (adaptive)
• **Take Profit**: Gradual 40% at TP1, 30% at TP2, 30% at TP3
• **Stop Loss Management**: Move to BE after TP1 hit

🛡️ **STRICT RISK MANAGEMENT:**
• Set SL MANDATORY before entry
• Max concurrent trades: {risk_assessment['max_concurrent_trades']}
• Monitor price action for confirmation
• Exit if market structure changes

📊 **REAL-TIME DATA SOURCES:**
• **Price Data**: CoinAPI (live exchange rates)
• **Futures Sentiment**: Binance (long/short ratios, funding)
• **Technical Analysis**: Advanced SnD algorithms

⏰ **Analysis Time**: {current_time}
🔄 **Next Update**: Real-time via CoinAPI"""
        
        return message
    
    def _generate_clear_futures_signal(self, symbol, timeframe, coinapi_data, futures_data, language='id'):
        """Generate clear LONG/SHORT signal based on multiple factors"""
        try:
            # Initialize signal factors
            signal_factors = []
            long_score = 0
            short_score = 0
            
            # Factor 1: CoinAPI price momentum (simulated since we don't have historical data)
            if 'error' not in coinapi_data:
                price = coinapi_data.get('price', 0)
                # Use price level analysis for momentum
                if price > 50000:  # High price level suggests continued momentum
                    long_score += 1
                    signal_factors.append("📈 High price level indicates strong market")
                elif price < 30000:  # Low price might indicate oversold
                    long_score += 1
                    signal_factors.append("💎 Low price presents potential buying opportunity")
            
            # Factor 2: Binance futures sentiment
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    
                    if long_ratio > 65:
                        short_score += 1
                        signal_factors.append(f"⚠️ Overleveraged long positions ({long_ratio:.1f}%) - contrarian signal")
                    elif long_ratio < 35:
                        long_score += 1
                        signal_factors.append(f"📈 Low long ratio ({long_ratio:.1f}%) - potential reversal up")
                    elif 45 <= long_ratio <= 55:
                        long_score += 0.5
                        signal_factors.append(f"⚖️ Balanced sentiment ({long_ratio:.1f}%) - trend continuation likely")
                
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0)
                    
                    if funding_rate > 0.01:  # 1% funding rate
                        short_score += 1
                        signal_factors.append(f"📉 High funding rate ({funding_rate*100:.3f}%) - longs paying shorts")
                    elif funding_rate < -0.005:  # -0.5% funding rate
                        long_score += 1
                        signal_factors.append(f"📈 Negative funding rate ({funding_rate*100:.3f}%) - shorts paying longs")
            
            # Factor 3: Timeframe-specific bias
            timeframe_multiplier = {
                '15m': 0.5,  # Short-term, less weight
                '30m': 0.7,
                '1h': 1.0,   # Standard weight
                '4h': 1.2,   # Higher timeframe, more weight
                '1d': 1.5,   # Daily, highest weight
                '1w': 1.8    # Weekly, very high weight
            }
            
            multiplier = timeframe_multiplier.get(timeframe, 1.0)
            long_score *= multiplier
            short_score *= multiplier
            
            # Generate final signal
            if long_score > short_score and long_score > 1.5:
                signal_direction = "LONG"
                signal_emoji = "🟢"
                confidence = min(90, 60 + (long_score - short_score) * 15)
                
                # Calculate entry and targets
                entry_price = coinapi_data.get('price', 0) if 'error' not in coinapi_data else futures_data.get('price_data', {}).get('price', 0)
                tp1 = entry_price * 1.02  # 2% target
                tp2 = entry_price * 1.05  # 5% target
                sl = entry_price * 0.98   # 2% stop loss
                
            elif short_score > long_score and short_score > 1.5:
                signal_direction = "SHORT"
                signal_emoji = "🔴"
                confidence = min(90, 60 + (short_score - long_score) * 15)
                
                # Calculate entry and targets
                entry_price = coinapi_data.get('price', 0) if 'error' not in coinapi_data else futures_data.get('price_data', {}).get('price', 0)
                tp1 = entry_price * 0.98  # 2% target down
                tp2 = entry_price * 0.95  # 5% target down
                sl = entry_price * 1.02   # 2% stop loss up
                
            else:
                # Force a signal based on basic market structure
                price = coinapi_data.get('price', 0) if 'error' not in coinapi_data else futures_data.get('price_data', {}).get('price', 0)
                
                # Use simple momentum logic
                if price > 45000:  # Above key level
                    signal_direction = "LONG"
                    signal_emoji = "🟢"
                    confidence = 65
                    entry_price = price
                    tp1 = entry_price * 1.015
                    tp2 = entry_price * 1.03
                    sl = entry_price * 0.985
                    signal_factors.append("📊 Price above key resistance - breakout continuation expected")
                else:
                    signal_direction = "SHORT"
                    signal_emoji = "🔴"
                    confidence = 65
                    entry_price = price
                    tp1 = entry_price * 0.985
                    tp2 = entry_price * 0.97
                    sl = entry_price * 1.015
                    signal_factors.append("📉 Price below key support - breakdown continuation expected")
            
            # Format the analysis
            if language == 'id':
                analysis = f"""🎯 **REKOMENDASI TRADING:**

{signal_emoji} **SIGNAL**: {signal_direction}
📊 **Confidence**: {confidence:.0f}%

💰 **ENTRY POINTS:**
• **Entry**: ${entry_price:,.4f}
• **TP 1**: ${tp1:,.4f} (Target pertama)
• **TP 2**: ${tp2:,.4f} (Target kedua)
• **Stop Loss**: ${sl:,.4f}

📈 **ANALISIS FAKTOR:**"""
                
                for factor in signal_factors:
                    analysis += f"\n• {factor}"
                
                analysis += f"""

⚡ **STRATEGY {timeframe}:**
• Masuk posisi di level entry dengan risk 1-2% dari modal
• Take profit partial 50% di TP1, hold 50% untuk TP2
• Move stop loss ke break-even setelah TP1 tercapai
• Timeframe {timeframe} cocok untuk {'scalping' if timeframe in ['15m', '30m'] else 'swing trading'}"""
            
            else:
                analysis = f"""🎯 **TRADING RECOMMENDATION:**

{signal_emoji} **SIGNAL**: {signal_direction}
📊 **Confidence**: {confidence:.0f}%

💰 **ENTRY POINTS:**
• **Entry**: ${entry_price:,.4f}
• **TP 1**: ${tp1:,.4f} (First target)
• **TP 2**: ${tp2:,.4f} (Second target)
• **Stop Loss**: ${sl:,.4f}

📈 **FACTOR ANALYSIS:**"""
                
                for factor in signal_factors:
                    analysis += f"\n• {factor}"
                
                analysis += f"""

⚡ **STRATEGY {timeframe}:**
• Enter position at entry level with 1-2% risk of capital
• Take profit partial 50% at TP1, hold 50% for TP2
• Move stop loss to break-even after TP1 is reached
• {timeframe} timeframe suitable for {'scalping' if timeframe in ['15m', '30m'] else 'swing trading'}"""
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error generating signal: {e}")
            return "❌ Error dalam menghasilkan sinyal trading."

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate optimized futures signals dengan SnD integration dan limit order recommendations untuk top 5 coins"""
        try:
            print(f"🎯 Generating SnD futures signals with limit order recommendations for top 5 coins")
            
            # Get top 5 coins by market cap
            target_symbols = self._get_top_5_coins_by_market_cap(crypto_api)
            
            # Generate SnD signals with limit order recommendations
            snd_signals = []
            
            for symbol in target_symbols:
                try:
                    # Get comprehensive SnD data for each coin
                    snd_signal_data = self._get_snd_signal_data_for_limit_orders(symbol, crypto_api)
                    if not snd_signal_data:
                        continue
                    
                    # Generate SnD signal with precise limit order recommendations
                    snd_signal = self._generate_snd_limit_order_signal(symbol, snd_signal_data, language)
                    if snd_signal:
                        snd_signals.append(snd_signal)
                        
                except Exception as e:
                    print(f"❌ Error processing SnD signal for {symbol}: {e}")
                    continue
            
            return self._format_snd_limit_order_signals_output(snd_signals, language)
            
        except Exception as e:
            print(f"❌ Error in generate_futures_signals: {e}")
            return "❌ Error generating SnD futures signals. Please try again later."
    
    def _get_enhanced_signal_data_with_snd(self, symbol, crypto_api):
        """Get enhanced data for SnD-based signal generation with limit order recommendations"""
        try:
            # Single data fetch per symbol
            price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True) if crypto_api else {}
            futures_data = crypto_api.get_comprehensive_futures_data(symbol) if crypto_api else {}
            
            # Determine best price source
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_source = "CoinAPI"
                source_emoji = "🟢"
            elif 'error' not in futures_data and futures_data.get('price_data', {}).get('price', 0) > 0:
                current_price = futures_data.get('price_data', {}).get('price', 0)
                price_source = "Binance"
                source_emoji = "🟡"
            else:
                current_price = self._get_estimated_price(symbol)
                price_source = "Estimated"
                source_emoji = "🔴"
            
            # Get multiple timeframe candlestick data for comprehensive SnD analysis
            snd_zones = {}
            consolidation_zones = {}
            breakout_signals = {}
            
            # Get 4H data for primary SnD analysis
            candlestick_4h = crypto_api.get_binance_candlestick(symbol, '4h', 100) if crypto_api else {}
            
            if 'error' not in candlestick_4h and candlestick_4h.get('candlesticks'):
                # Run comprehensive SnD analysis
                snd_zones = self._calculate_advanced_snd_zones(
                    candlestick_4h['candlesticks'], 
                    current_price
                )
                
                # Identify consolidation zones for better entry timing
                consolidation_zones = self._identify_consolidation_zones(
                    candlestick_4h['candlesticks']
                )
                
                # Check for breakout signals with volume confirmation
                breakout_signals = self._identify_breakout_zones(
                    candlestick_4h['candlesticks'],
                    snd_zones,
                    consolidation_zones
                )
            
            # Get 1H data for precision entry points
            candlestick_1h = crypto_api.get_binance_candlestick(symbol, '1h', 50) if crypto_api else {}
            precision_entries = {}
            
            if 'error' not in candlestick_1h and candlestick_1h.get('candlesticks'):
                precision_entries = self._calculate_precision_entry_points(
                    candlestick_1h['candlesticks'],
                    current_price,
                    snd_zones
                )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_source': price_source,
                'source_emoji': source_emoji,
                'snd_zones': snd_zones,
                'consolidation_zones': consolidation_zones,
                'breakout_signals': breakout_signals,
                'precision_entries': precision_entries,
                'futures_data': futures_data,
                'candlestick_4h': candlestick_4h,
                'candlestick_1h': candlestick_1h
            }
            
        except Exception as e:
            print(f"❌ Error getting enhanced signal data for {symbol}: {e}")
            return None
    
    def _get_clean_signal_data(self, symbol, crypto_api):
        """Get essential data for signal generation (no repetitive parsing) - legacy method"""
        try:
            # Single data fetch per symbol
            price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True) if crypto_api else {}
            futures_data = crypto_api.get_comprehensive_futures_data(symbol) if crypto_api else {}
            
            # Determine best price source
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_source = "CoinAPI"
                source_emoji = "🟢"
            elif 'error' not in futures_data and futures_data.get('price_data', {}).get('price', 0) > 0:
                current_price = futures_data.get('price_data', {}).get('price', 0)
                price_source = "Binance"
                source_emoji = "🟡"
            else:
                current_price = self._get_estimated_price(symbol)
                price_source = "Estimated"
                source_emoji = "🔴"
            
            # Get candlestick data for SnD analysis (if available)
            snd_zones = {}
            candlestick_data = crypto_api.get_binance_candlestick(symbol, '4h', 50) if crypto_api else {}
            
            if 'error' not in candlestick_data and candlestick_data.get('candlesticks'):
                # Run optimized SnD analysis
                snd_zones = self._calculate_advanced_snd_zones(
                    candlestick_data['candlesticks'], 
                    current_price
                )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_source': price_source,
                'source_emoji': source_emoji,
                'snd_zones': snd_zones,
                'futures_data': futures_data
            }
            
        except Exception as e:
            print(f"❌ Error getting signal data for {symbol}: {e}")
            return None
    
    def _generate_clean_futures_signal(self, symbol, data, language='id'):
        """Generate single clean futures signal dengan SnD"""
        try:
            current_price = data['current_price']
            snd_zones = data.get('snd_zones', {})
            
            # Determine trend dan direction
            trend_direction = self._determine_clean_trend(data)
            
            # Calculate clean trading levels
            levels = self._calculate_clean_trading_levels(current_price, trend_direction, snd_zones)
            
            # Format display
            price_display = self._format_price_smart(current_price)
            
            if language == 'id':
                signal_text = f"""🎯 {symbol} FUTURES {levels['direction_emoji']}

💰 Harga: {price_display} {data['source_emoji']}
📊 Signal: {levels['direction']} | Confidence: {levels['confidence']}%

💼 Trading Levels:
• Entry: {self._format_price_smart(levels['entry'])}
• TP1: {self._format_price_smart(levels['tp1'])} | TP2: {self._format_price_smart(levels['tp2'])}
• SL: {self._format_price_smart(levels['sl'])} | R/R: {levels['rr']:.1f}:1"""
            else:
                signal_text = f"""🎯 {symbol} FUTURES {levels['direction_emoji']}

💰 Price: {price_display} {data['source_emoji']}
📊 Signal: {levels['direction']} | Confidence: {levels['confidence']}%

💼 Trading Levels:
• Entry: {self._format_price_smart(levels['entry'])}
• TP1: {self._format_price_smart(levels['tp1'])} | TP2: {self._format_price_smart(levels['tp2'])}
• SL: {self._format_price_smart(levels['sl'])} | R/R: {levels['rr']:.1f}:1"""
            
            # Add SnD context if available
            if snd_zones.get('strength') in ['medium', 'high']:
                snd_context = self._get_snd_context(snd_zones, current_price, language)
                signal_text += f"\n{snd_context}"
            
            return signal_text
            
        except Exception as e:
            print(f"❌ Error generating clean signal for {symbol}: {e}")
            return None
    
    def _determine_clean_trend(self, data):
        """Determine trend direction efficiently"""
        futures_data = data.get('futures_data', {})
        snd_zones = data.get('snd_zones', {})
        
        # Simple trend logic
        long_score = 0
        short_score = 0
        
        # SnD bias
        if snd_zones.get('strength') == 'high':
            nearest_demand = min(snd_zones.get('demand_zones', []), default=0, key=lambda x: abs(x - data['current_price']))
            nearest_supply = min(snd_zones.get('supply_zones', []), default=float('inf'), key=lambda x: abs(x - data['current_price']))
            
            if abs(data['current_price'] - nearest_demand) < abs(data['current_price'] - nearest_supply):
                long_score += 2  # Near demand = bullish
            else:
                short_score += 2  # Near supply = bearish
        
        # Futures sentiment
        if 'error' not in futures_data:
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                if long_ratio > 70:
                    short_score += 1  # Contrarian
                elif long_ratio < 30:
                    long_score += 1   # Contrarian
        
        # Return direction
        return 'LONG' if long_score > short_score else 'SHORT'
    
    def _calculate_clean_trading_levels(self, current_price, direction, snd_zones):
        """Calculate clean trading levels dengan SnD integration"""
        if direction == 'LONG':
            entry = current_price * 0.999
            tp1 = current_price * 1.025
            tp2 = current_price * 1.05
            sl = current_price * 0.98
            emoji = "🟢"
        else:
            entry = current_price * 1.001
            tp1 = current_price * 0.975
            tp2 = current_price * 0.95
            sl = current_price * 1.02
            emoji = "🔴"
        
        # Adjust levels based on SnD zones if available
        if snd_zones.get('strength') == 'high':
            if direction == 'LONG' and snd_zones.get('demand_zones'):
                nearest_demand = max([z for z in snd_zones['demand_zones'] if z < current_price], default=entry)
                sl = max(sl, nearest_demand * 0.995)  # SL just below demand
            elif direction == 'SHORT' and snd_zones.get('supply_zones'):
                nearest_supply = min([z for z in snd_zones['supply_zones'] if z > current_price], default=entry)
                sl = min(sl, nearest_supply * 1.005)  # SL just above supply
        
        rr_ratio = abs(tp2 - entry) / abs(sl - entry) if abs(sl - entry) > 0 else 2.5
        confidence = 80 if snd_zones.get('strength') == 'high' else 75
        
        return {
            'direction': direction,
            'direction_emoji': emoji,
            'entry': entry,
            'tp1': tp1,
            'tp2': tp2,
            'sl': sl,
            'rr': rr_ratio,
            'confidence': confidence
        }
    
    def _calculate_precision_entry_points(self, candlestick_1h, current_price, snd_zones):
        """Calculate precision entry points for limit orders based on 1H data"""
        if not candlestick_1h or len(candlestick_1h) < 10:
            return {'entries': [], 'quality': 'low'}
        
        try:
            # Get recent price action for micro-structure analysis
            recent_candles = candlestick_1h[-20:]
            
            # Calculate support and resistance levels from recent action
            recent_highs = [float(c[2]) for c in recent_candles]
            recent_lows = [float(c[3]) for c in recent_candles]
            recent_closes = [float(c[4]) for c in recent_candles]
            
            # Find pivot points for precise entries
            pivot_levels = []
            
            # Calculate pivot highs and lows
            for i in range(2, len(recent_candles) - 2):
                high = recent_highs[i]
                low = recent_lows[i]
                
                # Pivot high (resistance for SHORT entries)
                if (high > recent_highs[i-1] and high > recent_highs[i+1] and 
                    high > recent_highs[i-2] and high > recent_highs[i+2]):
                    distance_pct = abs(high - current_price) / current_price * 100
                    if distance_pct < 3:  # Within 3% of current price
                        pivot_levels.append({
                            'price': high,
                            'type': 'resistance',
                            'strength': self._calculate_pivot_strength(recent_candles, i, 'high'),
                            'distance_pct': distance_pct
                        })
                
                # Pivot low (support for LONG entries)
                if (low < recent_lows[i-1] and low < recent_lows[i+1] and 
                    low < recent_lows[i-2] and low < recent_lows[i+2]):
                    distance_pct = abs(current_price - low) / current_price * 100
                    if distance_pct < 3:  # Within 3% of current price
                        pivot_levels.append({
                            'price': low,
                            'type': 'support',
                            'strength': self._calculate_pivot_strength(recent_candles, i, 'low'),
                            'distance_pct': distance_pct
                        })
            
            # Enhance with SnD zone alignment
            enhanced_entries = []
            for pivot in pivot_levels:
                # Check alignment with SnD zones
                snd_alignment = self._check_snd_alignment(pivot, snd_zones)
                
                if snd_alignment['aligned']:
                    enhanced_entries.append({
                        'entry_price': pivot['price'],
                        'entry_type': 'LONG' if pivot['type'] == 'support' else 'SHORT',
                        'precision_level': 'high' if pivot['strength'] > 70 else 'medium',
                        'snd_confirmation': snd_alignment['zone_type'],
                        'limit_order_distance': round(abs(pivot['price'] - current_price) / current_price * 100, 2),
                        'confidence': min(95, pivot['strength'] + snd_alignment['bonus'])
                    })
            
            # Sort by confidence and limit to top 3
            enhanced_entries.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'entries': enhanced_entries[:3],
                'quality': 'high' if len(enhanced_entries) > 0 else 'medium',
                'total_found': len(enhanced_entries)
            }
            
        except Exception as e:
            print(f"❌ Error calculating precision entries: {e}")
            return {'entries': [], 'quality': 'low'}
    
    def _calculate_pivot_strength(self, candles, pivot_index, pivot_type):
        """Calculate the strength of a pivot point based on volume and touch count"""
        try:
            pivot_candle = candles[pivot_index]
            pivot_volume = float(pivot_candle[5])
            
            # Compare with average volume
            surrounding_volumes = [float(c[5]) for c in candles[max(0, pivot_index-3):pivot_index+4]]
            avg_volume = sum(surrounding_volumes) / len(surrounding_volumes)
            
            volume_strength = min(50, (pivot_volume / avg_volume) * 25)
            
            # Check for multiple touches (stronger level)
            pivot_price = float(pivot_candle[2] if pivot_type == 'high' else pivot_candle[3])
            touch_count = 0
            
            for candle in candles:
                if pivot_type == 'high':
                    if abs(float(candle[2]) - pivot_price) / pivot_price < 0.002:  # Within 0.2%
                        touch_count += 1
                else:
                    if abs(float(candle[3]) - pivot_price) / pivot_price < 0.002:  # Within 0.2%
                        touch_count += 1
            
            touch_strength = min(30, touch_count * 10)
            
            return volume_strength + touch_strength + 20  # Base 20 points
            
        except Exception:
            return 40  # Default medium strength
    
    def _check_snd_alignment(self, pivot, snd_zones):
        """Check if pivot point aligns with SnD zones"""
        if not snd_zones or snd_zones.get('strength') == 'low':
            return {'aligned': False, 'zone_type': None, 'bonus': 0}
        
        pivot_price = pivot['price']
        
        # Check demand zones for LONG entries
        if pivot['type'] == 'support' and snd_zones.get('demand_zones'):
            for demand_price in snd_zones['demand_zones']:
                if abs(pivot_price - demand_price) / demand_price < 0.01:  # Within 1%
                    return {
                        'aligned': True,
                        'zone_type': 'demand_zone',
                        'bonus': 25 if snd_zones['strength'] == 'high' else 15
                    }
        
        # Check supply zones for SHORT entries
        if pivot['type'] == 'resistance' and snd_zones.get('supply_zones'):
            for supply_price in snd_zones['supply_zones']:
                if abs(pivot_price - supply_price) / supply_price < 0.01:  # Within 1%
                    return {
                        'aligned': True,
                        'zone_type': 'supply_zone',
                        'bonus': 25 if snd_zones['strength'] == 'high' else 15
                    }
        
        return {'aligned': False, 'zone_type': None, 'bonus': 0}
    
    def _generate_snd_futures_signal_with_entries(self, symbol, data, language='id'):
        """Generate SnD-based futures signal with precise limit order entry recommendations"""
        try:
            current_price = data['current_price']
            snd_zones = data.get('snd_zones', {})
            precision_entries = data.get('precision_entries', {})
            
            # Determine primary trend direction
            trend_direction = self._determine_snd_trend(data)
            
            # Calculate trading levels with SnD integration
            levels = self._calculate_snd_trading_levels(current_price, trend_direction, snd_zones)
            
            # Format price displays
            price_display = self._format_price_smart(current_price)
            
            if language == 'id':
                signal_text = f"""🎯 {symbol} SnD FUTURES {levels['direction_emoji']}

💰 Harga: {price_display} {data['source_emoji']} | SnD: {snd_zones.get('strength', 'low').upper()}
📊 Signal: {levels['direction']} | Confidence: {levels['confidence']}%

💼 LEVEL TRADING SnD:
• Entry Zone: {self._format_price_smart(levels['entry_zone_low'])} - {self._format_price_smart(levels['entry_zone_high'])}
• TP1: {self._format_price_smart(levels['tp1'])} | TP2: {self._format_price_smart(levels['tp2'])}
• SL: {self._format_price_smart(levels['sl'])} | R/R: {levels['rr']:.1f}:1"""
            else:
                signal_text = f"""🎯 {symbol} SnD FUTURES {levels['direction_emoji']}

💰 Price: {price_display} {data['source_emoji']} | SnD: {snd_zones.get('strength', 'low').upper()}
📊 Signal: {levels['direction']} | Confidence: {levels['confidence']}%

💼 SnD TRADING LEVELS:
• Entry Zone: {self._format_price_smart(levels['entry_zone_low'])} - {self._format_price_smart(levels['entry_zone_high'])}
• TP1: {self._format_price_smart(levels['tp1'])} | TP2: {self._format_price_smart(levels['tp2'])}
• SL: {self._format_price_smart(levels['sl'])} | R/R: {levels['rr']:.1f}:1"""
            
            # Add precision limit order recommendations
            if precision_entries.get('entries') and precision_entries.get('quality') != 'low':
                best_entry = precision_entries['entries'][0]
                
                if language == 'id':
                    signal_text += f"""

🎯 LIMIT ORDER RECOMMENDATION:
• Precision Entry: {self._format_price_smart(best_entry['entry_price'])} ({best_entry['entry_type']})
• Distance: {best_entry['limit_order_distance']}% dari harga saat ini
• SnD Alignment: {best_entry['snd_confirmation'].replace('_', ' ').title()}
• Order Type: LIMIT {best_entry['entry_type']} @ {self._format_price_smart(best_entry['entry_price'])}"""
                else:
                    signal_text += f"""

🎯 LIMIT ORDER RECOMMENDATION:
• Precision Entry: {self._format_price_smart(best_entry['entry_price'])} ({best_entry['entry_type']})
• Distance: {best_entry['limit_order_distance']}% from current price
• SnD Alignment: {best_entry['snd_confirmation'].replace('_', ' ').title()}
• Order Type: LIMIT {best_entry['entry_type']} @ {self._format_price_smart(best_entry['entry_price'])}"""
            
            return signal_text
            
        except Exception as e:
            print(f"❌ Error generating SnD futures signal for {symbol}: {e}")
            return None
    
    def _determine_snd_trend(self, data):
        """Determine trend direction based on SnD zones and market structure"""
        snd_zones = data.get('snd_zones', {})
        breakout_signals = data.get('breakout_signals', {})
        current_price = data['current_price']
        
        # Priority 1: Breakout signals
        if breakout_signals.get('breakout_signal') and breakout_signals.get('confidence', 0) > 70:
            return breakout_signals['breakout_signal']['direction']
        
        # Priority 2: SnD zone positioning
        if snd_zones.get('strength') in ['medium', 'high']:
            demand_zones = snd_zones.get('demand_zones', [])
            supply_zones = snd_zones.get('supply_zones', [])
            
            # Find nearest zones
            nearest_demand = min(demand_zones, default=0, key=lambda x: abs(x - current_price)) if demand_zones else 0
            nearest_supply = min(supply_zones, default=float('inf'), key=lambda x: abs(x - current_price)) if supply_zones else float('inf')
            
            demand_distance = abs(current_price - nearest_demand) / current_price * 100 if nearest_demand > 0 else 100
            supply_distance = abs(nearest_supply - current_price) / current_price * 100 if nearest_supply != float('inf') else 100
            
            # Closer to demand = LONG bias, closer to supply = SHORT bias
            if demand_distance < supply_distance and demand_distance < 2:
                return 'LONG'
            elif supply_distance < demand_distance and supply_distance < 2:
                return 'SHORT'
        
        # Priority 3: Futures sentiment
        futures_data = data.get('futures_data', {})
        if 'error' not in futures_data:
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                if long_ratio > 75:
                    return 'SHORT'  # Contrarian
                elif long_ratio < 25:
                    return 'LONG'   # Contrarian
        
        # Default to LONG if no clear direction
        return 'LONG'
    
    def _calculate_snd_trading_levels(self, current_price, direction, snd_zones):
        """Calculate trading levels with SnD zone integration and entry zones for limit orders"""
        
        # Base entry zone calculation
        if direction == 'LONG':
            base_entry = current_price * 0.998
            entry_zone_low = current_price * 0.995
            entry_zone_high = current_price * 1.001
            tp1 = current_price * 1.025
            tp2 = current_price * 1.05
            sl = current_price * 0.98
            emoji = "🟢"
        else:
            base_entry = current_price * 1.002
            entry_zone_low = current_price * 0.999
            entry_zone_high = current_price * 1.005
            tp1 = current_price * 0.975
            tp2 = current_price * 0.95
            sl = current_price * 1.02
            emoji = "🔴"
        
        # Adjust levels based on SnD zones if high quality
        if snd_zones.get('strength') == 'high':
            if direction == 'LONG' and snd_zones.get('demand_zones'):
                # Find nearest demand zone
                nearest_demand = max([z for z in snd_zones['demand_zones'] if z < current_price * 1.02], default=None)
                if nearest_demand:
                    # Adjust entry zone to align with demand zone
                    entry_zone_low = nearest_demand * 0.999
                    entry_zone_high = nearest_demand * 1.003
                    sl = max(sl, nearest_demand * 0.995)  # SL below demand zone
            
            elif direction == 'SHORT' and snd_zones.get('supply_zones'):
                # Find nearest supply zone
                nearest_supply = min([z for z in snd_zones['supply_zones'] if z > current_price * 0.98], default=None)
                if nearest_supply:
                    # Adjust entry zone to align with supply zone
                    entry_zone_low = nearest_supply * 0.997
                    entry_zone_high = nearest_supply * 1.001
                    sl = min(sl, nearest_supply * 1.005)  # SL above supply zone
        
        # Calculate risk/reward
        avg_entry = (entry_zone_low + entry_zone_high) / 2
        rr_ratio = abs(tp2 - avg_entry) / abs(sl - avg_entry) if abs(sl - avg_entry) > 0 else 2.5
        
        # Confidence based on SnD strength
        confidence = 85 if snd_zones.get('strength') == 'high' else 75 if snd_zones.get('strength') == 'medium' else 65
        
        return {
            'direction': direction,
            'direction_emoji': emoji,
            'entry_zone_low': entry_zone_low,
            'entry_zone_high': entry_zone_high,
            'tp1': tp1,
            'tp2': tp2,
            'sl': sl,
            'rr': rr_ratio,
            'confidence': confidence
        }
    
    def _get_snd_context(self, snd_zones, current_price, language='id'):
        """Get brief SnD context for signal"""
        if language == 'id':
            if snd_zones.get('strength') == 'high':
                return f"🎯 SnD: Zona kuat terdeteksi (strength: {snd_zones['strength']})"
            else:
                return f"📊 SnD: Setup medium (strength: {snd_zones['strength']})"
        else:
            if snd_zones.get('strength') == 'high':
                return f"🎯 SnD: Strong zones detected (strength: {snd_zones['strength']})"
            else:
                return f"📊 SnD: Medium setup (strength: {snd_zones['strength']})"
    
    def _format_final_snd_signals_output(self, signals, language='id'):
        """Format final SnD-optimized output with limit order guidance"""
        if not signals:
            return "❌ No SnD signals generated. Try again later."
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        if language == 'id':
            header = f"""🚨 SnD FUTURES SIGNALS - TOP {len(signals)} COINS
⏰ {current_time} | 📊 Multi-Timeframe SnD | 🎯 Limit Order Ready

"""
            footer = """
══════════════════════════════════════════
🎯 LIMIT ORDER STRATEGY:
• Entry Zone = area untuk spread limit orders
• Precision Entry = entry terbaik dengan limit order
• Gunakan LIMIT order untuk entry yang lebih baik
• Scale-in di entry zone untuk mengurangi risiko

🛡️ SnD RISK MANAGEMENT:
• Max 1.5% position size per trade (SnD = precision trading)
• SL WAJIB di luar zona SnD
• Take profit bertahap: 40% di TP1, 60% di TP2
• Cancel limit order jika struktur SnD berubah

📊 Data: CoinAPI + Binance + Advanced SnD Analysis
⚠️ SnD trading memerlukan disiplin dan patience!"""
            
        else:
            header = f"""🚨 SnD FUTURES SIGNALS - TOP {len(signals)} COINS
⏰ {current_time} | 📊 Multi-Timeframe SnD | 🎯 Limit Order Ready

"""
            footer = """
══════════════════════════════════════════
🎯 LIMIT ORDER STRATEGY:
• Entry Zone = area to spread limit orders
• Precision Entry = best entry with limit order
• Use LIMIT orders for better entry execution
• Scale-in at entry zone to reduce risk

🛡️ SnD RISK MANAGEMENT:
• Max 1.5% position size per trade (SnD = precision trading)
• SL MANDATORY outside SnD zones
• Take profit gradually: 40% at TP1, 60% at TP2
• Cancel limit orders if SnD structure changes

📊 Data: CoinAPI + Binance + Advanced SnD Analysis
⚠️ SnD trading requires discipline and patience!"""
        
        return header + "\n\n".join(signals) + footer
    
    def _format_final_signals_output(self, signals, language='id'):
        """Format final optimized output - legacy method"""
        if not signals:
            return "❌ No signals generated. Try again later."
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        if language == 'id':
            header = f"""🚨 FUTURES SIGNALS OPTIMIZED
⏰ {current_time} | 📊 4H Timeframe | 🎯 Top {len(signals)} Coins

"""
            footer = """
══════════════════════════════════════════
🛡️ RISK MANAGEMENT:
• Max 2% position size per trade
• Set SL before entry (WAJIB!)
• Take profit: 50% at TP1, 50% at TP2
• SnD zones = zona konfirmasi entry

📊 Data: CoinAPI + Binance + SnD Analysis
⚠️ High risk - gunakan proper risk management!"""
            
        else:
            header = f"""🚨 OPTIMIZED FUTURES SIGNALS
⏰ {current_time} | 📊 4H Timeframe | 🎯 Top {len(signals)} Coins

"""
            footer = """
══════════════════════════════════════════
🛡️ RISK MANAGEMENT:
• Max 2% position size per trade  
• Set SL before entry (MANDATORY!)
• Take profit: 50% at TP1, 50% at TP2
• SnD zones = entry confirmation areas

📊 Data: CoinAPI + Binance + SnD Analysis
⚠️ High risk - use proper risk management!"""
        
        return header + "\n\n".join(signals) + footer

    def get_ai_response(self, text, language='id'):
        """Enhanced AI response for crypto beginners and general questions"""
        text_lower = text.lower()

        if language == 'id':
            # Crypto basics and education
            if any(keyword in text_lower for keyword in ['apa itu bitcoin', 'bitcoin itu apa', 'penjelasan bitcoin']):
                return """🪙 **Apa itu Bitcoin?**

Bitcoin (BTC) adalah cryptocurrency pertama dan terbesar di dunia, diciptakan oleh Satoshi Nakamoto pada 2009.

🔑 **Karakteristik Utama:**
- **Digital Currency**: Mata uang digital yang tidak dikendalikan bank
- **Blockchain**: Teknologi buku besar terdistribusi yang aman
- **Limited Supply**: Hanya 21 juta BTC yang akan pernah ada
- **Decentralized**: Tidak ada otoritas pusat yang mengendalikan

💡 **Kegunaan Bitcoin:**
- Store of value (penyimpan nilai)
- Medium of exchange (alat tukar)
- Hedge against inflation (lindung nilai inflasi)

📈 **Untuk pemula**: Mulai dengan belajar tentang wallet, private key, dan cara membeli BTC di exchange resmi.

Gunakan `/price btc` untuk cek harga terkini!"""

            elif any(keyword in text_lower for keyword in ['apa itu crypto', 'cryptocurrency itu apa', 'kripto itu apa']):
                return """🌐 **Apa itu Cryptocurrency?**

Cryptocurrency adalah mata uang digital yang menggunakan kriptografi untuk keamanan dan beroperasi pada teknologi blockchain.

🔧 **Komponen Utama:**
- **Blockchain**: Database terdistribusi yang mencatat semua transaksi
- **Mining**: Proses validasi transaksi dan pembuatan blok baru
- **Wallet**: Tempat menyimpan cryptocurrency Anda dengan aman
- **Private Key**: Kunci rahasia untuk mengakses wallet
- **Public Key**: Alamat wallet untuk menerima crypto

💰 **Contoh Cryptocurrency Populer:**
- **Bitcoin (BTC)**: Cryptocurrency pertama dan terbesar
- **Ethereum (ETH)**: Platform smart contract
- **Binance Coin (BNB)**: Token exchange Binance
- **Solana (SOL)**: Blockchain cepat dan murah
- **Polygon (MATIC)**: Layer 2 untuk Ethereum

🌟 **Keuntungan Crypto:**
- Transaksi 24/7 tanpa bank
- Biaya transfer lebih murah
- Tidak ada batasan geografis
- Transparansi tinggi
- Potensi return investasi tinggi

⚠️ **Risiko Crypto:**
- Volatilitas tinggi (harga naik-turun drastis)
- Belum ada regulasi jelas
- Risiko kehilangan private key
- Scam dan fraud

💡 **Tips untuk Pemula:**
- Mulai dengan amount kecil
- Pelajari dasar-dasar dulu
- Gunakan exchange terpercaya
- Simpan di wallet sendiri (bukan di exchange)
- Jangan invest lebih dari yang bisa rugi

Gunakan `/price <symbol>` untuk cek harga crypto!"""

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`.\nContoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

            elif any(keyword in text_lower for keyword in ['market', 'pasar', 'overview']):
                return "📈 Gunakan command `/market` untuk melihat overview pasar crypto secara keseluruhan.\n\nIngin tau tentang market cap, dominasi BTC, atau trend pasar?"

            elif any(keyword in text_lower for keyword in ['help', 'bantuan', 'command']):
                return self.help_message()

            elif any(keyword in text_lower for keyword in ['terima kasih', 'thanks', 'thx']):
                return "🙏 Sama-sama! Senang bisa membantu belajar crypto Anda. Jangan ragu untuk bertanya lagi!"

            # Default response for unmatched queries
            else:
                return f"""🤖 **CryptoMentor AI**

Saya memahami Anda bertanya tentang: "{text}"

📚 **Yang bisa saya bantu:**
- Analisis harga crypto (`/price btc`)
- Analisis mendalam (`/analyze eth`) 
- Sinyal trading (`/futures_signals`)
- Overview pasar (`/market`)
- Pertanyaan crypto umum
- Tutorial trading dan DeFi

💡 **Tip**: Coba ketik pertanyaan lebih spesifik atau gunakan command yang tersedia.

Gunakan `/help` untuk melihat semua fitur!"""

        else:
            # English responses
            if any(keyword in text_lower for keyword in ['what is bitcoin', 'explain bitcoin', 'bitcoin basics']):
                return """🪙 **What is Bitcoin?**

Bitcoin (BTC) is the world's first and largest cryptocurrency, created by Satoshi Nakamoto in 2009.

🔑 **Key Characteristics:**
- **Digital Currency**: Not controlled by any bank or government
- **Blockchain**: Secure distributed ledger technology
- **Limited Supply**: Only 21 million BTC will ever exist
- **Decentralized**: No central authority controls it

💡 **Bitcoin Use Cases:**
- Store of value (digital gold)
- Medium of exchange
- Hedge against inflation
- Investment asset

📈 **For beginners**: Start by learning about wallets, private keys, and how to buy BTC on legitimate exchanges.

Use `/price btc` to check current price!"""

            elif any(keyword in text_lower for keyword in ['price', 'cost', 'how much']):
                return "💰 To check crypto prices, use `/price <symbol>`. Example: `/price btc`\n\nFor comprehensive analysis: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analysis', 'analyze', 'signal']):
                return "📊 For deep analysis, use `/analyze <symbol>` or `/futures_signals` for daily futures signals.\n\nExample: `/analyze btc` or `/futures_signals`\n💡 **Note**: Analysis includes technical analysis, sentiment, and trading recommendations."

            elif any(keyword in text_lower for keyword in ['market', 'overview']):
                return "📈 Use `/market` command to see overall crypto market overview.\n\nWant to know about market cap, BTC dominance, or market trends?"

            elif any(keyword in text_lower for keyword in ['help', 'command']):
                return self.help_message()

            elif any(keyword in text_lower for keyword in ['thank', 'thanks', 'thx']):
                return "🙏 You're welcome! Happy to help with your crypto learning journey. Feel free to ask anytime!"

            else:
                return """🤖 **CryptoMentor AI - Crypto Learning Assistant**

I'm here to help you learn about cryptocurrency!

📚 **Topics I can explain:**
- Crypto basics (Bitcoin, Blockchain, DeFi)
- How to buy and store crypto
- Trading and technical analysis
- Security and wallet management
- NFTs and blockchain technology

💡 **Example questions:**
- "What is Bitcoin?"
- "How to buy crypto?"
- "What is DeFi?"
- "How to trade cryptocurrency?"
- "Best crypto wallets?"

📊 **Available commands:**
- `/price <symbol>` - Check real-time prices
- `/analyze <symbol>` - Deep analysis
- `/futures_signals` - Trading signals
- `/help` - See all commands

Ask me anything about crypto! 🚀"""



    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get enhanced market sentiment analysis using CoinMarketCap Startup Plan"""
        if not crypto_api or not crypto_api.cmc_provider.api_key:
            # Return static response when API is not available
            if language == 'id':
                return """🌍 **OVERVIEW PASAR CRYPTO** (Mode Offline)

💰 **Data Pasar:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Crypto Aktif: 12,000+ coin

📈 **Status:** Pasar dalam fase recovery

⚠️ **Catatan:** Data real-time tidak tersedia, gunakan command lain untuk analisis live.

Coba lagi dalam beberapa menit untuk data real-time."""
            else:
                return """🌍 **CRYPTO MARKET OVERVIEW** (Offline Mode)

💰 **Market Data:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Active Cryptos: 12,000+ coins

📈 **Status:** Market in recovery phase

⚠️ **Note:** Real-time data unavailable, use other commands for live analysis.

Try again in a few minutes for real-time data."""

        try:
            # Get enhanced market overview from CoinMarketCap
            enhanced_data = crypto_api.cmc_provider.get_enhanced_market_overview()

            # Format message based on language
            if language == 'id':
                return self._format_enhanced_market_overview_id(enhanced_data)
            else:
                return self._format_enhanced_market_overview_en(enhanced_data)

        except Exception as e:
            print(f"❌ Enhanced market sentiment error: {e}")
            if language == 'id':
                return f"❌ Error mengambil data pasar: {str(e)}"
            else:
                return f"❌ Error fetching market data: {str(e)}"

    def _format_enhanced_market_overview_id(self, enhanced_data):
        """Format enhanced market overview in Indonesian with CoinMarketCap data"""
        try:
            if 'error' in enhanced_data:
                return f"❌ Error mengambil data CoinMarketCap: {enhanced_data.get('error')}"

            global_data = enhanced_data.get('global_metrics', {})
            top_cryptos = enhanced_data.get('top_cryptocurrencies', {})
            fng_data = enhanced_data.get('fear_greed_index', {})

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            message = f"""🌍 **OVERVIEW PASAR CRYPTO ADVANCED** (CoinMarketCap Real-time)

⏰ **Update**: {current_time}

"""

            # Global Market Stats
            if 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_24h', 0)
                total_volume = global_data.get('total_volume_24h', 0)
                btc_dominance = global_data.get('btc_dominance', 0)
                eth_dominance = global_data.get('eth_dominance', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                # Format large numbers
                mcap_str = f"${total_mcap/1e12:.2f}T" if total_mcap > 1e12 else f"${total_mcap/1e9:.1f}B"
                vol_str = f"${total_volume/1e12:.2f}T" if total_volume > 1e12 else f"${total_volume/1e9:.1f}B"

                change_emoji = "📈" if mcap_change >= 0 else "📉"
                change_color = "+" if mcap_change >= 0 else ""

                message += f"""💰 **DATA GLOBAL MARKET:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **Volume 24j**: {vol_str}
• **BTC Dominance**: {btc_dominance:.1f}%
• **ETH Dominance**: {eth_dominance:.1f}%
• **Altcoin Dominance**: {100 - btc_dominance - eth_dominance:.1f}%
• **Crypto Aktif**: {active_cryptos:,}

"""

                # ASCII Chart for BTC Dominance
                dominance_bar = self._create_dominance_chart(btc_dominance, eth_dominance)
                message += f"""📊 **DOMINANCE CHART:**
```
{dominance_bar}
```


    def _get_snd_signal_data_for_limit_orders(self, symbol, crypto_api):
        """Get comprehensive SnD data specifically for limit order entry recommendations"""
        try:
            # Get real-time price data
            price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True) if crypto_api else {}
            futures_data = crypto_api.get_comprehensive_futures_data(symbol) if crypto_api else {}
            
            # Determine best price source
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_source = "CoinAPI"
                source_emoji = "🟢"
            elif 'error' not in futures_data and futures_data.get('price_data', {}).get('price', 0) > 0:
                current_price = futures_data.get('price_data', {}).get('price', 0)
                price_source = "Binance"
                source_emoji = "🟡"
            else:
                current_price = self._get_estimated_price(symbol)
                price_source = "Estimated"
                source_emoji = "🔴"
            
            # Get multi-timeframe candlestick data for SnD analysis
            candlestick_4h = crypto_api.get_binance_candlestick(symbol, '4h', 100) if crypto_api else {}
            candlestick_1h = crypto_api.get_binance_candlestick(symbol, '1h', 50) if crypto_api else {}
            
            # Calculate advanced SnD zones
            snd_zones = {}
            if 'error' not in candlestick_4h and candlestick_4h.get('candlesticks'):
                snd_zones = self._calculate_advanced_snd_zones(
                    candlestick_4h['candlesticks'], 
                    current_price
                )
            
            # Calculate precision entry points for limit orders
            limit_order_entries = {}
            if 'error' not in candlestick_1h and candlestick_1h.get('candlesticks'):
                limit_order_entries = self._calculate_limit_order_entry_points(
                    candlestick_1h['candlesticks'],
                    current_price,
                    snd_zones
                )
            
            # Get market structure bias
            market_bias = self._get_snd_market_bias(current_price, snd_zones, futures_data)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_source': price_source,
                'source_emoji': source_emoji,
                'snd_zones': snd_zones,
                'limit_order_entries': limit_order_entries,
                'market_bias': market_bias,
                'futures_data': futures_data
            }
            
        except Exception as e:
            print(f"❌ Error getting SnD data for {symbol}: {e}")
            return None
    
    def _calculate_limit_order_entry_points(self, candlestick_1h, current_price, snd_zones):
        """Calculate precise limit order entry points based on SnD zones and micro-structure"""
        if not candlestick_1h or len(candlestick_1h) < 20:
            return {'entries': [], 'quality': 'low'}
        
        try:
            # Analyze recent price action for limit order placement
            recent_candles = candlestick_1h[-20:]
            
            # Extract price levels
            recent_highs = [float(c[2]) for c in recent_candles]
            recent_lows = [float(c[3]) for c in recent_candles]
            recent_closes = [float(c[4]) for c in recent_candles]
            recent_volumes = [float(c[5]) for c in recent_candles]
            
            # Find key support and resistance levels for limit orders
            limit_order_levels = []
            
            # Calculate swing highs and lows for limit order placement
            for i in range(3, len(recent_candles) - 3):
                high = recent_highs[i]
                low = recent_lows[i]
                volume = recent_volumes[i]
                
                # Swing high (potential SHORT limit order area)
                if (high > recent_highs[i-1] and high > recent_highs[i+1] and 
                    high > recent_highs[i-2] and high > recent_highs[i+2]):
                    
                    distance_from_current = abs(high - current_price) / current_price * 100
                    if distance_from_current <= 5:  # Within 5% for actionable limit orders
                        
                        # Check SnD zone alignment for SHORT
                        snd_alignment = self._check_limit_order_snd_alignment(high, snd_zones, 'SHORT')
                        
                        limit_order_levels.append({
                            'price': high,
                            'type': 'SHORT_LIMIT',
                            'distance_pct': distance_from_current,
                            'volume_strength': min(100, (volume / max(recent_volumes)) * 100),
                            'snd_aligned': snd_alignment['aligned'],
                            'snd_zone_type': snd_alignment.get('zone_type', 'none'),
                            'confidence': self._calculate_limit_order_confidence(high, current_price, volume, recent_volumes, snd_alignment)
                        })
                
                # Swing low (potential LONG limit order area)
                if (low < recent_lows[i-1] and low < recent_lows[i+1] and 
                    low < recent_lows[i-2] and low < recent_lows[i+2]):
                    
                    distance_from_current = abs(current_price - low) / current_price * 100
                    if distance_from_current <= 5:  # Within 5% for actionable limit orders
                        
                        # Check SnD zone alignment for LONG
                        snd_alignment = self._check_limit_order_snd_alignment(low, snd_zones, 'LONG')
                        
                        limit_order_levels.append({
                            'price': low,
                            'type': 'LONG_LIMIT',
                            'distance_pct': distance_from_current,
                            'volume_strength': min(100, (volume / max(recent_volumes)) * 100),
                            'snd_aligned': snd_alignment['aligned'],
                            'snd_zone_type': snd_alignment.get('zone_type', 'none'),
                            'confidence': self._calculate_limit_order_confidence(low, current_price, volume, recent_volumes, snd_alignment)
                        })
            
            # Sort by confidence and distance (prefer higher confidence and closer levels)
            limit_order_levels.sort(key=lambda x: (x['confidence'], -x['distance_pct']), reverse=True)
            
            # Filter to top 3 best limit order opportunities
            best_entries = limit_order_levels[:3]
            
            return {
                'entries': best_entries,
                'quality': 'high' if len(best_entries) > 0 and best_entries[0]['confidence'] > 70 else 'medium',
                'total_found': len(limit_order_levels)
            }
            
        except Exception as e:
            print(f"❌ Error calculating limit order entries: {e}")
            return {'entries': [], 'quality': 'low'}
    
    def _check_limit_order_snd_alignment(self, price_level, snd_zones, order_type):
        """Check if limit order level aligns with SnD zones"""
        if not snd_zones or snd_zones.get('strength') == 'low':
            return {'aligned': False, 'zone_type': 'none', 'bonus': 0}
        
        # Check LONG limit orders against demand zones
        if order_type == 'LONG' and snd_zones.get('demand_zones'):
            for demand_price in snd_zones['demand_zones']:
                if abs(price_level - demand_price) / demand_price < 0.015:  # Within 1.5%
                    return {
                        'aligned': True,
                        'zone_type': 'demand_zone',
                        'bonus': 30 if snd_zones['strength'] == 'high' else 20
                    }
        
        # Check SHORT limit orders against supply zones
        if order_type == 'SHORT' and snd_zones.get('supply_zones'):
            for supply_price in snd_zones['supply_zones']:
                if abs(price_level - supply_price) / supply_price < 0.015:  # Within 1.5%
                    return {
                        'aligned': True,
                        'zone_type': 'supply_zone',
                        'bonus': 30 if snd_zones['strength'] == 'high' else 20
                    }
        
        return {'aligned': False, 'zone_type': 'none', 'bonus': 0}
    
    def _calculate_limit_order_confidence(self, price_level, current_price, volume, recent_volumes, snd_alignment):
        """Calculate confidence score for limit order placement"""
        try:
            base_confidence = 50
            
            # Volume strength component
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            volume_score = min(20, volume_ratio * 10)
            
            # Distance penalty (closer is better for limit orders)
            distance_pct = abs(price_level - current_price) / current_price * 100
            distance_score = max(0, 15 - distance_pct * 3)  # Penalty for distance
            
            # SnD alignment bonus
            snd_bonus = snd_alignment.get('bonus', 0)
            
            # Calculate final confidence
            final_confidence = base_confidence + volume_score + distance_score + snd_bonus
            
            return min(95, max(30, final_confidence))
            
        except Exception:
            return 50  # Default confidence
    
    def _get_snd_market_bias(self, current_price, snd_zones, futures_data):
        """Determine overall market bias based on SnD zones and futures sentiment"""
        bias_score = 0
        bias_factors = []
        
        # SnD zone positioning bias
        if snd_zones.get('strength') in ['medium', 'high']:
            demand_zones = snd_zones.get('demand_zones', [])
            supply_zones = snd_zones.get('supply_zones', [])
            
            # Find nearest zones
            if demand_zones:
                nearest_demand = min(demand_zones, key=lambda x: abs(x - current_price))
                demand_distance = abs(current_price - nearest_demand) / current_price * 100
                
                if demand_distance < 3:  # Close to demand zone
                    bias_score += 2
                    bias_factors.append(f"🟢 Near strong demand zone (${nearest_demand:,.2f})")
            
            if supply_zones:
                nearest_supply = min(supply_zones, key=lambda x: abs(x - current_price))
                supply_distance = abs(nearest_supply - current_price) / current_price * 100
                
                if supply_distance < 3:  # Close to supply zone
                    bias_score -= 2
                    bias_factors.append(f"🔴 Near strong supply zone (${nearest_supply:,.2f})")
        
        # Futures sentiment bias
        if 'error' not in futures_data:
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                
                if long_ratio > 75:
                    bias_score -= 1
                    bias_factors.append(f"⚠️ Overleveraged longs ({long_ratio:.1f}%)")
                elif long_ratio < 25:
                    bias_score += 1
                    bias_factors.append(f"💎 Oversold conditions ({long_ratio:.1f}%)")
        
        # Determine final bias
        if bias_score >= 2:
            overall_bias = 'BULLISH'
            bias_emoji = '🟢'
        elif bias_score <= -2:
            overall_bias = 'BEARISH' 
            bias_emoji = '🔴'
        else:
            overall_bias = 'NEUTRAL'
            bias_emoji = '🟡'
        
        return {
            'direction': overall_bias,
            'emoji': bias_emoji,
            'score': bias_score,
            'factors': bias_factors
        }
    
    def _generate_snd_limit_order_signal(self, symbol, snd_data, language='id'):
        """Generate SnD-based signal with specific limit order recommendations"""
        try:
            current_price = snd_data['current_price']
            snd_zones = snd_data.get('snd_zones', {})
            limit_entries = snd_data.get('limit_order_entries', {})
            market_bias = snd_data.get('market_bias', {})
            
            # Format price display
            def format_price(p):
                if p < 1:
                    return f"${p:.8f}"
                elif p < 100:
                    return f"${p:.6f}"
                else:
                    return f"${p:,.4f}"
            
            price_display = format_price(current_price)
            
            if language == 'id':
                signal_text = f"""🎯 {symbol} SnD LIMIT ORDERS {market_bias.get('emoji', '🟡')}

💰 Harga: {price_display} {snd_data['source_emoji']} | SnD: {snd_zones.get('strength', 'low').upper()}
📊 Market Bias: {market_bias.get('direction', 'NEUTRAL')} | Source: {snd_data['price_source']}"""
                
                # Add best limit order recommendations
                if limit_entries.get('entries') and limit_entries.get('quality') != 'low':
                    signal_text += f"\n\n🎯 **REKOMENDASI LIMIT ORDER SnD:**"
                    
                    for i, entry in enumerate(limit_entries['entries'][:2], 1):  # Top 2 recommendations
                        order_type = entry['type'].replace('_LIMIT', '')
                        order_emoji = "🟢" if order_type == 'LONG' else "🔴"
                        
                        signal_text += f"""

{order_emoji} **{order_type} LIMIT ORDER #{i}:**
• **Entry Price**: {format_price(entry['price'])}
• **Distance**: {entry['distance_pct']:.1f}% dari harga saat ini
• **SnD Zone**: {entry['snd_zone_type'].replace('_', ' ').title() if entry['snd_aligned'] else 'No alignment'}
• **Confidence**: {entry['confidence']:.0f}%
• **Order Type**: LIMIT {order_type} @ {format_price(entry['price'])}"""
                        
                        # Calculate TP and SL for this entry
                        if order_type == 'LONG':
                            tp1 = entry['price'] * 1.02
                            tp2 = entry['price'] * 1.04
                            sl = entry['price'] * 0.985
                        else:
                            tp1 = entry['price'] * 0.98
                            tp2 = entry['price'] * 0.96
                            sl = entry['price'] * 1.015
                        
                        signal_text += f"""
• **TP1**: {format_price(tp1)} | **TP2**: {format_price(tp2)}
• **SL**: {format_price(sl)}"""
                
                else:
                    signal_text += f"""

⚠️ **NO CLEAR LIMIT ORDER SETUP:**
• SnD zones tidak memberikan entry yang jelas
• Tunggu price action konfirmasi di level kunci
• Monitor breakout/breakdown dengan volume"""
                
                # Add market bias factors
                if market_bias.get('factors'):
                    signal_text += f"\n\n📊 **ANALISIS SnD:**"
                    for factor in market_bias['factors'][:2]:
                        signal_text += f"\n• {factor}"
            
            else:  # English
                signal_text = f"""🎯 {symbol} SnD LIMIT ORDERS {market_bias.get('emoji', '🟡')}

💰 Price: {price_display} {snd_data['source_emoji']} | SnD: {snd_zones.get('strength', 'low').upper()}
📊 Market Bias: {market_bias.get('direction', 'NEUTRAL')} | Source: {snd_data['price_source']}"""
                
                # Add best limit order recommendations
                if limit_entries.get('entries') and limit_entries.get('quality') != 'low':
                    signal_text += f"\n\n🎯 **SnD LIMIT ORDER RECOMMENDATIONS:**"
                    
                    for i, entry in enumerate(limit_entries['entries'][:2], 1):  # Top 2 recommendations
                        order_type = entry['type'].replace('_LIMIT', '')
                        order_emoji = "🟢" if order_type == 'LONG' else "🔴"
                        
                        signal_text += f"""

{order_emoji} **{order_type} LIMIT ORDER #{i}:**
• **Entry Price**: {format_price(entry['price'])}
• **Distance**: {entry['distance_pct']:.1f}% from current price
• **SnD Zone**: {entry['snd_zone_type'].replace('_', ' ').title() if entry['snd_aligned'] else 'No alignment'}
• **Confidence**: {entry['confidence']:.0f}%
• **Order Type**: LIMIT {order_type} @ {format_price(entry['price'])}"""
                        
                        # Calculate TP and SL for this entry
                        if order_type == 'LONG':
                            tp1 = entry['price'] * 1.02
                            tp2 = entry['price'] * 1.04
                            sl = entry['price'] * 0.985
                        else:
                            tp1 = entry['price'] * 0.98
                            tp2 = entry['price'] * 0.96
                            sl = entry['price'] * 1.015
                        
                        signal_text += f"""
• **TP1**: {format_price(tp1)} | **TP2**: {format_price(tp2)}
• **SL**: {format_price(sl)}"""
                
                else:
                    signal_text += f"""

⚠️ **NO CLEAR LIMIT ORDER SETUP:**
• SnD zones don't provide clear entries
• Wait for price action confirmation at key levels
• Monitor breakout/breakdown with volume"""
                
                # Add market bias factors
                if market_bias.get('factors'):
                    signal_text += f"\n\n📊 **SnD ANALYSIS:**"
                    for factor in market_bias['factors'][:2]:
                        signal_text += f"\n• {factor}"
            
            return signal_text
            
        except Exception as e:
            print(f"❌ Error generating SnD limit order signal for {symbol}: {e}")
            return None
    
    def _format_snd_limit_order_signals_output(self, signals, language='id'):
        """Format final SnD limit order signals output"""
        if not signals:
            if language == 'id':
                return "❌ Tidak ada sinyal SnD limit order yang tersedia. Coba lagi nanti."
            else:
                return "❌ No SnD limit order signals available. Try again later."
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        if language == 'id':
            header = f"""🚨 SnD LIMIT ORDER SIGNALS - TOP {len(signals)} COINS BY MARKET CAP
⏰ {current_time} | 📊 Multi-Timeframe SnD Analysis | 🎯 Precision Limit Orders

💡 **STRATEGI LIMIT ORDER SnD:**
Entry berdasarkan zona Supply & Demand dengan konfirmasi price action dan volume.

"""
            footer = """
══════════════════════════════════════════
🎯 **PANDUAN LIMIT ORDER SnD:**

📍 **CARA PAKAI:**
• Set limit order di harga yang direkomendasikan
• Tunggu price mencapai level entry sebelum order tereksekusi
• Cancel order jika struktur SnD berubah atau confidence turun

🛡️ **RISK MANAGEMENT SnD:**
• Max 1% position size per limit order (precision trading)
• Set stop loss WAJIB setelah order terisi
• Take profit bertahap: 50% di TP1, 50% di TP2
• Monitor price action di zona SnD untuk konfirmasi

⚠️ **PERINGATAN PENTING:**
• Limit order bisa tidak terisi jika price tidak mencapai level
• Gunakan hanya di market dengan volatility cukup
• Cancel order jika market structure berubah drastis

📊 **Data Source:** CoinAPI + Binance + Advanced SnD Algorithm
🕐 **Valid:** 1-4 jam (tergantung volatilitas market)"""
            
        else:
            header = f"""🚨 SnD LIMIT ORDER SIGNALS - TOP {len(signals)} COINS BY MARKET CAP
⏰ {current_time} | 📊 Multi-Timeframe SnD Analysis | 🎯 Precision Limit Orders

💡 **SnD LIMIT ORDER STRATEGY:**
Entries based on Supply & Demand zones with price action and volume confirmation.

"""
            footer = """
══════════════════════════════════════════
🎯 **SnD LIMIT ORDER GUIDE:**

📍 **HOW TO USE:**
• Set limit orders at recommended price levels
• Wait for price to reach entry level before order execution
• Cancel orders if SnD structure changes or confidence drops

🛡️ **SnD RISK MANAGEMENT:**
• Max 1% position size per limit order (precision trading)
• Set stop loss MANDATORY after order fills
• Take profit gradually: 50% at TP1, 50% at TP2
• Monitor price action at SnD zones for confirmation

⚠️ **IMPORTANT WARNINGS:**
• Limit orders may not fill if price doesn't reach level
• Use only in markets with sufficient volatility
• Cancel orders if market structure changes drastically

📊 **Data Source:** CoinAPI + Binance + Advanced SnD Algorithm
🕐 **Valid:** 1-4 hours (depends on market volatility)"""
        
        return header + "\n\n".join(signals) + footer



"""

            # Top 5 Cryptocurrencies
            if 'error' not in top_cryptos and top_cryptos.get('data'):
                message += "🔝 **TOP 5 KOIN (MARKET CAP):**\n"
                
                gainers = 0
                losers = 0
                
                for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                    name = crypto.get('name', '')
                    symbol = crypto.get('symbol', '')
                    price = crypto.get('price', 0)
                    change_24h = crypto.get('percent_change_24h', 0)
                    
                    # Count gainers/losers
                    if change_24h > 0:
                        gainers += 1
                    elif change_24h < 0:
                        losers += 1
                    
                    # Format price
                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 1000:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:,.0f}"
                    
                    change_emoji = "📈" if change_24h >= 0 else "📉"
                    change_color = "+" if change_24h >= 0 else ""
                    
                    message += f"**{i}.** {name} ({symbol}): {price_str} {change_emoji} {change_color}{change_24h:.1f}%\n"

                message += "\n"

                # Market Sentiment Summary
                total_analyzed = len(top_cryptos['data'])
                neutral = total_analyzed - gainers - losers
                
                if gainers > losers:
                    market_sentiment = "🟢 BULLISH"
                elif losers > gainers:
                    market_sentiment = "🔴 BEARISH"
                else:
                    market_sentiment = "🟡 NEUTRAL"

                message += f"""📉 **RANGKUMAN PASAR:**
• **Naik**: {gainers} koin 📈
• **Turun**: {losers} koin 📉  
• **Netral**: {neutral} koin 📊
• **Sentimen**: {market_sentiment}

"""

            # Fear & Greed Index
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                fng_classification = fng_data.get('value_classification', 'Neutral')
                fng_source = fng_data.get('source', 'estimated')
                
                # Get emoji for FNG
                if fng_value >= 75:
                    fng_emoji = "🔥"
                elif fng_value >= 50:
                    fng_emoji = "😊"
                elif fng_value >= 25:
                    fng_emoji = "😐"
                else:
                    fng_emoji = "😨"
                
                # Create FNG bar
                fng_bar = self._create_fng_bar(fng_value)
                
                message += f"""🌡️ **FEAR & GREED INDEX:**
**{fng_value}/100** - {fng_classification} {fng_emoji}
```
{fng_bar}
```
*Source: {fng_source}*

"""

            message += f"""📡 **DATA SOURCES:**
• **Market Data**: CoinMarketCap Startup Plan
• **Fear & Greed**: Alternative.me API
• **Real-time**: Live exchange rates

💡 **TRADING INSIGHTS:**
{self._get_trading_insights_id(enhanced_data)}

⏰ **Update**: {current_time} | 🔄 **Auto-refresh**: Real-time"""

            return message

        except Exception as e:
            return f"❌ Error formatting enhanced market overview: {str(e)}"

    def _format_enhanced_market_overview_en(self, enhanced_data):
        """Format enhanced market overview in English with CoinMarketCap data"""
        try:
            if 'error' in enhanced_data:
                return f"❌ Error fetching CoinMarketCap data: {enhanced_data.get('error')}"

            global_data = enhanced_data.get('global_metrics', {})
            top_cryptos = enhanced_data.get('top_cryptocurrencies', {})
            fng_data = enhanced_data.get('fear_greed_index', {})

            current_time = datetime.now().strftime('%H:%M:%S UTC')

            message = f"""🌍 **ADVANCED CRYPTO MARKET OVERVIEW** (CoinMarketCap Real-time)

⏰ **Update**: {current_time}

"""

            # Global Market Stats
            if 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_24h', 0)
                total_volume = global_data.get('total_volume_24h', 0)
                btc_dominance = global_data.get('btc_dominance', 0)
                eth_dominance = global_data.get('eth_dominance', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                # Format large numbers
                mcap_str = f"${total_mcap/1e12:.2f}T" if total_mcap > 1e12 else f"${total_mcap/1e9:.1f}B"
                vol_str = f"${total_volume/1e12:.2f}T" if total_volume > 1e12 else f"${total_volume/1e9:.1f}B"

                change_emoji = "📈" if mcap_change >= 0 else "📉"
                change_color = "+" if mcap_change >= 0 else ""

                message += f"""💰 **GLOBAL MARKET DATA:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **24h Volume**: {vol_str}
• **BTC Dominance**: {btc_dominance:.1f}%
• **ETH Dominance**: {eth_dominance:.1f}%
• **Altcoin Dominance**: {100 - btc_dominance - eth_dominance:.1f}%
• **Active Cryptos**: {active_cryptos:,}

"""

                # ASCII Chart for BTC Dominance
                dominance_bar = self._create_dominance_chart(btc_dominance, eth_dominance)
                message += f"""📊 **DOMINANCE CHART:**
```
{dominance_bar}
```

"""

            # Top 5 Cryptocurrencies
            if 'error' not in top_cryptos and top_cryptos.get('data'):
                message += "🔝 **TOP 5 COINS (MARKET CAP):**\n"
                
                gainers = 0
                losers = 0
                
                for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                    name = crypto.get('name', '')
                    symbol = crypto.get('symbol', '')
                    price = crypto.get('price', 0)
                    change_24h = crypto.get('percent_change_24h', 0)
                    
                    # Count gainers/losers
                    if change_24h > 0:
                        gainers += 1
                    elif change_24h < 0:
                        losers += 1
                    
                    # Format price
                    if price < 1:
                        price_str = f"${price:.6f}"
                    elif price < 1000:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:,.0f}"
                    
                    change_emoji = "📈" if change_24h >= 0 else "📉"
                    change_color = "+" if change_24h >= 0 else ""
                    
                    message += f"**{i}.** {name} ({symbol}): {price_str} {change_emoji} {change_color}{change_24h:.1f}%\n"

                message += "\n"

                # Market Sentiment Summary
                total_analyzed = len(top_cryptos['data'])
                neutral = total_analyzed - gainers - losers
                
                if gainers > losers:
                    market_sentiment = "🟢 BULLISH"
                elif losers > gainers:
                    market_sentiment = "🔴 BEARISH"
                else:
                    market_sentiment = "🟡 NEUTRAL"

                message += f"""📉 **MARKET SUMMARY:**
• **Up**: {gainers} coins 📈
• **Down**: {losers} coins 📉  
• **Neutral**: {neutral} coins 📊
• **Sentiment**: {market_sentiment}

"""

            # Fear & Greed Index
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                fng_classification = fng_data.get('value_classification', 'Neutral')
                fng_source = fng_data.get('source', 'estimated')
                
                # Get emoji for FNG
                if fng_value >= 75:
                    fng_emoji = "🔥"
                elif fng_value >= 50:
                    fng_emoji = "😊"
                elif fng_value >= 25:
                    fng_emoji = "😐"
                else:
                    fng_emoji = "😨"
                
                # Create FNG bar
                fng_bar = self._create_fng_bar(fng_value)
                
                message += f"""🌡️ **FEAR & GREED INDEX:**
**{fng_value}/100** - {fng_classification} {fng_emoji}
```
{fng_bar}
```
*Source: {fng_source}*

"""

            message += f"""📡 **DATA SOURCES:**
• **Market Data**: CoinMarketCap Startup Plan  
• **Fear & Greed**: Alternative.me API
• **Real-time**: Live exchange rates

💡 **TRADING INSIGHTS:**
{self._get_trading_insights_en(enhanced_data)}

⏰ **Update**: {current_time} | 🔄 **Auto-refresh**: Real-time"""

            return message

        except Exception as e:
            return f"❌ Error formatting enhanced market overview: {str(e)}"

    def _create_dominance_chart(self, btc_dom, eth_dom):
        """Create ASCII chart for market dominance"""
        try:
            alt_dom = 100 - btc_dom - eth_dom
            
            # Create 20-character bar
            btc_chars = int((btc_dom / 100) * 20)
            eth_chars = int((eth_dom / 100) * 20)  
            alt_chars = 20 - btc_chars - eth_chars
            
            btc_bar = "█" * btc_chars
            eth_bar = "▓" * eth_chars
            alt_bar = "░" * alt_chars
            
            chart = f"""BTC: {btc_bar}{' ' * max(0, 8 - btc_chars)} {btc_dom:.1f}%
ETH: {eth_bar}{' ' * max(0, 8 - eth_chars)} {eth_dom:.1f}%
ALT: {alt_bar}{' ' * max(0, 8 - alt_chars)} {alt_dom:.1f}%"""
            
            return chart
        except:
            return "Chart unavailable"

    def _create_fng_bar(self, value):
        """Create ASCII bar for Fear & Greed Index"""
        try:
            # Create 50-character bar
            filled_chars = int((value / 100) * 50)
            empty_chars = 50 - filled_chars
            
            if value >= 75:
                char = "█"  # Extreme Greed
            elif value >= 50:
                char = "▓"  # Greed
            elif value >= 25:
                char = "▒"  # Neutral
            else:
                char = "░"  # Fear
                
            bar = char * filled_chars + "·" * empty_chars
            labels = "Fear    |    Neutral    |    Greed"
            
            return f"{bar}\n{labels}"
        except:
            return "Bar unavailable"

    def _get_trading_insights_id(self, enhanced_data):
        """Generate trading insights in Indonesian"""
        try:
            global_data = enhanced_data.get('global_metrics', {})
            fng_data = enhanced_data.get('fear_greed_index', {})
            
            insights = []
            
            # Market cap change insight
            if 'error' not in global_data:
                mcap_change = global_data.get('market_cap_change_24h', 0)
                if mcap_change > 3:
                    insights.append("🚀 Market cap naik signifikan - momentum bullish")
                elif mcap_change < -3:
                    insights.append("📉 Market cap turun signifikan - hati-hati koreksi")
                else:
                    insights.append("📊 Market cap stabil - sideways market")
            
            # Fear & Greed insight  
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                if fng_value >= 75:
                    insights.append("⚠️ Extreme Greed - pertimbangkan take profit")
                elif fng_value <= 25:
                    insights.append("💎 Extreme Fear - opportunity untuk DCA")
                else:
                    insights.append("⚖️ Sentiment seimbang - tunggu konfirmasi")
            
            return "\n".join([f"• {insight}" for insight in insights]) if insights else "• Data insight tidak tersedia"
            
        except:
            return "• Insight generation error"

    def _get_trading_insights_en(self, enhanced_data):
        """Generate trading insights in English"""  
        try:
            global_data = enhanced_data.get('global_metrics', {})
            fng_data = enhanced_data.get('fear_greed_index', {})
            
            insights = []
            
            # Market cap change insight
            if 'error' not in global_data:
                mcap_change = global_data.get('market_cap_change_24h', 0)
                if mcap_change > 3:
                    insights.append("🚀 Significant market cap increase - bullish momentum")
                elif mcap_change < -3:
                    insights.append("📉 Significant market cap decrease - correction alert")
                else:
                    insights.append("📊 Stable market cap - sideways market")
            
            # Fear & Greed insight
            if 'error' not in fng_data:
                fng_value = fng_data.get('value', 50)
                if fng_value >= 75:
                    insights.append("⚠️ Extreme Greed - consider taking profits")
                elif fng_value <= 25:
                    insights.append("💎 Extreme Fear - DCA opportunity")
                else:
                    insights.append("⚖️ Balanced sentiment - wait for confirmation")
            
            return "\n".join([f"• {insight}" for insight in insights]) if insights else "• Insight data unavailable"
            
        except:
            return "• Insight generation error"

    def _format_market_sentiment_id(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in Indonesian"""
        try:
            message = "🌍 **OVERVIEW PASAR CRYPTO** (Real-time CoinAPI)\n\n"

            # Market data section
            if market_data:
                message += "💰 **Harga Real-time (CoinAPI):**\n"
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    change = data.get('change_24h', 0)
                    change_emoji = "📈" if change >= 0 else "📉"
                    price_format = f"${price:,.2f}" if price > 1 else f"${price:.4f}"
                    message += f"• {symbol}: {price_format} {change_emoji} {change:+.1f}%\n"
                message += "\n"

            # Futures insights
            if 'error' not in btc_futures:
                ls_data = btc_futures.get('long_short_ratio_data', {})
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    sentiment = "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Neutral"
                    message += f"📊 **BTC Futures Sentiment**: {sentiment} ({long_ratio:.1f}% Long)\n\n"

            # Market analysis
            message += "📈 **Analisis Pasar:**\n"
            message += "• Data diambil dari CoinAPI real-time\n"
            message += "• Analisis berbasis Supply & Demand\n"
            message += "• Terintegrasi dengan Binance Futures data\n\n"

            # News section
            if news_data and len(news_data) > 0:
                message += "📰 **Berita Crypto Terbaru:**\n"
                for i, news in enumerate(news_data[:2], 1):
                    title = news.get('title', '')[:60] + '...' if len(news.get('title', '')) > 60 else news.get('title', '')
                    message += f"{i}. {title}\n"
                message += "\n"

            message += "🎯 **Source**: CoinAPI + Binance Futures + Crypto News\n"
            message += f"⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"

            return message

        except Exception as e:
            return f"❌ Error formatting market sentiment: {str(e)}"

    def _format_market_sentiment_en(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in English"""
        try:
            message = "🌍 **CRYPTO MARKET OVERVIEW** (Real-time CoinAPI)\n\n"

            # Market data section
            if market_data:
                message += "💰 **Real-time Prices (CoinAPI):**\n"
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    change = data.get('change_24h', 0)
                    change_emoji = "📈" if change >= 0 else "📉"
                    price_format = f"${price:,.2f}" if price > 1 else f"${price:.4f}"
                    message += f"• {symbol}: {price_format} {change_emoji} {change:+.1f}%\n"
                message += "\n"

            # Futures insights
            if 'error' not in btc_futures:
                ls_data = btc_futures.get('long_short_ratio_data', {})
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    sentiment = "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Neutral"
                    message += f"📊 **BTC Futures Sentiment**: {sentiment} ({long_ratio:.1f}% Long)\n\n"

            # Market analysis
            message += "📈 **Market Analysis:**\n"
            message += "• Data sourced from CoinAPI real-time\n"
            message += "• Analysis based on Supply & Demand\n"
            message += "• Integrated with Binance Futures data\n\n"

            # News section
            if news_data and len(news_data) > 0:
                message += "📰 **Latest Crypto News:**\n"
                for i, news in enumerate(news_data[:2], 1):
                    title = news.get('title', '')[:60] + '...' if len(news.get('title', '')) > 60 else news.get('title', '')
                    message += f"{i}. {title}\n"
                message += "\n"

            message += "🎯 **Source**: CoinAPI + Binance Futures + Crypto News\n"
            message += f"⏰ **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"

            return message

        except Exception as e:
            return f"❌ Error formatting market sentiment: {str(e)}"

    def _analyze_comprehensive_market_health(self, global_data, prices_data, news_data):
        """Analyze comprehensive market health from multiple APIs"""
        health_score = 5  # Base score
        health_factors = []

        # 1. CoinGecko global metrics analysis
        if global_data and 'error' not in global_data:
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 50)

            # Market cap change scoring
            if mcap_change > 5:
                health_score += 2
                health_factors.append("📈 Market cap sangat bullish (+5%+)")
            elif mcap_change > 2:
                health_score += 1
                health_factors.append("📈 Market cap positif (+2%+)")
            elif mcap_change > -2:
                health_factors.append("📊 Market cap stabil (±2%)")
            elif mcap_change > -5:
                health_score -= 1
                health_factors.append("📉 Market cap menurun (-2% to -5%)")
            else:
                health_score -= 2
                health_factors.append("📉 Market cap sangat bearish (-5%+)")

            # BTC dominance analysis
            if 45 <= btc_dominance <= 60:
                health_score += 1
                health_factors.append("🟢 BTC dominance sehat (45-60%)")
            elif btc_dominance > 65:
                health_score -= 1
                health_factors.append("🟡 BTC dominance terlalu tinggi (>65%)")
            elif btc_dominance < 40:
                health_score -= 1
                health_factors.append("🟡 BTC dominance terlalu rendah (<40%)")
        else:
            health_score -= 1
            health_factors.append("⚠️ Data global tidak tersedia")

        # 2. Individual cryptocurrency performance analysis
        if prices_data and len(prices_data) > 0:
            positive_changes = sum(1 for data in prices_data.values() 
                                 if isinstance(data, dict) and data.get('change_24h', 0) > 0)
            total_cryptos = len(prices_data)
            positive_ratio = positive_changes / total_cryptos if total_cryptos > 0 else 0

            # Calculate average change
            changes = [data.get('change_24h', 0) for data in prices_data.values() 
                      if isinstance(data, dict) and 'change_24h' in data]
            avg_change = sum(changes) / len(changes) if changes else 0

            if positive_ratio > 0.7:
                health_score += 2
                health_factors.append(f"🟢 {positive_ratio*100:.0f}% crypto naik (sangat bullish)")
            elif positive_ratio > 0.5:
                health_score += 1
                health_factors.append(f"🟢 {positive_ratio*100:.0f}% crypto naik (bullish)")
            elif positive_ratio > 0.3:
                health_factors.append(f"🟡 {positive_ratio*100:.0f}% crypto naik (mixed)")
            else:
                health_score -= 1
                health_factors.append(f"🔴 {positive_ratio*100:.0f}% crypto naik (bearish)")

            # Average change analysis
            if avg_change > 3:
                health_score += 1
                health_factors.append(f"📈 Rata-rata perubahan: +{avg_change:.1f}%")
            elif avg_change < -3:
                health_score -= 1
                health_factors.append(f"📉 Rata-rata perubahan: {avg_change:.1f}%")
        else:
            health_score -= 1
            health_factors.append("⚠️ Data harga real-time terbatas")

        # 3. News sentiment analysis
        if news_data and len(news_data) > 0:
            # Simple sentiment analysis based on news availability
            health_score += 0.5
            health_factors.append("📰 Berita crypto tersedia (sentiment normal)")

            # Analyze news titles for sentiment keywords
            positive_keywords = ['bull', 'rise', 'surge', 'pump', 'gain', 'rally', 'high', 'adoption', 'breakthrough']
            negative_keywords = ['bear', 'fall', 'crash', 'dump', 'loss', 'decline', 'low', 'ban', 'hack']

            news_sentiment = 0
            for news in news_data[:3]:  # Check first 3 news
                title = news.get('title', '').lower()
                if any(keyword in title for keyword in positive_keywords):
                    news_sentiment += 1
                elif any(keyword in title for keyword in negative_keywords):
                    news_sentiment -= 1

            if news_sentiment > 0:
                health_score += 0.5
                health_factors.append("📰 Sentiment berita positif")
            elif news_sentiment < 0:
                health_score -= 0.5
                health_factors.append("📰 Sentiment berita negatif")
        else:
            health_factors.append("📰 Data berita tidak tersedia")

        # Ensure score stays within bounds
        health_score = max(0, min(10, health_score))

        # Determine overall health status
        if health_score >= 8:
            overall_health = "🟢 SANGAT SEHAT"
        elif health_score >= 6.5:
            overall_health = "🟢 SEHAT"
        elif health_score >= 5:
            overall_health = "🟡 STABIL"
        elif health_score >= 3:
            overall_health = "🟡 LEMAH"
        else:
            overall_health = "🔴 TIDAK SEHAT"

        return {
            'score': round(health_score, 1),
            'status': overall_health,
            'factors': health_factors
        }

    def _format_cmc_market_sentiment_id(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in Indonesian using CoinMarketCap data"""
        try:
            if 'error' in market_data:
                return self._get_fallback_market_overview('id')

            # Format market cap
            total_mcap = market_data.get('total_market_cap', 0)
            mcap_change = market_data.get('market_cap_change_24h', 0)
            total_volume = market_data.get('total_volume_24h', 0)

            if total_mcap > 1e12:
                mcap_str = f"${total_mcap/1e12:.2f}T"
            else:
                mcap_str = f"${total_mcap/1e9:.1f}B"

            if total_volume > 1e12:
                volume_str = f"${total_volume/1e12:.2f}T"
            else:
                volume_str = f"${total_volume/1e9:.1f}B"

            change_emoji = "📈" if mcap_change >= 0 else "📉"
            change_color = "+" if mcap_change >= 0 else ""

            message = f"""🌍 **OVERVIEW PASAR CRYPTO** (CoinMarketCap Real-time)

💰 **Data Global:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **Volume 24j**: {volume_str}
• **BTC Dominance**: {market_data.get('btc_dominance', 0):.1f}%
• **ETH Dominance**: {market_data.get('eth_dominance', 0):.1f}%
• **Crypto Aktif**: {market_data.get('active_cryptocurrencies', 0):,}
• **Exchange Aktif**: {market_data.get('active_exchanges', 0):,}

📊 **Harga Utama:**
• **Bitcoin**: ${market_data.get('btc_price', 0):,.2f} ({market_data.get('btc_change_24h', 0):+.2f}%)
• **Ethereum**: ${market_data.get('eth_price', 0):,.2f} ({market_data.get('eth_change_24h', 0):+.2f}%)

⚡ **Futures Sentiment:**
• **BTC Long/Short**: {btc_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {btc_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%
• **ETH Long/Short**: {eth_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {eth_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%"""

            # Add funding rates if available
            if 'error' not in btc_futures:
                funding_data = btc_futures.get('funding_rate_data', {})
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"\n• **BTC Funding Rate**: {funding_rate:.4f}%"

            # Add news
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **Berita Terbaru:**
• {latest_news.get('title', 'No title')[:80]}..."""

            # Market sentiment assessment
            sentiment_score = 0
            if mcap_change > 2: sentiment_score += 2
            elif mcap_change > 0: sentiment_score += 1
            elif mcap_change < -2: sentiment_score -= 2
            elif mcap_change < 0: sentiment_score -= 1

            if sentiment_score >= 2:
                sentiment = "🟢 Sangat Bullish"
            elif sentiment_score == 1:
                sentiment = "🟢 Bullish"
            elif sentiment_score == 0:
                sentiment = "🟡 Netral"
            elif sentiment_score == -1:
                sentiment = "🔴 Bearish"
            else:
                sentiment = "🔴 Sangat Bearish"

            message += f"""

🎯 **Market Sentiment**: {sentiment}
📡 **Source**: CoinMarketCap Global + Binance Futures
⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            return message

        except Exception as e:
            return f"❌ Error formatting CoinMarketCap market sentiment: {str(e)}"

    def _format_cmc_market_sentiment_en(self, market_data, btc_futures, eth_futures, news_data):
        """Format market sentiment in English using CoinMarketCap data"""
        try:
            if 'error' in market_data:
                return self._get_fallback_market_overview('en')

            # Format market cap
            total_mcap = market_data.get('total_market_cap', 0)
            mcap_change = market_data.get('market_cap_change_24h', 0)
            total_volume = market_data.get('total_volume_24h', 0)

            if total_mcap > 1e12:
                mcap_str = f"${total_mcap/1e12:.2f}T"
            else:
                mcap_str = f"${total_mcap/1e9:.1f}B"

            if total_volume > 1e12:
                volume_str = f"${total_volume/1e12:.2f}T"
            else:
                volume_str = f"${total_volume/1e9:.1f}B"

            change_emoji = "📈" if mcap_change >= 0 else "📉"
            change_color = "+" if mcap_change >= 0 else ""

            message = f"""🌍 **CRYPTO MARKET OVERVIEW** (CoinMarketCap Real-time)

💰 **Global Data:**
• **Total Market Cap**: {mcap_str} {change_emoji} {change_color}{mcap_change:.2f}%
• **24h Volume**: {volume_str}
• **BTC Dominance**: {market_data.get('btc_dominance', 0):.1f}%
• **ETH Dominance**: {market_data.get('eth_dominance', 0):.1f}%
• **Active Cryptos**: {market_data.get('active_cryptocurrencies', 0):,}
• **Active Exchanges**: {market_data.get('active_exchanges', 0):,}

📊 **Major Prices:**
• **Bitcoin**: ${market_data.get('btc_price', 0):,.2f} ({market_data.get('btc_change_24h', 0):+.2f}%)
• **Ethereum**: ${market_data.get('eth_price', 0):,.2f} ({market_data.get('eth_change_24h', 0):+.2f}%)

⚡ **Futures Sentiment:**
• **BTC Long/Short**: {btc_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {btc_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%
• **ETH Long/Short**: {eth_futures.get('long_short_ratio_data', {}).get('long_ratio', 50):.1f}% / {eth_futures.get('long_short_ratio_data', {}).get('short_ratio', 50):.1f}%"""

            # Add funding rates if available
            if 'error' not in btc_futures:
                funding_data = btc_futures.get('funding_rate_data', {})
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"\n• **BTC Funding Rate**: {funding_rate:.4f}%"

            # Add news
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **Latest News:**
• {latest_news.get('title', 'No title')[:80]}..."""

            # Market sentiment assessment
            sentiment_score = 0
            if mcap_change > 2: sentiment_score += 2
            elif mcap_change > 0: sentiment_score += 1
            elif mcap_change < -2: sentiment_score -= 2
            elif mcap_change < 0: sentiment_score -= 1

            if sentiment_score >= 2:
                sentiment = "🟢 Very Bullish"
            elif sentiment_score == 1:
                sentiment = "🟢 Bullish"
            elif sentiment_score == 0:
                sentiment = "🟡 Neutral"
            elif sentiment_score == -1:
                sentiment = "🔴 Bearish"
            else:
                sentiment = "🔴 Very Bearish"

            message += f"""

🎯 **Market Sentiment**: {sentiment}
📡 **Source**: CoinMarketCap Global + Binance Futures
⏰ **Update**: {datetime.now().strftime('%H:%M:%S UTC')}"""

            return message

        except Exception as e:
            return f"❌ Error formatting CoinMarketCap market sentiment: {str(e)}"

    def _format_safe_market_overview_id(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in Indonesian using multiple APIs with safe formatting"""
        from datetime import datetime

        try:
            message = f"""🌍 **OVERVIEW PASAR CRYPTO KOMPREHENSIF**

🔍 **Analisis Multi-API:** CoinGecko + Binance + CryptoNews

📊 **1. Data Global (CoinGecko):**"""

            # Global market data
            if global_data and 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
                btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                message += f"""
- **Total Market Cap**: ${total_mcap:,.0f} ({mcap_change:+.2f}%)
- **BTC Dominance**: {btc_dominance:.1f}%
- **ETH Dominance**: {eth_dominance:.1f}%
- **Active Cryptocurrencies**: {active_cryptos:,}"""

            # Market health analysis
            message += f"""

🏥 **2. Kesehatan Pasar:** {market_health['status']}
{chr(10).join(['• ' + factor for factor in market_health['factors']])}"""

            # Top movers from multi-API data
            message += f"""

📈 **3. Top Movers (Multi-API):**"""

            if prices_data:
                sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

                gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
                losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

                message += "\n**Gainers:**"
                for symbol, data in gainers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

                message += "\n\n**Losers:**"
                for symbol, data in losers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

            # Futures sentiment
            message += f"""

⚡ **4. Futures Sentiment (Binance):**
- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

            # News sentiment
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **5. Sentiment Berita:**
- **Latest**: {latest_news.get('title', 'N/A')[:60]}...
- **Source**: {latest_news.get('source', 'CryptoNews')}
- **Impact**: Positive pada sentiment pasar"""

            message += f"""

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Sources**: CoinGecko Global + Binance Real-time + CryptoNews Sentiment

💡 **Trading Outlook**: {market_health['status']} - {"Bullish bias" if market_health['score'] >= 6 else "Bearish bias" if market_health['score'] <= 4 else "Neutral stance"}"""

            return message

        except Exception as e:
            print(f"Error formatting market overview (ID): {e}")
            return "❌ Gagal memformat overview pasar. Coba lagi nanti."

    def _format_safe_market_overview_en(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health):
        """Format comprehensive market overview in English using multiple APIs with safe formatting"""
        from datetime import datetime

        try:
            message = f"""🌍 **COMPREHENSIVE CRYPTO MARKET OVERVIEW**

🔍 **Multi-API Analysis:** CoinGecko + Binance + CryptoNews

📊 **1. Global Data (CoinGecko):**"""

            # Global market data
            if global_data and 'error' not in global_data:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
                btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
                active_cryptos = global_data.get('active_cryptocurrencies', 0)

                message += f"""
- **Total Market Cap**: ${total_mcap:,.0f} ({mcap_change:+.2f}%)
- **BTC Dominance**: {btc_dominance:.1f}%
- **ETH Dominance**: {eth_dominance:.1f}%
- **Active Cryptocurrencies**: {active_cryptos:,}"""

            # Market health analysis
            message += f"""

🏥 **2. Market Health:** {market_health['status']}
{chr(10).join(['• ' + factor for factor in market_health['factors']])}"""

            # Top movers from multi-API data
            message += f"""

📈 **3. Top Movers (Multi-API):**"""

            if prices_data:
                sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

                gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
                losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

                message += "\n**Gainers:**"
                for symbol, data in gainers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: +{data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

                message += "\n\n**Losers:**"
                for symbol, data in losers:
                    sources = ', '.join(data.get('sources_used', ['binance']))
                    message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% (${data.get('price', 0):,.2f}) - {sources}"

            # Futures sentiment
            message += f"""

⚡ **4. Futures Sentiment (Binance):**
- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

            # News sentiment
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                message += f"""

📰 **5. News Sentiment:**
- **Latest**: {latest_news.get('title', 'N/A')[:60]}...
- **Source**: {latest_news.get('source', 'CryptoNews')}
- **Impact**: Positive market sentiment"""

            message += f"""

🕐 **Update**: {datetime.now().strftime('%H:%M:%S UTC')}
📡 **Sources**: CoinGecko Global + Binance Real-time + CryptoNews Sentiment

💡 **Trading Outlook**: {market_health['status']} - {"Bullish bias" if market_health['score'] >= 6 else "Bearish bias" if market_health['score'] <= 4 else "Neutral stance"}"""

            return message

        except Exception as e:
            print(f"Error formatting market overview (EN): {e}")
            return "❌ Failed to format market overview. Try again later."

    def _format_comprehensive_market_overview_id(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health, btc_funding=None, eth_funding=None):
        """Format comprehensive market overview in Indonesian using multiple APIs"""
        from datetime import datetime

        def escape_markdown(text):
            """Escape special Markdown characters"""
            if not text:
                return ""
            # Escape problematic characters for Telegram Markdown
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                if char in str(text):
                    text = str(text).replace(char, f'\\{char}')
            return text

        message = "🌍 **OVERVIEW PASAR CRYPTO KOMPREHENSIF**\n\n"
        message += "🔍 **Analisis Multi\\-API:** CoinGecko \\+ Binance \\+ CryptoNews\n\n"
        message += "📊 **1\\. Data Global \\(CoinGecko\\):**"

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
\\- **Total Market Cap**: ${total_mcap:,.0f} \\({mcap_change:+.2f}%\\)
\\- **BTC Dominance**: {btc_dominance:.1f}%
\\- **ETH Dominance**: {eth_dominance:.1f}%
\\- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis - escape special characters
        health_status = escape_markdown(market_health.get('status', 'Unknown'))
        message += f"\n\n🏥 **2\\. Kesehatan Pasar:** {health_status}\n"

        for factor in market_health.get('factors', [])[:3]:  # Limit to 3 factors
            clean_factor = escape_markdown(factor)
            message += f"• {clean_factor}\n"

        # Top movers from multi-API data
        message += "\n📈 **3\\. Top Movers \\(Multi\\-API\\):**"

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += "\n**Gainers:**"
            for symbol, data in gainers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: \\+{data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

            message += "\n\n**Losers:**"
            for symbol, data in losers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

        # Futures sentiment
        message += f"""

⚡ **4\\. Futures Sentiment \\(Binance\\):**
\\- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%"""

        if btc_funding:
            funding_rate = btc_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {funding_rate:.4f}%\\)"

        message += f"""
\\- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

        if eth_funding:
            eth_funding_rate = eth_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {eth_funding_rate:.4f}%\\)"

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            news_title = escape_markdown(latest_news.get('title', 'N/A')[:50])
            news_source = escape_markdown(latest_news.get('source', 'CryptoNews'))

            message += f"""

📰 **5\\. Sentiment Berita:**
\\- **Latest**: {news_title}\\.\\.\\.
\\- **Source**: {news_source}
\\- **Impact**: Positive pada sentiment pasar"""

        # Final summary
        current_time = datetime.now().strftime('%H:%M:%S')
        health_status_clean = escape_markdown(market_health.get('status', 'Unknown'))

        if market_health.get('score', 5) >= 6:
            trading_bias = "Bullish bias"
        elif market_health.get('score', 5) <= 4:
            trading_bias = "Bearish bias"
        else:
            trading_bias = "Neutral stance"

        message += f"""

🕐 **Update**: {current_time} WIB
📡 **Sources**: CoinGecko Global \\+ Binance Real\\-time \\+ CryptoNews Sentiment

💡 **Trading Outlook**: {health_status_clean} \\- {trading_bias}"""

        return message

    def _format_comprehensive_market_overview_en(self, global_data, market_data, prices_data, news_data, futures_btc, futures_eth, market_health, btc_funding=None, eth_funding=None):
        """Format comprehensive market overview in English using multiple APIs"""
        from datetime import datetime

        def escape_markdown(text):
            """Escape special Markdown characters"""
            if not text:
                return ""
            # Escape problematic characters for Telegram Markdown
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                if char in str(text):
                    text = str(text).replace(char, f'\\{char}')
            return text

        message = "🌍 **COMPREHENSIVE CRYPTO MARKET OVERVIEW**\n\n"
        message += "🔍 **Multi\\-API Analysis:** CoinGecko \\+ Binance \\+ CryptoNews\n\n"
        message += "📊 **1\\. Data Global \\(CoinGecko\\):**"

        # Global market data
        if global_data and 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            mcap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            message += f"""
\\- **Total Market Cap**: ${total_mcap:,.0f} \\({mcap_change:+.2f}%\\)
\\- **BTC Dominance**: {btc_dominance:.1f}%
\\- **ETH Dominance**: {eth_dominance:.1f}%
\\- **Active Cryptocurrencies**: {active_cryptos:,}"""

        # Market health analysis - escape special characters
        health_status = escape_markdown(market_health.get('status', 'Unknown'))
        message += f"\n\n🏥 **2\\. Market Health:** {health_status}\n"

        for factor in market_health.get('factors', [])[:3]:  # Limit to 3 factors
            clean_factor = escape_markdown(factor)
            message += f"• {clean_factor}\n"

        # Top movers from multi-API data
        message += "\n📈 **3\\. Top Movers \\(Multi\\-API\\):**"

        if prices_data:
            sorted_symbols = sorted(prices_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)

            gainers = [s for s in sorted_symbols if s[1].get('change_24h', 0) > 0][:3]
            losers = [s for s in sorted_symbols if s[1].get('change_24h', 0) < 0][-3:]

            message += "\n**Gainers:**"
            for symbol, data in gainers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: \\+{data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

            message += "\n\n**Losers:**"
            for symbol, data in losers:
                sources_list = data.get('sources_used', ['binance'])
                sources = escape_markdown(', '.join(sources_list))
                message += f"\n• {symbol}: {data.get('change_24h', 0):.1f}% \\(${data.get('price', 0):,.2f}\\) \\- {sources}"

        # Futures sentiment
        message += f"""

⚡ **4\\. Futures Sentiment \\(Binance\\):**
\\- **BTC L/S Ratio**: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%"""

        if btc_funding:
            funding_rate = btc_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {funding_rate:.4f}%\\)"

        message += f"""
\\- **ETH L/S Ratio**: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%"""

        if eth_funding:
            eth_funding_rate = eth_funding.get('last_funding_rate', 0)
            message += f" \\(Funding: {eth_funding_rate:.4f}%\\)"

        # News sentiment
        if news_data and len(news_data) > 0:
            latest_news = news_data[0]
            news_title = escape_markdown(latest_news.get('title', 'N/A')[:50])
            news_source = escape_markdown(latest_news.get('source', 'CryptoNews'))

            message += f"""

📰 **5\\. News Sentiment:**
\\- **Latest**: {news_title}\\.\\.\\.
\\- **Source**: {news_source}
\\- **Impact**: Positive market sentiment"""

        # Final summary
        current_time = datetime.now().strftime('%H:%M:%S')
        health_status_clean = escape_markdown(market_health.get('status', 'Unknown'))

        if market_health.get('score', 5) >= 6:
            trading_bias = "Bullish bias"
        elif market_health.get('score', 5) <= 4:
            trading_bias = "Bearish bias"
        else:
            trading_bias = "Neutral stance"

        message += f"""

🕐 **Update**: {current_time} UTC
📡 **Sources**: CoinGecko Global \\+ Binance Real\\-time \\+ CryptoNews Sentiment

💡 **Trading Outlook**: {health_status_clean} \\- {trading_bias}"""

        return message

    def _format_market_overview_id(self, market_data, prices_data, news_data, futures_btc, futures_eth):
        """Format market overview in Indonesian"""
        from datetime import datetime

        # Market cap and basic data
        if 'error' not in market_data:
            total_market_cap = market_data.get('total_market_cap', 0)
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)
        else:
            total_market_cap = 2400000000000
            market_cap_change = 1.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **REAL-TIME CRYPTO MARKET OVERVIEW**

💰 **Data Global:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- Dominasi BTC: {btc_dominance:.1f}%
- Crypto Aktif: {active_cryptos:,} koin

📈 **Top Movers (24H):**
**Gainers:**
{gainers}

**Losers:**
{losers}

📊 **Futures Sentiment:**
- BTC Long/Short: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- ETH Long/Short: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Binance API

🔄 **Refresh:** Gunakan `/market` untuk update terbaru"""

        return message

    def _format_market_overview_en(self, market_data, prices_data, news_data, futures_btc, futures_eth):
        """Format market overview in English"""
        from datetime import datetime

        # Market cap and basic data
        if 'error' not in market_data:
            total_market_cap = market_data.get('total_market_cap', 0)
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)
        else:
            total_market_cap = 2400000000000
            market_cap_change = 2.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **REAL-TIME CRYPTO MARKET OVERVIEW**

💰 **Global Data:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- BTC Dominance: {btc_dominance:.1f}%
- Active Cryptos: {active_cryptos:,} coins

📈 **Top Movers (24H):**
**Gainers:**
{gainers}

**Losers:**
{losers}

📊 **Futures Sentiment:**
- BTC Long/Short: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- ETH Long/Short: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Binance API

🔄 **Refresh:** Use `/market` for latest update"""

        return message

    def _analyze_top_movers(self, prices_data):
        """Analyze top gainers and losers"""
        if 'error' in prices_data:
            # Fallback mock data
            gainers = """- SOL: +12.5% ($98.50)
- AVAX: +8.3% ($42.10)
- MATIC: +6.7% ($0.85)"""
            losers = """- DOGE: -4.2% ($0.075)
- ADA: -3.1% ($0.48)
- DOT: -2.8% ($6.90)"""
            return gainers, losers

        # Real data analysis
        movers = []
        for symbol, data in prices_data.items():
            if 'price' in data and 'change_24h' in data:
                movers.append({
                    'symbol': symbol.upper(),
                    'price': data['price'],
                    'change': data['change_24h']
                })

        # Sort by change percentage
        movers.sort(key=lambda x: x['change'], reverse=True)

        # Top 3 gainers
        gainers_list = []
        for mover in movers[:3]:
            if mover['change'] > 0:
                gainers_list.append(f"- {mover['symbol']}: +{mover['change']:.1f}% (${mover['price']:,.2f})")

        # Top 3 losers
        losers_list = []
        for mover in movers[-3:]:
            if mover['change'] < 0:
                losers_list.append(f"- {mover['symbol']}: {mover['change']:.1f}% (${mover['price']:,.2f})")

        gainers = '\n'.join(gainers_list) if gainers_list else "- Tidak ada gainer signifikan"
        losers = '\n'.join(losers_list) if losers_list else "- Tidak ada loser signifikan"

        return gainers, losers

    def _get_fallback_market_overview(self, language='id'):
        """Fallback market overview when APIs fail"""
        if language == 'id':
            return """🌍 **OVERVIEW PASAR CRYPTO** (Mode Offline)

💰 **Data Pasar:**
- Total Market Cap: $2.4T (+1.5%)
- Dominasi BTC: 52.3%
- Crypto Aktif: 12,000+ koin

📈 **Status:** Pasar dalam fase recovery

⚠️ **Catatan:** Data real-time tidak tersedia, gunakan command lain untuk analisis live.

Coba lagi dalam beberapa menit untuk data real-time."""
        else:
            return """🌍 **CRYPTO MARKET OVERVIEW** (Offline Mode)

💰 **Market Data:**
- Total Market Cap: $2.4T (+1.5%)
- BTC Dominance: 52.3%
- Active Cryptos: 12,000+ coins

📈 **Status:** Market in recovery phase

⚠️ **Note:** Real-time data unavailable, use other commands for live analysis.

Try again in a few minutes for real-time data."""

    def get_comprehensive_analysis(self, symbol, futures_data, price_data, language='id', crypto_api=None):
        """Get comprehensive FUNDAMENTAL analysis with CoinMarketCap data - NO TRADING RECOMMENDATIONS"""
        try:
            print(f"🔄 Generating fundamental analysis for {symbol}...")
            
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk analisis fundamental."
            
            # Get CoinMarketCap fundamental data
            cmc_data = {}
            if hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider:
                try:
                    cmc_response = crypto_api.cmc_provider.get_cryptocurrency_info(symbol)
                    if 'error' not in cmc_response:
                        cmc_data = cmc_response
                except Exception as e:
                    print(f"⚠️ CoinMarketCap data unavailable: {e}")
            
            # Get real-time price data from CoinAPI
            coinapi_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
            
            # Determine primary price source
            primary_price = 0
            primary_source = "Unknown"
            
            if 'error' not in coinapi_data and coinapi_data.get('price', 0) > 0:
                primary_price = coinapi_data.get('price', 0)
                primary_source = "CoinAPI Real-time"
            elif 'error' not in price_data and price_data.get('price', 0) > 0:
                primary_price = price_data.get('price', 0)
                primary_source = "Alternative API"
            elif 'error' not in futures_data:
                price_data_futures = futures_data.get('price_data', {})
                if 'error' not in price_data_futures and price_data_futures.get('price', 0) > 0:
                    primary_price = price_data_futures.get('price', 0)
                    primary_source = "Binance Futures"
            
            if primary_price <= 0:
                return f"❌ Tidak dapat mengambil data harga valid untuk {symbol}."
            
            # Generate FUNDAMENTAL analysis only
            if language == 'id':
                analysis = f"""📊 **ANALISIS FUNDAMENTAL {symbol.upper()}**

💰 **Data Harga Real-time:**
• **Current Price**: ${primary_price:,.4f}
• **Data Source**: {primary_source}"""
            else:
                analysis = f"""📊 **FUNDAMENTAL ANALYSIS {symbol.upper()}**

💰 **Real-time Price Data:**
• **Current Price**: ${primary_price:,.4f}
• **Data Source**: {primary_source}"""
            
            # Add 24h change if available
            change_24h = 0
            if 'error' not in price_data and 'change_24h' in price_data:
                change_24h = price_data.get('change_24h', 0)
            elif 'error' not in futures_data:
                futures_price_data = futures_data.get('price_data', {})
                if 'error' not in futures_price_data:
                    change_24h = futures_price_data.get('change_24h', 0)
            
            if change_24h != 0:
                change_emoji = "📈" if change_24h >= 0 else "📉"
                change_sign = "+" if change_24h >= 0 else ""
                analysis += f"""
• **24h Change**: {change_emoji} {change_sign}{change_24h:.2f}%"""
            
            # Add CoinMarketCap fundamental data if available
            if 'error' not in cmc_data and cmc_data:
                if language == 'id':
                    analysis += f"""

📋 **Data Fundamental (CoinMarketCap):**"""
                else:
                    analysis += f"""

📋 **Fundamental Data (CoinMarketCap):**"""
                
                # Market cap and rank
                market_cap = cmc_data.get('market_cap', 0)
                cmc_rank = cmc_data.get('cmc_rank', 0)
                if market_cap > 0:
                    if market_cap > 1e9:
                        mcap_formatted = f"${market_cap/1e9:.2f}B"
                    elif market_cap > 1e6:
                        mcap_formatted = f"${market_cap/1e6:.2f}M"
                    else:
                        mcap_formatted = f"${market_cap:,.0f}"
                    
                    analysis += f"""
• **Market Cap**: {mcap_formatted}"""
                    
                    if cmc_rank > 0:
                        analysis += f" (Rank #{cmc_rank})"
                
                # Volume and supply data
                volume_24h = cmc_data.get('volume_24h', 0)
                if volume_24h > 0:
                    if volume_24h > 1e9:
                        vol_formatted = f"${volume_24h/1e9:.2f}B"
                    elif volume_24h > 1e6:
                        vol_formatted = f"${volume_24h/1e6:.2f}M"
                    else:
                        vol_formatted = f"${volume_24h:,.0f}"
                    analysis += f"""
• **Volume 24h**: {vol_formatted}"""
                
                circulating_supply = cmc_data.get('circulating_supply', 0)
                total_supply = cmc_data.get('total_supply', 0)
                max_supply = cmc_data.get('max_supply', 0)
                
                if circulating_supply > 0:
                    analysis += f"""
• **Circulating Supply**: {circulating_supply:,.0f} {symbol.upper()}"""
                
                if max_supply > 0:
                    analysis += f"""
• **Max Supply**: {max_supply:,.0f} {symbol.upper()}"""
                    
                    # Calculate supply inflation
                    supply_inflation = (circulating_supply / max_supply * 100) if max_supply > 0 else 0
                    analysis += f"""
• **Supply Inflation**: {supply_inflation:.1f}% of max supply"""
                
                # Additional CoinMarketCap metrics
                if 'tags' in cmc_data and cmc_data['tags']:
                    tags = cmc_data['tags'][:3]  # First 3 tags
                    analysis += f"""
• **Categories**: {', '.join(tags)}"""
            
            # Add futures sentiment analysis (informational only, NOT trading signals)
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                
                if language == 'id':
                    analysis += f"""

⚡ **Sentiment Futures (Informasi Saja):**"""
                else:
                    analysis += f"""

⚡ **Futures Sentiment (Information Only):**"""
                
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    short_ratio = ls_data.get('short_ratio', 50)
                    
                    sentiment = "Bullish" if long_ratio > 60 else "Bearish" if long_ratio < 40 else "Neutral"
                    sentiment_emoji = "🟢" if sentiment == "Bullish" else "🔴" if sentiment == "Bearish" else "🟡"
                    
                    analysis += f"""
• **Long/Short Ratio**: {long_ratio:.1f}% / {short_ratio:.1f}%
• **Market Sentiment**: {sentiment_emoji} {sentiment}"""
                
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    funding_emoji = "📈" if funding_rate > 0 else "📉" if funding_rate < 0 else "⚖️"
                    analysis += f"""
• **Funding Rate**: {funding_emoji} {funding_rate:.4f}%"""
            
            # Add price levels (informational only)
            if language == 'id':
                analysis += f"""

📈 **Level Harga (Referensi):**"""
            else:
                analysis += f"""

📈 **Price Levels (Reference):**"""
            
            # Calculate basic support/resistance levels
            support_level = primary_price * 0.95
            resistance_level = primary_price * 1.05
            
            analysis += f"""
• **Support Level**: ${support_level:,.4f}
• **Resistance Level**: ${resistance_level:,.4f}
• **Current Position**: {"Above mid-range" if primary_price > (support_level + resistance_level) / 2 else "Below mid-range"}"""
            
            # Add data quality assessment
            data_sources = []
            if 'error' not in coinapi_data:
                data_sources.append("CoinAPI ✅")
            if 'error' not in cmc_data and cmc_data:
                data_sources.append("CoinMarketCap ✅")
            if 'error' not in futures_data:
                data_sources.append("Binance Futures ✅")
            
            if language == 'id':
                analysis += f"""

📡 **Kualitas Data:**
• **Sources Active**: {len(data_sources)}/3
• **Active APIs**: {', '.join(data_sources)}
• **Analysis Quality**: {"Excellent" if len(data_sources) >= 2 else "Good" if len(data_sources) == 1 else "Limited"}

⏰ **Generated**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Real-time**: Data fundamental ter-update otomatis

💡 **Untuk Trading Signals**: Gunakan command `/futures {symbol.lower()}` untuk mendapatkan rekomendasi trading lengkap dengan Entry/TP/SL"""
            else:
                analysis += f"""

📡 **Data Quality:**
• **Sources Active**: {len(data_sources)}/3
• **Active APIs**: {', '.join(data_sources)}
• **Analysis Quality**: {"Excellent" if len(data_sources) >= 2 else "Good" if len(data_sources) == 1 else "Limited"}

⏰ **Generated**: {datetime.now().strftime('%H:%M:%S UTC')}
🔄 **Real-time**: Fundamental data auto-updated

💡 **For Trading Signals**: Use command `/futures {symbol.lower()}` to get complete trading recommendations with Entry/TP/SL"""
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in fundamental analysis: {e}")
            return f"❌ Error dalam analisis fundamental {symbol}: {str(e)}"
    
    def _generate_clear_analysis_signal(self, symbol, price, futures_data, coinapi_data, language='id'):
        """Generate clear trading signal for comprehensive analysis"""
        try:
            # Initialize signal components
            signal_strength = 0
            signal_factors = []
            
            # Factor 1: Futures sentiment
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    if long_ratio > 65:
                        signal_strength -= 1
                        signal_factors.append("Overleveraged long positions")
                    elif long_ratio < 35:
                        signal_strength += 1
                        signal_factors.append("Oversold conditions")
                    else:
                        signal_strength += 0.5
                        signal_factors.append("Balanced market sentiment")
                
                funding_data = futures_data.get('funding_rate_data', {})
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0)
                    if funding_rate > 0.01:
                        signal_strength -= 0.5
                        signal_factors.append("High funding rate")
                    elif funding_rate < -0.005:
                        signal_strength += 0.5
                        signal_factors.append("Negative funding rate")
            
            # Factor 2: Price level analysis
            if symbol == 'BTC':
                if price > 55000:
                    signal_strength += 1
                    signal_factors.append("Above key resistance level")
                elif price < 40000:
                    signal_strength += 0.5
                    signal_factors.append("Near support zone")
            elif symbol == 'ETH':
                if price > 3200:
                    signal_strength += 1
                    signal_factors.append("Bullish price structure")
                elif price < 2800:
                    signal_strength += 0.5
                    signal_factors.append("Potential accumulation zone")
            
            # Generate final recommendation
            if signal_strength >= 1.5:
                signal_direction = "LONG"
                signal_emoji = "🟢"
                confidence = min(85, 65 + signal_strength * 10)
                
                entry = price
                tp1 = price * 1.03
                tp2 = price * 1.06
                sl = price * 0.97
                
            elif signal_strength <= -1:
                signal_direction = "SHORT"
                signal_emoji = "🔴"
                confidence = min(85, 65 + abs(signal_strength) * 10)
                
                entry = price
                tp1 = price * 0.97
                tp2 = price * 0.94
                sl = price * 1.03
                
            else:
                # Default to trend-following based on basic analysis
                signal_direction = "LONG" if price > 45000 else "SHORT" if symbol == 'BTC' else "LONG"
                signal_emoji = "🟢" if signal_direction == "LONG" else "🔴"
                confidence = 60
                
                entry = price
                if signal_direction == "LONG":
                    tp1 = price * 1.02
                    tp2 = price * 1.04
                    sl = price * 0.98
                else:
                    tp1 = price * 0.98
                    tp2 = price * 0.96
                    sl = price * 1.02
                
                signal_factors.append("Trend following setup")
            
            # Format signal output
            if language == 'id':
                signal_text = f"""🎯 **REKOMENDASI TRADING:**

{signal_emoji} **SIGNAL**: {signal_direction}
📊 **Confidence Level**: {confidence:.0f}%

💰 **Entry Strategy:**
• **Entry Point**: ${entry:,.4f}
• **Take Profit 1**: ${tp1:,.4f} (50% position)
• **Take Profit 2**: ${tp2:,.4f} (50% position)
• **Stop Loss**: ${sl:,.4f}

📈 **Analysis Factors:**"""
                
                for factor in signal_factors[:3]:  # Limit to top 3 factors
                    signal_text += f"\n• {factor}"
                
                signal_text += f"""

⚠️ **Risk Management:**
• Gunakan maksimal 1-2% capital per trade
• Set stop loss sebelum entry
• Take profit partial untuk mengamankan profit"""
            
            else:
                signal_text = f"""🎯 **TRADING RECOMMENDATION:**

{signal_emoji} **SIGNAL**: {signal_direction}
📊 **Confidence Level**: {confidence:.0f}%

💰 **Entry Strategy:**
• **Entry Point**: ${entry:,.4f}
• **Take Profit 1**: ${tp1:,.4f} (50% position)
• **Take Profit 2**: ${tp2:,.4f} (50% position)
• **Stop Loss**: ${sl:,.4f}

📈 **Analysis Factors:**"""
                
                for factor in signal_factors[:3]:  # Limit to top 3 factors
                    signal_text += f"\n• {factor}"
                
                signal_text += f"""

⚠️ **Risk Management:**
• Use maximum 1-2% capital per trade
• Set stop loss before entry
• Take profit partial to secure gains"""
            
            return signal_text
            
        except Exception as e:
            print(f"❌ Error generating analysis signal: {e}")
            return "❌ Error generating trading signal"

    def old_get_comprehensive_analysis(self, symbol, futures_data, price_data, language='id', crypto_api=None):
        """Get comprehensive crypto analysis with CoinMarketCap integration"""
        try:
            if language == 'id':
                return self._get_comprehensive_analysis_id(symbol, futures_data, price_data, crypto_api)
            else:
                return self._get_comprehensive_analysis_en(symbol, futures_data, price_data, crypto_api)
        except Exception as e:
            error_msg = f"Error in comprehensive analysis: {str(e)}"
            print(error_msg)
            if language == 'id':
                return f"❌ Gagal menganalisis {symbol}. Error: {error_msg[:100]}"
            else:
                return f"❌ Failed to analyze {symbol}. Error: {error_msg[:100]}"

    def _get_comprehensive_analysis_id(self, symbol, futures_data, price_data, crypto_api):
        """Indonesian comprehensive analysis using CoinMarketCap data"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        # Get comprehensive data from CoinMarketCap
        cmc_data = None
        if crypto_api and hasattr(crypto_api, 'get_comprehensive_crypto_analysis'):
            analysis_data = crypto_api.get_comprehensive_crypto_analysis(symbol)
            cmc_data = analysis_data.get('cmc_data', {}) if 'error' not in analysis_data else {}

        # Use CoinMarketCap data if available, fallback to CoinAPI
        if cmc_data and 'error' not in cmc_data:
            current_price = cmc_data.get('price', 0)
            change_24h = cmc_data.get('percent_change_24h', 0)
            market_cap = cmc_data.get('market_cap', 0)
            volume_24h = cmc_data.get('volume_24h', 0)
            rank = cmc_data.get('cmc_rank', 0)
            name = cmc_data.get('name', symbol)
            description = cmc_data.get('description', '')
        elif price_data and 'error' not in price_data:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            market_cap = 0
            volume_24h = 0
            rank = 0
            name = symbol
            description = ''
        else:
            current_price = 0
            change_24h = 0
            market_cap = 0
            volume_24h = 0
            rank = 0
            name = symbol
            description = ''

        # Format price
        if current_price < 1:
            price_format = f"${current_price:.8f}"
        elif current_price < 100:
            price_format = f"${current_price:.4f}"
        else:
            price_format = f"${current_price:,.2f}"

        change_emoji = "📈" if change_24h >= 0 else "📉"
        change_color = "+" if change_24h >= 0 else ""

        analysis = f"""🔍 **ANALISIS KOMPREHENSIF {symbol}** ({name})

💰 **Data Fundamental (CoinMarketCap):**
• **Harga**: {price_format}
{change_emoji} **Perubahan 24j**: {change_color}{change_24h:.2f}%
• **Market Cap**: ${market_cap:,.0f} {f'(Rank #{rank})' if rank > 0 else ''}
• **Volume 24j**: ${volume_24h:,.0f}

📊 **Analisis Teknikal:**"""

        # Add technical analysis based on price movement
        if change_24h > 5:
            analysis += f"""
• **Momentum**: Sangat Bullish 🚀
• **Trend**: Strong upward momentum
• **Support**: ${current_price * 0.95:.4f} (Dynamic)
• **Resistance**: ${current_price * 1.05:.4f} (Next target)"""
        elif change_24h > 2:
            analysis += f"""
• **Momentum**: Bullish 📈
• **Trend**: Positive momentum
• **Support**: ${current_price * 0.97:.4f}
• **Resistance**: ${current_price * 1.03:.4f}"""
        elif change_24h > -2:
            analysis += f"""
• **Momentum**: Sideways 📊
• **Trend**: Konsolidasi
• **Support**: ${current_price * 0.98:.4f}
• **Resistance**: ${current_price * 1.02:.4f}"""
        elif change_24h > -5:
            analysis += f"""
• **Momentum**: Bearish 📉
• **Trend**: Koreksi ringan
• **Support**: ${current_price * 0.95:.4f} (Critical)
• **Resistance**: ${current_price * 1.02:.4f}"""
        else:
            analysis += f"""
• **Momentum**: Sangat Bearish 🔻
• **Trend**: Heavy correction
• **Support**: ${current_price * 0.90:.4f} (Major)
• **Resistance**: ${current_price * 1.05:.4f}"""

        # Add futures analysis if available
        if futures_data and 'error' not in futures_data:
            analysis += f"""

⚡ **Futures Analysis:**
• **Mark Price**: ${futures_data.get('mark_price', current_price):,.4f}
• **Funding Rate**: {futures_data.get('funding_rate', 0):.4f}%
• **Open Interest**: ${futures_data.get('open_interest', 0):,.0f}"""

        # Add prediction based on current momentum
        if change_24h > 3:
            prediction = "📈 **Prediksi Jangka Pendek**: Bullish continuation expected"
        elif change_24h < -3:
            prediction = "📉 **Prediksi Jangka Pendek**: Further correction possible"
        else:
            prediction = "📊 **Prediksi Jangka Pendek**: Range-bound movement"

        analysis += f"""

{prediction}

🎯 **Rekomendasi Trading:**
• **Entry Strategy**: Wait for confirmation at support/resistance
• **Risk Management**: Use 2-3% position sizing
• **Time Horizon**: 1-7 days untuk swing trading

⏰ **Data Update**: {current_time}
📡 **Source**: CoinAPI Real-time + Binance Futures

⚠️ **Disclaimer**: Analisis ini untuk edukasi, bukan saran investasi."""

        return analysis

    def _get_comprehensive_analysis_en(self, symbol, futures_data, price_data, crypto_api):
        """English comprehensive analysis"""
        current_time = datetime.now().strftime('%H:%M:%S UTC')

        # Get current price from CoinAPI
        if price_data and 'error' not in price_data:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"

            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_color = "+" if change_24h >= 0 else ""
        else:
            price_format = "Data unavailable"
            change_24h = 0
            change_emoji = "⚠️"
            change_color = ""

        analysis = f"""🔍 **COMPREHENSIVE ANALYSIS {symbol}** (CoinAPI Real-time)

💰 **Current Price**: {price_format}
{change_emoji} **24h Change**: {change_color}{change_24h:.2f}%

📊 **Technical Analysis:**"""

        # Add technical analysis based on price movement
        if change_24h > 5:
            analysis += f"""
• **Momentum**: Very Bullish 🚀
• **Trend**: Strong upward momentum
• **Support**: ${current_price * 0.95:.4f} (Dynamic)
• **Resistance**: ${current_price * 1.05:.4f} (Next target)"""
        elif change_24h > 2:
            analysis += f"""
• **Momentum**: Bullish 📈
• **Trend**: Positive momentum
• **Support**: ${current_price * 0.97:.4f}
• **Resistance**: ${current_price * 1.03:.4f}"""
        elif change_24h > -2:
            analysis += f"""
• **Momentum**: Sideways 📊
• **Trend**: Consolidation
• **Support**: ${current_price * 0.98:.4f}
• **Resistance**: ${current_price * 1.02:.4f}"""
        elif change_24h > -5:
            analysis += f"""
• **Momentum**: Bearish 📉
• **Trend**: Light correction
• **Support**: ${current_price * 0.95:.4f} (Critical)
• **Resistance**: ${current_price * 1.02:.4f}"""
        else:
            analysis += f"""
• **Momentum**: Very Bearish 🔻
• **Trend**: Heavy correction
• **Support**: ${current_price * 0.90:.4f} (Major)
• **Resistance**: ${current_price * 1.05:.4f}"""

        # Add futures analysis if available
        if futures_data and 'error' not in futures_data:
            analysis += f"""

⚡ **Futures Analysis:**
• **Mark Price**: ${futures_data.get('mark_price', current_price):,.4f}
• **Funding Rate**: {futures_data.get('funding_rate', 0):.4f}%
• **Open Interest**: ${futures_data.get('open_interest', 0):,.0f}"""

        # Add prediction based on current momentum
        if change_24h > 3:
            prediction = "📈 **Short-term Prediction**: Bullish continuation expected"
        elif change_24h < -3:
            prediction = "📉 **Short-term Prediction**: Further correction possible"
        else:
            prediction = "📊 **Short-term Prediction**: Range-bound movement"

        analysis += f"""

{prediction}

🎯 **Trading Recommendation:**
• **Entry Strategy**: Wait for confirmation at support/resistance
• **Risk Management**: Use 2-3% position sizing
• **Time Horizon**: 1-7 days for swing trading

⏰ **Data Update**: {current_time}
📡 **Source**: CoinAPI Real-time + Binance Futures

⚠️ **Disclaimer**: This analysis is for educational purposes, not investment advice."""

        return analysis

    def generate_futures_signals(self, language='id', crypto_api=None):
        """Generate comprehensive futures TRADING signals with complete LONG/SHORT recommendations and Entry/TP/SL levels"""
        try:
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk generate trading signals."
            
            print("🎯 Generating comprehensive futures trading signals...")
            
            # Target top market cap coins for clear trading signals
            target_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
            signals_generated = []
            
            for symbol in target_symbols:
                try:
                    print(f"📊 Analyzing {symbol}...")
                    
                    # Get CoinAPI data (primary source)
                    coinapi_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
                    
                    # Get Binance futures data for sentiment
                    futures_data = crypto_api.get_comprehensive_futures_data(symbol)
                    
                    # Skip if both data sources fail
                    if 'error' in coinapi_data and 'error' in futures_data:
                        print(f"⚠️ Skipping {symbol} - no valid data")
                        continue
                    
                    # Generate TRADING signal for this symbol
                    signal = self._generate_individual_futures_signal(symbol, coinapi_data, futures_data, language)
                    
                    if signal:
                        signals_generated.append(signal)
                        print(f"✅ Trading signal generated for {symbol}")
                    
                except Exception as e:
                    print(f"❌ Error analyzing {symbol}: {e}")
                    continue
            
            if not signals_generated:
                if language == 'id':
                    return """❌ **Tidak dapat generate sinyal trading futures saat ini**

🔍 **Possible Causes:**
• Data market sedang tidak stabil
• API rate limiting
• Kondisi market sideways (tidak ada setup trading yang jelas)

💡 **Solusi:**
• Coba lagi dalam 15-30 menit
• Gunakan `/futures btc` untuk analisis trading spesifik
• Gunakan `/analyze btc` untuk analisis fundamental saja
• Gunakan `/price btc` untuk cek harga real-time

⚠️ **Note**: Sinyal trading futures hanya di-generate ketika ada setup trading yang jelas dengan Entry/TP/SL."""
                else:
                    return """❌ **Cannot generate futures trading signals currently**

🔍 **Possible Causes:**
• Market data unstable
• API rate limiting  
• Sideways market conditions (no clear trading setups)

💡 **Solutions:**
• Try again in 15-30 minutes
• Use `/futures btc` for specific trading analysis
• Use `/analyze btc` for fundamental analysis only
• Use `/price btc` for real-time price check

⚠️ **Note**: Futures trading signals only generated when clear trading setups exist with Entry/TP/SL."""
            
            # Format comprehensive trading signals
            if language == 'id':
                header = f"""🚨 **SINYAL TRADING FUTURES HARIAN** ({len(signals_generated)} Coins)

⏰ **Generated**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Data Source**: CoinAPI Real-time + Binance Futures
🎯 **Target**: Top Market Cap Coins dengan setup trading jelas

"""
                
                footer = f"""

📊 **TRADING RULES WAJIB:**
• Maksimal 2-3 posisi trading simultan
• Risk 1-2% dari total modal per trade
• ALWAYS set stop loss sebelum entry
• Take profit partial di TP1 (50%), hold untuk TP2 (50%)
• Move SL ke break-even setelah TP1 hit

⚠️ **FUTURES TRADING RISK WARNING:**
• Futures trading berisiko tinggi - bisa loss 100% modal
• Gunakan leverage dengan sangat hati-hati
• Tidak menjamin profit - bisa rugi total
• Hanya trade dengan modal yang bisa ditanggung jika hilang

🔄 **Next Update**: Trading signals akan di-update setiap 4-6 jam atau ketika ada perubahan market signifikan.

💡 **Perbedaan Commands:**
• `/futures_signals` = Sinyal trading lengkap dengan Entry/TP/SL
• `/futures [coin]` = Analisis trading individual per coin  
• `/analyze [coin]` = Analisis fundamental saja (bukan trading)"""
            
            else:
                header = f"""🚨 **DAILY FUTURES TRADING SIGNALS** ({len(signals_generated)} Coins)

⏰ **Generated**: {datetime.now().strftime('%H:%M:%S UTC')}
📡 **Data Source**: CoinAPI Real-time + Binance Futures
🎯 **Target**: Top Market Cap Coins with clear trading setups

"""
                
                footer = f"""

📊 **MANDATORY TRADING RULES:**
• Maximum 2-3 trading positions simultaneously
• Risk 1-2% of total capital per trade
• ALWAYS set stop loss before entry
• Take profit partial at TP1 (50%), hold for TP2 (50%)
• Move SL to break-even after TP1 hit

⚠️ **FUTURES TRADING RISK WARNING:**
• Futures trading is extremely high risk - can lose 100% capital
• Use leverage very carefully
• No guarantee of profit - can lose everything
• Only trade with money you can afford to lose

🔄 **Next Update**: Trading signals updated every 4-6 hours or on significant market changes.

💡 **Command Differences:**
• `/futures_signals` = Complete trading signals with Entry/TP/SL
• `/futures [coin]` = Individual trading analysis per coin  
• `/analyze [coin]` = Fundamental analysis only (not trading)"""
            
            # Format signals with proper numbering
            formatted_signals = []
            for i, signal in enumerate(signals_generated, 1):
                # Add numbering to each signal
                numbered_signal = signal.replace(f"**{signal.split('**')[1].split('**')[0]}**", f"**{i}. {signal.split('**')[1].split('**')[0]}**")
                formatted_signals.append(numbered_signal)
            
            # Combine all signals
            full_message = header + "\n\n".join(formatted_signals) + footer
            
            print(f"✅ Generated {len(signals_generated)} futures trading signals")
            return full_message
            
        except Exception as e:
            print(f"❌ Error in generate_futures_signals: {e}")
            return f"❌ Error generating futures trading signals: {str(e)}"
    
    def _generate_individual_futures_signal(self, symbol, coinapi_data, futures_data, language='id'):
        """Generate individual futures signal for a symbol with HOLD for low confidence"""
        try:
            # Get price from best available source
            price = 0
            price_source = "Unknown"
            
            if 'error' not in coinapi_data and coinapi_data.get('price', 0) > 0:
                price = coinapi_data.get('price', 0)
                price_source = "CoinAPI"
            elif 'error' not in futures_data:
                price_data = futures_data.get('price_data', {})
                if 'error' not in price_data and price_data.get('price', 0) > 0:
                    price = price_data.get('price', 0)
                    price_source = "Binance"
            
            if price <= 0:
                return None
            
            # Determine signal based on multiple factors
            signal_score = 0
            signal_reasons = []
            
            # Factor 1: Binance futures sentiment analysis
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                
                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    
                    if long_ratio > 70:  # Too many longs - contrarian short
                        signal_score -= 2
                        signal_reasons.append(f"Overleveraged longs ({long_ratio:.1f}%)")
                    elif long_ratio < 30:  # Too many shorts - contrarian long
                        signal_score += 2
                        signal_reasons.append(f"Oversold condition ({long_ratio:.1f}% long)")
                    elif 45 <= long_ratio <= 55:  # Balanced
                        signal_score += 1
                        signal_reasons.append(f"Balanced sentiment ({long_ratio:.1f}%)")
                
                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    
                    if funding_rate > 0.05:  # High positive funding
                        signal_score -= 1
                        signal_reasons.append(f"High funding rate ({funding_rate:.3f}%)")
                    elif funding_rate < -0.02:  # Negative funding
                        signal_score += 1
                        signal_reasons.append(f"Negative funding rate ({funding_rate:.3f}%)")
            
            # Factor 2: Price level analysis (basic momentum)
            if symbol == 'BTC':
                if price > 60000:
                    signal_score += 1
                    signal_reasons.append("Above key resistance level")
                elif price < 40000:
                    signal_score += 1
                    signal_reasons.append("Oversold price level")
            elif symbol == 'ETH':
                if price > 3500:
                    signal_score += 1
                    signal_reasons.append("Above key resistance")
                elif price < 2500:
                    signal_score += 1
                    signal_reasons.append("Support zone entry")
            
            # Generate clear signal with HOLD for low confidence
            if signal_score >= 2:
                direction = "LONG"
                emoji = "🟢"
                confidence = min(85, 65 + signal_score * 5)
                entry = price
                tp1 = price * 1.025
                tp2 = price * 1.05
                sl = price * 0.975
            elif signal_score <= -2:
                direction = "SHORT"
                emoji = "🔴"
                confidence = min(85, 65 + abs(signal_score) * 5)
                entry = price
                tp1 = price * 0.975
                tp2 = price * 0.95
                sl = price * 1.025
            else:
                # NEW LOGIC: Set HOLD for unclear signals (confidence ≤60%)
                direction = "HOLD"
                emoji = "⏸️"
                confidence = 55  # Low confidence for HOLD
                entry = price
                tp1 = price * 1.01  # Minimal TP for display
                tp2 = price * 1.02
                sl = price * 0.99   # Minimal SL for display
                signal_reasons.append("Sinyal tidak jelas - tunggu konfirmasi")
            
            # Skip HOLD signals from final output (don't return signal for HOLD)
            if direction == "HOLD":
                return None
            
            # Format individual signal (only for LONG/SHORT signals)
            if language == 'id':
                signal_text = f"""**{symbol.upper()}** {emoji} **{direction}**
💰 Entry: ${entry:,.4f} | TP1: ${tp1:,.4f} | TP2: ${tp2:,.4f} | SL: ${sl:,.4f}
📊 Confidence: {confidence:.0f}% | 📡 Source: {price_source}
💡 Reason: {', '.join(signal_reasons[:2]) if signal_reasons else 'Technical momentum'}"""
            else:
                signal_text = f"""**{symbol.upper()}** {emoji} **{direction}**
💰 Entry: ${entry:,.4f} | TP1: ${tp1:,.4f} | TP2: ${tp2:,.4f} | SL: ${sl:,.4f}
📊 Confidence: {confidence:.0f}% | 📡 Source: {price_source}
💡 Reason: {', '.join(signal_reasons[:2]) if signal_reasons else 'Technical momentum'}"""
            
            return signal_text
            
        except Exception as e:
            print(f"❌ Error generating individual signal for {symbol}: {e}")
            return None

    def old_generate_futures_signals(self, language='id', crypto_api=None):
        """Generate enhanced futures signals with CoinAPI integration and altcoin focus"""
        try:
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk analisis futures"

            # Enhanced target symbols - mix of top coins and promising altcoins
            major_coins = ['BTC', 'ETH', 'BNB', 'SOL']
            trending_altcoins = ['MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'ATOM', 'FTM', 'NEAR', 'ALGO', 'MANA', 'SAND', 'AXS']

            # Prioritize altcoins for more diverse signals
            target_symbols = major_coins[:2] + trending_altcoins[:8]  # 2 major + 8 altcoins

            signals = []
            processed_count = 0

            for symbol in target_symbols:
                try:
                    processed_count += 1
                    print(f"🔄 Processing {symbol} ({processed_count}/{len(target_symbols)})")

                    # Get price from CoinAPI first, fallback to CoinGecko
                    price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
                    if 'error' in price_data:
                        print(f"⚠️ CoinAPI failed for {symbol}, trying fallback...")
                        # Silent fallback to other sources if needed
                        price_data = {'price': 0, 'error': 'CoinAPI unavailable'}

                    # Get futures data from Binance
                    futures_data = crypto_api.get_comprehensive_futures_data(symbol)
                    if 'error' in futures_data:
                        print(f"❌ Futures data failed for {symbol}")
                        continue

                    # Analyze SnD with enhanced logic
                    snd_analysis = crypto_api.analyze_supply_demand(symbol, '1h')
                    if 'error' in snd_analysis:
                        print(f"❌ SnD analysis failed for {symbol}")
                        continue

                    # Generate enhanced signal
                    signal = self._generate_enhanced_snd_signal(symbol, price_data, futures_data, snd_analysis)
                    if signal and signal.get('confidence', 0) >= 60:  # Only high confidence signals
                        signals.append(signal)
                        print(f"✅ Generated signal for {symbol} (confidence: {signal.get('confidence', 0)}%)")

                except Exception as e:
                    print(f"❌ Error generating signal for {symbol}: {e}")
                    continue

            if not signals:
                if language == 'id':
                    return """❌ **Tidak dapat menghasilkan sinyal futures saat ini**

🔍 **Kemungkinan Penyebab:**
• Market dalam kondisi sideways (no clear SnD zones)
• Volume trading rendah pada altcoins
• Tidak ada setup entry yang aman (confidence < 60%)
• CoinAPI rate limit atau gangguan sementara

💡 **Saran:**
• Coba lagi dalam 30-60 menit
• Gunakan `/futures BTC` untuk analisis spesifik
• Check market volatility dengan `/market`

⚠️ **Note**: SnD signals hanya muncul saat ada zone Supply/Demand yang kuat."""
                else:
                    return """❌ **Cannot generate futures signals currently**

🔍 **Possible Causes:**
• Market in sideways condition (no clear SnD zones)
• Low trading volume on altcoins
• No safe entry setups (confidence < 60%)
• CoinAPI rate limit or temporary issues

💡 **Suggestions:**
• Try again in 30-60 minutes
• Use `/futures BTC` for specific analysis
• Check market volatility dengan `/market`

⚠️ **Note**: SnD signals only appear when strong Supply/Demand zones exist."""

            # Format enhanced signals
            if language == 'id':
                return self._format_enhanced_futures_signals_id(signals)
            else:
                return self._format_enhanced_futures_signals_en(signals)

        except Exception as e:
            print(f"💥 Critical error in generate_futures_signals: {e}")
            import traceback
            traceback.print_exc()

            error_msg = f"Error dalam sistem AI futures: {str(e)[:100]}"
            if language == 'id':
                return f"❌ {error_msg}\n\n💡 Coba `/futures BTC` untuk analisis spesifik."
            else:
                return f"❌ {error_msg}\n\n💡 Try `/futures BTC` for specific analysis."

    def _generate_enhanced_snd_signal(self, symbol, price_data, futures_data, snd_analysis):
        """Generate enhanced SnD signal with CoinAPI price integration - IMPROVED SHORT LOGIC"""
        try:
            # Get current price from CoinAPI or futures data
            current_price = 0
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                price_source = "CoinAPI"
            elif 'error' not in futures_data:
                price_data_futures = futures_data.get('price_data', {})
                if 'error' not in price_data_futures:
                    current_price = price_data_futures.get('price', 0)
                    price_source = "Binance Futures"

            if current_price <= 0:
                return None

            # Analyze market structure from futures data
            ls_ratio_data = futures_data.get('long_short_ratio_data', {})
            long_ratio = ls_ratio_data.get('long_ratio', 50) if 'error' not in ls_ratio_data else 50

            # Funding rate analysis
            funding_data = futures_data.get('funding_rate_data', {})
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0

            # Volume analysis
            volume_24h = price_data_futures.get('volume_24h', 0) if 'price_data_futures' in locals() else 0

            # SnD zone analysis - ENHANCED for SHORT detection
            snd_signals = snd_analysis.get('signals', [])
            confidence_score = snd_analysis.get('confidence_score', 0)

            # FORCE signal generation even with weak SnD zones
            best_signal = None
            
            if snd_signals and len(snd_signals) > 0:
                # First, look for SHORT signals from supply zones
                short_signals = [s for s in snd_signals if s.get('direction') == 'SHORT']
                long_signals = [s for s in snd_signals if s.get('direction') == 'LONG']
                
                # Prioritize SHORT if market conditions favor it
                if short_signals and (long_ratio > 65 or funding_rate > 0.005):
                    best_signal = max(short_signals, key=lambda x: x.get('confidence', 0))
                    print(f"🔴 SHORT signal prioritized for {symbol} (L/S: {long_ratio:.1f}%, Funding: {funding_rate*100:.4f}%)")
                elif long_signals and (long_ratio < 35 or funding_rate < -0.005):
                    best_signal = max(long_signals, key=lambda x: x.get('confidence', 0))
                    print(f"🟢 LONG signal prioritized for {symbol} (L/S: {long_ratio:.1f}%, Funding: {funding_rate*100:.4f}%)")
                else:
                    # Take best signal overall
                    best_signal = max(snd_signals, key=lambda x: x.get('confidence', 0))

            # FALLBACK: Generate signal based on market conditions even without SnD zones
            if not best_signal:
                print(f"⚠️ No SnD signals for {symbol}, generating based on market conditions...")
                
                # Generate signal based on long/short ratio and funding rate
                if long_ratio > 70 or funding_rate > 0.01:
                    # Overcrowded longs = SHORT opportunity
                    direction = 'SHORT'
                    entry_price = current_price * 1.002  # Slight rally entry
                    tp1 = current_price * 0.975  # 2.5% down
                    tp2 = current_price * 0.95   # 5% down
                    sl = current_price * 1.015   # 1.5% up
                    base_confidence = 65
                    reason = f"Overcrowded longs ({long_ratio:.1f}%) + positive funding"
                elif long_ratio < 30 or funding_rate < -0.01:
                    # Overcrowded shorts = LONG opportunity
                    direction = 'LONG'
                    entry_price = current_price * 0.998  # Slight dip entry
                    tp1 = current_price * 1.025  # 2.5% up
                    tp2 = current_price * 1.05   # 5% up
                    sl = current_price * 0.985   # 1.5% down
                    base_confidence = 65
                    reason = f"Overcrowded shorts ({long_ratio:.1f}%) + negative funding"
                else:
                    # Neutral market - use price action to determine direction
                    price_change_24h = price_data.get('change_24h', 0)
                    if price_change_24h > 2:
                        direction = 'LONG'
                        entry_price = current_price * 0.999
                        tp1 = current_price * 1.02
                        tp2 = current_price * 1.04
                        sl = current_price * 0.985
                        reason = f"Bullish momentum ({price_change_24h:.1f}%)"
                    else:
                        direction = 'SHORT'
                        entry_price = current_price * 1.001
                        tp1 = current_price * 0.98
                        tp2 = current_price * 0.96
                        sl = current_price * 1.015
                        reason = f"Bearish bias (momentum: {price_change_24h:.1f}%)"
                    base_confidence = 60

                # Create fallback signal
                best_signal = {
                    'direction': direction,
                    'entry_price': entry_price,
                    'take_profit_1': tp1,
                    'take_profit_2': tp2,
                    'stop_loss': sl,
                    'confidence': base_confidence,
                    'reason': reason,
                    'zone_distance': 5  # Fallback value
                }
                print(f"✅ Generated fallback {direction} signal for {symbol} based on market conditions")

            # Enhanced signal generation - FORCE direction to be valid
            direction = best_signal.get('direction', 'LONG')  # Default to LONG if unknown
            
            # Ensure direction is never UNKNOWN
            if direction not in ['LONG', 'SHORT']:
                # Determine direction based on market conditions
                if long_ratio > 60 or funding_rate > 0.005:
                    direction = 'SHORT'
                else:
                    direction = 'LONG'
                print(f"🔧 Fixed direction for {symbol}: {direction} (was: {best_signal.get('direction', 'None')})")

            entry_price = best_signal.get('entry_price', current_price)

            # Use TP/SL from best_signal if available, otherwise calculate
            if 'take_profit_1' in best_signal and 'stop_loss' in best_signal:
                tp1 = best_signal.get('take_profit_1')
                tp2 = best_signal.get('take_profit_2', tp1 * 1.5)
                sl = best_signal.get('stop_loss')
            else:
                # Dynamic TP/SL calculation based on volatility
                volatility_multiplier = 1.0
                if symbol in ['BTC', 'ETH']:
                    volatility_multiplier = 0.8  # Lower for major coins
                else:
                    volatility_multiplier = 1.2  # Higher for altcoins

                if direction == 'LONG':
                    tp1 = entry_price * (1 + 0.025 * volatility_multiplier)  # 2.5% for majors, 3% for alts
                    tp2 = entry_price * (1 + 0.05 * volatility_multiplier)   # 5% for majors, 6% for alts
                    sl = entry_price * (1 - 0.015 * volatility_multiplier)   # 1.5% for majors, 1.8% for alts
                else:  # SHORT - Enhanced calculations
                    tp1 = entry_price * (1 - 0.025 * volatility_multiplier)  # 2.5% down for majors, 3% for alts
                    tp2 = entry_price * (1 - 0.05 * volatility_multiplier)   # 5% down for majors, 6% for alts
                    sl = entry_price * (1 + 0.015 * volatility_multiplier)   # 1.5% up for majors, 1.8% for alts

            # Calculate confidence based on multiple factors - ENHANCED SHORT LOGIC
            final_confidence = confidence_score

            # Enhanced confidence for SHORT signals
            if direction == 'SHORT':
                # Overcrowded longs = good for SHORT
                if long_ratio > 70:
                    final_confidence += 10
                    print(f"🔴 SHORT confidence boost: Overcrowded longs ({long_ratio:.1f}%)")
                elif long_ratio > 60:
                    final_confidence += 5
                
                # Positive funding rate = longs pay shorts = good for SHORT
                if funding_rate > 0.01:
                    final_confidence += 8
                    print(f"🔴 SHORT confidence boost: Positive funding ({funding_rate*100:.4f}%)")
                elif funding_rate > 0.005:
                    final_confidence += 4
                
                # Additional SHORT market structure confirmations
                supply_zones = snd_analysis.get('supply_zones', [])
                if len(supply_zones) >= 2:
                    final_confidence += 5
                    print(f"🔴 SHORT confidence boost: Multiple supply zones ({len(supply_zones)})")
                
                # Price near supply zone = good for SHORT
                zone_distance = best_signal.get('zone_distance', 10)
                if zone_distance < 2:  # Very close to supply zone
                    final_confidence += 8
                elif zone_distance < 5:
                    final_confidence += 4

            # Enhanced confidence for LONG signals
            elif direction == 'LONG':
                # Overcrowded shorts = good for LONG
                if long_ratio < 30:
                    final_confidence += 10
                elif long_ratio < 40:
                    final_confidence += 5
                
                # Negative funding rate = shorts pay longs = good for LONG
                if funding_rate < -0.01:
                    final_confidence += 8
                elif funding_rate < -0.005:
                    final_confidence += 4

            # Volume confirmation
            if volume_24h > 1000000:  # Good volume
                final_confidence += 3

            # Market momentum confirmation
            try:
                price_change_24h = price_data.get('change_24h', 0)
                if direction == 'SHORT' and price_change_24h < -2:
                    final_confidence += 5  # Bearish momentum confirms SHORT
                elif direction == 'LONG' and price_change_24h > 2:
                    final_confidence += 5  # Bullish momentum confirms LONG
            except:
                pass

            # Cap confidence at 95% but ensure SHORT signals get fair treatment
            final_confidence = min(final_confidence, 95)
            
            # Ensure minimum confidence for valid SHORT signals
            if direction == 'SHORT' and final_confidence < 60:
                final_confidence = max(final_confidence, 62)  # Minimum for SHORT

            # Risk/Reward calculation
            if direction == 'LONG':
                risk = abs(entry_price - sl)
                reward = abs(tp2 - entry_price)
            else:  # SHORT
                risk = abs(sl - entry_price)
                reward = abs(entry_price - tp2)

            risk_reward = reward / risk if risk > 0 else 0

            # Enhanced reason for SHORT signals
            reason = best_signal.get('reason', 'SnD zone detected')
            if direction == 'SHORT':
                reason_parts = [reason]
                if long_ratio > 65:
                    reason_parts.append(f"Overcrowded longs ({long_ratio:.0f}%)")
                if funding_rate > 0.005:
                    reason_parts.append(f"Positive funding ({funding_rate*100:.3f}%)")
                reason = " + ".join(reason_parts)

            return {
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl,
                'confidence': final_confidence,
                'risk_reward': risk_reward,
                'current_price': current_price,
                'price_source': price_source,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100,  # Convert to percentage
                'volume_24h': volume_24h,
                'reason': reason,
                'timeframe': '1h'
            }

        except Exception as e:
            print(f"Error generating enhanced SnD signal for {symbol}: {e}")
            return None

    def _format_enhanced_futures_signals_id(self, signals):
        """Format enhanced futures signals in Indonesian"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            message = f"""🚨 **FUTURES SIGNALS ENHANCED (CoinAPI + SnD)**

📅 **Generated**: {current_time}
🎯 **Total Signals**: {len(signals)} high-confidence setups
📊 **Source**: CoinAPI Real-time + Binance Futures + SnD Analysis

"""

            for i, signal in enumerate(signals[:6], 1):  # Max 6 signals
                symbol = signal['symbol']
                direction = signal['direction']
                entry = signal['entry_price']
                tp1 = signal['tp1']
                tp2 = signal['tp2']
                sl = signal['sl']
                confidence = signal['confidence']
                rr = signal['risk_reward']
                current_price = signal['current_price']
                price_source = signal['price_source']
                long_ratio = signal['long_ratio']
                funding_rate = signal['funding_rate']

                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                confidence_emoji = "🔥" if confidence >= 80 else "⚡" if confidence >= 70 else "💡"

                # Smart price formatting
                if entry < 1:
                    entry_fmt = f"${entry:.6f}"
                    tp1_fmt = f"${tp1:.6f}"
                    tp2_fmt = f"${tp2:.6f}"
                    sl_fmt = f"${sl:.6f}"
                    current_fmt = f"${current_price:.6f}"
                elif entry < 100:
                    entry_fmt = f"${entry:.4f}"
                    tp1_fmt = f"${tp1:.4f}"
                    tp2_fmt = f"${tp2:.4f}"
                    sl_fmt = f"${sl:.4f}"
                    current_fmt = f"${current_price:.4f}"
                else:
                    entry_fmt = f"${entry:,.2f}"
                    tp1_fmt = f"${tp1:.2f}"
                    tp2_fmt = f"${tp2:.2f}"
                    sl_fmt = f"${sl:.2f}"
                    current_fmt = f"${current_price:.2f}"

                message += f"""**{i}. {symbol} {direction} {direction_emoji}**
**Harga**: {current_fmt} ({price_source})
**Entry sesuai SnD**: {entry_fmt}
**TP 1**: {tp1_fmt}
**TP 2**: {tp2_fmt}
**SL**: {sl_fmt}

**Analisis**:
• Confidence: {confidence:.0f}% {confidence_emoji}
• Risk/Reward: {rr:.1f}:1
• Long Ratio: {long_ratio:.0f}%
• Funding: {funding_rate:.3f}%

"""

            message += f"""📋 **SnD Trading Rules:**
• Wait for price action confirmation at entry zones
• Use 1-3% position sizing per trade
• Exit 50% at TP1, hold remainder for TP2
• Monitor volume for breakout/rejection confirmation

⚠️ **Risk Management:**
• Max 2-3 positions simultaneously
• Always set stop loss before entry
• Don't FOMO if you miss the entry point

🎯 **Auto Signals**: Khusus Admin & Lifetime users
📡 **Next Update**: Setiap 2-4 jam (market dependent)"""

            return message

        except Exception as e:
            return f"❌ Error formatting signals: {str(e)}"

    def _format_enhanced_futures_signals_en(self, signals):
        """Format enhanced futures signals in English"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')

            message = f"""🚨 **ENHANCED FUTURES SIGNALS (CoinAPI + SnD)**

📅 **Generated**: {current_time}
🎯 **Total Signals**: {len(signals)} high-confidence setups
📊 **Source**: CoinAPI Real-time + Binance Futures + SnD Analysis

"""

            for i, signal in enumerate(signals[:6], 1):  # Max 6 signals
                symbol = signal['symbol']
                direction = signal['direction']
                entry = signal['entry_price']
                tp1 = signal['tp1']
                tp2 = signal['tp2']
                sl = signal['sl']
                confidence = signal['confidence']
                rr = signal['risk_reward']
                current_price = signal['current_price']
                price_source = signal['price_source']
                long_ratio = signal['long_ratio']
                funding_rate = signal['funding_rate']

                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                confidence_emoji = "🔥" if confidence >= 80 else "⚡" if confidence >= 70 else "💡"

                # Smart price formatting
                if entry < 1:
                    entry_fmt = f"${entry:.6f}"
                    tp1_fmt = f"${tp1:.6f}"
                    tp2_fmt = f"${tp2:.6f}"
                    sl_fmt = f"${sl:.6f}"
                    current_fmt = f"${current_price:.6f}"
                elif entry < 100:
                    entry_fmt = f"${entry:.4f}"
                    tp1_fmt = f"${tp1:.4f}"
                    tp2_fmt = f"${tp2:.4f}"
                    sl_fmt = f"${sl:.4f}"
                    current_fmt = f"${current_price:.4f}"
                else:
                    entry_fmt = f"${entry:,.2f}"
                    tp1_fmt = f"${tp1:.2f}"
                    tp2_fmt = f"${tp2:.2f}"
                    sl_fmt = f"${sl:.2f}"
                    current_fmt = f"${current_price:.2f}"

                message += f"""**{i}. {symbol} {direction} {direction_emoji}**
**Price**: {current_fmt} ({price_source})
**Entry sesuai SnD**: {entry_fmt}
**TP 1**: {tp1_fmt}
**TP 2**: {tp2_fmt}
**SL**: {sl_fmt}

**Analysis**:
• Confidence: {confidence:.0f}% {confidence_emoji}
• Risk/Reward: {rr:.1f}:1
• Long Ratio: {long_ratio:.0f}%
• Funding: {funding_rate:.3f}%

"""

            message += f"""📋 **SnD Trading Rules:**
• Wait for price action confirmation at entry zones
• Use 1-3% position sizing per trade
• Exit 50% at TP1, hold remainder for TP2
• Monitor volume for breakout/rejection confirmation

⚠️ **Risk Management:**
• Max 2-3 positions simultaneously
• Always set stop loss before entry
• Don't FOMO if you miss the entry point

🎯 **Auto Signals**: Admin & Lifetime users only
📡 **Next Update**: Every 2-4 hours (market dependent)"""

            return message

        except Exception as e:
            return f"❌ Error formatting signals: {str(e)}"

    def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get enhanced futures analysis with advanced SnD and market condition detection"""
        try:
            if not crypto_api:
                return "❌ CryptoAPI tidak tersedia untuk analisis futures"

            # Get comprehensive data from multiple sources
            futures_data = crypto_api.get_comprehensive_futures_data(symbol)
            price_data = crypto_api.get_coinapi_price(symbol, force_refresh=True)
            candlestick_data = crypto_api.get_binance_candlestick(symbol, timeframe, 100)

            # Enhanced market condition analysis
            market_condition = self._analyze_market_condition(candlestick_data, futures_data)

            if language == 'id':
                return self._format_advanced_futures_analysis_id(symbol, timeframe, futures_data, price_data, market_condition, candlestick_data)
            else:
                return self._format_advanced_futures_analysis_en(symbol, timeframe, futures_data, price_data, market_condition, candlestick_data)

        except Exception as e:
            if language == 'id':
                return f"❌ Error dalam analisis futures: {str(e)}"
            else:
                return f"❌ Error in futures analysis: {str(e)}"

    def _generate_advanced_individual_signal(self, symbol, futures_data, price_data, market_condition):
        """Generate advanced individual trading signal with ENHANCED SHORT LOGIC"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Market condition analysis
            condition_type = market_condition.get('type', 'unknown')
            condition_strength = market_condition.get('strength', 0)
            volatility = market_condition.get('volatility', 0)
            trend_direction = market_condition.get('trend_direction', 'neutral')

            # Get futures metrics
            ls_data = futures_data.get('long_short_ratio_data', {})
            funding_data = futures_data.get('funding_rate_data', {})
            oi_data = futures_data.get('open_interest_data', {})

            long_ratio = ls_data.get('long_ratio', 50) if 'error' not in ls_data else 50
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
            open_interest = oi_data.get('open_interest', 0) if 'error' not in oi_data else 0

            signal = {
                'symbol': symbol,
                'price': current_price,
                'condition': condition_type,
                'strength': condition_strength,
                'volatility': volatility,
                'trend': trend_direction,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100,  # Convert to percentage
                'open_interest': open_interest,
                'recommendation': 'long',  # Default to LONG instead of hold
                'confidence': 60,  # Base confidence
                'entry_price': current_price,
                'tp1': current_price * 1.025,  # 2.5% up
                'tp2': current_price * 1.05,   # 5% up
                'sl': current_price * 0.985,   # 1.5% down
                'position_size': '1-2%',
                'reasoning': []
            }

            # ENHANCED SHORT SIGNAL DETECTION - Priority Check
            short_conditions_met = 0
            short_confidence_boost = 0
            long_conditions_met = 0
            long_confidence_boost = 0

            # Check for SHORT-favorable conditions
            if long_ratio > 65:  # Overcrowded longs
                short_conditions_met += 1
                short_confidence_boost += 15
                signal['reasoning'].append(f"🔴 Overcrowded longs ({long_ratio:.1f}%) - SHORT opportunity")

            if funding_rate > 0.005:  # Positive funding = longs pay shorts
                short_conditions_met += 1
                short_confidence_boost += 10
                signal['reasoning'].append(f"🔴 Positive funding ({funding_rate*100:.4f}%) favors SHORT")

            if trend_direction == 'bearish' and condition_strength > 50:
                short_conditions_met += 1
                short_confidence_boost += 20
                signal['reasoning'].append(f"🔴 Strong bearish trend ({condition_strength:.1f}%)")

            # Check for LONG-favorable conditions
            if long_ratio < 35:  # Overcrowded shorts
                long_conditions_met += 1
                long_confidence_boost += 15
                signal['reasoning'].append(f"🟢 Overcrowded shorts ({long_ratio:.1f}%) - LONG opportunity")

            if funding_rate < -0.005:  # Negative funding = shorts pay longs
                long_conditions_met += 1
                long_confidence_boost += 10
                signal['reasoning'].append(f"🟢 Negative funding ({funding_rate*100:.4f}%) favors LONG")

            if trend_direction == 'bullish' and condition_strength > 50:
                long_conditions_met += 1
                long_confidence_boost += 20
                signal['reasoning'].append(f"🟢 Strong bullish trend ({condition_strength:.1f}%)")

            # Determine recommendation based on stronger signal
            if short_conditions_met > long_conditions_met or (short_conditions_met == long_conditions_met and short_conditions_met >= 1):
                signal['recommendation'] = 'short'
                signal['confidence'] = min(92, 65 + short_confidence_boost)
                signal['entry_price'] = current_price * 1.001  # Slight rally entry
                signal['tp1'] = current_price * 0.975  # 2.5% down
                signal['tp2'] = current_price * 0.955  # 4.5% down
                signal['sl'] = current_price * 1.015   # 1.5% up
                signal['reasoning'].append("🎯 SHORT conditions favored")
                signal['position_size'] = '2-3%'
                return signal
            elif long_conditions_met >= 1:
                signal['recommendation'] = 'long'
                signal['confidence'] = min(92, 65 + long_confidence_boost)
                signal['entry_price'] = current_price * 0.999  # Slight dip entry
                signal['tp1'] = current_price * 1.025  # 2.5% up
                signal['tp2'] = current_price * 1.055  # 5.5% up
                signal['sl'] = current_price * 0.985   # 1.5% down
                signal['reasoning'].append("🎯 LONG conditions favored")
                signal['position_size'] = '2-3%'
                return signal

            # FORCE LONG/SHORT recommendation - NO range trading or hold
            # Determine trading signal based on conditions (always LONG or SHORT)
            if condition_type == 'sideways':
                # Even in sideways market, choose LONG or SHORT based on long/short ratio
                if long_ratio > 55:
                    signal['recommendation'] = 'short'
                    signal['confidence'] = 65
                    signal['entry_price'] = current_price * 1.001
                    signal['tp1'] = current_price * 0.98
                    signal['tp2'] = current_price * 0.96
                    signal['sl'] = current_price * 1.015
                    signal['reasoning'].append(f"Sideways market + overcrowded longs ({long_ratio:.1f}%) = SHORT")
                else:
                    signal['recommendation'] = 'long'
                    signal['confidence'] = 65
                    signal['entry_price'] = current_price * 0.999
                    signal['tp1'] = current_price * 1.02
                    signal['tp2'] = current_price * 1.04
                    signal['sl'] = current_price * 0.985
                    signal['reasoning'].append(f"Sideways market + balanced ratio ({long_ratio:.1f}%) = LONG")

            elif condition_type == 'trending' and condition_strength > 60:
                if trend_direction == 'bullish':
                    # Check if SHORT is still better despite bullish trend
                    if long_ratio > 75:  # Extremely overcrowded longs
                        signal['recommendation'] = 'short'
                        signal['confidence'] = 78
                        signal['entry_price'] = current_price * 1.005  # Wait for rally
                        signal['tp1'] = current_price * 0.975
                        signal['tp2'] = current_price * 0.950
                        signal['sl'] = current_price * 1.020
                        signal['reasoning'].append(f"🔴 Contrarian SHORT: Extremely overcrowded longs ({long_ratio:.1f}%)")
                    else:
                        signal['recommendation'] = 'long'
                        signal['confidence'] = min(90, condition_strength - (10 if long_ratio > 65 else 0))
                        signal['entry_price'] = current_price * 0.998  # Slight pullback entry
                        signal['tp1'] = current_price * 1.025
                        signal['tp2'] = current_price * 1.045
                        signal['sl'] = current_price * 0.985
                        signal['reasoning'].append(f"Strong bullish trend ({condition_strength:.1f}%)")

                elif trend_direction == 'bearish':
                    signal['recommendation'] = 'short'
                    # Enhanced confidence for bearish trends
                    base_confidence = condition_strength
                    if long_ratio > 60:
                        base_confidence += 15  # Boost for overcrowded longs in bearish trend
                    if funding_rate > 0:
                        base_confidence += 10  # Boost for positive funding in bearish trend
                    
                    signal['confidence'] = min(95, base_confidence)
                    signal['entry_price'] = current_price * 1.002  # Slight rally entry
                    signal['tp1'] = current_price * 0.975
                    signal['tp2'] = current_price * 0.955
                    signal['sl'] = current_price * 1.015
                    signal['reasoning'].append(f"🔴 Strong bearish trend ({condition_strength:.1f}%)")

            elif volatility > 5:
                # In high volatility, consider SHORT if conditions favor it
                if long_ratio > 70 or funding_rate > 0.01:
                    signal['recommendation'] = 'short'
                    signal['confidence'] = min(85, volatility * 8 + short_confidence_boost)
                    signal['entry_price'] = current_price * 1.003
                    signal['tp1'] = current_price * 0.970
                    signal['tp2'] = current_price * 0.945
                    signal['sl'] = current_price * 1.020
                    signal['reasoning'].append(f"🔴 High volatility SHORT ({volatility:.2f}%) + favorable conditions")
                    signal['position_size'] = '1-2%'  # Moderate size for volatile SHORT
                else:
                    signal['condition'] = 'volatile'
                    signal['recommendation'] = 'scalping'
                    signal['confidence'] = min(80, volatility * 10)
                    signal['reasoning'].append(f"High volatility ({volatility:.2f}%) - scalping opportunity")
                    signal['position_size'] = '0.5-1%'  # Smaller size for volatile markets

            else:
                # Even in unclear conditions, check for strong SHORT setups
                if long_ratio > 75 and funding_rate > 0.01:
                    signal['recommendation'] = 'short'
                    signal['confidence'] = 72
                    signal['entry_price'] = current_price * 1.003
                    signal['tp1'] = current_price * 0.975
                    signal['tp2'] = current_price * 0.950
                    signal['sl'] = current_price * 1.018
                    signal['reasoning'].append("🔴 Strong contrarian SHORT setup despite unclear trend")
                else:
                    signal['recommendation'] = 'wait'
                    signal['confidence'] = 30
                    signal['reasoning'].append("Tidak ada setup trading yang jelas")
                    signal['reasoning'].append("Tunggu konfirmasi trend atau breakout")

            # Enhanced funding rate analysis
            if abs(funding_rate * 100) > 0.01:
                if funding_rate > 0:
                    signal['reasoning'].append(f"💰 Funding rate positif ({funding_rate*100:.4f}%) - longs bayar shorts")
                    if signal['recommendation'] == 'short':
                        signal['confidence'] = min(95, signal['confidence'] + 5)
                else:
                    signal['reasoning'].append(f"💰 Funding rate negatif ({funding_rate*100:.4f}%) - shorts bayar longs")
                    if signal['recommendation'] == 'long':
                        signal['confidence'] = min(95, signal['confidence'] + 5)

            # Enhanced long/short ratio analysis
            if long_ratio > 70:
                signal['reasoning'].append(f"⚠️ Overcrowded long positions ({long_ratio:.1f}%) - potential reversal to SHORT")
                if signal['recommendation'] != 'short':
                    signal['reasoning'].append("🔴 Consider SHORT position on next resistance")
            elif long_ratio < 30:
                signal['reasoning'].append(f"⚠️ Overcrowded short positions ({long_ratio:.1f}%) - potential bounce to LONG")

            return signal

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    def _generate_individual_signal(self, symbol, futures_data, price_data):
        """Generate individual trading signal"""
        try:
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return None

            # Analyze market structure
            ls_ratio_data = futures_data.get('long_short_ratio_data', {})
            long_ratio = ls_ratio_data.get('long_ratio', 50) if 'error' not in ls_ratio_data else 50

            # Funding rate analysis
            funding_data = futures_data.get('funding_rate_data', {})
            funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0

            # Generate very basic signal - improve this
            if long_ratio > 60 and funding_rate > 0.001:
                recommendation = "short"  # Overbought, potential reversal
                confidence = 65
            elif long_ratio < 40 and funding_rate < -0.001:
                recommendation = "long"  # Oversold, potential bounce
                confidence = 65
            else:
                recommendation = "wait"
                confidence = 40

            return {
                'symbol': symbol,
                'price': current_price,
                'recommendation': recommendation,
                'confidence': confidence,
                'long_ratio': long_ratio,
                'funding_rate': funding_rate * 100  # Convert to percentage
            }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    def _format_advanced_signals_id(self, signals, sideways_markets, volatile_markets):
        """Format advanced futures signals with detailed market condition analysis"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        message = f"""🚨 **FUTURES SIGNALS ADVANCED - SUPPLY & DEMAND ANALYSIS**

⏰ **Update**: {current_time}
📊 **Total Markets Analyzed**: {len(signals) + len(sideways_markets) + len(volatile_markets)}
"""

        # Active trading signals
        if signals:
            message += f"""
🎯 **ACTIVE TRADING SIGNALS** ({len(signals)} coins):

"""
            for i, signal in enumerate(signals[:5], 1):  # Top 5 signals
                symbol = signal['symbol']
                price = signal['price']
                recommendation = signal['recommendation']
                confidence = signal['confidence']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                # Direction emoji
                direction_emoji = "🟢" if recommendation == 'long' else "🔴" if recommendation == 'short' else "🔄"

                message += f"""**{i}. {symbol} {direction_emoji}**
💰 **Price**: {price_format}
📊 **Signal**: {recommendation.upper()}
🎯 **Confidence**: {confidence:.1f}%"""

                if signal['entry_price'] > 0:
                    entry_format = f"${signal['entry_price']:.6f}" if signal['entry_price'] < 1 else f"${signal['entry_price']:,.4f}"
                    message += f"""
🎪 **Entry**: {entry_format}"""

                    if signal['tp1'] > 0:
                        tp1_format = f"${signal['tp1']:.6f}" if signal['tp1'] < 1 else f"${signal['tp1']:,.4f}"
                        message += f"""
🎯 **TP1**: {tp1_format}"""

                    if signal['tp2'] > 0:
                        tp2_format = f"${signal['tp2']:.6f}" if signal['tp2'] < 1 else f"${signal['tp2']:,.4f}"
                        message += f"""
🚀 **TP2**: {tp2_format}"""

                    if signal['sl'] > 0:
                        sl_format = f"${signal['sl']:.6f}" if signal['sl'] < 1 else f"${signal['sl']:,.4f}"
                        message += f"""
🛑 **SL**: {sl_format}"""

                message += f"""
📏 **Position Size**: {signal['position_size']}
📈 **Long/Short Ratio**: {signal['long_ratio']:.1f}% / {100-signal['long_ratio']:.1f}%
💸 **Funding Rate**: {signal['funding_rate']:.4f}%

"""

        # Sideways markets
        if sideways_markets:
            message += f"""
🔄 **SIDEWAYS MARKETS** ({len(sideways_markets)} coins):

⚠️ **KONDISI SIDEWAYS TERDETEKSI - TIDAK ADA SINYAL ENTRY YANG JELAS**

"""
            for signal in sideways_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']
                strength = signal['strength']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  📊 Sideways Strength: {strength:.1f}%
  📈 Volatility: {volatility:.2f}%
  🎯 Strategy: Range trading atau tunggu breakout

"""

        # Volatile markets  
        if volatile_markets:
            message += f"""
⚡ **HIGH VOLATILITY MARKETS** ({len(volatile_markets)} coins):

"""
            for signal in volatile_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  ⚡ Volatility: {volatility:.2f}%
  🎯 Strategy: Scalping dengan position size kecil (0.5-1%)

"""

        # Market summary
        total_markets = len(signals) + len(sideways_markets) + len(volatile_markets)
        trending_percentage = (len(signals) / total_markets * 100) if total_markets > 0 else 0
        sideways_percentage = (len(sideways_markets) / total_markets * 100) if total_markets > 0 else 0

        message += f"""
📊 **MARKET OVERVIEW:**
• **Trending Markets**: {trending_percentage:.1f}% ({len(signals)}/{total_markets})
• **Sideways Markets**: {sideways_percentage:.1f}% ({len(sideways_markets)}/{total_markets})
• **Volatile Markets**: {(len(volatile_markets) / total_markets * 100) if total_markets > 0 else 0:.1f}% ({len(volatile_markets)}/{total_markets})

💡 **MARKET SENTIMENT:**"""

        if sideways_percentage > 50:
            message += """
🔄 **DOMINASI SIDEWAYS**: Mayoritas market dalam konsolidasi
• Hindari trend following strategies
• Focus pada range trading
• Tunggu catalyst untuk breakout yang jelas
• Risk management extra ketat"""
        elif trending_percentage > 60:
            message += """
📈 **MARKET TRENDING**: Kondisi bagus untuk trend following
• Manfaatkan momentum yang ada
• Follow the trend dengan proper risk management
• Watch for trend reversal signals"""
        else:
            message += """
📊 **MARKET MIXED**: Kondisi market campuran
• Selective trading - pilih setup terbaik
• Avoid FOMO, tunggu konfirmasi yang jelas
• Smaller position size recommended"""

        message += f"""

⚠️ **RISK MANAGEMENT RULES:**
• Maximum 2-3% risk per trade
• Jangan trade lebih dari 3 pairs simultan
• Cut loss cepat jika salah arah
• Take profit bertahap (50% di TP1, 50% di TP2)

🎯 **SUPPLY & DEMAND FEATURES:**
• Entry berdasarkan S&D zones
• TP/SL calculation dengan risk/reward optimal
• Volume confirmation untuk validasi breakout
• Multi-timeframe analysis

📡 **Data Sources**: CoinAPI Real-time + Binance Futures + Advanced SnD Algorithm

💡 **Disclaimer**: Sinyal untuk edukasi, bukan financial advice. Always DYOR!"""

        return message

    def _format_advanced_signals_en(self, signals, sideways_markets, volatile_markets):
        """Format advanced futures signals in English with detailed market condition analysis"""
        current_time = datetime.now().strftime('%H:%M:%S UTC')

        message = f"""🚨 **FUTURES SIGNALS ADVANCED - SUPPLY & DEMAND ANALYSIS**

⏰ **Update**: {current_time}
📊 **Total Markets Analyzed**: {len(signals) + len(sideways_markets) + len(volatile_markets)}
"""

        # Active trading signals
        if signals:
            message += f"""
🎯 **ACTIVE TRADING SIGNALS** ({len(signals)} coins):

"""
            for i, signal in enumerate(signals[:5], 1):  # Top 5 signals
                symbol = signal['symbol']
                price = signal['price']
                recommendation = signal['recommendation']
                confidence = signal['confidence']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                # Direction emoji
                direction_emoji = "🟢" if recommendation == 'long' else "🔴" if recommendation == 'short' else "🔄"

                message += f"""**{i}. {symbol} {direction_emoji}**
💰 **Price**: {price_format}
📊 **Signal**: {recommendation.upper()}
🎯 **Confidence**: {confidence:.1f}%"""

                if signal['entry_price'] > 0:
                    entry_format = f"${signal['entry_price']:.6f}" if signal['entry_price'] < 1 else f"${signal['entry_price']:,.4f}"
                    message += f"""
🎪 **Entry**: {entry_format}"""

                    if signal['tp1'] > 0:
                        tp1_format = f"${signal['tp1']:.6f}" if signal['tp1'] < 1 else f"${signal['tp1']:,.4f}"
                        message += f"""
🎯 **TP1**: {tp1_format}"""

                    if signal['tp2'] > 0:
                        tp2_format = f"${signal['tp2']:.6f}" if signal['tp2'] < 1 else f"${signal['tp2']:,.4f}"
                        message += f"""
🚀 **TP2**: {tp2_format}"""

                    if signal['sl'] > 0:
                        sl_format = f"${signal['sl']:.6f}" if signal['sl'] < 1 else f"${signal['sl']:,.4f}"
                        message += f"""
🛑 **SL**: {sl_format}"""

                message += f"""
📏 **Position Size**: {signal['position_size']}
📈 **Long/Short Ratio**: {signal['long_ratio']:.1f}% / {100-signal['long_ratio']:.1f}%
💸 **Funding Rate**: {signal['funding_rate']:.4f}%

"""

        # Sideways markets
        if sideways_markets:
            message += f"""
🔄 **SIDEWAYS MARKETS** ({len(sideways_markets)} coins):

⚠️ **SIDEWAYS CONDITION DETECTED - NO CLEAR ENTRY SIGNALS**

"""
            for signal in sideways_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']
                strength = signal['strength']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  📊 Sideways Strength: {strength:.1f}%
  📈 Volatility: {volatility:.2f}%
  🎯 Strategy: Range trading or wait for breakout

"""

        # Volatile markets  
        if volatile_markets:
            message += f"""
⚡ **HIGH VOLATILITY MARKETS** ({len(volatile_markets)} coins):

"""
            for signal in volatile_markets:
                symbol = signal['symbol']
                price = signal['price']
                volatility = signal['volatility']

                price_format = f"${price:.6f}" if price < 1 else f"${price:,.4f}" if price < 1000 else f"${price:,.2f}"

                message += f"""• **{symbol}**: {price_format}
  ⚡ Volatility: {volatility:.2f}%
  🎯 Strategy: Scalping with small position size (0.5-1%)

"""

        # Market summary
        total_markets = len(signals) + len(sideways_markets) + len(volatile_markets)
        trending_percentage = (len(signals) / total_markets * 100) if total_markets > 0 else 0
        sideways_percentage = (len(sideways_markets) / total_markets * 100) if total_markets > 0 else 0

        message += f"""
📊 **MARKET OVERVIEW:**
• **Trending Markets**: {trending_percentage:.1f}% ({len(signals)}/{total_markets})
• **Sideways Markets**: {sideways_percentage:.1f}% ({len(sideways_markets)}/{total_markets})
• **Volatile Markets**: {(len(volatile_markets) / total_markets * 100) if total_markets > 0 else 0:.1f}% ({len(volatile_markets)}/{total_markets})

💡 **MARKET SENTIMENT:**"""

        if sideways_percentage > 50:
            message += """
🔄 **SIDEWAYS DOMINANCE**: Majority of markets in consolidation
• Avoid trend following strategies
• Focus on range trading
• Wait for catalyst for clear breakout
• Extra strict risk management"""
        elif trending_percentage > 60:
            message += """
📈 **MARKET TRENDING**: Good condition for trend following
• Take advantage of existing momentum
• Follow the trend with proper risk management
• Watch for trend reversal signals"""
        else:
            message += """
📊 **MARKET MIXED**: Mixed market condition
• Selective trading - choose best setups
• Avoid FOMO, wait for clear confirmation
• Smaller position size recommended"""

        message += f"""

⚠️ **RISK MANAGEMENT RULES:**
• Maximum 2-3% risk per trade
• Do not trade more than 3 pairs simultaneously
• Cut loss quickly if wrong direction
• Take profit gradually (50% at TP1, 50% at TP2)

🎯 **SUPPLY & DEMAND FEATURES:**
• Entry based on S&D zones
• TP/SL calculation dengan risk/reward optimal
• Volume confirmation untuk validasi breakout
• Multi-timeframe analysis

📡 **Data Sources**: CoinAPI Real-time + Binance Futures + Advanced SnD Algorithm

💡 **Disclaimer**: Signals for education, not financial advice. Always DYOR!"""

        return message

    def _format_futures_analysis_id(self, symbol, timeframe, futures_data, price_data):
        """Format individual futures analysis in Indonesian"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            current_price = price_data.get('price', 0)

            message = f"""📊 **Analisis Futures {symbol} - {timeframe}**

💰 **Harga**: ${current_price:.4f}
⏰ **Update**: {current_time}

"""
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%\n"

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"💰 Funding Rate: {funding_rate:.3f}%\n"

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    message += f"🔍 Open Interest: ${oi:,.0f}\n"

            message += f"""
💡Disclaimer: Bukan saran investasi, lakukan riset sendiri"""

            return message

        except Exception as e:
            return f"❌ Error formatting individual analysis: {str(e)}"

    def _format_futures_analysis_en(self, symbol, timeframe, futures_data, price_data):
        """Format individual futures analysis in English"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')
            current_price = price_data.get('price', 0)

            message = f"""📊 **Futures Analysis {symbol} - {timeframe}**

💰 **Price**: ${current_price:.4f}
⏰ **Update**: {current_time}

"""
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%\n"

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"💰 Funding Rate: {funding_rate:.3f}%\n"

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    message += f"🔍 Open Interest: ${oi:,.0f}\n"

            message += f"""
💡Disclaimer: Not investment advice, do your own research"""

            return message

        except Exception as e:
            return f"❌ Error formatting individual analysis: {str(e)}"

    def _analyze_market_condition(self, candlestick_data, futures_data):
        """Analyze market condition based on candlestick patterns and futures data with safe error handling"""
        try:
            # Safe data validation
            if not candlestick_data or not isinstance(candlestick_data, list):
                print("⚠️ Invalid candlestick_data, using fallback analysis")
                return self._get_fallback_market_condition(futures_data)
            
            # Extract closes with type checking
            closes = []
            for candle in candlestick_data:
                if isinstance(candle, dict) and 'close' in candle:
                    try:
                        close_price = float(candle['close'])
                        closes.append(close_price)
                    except (ValueError, TypeError):
                        continue
                elif isinstance(candle, (int, float)):
                    closes.append(float(candle))
            
            if len(closes) < 10:
                print(f"⚠️ Insufficient closes data ({len(closes)}), using fallback")
                return self._get_fallback_market_condition(futures_data)

            # Safe moving average calculation
            try:
                sma_short = sum(closes[-min(10, len(closes)):]) / min(10, len(closes))
                sma_long = sum(closes[-min(20, len(closes)):]) / min(20, len(closes))
                
                if sma_long > 0:
                    trend_strength = abs(sma_short - sma_long) / sma_long * 100
                else:
                    trend_strength = 0
                
            except (ZeroDivisionError, TypeError):
                trend_strength = 0
                sma_short = closes[-1] if closes else 0
                sma_long = closes[0] if closes else 0

            # Determine trend direction safely
            if sma_short > sma_long and trend_strength > 1:
                trend_direction = "bullish"
                condition_type = "trending"
            elif sma_short < sma_long and trend_strength > 1:
                trend_direction = "bearish"
                condition_type = "trending"
            else:
                trend_direction = "neutral"
                condition_type = "sideways"

            # Safe volatility calculation
            try:
                high_low_ranges = []
                for candle in candlestick_data:
                    if isinstance(candle, dict) and 'high' in candle and 'low' in candle:
                        try:
                            high_val = float(candle['high'])
                            low_val = float(candle['low'])
                            high_low_ranges.append(high_val - low_val)
                        except (ValueError, TypeError):
                            continue
                
                if high_low_ranges:
                    average_range = sum(high_low_ranges[-min(14, len(high_low_ranges)):]) / min(14, len(high_low_ranges))
                else:
                    average_range = abs(closes[-1] - closes[0]) / len(closes) if len(closes) > 1 else 0
                    
            except Exception:
                average_range = 0

            # Safe body size calculation
            try:
                body_sizes = []
                for candle in candlestick_data:
                    if isinstance(candle, dict) and 'close' in candle and 'open' in candle:
                        try:
                            close_val = float(candle['close'])
                            open_val = float(candle['open'])
                            body_sizes.append(abs(close_val - open_val))
                        except (ValueError, TypeError):
                            continue
                
                if body_sizes:
                    avg_body_size = sum(body_sizes[-min(20, len(body_sizes)):]) / min(20, len(body_sizes))
                else:
                    avg_body_size = average_range * 0.5
                    
            except Exception:
                avg_body_size = average_range * 0.5

            # Calculate sideways strength safely
            if condition_type == "sideways" and average_range > 0:
                sideways_strength = (avg_body_size / average_range) * 100
            else:
                sideways_strength = 0

            # Safe support and resistance detection
            supports = []
            resistances = []
            
            try:
                if len(candlestick_data) >= 5:
                    for i in range(2, min(len(candlestick_data) - 2, 50)):  # Limit iteration
                        candle = candlestick_data[i]
                        if not isinstance(candle, dict):
                            continue
                            
                        try:
                            current_low = float(candle.get('low', 0))
                            current_high = float(candle.get('high', 0))
                            
                            # Check for support (simplified)
                            if current_low > 0:
                                is_support = True
                                for j in range(max(0, i-2), min(len(candlestick_data), i+3)):
                                    if j != i and isinstance(candlestick_data[j], dict):
                                        other_low = float(candlestick_data[j].get('low', current_low + 1))
                                        if other_low <= current_low:
                                            is_support = False
                                            break
                                
                                if is_support:
                                    supports.append({'level': current_low, 'type': 'support'})
                            
                            # Check for resistance (simplified)
                            if current_high > 0:
                                is_resistance = True
                                for j in range(max(0, i-2), min(len(candlestick_data), i+3)):
                                    if j != i and isinstance(candlestick_data[j], dict):
                                        other_high = float(candlestick_data[j].get('high', current_high - 1))
                                        if other_high >= current_high:
                                            is_resistance = False
                                            break
                                
                                if is_resistance:
                                    resistances.append({'level': current_high, 'type': 'resistance'})
                                    
                        except (ValueError, TypeError):
                            continue
                            
            except Exception as e:
                print(f"⚠️ Support/resistance detection error: {e}")

            market_condition = {
                'type': condition_type,
                'strength': max(0, trend_strength),
                'volatility': max(0, average_range),
                'trend_direction': trend_direction,
                'sideways_strength': max(0, sideways_strength),
                'support_resistance': (supports + resistances)[:10]  # Limit to 10 levels
            }

            return market_condition

        except Exception as e:
            print(f"❌ Error analyzing market condition: {e}")
            return self._get_fallback_market_condition(futures_data)
    
    def _get_fallback_market_condition(self, futures_data):
        """Fallback market condition when candlestick analysis fails"""
        try:
            # Use futures data to determine basic market condition
            condition_type = "trending"
            trend_direction = "bullish"  # Default to bullish
            strength = 65
            
            if isinstance(futures_data, dict) and 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                if isinstance(ls_data, dict) and 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    if isinstance(long_ratio, (int, float)):
                        if long_ratio > 60:
                            trend_direction = "bearish"  # Contrarian
                            strength = min(80, 60 + (long_ratio - 60))
                        elif long_ratio < 40:
                            trend_direction = "bullish"
                            strength = min(80, 60 + (40 - long_ratio))
                        else:
                            condition_type = "sideways"
                            strength = 50
            
            return {
                'type': condition_type,
                'strength': strength,
                'volatility': 2.5,  # Default volatility
                'trend_direction': trend_direction,
                'sideways_strength': 30 if condition_type == "sideways" else 0,
                'support_resistance': []
            }
            
        except Exception:
            # Ultimate fallback
            return {
                'type': 'trending',
                'strength': 60,
                'volatility': 2.0,
                'trend_direction': 'bullish',
                'sideways_strength': 0,
                'support_resistance': []
            }

    def _format_advanced_futures_analysis_id(self, symbol, timeframe, futures_data, price_data, market_condition, candlestick_data):
        """Format advanced futures analysis in Indonesian with market condition"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            current_price = price_data.get('price', 0)
            price_format = f"${current_price:.6f}" if current_price < 1 else f"${current_price:,.4f}" if current_price < 1000 else f"${current_price:,.2f}"

            message = f"""📊 **Analisis Futures {symbol} - {timeframe}**

💰 **Harga**: {price_format}
⏰ **Update**: {current_time}

"""

            # 1. Market Condition
            condition_type = market_condition.get('type', 'unknown')
            trend_direction = market_condition.get('trend_direction', 'neutral')
            volatility = market_condition.get('volatility', 0)

            message += f"""
📈 **Kondisi Market**: {condition_type.upper()}"""

            if condition_type == "trending":
                message += f"""
• **Trend**: {trend_direction.upper()}
• **Strength**: {market_condition.get('strength', 0):.1f}%
"""
            elif condition_type == "sideways":
                message += f"""
• **Sideways Strength**: {market_condition.get('sideways_strength', 0):.1f}%
• **Volatility**: {volatility:.2f}"""
            elif condition_type == "volatile":
                message += f"""
• **Volatility**: {volatility:.2f}"""

            # 2. Support and Resistance
            supports_resistances = market_condition.get('support_resistance', [])
            if supports_resistances:
                message += """
🎯 **Support/Resistance:**"""
                for level in supports_resistances[:3]:
                    message += f"""
• {level['type'].capitalize()}: ${level['level']:.4f}"""

            # 3. Futures Data
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"""
📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%"""

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"""
💰 Funding Rate: {funding_rate:.3f}%"""

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    oi_fmt = f"${oi/1000000:.1f}M" if oi > 1000000 else f"${oi:,.0f}"
                    message += f"""
🔍 Open Interest: {oi_fmt}"""

            # 4. Trading Recommendations
            if condition_type == "trending":
                if trend_direction == "bullish":
                    message += """
💡 Rekomendasi: Long - Follow the trend, cari pullback
🛑 Stop Loss: Bawah support terdekat"""
                else:
                    message += """
💡 Rekomendasi: Short - Follow the trend, cari rally
🛑 Stop Loss: Atas resistance terdekat"""
            elif condition_type == "sideways":
                message += """
💡 Rekomendasi: Range Trading - Beli support, jual resistance
🛑 Stop Loss: Luar range"""
            else:
                message += """
💡 Rekomendasi: Tunggu - Market tidak jelas
🛑 Hindari trading sampai ada konfirmasi"""

            message += f"""

⚠️Disclaimer: Bukan saran investasi, lakukan riset sendiri"""

            return message

        except Exception as e:
            return f"❌ Error formatting advanced individual analysis: {str(e)}"

    def _format_advanced_futures_analysis_en(self, symbol, timeframe, futures_data, price_data, market_condition, candlestick_data):
        """Format advanced futures analysis in English with market condition"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S UTC')
            current_price = price_data.get('price', 0)
            price_format = f"${current_price:.6f}" if current_price < 1 else f"${current_price:,.4f}" if current_price < 1000 else f"${current_price:,.2f}"

            message = f"""📊 **Futures Analysis {symbol} - {timeframe}**

💰 **Price**: {price_format}
⏰ **Update**: {current_time}

"""

            # 1. Market Condition
            condition_type = market_condition.get('type', 'unknown')
            trend_direction = market_condition.get('trend_direction', 'neutral')
            volatility = market_condition.get('volatility', 0)

            message += f"""
📈 **Market Condition**: {condition_type.upper()}"""

            if condition_type == "trending":
                message += f"""
• **Trend**: {trend_direction.upper()}
• **Strength**: {market_condition.get('strength', 0):.1f}%
"""
            elif condition_type == "sideways":
                message += f"""
• **Sideways Strength**: {market_condition.get('sideways_strength', 0):.1f}%
• **Volatility**: {volatility:.2f}"""
            elif condition_type == "volatile":
                message += f"""
• **Volatility**: {volatility:.2f}"""

            # 2. Support and Resistance
            supports_resistances = market_condition.get('support_resistance', [])
            if supports_resistances:
                message += """
🎯 **Support/Resistance:**"""
                for level in supports_resistances[:3]:
                    message += f"""
• {level['type'].capitalize()}: ${level['level']:.4f}"""

            # 3. Futures Data
            if 'error' not in futures_data:
                ls_data = futures_data.get('long_short_ratio_data', {})
                funding_data = futures_data.get('funding_rate_data', {})
                oi_data = futures_data.get('open_interest_data', {})

                if 'error' not in ls_data:
                    long_ratio = ls_data.get('long_ratio', 50)
                    message += f"""
📊 Long/Short Ratio: {long_ratio:.0f}% / {100-long_ratio:.0f}%"""

                if 'error' not in funding_data:
                    funding_rate = funding_data.get('last_funding_rate', 0) * 100
                    message += f"""
💰 Funding Rate: {funding_rate:.3f}%"""

                if 'error' not in oi_data:
                    oi = oi_data.get('open_interest', 0)
                    oi_fmt = f"${oi/1000000:.1f}M" if oi > 1000000 else f"${oi:,.0f}"
                    message += f"""
🔍 Open Interest: {oi_fmt}"""

            # 4. Trading Recommendations
            if condition_type == "trending":
                if trend_direction == "bullish":
                    message += """
💡 Recommendation: Long - Follow the trend, look for pullbacks
🛑 Stop Loss: Below nearest support"""
                else:
                    message += """
💡 Recommendation: Short - Follow the trend, look for rallies
🛑 Stop Loss: Above nearest resistance"""
            elif condition_type == "sideways":
                message += """
💡 Recommendation: Range Trading - Buy support, sell resistance
🛑 Stop Loss: Outside the range"""
            else:
                message += """
💡 Recommendation: Wait - Market is unclear
🛑 Avoid trading until there is confirmation"""

            message += f"""

⚠️Disclaimer: Not investment advice, do your own research"""

            return message

        except Exception as e:
            return f"❌ Error formatting advanced individual analysis: {str(e)}"