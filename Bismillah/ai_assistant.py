
import os
import json
import time
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional, Tuple
import requests
import sqlite3

class AIAssistant:
    def __init__(self, crypto_api, db, auto_signals=None):
        self.crypto_api = crypto_api
        self.db = db
        self.auto_signals = auto_signals
        self.signal_cooldown = {}  # Store last signal time for each coin
        self.cooldown_minutes = 60  # 1 hour cooldown
        
        # CoinAPI endpoints
        self.coinapi_base = "https://rest.coinapi.io/v1"
        self.coinapi_key = os.getenv('COINAPI_KEY', '')
        
        # CMC endpoints  
        self.cmc_base = "https://pro-api.coinmarketcap.com/v1"
        self.cmc_key = os.getenv('CMC_API_KEY', '')
        
        print("✅ AI Assistant initialized with CoinAPI + CMC integration")

    def _get_coinapi_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> Dict:
        """Get OHLCV data from CoinAPI for specific timeframe"""
        try:
            # Convert symbol to CoinAPI format (e.g., BTC -> BINANCE_SPOT_BTC_USDT)
            if symbol.upper() == 'BTC':
                coinapi_symbol = 'BINANCE_SPOT_BTC_USDT'
            elif symbol.upper() == 'ETH':
                coinapi_symbol = 'BINANCE_SPOT_ETH_USDT'
            else:
                coinapi_symbol = f'BINANCE_SPOT_{symbol.upper()}_USDT'
            
            # Convert timeframe to CoinAPI format
            timeframe_map = {'5m': '5MIN', '1h': '1HRS', '4h': '4HRS', '1d': '1DAY'}
            api_timeframe = timeframe_map.get(timeframe, '1HRS')
            
            url = f"{self.coinapi_base}/ohlcv/{coinapi_symbol}/history"
            headers = {'X-CoinAPI-Key': self.coinapi_key}
            params = {
                'period_id': api_timeframe,
                'limit': limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        'success': True,
                        'data': data,
                        'symbol': symbol,
                        'timeframe': timeframe
                    }
            
            return {'success': False, 'error': f'CoinAPI error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': f'CoinAPI exception: {str(e)}'}

    def _calculate_technical_indicators(self, ohlcv_data: List[Dict]) -> Dict:
        """Calculate technical indicators from OHLCV data"""
        try:
            if len(ohlcv_data) < 50:
                return {'error': 'Insufficient data for indicators'}
            
            # Extract price data
            closes = [float(item['price_close']) for item in ohlcv_data]
            highs = [float(item['price_high']) for item in ohlcv_data]
            lows = [float(item['price_low']) for item in ohlcv_data]
            volumes = [float(item['volume_traded']) for item in ohlcv_data]
            
            # Calculate EMA50 and EMA200
            ema50 = self._calculate_ema(closes, 50)
            ema200 = self._calculate_ema(closes, 200) if len(closes) >= 200 else None
            
            # Calculate RSI
            rsi = self._calculate_rsi(closes, 14)
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(closes)
            
            # Calculate ATR
            atr = self._calculate_atr(highs, lows, closes, 14)
            
            # Calculate Volume Oscillator
            volume_osc = self._calculate_volume_oscillator(volumes)
            
            # Determine trend
            current_price = closes[-1]
            trend = 'neutral'
            if ema50 and ema200:
                if ema50 > ema200:
                    trend = 'bullish'
                elif ema50 < ema200:
                    trend = 'bearish'
            
            return {
                'price': current_price,
                'ema50': ema50,
                'ema200': ema200,
                'rsi': rsi,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'atr': atr,
                'volume_oscillator': volume_osc,
                'trend': trend,
                'data_points': len(closes)
            }
            
        except Exception as e:
            return {'error': f'Indicator calculation error: {str(e)}'}

    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return None
            
            multiplier = 2 / (period + 1)
            ema = sum(prices[:period]) / period  # Start with SMA
            
            for price in prices[period:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return round(ema, 2)
        except:
            return None

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        try:
            if len(prices) < period + 1:
                return None
            
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-change)
            
            if len(gains) < period:
                return None
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
        except:
            return None

    def _calculate_macd(self, prices: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD (12, 26, 9)"""
        try:
            if len(prices) < 35:
                return None, None, None
            
            ema12 = self._calculate_ema(prices, 12)
            ema26 = self._calculate_ema(prices, 26)
            
            if not ema12 or not ema26:
                return None, None, None
            
            macd_line = ema12 - ema26
            
            # Calculate signal line (9-period EMA of MACD line)
            # For simplicity, we'll use a basic calculation
            macd_signal = macd_line * 0.8  # Simplified signal line
            macd_histogram = macd_line - macd_signal
            
            return round(macd_line, 4), round(macd_signal, 4), round(macd_histogram, 4)
        except:
            return None, None, None

    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        try:
            if len(highs) < period + 1:
                return None
            
            true_ranges = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            if len(true_ranges) < period:
                return None
            
            atr = sum(true_ranges[-period:]) / period
            return round(atr, 4)
        except:
            return None

    def _calculate_volume_oscillator(self, volumes: List[float]) -> Optional[float]:
        """Calculate Volume Oscillator (5 vs 10 period)"""
        try:
            if len(volumes) < 10:
                return None
            
            short_avg = sum(volumes[-5:]) / 5
            long_avg = sum(volumes[-10:]) / 10
            
            if long_avg == 0:
                return None
            
            volume_osc = ((short_avg - long_avg) / long_avg) * 100
            return round(volume_osc, 2)
        except:
            return None

    def _get_cmc_global_metrics(self) -> Dict:
        """Get global market metrics from CoinMarketCap"""
        try:
            url = f"{self.cmc_base}/global-metrics/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_key,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote_data = data['data']['quote']['USD']
                
                return {
                    'success': True,
                    'total_market_cap': quote_data['total_market_cap'],
                    'total_volume_24h': quote_data['total_volume_24h'],
                    'market_cap_change_24h': quote_data['total_market_cap_yesterday_percentage_change'],
                    'volume_change_24h': quote_data['total_volume_24h_yesterday_percentage_change'],
                    'btc_dominance': data['data']['btc_dominance'],
                    'active_cryptocurrencies': data['data']['active_cryptocurrencies']
                }
            
            return {'success': False, 'error': f'CMC API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': f'CMC exception: {str(e)}'}

    def _calculate_confidence_score(self, technical_data: Dict, macro_data: Dict, signal_direction: str) -> int:
        """Calculate confidence score (0-100) based on technical + macro analysis"""
        try:
            score = 0
            
            # Technical Analysis (50 points max)
            if technical_data.get('ema50') and technical_data.get('ema200'):
                # EMA trend alignment (15 points)
                if signal_direction == 'BUY' and technical_data['ema50'] > technical_data['ema200']:
                    score += 15
                elif signal_direction == 'SELL' and technical_data['ema50'] < technical_data['ema200']:
                    score += 15
            
            # RSI scoring (10 points)
            rsi = technical_data.get('rsi')
            if rsi:
                if 45 <= rsi <= 65:
                    score += 10
                elif 40 <= rsi <= 70:
                    score += 5
            
            # MACD histogram alignment (10 points)
            macd_hist = technical_data.get('macd_histogram')
            if macd_hist:
                if signal_direction == 'BUY' and macd_hist > 0:
                    score += 10
                elif signal_direction == 'SELL' and macd_hist < 0:
                    score += 10
            
            # Volume Oscillator (5 points)
            vol_osc = technical_data.get('volume_oscillator')
            if vol_osc and vol_osc > 0:
                score += 5
            
            # ATR volatility check (5 points)
            atr = technical_data.get('atr')
            if atr and atr > 0:  # Simplified check
                score += 5
            
            # Macro Analysis (50 points max)
            if macro_data.get('success'):
                # Market cap change (15 points)
                mc_change = macro_data.get('market_cap_change_24h', 0)
                if mc_change > 1:
                    score += 15
                elif mc_change > -3:
                    score += 5
                
                # Volume change (10 points)
                vol_change = macro_data.get('volume_change_24h', 0)
                if vol_change > 5:
                    score += 10
                
                # BTC dominance stability (10 points)
                btc_dom = macro_data.get('btc_dominance', 0)
                if 40 <= btc_dom <= 60:  # Stable range
                    score += 10
                
                # Global sentiment alignment (15 points)
                if signal_direction == 'BUY' and mc_change > 0:
                    score += 15
                elif signal_direction == 'SELL' and mc_change < -2:
                    score += 15
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            print(f"Error calculating confidence score: {e}")
            return 0

    def _check_signal_cooldown(self, symbol: str) -> bool:
        """Check if signal is in cooldown period"""
        now = time.time()
        last_signal_time = self.signal_cooldown.get(symbol, 0)
        
        if now - last_signal_time < (self.cooldown_minutes * 60):
            return True  # Still in cooldown
        
        return False  # Cooldown expired

    def _update_signal_cooldown(self, symbol: str):
        """Update signal cooldown for symbol"""
        self.signal_cooldown[symbol] = time.time()

    def _multi_timeframe_analysis(self, symbol: str) -> Dict:
        """Perform multi-timeframe analysis (5m, 1h, 4h)"""
        try:
            timeframes = ['5m', '1h', '4h']
            analysis_results = {}
            
            for tf in timeframes:
                ohlcv_result = self._get_coinapi_ohlcv(symbol, tf)
                if ohlcv_result.get('success'):
                    technical = self._calculate_technical_indicators(ohlcv_result['data'])
                    analysis_results[tf] = technical
                else:
                    analysis_results[tf] = {'error': ohlcv_result.get('error', 'Unknown error')}
            
            return analysis_results
            
        except Exception as e:
            return {'error': f'Multi-timeframe analysis error: {str(e)}'}

    def _determine_signal_direction(self, analysis_5m: Dict, analysis_1h: Dict) -> Optional[str]:
        """Determine signal direction based on 5m and 1h alignment"""
        try:
            if 'error' in analysis_5m or 'error' in analysis_1h:
                return None
            
            trend_5m = analysis_5m.get('trend', 'neutral')
            trend_1h = analysis_1h.get('trend', 'neutral')
            
            # Both timeframes must agree
            if trend_5m == 'bullish' and trend_1h == 'bullish':
                return 'BUY'
            elif trend_5m == 'bearish' and trend_1h == 'bearish':
                return 'SELL'
            
            return None  # No agreement
            
        except Exception as e:
            print(f"Error determining signal direction: {e}")
            return None

    async def futures_command(self, symbol: str, user_id: int) -> str:
        """Enhanced futures analysis with confidence scoring"""
        try:
            print(f"🎯 Starting enhanced futures analysis for {symbol}")
            
            # Check if symbol is in cooldown
            if self._check_signal_cooldown(symbol):
                remaining_time = self.cooldown_minutes - ((time.time() - self.signal_cooldown.get(symbol, 0)) / 60)
                return f"⏳ Sinyal {symbol} masih dalam cooldown. Coba lagi dalam {int(remaining_time)} menit."
            
            # Multi-timeframe analysis
            timeframe_analysis = self._multi_timeframe_analysis(symbol)
            
            if 'error' in timeframe_analysis:
                return f"❌ Error analisis multi-timeframe: {timeframe_analysis['error']}"
            
            # Get macro data
            macro_data = self._get_cmc_global_metrics()
            
            # Determine signal direction
            analysis_5m = timeframe_analysis.get('5m', {})
            analysis_1h = timeframe_analysis.get('1h', {})
            analysis_4h = timeframe_analysis.get('4h', {})
            
            signal_direction = self._determine_signal_direction(analysis_5m, analysis_1h)
            
            if not signal_direction:
                return f"📊 **{symbol} Futures Analysis**\n\n❌ Tidak ada sinyal yang valid. Timeframe 5m dan 1h tidak selaras.\n\n**5m Trend**: {analysis_5m.get('trend', 'error')}\n**1h Trend**: {analysis_1h.get('trend', 'error')}"
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(analysis_1h, macro_data, signal_direction)
            
            # Only proceed if confidence >= 75
            if confidence < 75:
                return f"📊 **{symbol} Futures Analysis**\n\n⚠️ Confidence Score terlalu rendah: {confidence}%\nMinimal 75% untuk sinyal valid."
            
            # Update cooldown
            self._update_signal_cooldown(symbol)
            
            # Format comprehensive response
            price = analysis_1h.get('price', 0)
            ema50 = analysis_1h.get('ema50', 0)
            ema200 = analysis_1h.get('ema200', 0)
            rsi = analysis_1h.get('rsi', 0)
            macd_line = analysis_1h.get('macd_line', 0)
            macd_histogram = analysis_1h.get('macd_histogram', 0)
            atr = analysis_1h.get('atr', 0)
            
            # Market data
            mc_change = macro_data.get('market_cap_change_24h', 0) if macro_data.get('success') else 0
            vol_change = macro_data.get('volume_change_24h', 0) if macro_data.get('success') else 0
            btc_dom = macro_data.get('btc_dominance', 0) if macro_data.get('success') else 0
            
            # Direction emoji
            direction_emoji = "🚀" if signal_direction == "BUY" else "🔻"
            
            # Entry, TP, SL calculations (simplified)
            if signal_direction == "BUY":
                entry = price
                tp1 = price * 1.02  # 2% profit
                tp2 = price * 1.05  # 5% profit
                sl = price * 0.98   # 2% stop loss
            else:
                entry = price
                tp1 = price * 0.98  # 2% profit
                tp2 = price * 0.95  # 5% profit
                sl = price * 1.02   # 2% stop loss
            
            response = f"""🎯 **{symbol} Futures Signal**

{direction_emoji} **Arah**: {signal_direction}
🎯 **Confidence**: {confidence}%
💰 **Entry**: ${entry:,.4f}

📊 **Targets & Risk**:
🎯 TP1: ${tp1:,.4f} (2%)
🎯 TP2: ${tp2:,.4f} (5%)
🛑 SL: ${sl:,.4f} (2%)

📈 **Technical Analysis (1H)**:
• EMA50: ${ema50:,.2f}
• EMA200: ${ema200:,.2f}
• RSI: {rsi:.1f}
• MACD: {macd_line:.4f}
• MACD Histogram: {macd_histogram:.4f}
• ATR: {atr:.4f}

⏰ **Multi-Timeframe**:
• 5m: {timeframe_analysis['5m'].get('trend', 'error')}
• 1h: {timeframe_analysis['1h'].get('trend', 'error')}
• 4h: {timeframe_analysis['4h'].get('trend', 'error')}

🌍 **Global Market**:
• Market Cap 24h: {mc_change:+.2f}%
• Volume 24h: {vol_change:+.2f}%
• BTC Dominance: {btc_dom:.1f}%

⚠️ **Risk Management**:
- Gunakan max 2-5% dari portfolio
- Set stop loss sebelum entry
- Take profit bertahap (50% di TP1, 50% di TP2)

🔄 **Source**: CoinAPI + CoinMarketCap
⏳ **Next Signal**: {self.cooldown_minutes} menit"""

            return response
            
        except Exception as e:
            print(f"❌ Error in futures command: {e}")
            return f"❌ Error analisis futures: {str(e)}"

    async def futures_signals_command(self, user_id: int) -> str:
        """Multiple futures signals with confidence filtering"""
        try:
            print("🎯 Starting multiple futures signals analysis")
            
            # List of popular futures coins
            target_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']
            valid_signals = []
            
            # Get macro data once
            macro_data = self._get_cmc_global_metrics()
            
            for symbol in target_coins:
                try:
                    # Skip if in cooldown
                    if self._check_signal_cooldown(symbol):
                        continue
                    
                    # Multi-timeframe analysis
                    timeframe_analysis = self._multi_timeframe_analysis(symbol)
                    
                    if 'error' in timeframe_analysis:
                        continue
                    
                    # Determine signal direction
                    analysis_5m = timeframe_analysis.get('5m', {})
                    analysis_1h = timeframe_analysis.get('1h', {})
                    
                    signal_direction = self._determine_signal_direction(analysis_5m, analysis_1h)
                    
                    if not signal_direction:
                        continue
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence_score(analysis_1h, macro_data, signal_direction)
                    
                    # Only include high confidence signals
                    if confidence >= 75:
                        price = analysis_1h.get('price', 0)
                        
                        valid_signals.append({
                            'symbol': symbol,
                            'direction': signal_direction,
                            'confidence': confidence,
                            'price': price,
                            'trend_5m': analysis_5m.get('trend', 'neutral'),
                            'trend_1h': analysis_1h.get('trend', 'neutral'),
                            'rsi': analysis_1h.get('rsi', 0),
                            'ema50': analysis_1h.get('ema50', 0),
                            'ema200': analysis_1h.get('ema200', 0)
                        })
                        
                        # Update cooldown
                        self._update_signal_cooldown(symbol)
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue
            
            if not valid_signals:
                return "📊 **Futures Signals Scan**\n\n⏳ Tidak ada sinyal dengan confidence ≥75% saat ini.\nSemua coin sedang dalam cooldown atau tidak memenuhi kriteria."
            
            # Sort by confidence
            valid_signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Format response
            response = f"""🚀 **Futures Signals Dashboard**

📊 **Found {len(valid_signals)} high-confidence signals**
⚡ **Min Confidence**: 75%
🕐 **Scan Time**: {datetime.now().strftime('%H:%M:%S')}

"""
            
            for i, signal in enumerate(valid_signals[:5], 1):  # Limit to top 5
                direction_emoji = "🚀" if signal['direction'] == "BUY" else "🔻"
                
                response += f"""**#{i} {signal['symbol']}** {direction_emoji}
💰 Price: ${signal['price']:,.4f}
🎯 Confidence: {signal['confidence']}%
📊 Timeframes: {signal['trend_5m']} (5m) | {signal['trend_1h']} (1h)
📈 RSI: {signal['rsi']:.1f} | EMA: {signal['ema50']:,.2f}/{signal['ema200']:,.2f}

"""
            
            # Global market summary
            if macro_data.get('success'):
                mc_change = macro_data.get('market_cap_change_24h', 0)
                vol_change = macro_data.get('volume_change_24h', 0)
                btc_dom = macro_data.get('btc_dominance', 0)
                
                response += f"""🌍 **Global Market Context**:
• Market Cap 24h: {mc_change:+.2f}%
• Volume 24h: {vol_change:+.2f}%
• BTC Dominance: {btc_dom:.1f}%

⚠️ **Risk Management**:
- Maksimal 2-5% portfolio per sinyal
- Selalu gunakan stop loss
- Take profit bertahap

🔄 **Data Source**: CoinAPI + CMC Real-time"""
            
            return response
            
        except Exception as e:
            print(f"❌ Error in futures signals: {e}")
            return f"❌ Error generating futures signals: {str(e)}"

    async def analyze_command(self, symbol: str, user_id: int) -> str:
        """Enhanced crypto analysis with CoinAPI data"""
        try:
            print(f"🎯 Starting enhanced analysis for {symbol}")
            
            # Get multi-timeframe technical data
            timeframe_analysis = self._multi_timeframe_analysis(symbol)
            
            # Get fundamental data from CoinMarketCap
            fundamental_data = await self.crypto_api.get_coin_info(symbol)
            
            # Get global market data
            macro_data = self._get_cmc_global_metrics()
            
            # Format comprehensive analysis
            response = f"📊 **{symbol.upper()} Comprehensive Analysis**\n\n"
            
            # Fundamental section
            if fundamental_data.get('success'):
                coin_data = fundamental_data.get('data', {})
                response += f"""💎 **Fundamental Data**:
• **Rank**: #{coin_data.get('rank', 'N/A')}
• **Market Cap**: ${coin_data.get('market_cap', 0):,.0f}
• **Volume 24h**: ${coin_data.get('volume_24h', 0):,.0f}
• **Circulating Supply**: {coin_data.get('circulating_supply', 0):,.0f}
• **Price Change 24h**: {coin_data.get('percent_change_24h', 0):+.2f}%

"""
            
            # Technical analysis section
            if '1h' in timeframe_analysis and 'error' not in timeframe_analysis['1h']:
                tech_data = timeframe_analysis['1h']
                response += f"""📈 **Technical Analysis (1H)**:
• **Current Price**: ${tech_data.get('price', 0):,.4f}
• **EMA50**: ${tech_data.get('ema50', 0):,.2f}
• **EMA200**: ${tech_data.get('ema200', 0):,.2f}
• **RSI**: {tech_data.get('rsi', 0):.1f}
• **MACD**: {tech_data.get('macd_line', 0):.4f}
• **ATR**: {tech_data.get('atr', 0):.4f}
• **Trend**: {tech_data.get('trend', 'neutral').title()}

"""
            
            # Multi-timeframe overview
            response += "⏰ **Multi-Timeframe Overview**:\n"
            for tf in ['5m', '1h', '4h']:
                if tf in timeframe_analysis:
                    trend = timeframe_analysis[tf].get('trend', 'error')
                    response += f"• **{tf}**: {trend.title()}\n"
            response += "\n"
            
            # Global market context
            if macro_data.get('success'):
                response += f"""🌍 **Global Market Context**:
• **Total Market Cap**: ${macro_data.get('total_market_cap', 0):,.0f}
• **24h Volume**: ${macro_data.get('total_volume_24h', 0):,.0f}
• **Market Cap Change**: {macro_data.get('market_cap_change_24h', 0):+.2f}%
• **BTC Dominance**: {macro_data.get('btc_dominance', 0):.1f}%

"""
            
            # Trading recommendation
            if '1h' in timeframe_analysis and 'error' not in timeframe_analysis['1h']:
                tech_data = timeframe_analysis['1h']
                rsi = tech_data.get('rsi', 50)
                trend = tech_data.get('trend', 'neutral')
                
                if trend == 'bullish' and 30 < rsi < 70:
                    recommendation = "🟢 **BULLISH** - Momentum positif dengan RSI sehat"
                elif trend == 'bearish' and 30 < rsi < 70:
                    recommendation = "🔴 **BEARISH** - Momentum negatif, hati-hati"
                elif rsi > 70:
                    recommendation = "🟡 **OVERBOUGHT** - Potensi koreksi"
                elif rsi < 30:
                    recommendation = "🟡 **OVERSOLD** - Potensi rebound"
                else:
                    recommendation = "⚪ **NEUTRAL** - Tunggu konfirmasi"
                
                response += f"🎯 **Trading Recommendation**: {recommendation}\n\n"
            
            response += f"""💡 **Tips Trading**:
• Gunakan stop loss 2-3%
• Take profit bertahap
• Perhatikan volume dan volatilitas
• Konfirmasi dengan berita fundamental

🔄 **Data Sources**: CoinAPI (Technical) + CoinMarketCap (Fundamental)
📅 **Analysis Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            return response
            
        except Exception as e:
            print(f"❌ Error in analyze command: {e}")
            return f"❌ Error analisis: {str(e)}"

    def get_ai_response(self, text: str, language: str = 'id', user_id: int = None) -> str:
        """Enhanced AI response with crypto expertise"""
        text_lower = text.lower()
        
        try:
            # Price query detection
            if any(keyword in text_lower for keyword in ['harga', 'price']) and any(coin in text_lower for coin in ['btc', 'bitcoin', 'eth', 'ethereum']):
                if 'btc' in text_lower or 'bitcoin' in text_lower:
                    return "💰 Untuk cek harga Bitcoin real-time, gunakan `/price btc`\nUntuk analisis lengkap: `/analyze btc`\nUntuk sinyal trading: `/futures btc`"
                elif 'eth' in text_lower or 'ethereum' in text_lower:
                    return "💰 Untuk cek harga Ethereum real-time, gunakan `/price eth`\nUntuk analisis lengkap: `/analyze eth`\nUntuk sinyal trading: `/futures eth`"
            
            # Bitcoin explanation
            if any(keyword in text_lower for keyword in ['bitcoin', 'btc', 'apa itu bitcoin']):
                return """₿ **Bitcoin (BTC) - Digital Gold**

🌟 **Definisi**: Cryptocurrency pertama dan terbesar di dunia, diciptakan Satoshi Nakamoto 2009.

🔑 **Keunggulan Bitcoin**:
- **Decentralized**: Tidak dikontrol pemerintah/bank
- **Blockchain Technology**: Transparansi & keamanan tinggi
- **Limited Supply**: Hanya 21 juta BTC yang akan ada
- **Store of Value**: Lindung nilai inflasi
- **Global**: Transfer ke mana saja 24/7

💡 **Kegunaan Bitcoin**:
- Investment/Trading asset
- Medium of exchange (alat tukar)
- Hedge against inflation (lindung nilai)
- Portfolio diversification

📊 **Untuk analisis Bitcoin**:
• `/price btc` - Harga real-time
• `/analyze btc` - Analisis mendalam
• `/futures btc` - Sinyal trading

🚀 **Bitcoin adalah "Digital Gold" era modern!**"""

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal', 'signal']):
                return """📊 **CryptoMentor AI - Advanced Analysis**

🎯 **Fitur Analisis Terbaru**:

**📈 Technical Analysis**:
• Multi-timeframe (5m, 1h, 4h)
• EMA50/200, RSI, MACD, ATR
• Volume Oscillator
• Supply & Demand zones

**🌍 Macro Analysis**:
• Global market cap & volume
• BTC dominance tracking
• Market sentiment analysis
• 24h change monitoring

**🤖 AI Confidence Scoring**:
• Technical (50 points) + Macro (50 points)
• Minimum 75% untuk sinyal valid
• Multi-timeframe confirmation
• 1 jam cooldown per coin

**💡 Commands**:
• `/analyze <symbol>` - Analisis komprehensif
• `/futures <symbol>` - Sinyal trading dengan confidence score
• `/futures_signals` - Multiple signals dashboard

🔄 **Data Real-time**: CoinAPI + CoinMarketCap"""

            elif any(keyword in text_lower for keyword in ['help', 'bantuan', 'command', 'perintah']):
                return """🤖 **CryptoMentor AI - Command Guide**

📊 **Analysis Commands**:
• `/price <symbol>` - Real-time price **[GRATIS]**
• `/analyze <symbol>` - Comprehensive analysis (20 credit)
• `/futures <symbol>` - Trading signals + confidence (20 credit)
• `/futures_signals` - Multiple signals dashboard (60 credit)
• `/market` - Global market overview (20 credit)

💼 **Portfolio & Account**:
• `/portfolio` - Portfolio tracker
• `/credits` - Check credit balance
• `/subscribe` - Upgrade premium

🎯 **Others**:
• `/ask_ai <question>` - Ask crypto questions **[GRATIS]**
• `/referral` - Referral program
• `/help` - Complete guide

🚀 **Premium Features**:
- Unlimited access to all commands
- Auto SnD signals (Lifetime only)
- Priority support
- Advanced analytics

💡 **Data Sources**: CoinAPI + CoinMarketCap + Internal AI"""

            elif any(keyword in text_lower for keyword in ['ethereum', 'eth']):
                return """⚡ **Ethereum (ETH) - World Computer**

🌟 **Definisi**: Platform blockchain untuk smart contracts dan aplikasi terdesentralisasi (dApps).

🔑 **Keunggulan Ethereum**:
- **Smart Contracts**: Kontrak otomatis tanpa perantara
- **DeFi Ecosystem**: Keuangan terdesentralisasi terbesar
- **NFT Platform**: Pasar NFT utama dunia
- **Proof of Stake**: Lebih hemat energi setelah "The Merge"
- **Developer Friendly**: Bahasa Solidity untuk dApps

💡 **Use Cases Ethereum**:
- DeFi protocols (lending, DEX, yield farming)
- NFT marketplace
- Gaming & metaverse
- DAOs (Decentralized Organizations)
- Enterprise blockchain solutions

📊 **Untuk analisis Ethereum**:
• `/price eth` - Harga real-time
• `/analyze eth` - Analisis fundamental + technical
• `/futures eth` - Sinyal trading ETH

🚀 **Ethereum = "World Computer" untuk Web3!**"""

            else:
                return f"""🤖 **CryptoMentor AI Assistant**

Saya memahami pertanyaan Anda: "{text}"

💡 **Yang bisa saya bantu**:
- ✅ Analisis harga crypto real-time
- ✅ Sinyal trading dengan confidence score
- ✅ Technical analysis multi-timeframe  
- ✅ Global market analysis
- ✅ Pertanyaan crypto umum
- ✅ Tutorial trading & investing

🎯 **Coba gunakan command spesifik**:
• `/price btc` - Harga Bitcoin
• `/analyze eth` - Analisis Ethereum
• `/futures btc` - Sinyal trading Bitcoin
• `/help` - Panduan lengkap

Atau tanya lebih spesifik tentang crypto!"""

        except Exception as e:
            print(f"Error in AI response: {e}")
            return "🤖 Maaf, terjadi error. Coba tanya lagi atau gunakan command yang tersedia."

    # Auto signal integration methods
    async def scan_for_auto_signals(self) -> List[Dict]:
        """Scan multiple coins for auto signals"""
        try:
            target_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK', 
                            'ALGO', 'ATOM', 'FTM', 'NEAR', 'SAND', 'MANA', 'AXS', 'ICP', 'THETA', 'VET',
                            'FIL', 'TRX', 'ETC', 'AAVE', 'UNI']
            
            valid_signals = []
            macro_data = self._get_cmc_global_metrics()
            
            print(f"🔍 Scanning {len(target_symbols)} altcoins for enhanced SnD signals...")
            
            for symbol in target_symbols:
                try:
                    # Skip if in cooldown
                    if self._check_signal_cooldown(symbol):
                        continue
                    
                    # Multi-timeframe analysis
                    timeframe_analysis = self._multi_timeframe_analysis(symbol)
                    
                    if 'error' in timeframe_analysis:
                        continue
                    
                    # Check 5m and 1h alignment
                    analysis_5m = timeframe_analysis.get('5m', {})
                    analysis_1h = timeframe_analysis.get('1h', {})
                    
                    signal_direction = self._determine_signal_direction(analysis_5m, analysis_1h)
                    
                    if not signal_direction:
                        continue
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence_score(analysis_1h, macro_data, signal_direction)
                    
                    # Filter for high confidence signals
                    if confidence >= 70:  # Slightly lower threshold for auto signals
                        price = analysis_1h.get('price', 0)
                        
                        signal_data = {
                            'symbol': symbol,
                            'direction': signal_direction,
                            'confidence': confidence,
                            'price': price,
                            'timeframe_5m': analysis_5m.get('trend', 'neutral'),
                            'timeframe_1h': analysis_1h.get('trend', 'neutral'),
                            'rsi': analysis_1h.get('rsi', 0),
                            'ema50': analysis_1h.get('ema50', 0),
                            'ema200': analysis_1h.get('ema200', 0),
                            'macd_histogram': analysis_1h.get('macd_histogram', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        valid_signals.append(signal_data)
                        
                        # Update cooldown
                        self._update_signal_cooldown(symbol)
                        
                        print(f"✅ Found signal: {symbol} {signal_direction} ({confidence}%)")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
                    continue
            
            print(f"📊 Auto signal scan completed: {len(valid_signals)} signals found")
            return valid_signals
            
        except Exception as e:
            print(f"❌ Error in auto signal scan: {e}")
            return []

    def format_auto_signal_message(self, signal: Dict, macro_data: Dict = None) -> str:
        """Format auto signal message for Telegram"""
        try:
            direction_emoji = "🚀" if signal['direction'] == "BUY" else "🔻"
            
            # Entry, TP, SL calculations
            price = signal['price']
            if signal['direction'] == "BUY":
                entry = price
                tp1 = price * 1.015  # 1.5%
                tp2 = price * 1.03   # 3%
                sl = price * 0.985   # 1.5% SL
            else:
                entry = price
                tp1 = price * 0.985  # 1.5%
                tp2 = price * 0.97   # 3%
                sl = price * 1.015   # 1.5% SL
            
            message = f"""🎯 **Auto SnD Signal**

{direction_emoji} **{signal['symbol']}** - {signal['direction']}
🎯 **Confidence**: {signal['confidence']}%
💰 **Entry**: ${entry:,.4f}

📊 **Targets**:
🎯 TP1: ${tp1:,.4f} (1.5%)
🎯 TP2: ${tp2:,.4f} (3%)
🛑 SL: ${sl:,.4f} (1.5%)

📈 **Technical**:
• Timeframes: {signal['timeframe_5m']} (5m) | {signal['timeframe_1h']} (1h)
• RSI: {signal['rsi']:.1f}
• EMA: {signal['ema50']:,.2f}/{signal['ema200']:,.2f}
• MACD: {signal['macd_histogram']:+.4f}

⚠️ **Risk**: Max 2% portfolio
🔄 **Source**: CoinAPI Enhanced SnD
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}"""
            
            return message
            
        except Exception as e:
            print(f"Error formatting auto signal: {e}")
            return f"🎯 Auto Signal: {signal.get('symbol', 'Unknown')} {signal.get('direction', 'Unknown')}"
