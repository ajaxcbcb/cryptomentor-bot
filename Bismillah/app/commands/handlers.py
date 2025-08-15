from telegram import Update
from telegram.ext import ContextTypes

from app.utils.rate_limiter import rate_limiter
from app.utils.text_formatter import format_futures_signals_response
from app.utils.telegram_safe import safe_reply, safe_edit
from app.services.analysis import (
    AnalysisService, 
    analyze_coin, 
    analyze_coin_crypto, 
    analyze_coin_futures,
    futures_signals as futures_signals_modern
)
from app.services.futures_legacy import futures_signals_legacy
from app.services.futures_report import build_futures_signals_report
from app.services.market_report import build_market_report
from app.formatters.futures_signals_html import format_futures_signals_html
from app.formatters.market_card import format_market_report
from app.formatters.signal_card import format_signal_card, format_signal_list
from config import USE_LEGACY_FUTURES_SIGNALS
import importlib

# Assuming analyze_coin is defined elsewhere and imported correctly
# For demonstration, a placeholder function is used if not found in original snippet context
try:
    from app.services.analysis import analyze_coin
except ImportError:
    async def analyze_coin(symbol):
        # Placeholder for actual analysis function
        print(f"Placeholder analyze_coin called for {symbol}")
        return {
            "symbol": symbol,
            "trend": "Up",
            "confidence": 0.8,
            "stop_loss": 1000,
            "tp1": 1200,
            "tp2": 1300,
            "risk_reward_ratio": 2.5,
            "structure": "Bullish",
            "reason": "Positive market sentiment",
            "change_24h": 5.5
        }

async def cmd_futures_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /futures_signals command with improved global metrics"""
    user_id = update.effective_user.id
    coins = [c.upper() for c in (context.args or [])]
    threshold = 75.0  # High confidence threshold

    print(f"🚨 /futures_signals from user {user_id} - coins: {coins}")

    try:
        rep = await build_futures_signals_report(coins or None, threshold=threshold)
        text = format_futures_signals_html(rep)
        await safe_reply(update, text, prefer_html=True)
    except Exception as e:
        print(f"❌ Error in futures_signals command: {e}")
        await safe_reply(update,
            "❌ Terjadi kesalahan mengambil data untuk FUTURES_SIGNALS\n\n"
            f"🔄 Error context: {e}",
            prefer_html=True
        )

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze command - SPOT analysis without Entry"""
    user_id = update.effective_user.id
    symbol = (context.args[0] if context.args else "BTC").upper()

    print(f"🔍 /analyze {symbol} from user {user_id}")

    try:
        # SPOT analysis (tanpa Entry)
        from app.services.analysis import analyze_coin
        res = await analyze_coin(symbol)
        
        # Map untuk formatter (tanpa Entry)
        item = {k: res.get(k) for k in ["coin", "trend", "structure", "reason", "rsi", "macd_hist", "change_24h", "rr", "stop", "tp1", "tp2", "confidence"] if k in res}
        
        formatted_text = format_signal_card(item, include_entry=False)  # NO Entry line
        await safe_reply(update, formatted_text, prefer_html=False)   # Markdown OK

    except Exception as e:
        print(f"❌ Error in analyze command: {e}")
        await safe_reply(update, "❌ Gagal menganalisis koin.")

async def cmd_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /futures command - PERP analysis with Entry"""
    user_id = update.effective_user.id
    symbol = (context.args[0] if context.args else "BTC").upper()

    print(f"📊 /futures {symbol} from user {user_id}")

    try:
        # PERP analysis (dengan Entry)
        from app.services.analysis import analyze_coin_futures
        res = await analyze_coin_futures(symbol)  # entry tunggal + SL/TP/TP2/RR
        
        formatted_text = format_signal_card(res, include_entry=True)
        await safe_reply(update, formatted_text, prefer_html=False)

    except Exception as e:
        print(f"❌ Error in futures command: {e}")
        await safe_reply(update, "❌ Gagal mengambil data futures.")

# The original cmd_futures_signals function was replaced by the new implementation above.
# The following lines are kept from the original for completeness if they were meant to be preserved.
# However, the prompt indicates the entire function is being rewritten.
# Keeping original code block for reference if needed, but it's superseded by the new implementation above.

# Original cmd_futures_signals block that was modified:
# async def cmd_futures_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle /futures_signals command"""
#     user_id = update.effective_user.id
#     coins = [c.upper() for c in (context.args or [])]
#     try:
#         if USE_LEGACY_FUTURES_SIGNALS:
#             lst = await futures_signals_legacy(coins or None)
#         else:
#             lst = await futures_signals_modern(coins or None, threshold=75.0)

#         F = None
#         try:
#             F = importlib.import_module("app.formatters.texts")
#         except Exception:
#             pass

#         if F and hasattr(F, "format_futures_signals"):
#             text = F.format_futures_signals(lst)
#         else:
#             lines = ["🚨 **FUTURES SIGNALS**"]
#             if not lst:
#                 lines += ["❌ Tidak ada sinyal"]
#             else:
#                 for it in lst:
#                     if "error" in it:
#                         lines.append(f"- {it['coin']}: ❌ error")
#                         continue
#                     entry = it.get('entry', 0)
#                     rsi = it.get('rsi', 0)
#                     macd_hist = it.get('macd_hist', 0)
#                     trend = it.get('trend', 'Unknown')
#                     lines.append(
#                         f"- **{it['coin']}**: Entry {entry:.4f} | "
#                         f"RSI {rsi:.1f} | MACD {macd_hist:.4f} | {trend}"
#                     )
#             text = "\n".join(lines)

#         await safe_reply(update, text)
#     except Exception as e:
#         error_msg = (
#             "❌ Terjadi kesalahan mengambil data untuk FUTURES_SIGNALS\n\n"
#             "🔄 Error context: legacy mode\n"
#             f"Error: {str(e)[:100]}\n"
#             "💡 Coba: /price btc — Cek harga basic"
#         )
#         await safe_reply(update, error_msg)


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /market command"""
    user_id = update.effective_user.id
    syms = [s.upper() for s in (context.args or [])]

    print(f"📊 /market from user {user_id} - symbols: {syms}")

    try:
        # Build comprehensive market report
        rep = await build_market_report(symbols=syms or None)

        # Format with HTML support
        text = format_market_report(rep)

        # Send with HTML formatting
        await safe_reply(update, text, prefer_html=True)

        print(f"✅ Market analysis completed, sending response ({len(text)} chars)")

    except Exception as e:
        print(f"❌ Error in market command: {e}")
        await safe_reply(update,
            f"❌ Terjadi kesalahan saat menganalisis pasar.\n\n"
            f"Error: {str(e)[:100]}...\n\n"
            "🔄 Silakan coba lagi dalam beberapa menit.\n"
            "💡 Pastikan CMC_API_KEY tersedia untuk data optimal.",
            prefer_html=False
        )