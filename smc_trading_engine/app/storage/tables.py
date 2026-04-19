from __future__ import annotations

from app.storage.db import get_connection


DDL = [
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        symbol TEXT NOT NULL,
        action TEXT NOT NULL,
        direction TEXT NOT NULL,
        confidence REAL NOT NULL,
        reason TEXT NOT NULL,
        payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        symbol TEXT NOT NULL,
        success INTEGER NOT NULL,
        message TEXT,
        payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
        symbol TEXT PRIMARY KEY,
        side TEXT NOT NULL,
        size REAL NOT NULL,
        entry_price REAL NOT NULL,
        opened_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics_status (
        symbol TEXT PRIMARY KEY,
        updated_at TEXT NOT NULL,
        market_state TEXT,
        confidence REAL,
        action TEXT,
        reason TEXT,
        payload_json TEXT NOT NULL
    )
    """,
]


def ensure_tables() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        for sql in DDL:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()
