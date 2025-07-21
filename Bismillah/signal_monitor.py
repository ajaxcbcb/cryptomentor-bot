def __init__(self, bot_token, database, crypto_api, ai_assistant):
        self.bot_token = bot_token
        self.db = database
        self.crypto_api = crypto_api
        self.ai = ai_assistant
        self.is_running = False
        self.monitoring_task = None

        # Expanded list of cryptocurrencies to monitor (big and small market cap)
        self.symbols_to_monitor = [
            # Major coins (Large cap)
            'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE', 'MATIC', 'AVAX', 'LINK',
            'DOT', 'UNI', 'LTC', 'ATOM', 'FIL', 'TRX', 'ETC', 'XLM', 'AAVE', 'ALGO',

            # Mid-cap coins with potential
            'VET', 'MANA', 'SAND', 'AXS', 'GALA', 'ENJ', 'CHZ', 'BAT', 'ZIL', 'HOT',
            'ONE', 'HBAR', 'THETA', 'FTM', 'NEAR', 'FLOW', 'ICP', 'EGLD', 'KAVA', 'RUNE',

            # Small-cap with high potential (DeFi & Gaming)
            'CRV', 'COMP', 'YFI', 'SUSHI', 'CAKE', 'ALPHA', 'REEF', 'DODO', 'BADGER', 'FARM',
            'GMT', 'STEPN', 'APE', 'LOOKS', 'IMX', 'GODS', 'SLP', 'PYR', 'WHALE', 'SUPER'
        ]
def _analyze_signal_potential(self, symbol, price_data):
        """Enhanced signal analysis with Supply & Demand integration"""
        try:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)

            score = 0
            reasons = []
            confidence = "LOW"

            # 1. Get Supply & Demand Analysis
            try:
                snd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                if 'error' not in snd_analysis:
                    snd_score = snd_analysis.get('supply_demand_score', {}).get('score', 50)
                    snd_recommendation = snd_analysis.get('supply_demand_score', {}).get('recommendation', 'HOLD')

                    # SND scoring (40% weight)
                    if snd_score >= 75:
                        score += 40
                        reasons.append(f"Strong SND signal: {snd_recommendation} ({snd_score}/100)")
                        confidence = "HIGH"
                    elif snd_score >= 65:
                        score += 30
                        reasons.append(f"Good SND signal: {snd_recommendation} ({snd_score}/100)")
                        confidence = "MEDIUM"
                    elif snd_score <= 25:
                        score += 35
                        reasons.append(f"Strong SHORT signal: {snd_recommendation} ({snd_score}/100)")
                        confidence = "HIGH"
                    elif snd_score <= 35:
                        score += 25
                        reasons.append(f"Good SHORT signal: {snd_recommendation} ({snd_score}/100)")
                        confidence = "MEDIUM"

                    # Check for demand/supply zones proximity
                    zones = snd_analysis.get('supply_demand_zones', {})
                    nearest_demand = zones.get('nearest_demand')
                    nearest_supply = zones.get('nearest_supply')

                    if nearest_demand and nearest_demand.get('distance_from_current', 100) < 3:
                        score += 15
                        reasons.append("Near strong demand zone (high probability bounce)")
                        confidence = "HIGH"

                    if nearest_supply and nearest_supply.get('distance_from_current', 100) < 3:
                        score += 15
                        reasons.append("Near strong supply zone (high probability rejection)")
                        confidence = "HIGH"

            except Exception as e:
                print(f"SND analysis failed for {symbol}: {e}")

            # 2. Price Movement Analysis (25% weight)
            if abs(change_24h) >= 10:
                score += 25
                reasons.append(f"Extreme price movement: {change_24h:+.1f}%")
                confidence = "HIGH"
            elif abs(change_24h) >= 6:
                score += 20
                reasons.append(f"Significant price movement: {change_24h:+.1f}%")
                if confidence != "HIGH":
                    confidence = "MEDIUM"
            elif abs(change_24h) >= 3:
                score += 15
                reasons.append(f"Notable price movement: {change_24h:+.1f}%")

            # 3. Volume Analysis (20% weight)
            if volume_24h > 200000000:  # >200M USDT
                score += 20
                reasons.append("Exceptional trading volume (institutional interest)")
                confidence = "HIGH"
            elif volume_24h > 100000000:  # >100M USDT
                score += 15
                reasons.append("High trading volume")
            elif volume_24h > 20000000:  # >20M USDT (good for small caps)
                score += 10
                reasons.append("Good trading volume for market cap")

            # 4. Momentum & Pattern Analysis (15% weight)
            if change_24h > 12:
                score += 15
                reasons.append("Parabolic bullish momentum")
                confidence = "HIGH"
            elif change_24h < -12:
                score += 12
                reasons.append("Extreme bearish momentum (bounce/short opportunity)")
                confidence = "HIGH"
            elif 4 <= change_24h <= 8:
                score += 10
                reasons.append("Healthy bullish momentum")
            elif -8 <= change_24h <= -4:
                score += 8
                reasons.append("Healthy bearish momentum")

            # 5. Breakout Detection
            if 1.5 <= abs(change_24h) <= 3:
                score += 8
                reasons.append("Early breakout formation")

            # Confidence adjustment based on multiple factors
            if len(reasons) >= 4 and score >= 60:
                confidence = "HIGH"
            elif len(reasons) >= 3 and score >= 45:
                confidence = "MEDIUM"

            return {
                'score': score,
                'reasons': reasons,
                'confidence': confidence,
                'is_significant': score >= 50,  # Lowered threshold for more opportunities
                'snd_integrated': True
            }

        except Exception as e:
            print(f"Error analyzing enhanced signal potential for {symbol}: {e}")
            return {'score': 0, 'reasons': [], 'confidence': 'LOW', 'is_significant': False, 'snd_integrated': False}
def _format_signal_message(self, symbol, price_data, analysis):
        """Enhanced signal message with SND entry recommendations"""
        try:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            confidence = analysis.get('confidence', 'MEDIUM')

            # Price formatting
            if current_price < 1:
                price_str = f"${current_price:.6f}"
            elif current_price < 100:
                price_str = f"${current_price:.4f}"
            else:
                price_str = f"${current_price:,.2f}"

            # Volume formatting with market cap context
            if volume_24h > 1000000000:
                volume_str = f"${volume_24h/1000000000:.2f}B"
                cap_status = "🐋 Large Cap"
            elif volume_24h > 100000000:
                volume_str = f"${volume_24h/1000000:.1f}M"
                cap_status = "🦈 Mid Cap"
            elif volume_24h > 20000000:
                volume_str = f"${volume_24h/1000000:.1f}M"
                cap_status = "🐠 Small Cap"
            else:
                volume_str = f"${volume_24h:,.0f}"
                cap_status = "🦐 Micro Cap"

            # Enhanced signal emoji based on confidence and type
            if confidence == "HIGH":
                signal_emoji = "🔥" if change_24h > 0 else "⚡"
                confidence_emoji = "🎯 HIGH CONFIDENCE"
            elif confidence == "MEDIUM":
                signal_emoji = "📈" if change_24h > 0 else "📉"
                confidence_emoji = "🔸 MEDIUM CONFIDENCE"
            else:
                signal_emoji = "📊"
                confidence_emoji = "🔹 LOW CONFIDENCE"

            message = f"""{signal_emoji} **SINYAL OTOMATIS SND** 

💎 **{symbol}** ({cap_status})
💰 **Harga**: {price_str} ({change_24h:+.2f}%)
📊 **Volume 24h**: {volume_str}
⭐ **SND Score**: {analysis['score']}/100
{confidence_emoji}

🎯 **Analisis Signal:**"""

            for reason in analysis['reasons'][:4]:  # Limit to 4 main reasons
                message += f"\n• {reason}"

            # Get SND-based entry recommendations
            try:
                snd_analysis = self.crypto_api.analyze_supply_demand(symbol)
                if 'error' not in snd_analysis:
                    entry_rec = snd_analysis.get('entry_recommendation', {})
                    if entry_rec and len(entry_rec) > 0:
                        best_entry = entry_rec[0]
                        direction = best_entry.get('direction', 'HOLD')
                        entry_price = best_entry.get('entry_price', current_price)
                        stop_loss = best_entry.get('stop_loss', current_price * 0.95)
                        take_profit = best_entry.get('take_profit', current_price * 1.05)
                        entry_logic = best_entry.get('logic', 'SND-based entry')
                        risk_reward = best_entry.get('risk_reward', 1.0)

                        message += f"""

🎯 **SND ENTRY RECOMMENDATION:**
• **Direction**: {direction}
• **Entry**: ${entry_price:.6f if entry_price < 1 else entry_price:.4f if entry_price < 100 else entry_price:,.2f}
• **Take Profit**: ${take_profit:.6f if take_profit < 1 else take_profit:.4f if take_profit < 100 else take_profit:,.2f}
• **Stop Loss**: ${stop_loss:.6f if stop_loss < 1 else stop_loss:.4f if stop_loss < 100 else stop_loss:,.2f}
• **R/R Ratio**: 1:{risk_reward:.2f}
• **Logic**: {entry_logic}"""
            except:
                # Fallback simple recommendation
                if change_24h > 5:
                    message += f"""

📈 **BASIC ENTRY SETUP:**
• **Direction**: LONG
• **Entry**: Market atau {current_price * 0.99:.6f if current_price < 1 else current_price * 0.99:.4f if current_price < 100 else current_price * 0.99:,.2f}
• **Target 1**: {current_price * 1.05:.6f if current_price < 1 else current_price * 1.05:.4f if current_price < 100 else current_price * 1.05:,.2f} (+5%)
• **Stop Loss**: {current_price * 0.96:.6f if current_price < 1 else current_price * 0.96:.4f if current_price < 100 else current_price * 0.96:,.2f} (-4%)"""
                elif change_24h < -5:
                    message += f"""

📉 **BASIC SHORT SETUP:**
• **Direction**: SHORT
• **Entry**: Market atau {current_price * 1.01:.6f if current_price < 1 else current_price * 1.01:.4f if current_price < 100 else current_price * 1.01:,.2f}
• **Target 1**: {current_price * 0.95:.6f if current_price < 1 else current_price * 0.95:.4f if current_price < 100 else current_price * 0.95:,.2f} (-5%)
• **Stop Loss**: {current_price * 1.04:.6f if current_price < 1 else current_price * 1.04:.4f if current_price < 100 else current_price * 1.04:,.2f} (+4%)"""

            message += f"""

⚠️ **RISK WARNING**: 
• Maksimal 2-3% dari portfolio per trade
• Selalu gunakan stop loss
• Jangan FOMO, tunggu konfirmasi

🕐 **Time**: {datetime.now().strftime('%H:%M:%S WIB')}
📡 **Source**: Binance + SND Analysis"""

            return message

        except Exception as e:
            print(f"Error formatting enhanced signal message: {e}")
            return f"🎯 **SINYAL SND DETECTED: {symbol}** - Error formatting message"
async def _monitor_signals(self):
        """Enhanced monitoring loop with expanded coverage and SND analysis"""
        print("🔔 Enhanced Signal Monitor: Started monitoring for admin & lifetime users")
        print(f"📊 Monitoring {len(self.symbols_to_monitor)} cryptocurrencies (all market caps)")

        check_interval = 240  # 4 minutes between checks (faster for more opportunities)
        last_signals = {}  # Track last signal times to avoid spam
        cooldown_period = 1800  # 30 minutes cooldown per symbol

        while self.is_running:
            try:
                print(f"🔄 Signal Monitor: Scanning {len(self.symbols_to_monitor)} symbols for SND opportunities...")

                current_time = time.time()
                signals_found = 0
                high_confidence_signals = 0

                # Process symbols in batches to avoid API rate limits
                batch_size = 10
                for i in range(0, len(self.symbols_to_monitor), batch_size):
                    batch = self.symbols_to_monitor[i:i+batch_size]

                    for symbol in batch:
                        try:
                            # Get enhanced price data with force refresh for real-time
                            price_data = self.crypto_api.get_multi_api_price(symbol, force_refresh=True)

                            if 'error' in price_data or not price_data.get('price') or price_data.get('price', 0) <= 0:
                                continue

                            # Enhanced signal analysis with SND integration
                            analysis = self._analyze_signal_potential(symbol, price_data)

                            if analysis['is_significant']:
                                # Enhanced cooldown logic based on confidence
                                last_signal_time = last_signals.get(symbol, 0)
                                required_cooldown = cooldown_period

                                # Reduce cooldown for high confidence signals
                                if analysis['confidence'] == 'HIGH':
                                    required_cooldown = 1200  # 20 minutes for high confidence

                                if current_time - last_signal_time < required_cooldown:
                                    continue

                                # Format enhanced signal message
                                message = self._format_signal_message(symbol, price_data, analysis)

                                # Send to eligible users (admin + lifetime)
                                users_reached = await self._send_signal_to_eligible_users(message)

                                # Update tracking
                                last_signals[symbol] = current_time
                                signals_found += 1

                                if analysis['confidence'] == 'HIGH':
                                    high_confidence_signals += 1

                                # Enhanced logging
                                confidence_emoji = "🔥" if analysis['confidence'] == 'HIGH' else "📈" if analysis['confidence'] == 'MEDIUM' else "📊"
                                market_cap = "Large" if price_data.get('volume_24h', 0) > 100000000 else "Mid" if price_data.get('volume_24h', 0) > 20000000 else "Small"

                                print(f"{confidence_emoji} Signal: {symbol} ({market_cap} Cap) | Score: {analysis['score']}/100 | Confidence: {analysis['confidence']} | Users: {users_reached}")

                        except Exception as e:
                            print(f"❌ Error processing {symbol}: {e}")
                            continue

                    # Small delay between batches to be API-friendly
                    await asyncio.sleep(2)

                # Enhanced monitoring summary
                total_monitored = len(self.symbols_to_monitor)
                print(f"📊 Monitor Round Complete:")
                print(f"   • Total Scanned: {total_monitored} cryptocurrencies")
                print(f"   • Signals Sent: {signals_found}")
                print(f"   • High Confidence: {high_confidence_signals}")
                print(f"   • Next scan in: {check_interval//60} minutes")

                # Wait before next check
                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"❌ Enhanced Signal Monitor: Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)  # Wait longer on error
                continue
async def _send_signal_to_eligible_users(self, message):
        """Enhanced signal delivery to admin and lifetime users with better formatting"""
        try:
            bot = telegram.Bot(token=self.bot_token)
            users_notified = 0
            failed_sends = 0

            # Get admin ID from environment
            admin_id = int(os.getenv('ADMIN_USER_ID', 0))

            # Enhanced message with special header for signals
            enhanced_message = f"""🔔 **AUTO SIGNAL NOTIFICATION**
{message}

💡 **Exclusive untuk Admin & Lifetime Members**
⚠️ **Disclaimer**: Bukan saran investasi, gunakan analisis pribadi!"""

            # Send to admin first
            if admin_id > 0:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=enhanced_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    users_notified += 1
                    print(f"✅ Enhanced signal sent to admin ({admin_id})")
                except Exception as e:
                    print(f"❌ Failed to send signal to admin: {e}")
                    failed_sends += 1

            # Get and send to all lifetime users
            lifetime_users = self.db.get_lifetime_users()
            print(f"📋 Found {len(lifetime_users)} lifetime users for signal delivery")

            for user_data in lifetime_users:
                user_id = user_data[0]  # telegram_id
                user_name = user_data[1]  # first_name
                username = user_data[2] if len(user_data) > 2 else "No username"  # username

                if user_id == admin_id:  # Skip admin (already sent)
                    continue

                try:
                    # Add personalized touch for lifetime users
                    personalized_message = enhanced_message.replace(
                        "💡 **Exclusive untuk Admin & Lifetime Members**",
                        f"💎 **Exclusive untuk Lifetime Member: {user_name}**"
                    )

                    await bot.send_message(
                        chat_id=user_id,
                        text=personalized_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    users_notified += 1
                    print(f"✅ Signal sent to lifetime user: {user_name} (@{username}) [{user_id}]")

                    # Small delay to avoid hitting rate limits
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"❌ Failed to send signal to {user_name} ({user_id}): {e}")
                    failed_sends += 1

            # Log delivery summary
            total_attempted = 1 + len(lifetime_users) if admin_id > 0 else len(lifetime_users)
            success_rate = (users_notified / total_attempted * 100) if total_attempted > 0 else 0

            print(f"📊 Signal Delivery Summary:")
            print(f"   • Successfully sent: {users_notified}")
            print(f"   • Failed sends: {failed_sends}")
            print(f"   • Success rate: {success_rate:.1f}%")

            return users_notified

        except Exception as e:
            print(f"❌ Critical error in signal delivery: {e}")
            import traceback
            traceback.print_exc()
            return 0