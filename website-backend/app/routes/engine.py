"""
Engine control endpoints — start/stop/state the autotrade engine.
Runs on same VPS as Telegram bot, shares the same Python modules.
"""

import os
import sys
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_token
from app.db.supabase import _client

router = APIRouter(prefix="/dashboard/engine", tags=["engine"])
bearer = HTTPBearer()

# Add Bismillah root + Bismillah/app to sys.path so we can import bot modules directly
_BISMILLAH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "Bismillah")
)
_BISMILLAH_APP = os.path.join(_BISMILLAH, "app")
for _p in [_BISMILLAH, _BISMILLAH_APP]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


def _get_session(tg_id: int) -> dict:
    res = _client().table("autotrade_sessions").select("*").eq(
        "telegram_id", tg_id
    ).limit(1).execute()
    return res.data[0] if res.data else {}


@router.get("/state")
async def engine_state(tg_id: int = Depends(get_current_user)):
    session = _get_session(tg_id)
    try:
        # autotrade_engine is at Bismillah/app/autotrade_engine.py
        import autotrade_engine as ae
        running = ae.is_running(tg_id)
    except Exception:
        running = session.get("engine_active", False) and session.get("status") == "active"
    return {
        "running": running,
        "status": session.get("status", "unknown"),
        "engine_active": session.get("engine_active", False),
        "trading_mode": session.get("trading_mode", "scalping"),
    }


@router.post("/start")
async def engine_start(tg_id: int = Depends(get_current_user)):
    s = _client()
    session = _get_session(tg_id)
    if not session:
        raise HTTPException(status_code=404, detail="No autotrade session. Set up via Telegram bot first.")

    deposit = float(session.get("initial_deposit") or 0)
    leverage = int(session.get("leverage") or 10)
    if deposit <= 0:
        raise HTTPException(status_code=400, detail="Invalid deposit amount.")

    # Get API keys via web service (handles decrypt)
    from app.services import bitunix as bsvc
    keys = bsvc.get_user_api_keys(tg_id)
    if not keys:
        raise HTTPException(status_code=409, detail="Bitunix API keys not configured.")

    try:
        import autotrade_engine as ae
        if ae.is_running(tg_id):
            return {"running": True, "message": "Engine already running."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine module error: {e}")

    try:
        from telegram import Bot
        import os as _os
        bot_token = _os.getenv("TELEGRAM_BOT_TOKEN", "")
        bot = Bot(token=bot_token)

        try:
            import skills_repo
            is_premium = skills_repo.has_skill(tg_id, "dual_tp_rr3")
        except Exception:
            is_premium = False

        ae.start_engine(
            bot=bot,
            user_id=tg_id,
            api_key=keys["api_key"],
            api_secret=keys["api_secret"],
            amount=deposit,
            leverage=leverage,
            notify_chat_id=tg_id,
            is_premium=is_premium,
            silent=False,
            exchange_id=keys.get("exchange", "bitunix"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start engine: {e}")

    s.table("autotrade_sessions").update({
        "status": "active",
        "engine_active": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("telegram_id", tg_id).execute()

    return {"running": True, "message": "Engine started."}


@router.post("/stop")
async def engine_stop(tg_id: int = Depends(get_current_user)):
    s = _client()

    try:
        import autotrade_engine as ae
        ae.stop_engine(tg_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine module error: {e}")

    s.table("autotrade_sessions").update({
        "status": "stopped",
        "engine_active": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("telegram_id", tg_id).execute()

    # Notify user on Telegram
    try:
        from telegram import Bot
        import os as _os
        bot = Bot(token=_os.getenv("TELEGRAM_BOT_TOKEN", ""))
        await bot.send_message(
            chat_id=tg_id,
            text="🛑 <b>AutoTrade stopped via Web Dashboard.</b>\n\nUse /autotrade to restart.",
            parse_mode="HTML",
        )
    except Exception:
        pass

    return {"running": False, "message": "Engine stopped."}
