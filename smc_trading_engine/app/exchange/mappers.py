from __future__ import annotations

from datetime import datetime, timezone

from app.core.models import AccountInfo, Candle, OrderResult, Position


def map_candle_row(row: dict) -> Candle:
    ts = row.get("timestamp") or row.get("ts") or row.get("time") or datetime.now(timezone.utc).isoformat()
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(float(ts) / (1000.0 if ts > 10_000_000_000 else 1.0), tz=timezone.utc)
    else:
        ts = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return Candle(
        timestamp=ts,
        open=float(row.get("open", 0)),
        high=float(row.get("high", 0)),
        low=float(row.get("low", 0)),
        close=float(row.get("close", 0)),
        volume=float(row.get("volume", 0)),
    )


def map_position(row: dict) -> Position:
    return Position(
        symbol=str(row.get("symbol", "")),
        side="LONG" if str(row.get("side", "LONG")).upper() in ("BUY", "LONG") else "SHORT",
        entry_price=float(row.get("entry_price", row.get("entryPrice", 0))),
        size=abs(float(row.get("size", row.get("amount", 0)))),
        leverage=int(row.get("leverage", 1) or 1),
        unrealized_pnl=float(row.get("unrealized_pnl", row.get("unrealizedPnl", 0)) or 0),
        opened_at=datetime.now(timezone.utc),
    )


def map_account_info(row: dict) -> AccountInfo:
    return AccountInfo(
        equity=float(row.get("equity", row.get("balance", 0)) or 0),
        available_balance=float(row.get("available_balance", row.get("available", 0)) or 0),
        used_margin=float(row.get("used_margin", row.get("margin", 0)) or 0),
        unrealized_pnl=float(row.get("unrealized_pnl", row.get("total_unrealized_pnl", 0)) or 0),
    )


def map_order_result(success: bool, symbol: str, payload: dict | None = None, message: str = "") -> OrderResult:
    p = payload or {}
    return OrderResult(
        success=success,
        order_id=str(p.get("order_id") or p.get("id") or "") or None,
        symbol=symbol,
        status=str(p.get("status") or ("ok" if success else "failed")),
        message=message or str(p.get("message") or ""),
        raw_metadata=p,
    )
