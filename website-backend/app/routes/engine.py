"""
Engine control endpoints — start/stop/state the autotrade engine.
Runs on same VPS as Telegram bot, shares the same Python modules.
"""

import os
import sys
import importlib.util
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_token
from app.db.supabase import _client

router = APIRouter(prefix="/dashboard/engine", tags=["engine"])
bearer = HTTPBearer()

# ── Bismillah path injection ────────────────────────────────────────────────
# IMPORTANT: Bismillah root MUST be first in sys.path so that
# `from app.X import ...` inside autotrade_engine resolves to
# Bismillah/app/X, NOT website-backend/app/X.
_BISMILLAH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "Bismillah")
)
_BISMILLAH_APP = os.path.join(_BISMILLAH, "app")

# Force Bismillah root to position 0 so its `app` package wins
if _BISMILLAH in sys.path:
    sys.path.remove(_BISMILLAH)
sys.path.insert(0, _BISMILLAH)

if _BISMILLAH_APP not in sys.path:
    sys.path.insert(1, _BISMILLAH_APP)


def _load_bismillah_submodule(rel_name: str, alias: str):
    """Load a Bismillah app submodule by file path and register it under
    both `alias` (e.g. 'bismillah.app.stackmentor') AND the short
    `app.<rel_name>` key so that internal `from app.X import ...` calls
    inside autotrade_engine resolve to the Bismillah version rather than
    the web backend's own `app` package.
    """
    short_key = f"app.{rel_name}"
    if short_key in sys.modules:
        return sys.modules[short_key]

    file_path = os.path.join(_BISMILLAH_APP, f"{rel_name}.py")
    if not os.path.isfile(file_path):
        return None  # optional module — skip silently

    spec = importlib.util.spec_from_file_location(alias, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    sys.modules[short_key] = mod   # <-- this is the key fix
    spec.loader.exec_module(mod)
    return mod


def _get_engine():
    """
    Load autotrade_engine from its absolute path using importlib.

    Root cause of 'No module named app.stackmentor':
    sys.modules['app'] is already the web-backend package. When
    autotrade_engine.py runs `from app.stackmentor import ...`, Python
    resolves `app` to the web backend and fails to find `stackmentor`.

    Fix: pre-register each Bismillah app.* submodule that the engine (and
    its transitive imports) needs under *both* 'bismillah.app.X' and the
    bare 'app.X' key. Subsequent imports hit sys.modules directly — the
    web backend's `app` package is never consulted for these names.
    """
    module_path = os.path.join(_BISMILLAH_APP, "autotrade_engine.py")
    if not os.path.isfile(module_path):
        raise ImportError(f"autotrade_engine.py not found at: {module_path}")

    # Reuse cached module to preserve in-memory _running_tasks state.
    if "bismillah.autotrade_engine" in sys.modules:
        return sys.modules["bismillah.autotrade_engine"]

    # Pre-load every app.* module the engine or its deps import.
    # Order matters: leaves first (no internal app.* deps), then consumers.
    for submod in ("trading_mode", "supabase_repo", "stackmentor", "scalping_engine"):
        _load_bismillah_submodule(submod, f"bismillah.app.{submod}")

    spec = importlib.util.spec_from_file_location("bismillah.autotrade_engine", module_path)
    ae = importlib.util.module_from_spec(spec)
    sys.modules["bismillah.autotrade_engine"] = ae
    spec.loader.exec_module(ae)
    return ae


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
        ae = _get_engine()
        running = ae.is_running(tg_id)
    except Exception:
        running = session.get("engine_active", False) and session.get("status") == "active"
    return {
        "running": running,
        "status": session.get("status", "unknown"),
        "engine_active": session.get("engine_active", False),
        "trading_mode": session.get("trading_mode", "swing"),
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

    # Load engine module once — reused for is_running check + start_engine call
    try:
        ae = _get_engine()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine module error: {e}")

    if ae.is_running(tg_id):
        return {"running": True, "message": "Engine already running."}

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
        ae = _get_engine()
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
