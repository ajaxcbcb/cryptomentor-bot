from __future__ import annotations

import json
from datetime import datetime, timezone

from app.storage.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_decision(symbol: str, action: str, direction: str, confidence: float, reason: str, payload: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO decisions(ts,symbol,action,direction,confidence,reason,payload_json) VALUES (?,?,?,?,?,?,?)",
            (_now(), symbol, action, direction, confidence, reason, json.dumps(payload)),
        )
        conn.commit()
    finally:
        conn.close()


def insert_execution(symbol: str, success: bool, message: str, payload: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO executions(ts,symbol,success,message,payload_json) VALUES (?,?,?,?,?)",
            (_now(), symbol, 1 if success else 0, message, json.dumps(payload)),
        )
        conn.commit()
    finally:
        conn.close()


def upsert_status(symbol: str, market_state: str, confidence: float, action: str, reason: str, payload: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO analytics_status(symbol,updated_at,market_state,confidence,action,reason,payload_json)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(symbol) DO UPDATE SET
                updated_at=excluded.updated_at,
                market_state=excluded.market_state,
                confidence=excluded.confidence,
                action=excluded.action,
                reason=excluded.reason,
                payload_json=excluded.payload_json
            """,
            (symbol, _now(), market_state, confidence, action, reason, json.dumps(payload)),
        )
        conn.commit()
    finally:
        conn.close()


def get_status(symbol: str | None = None) -> list[dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if symbol:
            rows = cur.execute("SELECT * FROM analytics_status WHERE symbol=?", (symbol,)).fetchall()
        else:
            rows = cur.execute("SELECT * FROM analytics_status ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_open_positions() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM positions").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_executions(limit: int = 100) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM executions ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
