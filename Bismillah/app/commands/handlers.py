from telegram import Update
from telegram.ext import ContextTypes

from app.utils.rate_limiter import rate_limiter
from app.utils.text_formatter import format_futures_signals_response
from app.services.analysis import (
    AnalysisService, 
    analyze_coin_crypto, 
    analyze_coin_futures,
    futures_signals as futures_signals_modern
)
from app.services.futures_legacy import futures_signals_legacy
from config import USE_LEGACY_FUTURES_SIGNALS
import importlib

async def cmd_futures_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /futures_signals command"""
    user_id = update.effective_user.id

    # Check rate limiting
    if not rate_limiter.check_limit(user_id, 'futures_signals'):
        await update.message.reply_text(
            "⏰ **Rate limit terlampaui**\n"
            "Tunggu beberapa detik sebelum menggunakan command ini lagi.",
            parse_mode='Markdown'
        )
        return

    coins = [c.upper() for c in (context.args or [])]
    try:
        if USE_LEGACY_FUTURES_SIGNALS:
            lst = await futures_signals_legacy(coins or None)
        else:
            # modern (Top30 + threshold) jika suatu saat kamu butuh lagi
            lst = await futures_signals_modern(coins or None, threshold=75.0)

        # Coba formatter lama dulu biar output identik
        F = None
        try:
            F = importlib.import_module("app.formatters.texts")
        except Exception:
            pass

        if F and hasattr(F, "format_futures_signals"):
            text = F.format_futures_signals(lst)
        else:
            # Fallback simple, menyerupai lama
            lines = ["🚨 **FUTURES SIGNALS**"]
            if not lst:
                lines += ["❌ Tidak ada sinyal"]
            else:
                for it in lst:
                    if "error" in it:
                        lines.append(f"- {it['coin']}: ❌ error")
                        continue
                    entry = it.get('entry', 0)
                    rsi = it.get('rsi', 0)
                    macd_hist = it.get('macd_hist', 0)
                    trend = it.get('trend', 'Unknown')
                    lines.append(
                        f"- **{it['coin']}**: Entry {entry:.4f} | "
                        f"RSI {rsi:.1f} | MACD {macd_hist:.4f} | {trend}"
                    )
            text = "\n".join(lines)

        await update.effective_message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.effective_message.reply_text(
            "❌ **Terjadi kesalahan mengambil data untuk FUTURES_SIGNALS**\n\n"
            "🔄 **Error context**: legacy mode\n"
            f"`{e}`\n"
            "💡 Coba: /price btc — Cek harga basic\n",
            parse_mode="Markdown",
        )