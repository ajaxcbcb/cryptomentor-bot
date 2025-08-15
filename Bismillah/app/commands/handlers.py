
import importlib
from telegram import Update
from telegram.ext import ContextTypes

# Import services lewat paket resmi agar stabil
try:
    from app.services import (
        analyze_coin, analyze_coin_futures,
        futures_entry, futures_signals,
        market_overview, services_healthcheck
    )
    SERVICES_READY = True
    _SERVICES_IMPORT_ERROR = None
except Exception as e:
    SERVICES_READY = False
    _SERVICES_IMPORT_ERROR = str(e)

def _fmt_basic_error(ctx="analysis service"):
    return (
        "❌ **Terjadi kesalahan mengambil data**\n\n"
        "🔄 **Error context**: {ctx}\n"
        "💡 Coba: /price btc — Cek harga basic"
    ).format(ctx=ctx)

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check command"""
    if not SERVICES_READY:
        return await update.effective_message.reply_text(
            f"❌ Services not ready: import error\n`{_SERVICES_IMPORT_ERROR}`",
            parse_mode="Markdown",
        )
    try:
        res = await services_healthcheck()
        if res.get("ok"):
            await update.effective_message.reply_text(f"✅ Services OK\nSample BTC price: ${res.get('sample_close', 0):,.2f}")
        else:
            await update.effective_message.reply_text(f"❌ Healthcheck failed: {res.get('error', 'Unknown')}")
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Healthcheck failed: {e}")

async def cmd_futures_signals_safe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Safe futures signals handler"""
    if not SERVICES_READY:
        return await update.effective_message.reply_text(
            "❌ **Terjadi kesalahan mengambil data untuk FUTURES_SIGNALS**\n\n"
            "🔄 **Error context**: analysis service not available\n"
            "💡 Coba: /price btc — Cek harga basic\n",
            parse_mode="Markdown",
        )
    
    coins = [c.upper() for c in (context.args or [])]  # kosong = top30 by service
    
    try:
        lst = await futures_signals(coins or None, threshold=75.0)
        
        # Basic formatter
        from datetime import datetime
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")
        lines = [
            "🚨 FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS",
            f"🕐 Scan Time: {now}",
            f"📊 Signals Found: {len(lst)} (Confidence ≥ 75.00%)",
        ]
        
        if not lst:
            lines += [
                "",
                "❌ Tidak ada sinyal memenuhi syarat",
                "",
                "💡 Alternatif:",
                "• Coba /futures btc untuk analisis spesifik",
                "• Gunakan /analyze eth untuk analisis teknikal", 
                "• Monitor kondisi market dengan /market",
            ]
        else:
            lines += ["", "📌 **TOP SIGNALS:**", ""]
            for i, it in enumerate(lst[:5], 1):
                if "error" in it:  # mestinya sudah difilter, tapi berjaga-jaga
                    continue
                direction = 'LONG' if it.get('trend') == 'up' else 'SHORT'
                direction_emoji = "🟢" if direction == 'LONG' else "🔴"
                
                lines.append(f"{i}. **{it['coin']}** {direction_emoji} **{direction}**")
                lines.append(f"⭐️ **Confidence**: {it['confidence']:.2f}%")
                lines.append(f"• 🎯 **Entry**: ${it['entry']:.4f}")
                lines.append(f"• 📊 **RSI**: {it['rsi']:.1f} | **MACD**: {it['macd_hist']:.4f}")
                lines.append("")
        
        text = "\n".join(lines)
        await update.effective_message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        await update.effective_message.reply_text(
            "❌ **Terjadi kesalahan mengambil data untuk FUTURES_SIGNALS**\n\n"
            "🔄 **Error context**: scan top30 pipeline\n"
            f"`{str(e)[:100]}...`\n"
            "💡 Coba: /price btc — Cek harga basic\n",
            parse_mode="Markdown",
        )
