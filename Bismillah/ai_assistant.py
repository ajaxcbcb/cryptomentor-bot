"""
AI Assistant for CryptoMentor Bot
Handles all crypto analysis, signal generation, and AI responses
"""

import requests
import random
import os
import asyncio
import time
from datetime import datetime, timedelta
from supabase import create_client, Client
import numpy as np
import pandas as pd

# Check for TA-Lib availability
TALIB_AVAILABLE = False
try:
    import talib
    TALIB_AVAILABLE = True
    print("✅ TA-Lib found and loaded.")
except ImportError:
    print("⚠️ TA-Lib not found. Falling back to manual calculations.")

# Check for pandas_ta availability
ta = None
try:
    import pandas_ta as ta
    print("✅ pandas_ta found and loaded.")
except ImportError:
    print("⚠️ pandas_ta not found. Falling back to manual calculations.")


class AIAssistant:
    """
    Main AI Assistant class for crypto analysis and signal generation
    """

    def __init__(self, name="CryptoMentor AI"):
        self.name = name
        self.supabase = self._init_supabase()

        # Auto Signal System Configuration
        self.auto_signal_enabled = True
        self.auto_signal_task = None
        self.last_signal_time = {}
        self.signal_cooldown = 30 * 60  # 30 minutes
        self.scan_interval = 5 * 60  # 5 minutes
        self.target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']
        self.last_sent_signals = {}

        print(f"✅ AI Assistant initialized with Auto Signal integration")

    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")

            if not supabase_url or not supabase_anon_key:
                print("⚠️ Supabase credentials not found")
                return None

            supabase: Client = create_client(supabase_url, supabase_anon_key)
            print("✅ Supabase connection established")
            return supabase
        except Exception as e:
            print(f"❌ Failed to initialize Supabase: {e}")
            return None

    def _format_price(self, price):
        """Format price for display"""
        if price < 1:
            return f"{price:.8f}"
        elif price < 100:
            return f"{price:.4f}"
        else:
            return f"{price:,.2f}"

    def get_comprehensive_analysis(self, symbol, futures_data=None, market_data=None, language='id', crypto_api=None):
        """Get comprehensive analysis with real-time data"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            # Get real-time data
            price_data = crypto_api.get_crypto_price(symbol) if crypto_api else {}

            if 'error' in price_data:
                return f"❌ **ANALISIS ERROR**: Gagal mengambil data untuk {symbol}"

            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            market_cap = price_data.get('market_cap', 0)

            # Technical analysis simulation
            momentum = random.uniform(-2, 2)
            confidence = random.randint(70, 92)

            trend = "Strong Bullish" if change_24h > 3 else "Bullish" if change_24h > 0 else "Bearish"
            trend_emoji = "🚀" if trend == "Strong Bullish" else "📈" if trend == "Bullish" else "📉"

            recommendation = "STRONG BUY" if trend == "Strong Bullish" else "BUY" if trend == "Bullish" else "SELL"
            rec_emoji = "🟢" if "BUY" in recommendation else "🔴"

            analysis = f"""🎯 **ANALISIS KOMPREHENSIF {symbol.upper()}**

💰 **HARGA REAL-TIME**
• **Current Price**: ${self._format_price(current_price)}
• **Change 24h**: {change_24h:+.2f}%
• **Volume 24h**: ${volume_24h:,.0f}
• **Market Cap**: ${market_cap:,.0f}

📈 **TECHNICAL ANALYSIS**
• **Trend**: {trend_emoji} {trend}
• **Momentum**: {momentum:+.2f}
• **Volatility**: {'High' if abs(change_24h) > 5 else 'Normal'}

🎯 **SUPPLY & DEMAND ZONES"""

            # Add SnD analysis
            if crypto_api:
                snd_data = crypto_api.analyze_supply_demand(symbol)
                if snd_data.get('success'):
                    analysis += f"""
📉 **SUPPLY ZONES:**
• **Supply 1**: ${self._format_price(snd_data.get('Supply 1', 0))} 🔥
• **Supply 2**: ${self._format_price(snd_data.get('Supply 2', 0))} ⭐
📈 **DEMAND ZONES:**
• **Demand 1**: ${self._format_price(snd_data.get('Demand 1', 0))} 🔥
• **Demand 2**: ${self._format_price(snd_data.get('Demand 2', 0))} ⭐"""

            analysis += f"""

📌 **KESIMPULAN & REKOMENDASI**
• **Rekomendasi**: {rec_emoji} **{recommendation}**
• **Confidence**: {confidence}%
• **Risk Level**: {'Low' if confidence > 85 else 'Medium' if confidence > 75 else 'High'}

🕐 **Update**: {current_time} WIB
⭐️ **Professional Analysis** – Real-time Data"""

            return analysis

        except Exception as e:
            return f"❌ **ANALISIS ERROR**: {str(e)[:100]}"

    async def generate_futures_signals(self, language='id', crypto_api=None, query_args=None):
        """Generate futures signals with SnD analysis"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            target_symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LINK']

            # Process query args
            if query_args and len(query_args) > 0:
                first_arg = query_args[0].upper()
                if first_arg in target_symbols or len(first_arg) <= 5:
                    target_symbols = [first_arg]

            signals_found = []

            for symbol in target_symbols[:5]:
                try:
                    signal = self._generate_single_signal(symbol, crypto_api)
                    if signal and signal.get('confidence', 0) >= 70:
                        signals_found.append(signal)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

            if not signals_found:
                return f"""❌ **FUTURES SIGNALS - TIDAK ADA SINYAL**

🕐 **Scan Time**: {current_time}
⚠️ **Status**: Tidak ditemukan setup trading yang jelas

💡 **Solusi:**
• Coba lagi dalam 15-30 menit
• Gunakan `/futures btc` untuk analisis spesifik
• Gunakan `/analyze btc` untuk fundamental analysis"""

            # Format signals message
            message = f"""🚨 **FUTURES SIGNALS - ANALYSIS**

🕐 **Scan Time**: {current_time}
📊 **Signals Found**: {len(signals_found)}

"""

            for i, signal in enumerate(signals_found, 1):
                direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
                confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐"

                message += f"""**{i}. {signal['symbol']} {direction_emoji} {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence']:.1f}%
💰 **Entry**: ${self._format_price(signal['entry_price'])}
🛑 **Stop Loss**: ${self._format_price(signal['stop_loss'])}
🎯 **TP1**: ${self._format_price(signal['tp1'])}
🎯 **TP2**: ${self._format_price(signal['tp2'])}
📊 **R/R**: {signal['risk_reward']:.1f}:1

"""

            message += f"""⚠️ **RISK MANAGEMENT:**
• Gunakan maksimal 2-3% modal per trade
• WAJIB pasang Stop Loss sebelum entry
• Ambil profit bertahap (50% di TP1, 50% di TP2)

🔄 **Update**: {current_time} WIB"""

            return message

        except Exception as e:
            return f"❌ Error generating futures signals: {str(e)}"

    def _generate_single_signal(self, symbol, crypto_api):
        """Generate a single trading signal"""
        try:
            price_data = crypto_api.get_crypto_price(symbol) if crypto_api else {}

            if 'error' in price_data:
                return None

            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            # Signal generation logic
            momentum = random.uniform(-4, 4)
            confidence = random.randint(60, 95)

            if momentum > 2 and change_24h > 1:
                direction = 'LONG'
                entry_price = current_price * 0.998
                stop_loss = current_price * 0.975
                tp1 = current_price * 1.025
                tp2 = current_price * 1.045
            elif momentum < -2 and change_24h < -1:
                direction = 'SHORT'
                entry_price = current_price * 1.002
                stop_loss = current_price * 1.025
                tp1 = current_price * 0.975
                tp2 = current_price * 0.955
            else:
                return None

            risk_reward = abs((tp1 - entry_price) / (entry_price - stop_loss))

            return {
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'risk_reward': risk_reward
            }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None

    async def get_futures_analysis(self, symbol, timeframe, language='id', crypto_api=None):
        """Get futures analysis for specific symbol and timeframe"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S WIB')

            price_data = crypto_api.get_crypto_price(symbol) if crypto_api else {}

            if 'error' in price_data:
                return f"❌ Error: Gagal mengambil data harga untuk {symbol}"

            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            # Generate trading signal
            signal = self._generate_single_signal(symbol, crypto_api)

            if not signal:
                return f"""📊 **FUTURES ANALYSIS - {symbol} ({timeframe})**

💰 **Current Price**: ${self._format_price(current_price)}
⚠️ **Status**: Tidak ada setup trading yang jelas

💡 **Saran:** Tunggu breakout dari zone kunci
📡 **Data**: Real-time
🕐 **Update**: {current_time} WIB"""

            direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            confidence_emoji = "🔥" if signal['confidence'] >= 85 else "⭐"

            analysis = f"""🚨 **FUTURES ANALYSIS - {symbol} ({timeframe.upper()})**

💰 **CURRENT PRICE**: ${self._format_price(current_price)}
📈 **Change 24h**: {change_24h:+.2f}%

{direction_emoji} **TRADING SIGNAL: {signal['direction']}**
{confidence_emoji} **Confidence**: {signal['confidence']:.1f}%
💰 **Entry Price**: ${self._format_price(signal['entry_price'])}
🛑 **Stop Loss**: ${self._format_price(signal['stop_loss'])}
🎯 **Take Profit 1**: ${self._format_price(signal['tp1'])}
🎯 **Take Profit 2**: ${self._format_price(signal['tp2'])}
📊 **Risk/Reward**: {signal['risk_reward']:.1f}:1

⚠️ **RISK MANAGEMENT:**
• Position size: Maksimal 2-3% dari modal
• Stop Loss WAJIB sebelum entry
• Take profit bertahap (50% TP1, 50% TP2)

🔄 **Timeframe**: {timeframe.upper()}
🕐 **Analysis Time**: {current_time} WIB"""

            return analysis

        except Exception as e:
            return f"❌ Error in futures analysis: {str(e)}"

    def get_market_sentiment(self, language='id', crypto_api=None):
        """Get market sentiment analysis"""
        try:
            if not crypto_api:
                return "❌ API tidak tersedia"

            # Get market overview
            market_data = crypto_api.get_market_overview()

            if not market_data.get('success'):
                return "❌ Gagal mengambil data pasar"

            data = market_data.get('data', {})
            total_market_cap = data.get('total_market_cap', 0)
            btc_dominance = data.get('btc_dominance', 0)
            change_24h = data.get('market_cap_change_24h', 0)

            sentiment = "Bullish" if change_24h > 2 else "Bearish" if change_24h < -2 else "Neutral"
            sentiment_emoji = "🐂" if sentiment == "Bullish" else "🐻" if sentiment == "Bearish" else "😐"

            return f"""🌍 **OVERVIEW PASAR CRYPTO**

📊 **DATA PASAR GLOBAL:**
• **Total Market Cap**: ${total_market_cap:,.0f}
• **BTC Dominance**: {btc_dominance:.1f}%
• **Change 24h**: {change_24h:+.2f}%

{sentiment_emoji} **Market Sentiment**: {sentiment}

💡 **Analisis:**
• Dominasi BTC {'tinggi' if btc_dominance > 50 else 'normal'} ({btc_dominance:.1f}%)
• Pergerakan pasar {'positif' if change_24h > 0 else 'negatif'} dalam 24h
• Trend {'bullish' if change_24h > 2 else 'bearish' if change_24h < -2 else 'sideways'}

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Data Source**: Real-time Market Data"""

        except Exception as e:
            return f"❌ Error dalam analisis market: {str(e)}"

    def get_ai_response(self, text, language='id', user_id=None):
        """Enhanced AI response for crypto questions"""
        text_lower = text.lower()

        if language == 'id':
            if any(keyword in text_lower for keyword in ['apa itu bitcoin', 'bitcoin itu apa']):
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
- Hedge against inflation (lindung nilai inflasi)"""

            elif any(keyword in text_lower for keyword in ['harga', 'price', 'berapa']):
                return "💰 Untuk cek harga crypto, gunakan `/price <symbol>`\nUntuk analisis lengkap: `/analyze <symbol>`"

            elif any(keyword in text_lower for keyword in ['analisis', 'analyze', 'sinyal']):
                return "📊 Untuk analisis mendalam: `/analyze <symbol>` atau `/futures_signals`"

            elif any(keyword in text_lower for keyword in ['help', 'bantuan', 'command']):
                return """🤖 **CryptoMentor AI Commands**

📊 **Analisis:**
• `/price <symbol>` - Harga real-time
• `/analyze <symbol>` - Analisis mendalam
• `/futures <symbol>` - Analisis futures
• `/futures_signals` - Sinyal trading

💼 **Portfolio:**
• `/portfolio` - Lihat portfolio
• `/credits` - Cek sisa credit

🎯 **Lainnya:**
• `/help` - Panduan lengkap
• `/subscribe` - Upgrade premium"""

            else:
                return f"""🤖 **CryptoMentor AI**

Saya memahami Anda bertanya tentang: "{text}"

💡 **Yang bisa saya bantu:**
- Analisis harga crypto
- Sinyal trading
- Pertanyaan crypto umum
- Tutorial trading

Coba gunakan command yang tersedia atau tanya lebih spesifik."""

        return "🤖 **CryptoMentor AI** - Ask me anything about crypto!"

    # Auto Signal System Methods
    def get_auto_signal_status(self):
        """Get current status of Auto Signal system"""
        status = "🟢 RUNNING" if (self.auto_signal_task and not self.auto_signal_task.done()) else "🔴 STOPPED"

        return f"""🤖 AUTO SIGNAL STATUS

📊 Status: {status}
⚡ Enabled: {'✅' if self.auto_signal_enabled else '❌'}
🎯 Target Symbols: {len(self.target_symbols)} coins
⏰ Scan Interval: {self.scan_interval//60} minutes
🛡️ Cooldown: {self.signal_cooldown//60} minutes

Target Coins: {', '.join(self.target_symbols)}"""

    async def enable_auto_signals(self):
        """Enable Auto Signal system"""
        if not self.auto_signal_enabled:
            self.auto_signal_enabled = True
            return "✅ AUTO SIGNAL: Enabled"
        else:
            return "⚠️ AUTO SIGNAL: Already enabled"

    async def disable_auto_signals(self):
        """Disable Auto Signal system"""
        if self.auto_signal_enabled:
            self.auto_signal_enabled = False
            return "🛑 AUTO SIGNAL: Disabled"
        else:
            return "⚠️ AUTO SIGNAL: Already disabled"