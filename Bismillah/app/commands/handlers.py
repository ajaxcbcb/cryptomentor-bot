
import importlib
import sys
import os
from telegram import Update
from telegram.ext import ContextTypes

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.analysis import analyze_coin, futures_entry, futures_signals, market_overview

# Coba muat formatter lama
def _fmt():
    try:
        return importlib.import_module("app.formatters.texts")
    except Exception:
        return None

def _fallback_err(coin, ctx="price data"):
    return (
        f"❌ **Terjadi kesalahan mengambil data untuk {coin.upper()}**\n\n"
        "💡 **Coba alternatif**:\n"
        "• `/price {}` - Cek harga basic\n"
        "• Tunggu beberapa menit dan coba lagi\n"
        "• Hubungi admin jika masalah berlanjut\n\n"
        f"🔄 **Error context**: {ctx}\n"
    ).format(coin.lower())

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = (context.args[0] if context.args else "ETH").upper()
    try:
        res = await analyze_coin(coin)
        F = _fmt()
        if F and hasattr(F, "format_analyze"):
            text = F.format_analyze(res)  # gunakan template lama
        else:
            text = (
                f"🔍 **PROFESSIONAL COMPREHENSIVE ANALYSIS - {res['coin']}**\n\n"
                f"💰 **Current Price**: ${res['price']:.4f}\n"
                f"📈 **Trend**: {res['trend'].title()}\n"
                f"📊 **RSI(14)**: {res['rsi']:.2f}\n"
                f"📈 **MACD Histogram**: {res['macd_hist']:.4f}\n"
                f"📊 **ATR(14)**: ${res['atr']:.4f}\n\n"
                f"🎯 **Single Entry Point**: ${res['entry_one']:.4f}\n\n"
                f"📡 **Data Source**: CoinAPI Real-time"
            )
        await update.effective_message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        await update.effective_message.reply_text(_fallback_err(coin, "analyze"))

async def cmd_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = (context.args[0] if context.args else "ETH").upper()
    try:
        res = await futures_entry(coin)
        F = _fmt()
        if F and hasattr(F, "format_futures"):
            text = F.format_futures(res)  # template lama
        else:
            text = (
                f"🔍 **PROFESSIONAL FUTURES ANALYSIS - {res['coin']}**\n\n"
                f"💰 **Current Price**: ${res['price']:.4f}\n"
                f"🎯 **Single Entry Point**: ${res['entry']:.4f}\n"
                f"📈 **Trend**: {res['trend'].title()}\n\n"
                f"⚠️ **Trading Rules**:\n"
                f"• Single entry point strategy\n"
                f"• Use proper position sizing (1-3% risk)\n"
                f"• Set stop loss before entry\n"
                f"• Monitor volume for confirmation\n\n"
                f"📡 **Data Source**: CoinAPI Real-time"
            )
        await update.effective_message.reply_text(text, parse_mode='Markdown')
    except Exception:
        await update.effective_message.reply_text(_fallback_err(coin, "futures"))

async def cmd_futures_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = [c.upper() for c in (context.args or ["BTC","ETH","SOL"])]
    try:
        lst = await futures_signals(coins)
        F = _fmt()
        if F and hasattr(F, "format_futures_signals"):
            text = F.format_futures_signals(lst)
        else:
            lines = ["🚨 **FUTURES SIGNALS - CoinAPI Analysis**\n"]
            for item in lst:
                if "error" in item:
                    lines.append(f"❌ {item['coin']}: Error retrieving data")
                else:
                    status = "✅ **GOOD**" if item['ok'] else "❌ **WAIT**"
                    lines.append(
                        f"{status} **{item['coin']}**\n"
                        f"• Entry: ${item['entry']:.4f}\n"
                        f"• RSI: {item['rsi']:.1f}\n"
                        f"• MACD: {item['macd_hist']:.4f}\n"
                        f"• Trend: {item['trend'].title()}\n"
                    )
            text = "\n".join(lines) + f"\n\n📡 **Source**: CoinAPI Real-time"
        await update.effective_message.reply_text(text, parse_mode='Markdown')
    except Exception:
        await update.effective_message.reply_text("❌ Gagal membuat futures signals.")

async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = [c.upper() for c in (context.args or ["BTC","ETH","SOL"])]
    try:
        mv = await market_overview(coins)
        F = _fmt()
        if F and hasattr(F, "format_market"):
            text = F.format_market(mv)
        else:
            lines = ["🌐 **MARKET OVERVIEW - CoinAPI**\n"]
            for c, obj in mv["coins"].items():
                if "error" in obj:
                    lines.append(f"❌ {c}: Data unavailable")
                else:
                    lines.append(f"💰 **{c}**: ${obj['price']:.4f}")
            text = "\n".join(lines) + f"\n\n📡 **Source**: CoinAPI Real-time"
        await update.effective_message.reply_text(text, parse_mode='Markdown')
    except Exception:
        await update.effective_message.reply_text("❌ Gagal mengambil market overview.")
