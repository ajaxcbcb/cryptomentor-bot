
from typing import List, Dict, Any

def format_futures_signals(signals: List[Dict[str, Any]]) -> str:
    """Legacy formatter for futures signals"""
    if not signals:
        return "🚨 **FUTURES SIGNALS**\n\n❌ Tidak ada sinyal tersedia"
    
    lines = ["🚨 **FUTURES SIGNALS**\n"]
    
    for signal in signals:
        if "error" in signal:
            lines.append(f"❌ **{signal['coin']}**: Error - {signal['error']}")
            continue
            
        coin = signal.get('coin', 'Unknown')
        entry = signal.get('entry', 0)
        rsi = signal.get('rsi', 0)
        macd_hist = signal.get('macd_hist', 0)
        trend = signal.get('trend', 'Unknown')
        
        lines.append(
            f"📊 **{coin}**:\n"
            f"   • Entry: ${entry:.4f}\n"
            f"   • RSI: {rsi:.1f}\n"
            f"   • MACD: {macd_hist:.4f}\n"
            f"   • Trend: {trend}\n"
        )
    
    return "\n".join(lines)
