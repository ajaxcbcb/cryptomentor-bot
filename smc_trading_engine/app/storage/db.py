from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config.settings import settings


def _sqlite_path_from_db_url(db_url: str) -> Path:
    if db_url.startswith("sqlite:///"):
        return Path(db_url.replace("sqlite:///", "", 1))
    return Path("smc_engine.db")


def get_connection() -> sqlite3.Connection:
    path = _sqlite_path_from_db_url(settings.db_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
