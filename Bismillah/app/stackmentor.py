"""
StackMentor System - Advanced 3-Tier TP Strategy
Maximize trading volume with incremental profit taking and breakeven protection

Strategy:
- TP1 (60%): R:R 1:2 → Close 60%, Move SL to Breakeven
- TP2 (30%): R:R 1:3 → Close 30%, Keep SL at Breakeven  
- TP3 (10%): R:R 1:5 → Close 10%, Ride the trend

For ALL users (not premium only)
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# StackMentor Configuration
STACKMENTOR_CONFIG = {
    "enabled": True,           # Enable for all users
    "tp1_pct": 0.60,          # 60% at TP1
    "tp2_pct": 0.30,          # 30% at TP2
    "tp3_pct": 0.10,          # 10% at TP3
    "tp1_rr": 2.0,            # R:R 1:2
    "tp2_rr": 3.0,            # R:R 1:3
    "tp3_rr": 5.0,            # R:R 1:5 (changed from 1:10)
    "breakeven_after_tp1": True,
}

# Track StackMentor positions: user_id → {symbol: position_data}
_stackmentor_positions: Dict[int, Dict[str, Dict]] = {}


def calculate_stackmentor_levels(
    entry_price: float,
    sl_price: float,
    side: str
) -> Tuple[float, float, float]:
    """
    Calculate 3-tier TP levels based on SL distance
    
    Returns: (tp1, tp2, tp3)
    """
    cfg = STACKMENTOR_CONFIG
    
    # Calculate SL distance
    sl_distance = abs(entry_price - sl_price)
    
    if side == "LONG":
        tp1 = entry_price + (sl_distance * cfg["tp1_rr"])
        tp2 = entry_price + (sl_distance * cfg["tp2_rr"])
        tp3 = entry_price + (sl_distance * cfg["tp3_rr"])
    else:  # SHORT
        tp1 = entry_price - (sl_distance * cfg["tp1_rr"])
        tp2 = entry_price - (sl_distance * cfg["tp2_rr"])
        tp3 = entry_price - (sl_distance * cfg["tp3_rr"])
    
    return (tp1, tp2, tp3)


def calculate_qty_splits(total_qty: float, precision: int = 3) -> Tuple[float, float, float]:
    """
    Split quantity into 3 tiers: 60%, 30%, 10%
    Dynamically infers max precision from total_qty to prevent rounding errors
    from breaking percentage expectations.
    
    Returns: (qty_tp1, qty_tp2, qty_tp3)
    """
    cfg = STACKMENTOR_CONFIG
    
    # Analyze the actual precision of total_qty
    qty_str = f"{total_qty:.8f}".rstrip('0')
    if '.' in qty_str:
        actual_prec = len(qty_str.split('.')[1])
        precision = max(precision, actual_prec)
    
    qty_tp1 = round(total_qty * cfg["tp1_pct"], precision)
    qty_tp2 = round(total_qty * cfg["tp2_pct"], precision)
    
    # Give remaining directly to tp3 to ensure total sum is perfectly equal
    qty_tp3 = round(total_qty - qty_tp1 - qty_tp2, precision)
    
    return (qty_tp1, qty_tp2, qty_tp3)


def register_stackmentor_position(
    user_id: int,
    symbol: str,
    entry_price: float,
    sl_price: float,
    tp1: float,
    tp2: float,
    tp3: float,
    total_qty: float,
    qty_tp1: float,
    qty_tp2: float,
    qty_tp3: float,
    side: str,
    leverage: int
):
    """Register a new StackMentor position for monitoring"""
    if user_id not in _stackmentor_positions:
        _stackmentor_positions[user_id] = {}
    
    _stackmentor_positions[user_id][symbol] = {
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "total_qty": total_qty,
        "qty_tp1": qty_tp1,
        "qty_tp2": qty_tp2,
        "qty_tp3": qty_tp3,
        "side": side,
        "leverage": leverage,
        "tp1_hit": False,
        "tp2_hit": False,
        "tp3_hit": False,
        "breakeven_mode": False,
        "opened_at": datetime.utcnow(),
    }
    
    logger.info(
        f"[StackMentor:{user_id}] Registered {symbol} {side} — "
        f"TP1={tp1:.4f} TP2={tp2:.4f} TP3={tp3:.4f}"
    )


def get_stackmentor_position(user_id: int, symbol: str) -> Optional[Dict]:
    """Get StackMentor position data"""
    if user_id not in _stackmentor_positions:
        return None
    return _stackmentor_positions[user_id].get(symbol)


def remove_stackmentor_position(user_id: int, symbol: str):
    """Remove StackMentor position (fully closed)"""
    if user_id in _stackmentor_positions:
        _stackmentor_positions[user_id].pop(symbol, None)
        logger.info(f"[StackMentor:{user_id}] Removed {symbol} from monitoring")


async def monitor_stackmentor_positions(bot, user_id: int, client, notify_chat_id: int):
    """
    Monitor StackMentor positions for TP hits
    Called from main trade loop every scan interval
    """
    if user_id not in _stackmentor_positions:
        return
    
    positions = _stackmentor_positions[user_id].copy()
    
    for symbol, pos_data in positions.items():
        try:
            # Get current mark price
            ticker_result = await asyncio.to_thread(client.get_ticker, symbol)
            if not ticker_result.get('success'):
                continue
            
            mark_price = float(ticker_result.get('mark_price', 0))
            if mark_price == 0:
                continue
            
            side = pos_data['side']
            
            # Check TP1 hit (trigger breakeven)
            if not pos_data['tp1_hit']:
                tp1_hit = (side == "LONG" and mark_price >= pos_data['tp1']) or \
                          (side == "SHORT" and mark_price <= pos_data['tp1'])
                
                if tp1_hit:
                    await handle_tp1_hit(bot, user_id, client, notify_chat_id, symbol, pos_data, mark_price)
            
            # Check TP2 hit
            elif not pos_data['tp2_hit']:
                tp2_hit = (side == "LONG" and mark_price >= pos_data['tp2']) or \
                          (side == "SHORT" and mark_price <= pos_data['tp2'])
                
                if tp2_hit:
                    await handle_tp2_hit(bot, user_id, client, notify_chat_id, symbol, pos_data, mark_price)
            
            # Check TP3 hit
            elif not pos_data['tp3_hit']:
                tp3_hit = (side == "LONG" and mark_price >= pos_data['tp3']) or \
                          (side == "SHORT" and mark_price <= pos_data['tp3'])
                
                if tp3_hit:
                    await handle_tp3_hit(bot, user_id, client, notify_chat_id, symbol, pos_data, mark_price)
        
        except Exception as e:
            logger.error(f"[StackMentor:{user_id}] Monitor error {symbol}: {e}")


async def handle_tp1_hit(bot, user_id: int, client, notify_chat_id: int, 
                        symbol: str, pos_data: Dict, mark_price: float):
    """
    TP1 Hit: Close 60%, Move SL to Breakeven
    """
    logger.warning(f"[StackMentor:{user_id}] TP1 HIT {symbol} @ {mark_price:.4f}")
    
    entry = pos_data['entry_price']
    side = pos_data['side']
    qty_tp1 = pos_data['qty_tp1']
    
    # 1. Close 60% position
    close_side = "SELL" if side == "LONG" else "BUY"
    close_result = await asyncio.to_thread(
        client.place_order,
        symbol,
        close_side,
        qty_tp1,
        order_type='market',
        reduce_only=True
    )
    
    if not close_result.get('success'):
        logger.error(f"[StackMentor:{user_id}] TP1 close failed: {close_result.get('error')}")
        return
    
    logger.info(f"[StackMentor:{user_id}] TP1 closed 50% @ {mark_price:.4f}")
    
    # 2. Move SL to breakeven
    await asyncio.sleep(0.5)  # Give exchange time to process
    
    # 2.1 Validate breakeven SL before setting (prevent error 30029)
    try:
        # Get current mark price to validate breakeven SL
        ticker_result = await asyncio.to_thread(client.get_ticker, symbol)
        if ticker_result.get('success'):
            current_mark_price = float(ticker_result.get('mark_price', mark_price))
            
            # Validate breakeven SL based on side
            sl_valid = True
            if side == "LONG":
                # For LONG: breakeven SL must be BELOW current mark price
                if entry >= current_mark_price:
                    logger.warning(
                        f"[StackMentor:{user_id}] Cannot set breakeven SL for LONG: "
                        f"entry {entry:.4f} >= mark {current_mark_price:.4f} "
                        f"(market dropped below entry, keeping original SL)"
                    )
                    sl_valid = False
            else:  # SHORT
                # For SHORT: breakeven SL must be ABOVE current mark price
                if entry <= current_mark_price:
                    logger.warning(
                        f"[StackMentor:{user_id}] Cannot set breakeven SL for SHORT: "
                        f"entry {entry:.4f} <= mark {current_mark_price:.4f} "
                        f"(market pumped above entry, keeping original SL)"
                    )
                    sl_valid = False
            
            # Only update SL if validation passed
            if sl_valid:
                sl_result = await asyncio.to_thread(client.set_position_sl, symbol, entry)
                
                if sl_result.get('success'):
                    logger.info(f"[StackMentor:{user_id}] SL moved to breakeven @ {entry:.4f}")
                else:
                    logger.warning(f"[StackMentor:{user_id}] SL update failed: {sl_result.get('error')}")
            else:
                # SL validation failed - notify user but don't fail the trade
                sl_result = {'success': False, 'error': 'SL validation failed - market moved too far'}
        else:
            # Couldn't get ticker - try to set SL anyway (will fail gracefully if invalid)
            logger.warning(f"[StackMentor:{user_id}] Couldn't validate SL, attempting to set anyway")
            sl_result = await asyncio.to_thread(client.set_position_sl, symbol, entry)
    except Exception as sl_err:
        logger.error(f"[StackMentor:{user_id}] SL validation/update error: {sl_err}")
        sl_result = {'success': False, 'error': str(sl_err)}
    
    # 3. Update position data
    pos_data['tp1_hit'] = True
    pos_data['tp1_hit_at'] = datetime.utcnow()
    pos_data['breakeven_mode'] = True
    pos_data['sl_price'] = entry
    
    # 4. Update database
    try:
        from app.supabase_repo import _client
        profit_tp1 = abs(mark_price - entry) * qty_tp1
        
        _client().table("autotrade_trades").update({
            "tp1_hit": True,
            "tp1_hit_at": datetime.utcnow().isoformat(),
            "breakeven_mode": True,
            "sl_price": entry,
            "profit_tp1": profit_tp1,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", user_id).eq("symbol", symbol).eq("status", "open").execute()
    except Exception as e:
        logger.error(f"[StackMentor:{user_id}] DB update failed: {e}")
    
    # 5. Notify user
    profit_pct = abs(mark_price - entry) / entry * 100 * pos_data['leverage']
    
    # Build SL status message
    if sl_result.get('success'):
        sl_status = "✅ Stop Loss dipindah ke Breakeven"
        sl_detail = (
            f"📍 Harga Breakeven: <code>{entry:.4f}</code>\n"
            f"💡 Artinya: Jika market berbalik, posisi akan ditutup di harga entry (tidak rugi)"
        )
    else:
        sl_error = sl_result.get('error', 'Unknown error')
        if 'market moved too far' in sl_error or 'validation failed' in sl_error:
            sl_status = "⚠️ Stop Loss tetap di level awal"
            sl_detail = (
                "Market bergerak terlalu cepat - SL breakeven tidak bisa diset.\n"
                "Tapi tenang, 60% profit sudah terkunci!"
            )
        else:
            sl_status = "⚠️ Gagal update Stop Loss"
            sl_detail = f"Tapi 60% profit sudah aman! Error: {sl_error[:50]}"
    
    await bot.send_message(
        chat_id=notify_chat_id,
        text=(
            f"🎯 <b>Target Profit 1 Tercapai! — {symbol}</b>\n\n"
            f"✅ Tutup 60% posisi @ <code>{mark_price:.4f}</code>\n"
            f"💰 Profit terkunci: <b>+${profit_tp1:.2f} USDT</b> (+{profit_pct:.1f}%)\n\n"
            f"🔒 <b>{sl_status}</b>\n"
            f"{sl_detail}\n\n"
            f"⏳ Sisa 40% posisi masih berjalan ke TP2 & TP3...\n\n"
            f"💡 <b>Apa artinya?</b>\n"
            f"{'✅ Posisi Anda sekarang BEBAS RISIKO! Bahkan jika market berbalik, Anda tidak akan rugi.' if sl_result.get('success') else '⚠️ SL masih di level awal. Profit sudah terkunci 60%.'}\n\n"
            f"🎯 StackMentor: Strategi profit bertahap untuk maksimalkan hasil!"
        ),
        parse_mode='HTML'
    )


async def handle_tp2_hit(bot, user_id: int, client, notify_chat_id: int,
                        symbol: str, pos_data: Dict, mark_price: float):
    """
    TP2 Hit: Close 30% of original position
    """
    logger.warning(f"[StackMentor:{user_id}] TP2 HIT {symbol} @ {mark_price:.4f}")
    
    entry = pos_data['entry_price']
    side = pos_data['side']
    qty_tp2 = pos_data['qty_tp2']
    
    # Close 30%
    close_side = "SELL" if side == "LONG" else "BUY"
    close_result = await asyncio.to_thread(
        client.place_order,
        symbol,
        close_side,
        qty_tp2,
        order_type='market',
        reduce_only=True
    )
    
    if not close_result.get('success'):
        logger.error(f"[StackMentor:{user_id}] TP2 close failed: {close_result.get('error')}")
        return
    
    logger.info(f"[StackMentor:{user_id}] TP2 closed 40% @ {mark_price:.4f}")
    
    # Update position data
    pos_data['tp2_hit'] = True
    pos_data['tp2_hit_at'] = datetime.utcnow()
    
    # Update database
    try:
        from app.supabase_repo import _client
        profit_tp2 = abs(mark_price - entry) * qty_tp2
        
        _client().table("autotrade_trades").update({
            "tp2_hit": True,
            "tp2_hit_at": datetime.utcnow().isoformat(),
            "profit_tp2": profit_tp2,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", user_id).eq("symbol", symbol).eq("status", "open").execute()
    except Exception as e:
        logger.error(f"[StackMentor:{user_id}] DB update failed: {e}")
    
    # Notify user
    profit_pct = abs(mark_price - entry) / entry * 100 * pos_data['leverage']
    
    await bot.send_message(
        chat_id=notify_chat_id,
        text=(
            f"🎯🎯 <b>Target Profit 2 Tercapai! — {symbol}</b>\n\n"
            f"✅ Tutup 30% posisi @ <code>{mark_price:.4f}</code>\n"
            f"💰 Profit tambahan: <b>+${profit_tp2:.2f} USDT</b> (+{profit_pct:.1f}%)\n\n"
            f"🔒 SL tetap di breakeven (entry price)\n"
            f"⏳ Sisa 10% terakhir menuju TP3 (target 1:5)...\n\n"
            f"💡 <b>Status:</b>\n"
            f"✅ 90% posisi sudah ditutup dengan profit\n"
            f"✅ 10% terakhir = bonus jika market terus naik\n"
            f"✅ Tidak ada risiko rugi (SL di breakeven)\n\n"
            f"🎯 StackMentor: Profit aman, bonus masih jalan!"
        ),
        parse_mode='HTML'
    )


async def handle_tp3_hit(bot, user_id: int, client, notify_chat_id: int,
                        symbol: str, pos_data: Dict, mark_price: float):
    """
    TP3 Hit: Close final 10% - JACKPOT!
    """
    logger.warning(f"[StackMentor:{user_id}] TP3 HIT {symbol} @ {mark_price:.4f} — JACKPOT!")
    
    entry = pos_data['entry_price']
    side = pos_data['side']
    qty_tp3 = pos_data['qty_tp3']
    
    # Close final 10%
    close_side = "SELL" if side == "LONG" else "BUY"
    close_result = await asyncio.to_thread(
        client.place_order,
        symbol,
        close_side,
        qty_tp3,
        order_type='market',
        reduce_only=True
    )
    
    if not close_result.get('success'):
        logger.error(f"[StackMentor:{user_id}] TP3 close failed: {close_result.get('error')}")
        return
    
    logger.info(f"[StackMentor:{user_id}] TP3 closed 10% @ {mark_price:.4f}")
    
    # Calculate total profit
    total_qty = pos_data['total_qty']
    profit_tp1 = abs(pos_data['tp1'] - entry) * pos_data['qty_tp1']
    profit_tp2 = abs(pos_data['tp2'] - entry) * pos_data['qty_tp2']
    profit_tp3 = abs(mark_price - entry) * qty_tp3
    total_profit = profit_tp1 + profit_tp2 + profit_tp3
    
    # Update position data
    pos_data['tp3_hit'] = True
    pos_data['tp3_hit_at'] = datetime.utcnow()
    
    # Update database - position fully closed
    try:
        from app.supabase_repo import _client
        
        _client().table("autotrade_trades").update({
            "tp3_hit": True,
            "tp3_hit_at": datetime.utcnow().isoformat(),
            "profit_tp3": profit_tp3,
            "pnl_usdt": total_profit,
            "status": "closed_tp3",
            "closed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", user_id).eq("symbol", symbol).eq("status", "open").execute()
    except Exception as e:
        logger.error(f"[StackMentor:{user_id}] DB update failed: {e}")
    
    # Remove from monitoring
    remove_stackmentor_position(user_id, symbol)
    
    # Notify user - CELEBRATION!
    profit_pct = abs(mark_price - entry) / entry * 100 * pos_data['leverage']
    
    await bot.send_message(
        chat_id=notify_chat_id,
        text=(
            f"🎉🎉🎉 <b>JACKPOT! Target Profit 3 Tercapai! — {symbol}</b>\n\n"
            f"✅ Tutup 10% terakhir @ <code>{mark_price:.4f}</code>\n"
            f"💰 Profit TP3: <b>+${profit_tp3:.2f} USDT</b> (+{profit_pct:.1f}%)\n\n"
            f"🏆 <b>TOTAL PROFIT TRADE INI:</b>\n"
            f"💵 <b>+${total_profit:.2f} USDT</b>\n\n"
            f"📊 <b>Rincian Profit Bertahap:</b>\n"
            f"• TP1 (60% posisi): +${profit_tp1:.2f} ✅\n"
            f"• TP2 (30% posisi): +${profit_tp2:.2f} ✅\n"
            f"• TP3 (10% posisi): +${profit_tp3:.2f} ✅\n\n"
            f"💡 <b>Kenapa strategi ini bagus?</b>\n"
            f"✅ Profit dikunci bertahap (tidak serakah)\n"
            f"✅ Risiko diminimalkan (SL ke breakeven)\n"
            f"✅ Tetap dapat bonus jika market lanjut naik\n\n"
            f"🎯 StackMentor: Eksekusi sempurna! Semua target tercapai! 🔥"
        ),
        parse_mode='HTML'
    )
    
    # Broadcast big wins (≥$10)
    if total_profit >= 10.0:
        try:
            from app.social_proof import broadcast_profit
            from app.supabase_repo import get_user_by_tid
            
            user_data = get_user_by_tid(user_id)
            fname = user_data.get("first_name", "User") if user_data else "User"
            
            asyncio.create_task(broadcast_profit(
                bot=bot,
                user_id=user_id,
                first_name=fname,
                symbol=symbol,
                side=side,
                pnl_usdt=total_profit,
                leverage=pos_data['leverage'],
            ))
        except Exception as e:
            logger.warning(f"[StackMentor:{user_id}] Broadcast failed: {e}")
