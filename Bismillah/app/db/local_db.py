
import os
import aiosqlite
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

DB_PATH = os.getenv("LOCAL_DB_PATH", "/mnt/data/app.db")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    user_id            TEXT PRIMARY KEY,
    first_name         TEXT,
    last_name          TEXT,
    username           TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS premiums (
    user_id            TEXT PRIMARY KEY,
    status             TEXT CHECK (status IN ('none','days','months','lifetime')) NOT NULL DEFAULT 'none',
    expires_at         TEXT, -- ISO timestamp; NULL untuk lifetime
    updated_at         TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credits (
    user_id            TEXT PRIMARY KEY,
    balance            INTEGER NOT NULL DEFAULT 0,
    updated_at         TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            TEXT NOT NULL,
    amount             REAL NOT NULL,
    currency           TEXT NOT NULL DEFAULT 'IDR',
    plan               TEXT, -- contoh: 'monthly', '2months', 'lifetime'
    created_at         TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    level              TEXT,
    event              TEXT,
    detail             TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);
"""

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()

# ---------- Helper ----------
def _now_iso():
    return datetime.utcnow().isoformat()

def _add_duration(start: datetime, duration_type: str, value: int) -> Optional[datetime]:
    if duration_type == "days":
        return start + timedelta(days=value)
    if duration_type == "months":
        # approx 30 days per month; sesuaikan jika butuh presisi
        return start + timedelta(days=30*value)
    return None

# ---------- CRUD ----------
async def upsert_user(user_id: str, first_name: Optional[str]=None, last_name: Optional[str]=None, username: Optional[str]=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users(user_id, first_name, last_name, username)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                username=excluded.username
        """, (str(user_id), first_name, last_name, username))
        await db.commit()

async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id, first_name, last_name, username, created_at FROM users WHERE user_id = ?", (str(user_id),))
        row = await cur.fetchone()
        return dict(zip([c[0] for c in cur.description], row)) if row else None

async def set_premium(user_id: str, duration_type: str):
    """
    duration_type: 'days', 'months', atau 'lifetime'
    """
    await ensure_premium_row(user_id)
    now = datetime.utcnow()
    expires_at = None
    status = 'none'

    if duration_type in ('days','months'):
        # default 30 hari jika tidak di-override
        expires_at = _add_duration(now, 'days' if duration_type=='days' else 'months', 1)
        status = duration_type
    elif duration_type == 'lifetime':
        status = 'lifetime'
        expires_at = None
    else:
        raise ValueError("Invalid duration_type. Use 'days', 'months', or 'lifetime'.")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE premiums
            SET status=?, expires_at=?, updated_at=?
            WHERE user_id=?
        """, (status, expires_at.isoformat() if expires_at else None, _now_iso(), str(user_id)))
        await db.commit()

async def set_premium_with_value(user_id: str, duration_type: str, value: int):
    await ensure_premium_row(user_id)
    now = datetime.utcnow()
    expires_at = None
    status = 'none'

    if duration_type in ('days','months'):
        expires_at = _add_duration(now, duration_type, value)
        status = duration_type
    elif duration_type == 'lifetime':
        status = 'lifetime'
        expires_at = None
    else:
        raise ValueError("Invalid duration_type. Use 'days', 'months', or 'lifetime'.")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE premiums
            SET status=?, expires_at=?, updated_at=?
            WHERE user_id=?
        """, (status, expires_at.isoformat() if expires_at else None, _now_iso(), str(user_id)))
        await db.commit()

async def ensure_premium_row(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO premiums(user_id, status) VALUES (?, 'none')", (str(user_id),))
        await db.commit()

async def get_premium(user_id: str) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id, status, expires_at, updated_at FROM premiums WHERE user_id=?", (str(user_id),))
        row = await cur.fetchone()
        if not row:
            return {"user_id": str(user_id), "status": "none", "expires_at": None, "updated_at": None}
        return dict(zip([c[0] for c in cur.description], row))

async def is_premium(user_id: str) -> bool:
    premium_data = await get_premium(user_id)
    status = premium_data.get('status', 'none')
    if status == 'lifetime':
        return True
    elif status in ('days', 'months'):
        expires_at = premium_data.get('expires_at')
        if expires_at:
            return datetime.fromisoformat(expires_at) > datetime.utcnow()
    return False

async def get_user_credits(user_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT balance FROM credits WHERE user_id=?", (str(user_id),))
        row = await cur.fetchone()
        return row[0] if row else 0

async def add_credits(user_id: str, amount: int):
    await ensure_credit_row(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE credits
            SET balance = balance + ?, updated_at=?
            WHERE user_id=?
        """, (int(amount), _now_iso(), str(user_id)))
        await db.commit()

async def consume_credits(user_id: str, amount: int) -> bool:
    await ensure_credit_row(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        # Cek saldo cukup
        cur = await db.execute("SELECT balance FROM credits WHERE user_id=?", (str(user_id),))
        row = await cur.fetchone()
        balance = row[0] if row else 0
        if balance < amount:
            return False
        await db.execute("""
            UPDATE credits
            SET balance = balance - ?, updated_at=?
            WHERE user_id=?
        """, (int(amount), _now_iso(), str(user_id)))
        await db.commit()
        return True

async def ensure_credit_row(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO credits(user_id, balance) VALUES (?, 100)", (str(user_id),))  # Default 100 credits
        await db.commit()

async def log_event(level: str, event: str, detail: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO app_logs(level, event, detail) VALUES (?, ?, ?)
        """, (level, event, detail))
        await db.commit()

async def count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        return row[0] if row else 0

async def count_premium_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT COUNT(*) FROM premiums 
            WHERE status = 'lifetime' 
            OR (status IN ('days', 'months') AND expires_at > datetime('now'))
        """)
        row = await cur.fetchone()
        return row[0] if row else 0

# Compatibility functions to match old API
async def remove_premium(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE premiums 
            SET status='none', expires_at=NULL, updated_at=?
            WHERE user_id=?
        """, (_now_iso(), str(user_id)))
        await db.commit()

async def grant_credits(user_id: str, amount: int):
    return await add_credits(user_id, amount)
