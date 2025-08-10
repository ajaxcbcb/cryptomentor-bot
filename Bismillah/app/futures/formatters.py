
from typing import Dict, Any, List
from datetime import datetime

def format_futures_summary(result: Dict[str, Any]) -> str:
    """Format comprehensive futures analysis (for /futures command)"""
    try:
        symbol = result.get('symbol', 'UNKNOWN')
        timeframe = result.get('timeframe', '15m')
        price = result.get('price', 0)
        signals = result.get('signals', [])
        meta = result.get('meta', {})
        indicators = meta.get('indicators', {})
        
        # Header
        analysis = f"🔍 **PROFESSIONAL FUTURES ANALYSIS - {symbol} ({timeframe})**\n\n"
        
        # Current status
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        analysis += f"🕐 **Analysis Time**: {current_time}\n"
        analysis += f"💰 **Current Price**: ${price:,.6f}\n\n"
        
        # Best signal
        if signals:
            best_signal = signals[0]
            direction = best_signal['side']
            confidence = best_signal['confidence']
            
            direction_emoji = "🟢" if direction == "LONG" else "🔴"
            
            if confidence >= 85:
                confidence_desc = "🔥 Very High"
            elif confidence >= 75:
                confidence_desc = "⚡ High"
            elif confidence >= 65:
                confidence_desc = "💡 Medium"
            else:
                confidence_desc = "⚠️ Low"
            
            analysis += f"{direction_emoji} **TRADING SIGNAL**: {direction}\n"
            analysis += f"⭐ **Confidence**: {confidence}% ({confidence_desc})\n"
            analysis += f"🎯 **Strategy**: Multi-Timeframe Analysis\n"
            analysis += f"⚡ **Time Horizon**: 4-24 hours\n\n"
            
            # Trading levels
            entry = best_signal.get('entry', price)
            sl = best_signal.get('sl', price)
            tp_levels = best_signal.get('tp', [price, price])
            
            analysis += f"💰 **DETAILED TRADING SETUP:**\n"
            analysis += f"• Entry: ${entry:.6f}\n"
            analysis += f"• Stop Loss: ${sl:.6f}\n"
            analysis += f"• TP1 (60%): ${tp_levels[0]:.6f}\n"
            analysis += f"• TP2 (40%): ${tp_levels[1]:.6f}\n"
            
            # Risk/Reward
            risk = abs(entry - sl)
            reward = abs(tp_levels[1] - entry)
            rr_ratio = reward / risk if risk > 0 else 2.0
            analysis += f"• Risk/Reward: {rr_ratio:.1f}:1\n"
            analysis += f"• Max Risk: 2.5% per position\n\n"
            
            # Reasons
            reasons = best_signal.get('reasons', [])
            if reasons:
                analysis += f"💡 **Signal Reasons:**\n"
                for reason in reasons[:5]:
                    analysis += f"• {reason}\n"
                analysis += "\n"
        else:
            analysis += "⚠️ **No clear signals at current levels**\n\n"
        
        # Technical indicators
        if indicators:
            rsi = indicators.get('rsi', 0)
            macd = indicators.get('macd_histogram', 0)
            
            rsi_condition = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Normal"
            macd_condition = "Bullish" if macd > 0 else "Bearish"
            
            analysis += f"🔬 **TECHNICAL ANALYSIS ({timeframe}):**\n"
            analysis += f"• EMA50: ${indicators.get('ema_50', 0):,.4f}\n"
            analysis += f"• EMA200: ${indicators.get('ema_200', 0):,.4f}\n"
            analysis += f"• RSI(14): {rsi:.1f} ({rsi_condition})\n"
            analysis += f"• MACD: {macd:.4f} ({macd_condition})\n"
            analysis += f"• ATR: ${indicators.get('atr', 0):,.4f}\n\n"
        
        # Footer
        analysis += f"⚠️ **RISK MANAGEMENT PROTOCOL:**\n"
        analysis += f"• Gunakan proper position sizing (1-3% per trade)\n"
        analysis += f"• Set stop loss sebelum entry\n"
        analysis += f"• Take profit secara bertahap\n"
        analysis += f"• Monitor market conditions\n"
        analysis += f"• DYOR sebelum trading\n\n"
        
        analysis += f"📡 **Data Sources**: CoinAPI OHLCV + Unified Engine\n"
        analysis += f"🔄 **Update Frequency**: Real-time price + Technical refresh"
        
        return analysis
        
    except Exception as e:
        return f"❌ Error formatting futures analysis: {str(e)}"

def format_signals_list(signals: List[Dict[str, Any]], result: Dict[str, Any]) -> str:
    """Format signals list (for /futures_signals command)"""
    try:
        symbol = result.get('symbol', 'UNKNOWN')
        price = result.get('price', 0)
        timeframe = result.get('timeframe', '15m')
        
        # Filter signals with confidence >= 75%
        filtered_signals = [s for s in signals if s.get('confidence', 0) >= 75]
        
        current_time = datetime.now().strftime('%H:%M:%S WIB')
        
        # Header
        message = f"🚨 **FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS**\n\n"
        message += f"🕐 **Scan Time**: {current_time}\n"
        message += f"📊 **Signals Found**: {len(filtered_signals)} (Confidence ≥ 75.00%)\n\n"
        
        if not filtered_signals:
            message += f"❌ Tidak ada sinyal memenuhi syarat untuk {symbol}\n\n"
            message += f"📊 **Current Price**: ${price:,.6f}\n"
            message += f"⚠️ **Status**: Tidak ada setup trading yang jelas saat ini\n\n"
            message += f"💡 **Kemungkinan Penyebab:**\n"
            message += f"• Market dalam kondisi consolidation\n"
            message += f"• Volatilitas rendah saat ini\n"
            message += f"• Menunggu momentum yang lebih jelas\n\n"
            message += f"🔄 **Alternatif:**\n"
            message += f"• Coba /futures {symbol.replace('USDT', '').lower()} untuk analisis spesifik\n"
            message += f"• Monitor kondisi market dengan /market\n\n"
            return message
        
        # Signal details
        for i, signal in enumerate(filtered_signals, 1):
            direction = signal.get('side', 'UNKNOWN')
            confidence = signal.get('confidence', 0)
            entry = signal.get('entry', price)
            sl = signal.get('sl', price)
            tp_levels = signal.get('tp', [price, price])
            reasons = signal.get('reasons', [])
            
            direction_emoji = "🟢" if direction == "LONG" else "🔴"
            
            # Calculate R/R ratio
            risk = abs(entry - sl)
            reward = abs(tp_levels[1] - entry)
            rr_ratio = reward / risk if risk > 0 else 2.0
            
            # Determine trend and structure
            trend = "Bullish" if direction == "LONG" else "Bearish"
            structure = f"{direction} Bias"
            
            # Main reason (first one)
            main_reason = reasons[0] if reasons else "Technical confluence detected"
            
            message += f"**{i}. {symbol} {direction_emoji} {direction}**\n"
            message += f"⭐️ Confidence: {confidence:.1f}%\n"
            message += f"💰 Entry: ${entry:.2f}\n"
            message += f"🛑 Stop Loss: ${sl:.2f}\n"
            message += f"🎯 TP1: ${tp_levels[0]:.2f}\n"
            message += f"🎯 TP2: ${tp_levels[1]:.2f}\n"
            message += f"📊 R/R Ratio: {rr_ratio:.1f}:1\n"
            message += f"🔄 Trend: {trend}\n"
            message += f"⚡️ Structure: {structure}\n"
            message += f"🧠 Reason: {main_reason}\n\n"
        
        # Footer
        message += f"⚠️ **TRADING DISCLAIMER:**\n"
        message += f"• Signals berbasis Multi-Timeframe analysis\n"
        message += f"• Gunakan proper risk management\n"
        message += f"• Position sizing sesuai risk level\n"
        message += f"• DYOR sebelum trading\n\n"
        
        message += f"📡 **Data Sources**: CoinAPI + Unified Engine\n"
        message += f"🔄 **Update Frequency**: Real-time technical refresh"
        
        return message
        
    except Exception as e:
        return f"❌ Error formatting signals list: {str(e)}"

def format_autosignal_message(signal: Dict[str, Any]) -> str:
    """Format AutoSignal message (consistent with manual signals)"""
    try:
        symbol = signal.get('symbol', 'UNKNOWN')
        side = signal.get('side', 'UNKNOWN')
        confidence = signal.get('confidence', 0)
        price = signal.get('price')
        reason = signal.get('reason', '')
        
        side_emoji = "🟢" if side == "LONG" else "🔴"
        
        message = f"🤖 **AUTO FUTURES SIGNAL**\n\n"
        message += f"📊 **Pair**: {symbol}\n"
        message += f"{side_emoji} **Side**: {side}\n"
        message += f"⭐ **Confidence**: {confidence}%\n"
        
        if price:
            message += f"💰 **Entry**: ~${price:,.2f}\n"
        
        if reason:
            message += f"🧠 **Reason**: {reason}\n"
        
        message += f"\n⚡ **Auto-generated** from unified engine\n"
        message += f"⚠️ **Risk Management**: Use proper position sizing\n"
        message += f"📱 **Action**: Monitor and apply your strategy"
        
        return message
        
    except Exception as e:
        return f"❌ Error formatting auto signal: {str(e)}"
