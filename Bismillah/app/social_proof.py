"""
Social Proof System
Broadcast profit besar ke semua user untuk meningkatkan konversi.
Threshold: profit >= MIN_BROADCAST_PROFIT USDT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum profit untuk di-broadcast ke semua user
MIN_BROADCAST_PROFIT = 5.0  # USDT

# Cooldown per user: jangan broadcast terlalu sering dari user yang sama
_last_broadcast: dict = {}  # user_id -> timestamp
BROADCAST_COOLDOWN_HOURS = 4


def _should_broadcast(user_id: int, pnl_usdt: float) -> bool:
    """Cek apakah profit ini layak di-broadcast."""
    if pnl_usdt < MIN_BROADCAST_PROFIT:
        return False
    last = _last_broadcast.get(user_id)
    if last:
        elapsed = (datetime.utcnow() - last).total_seconds() / 3600
        if elapsed < BROADCAST_COOLDOWN_HOURS:
            return False
    return True


async def broadcast_profit(
    bot,
    user_id: int,
    first_name: str,
    symbol: str,
    side: str,
    pnl_usdt: float,
    leverage: int,
):
    """
    Broadcast notifikasi profit ke semua user yang BELUM menggunakan autotrade.
    Dipanggil dari autotrade_engine saat trade close dengan profit besar.
    """
    if not _should_broadcast(user_id, pnl_usdt):
        return

    _last_broadcast[user_id] = datetime.utcnow()

    # Format nama: sensor untuk privacy
    display_name = _mask_name(first_name)
    emoji = "🟢" if side == "LONG" else "🔴"
    direction = "LONG ↑" if side == "LONG" else "SHORT ↓"

    message = (
        f"🔥 <b>Trade Profit Alert!</b>\n\n"
        f"👤 User <b>{display_name}</b> baru saja profit:\n\n"
        f"{emoji} <b>{symbol}</b> {direction}\n"
        f"💰 Profit: <b>+{pnl_usdt:.2f} USDT</b>\n"
        f"⚡ Leverage: {leverage}x\n\n"
        f"🤖 <i>Dieksekusi otomatis oleh CryptoMentor AI</i>\n\n"
        f"💡 Mau bot trading juga buat kamu?\n"
        f"Ketik /autotrade untuk mulai!"
    )

    # Kirim ke semua user yang BELUM daftar autotrade
    asyncio.create_task(_send_to_all_users(bot, message))
    logger.info(f"[SocialProof] Queued broadcast for {display_name} profit ${pnl_usdt:.2f}")


async def _send_to_all_users(bot, message: str):
    """Kirim pesan ke user yang BELUM daftar autotrade saja."""
    try:
        from app.supabase_repo import _client

        def _get_target_uids():
            s = _client()
            # Ambil semua user
            all_uids = []
            offset = 0
            while True:
                res = s.table("users").select("telegram_id").range(offset, offset + 999).execute()
                batch = res.data or []
                all_uids.extend(row["telegram_id"] for row in batch)
                if len(batch) < 1000:
                    break
                offset += 1000

            # Ambil user yang sudah punya autotrade session
            at_res = s.table("autotrade_sessions").select("telegram_id").execute()
            at_ids = {row["telegram_id"] for row in (at_res.data or [])}

            # Hanya kirim ke yang belum daftar
            return [uid for uid in all_uids if uid not in at_ids]

        target_uids = await asyncio.to_thread(_get_target_uids)
        logger.info(f"[SocialProof] Broadcasting to {len(target_uids)} non-autotrade users")

        sent = 0
        failed = 0
        for uid in target_uids:
            try:
                await bot.send_message(chat_id=uid, text=message, parse_mode='HTML')
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1

        logger.info(f"[SocialProof] Broadcast done: {sent} ok, {failed} failed")

    except Exception as e:
        logger.error(f"[SocialProof] Broadcast failed: {e}")


def _mask_name(name: str) -> str:
    """
    Sensor username untuk privacy.
    Examples:
    - 'Budi' → 'B***i'
    - 'Budi Santoso' → 'B***i S***o'
    - 'John' → 'J***n'
    - 'A' → 'A***'
    """
    if not name:
        return "User***"
    
    parts = name.strip().split()
    masked_parts = []
    
    for part in parts:
        if len(part) <= 1:
            # Single character: 'A' → 'A***'
            masked_parts.append(part + "***")
        elif len(part) == 2:
            # Two characters: 'Jo' → 'J***o'
            masked_parts.append(part[0] + "***" + part[1])
        elif len(part) == 3:
            # Three characters: 'Bob' → 'B***b'
            masked_parts.append(part[0] + "***" + part[-1])
        else:
            # Four or more: 'John' → 'J***n', 'Budi' → 'B***i'
            masked_parts.append(part[0] + "***" + part[-1])
    
    return " ".join(masked_parts)


async def get_platform_stats() -> dict:
    """
    Ambil statistik platform untuk ditampilkan di welcome message.
    Return: total_users, active_traders, total_profit_month, total_trades_month
    """
    try:
        import asyncio as _asyncio
        from app.supabase_repo import _client

        def _fetch():
            s = _client()
            total_res = s.table("users").select("telegram_id", count="exact").execute()
            total_users = total_res.count or 0

            active_res = s.table("autotrade_sessions").select("telegram_id", count="exact").eq("status", "active").execute()
            active_traders = active_res.count or 0

            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0).isoformat()
            profit_res = s.table("autotrade_trades").select("pnl_usdt").eq("status", "closed_tp").gte("closed_at", month_start).execute()
            total_profit = sum(float(r.get("pnl_usdt", 0)) for r in (profit_res.data or []) if r.get("pnl_usdt"))

            trades_res = s.table("autotrade_trades").select("id", count="exact").gte("opened_at", month_start).execute()
            total_trades = trades_res.count or 0

            return {
                "total_users": total_users,
                "active_traders": active_traders,
                "total_profit_month": total_profit,
                "total_trades_month": total_trades,
            }

        return await _asyncio.to_thread(_fetch)

    except Exception as e:
        logger.error(f"[SocialProof] get_platform_stats failed: {e}")
        return {
            "total_users": 0,
            "active_traders": 0,
            "total_profit_month": 0,
            "total_trades_month": 0,
        }
