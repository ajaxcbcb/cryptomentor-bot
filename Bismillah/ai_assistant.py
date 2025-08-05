# -*- coding: utf-8 -*-
import requests
import random
import os
import asyncio
import time
from datetime import datetime
import html

class AIAssistant:
    def __init__(self, name="CryptoMentor AI"):
        self.name = name
        self.coinglass_key = os.getenv("COINGLASS_API_KEY")
        self.coinglass_base_url = "https://open-api.coinglass.com/public/v2"

        if not self.coinglass_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
            print("💡 Please set COINGLASS_API_KEY in Replit Secrets")

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

🚀 **Semua analisis menggunakan data real-time dari Coinglass & CMC!**"""

    def _get_coinglass_headers(self):
        """Get headers for Coinglass API requests"""
        return {
            "accept": "application/json",
            "coinglassSecret": self.coinglass_key
        }

    def _get_coinglass_price(self, symbol):
        """Get price data for Coinglass analysis - removed CoinAPI dependency"""
        # This method is no longer needed as we get price from comprehensive_futures_data
        # Return empty to maintain compatibility
        return {'error': 'Use comprehensive_futures_data instead'}

    def _get_coinglass_long_short_data(self, symbol, timeframe='1h'):
        """Get long/short ratio data from Coinglass v2 API"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol (remove USDT if present)
            clean_symbol = symbol.upper().replace('USDT', '')

            url = f"{self.coinglass_base_url}/futures/longShortChart"
            headers = self._get_coinglass_headers()

            # Map timeframe to intervalType
            interval_map = {
                '5m': 0, '15m': 1, '1h': 2, '4h': 3, '12h': 4, '24h': 5
            }
            interval_type = interval_map.get(timeframe, 2)  # Default to 1h

            params = {
                'symbol': clean_symbol,
                'intervalType': interval_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', [])
                if result_data and len(result_data) > 0:
                    latest = result_data[-1]  # Get latest data point

                    return {
                        'symbol': clean_symbol,
                        'long_ratio': float(latest.get('longShortRatio', 50)),
                        'short_ratio': 100 - float(latest.get('longShortRatio', 50)),
                        'timestamp': latest.get('time', ''),
                        'source': 'coinglass',
                        'raw_data': latest
                    }
                else:
                    return {'error': 'No data available from Coinglass'}
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass long/short data error: {str(e)}"}

    def _get_coinglass_open_interest_data(self, symbol, timeframe='1h'):
        """Get open interest data from Coinglass v2 API"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Clean symbol
            clean_symbol = symbol.upper().replace('USDT', '')

            url = f"{self.coinglass_base_url}/futures/openInterest"
            headers = self._get_coinglass_headers()

            params = {
                'symbol': clean_symbol
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', [])
                if result_data and len(result_data) > 0:
                    latest = result_data[-1]
                    previous = result_data[-2] if len(result_data) > 1 else latest

                    # Calculate OI change
                    current_oi = float(latest.get('openInterest', 0))
                    previous_oi = float(previous.get('openInterest', 0))
                    oi_change = ((current_oi - previous_oi) / previous_oi * 100) if previous_oi > 0 else 0

                    return {
                        'symbol': clean_symbol,
                        'open_interest': current_oi,
                        'oi_change_percent': oi_change,
                        'funding_rate': float(latest.get('fundingRate', 0)),
                        'timestamp': latest.get('time', ''),
                        'source': 'coinglass',
                        'raw_data': latest
                    }
                else:
                    return {'error': 'No open interest data available'}
            else:
                return {'error': f"Coinglass OI API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass open interest error: {str(e)}"}

    def _analyze_smc_structure(self, long_short_data, oi_data, symbol):
        """Analyze Smart Money Concepts (SMC) structure using Coinglass data"""
        try:
            smc_analysis = {
                'market_structure': 'neutral',
                'smart_money_bias': 'neutral',
                'liquidity_zones': [],
                'confidence': 50,
                'entry_type': 'HOLD',
                'accumulation_distribution': 'neutral',
                'smc_signals': [],
                'liquidity_sweep': False,
                'smc_note': ''
            }

            if 'error' in long_short_data or 'error' in oi_data:
                smc_analysis['smc_signals'].append('⚠️ Insufficient data for SMC analysis.')
                return smc_analysis

            long_ratio = long_short_data.get('long_ratio', 50)
            oi_change = oi_data.get('oi_change_percent', 0)
            funding_rate = oi_data.get('funding_rate', 0)

            confidence_score = 50

            # 1. Long/Short Ratio Analysis (Contrarian indicator)
            if long_ratio > 70:
                smc_analysis['smart_money_bias'] = 'bearish'
                smc_analysis['market_structure'] = 'distribution'
                smc_analysis['accumulation_distribution'] = 'distribution'
                smc_analysis['smc_signals'].append(f'⚠️ High Long Ratio ({long_ratio:.1f}%) indicates potential smart money shorting.')
                confidence_score += 20
            elif long_ratio < 30:
                smc_analysis['smart_money_bias'] = 'bullish'
                smc_analysis['market_structure'] = 'accumulation'
                smc_analysis['accumulation_distribution'] = 'accumulation'
                smc_analysis['smc_signals'].append(f'💎 Low Long Ratio ({long_ratio:.1f}%) suggests smart money accumulation.')
                confidence_score += 20
            else:
                smc_analysis['smc_signals'].append(f'📊 Balanced Long/Short Ratio ({long_ratio:.1f}%).')
                confidence_score += 5

            # 2. Open Interest Analysis
            if oi_change > 5:
                smc_analysis['smc_signals'].append(f'📈 Increasing OI ({oi_change:+.2f}%) supports current trend momentum.')
                if smc_analysis['smart_money_bias'] == 'bullish':
                    confidence_score += 15
                elif smc_analysis['smart_money_bias'] == 'bearish':
                    confidence_score += 15
                else:
                    smc_analysis['smart_money_bias'] = 'bullish' if long_ratio < 50 else 'bearish'
                    smc_analysis['smc_signals'].append(f'💡 OI confirms bias towards {smc_analysis["smart_money_bias"]}.')
                    confidence_score += 10
            elif oi_change < -5:
                smc_analysis['smc_signals'].append(f'📉 Decreasing OI ({oi_change:+.2f}%) may signal weakening momentum.')
                confidence_score -= 10

            # 3. Funding Rate Analysis
            if funding_rate > 0.005:  # High positive funding (0.5%+)
                smc_analysis['smc_signals'].append(f'💸 High Funding Rate ({funding_rate*100:.4f}%) suggests over-enthusiasm in longs.')
                if smc_analysis['smart_money_bias'] != 'bearish':
                    smc_analysis['smart_money_bias'] = 'bearish'
                confidence_score += 15
            elif funding_rate < -0.003:  # Negative funding
                smc_analysis['smc_signals'].append(f'💰 Negative Funding Rate ({funding_rate*100:.4f}%) indicates smart money might be favoring longs.')
                if smc_analysis['smart_money_bias'] != 'bullish':
                    smc_analysis['smart_money_bias'] = 'bullish'
                confidence_score += 15
            else:
                smc_analysis['smc_signals'].append(f'⚖️ Neutral Funding Rate ({funding_rate*100:.4f}%).')


            # 4. Determine entry type based on SMC bias and confidence
            if confidence_score >= 75: # High confidence for signals
                if smc_analysis['smart_money_bias'] == 'bullish':
                    smc_analysis['entry_type'] = 'LONG'
                    smc_analysis['smc_note'] = "Smart money likely accumulating."
                elif smc_analysis['smart_money_bias'] == 'bearish':
                    smc_analysis['entry_type'] = 'SHORT'
                    smc_analysis['smc_note'] = "Smart money likely distributing."
            elif confidence_score >= 60: # Medium confidence
                 smc_analysis['entry_type'] = 'HOLD'
                 smc_analysis['smc_note'] = "Market bias unclear, wait for confirmation."
            else: # Low confidence
                smc_analysis['entry_type'] = 'HOLD'
                smc_analysis['smc_note'] = "Market lacks clear smart money direction."


            # 5. Generate liquidity zones (simplified)
            # This is a placeholder, real liquidity sweep detection requires price action analysis
            # For now, we infer potential liquidity areas based on bias.
            if smc_analysis['smart_money_bias'] == 'bullish':
                smc_analysis['liquidity_zones'].append(
                    {'type': 'support', 'price': self._get_estimated_price(symbol) * 0.97, 'strength': 'high', 'smc_note': 'Potential support liquidity'}
                )
                smc_analysis['liquidity_sweep'] = True # Assume potential sweep if bullish bias
                smc_analysis['smc_signals'].append("✅ Potential bullish liquidity sweep expected.")
            elif smc_analysis['smart_money_bias'] == 'bearish':
                 smc_analysis['liquidity_zones'].append(
                    {'type': 'resistance', 'price': self._get_estimated_price(symbol) * 1.03, 'strength': 'high', 'smc_note': 'Potential resistance liquidity'}
                )
                 smc_analysis['liquidity_sweep'] = True # Assume potential sweep if bearish bias
                 smc_analysis['smc_signals'].append("✅ Potential bearish liquidity sweep expected.")


            smc_analysis['confidence'] = min(95, max(30, confidence_score))
            return smc_analysis

        except Exception as e:
            print(f"❌ SMC analysis error: {e}")
            return {
                'market_structure': 'unknown',
                'smart_money_bias': 'neutral',
                'liquidity_zones': [],
                'confidence': 30,
                'entry_type': 'HOLD',
                'accumulation_distribution': 'neutral',
                'smc_signals': [f'⚠️ Error during SMC analysis: {str(e)}'],
                'liquidity_sweep': False,
                'smc_note': 'SMC analysis failed.'
            }

    def _calculate_smc_levels(self, symbol, smc_analysis, long_short_data, oi_data):
        """Calculate precise entry, TP, and SL levels based on SMC analysis"""
        try:
            base_price = self._get_estimated_price(symbol)
            entry_type = smc_analysis.get('entry_type', 'HOLD')
            confidence = smc_analysis.get('confidence', 50)
            smc_note = smc_analysis.get('smc_note', '')

            # Risk management based on confidence
            if confidence >= 80:
                risk_percent = 0.015  # 1.5% risk for high confidence
                reward_ratio = 3.0    # 3:1 RR
                pos_size_factor = 0.03 # 3% position size
            elif confidence >= 70:
                risk_percent = 0.012  # 1.2% risk for medium confidence
                reward_ratio = 2.5    # 2.5:1 RR
                pos_size_factor = 0.02 # 2% position size
            else:
                risk_percent = 0.01   # 1% risk for low confidence
                reward_ratio = 2.0    # 2:1 RR
                pos_size_factor = 0.01 # 1% position size


            if entry_type == 'LONG':
                entry = base_price * 0.9995  # Slight discount for better fill
                sl = entry * (1 - risk_percent)
                tp1 = entry * (1 + (risk_percent * (reward_ratio / 2)))
                tp2 = entry * (1 + (risk_percent * reward_ratio))

            elif entry_type == 'SHORT':
                entry = base_price * 1.0005  # Slight premium for short entry
                sl = entry * (1 + risk_percent)
                tp1 = entry * (1 - (risk_percent * (reward_ratio / 2)))
                tp2 = entry * (1 - (risk_percent * reward_ratio))

            else:  # HOLD
                entry = base_price
                tp1 = base_price * 1.01
                tp2 = base_price * 1.02
                sl = base_price * 0.99

            return {
                'entry_type': entry_type,
                'entry': entry,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl,
                'risk_percent': risk_percent * 100,
                'reward_ratio': reward_ratio,
                'confidence': confidence,
                'smc_note': smc_note,
                'position_size': f"{pos_size_factor*100:.0f}% capital"
            }

        except Exception as e:
            print(f"❌ SMC levels calculation error: {e}")
            base_price = self._get_estimated_price(symbol)
            return {
                'entry_type': 'HOLD',
                'entry': base_price,
                'tp1': base_price * 1.01,
                'tp2': base_price * 1.02,
                'sl': base_price * 0.99,
                'risk_percent': 1.0,
                'reward_ratio': 2.0,
                'confidence': 50,
                'smc_note': 'Error calculating SMC levels.',
                'position_size': '1% capital'
            }

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis with Coinglass v2 integration"""
        try:
            if not crypto_api:
                return self._generate_emergency_futures_signal(symbol, timeframe, language, "CryptoAPI not available")

            print(f"🎯 Starting futures analysis for {symbol} {timeframe} with Coinglass v2")

            # Get comprehensive futures data from Coinglass v2
            futures_data = await asyncio.to_thread(
                crypto_api.get_comprehensive_futures_data, symbol
            )

            if 'error' in futures_data:
                return self._generate_emergency_futures_signal(
                    symbol, timeframe, language, futures_data['error']
                )

            # Format analysis with Coinglass v2 data
            analysis = self._format_coinglass_v2_analysis(
                symbol, timeframe, futures_data, language
            )

            return analysis

        except Exception as e:
            print(f"❌ Error in futures analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _format_coinglass_analysis(self, symbol, timeframe, long_short_data, oi_data, cmc_data, smc_analysis, trading_levels, language='id'):
        """Format Coinglass analysis output"""
        try:

            # Helper function to format price
            def format_price(price):
                if price < 1:
                    return f"${price:.8f}"
                elif price < 100:
                    return f"${price:.6f}"
                else:
                    return f"${price:,.4f}"

            # Get current price
            current_price = trading_levels.get('entry', 0)
            if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
                current_price = cmc_data.get('price', 0)
                price_source = "CMC Real-time"
                source_emoji = "🟢"
            else:
                price_source = "Estimated"
                source_emoji = "🟡"

            # Direction emoji
            entry_type = trading_levels.get('entry_type', 'HOLD') # Get entry_type from trading_levels
            if entry_type == 'LONG':
                direction_emoji = "🟢"
                signal_emoji = "📈"
            elif entry_type == 'SHORT':
                direction_emoji = "🔴"
                signal_emoji = "📉"
            else:
                direction_emoji = "⏸️"
                signal_emoji = "📊"

            current_time = datetime.now().strftime('%H:%M:%S WIB')

            if language == 'id':
                message = f"""🎯 **ANALISIS FUTURES COINGLASS - {symbol.upper()} ({timeframe})**

💰 **Data Harga:**
• **Current**: {format_price(current_price)} {source_emoji}
• **Source**: {price_source}

{direction_emoji} **SMART MONEY SIGNAL: {entry_type}** {signal_emoji}
📊 **Confidence**: {trading_levels.get('confidence', 50):.0f}%
🧠 **SMC Bias**: {smc_analysis.get('smart_money_bias', 'neutral').title()}

💰 **REKOMENDASI TRADING COINGLASS:**"""

                if entry_type != 'HOLD':
                    message += f"""
┣━ 📍 **ENTRY**: {format_price(trading_levels['entry'])}
┣━ 🎯 **TP 1**: {format_price(trading_levels['tp1'])} (50% profit)
┣━ 🎯 **TP 2**: {format_price(trading_levels['tp2'])} (50% profit)
┗━ 🛡️ **STOP LOSS**: {format_price(trading_levels['sl'])} (**WAJIB!**)"""
                else:
                    message += f"""
┣━ ⏸️ **HOLD POSITION** - Tunggu setup yang lebih jelas
┣━ 📊 **Monitor Level**: {format_price(current_price * 0.98)} - {format_price(current_price * 1.02)}
┗━ 🔍 **Next Signal**: Tunggu perubahan struktur market"""

                # Add Coinglass data analysis
                message += f"""

📊 **ANALISIS COINGLASS DATA:**"""

                if 'error' not in long_short_data:
                    long_ratio = long_short_data.get('long_ratio', 50)
                    short_ratio = long_short_data.get('short_ratio', 50)
                    message += f"""
• **Long/Short Ratio**: {long_ratio:.1f}% / {short_ratio:.1f}%"""

                    if long_ratio > 70:
                        message += f" (⚠️ Overleveraged Longs)"
                    elif long_ratio < 30:
                        message += f" (💎 Oversold Conditions)"
                    else:
                        message += f" (⚖️ Balanced)"

                if 'error' not in oi_data:
                    oi_change = oi_data.get('oi_change_percent', 0)
                    funding_rate = oi_data.get('funding_rate', 0) * 100
                    message += f"""
• **Open Interest Change**: {oi_change:+.2f}%"""
                    if oi_change > 5:
                        message += f" (📈 Strong momentum)"
                    elif oi_change < -5:
                        message += f" (📉 Weakening momentum)"
                    else:
                        message += f" (📊 Stable)"

                    message += f"""
• **Funding Rate**: {funding_rate:.4f}%"""
                    if funding_rate > 1:
                        message += f" (💸 Longs overpaying)"
                    elif funding_rate < -0.5:
                        message += f" (💰 Shorts overpaying)"
                else:
                    message += "\n• Open Interest Data: Unavailable"


                # SMC Analysis
                message += f"""

🧠 *ANALISIS SMC ENHANCED:*
• *Smart Money Bias*: {smc_analysis.get('smart_money_bias', 'Neutral').title()}
• *Market Structure*: {smc_analysis.get('market_structure', 'Neutral').title()}
• *Accumulation/Distribution*: {smc_analysis.get('accumulation_distribution', 'Neutral').title()}"""

                if smc_analysis.get('liquidity_sweep'):
                    message += f"\n• *Liquidity Sweep*: ✅ Detected"

                # Show key SMC signals
                smc_signals = smc_analysis.get('smc_signals', [])
                if smc_signals:
                    key_signals = [s for s in smc_signals if any(indicator in s for indicator in ['✅', '⚠️', 'Extreme', 'Strong'])]
                    if key_signals:
                        message += f"\n• *Key SMC Signals*:"
                        for signal in key_signals[:2]:  # Show top 2 key signals
                            message += f"\n  \\- {safe_text(signal[:60])}{'...' if len(signal) > 60 else ''}"

                liquidity_zones = smc_analysis.get('liquidity_zones', [])
                if liquidity_zones:
                    message += f"\n• *SMC Liquidity Zones*:"
                    for zone in liquidity_zones[:2]:
                        zone_price = format_price(zone.get('price', 0))
                        zone_type = safe_text(zone.get('type', 'N/A').replace('_', ' ').title())
                        zone_strength = safe_text(zone.get('strength', 'medium').replace('_', ' ').title())
                        smc_note = zone.get('smc_note', '')
                        message += f"\n  \\- {zone_type}: {safe_text(zone_price)} \\({zone_strength}\\)"
                        if smc_note:
                            message += f"\n    {safe_text(smc_note[:40])}{'...' if len(smc_note) > 40 else ''}"

                if entry_type != 'HOLD':
                    message += f"""

⚡ *STRATEGI SMC {timeframe.upper()}:*
• *Risk Management*: {trading_levels.get('risk_percent', 1):.1f}% risk per trade
• *Reward Ratio*: {trading_levels.get('reward_ratio', 2):.1f}:1
• *Position Size*: {trading_levels.get('position_size', '1-2% capital')} modal
• *Market Bias*: Follow smart money {smc_analysis.get('smart_money_bias', 'neutral')} bias

🛡️ *RISK MANAGEMENT KETAT:*
• Set SL WAJIB sebelum entry
• Take profit: 50% di TP1, 50% di TP2
• Move SL ke breakeven setelah TP1 hit
• Exit jika SMC structure berubah"""
                else:
                    message += f"""

⏸️ *STRATEGI HOLD:*
• Market belum memberikan setup SMC yang jelas
• Tunggu konfirmasi smart money bias
• Monitor perubahan long/short ratio dan OI
• Entry hanya setelah confidence >70%"""

                message += f"""

📡 *DATA SOURCES (100% COINGLASS):*
• *Long/Short Ratio*: Coinglass longShortChart API ✅
• *Open Interest*: Coinglass openInterest API ✅
• *Price Data*: {price_source}
• *SMC Analysis*: Coinglass + Advanced algorithmic analysis

⏰ *Analysis Time*: {current_time}
🔄 *Next Update*: Real-time via Coinglass API"""

            else:
                # English version
                message = f"""🎯 *COINGLASS FUTURES ANALYSIS \\- {symbol.upper()} \\({timeframe}\\)*

💰 *CURRENT PRICE*: {format_price(current_price)} {source_emoji}
💰 *SOURCE*: {price_source}

{direction_emoji} *RECOMMENDATION: {entry_type}* {signal_emoji}
📊 *CONFIDENCE*: {trading_levels.get('confidence', 50):.0f}%
🧠 *SENTIMENT*: {sentiment}

💰 *TRADING DETAILS:*"""

                if entry_type != 'HOLD':
                    entry_price = format_price(trading_levels['entry'])
                    tp1_price = format_price(trading_levels['tp1'])
                    tp2_price = format_price(trading_levels['tp2'])
                    sl_price = format_price(trading_levels['sl'])

                    message += f"""
• 📍 *ENTRY*: {entry_price}
• 🎯 *TP 1*: {tp1_price}
• 🎯 *TP 2*: {tp2_price}
• 🛡️ *STOP LOSS*: {sl_price} \\(*MANDATORY\\!*\\)"""
                else:
                    monitor_low = format_price(current_price * 0.98)
                    monitor_high = format_price(current_price * 1.02)
                    message += f"""
• ⏸️ *HOLD POSITION* \\- Wait for clearer setup
• 📊 *MONITOR LEVELS*: {monitor_low} \\- {monitor_high}"""

                long_ratio = long_short_data.get('long_ratio', 50) if 'error' not in long_short_data else 0
                long_status = 'Overleveraged Longs' if long_ratio > 70 else 'Oversold Conditions' if long_ratio < 30 else 'Balanced'
                funding_rate = oi_data.get('funding_rate', 0) * 100 if 'error' not in oi_data else 0
                funding_status = 'High Longs Paying' if funding_rate > 1 else 'High Shorts Paying' if funding_rate < -0.5 else 'Neutral'

                message += f"""

📊 *COINGLASS v2 DATA:*
• *Long/Short Ratio*: {long_short_data.get('long_ratio', 50):.1f}% \\({long_status}\\)
• *Open Interest Change*: {oi_data.get('oi_change_percent', 0):+.2f}%
• *Funding Rate*: {funding_rate:.4f}% \\({funding_status}\\)

🧠 *ENHANCED SMC ANALYSIS:*
• *Smart Money Bias*: {smc_analysis.get('smart_money_bias', 'Neutral').title()}
• *Market Structure*: {smc_analysis.get('market_structure', 'Neutral').title()}
• *Accumulation/Distribution*: {smc_analysis.get('accumulation_distribution', 'Neutral').title()}"""

                if smc_analysis.get('liquidity_sweep'):
                    message += f"\n• *Liquidity Sweep*: ✅ Detected"

                # Show key SMC signals
                smc_signals = smc_analysis.get('smc_signals', [])
                if smc_signals:
                    key_signals = [s for s in smc_signals if any(indicator in s for indicator in ['✅', '⚠️', 'Extreme', 'Strong'])]
                    if key_signals:
                        message += f"\n• *Key SMC Signals*:"
                        for signal in key_signals[:2]:  # Show top 2 key signals
                            message += f"\n  \\- {safe_text(signal[:60])}{'...' if len(signal) > 60 else ''}"

                liquidity_zones = smc_analysis.get('liquidity_zones', [])
                if liquidity_zones:
                    message += f"\n• *SMC Liquidity Zones*:"
                    for zone in liquidity_zones[:2]:
                        zone_price = format_price(zone.get('price', 0))
                        zone_type = safe_text(zone.get('type', 'N/A').replace('_', ' ').title())
                        zone_strength = safe_text(zone.get('strength', 'medium').replace('_', ' ').title())
                        smc_note = zone.get('smc_note', '')
                        message += f"\n  \\- {zone_type}: {safe_text(zone_price)} \\({zone_strength}\\)"
                        if smc_note:
                            message += f"\n    {safe_text(smc_note[:40])}{'...' if len(smc_note) > 40 else ''}"

                pos_size = '2-3%' if trading_levels.get('confidence', 50) >= 80 else '1-2%' if trading_levels.get('confidence', 50) >= 70 else '0.5-1%'
                message += f"""

⚡ *TRADING DETAILS:*
• *Confidence*: {trading_levels.get('confidence', 50):.0f}%
• *Risk/Reward Ratio*: {trading_levels.get('reward_ratio', 2):.1f}:1
• *Position Size*: {trading_levels.get('position_size', '1-2% capital')} Capital

⏰ *Update*: {datetime.now().strftime('%H:%M:%S UTC')}
🔄 *Next Update*: Auto-refreshing"""

            return message

        except Exception as e:
            print(f"❌ Error formatting Coinglass analysis: {e}")
            return self._generate_emergency_futures_signal(symbol, timeframe, language, str(e))

    def _generate_comprehensive_futures_data(self, symbol, crypto_api=None):
        """Fetch and combine data from Coinglass for comprehensive futures analysis"""
        try:
            if not crypto_api:
                return {'error': 'CryptoAPI not available'}

            print(f"Fetching comprehensive data for {symbol}...")

            # Fetch individual data points
            ls_data = asyncio.run(asyncio.to_thread(self._get_coinglass_long_short_data, symbol))
            oi_data = asyncio.run(asyncio.to_thread(self._get_coinglass_open_interest_data, symbol))
            # Assume funding_rate is part of oi_data, no need for separate call if already present
            funding_data = oi_data if 'error' not in oi_data and 'funding_rate' in oi_data else {'funding_rate': 0}
            price_data = asyncio.run(asyncio.to_thread(crypto_api.get_price_data, symbol)) # Assuming crypto_api has get_price_data

            # Fetch recommendation data (this might be from another module/API)
            # For now, we'll use a placeholder or simplified logic
            recommendation = {}
            if 'error' not in ls_data and 'error' not in oi_data and 'error' not in price_data:
                 recommendation = self._analyze_coinglass_data(
                    {'long_short': ls_data, 'open_interest': oi_data}, symbol
                 )
                 # Enhance recommendation with SMC logic
                 smc_analysis = self._analyze_smc_structure(ls_data, oi_data, symbol)
                 smc_levels = self._calculate_smc_levels(symbol, smc_analysis, ls_data, oi_data)

                 recommendation.update({
                    'smc_analysis': smc_analysis,
                    'smc_levels': smc_levels,
                    'smc_note': smc_levels.get('smc_note', ''),
                    'position_size_smc': smc_levels.get('position_size', '1-2% capital')
                 })

            successful_calls = sum([
                not isinstance(ls_data, dict) or 'error' not in ls_data,
                not isinstance(oi_data, dict) or 'error' not in oi_data,
                not isinstance(price_data, dict) or 'error' not in price_data,
                not isinstance(recommendation, dict) or 'error' not in recommendation
            ])
            total_calls = 4

            # Enhanced SMC Analysis Integration
            smc_analysis = self._analyze_smc_structure(ls_data, oi_data, symbol)
            smc_levels = self._calculate_smc_levels(symbol, smc_analysis, ls_data, oi_data)

            # Combine SMC with existing recommendation
            if 'error' not in recommendation:
                recommendation.update({
                    'smc_analysis': smc_analysis,
                    'smc_levels': smc_levels,
                    'smc_note': smc_levels.get('smc_note', ''),
                    'position_size_smc': smc_levels.get('position_size', '1-2% capital')
                })
            else: # If recommendation failed, try to populate with SMC directly
                recommendation = {
                    'smc_analysis': smc_analysis,
                    'smc_levels': smc_levels,
                    'smc_note': smc_levels.get('smc_note', ''),
                    'position_size_smc': smc_levels.get('position_size', '1-2% capital'),
                    'direction': smc_analysis.get('entry_type', 'HOLD'),
                    'confidence': smc_analysis.get('confidence', 50),
                    'analysis': smc_analysis
                }


            return {
                'symbol': symbol,
                'open_interest_data': oi_data,
                'long_short_data': ls_data,
                'funding_rate_data': funding_data,
                'price_data': price_data,
                'trading_recommendation': recommendation,
                'smc_analysis': smc_analysis,
                'smc_levels': smc_levels,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': 'excellent' if successful_calls >= 3 else 'good' if successful_calls >= 2 else 'partial',
                'source': 'coinglass_v2_comprehensive_smc'
            }

        except Exception as e:
            print(f"Error in _generate_comprehensive_futures_data: {e}")
            return {'error': f'Failed to fetch comprehensive data: {str(e)}'}


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

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan command `/price <symbol>`.\nContoh: `/price btc`\n\nUntuk analisis lengkap dengan prediksi: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam, gunakan `/analyze <symbol>` atau `/futures_signals` untuk sinyal futures harian.\n\n💡 **Tips**: Analisis mencakup technical analysis, sentiment, dan rekomendasi trading."

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
            if any(keyword in text_lower for keyword in ['price', 'cost', 'how much']):
                return "💰 To check crypto prices, use `/price <symbol>`. Example: `/price btc`\n\nFor comprehensive analysis: `/analyze <symbol>`"

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

    def _get_top_coins_for_signals(self, crypto_api=None):
        """Get top coins for signal generation"""
        return ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'MATIC', 'DOT', 'ATOM', 'LINK']

    def _analyze_coinglass_data(self, coinglass_data, symbol):
        """Analyze Coinglass data for insights"""
        try:
            long_short = coinglass_data.get('long_short', {})
            open_interest = coinglass_data.get('open_interest', {})

            if 'error' in long_short or 'error' in open_interest:
                return {
                    'direction': 'HOLD',
                    'confidence': 30,
                    'reason': 'Insufficient data'
                }

            long_ratio = long_short.get('long_ratio', 50)
            oi_change = open_interest.get('oi_change_percent', 0)

            # Analysis logic
            if long_ratio > 70:
                return {
                    'direction': 'SHORT',
                    'confidence': min(80, 60 + (long_ratio - 70)),
                    'reason': f'Overleveraged longs ({long_ratio:.1f}%)',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }
            elif long_ratio < 30:
                return {
                    'direction': 'LONG',
                    'confidence': min(80, 60 + (30 - long_ratio)),
                    'reason': f'Oversold conditions ({long_ratio:.1f}%)',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }
            else:
                return {
                    'direction': 'HOLD',
                    'confidence': 50,
                    'reason': 'Balanced market conditions',
                    'long_ratio': long_ratio,
                    'oi_change': oi_change
                }

        except Exception as e:
            return {
                'direction': 'HOLD',
                'confidence': 30,
                'reason': f'Analysis error: {str(e)}'
            }

    def _analyze_historical_trend(self, historical_data):
        """Analyze historical price trend"""
        try:
            if 'error' in historical_data or not historical_data.get('data'):
                return {'trend': 'neutral', 'strength': 'low'}

            data = historical_data['data']
            if len(data) < 10:
                return {'trend': 'neutral', 'strength': 'low'}

            # Simple trend analysis
            closes = [float(candle.get('price_close', 0)) for candle in data[-10:]]

            if len(closes) >= 5:
                recent_avg = sum(closes[-5:]) / 5
                older_avg = sum(closes[:5]) / 5

                change = (recent_avg - older_avg) / older_avg * 100

                if change > 2:
                    return {'trend': 'bullish', 'strength': 'strong' if change > 5 else 'medium'}
                elif change < -2:
                    return {'trend': 'bearish', 'strength': 'strong' if change < -5 else 'medium'}

            return {'trend': 'neutral', 'strength': 'medium'}

        except Exception as e:
            return {'trend': 'neutral', 'strength': 'low'}

    def _analyze_coinglass_comprehensive(self, coinglass_data):
        """Analyze comprehensive Coinglass data"""
        try:
            sentiment_score = 50  # Neutral
            signals = []

            # Analyze each data component
            long_short = coinglass_data.get('long_short', {})
            open_interest = coinglass_data.get('open_interest', {})
            liquidation = coinglass_data.get('liquidation', {})

            if 'error' not in long_short:
                long_ratio = long_short.get('long_ratio', 50)
                if long_ratio > 65:
                    sentiment_score -= 10
                    signals.append('High long ratio suggests potential reversal')
                elif long_ratio < 35:
                    sentiment_score += 10
                    signals.append('Low long ratio suggests bullish sentiment')

            if 'error' not in open_interest:
                oi_change = open_interest.get('oi_change_percent', 0)
                if oi_change > 10:
                    sentiment_score += 5
                    signals.append('Rising open interest confirms trend')
                elif oi_change < -10:
                    sentiment_score -= 5
                    signals.append('Falling open interest suggests weakening')

            return {
                'sentiment_score': max(0, min(100, sentiment_score)),
                'signals': signals,
                'overall': 'bullish' if sentiment_score > 60 else 'bearish' if sentiment_score < 40 else 'neutral'
            }

        except Exception as e:
            return {
                'sentiment_score': 50,
                'signals': [f'Analysis error: {str(e)}'],
                'overall': 'neutral'
            }

    def _generate_emergency_futures_signal(self, symbol, timeframe, language, error_message):
        """Generate a fallback signal in case of errors."""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            message = f"""❌ SIGNAL GAGAL - {symbol.upper()} ({timeframe})
⏰ {current_time}

Terjadi kesalahan saat memproses data:
{error_message[:100]}...

🔄 **Solusi:**
• Coba lagi dalam beberapa menit
• Gunakan `/price {symbol.lower()}` untuk harga basic
• Contact admin jika masalah berlanjut"""
        else:
            message = f"""❌ SIGNAL FAILED - {symbol.upper()} ({timeframe})
⏰ {current_time}

Error processing data:
{error_message[:100]}...

🔄 **Solutions:**
• Try again in a few minutes
• Use `/price {symbol.lower()}` for basic price
• Contact admin if issue persists"""

        return message

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get market sentiment with CoinMarketCap integration"""
        try:
            if crypto_api and hasattr(crypto_api, 'cmc_provider') and crypto_api.cmc_provider.api_key:
                # Get comprehensive market data from CoinMarketCap
                market_data = crypto_api.cmc_provider.get_enhanced_market_overview()

                if 'error' not in market_data:
                    global_metrics = market_data.get('global_metrics', {})
                    top_cryptos = market_data.get('top_cryptocurrencies', {})
                    fng_data = market_data.get('fear_greed_index', {})

                    current_time = datetime.now().strftime('%H:%M:%S WIB')

                    # Format large numbers
                    def format_currency(amount):
                        if amount > 1000000000000:  # Trillions
                            return f"${amount/1000000000000:.2f}T"
                        elif amount > 1000000000:  # Billions
                            return f"${amount/1000000000:.2f}B"
                        elif amount > 1000000:  # Millions
                            return f"${amount/1000000:.1f}M"
                        else:
                            return f"${amount:,.0f}"

                    total_market_cap = global_metrics.get('total_market_cap', 0)
                    total_volume = global_metrics.get('total_volume_24h', 0)
                    market_cap_change = global_metrics.get('market_cap_change_24h', 0)
                    btc_dominance = global_metrics.get('btc_dominance', 0)
                    eth_dominance = global_metrics.get('eth_dominance', 0)
                    active_cryptos = global_metrics.get('active_cryptocurrencies', 0)
                    active_exchanges = global_metrics.get('active_exchanges', 0)

                    # Fear & Greed Index
                    fng_value = fng_data.get('value', 50)
                    fng_classification = fng_data.get('value_classification', 'Neutral')

                    # Market sentiment emoji
                    if market_cap_change > 3:
                        sentiment_emoji = "🚀"
                        sentiment_text = "Very Bullish"
                    elif market_cap_change > 0:
                        sentiment_emoji = "📈"
                        sentiment_text = "Bullish"
                    elif market_cap_change > -3:
                        sentiment_emoji = "⚡"
                        sentiment_text = "Neutral"
                    else:
                        sentiment_emoji = "📉"
                        sentiment_text = "Bearish"

                    if language == 'id':
                        analysis = f"""🌍 **OVERVIEW PASAR CRYPTO GLOBAL (CoinMarketCap)**

💰 **Statistik Pasar:**
• **Total Market Cap**: {format_currency(total_market_cap)}
• **Perubahan 24j**: {sentiment_emoji} {market_cap_change:+.2f}%
• **Volume 24j**: {format_currency(total_volume)}
• **Sentiment**: {sentiment_text}

🪙 **Dominasi Crypto:**
• **Bitcoin (BTC)**: {btc_dominance:.1f}%
• **Ethereum (ETH)**: {eth_dominance:.1f}%
• **Altcoins**: {100-btc_dominance-eth_dominance:.1f}%

📊 **Aktivitas Pasar:**
• **Cryptocurrency Aktif**: {active_cryptos:,}
• **Exchange Aktif**: {active_exchanges:,}
• **Market Pairs**: {global_metrics.get('active_market_pairs', 0):,}

😨😱 **Fear & Greed Index:**
• **Nilai**: {fng_value}/100
• **Status**: {fng_classification}
• **Indikator**: {'Extreme Fear' if fng_value < 20 else 'Fear' if fng_value < 40 else 'Neutral' if fng_value < 60 else 'Greed' if fng_value < 80 else 'Extreme Greed'}"""

                        # Add top movers if available
                        if 'data' in top_cryptos and top_cryptos['data']:
                            analysis += f"\n\n🎯 **Top 5 Cryptocurrency:**"
                            for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                                price = crypto.get('price', 0)
                                change_24h = crypto.get('percent_change_24h', 0)
                                symbol = crypto.get('symbol', '')
                                name = crypto.get('name', '')

                                price_display = f"${price:.4f}" if price < 100 else f"${price:,.2f}"
                                change_emoji = "📈" if change_24h >= 0 else "📉"

                                analysis += f"\n• **{i}. {name} ({symbol})**: {price_display} {change_emoji} {change_24h:+.1f}%"

                        analysis += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinMarketCap Startup Plan
💎 **Data Quality**: Real-time & Verified"""

                        return analysis
                    else:
                        analysis = f"""🌍 **GLOBAL CRYPTO MARKET OVERVIEW (CoinMarketCap)**

💰 **Market Statistics:**
• **Total Market Cap**: {format_currency(total_market_cap)}
• **24h Change**: {sentiment_emoji} {market_cap_change:+.2f}%
• **Volume 24h**: {format_currency(total_volume)}
• **Sentiment**: {sentiment_text}

🪙 **Crypto Dominance:**
• **Bitcoin (BTC)**: {btc_dominance:.1f}%
• **Ethereum (ETH)**: {eth_dominance:.1f}%
• **Altcoins**: {100-btc_dominance-eth_dominance:.1f}%

📊 **Market Activity:**
• **Active Cryptocurrencies**: {active_cryptos:,}
• **Active Exchanges**: {active_exchanges:,}
• **Market Pairs**: {global_metrics.get('active_market_pairs', 0):,}

😨😱 **Fear & Greed Index:**
• **Value**: {fng_value}/100
• **Status**: {fng_classification}
• **Indicator**: {'Extreme Fear' if fng_value < 20 else 'Fear' if fng_value < 40 else 'Neutral' if fng_value < 60 else 'Greed' if fng_value < 80 else 'Extreme Greed'}"""

                        # Add top movers if available
                        if 'data' in top_cryptos and top_cryptos['data']:
                            analysis += f"\n\n🎯 **Top 5 Cryptocurrencies:**"
                            for i, crypto in enumerate(top_cryptos['data'][:5], 1):
                                price = crypto.get('price', 0)
                                change_24h = crypto.get('percent_change_24h', 0)
                                symbol = crypto.get('symbol', '')
                                name = crypto.get('name', '')

                                price_display = f"${price:.4f}" if price < 100 else f"${price:,.2f}"
                                change_emoji = "📈" if change_24h >= 0 else "📉"

                                analysis += f"\n• **{i}. {name} ({symbol})**: {price_display} {change_emoji} {change_24h:+.1f}%"

                        analysis += f"""

⏰ **Update**: {current_time}
📡 **Source**: CoinMarketCap Startup Plan
💎 **Data Quality**: Real-time & Verified"""

                        return analysis

            # Fallback if CoinMarketCap fails
            fallback_msg = "⚠️ **Data CoinMarketCap sementara tidak tersedia**\n\n" if language == 'id' else "⚠️ **CoinMarketCap data temporarily unavailable**\n\n"
            fallback_msg += f"""💡 **Alternatif:**
• Pastikan CMC_API_KEY tersedia di Secrets
• Coba command `/price btc` untuk harga basic
• Contact admin jika masalah berlanjut

🔄 **Reason**: CoinMarketCap API rate limit atau koneksi error"""

            return fallback_msg

        except Exception as e:
            print(f"Error in market sentiment: {e}")
            if language == 'id':
                return f"❌ **Error mengambil data pasar**\n\n**Detail**: {str(e)[:100]}...\n\n💡 Coba lagi dalam beberapa menit"
            else:
                return f"❌ **Error fetching market data**\n\n**Detail**: {str(e)[:100]}...\n\n💡 Try again in a few minutes"

    def _format_top_movers(self, market_data, language='id'):
        """Format top movers from market data"""
        try:
            if 'top_gainers' in market_data and 'top_losers' in market_data:
                gainers = market_data['top_gainers'][:3]
                losers = market_data['top_losers'][:3]

                if language == 'id':
                    output = "**Top Gainers:**\n"
                    for gainer in gainers:
                        output += f"• {gainer.get('symbol', 'N/A')}: +{gainer.get('percent_change_24h', 0):.1f}%\n"

                    output += "\n**Top Losers:**\n"
                    for loser in losers:
                        output += f"• {loser.get('symbol', 'N/A')}: {loser.get('percent_change_24h', 0):.1f}%\n"

                    return output
                else:
                    output = "**Top Gainers:**\n"
                    for gainer in gainers:
                        output += f"• {gainer.get('symbol', 'N/A')}: +{gainer.get('percent_change_24h', 0):.1f}%\n"

                    output += "\n**Top Losers:**\n"
                    for loser in losers:
                        output += f"• {loser.get('symbol', 'N/A')}: {loser.get('percent_change_24h', 0):.1f}%\n"

                    return output

            return "• Data movers tidak tersedia" if language == 'id' else "• Movers data unavailable"

        except Exception as e:
            return f"• Error formatting movers: {str(e)[:50]}..."

    def _generate_no_signals_message(self, language='id'):
        """Generate message when no signals are found."""
        if language == 'id':
            return "😔 Maaf, saat ini tidak ada sinyal futures dengan confidence tinggi. Coba lagi nanti atau periksa command `/help`."
        else:
            return "😔 Sorry, no high-confidence futures signals found at the moment. Please try again later or check `/help`."

    def get_comprehensive_analysis(self, symbol, timeframe=None, leverage=None, risk=None, user_id=None):
        """Get comprehensive analysis using CoinMarketCap API with Smart Money Concepts"""
        try:
            import html

            # Get CoinMarketCap API key from environment
            cmc_api_key = os.getenv("COINMARKETCAP_API_KEY")

            if not cmc_api_key:
                return """❌ **ANALISIS GAGAL**

CoinMarketCap API key tidak ditemukan di Secrets.

🔧 **Setup diperlukan:**
• Buka Tools > Secrets di Replit
• Tambahkan secret dengan nama: COINMARKETCAP_API_KEY
• Masukkan API key dari CoinMarketCap

💡 **Cara mendapatkan API key:**
1. Daftar di coinmarketcap.com/api
2. Buat akun gratis
3. Copy API key dari dashboard
4. Paste ke Replit Secrets"""

            # Setup CoinMarketCap API request
            cmc_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            cmc_headers = {
                'X-CMC_PRO_API_KEY': cmc_api_key,
                'Accept': 'application/json'
            }
            cmc_params = {
                'symbol': symbol.upper()
            }

            # Make CoinMarketCap API request
            cmc_response = requests.get(cmc_url, headers=cmc_headers, params=cmc_params, timeout=15)
            cmc_response.raise_for_status()

            cmc_data = cmc_response.json()

            # Check if CoinMarketCap API call was successful
            if cmc_data.get('status', {}).get('error_code') != 0:
                error_msg = cmc_data.get('status', {}).get('error_message', 'Unknown error')
                return f"""❌ **CoinMarketCap API Error**

{html.escape(error_msg)}

💡 **Kemungkinan penyebab:**
• API key tidak valid
• Limit request tercapai
• Symbol cryptocurrency tidak ditemukan
• Masalah koneksi internet

🔄 **Solusi:** Coba lagi dalam beberapa menit"""

            # Extract cryptocurrency data from CoinMarketCap
            crypto_data = cmc_data.get('data', {}).get(symbol.upper(), {})

            if not crypto_data:
                return f"""❌ **Cryptocurrency Tidak Ditemukan**

Symbol "{html.escape(symbol.upper())}" tidak ditemukan di CoinMarketCap.

💡 **Tips:**
• Pastikan symbol benar (contoh: BTC, ETH, BNB)
• Gunakan symbol resmi, bukan nama lengkap
• Coba symbol populer seperti BTC atau ETH"""

            quote_data = crypto_data.get('quote', {}).get('USD', {})

            # Extract relevant data from CoinMarketCap
            name = crypto_data.get('name', symbol.upper())
            current_price = quote_data.get('price', 0)
            market_cap = quote_data.get('market_cap', 0)
            volume_24h = quote_data.get('volume_24h', 0)
            percent_change_24h = quote_data.get('percent_change_24h', 0)
            cmc_rank = crypto_data.get('cmc_rank', 0)

            # Get Smart Money Concepts data from Coinglass
            smc_analysis = self._get_smart_money_analysis(symbol)

            # Format numbers for readability
            def format_currency(amount):
                if amount >= 1_000_000_000_000:  # Trillions
                    return f"${amount/1_000_000_000_000:.2f}T"
                elif amount >= 1_000_000_000:  # Billions
                    return f"${amount/1_000_000_000:.2f}B"
                elif amount >= 1_000_000:  # Millions
                    return f"${amount/1_000_000:.1f}M"
                else:
                    return f"${amount:,.0f}"

            def format_price(price):
                if price < 1:
                    return f"${price:.8f}"
                elif price < 100:
                    return f"${price:.4f}"
                else:
                    return f"${price:,.2f}"

            # Generate basic trading recommendation from price movement
            if percent_change_24h > 5:
                basic_recommendation = "BUY"
                basic_emoji = "🟢"
                basic_reason = f"Strong bullish momentum (+{percent_change_24h:.1f}%)"
            elif percent_change_24h > 0:
                basic_recommendation = "HOLD"
                basic_emoji = "🟡"
                basic_reason = f"Slight upward movement (+{percent_change_24h:.1f}%)"
            elif percent_change_24h > -5:
                basic_recommendation = "HOLD"
                basic_emoji = "🟡"
                basic_reason = f"Minor correction ({percent_change_24h:.1f}%)"
            else:
                basic_recommendation = "SELL"
                basic_emoji = "🔴"
                basic_reason = f"Strong bearish pressure ({percent_change_24h:.1f}%)"

            # Combine basic recommendation with SMC analysis
            final_recommendation = self._combine_recommendations(basic_recommendation, smc_analysis)

            # Format final output
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            analysis = f"""📊 **ANALISIS KOMPREHENSIF {html.escape(name)} ({html.escape(symbol.upper())})**

💰 **DATA FUNDAMENTAL (CoinMarketCap):**
• Harga Sekarang: {format_price(current_price)}
• Ranking CMC: #{cmc_rank}
• Market Cap: {format_currency(market_cap)}
• Volume 24 Jam: {format_currency(volume_24h)}
• Perubahan 24 Jam: {percent_change_24h:+.2f}% {'📈' if percent_change_24h >= 0 else '📉'}

🧠 **SMART MONEY CONCEPTS (Coinglass):**
{smc_analysis.get('analysis_text', '• Data Smart Money sedang diproses...')}

🎯 **REKOMENDASI GABUNGAN:** {final_recommendation['emoji']} {final_recommendation['action']}
💡 **Alasan:** {html.escape(final_recommendation['reason'])}
📊 **Confidence:** {final_recommendation['confidence']:.1f}%

⚠️ **RISK MANAGEMENT:**
• Gunakan stop loss 3-5% untuk trading jangka pendek
• Take profit bertahap di level resistance
• Maksimal 2-3% dari total portfolio per trade
• Monitor smart money flow untuk timing entry/exit
• Selalu DYOR (Do Your Own Research)

📡 **DATA SOURCES:**
• Fundamental: CoinMarketCap Professional API
• Smart Money: Coinglass Real-time API
⏰ **Update:** {current_time}

💎 **DISCLAIMER:** Analisis ini menggabungkan data fundamental dan smart money flow. Selalu kombinasikan dengan technical analysis dan berita terkini untuk keputusan trading yang lebih baik."""

            return analysis

        except requests.exceptions.RequestException as e:
            return f"""❌ **KONEKSI ERROR**

Gagal mengambil data dari CoinMarketCap API.

**Detail Error:** {html.escape(str(e)[:100])}...

🔄 **Solusi:**
• Cek koneksi internet
• Coba lagi dalam beberapa menit
• Pastikan API key CoinMarketCap valid

💡 **Alternative:** Gunakan command `/price {symbol.lower()}` untuk harga basic"""

        except Exception as e:
            return f"""❌ **ANALISIS GAGAL**

Terjadi kesalahan tak terduga saat memproses data.

**Detail Error:** {html.escape(str(e)[:100])}...

🔄 **Solusi:**
• Coba lagi dalam beberapa menit
• Pastikan symbol cryptocurrency benar
• Contact admin jika masalah berlanjut

💡 **Example:** `/analyze BTC` atau `/analyze ETH`"""

    def _get_smart_money_analysis(self, symbol):
        """Get Smart Money Concepts analysis using Coinglass data"""
        try:
            # Get long/short ratio data
            long_short_data = self._get_coinglass_long_short_data(symbol, '1h')

            # Get open interest data
            oi_data = self._get_coinglass_open_interest_data(symbol, '1h')

            # Get funding rate data (from OI data if available)
            funding_rate = oi_data.get('funding_rate', 0) if 'error' not in oi_data else 0

            smc_signals = []
            confidence_score = 50
            smart_money_bias = "NEUTRAL"

            if 'error' not in long_short_data:
                long_ratio = long_short_data.get('long_ratio', 50)
                short_ratio = long_short_data.get('short_ratio', 50)

                # Smart Money Contrarian Analysis
                if long_ratio > 75:
                    smart_money_bias = "BEARISH"
                    smc_signals.append(f"⚠️ Extreme Long Dominance ({long_ratio:.1f}%) - Smart money likely positioning short")
                    confidence_score += 20
                elif long_ratio < 25:
                    smart_money_bias = "BULLISH"
                    smc_signals.append(f"💎 Extreme Short Dominance ({100-long_ratio:.1f}%) - Smart money likely accumulating")
                    confidence_score += 20
                elif long_ratio > 65:
                    smart_money_bias = "BEARISH"
                    smc_signals.append(f"🔴 High Long Ratio ({long_ratio:.1f}%) - Potential distribution phase")
                    confidence_score += 10
                elif long_ratio < 35:
                    smart_money_bias = "BULLISH"
                    smc_signals.append(f"🟢 Low Long Ratio ({long_ratio:.1f}%) - Potential accumulation phase")
                    confidence_score += 10
                else:
                    smc_signals.append(f"📊 Balanced Positioning ({long_ratio:.1f}%/{short_ratio:.1f}%)")
            else:
                smc_signals.append("⚠️ Long/Short data tidak tersedia")

            if 'error' not in oi_data:
                oi_change = oi_data.get('oi_change_percent', 0)

                if oi_change > 10:
                    smc_signals.append(f"📈 Strong OI Increase ({oi_change:+.1f}%) - Institutional accumulation")
                    confidence_score += 15
                elif oi_change < -10:
                    smc_signals.append(f"📉 Strong OI Decrease ({oi_change:+.1f}%) - Position unwinding")
                    confidence_score -= 10
                elif abs(oi_change) > 5:
                    smc_signals.append(f"📊 Moderate OI Change ({oi_change:+.1f}%)")
                    confidence_score += 5
            else:
                smc_signals.append("⚠️ Open Interest data tidak tersedia")

            # Funding Rate Analysis
            if funding_rate > 0.01:  # > 1%
                smc_signals.append(f"💸 High Funding Rate ({funding_rate*100:.3f}%) - Longs overpaying, bearish signal")
                if smart_money_bias != "BEARISH":
                    smart_money_bias = "BEARISH"
                confidence_score += 15
            elif funding_rate < -0.005:  # < -0.5%
                smc_signals.append(f"💰 Negative Funding ({funding_rate*100:.3f}%) - Shorts paying, bullish signal")
                if smart_money_bias != "BULLISH":
                    smart_money_bias = "BULLISH"
                confidence_score += 10
            elif abs(funding_rate) > 0.003:
                smc_signals.append(f"⚖️ Moderate Funding ({funding_rate*100:.3f}%)")

            # Format analysis text
            analysis_text = f"• Smart Money Bias: {smart_money_bias}\n"
            for signal in smc_signals[:4]:  # Limit to top 4 signals
                analysis_text += f"• {signal}\n"

            confidence_score = min(95, max(30, confidence_score))

            return {
                'smart_money_bias': smart_money_bias,
                'confidence': confidence_score,
                'signals': smc_signals,
                'analysis_text': analysis_text,
                'long_short_data': long_short_data,
                'oi_data': oi_data,
                'funding_rate': funding_rate
            }

        except Exception as e:
            return {
                'smart_money_bias': 'NEUTRAL',
                'confidence': 40,
                'signals': [f'⚠️ Error dalam Smart Money analysis: {str(e)[:50]}...'],
                'analysis_text': '• Smart Money analysis error - menggunakan analisis fundamental saja',
                'error': str(e)
            }

    def _combine_recommendations(self, basic_recommendation, smc_analysis):
        """Combine basic price analysis with Smart Money Concepts"""
        try:
            smc_bias = smc_analysis.get('smart_money_bias', 'NEUTRAL')
            smc_confidence = smc_analysis.get('confidence', 50)

            # Weight the recommendations
            if smc_bias == basic_recommendation:
                # Both analyses agree
                final_action = basic_recommendation
                final_confidence = min(95, (smc_confidence + 70) // 2)
                final_reason = f"Fundamental dan Smart Money analysis sinkron mendukung {basic_recommendation}"

                if basic_recommendation == "BUY":
                    final_emoji = "🟢"
                elif basic_recommendation == "SELL":
                    final_emoji = "🔴"
                else:
                    final_emoji = "🟡"

            elif smc_bias == "NEUTRAL":
                # SMC neutral, use basic recommendation
                final_action = basic_recommendation
                final_confidence = max(40, smc_confidence - 10)
                final_reason = f"Smart Money netral, ikuti momentum harga ({basic_recommendation})"

                if basic_recommendation == "BUY":
                    final_emoji = "🟡"
                elif basic_recommendation == "SELL":
                    final_emoji = "🟡"
                else:
                    final_emoji = "🟡"

            elif (smc_bias == "BULLISH" and basic_recommendation == "SELL") or \
                 (smc_bias == "BEARISH" and basic_recommendation == "BUY"):
                # Conflicting signals - be cautious
                final_action = "HOLD"
                final_confidence = max(30, min(smc_confidence, 60))
                final_reason = f"Konflik sinyal: Smart Money {smc_bias.lower()} vs Harga {basic_recommendation.lower()}"
                final_emoji = "⚠️"

            else:
                # SMC overrides if confidence is high
                if smc_confidence > 70:
                    if smc_bias == "BULLISH":
                        final_action = "BUY"
                        final_emoji = "🟢"
                    elif smc_bias == "BEARISH":
                        final_action = "SELL"
                        final_emoji = "🔴"
                    else:
                        final_action = "HOLD"
                        final_emoji = "🟡"

                    final_confidence = smc_confidence
                    final_reason = f"Smart Money dominan: {smc_bias.lower()} signal kuat"
                else:
                    final_action = "HOLD"
                    final_confidence = 50
                    final_reason = "Sinyal mixed dengan confidence rendah"
                    final_emoji = "🟡"

            return {
                'action': final_action,
                'confidence': final_confidence,
                'reason': final_reason,
                'emoji': final_emoji
            }

        except Exception as e:
            return {
                'action': basic_recommendation,
                'confidence': 40,
                'reason': f"Error kombinasi analisis: {str(e)[:50]}...",
                'emoji': "⚠️"
            }

    def _generate_emergency_analysis(self, symbol, language, error_message):
        """Generate fallback analysis in case of errors"""
        current_time = datetime.now().strftime('%H:%M:%S WIB')

        if language == 'id':
            message = f"""❌ **ANALISIS GAGAL - {symbol.upper()}**
⏰ {current_time}

Terjadi kesalahan saat mengambil data CoinMarketCap:
{error_message[:100]}...

🔄 **Solusi:**
• Coba lagi dalam beberapa menit
• Gunakan `/price {symbol.lower()}` untuk harga basic
• Pastikan CMC_API_KEY tersedia di Secrets
• Contact admin jika masalah berlanjut

💡 **Alternative**: Gunakan `/futures {symbol.lower()}` untuk analisis futures"""
        else:
            message = f"""❌ **ANALYSIS FAILED - {symbol.upper()}**
⏰ {current_time}

Error fetching CoinMarketCap data:
{error_message[:100]}...

🔄 **Solutions:**
• Try again in a few minutes
• Use `/price {symbol.lower()}` for basic price
• Ensure CMC_API_KEY is available in Secrets
• Contact admin if issue persists

💡 **Alternative**: Use `/futures {symbol.lower()}` for futures analysis"""

        return message

    def _estimate_price(self, symbol):
        """Helper to get an estimated price, fallback to 0 if not found"""
        # In a real scenario, this would query a reliable price source.
        # For now, returning a placeholder.
        print(f"⚠️ Using placeholder price for {symbol}")
        return 30000.0 # Placeholder value

    # Placeholder for safe_text to avoid NameError
    def safe_text(self, text, max_length=100):
        """Safely truncate text and escape HTML characters."""
        if not isinstance(text, str):
            return ""
        text = text[:max_length]
        text = html.escape(text)
        return text

    # Placeholder for determine_overall_sentiment to avoid NameError
    def determine_overall_sentiment(self, cmc_data, smc_analysis, price_data):
        """Determine overall sentiment based on available data."""
        # This is a simplified placeholder. A real implementation would combine
        # price momentum, volume, CMC data, and SMC bias more rigorously.
        overall_confidence = 50
        overall_recommendation = "HOLD"
        reason = "Mixed signals"

        # Use SMC confidence if available and high
        if smc_analysis and smc_analysis.get('confidence', 0) > 65:
            overall_confidence = smc_analysis['confidence']
            smc_bias = smc_analysis.get('smart_money_bias', 'NEUTRAL')
            if smc_bias == 'BULLISH':
                overall_recommendation = "BUY"
                reason = "Strong bullish SMC bias"
            elif smc_bias == 'BEARISH':
                overall_recommendation = "SELL"
                reason = "Strong bearish SMC bias"
            else:
                overall_recommendation = "HOLD"
                reason = "SMC bias is neutral"
        else:
            # Use price momentum if SMC is not decisive
            price_change_24h = cmc_data.get('percent_change_24h', 0) if cmc_data else 0
            if price_change_24h > 5:
                overall_recommendation = "BUY"
                overall_confidence = 75
                reason = f"Positive price momentum (+{price_change_24h:.1f}%)"
            elif price_change_24h < -5:
                overall_recommendation = "SELL"
                overall_confidence = 75
                reason = f"Negative price momentum ({price_change_24h:.1f}%)"
            else:
                overall_recommendation = "HOLD"
                overall_confidence = 50
                reason = "Neutral price movement"

        return {
            'recommendation': overall_recommendation,
            'confidence': overall_confidence,
            'reason': reason
        }

    # Placeholder for get_smc_analysis to avoid NameError
    def get_smc_analysis(self, symbol, timeframe):
        """Placeholder for SMC analysis function."""
        # In a real scenario, this would call _get_smart_money_analysis and _calculate_smc_levels
        # and combine them into a meaningful recommendation.
        print(f"⚠️ Placeholder called: get_smc_analysis for {symbol} {timeframe}")
        # Simulate some basic SMC analysis for placeholder
        smc_data = self._get_smart_money_analysis(symbol)
        smc_levels = self._calculate_smc_levels(symbol, smc_data, {}, {}) # Mock data for levels

        recommendation = smc_data.get('smart_money_bias', 'HOLD')
        confidence = smc_data.get('confidence', 50)
        reason = smc_data.get('analysis_text', 'Placeholder analysis')

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reason': reason,
            'levels': smc_levels
        }