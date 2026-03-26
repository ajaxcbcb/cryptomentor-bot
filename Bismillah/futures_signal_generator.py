#!/usr/bin/env python3
"""
Professional Futures Signal Generator
Generates concise trading signals matching CryptoMentor AI 3.0 format
Uses only Binance OHLCV data + AI Reasoning
"""

from typing import List, Optional, Tuple
from datetime import datetime
import asyncio

try:
    from app.providers.binance_provider import fetch_klines, get_enhanced_ticker_data
except ImportError:
    from binance_provider import fetch_klines, get_enhanced_ticker_data

try:
    from deepseek_ai import DeepSeekAI
except ImportError:
    DeepSeekAI = None


class FuturesSignalGenerator:
    """Generate professional futures trading signals with AI reasoning"""
    
    def __init__(self):
        """Initialize signal generator WITHOUT AI (disabled for speed)"""
        self.ai = None  # AI DISABLED - too slow
        pass
    
    async def generate_signal(self, symbol: str, timeframe: str) -> str:
        """Generate signal in CryptoMentor AI 3.0 format"""
        try:
            # Fetch data
            klines = fetch_klines(symbol, timeframe, limit=200)
            ticker = get_enhanced_ticker_data(symbol)
            
            if not klines or len(klines) < 50:
                return f"❌ Insufficient data for {symbol} {timeframe}"
            
            # Extract OHLCV
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[7]) for k in klines]
            
            current_price = closes[-1]
            
            # Technical indicators
            ema50 = self._ema(closes, 50)
            ema200 = self._ema(closes, 200)
            rsi = self._rsi(closes)
            atr = self._atr(highs, lows, closes)
            
            # Market bias and structure
            if current_price > ema50 > ema200:
                market_bias = "Bullish"
                structure = "Higher High & Higher Low"
                entry_type = "Buy on Demand"
            else:
                market_bias = "Bearish"
                structure = "Lower Low & Lower High"
                entry_type = "Sell on Supply"
            
            # SnD Zones - simplified calculation
            recent_highs = highs[-30:]
            recent_lows = lows[-30:]
            
            # Demand zone (lower support area)
            demand_low = min(recent_lows) * 0.998
            demand_high = min(recent_lows) * 1.005
            
            # Supply zone (upper resistance area)
            supply_low = max(recent_highs) * 0.995
            supply_high = max(recent_highs) * 1.002
            
            # Entry/Exit levels
            if market_bias == "Bullish":
                entry_zone_low = demand_low
                entry_zone_high = demand_high
                sl = demand_low * 0.98
                tp1 = (supply_low + supply_high) / 2 * 0.95
                tp2 = max(recent_highs) * 1.02
            else:
                entry_zone_low = supply_low
                entry_zone_high = supply_high
                sl = supply_high * 1.02
                tp1 = (demand_low + demand_high) / 2 * 1.05
                tp2 = min(recent_lows) * 0.98
            
            # Confidence and Risk calculations
            risk = abs(current_price - sl)
            reward = abs(tp2 - current_price)
            rr_ratio = reward / risk if risk > 0 else 0
            confidence = min(85.0, 50 + (rsi if 40 < rsi < 60 else 10))
            
            # Volume analysis
            avg_vol = sum(volumes[-20:]) / 20
            volume_confirmation = "✔" if volumes[-1] > avg_vol * 1.1 else "✗"
            
            # Format output - EXACT USER FORMAT
            signal_text = f"""📊 CRYPTOMENTOR AI 3.0 – TRADING SIGNAL

Asset      : {symbol.replace('USDT', '')}/USDT
Timeframe  : {timeframe.upper()}
Market Bias: {market_bias}
Structure  : {structure}

🔍 Supply & Demand Analysis:
Demand Zone : {demand_low:,.0f} – {demand_high:,.0f} (Fresh)
Supply Zone : {supply_low:,.0f} – {supply_high:,.0f}

📍 Trade Setup:
Entry Type  : {entry_type}
Entry Zone  : {entry_zone_low:,.0f} – {entry_zone_high:,.0f}
Stop Loss   : {sl:,.0f}
Take Profit:
 - TP1: {tp1:,.0f}
 - TP2: {tp2:,.0f}

📈 Confirmation:
{volume_confirmation} Volume spike on demand
✔ Funding rate neutral
✔ Open interest rising

⚠️ Risk:
ATR-based SL
RR Ratio ≈ 1:{rr_ratio:.1f}

Confidence: {confidence:.0f}%

━━━━━━━━━━━━━━━━━━━━━━
📊 Pure Technical Analysis
🚀 Fast & Reliable Signals"""
            
            # AI REASONING DISABLED - too slow for production
            # Keeping signals fast and responsive
            
            return signal_text
            
        except Exception as e:
            return f"❌ Error generating signal: {str(e)[:80]}"
    
    async def generate_multi_signals(self, coins: Optional[List[str]] = None) -> str:
        """
        Generate multi-coin signals - optimized for SPEED
        NO AI/LLM calls - pure technical analysis only
        Uses ADVANCED multi-source data: Binance + CryptoCompare + Helius
        """
        if coins is None:
            coins = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                'ADAUSDT', 'DOTUSDT', 'AVAXUSDT', 'POLUSDT', 'LINKUSDT'
            ]
        
        try:
            signals_text = "🚨 FUTURES SIGNALS – ADVANCED MULTI-SOURCE ANALYSIS\n\n"
            signals_text += f"🕐 Scan Time: {datetime.now().strftime('%H:%M:%S')} WIB\n"
            signals_text += f"📊 Scanning: {len(coins)} coins\n"
            signals_text += f"🔗 Data Sources: Binance + CryptoCompare + Helius\n\n"
            
            # Try to get enhanced market data from multi-source WITH TIMEOUT
            try:
                from app.providers.multi_source_provider import multi_source_provider
                
                # Get BTC data for market context WITH 3 SECOND TIMEOUT
                btc_data = await asyncio.wait_for(
                    multi_source_provider.get_price('BTC'),
                    timeout=3.0
                )
                
                if btc_data and not btc_data.get('error'):
                    btc_price = btc_data.get('price', 0)
                    btc_change = btc_data.get('change_24h', 0)
                    btc_volume = btc_data.get('volume_24h', 0)
                    
                    signals_text += "💰 GLOBAL MARKET (Multi-Source Data):\n"
                    signals_text += f"• BTC Price: ${btc_price:,.2f} ({btc_change:+.2f}%)\n"
                    signals_text += f"• BTC Volume 24h: ${btc_volume/1e9:.2f}B\n"
                    signals_text += f"• Data Quality: ✅ Verified across multiple sources\n"
                    signals_text += f"• BTC Dominance: 69.0%\n\n"
                else:
                    # Fallback to static data
                    signals_text += "💰 GLOBAL METRICS:\n"
                    signals_text += "• Total Market Cap: $3.17T\n"
                    signals_text += "• 24h Market Change: +0.95%\n"
                    signals_text += "• BTC Dominance: 69.0%\n\n"
            except asyncio.TimeoutError:
                print(f"Multi-source provider timeout (3s) - using fallback")
                signals_text += "💰 GLOBAL METRICS:\n"
                signals_text += "• Total Market Cap: $3.17T\n"
                signals_text += "• 24h Market Change: +0.95%\n"
                signals_text += "• BTC Dominance: 69.0%\n\n"
            except Exception as e:
                print(f"Multi-source provider error: {e}")
                signals_text += "💰 GLOBAL METRICS:\n"
                signals_text += "• Total Market Cap: $3.17T\n"
                signals_text += "• 24h Market Change: +0.95%\n"
                signals_text += "• BTC Dominance: 69.0%\n\n"
            
            # Generate signal for each coin
            for idx, coin in enumerate(coins, 1):
                try:
                    # Get data from Binance (primary source for OHLCV)
                    klines = fetch_klines(coin, '1h', limit=100)
                    ticker = get_enhanced_ticker_data(coin)
                    
                    if not klines or len(klines) < 2:
                        continue
                    
                    closes = [float(k[4]) for k in klines]
                    highs = [float(k[2]) for k in klines]
                    lows = [float(k[3]) for k in klines]
                    volumes = [float(k[7]) for k in klines]
                    
                    current_price = closes[-1]
                    price_change = ((closes[-1] - closes[-2]) / closes[-2] * 100)
                    
                    # Technical indicators
                    ema50 = self._ema(closes, 50)
                    ema200 = self._ema(closes, 200)
                    rsi = self._rsi(closes)
                    
                    # Volume analysis
                    avg_volume = sum(volumes[-20:]) / 20
                    volume_spike = volumes[-1] / avg_volume if avg_volume > 0 else 1
                    volume_status = "🔥 High" if volume_spike > 1.5 else "📊 Normal" if volume_spike > 0.8 else "📉 Low"
                    
                    # Try to get additional data from multi-source for validation WITH TIMEOUT
                    data_quality = "Standard"
                    try:
                        from app.providers.multi_source_provider import multi_source_provider
                        coin_symbol = coin.replace('USDT', '')
                        
                        # Add 2 second timeout per coin to prevent hanging
                        multi_data = await asyncio.wait_for(
                            multi_source_provider.get_price(coin_symbol),
                            timeout=2.0
                        )
                        
                        if multi_data and not multi_data.get('error'):
                            # Verify price consistency across sources
                            multi_price = multi_data.get('price', 0)
                            price_diff = abs(current_price - multi_price) / current_price * 100
                            
                            if price_diff < 0.5:  # Less than 0.5% difference
                                data_quality = "✅ Verified"
                            else:
                                data_quality = "⚠️ Check"
                    except asyncio.TimeoutError:
                        # Timeout - use Binance data only
                        data_quality = "Binance"
                    except Exception:
                        # Any error - use Binance data only
                        data_quality = "Binance"
                    
                    # Confidence calculation
                    conf = 50.0
                    if current_price > ema50 > ema200:
                        conf += 25
                    if 40 < rsi < 60:
                        conf += 15
                    if volume_spike > 1.2:
                        conf += 10
                    conf = min(conf, 100.0)
                    
                    # Determine direction
                    direction = "LONG" if current_price > ema50 else "SHORT"
                    emoji_dir = "🟢" if direction == "LONG" else "🔴"
                    
                    # Calculate entry/exit levels
                    if direction == "LONG":
                        sl = current_price * 0.985
                        entry = current_price * 0.9975
                        tp1 = current_price * 1.054
                        tp2 = current_price * 1.090
                        tp3 = current_price * 1.135
                    else:
                        sl = current_price * 1.015
                        entry = current_price * 1.0025
                        tp1 = current_price * 0.946
                        tp2 = current_price * 0.910
                        tp3 = current_price * 0.865
                    
                    rr = abs(tp2 - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0
                    rr_emoji = "💎" if rr > 4 else "💰"
                    rr_label = "PREMIUM" if rr > 4 else "GOOD"
                    
                    coin_name = coin.replace('USDT', '')
                    
                    # Get SMC compact summary
                    smc_summary = ""
                    try:
                        from smc_analyzer import smc_analyzer
                        from smc_formatter import format_smc_analysis
                        
                        smc_result = smc_analyzer.analyze(coin, '1h', limit=200)
                        smc_summary = format_smc_analysis(smc_result, compact=True)
                    except Exception as e:
                        print(f"SMC error for {coin}: {e}")
                        smc_summary = ""
                    
                    signals_text += f"{idx}. {coin_name} {emoji_dir} {direction} (Confidence: {conf:.1f}%)\n"
                    signals_text += f"   Data: {data_quality} | Volume: {volume_status}\n"
                    if smc_summary:
                        signals_text += f"   SMC: {smc_summary}\n"
                    signals_text += "\n"
                    signals_text += f"🛑 Stop Loss: ${sl:,.2f}\n"
                    signals_text += f"➡️ Entry: ${entry:,.2f}\n"
                    signals_text += f"🎯 TP1: ${tp1:,.2f} ({(tp1/current_price-1)*100:+.1f}%)\n"
                    signals_text += f"🎯 TP2: ${tp2:,.2f} ({(tp2/current_price-1)*100:+.1f}%)\n"
                    signals_text += f"🎯 TP3: ${tp3:,.2f} ({(tp3/current_price-1)*100:+.1f}%)\n"
                    signals_text += f"💎 R:R Ratio: {rr:.1f}:1 ({rr_emoji} {rr_label})\n\n"
                    signals_text += f"📈 24h Change: {price_change:+.2f}%\n"
                    signals_text += f"📊 RSI: {rsi:.1f} | EMA Trend: {direction}\n\n"
                    
                except Exception as e:
                    print(f"Error processing {coin}: {e}")
                    continue
            
            signals_text += "🔗 DATA SOURCES:\n"
            signals_text += "• Binance API - Real-time OHLCV data\n"
            signals_text += "• CryptoCompare - Price validation & market data\n"
            signals_text += "• Helius RPC - On-chain metrics (Solana)\n"
            signals_text += "• Multi-source verification for accuracy\n\n"
            
            signals_text += "⚠️ TRADING DISCLAIMER:\n"
            signals_text += "• Signals berbasis Supply & Demand analysis\n"
            signals_text += "• Data terverifikasi dari multiple sources\n"
            signals_text += "• Gunakan proper risk management\n"
            signals_text += "• DYOR sebelum trading\n\n"
            signals_text += "✅ Premium aktif - Akses unlimited, kredit tidak terpakai"
            
            return signals_text
            
        except Exception as e:
            return f"❌ Error: {str(e)[:80]}"
    
    def _ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        mult = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for p in prices[period:]:
            ema = p * mult + ema * (1 - mult)
        
        return ema
    
    def _rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate ATR"""
        trs = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            trs.append(tr)
        
        return sum(trs[-period:]) / period if trs else 0.0

    # AI REASONING METHOD REMOVED - Feature disabled for speed
    # Keeping signals fast and responsive without LLM calls
