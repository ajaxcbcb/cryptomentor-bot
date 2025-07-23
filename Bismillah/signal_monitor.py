
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

class SignalMonitor:
    def __init__(self, crypto_api, ai_assistant, database, bot_instance):
        self.crypto_api = crypto_api
        self.ai_assistant = ai_assistant
        self.database = database
        self.bot = bot_instance
        self.is_running = False
        self.last_signal_time = {}
        self.min_signal_interval = 3600  # 1 hour minimum between signals for same coin
        
        # Extended list of coins to monitor (not just top 10)
        self.monitored_coins = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'AVAX', 'LINK',
            'DOT', 'UNI', 'LTC', 'ALGO', 'ATOM', 'FTM', 'NEAR', 'SAND', 'MANA', 'AXS',
            'CRV', 'SUSHI', 'COMP', 'AAVE', 'MKR', 'SNX', 'YFI', 'RUNE', 'LUNA', 'UST',
            'CAKE', 'PCS', 'AUTO', 'BAKE', 'TWT', 'SFP', 'LINA', 'DODO', 'ALPACA', 'XVS',
            'VAI', 'BETH', 'SXP', 'CTK', 'HARD', 'KAVA', 'SWP', 'USDP', 'NFT', 'C98',
            'ALICE', 'FOR', 'REQ', 'GHST', 'TLM', 'SUPER', 'ICP', 'AR', 'FIL', 'ETC',
            'THETA', 'VET', 'TRX', 'FTT', 'SHIB', 'CRO', 'LEO', 'WBTC', 'DAI', 'HEX',
            'BUSD', 'USDC', 'USDT', 'TUSD', 'USDP', 'FRAX', 'GUSD', 'HUSD', 'SUSD',
            'ONDO', 'SEI', 'PEPE', 'FLOKI', 'WIF', 'BONK', 'JUP', 'PYTH', 'RENDER',
            'INJ', 'SUI', 'APT', 'OP', 'ARB', 'TIA', 'PENDLE', 'EIGEN', 'HYPERLIQUID'
        ]
        
        # Confidence threshold for signals
        self.min_confidence_score = 7.5  # Only high confidence signals
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """Start the automated signal monitoring"""
        if self.is_running:
            self.logger.info("Signal monitor already running")
            return
            
        self.is_running = True
        self.logger.info("🚀 Starting automated signal monitoring for admin and premium lifetime users")
        
        while self.is_running:
            try:
                await self.scan_and_send_signals()
                # Wait 30 minutes before next scan
                await asyncio.sleep(1800)  # 30 minutes
            except Exception as e:
                self.logger.error(f"Error in signal monitoring loop: {e}")
                # Wait 5 minutes before retrying if error
                await asyncio.sleep(300)

    async def stop_monitoring(self):
        """Stop the automated signal monitoring"""
        self.is_running = False
        self.logger.info("🛑 Stopped automated signal monitoring")

    async def scan_and_send_signals(self):
        """Scan all monitored coins and send high-confidence signals"""
        self.logger.info(f"🔍 Scanning {len(self.monitored_coins)} coins for high-confidence signals...")
        
        high_confidence_signals = []
        
        # Randomly shuffle coins to distribute API load
        coins_to_scan = self.monitored_coins.copy()
        random.shuffle(coins_to_scan)
        
        # Scan first 30 coins each cycle to manage API limits
        for symbol in coins_to_scan[:30]:
            try:
                # Check if enough time has passed since last signal for this coin
                if self._should_skip_coin(symbol):
                    continue
                
                signal_data = await self._analyze_coin_for_signal(symbol)
                
                if signal_data and signal_data['confidence_score'] >= self.min_confidence_score:
                    high_confidence_signals.append(signal_data)
                    self.logger.info(f"✅ High confidence signal found: {symbol} (Score: {signal_data['confidence_score']}/10)")
                
                # Small delay to avoid API rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Send signals if found
        if high_confidence_signals:
            await self._send_signals_to_special_users(high_confidence_signals)
        else:
            self.logger.info("🔍 No high-confidence signals found in this scan")

    async def _analyze_coin_for_signal(self, symbol: str) -> Dict[str, Any]:
        """Analyze a single coin for trading signals"""
        try:
            # Get comprehensive data
            price_data = self.crypto_api.get_price(symbol)
            if not price_data or 'error' in price_data:
                return None
                
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            
            # Get futures data
            futures_data = self.crypto_api.get_futures_data(symbol)
            long_ratio = futures_data.get('long_ratio', 50) if futures_data else 50
            
            # Get supply/demand analysis if available
            sd_analysis = None
            try:
                sd_analysis = self.crypto_api.analyze_supply_demand(symbol)
            except:
                pass
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                symbol, current_price, change_24h, volume_24h, long_ratio, sd_analysis
            )
            
            if confidence_score < self.min_confidence_score:
                return None
            
            # Generate signal recommendation
            signal_recommendation = self._generate_signal_recommendation(
                symbol, current_price, change_24h, long_ratio, sd_analysis, confidence_score
            )
            
            return {
                'symbol': symbol,
                'confidence_score': confidence_score,
                'current_price': current_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'long_ratio': long_ratio,
                'recommendation': signal_recommendation,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in _analyze_coin_for_signal for {symbol}: {e}")
            return None

    def _calculate_confidence_score(self, symbol: str, price: float, change_24h: float, 
                                  volume_24h: float, long_ratio: float, sd_analysis: Any) -> float:
        """Calculate confidence score for a trading signal"""
        confidence = 5.0  # Base score
        
        # Volume factor (higher volume = higher confidence)
        if volume_24h > 100000000:  # > 100M
            confidence += 1.5
        elif volume_24h > 50000000:  # > 50M
            confidence += 1.0
        elif volume_24h > 10000000:  # > 10M
            confidence += 0.5
        
        # Price momentum factor
        abs_change = abs(change_24h)
        if abs_change > 10:
            confidence += 2.0  # Strong momentum
        elif abs_change > 5:
            confidence += 1.5
        elif abs_change > 3:
            confidence += 1.0
        elif abs_change < 1:
            confidence -= 1.0  # Low momentum reduces confidence
        
        # Long/Short ratio factor (extreme ratios indicate potential reversals)
        if long_ratio > 75 or long_ratio < 25:
            confidence += 2.0  # Extreme sentiment = high reversal potential
        elif long_ratio > 65 or long_ratio < 35:
            confidence += 1.0
        
        # Supply/Demand factor
        if sd_analysis and 'error' not in sd_analysis:
            sd_score_data = sd_analysis.get('supply_demand_score', {})
            sd_score = sd_score_data.get('score', 50)
            
            if sd_score >= 80 or sd_score <= 20:
                confidence += 1.5  # Strong S&D levels
            elif sd_score >= 70 or sd_score <= 30:
                confidence += 1.0
        
        # Market cap consideration (major coins get slight boost)
        major_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'AVAX', 'LINK']
        if symbol in major_coins:
            confidence += 0.5
        
        # Cap confidence score at 10
        return min(10.0, confidence)

    def _generate_signal_recommendation(self, symbol: str, price: float, change_24h: float,
                                      long_ratio: float, sd_analysis: Any, confidence: float) -> Dict[str, Any]:
        """Generate trading signal recommendation"""
        
        # Determine signal direction
        signal_direction = "HOLD"
        signal_strength = "NEUTRAL"
        entry_price = price
        stop_loss = price
        take_profit = price
        reasoning = []
        
        # Contrarian approach based on long/short ratio
        if long_ratio > 70:
            signal_direction = "SHORT"
            signal_strength = "STRONG" if long_ratio > 80 else "MODERATE"
            entry_price = price * 1.002
            stop_loss = price * 1.025
            take_profit = price * 0.96
            reasoning.append(f"Long ratio sangat tinggi ({long_ratio:.1f}%) - potensi long squeeze")
        elif long_ratio < 30:
            signal_direction = "LONG"
            signal_strength = "STRONG" if long_ratio < 20 else "MODERATE"
            entry_price = price * 0.998
            stop_loss = price * 0.975
            take_profit = price * 1.04
            reasoning.append(f"Long ratio sangat rendah ({long_ratio:.1f}%) - potensi short squeeze")
        
        # Momentum consideration
        if abs(change_24h) > 8:
            if change_24h > 0 and signal_direction != "SHORT":
                signal_direction = "LONG"
                reasoning.append(f"Momentum bullish kuat (+{change_24h:.1f}%)")
            elif change_24h < 0 and signal_direction != "LONG":
                signal_direction = "SHORT"
                reasoning.append(f"Momentum bearish kuat ({change_24h:.1f}%)")
        
        # Supply/Demand enhancement
        if sd_analysis and 'error' not in sd_analysis:
            sd_score_data = sd_analysis.get('supply_demand_score', {})
            sd_bias = sd_score_data.get('bias', 'Balanced')
            
            if 'Strong Demand' in sd_bias and signal_direction != "SHORT":
                signal_direction = "LONG"
                reasoning.append("Area demand kuat teridentifikasi")
            elif 'Strong Supply' in sd_bias and signal_direction != "LONG":
                signal_direction = "SHORT"
                reasoning.append("Area supply kuat teridentifikasi")
        
        return {
            'direction': signal_direction,
            'strength': signal_strength,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': abs(take_profit - entry_price) / abs(stop_loss - entry_price) if abs(stop_loss - entry_price) > 0 else 1.5,
            'reasoning': reasoning,
            'confidence': confidence
        }

    def _should_skip_coin(self, symbol: str) -> bool:
        """Check if we should skip this coin due to recent signal"""
        last_signal = self.last_signal_time.get(symbol)
        if last_signal:
            time_diff = (datetime.now() - last_signal).total_seconds()
            if time_diff < self.min_signal_interval:
                return True
        return False

    async def _send_signals_to_special_users(self, signals: List[Dict[str, Any]]):
        """Send signals to admin and premium lifetime users"""
        try:
            # Get admin and premium lifetime users
            special_users = self._get_special_users()
            
            if not special_users:
                self.logger.info("No special users found to send signals")
                return
            
            # Format signal message
            signal_message = self._format_signal_message(signals)
            
            # Send to each special user
            sent_count = 0
            for user_id in special_users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=signal_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    sent_count += 1
                    
                    # Update last signal time for all coins in this batch
                    for signal in signals:
                        self.last_signal_time[signal['symbol']] = datetime.now()
                    
                    # Log activity
                    signal_symbols = [s['symbol'] for s in signals]
                    self.database.log_user_activity(
                        user_id, 
                        "auto_signal_received", 
                        f"Received automated signals: {', '.join(signal_symbols)}"
                    )
                    
                    # Small delay between sends
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Failed to send signal to user {user_id}: {e}")
                    continue
            
            self.logger.info(f"✅ Sent {len(signals)} signals to {sent_count} special users")
            
        except Exception as e:
            self.logger.error(f"Error in _send_signals_to_special_users: {e}")

    def _get_special_users(self) -> List[int]:
        """Get list of admin and premium lifetime users"""
        try:
            special_users = []
            
            # Add admin user from environment variables
            import os
            admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
            if admin_id > 0:
                special_users.append(admin_id)
            
            # Add premium lifetime users
            self.database.cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE is_premium = 1 AND (subscription_end IS NULL OR subscription_end = '')
                AND telegram_id IS NOT NULL
            """)
            
            lifetime_users = self.database.cursor.fetchall()
            for user in lifetime_users:
                user_id = user[0]
                if user_id not in special_users:
                    special_users.append(user_id)
            
            self.logger.info(f"Special users found: {len(special_users)} (Admin: {admin_id > 0}, Lifetime: {len(lifetime_users)})")
            return special_users
            
        except Exception as e:
            self.logger.error(f"Error getting special users: {e}")
            # Fallback: try to get admin from environment
            import os
            admin_id = int(os.getenv('ADMIN_USER_ID', '0'))
            return [admin_id] if admin_id > 0 else []

    def _format_signal_message(self, signals: List[Dict[str, Any]]) -> str:
        """Format signals into a readable message"""
        if not signals:
            return ""
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        message = f"""🚨 **SINYAL OTOMATIS PREMIUM**

⏰ **Waktu**: {current_time}
🎯 **High Confidence Signals** ({len(signals)} coins)

"""
        
        for i, signal in enumerate(signals[:5], 1):  # Limit to 5 signals per message
            symbol = signal['symbol']
            confidence = signal['confidence_score']
            recommendation = signal['recommendation']
            current_price = signal['current_price']
            change_24h = signal['change_24h']
            
            direction_emoji = "🟢" if recommendation['direction'] == "LONG" else "🔴" if recommendation['direction'] == "SHORT" else "⚪"
            
            message += f"""**{i}. {symbol} {direction_emoji} {recommendation['direction']}**
💰 Price: ${current_price:,.4f} ({change_24h:+.1f}%)
🎯 Confidence: {confidence:.1f}/10
📈 Entry: ${recommendation['entry_price']:,.4f}
🛡️ SL: ${recommendation['stop_loss']:,.4f}
🎯 TP: ${recommendation['take_profit']:,.4f}
📊 R/R: {recommendation['risk_reward_ratio']:.1f}:1
💡 Alasan: {', '.join(recommendation['reasoning'][:2])}

"""
        
        message += f"""⚠️ **DISCLAIMER:**
• Sinyal otomatis berdasarkan analisis teknikal
• Gunakan proper risk management
• DYOR sebelum trading
• Trading berisiko tinggi

🤖 **Auto Signal System** - Hanya untuk Admin & Premium Lifetime"""
        
        return message

    async def force_scan_now(self):
        """Force immediate scan (for testing purposes)"""
        self.logger.info("🔄 Force scanning for signals...")
        await self.scan_and_send_signals()
