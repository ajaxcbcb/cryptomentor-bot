
import os
import re
from typing import List, Set

# Kunci env yang didukung (urutan prioritas):
ENV_KEYS = [
    "ADMIN",          # ← utama (bisa 1 atau banyak)
    "ADMIN1",         # ← admin utama
    "ADMIN2",         # ← admin kedua (super admin)
    "ADMINS",
    "ADMIN_IDS",
    "ADMIN_ID",
]
# Dukungan legacy: ADMIN1..ADMIN10
LEGACY_KEYS = [f"ADMIN{i}" for i in range(1, 11)]

def _split_candidates(val: str) -> List[str]:
    """Pisah string berdasarkan koma, spasi, newline, titik koma."""
    # Hapus bracket/quotes bila ada
    val = val.strip().strip("[](){}\"'")
    # Gantikan pemisah umum jadi spasi
    val = re.sub(r"[,;\n\r\t]+", " ", val)
    parts = [p for p in val.split(" ") if p]
    return parts

def _coerce_id(s: str):
    s = s.strip()
    m = re.search(r"\d+", s)
    if not m:
        return None
    try:
        return int(m.group(0))
    except Exception:
        return None

def get_admin_ids() -> List[int]:
    ids: Set[int] = set()

    # 1) baca ENV_KEYS dahulu
    for k in ENV_KEYS:
        v = os.getenv(k)
        if v:
            for p in _split_candidates(v):
                uid = _coerce_id(p)
                if uid is not None:
                    ids.add(uid)

    # 2) legacy ADMIN1..ADMIN10
    for k in LEGACY_KEYS:
        v = os.getenv(k)
        if v:
            uid = _coerce_id(v)
            if uid is not None:
                ids.add(uid)

    # Hasil terurut
    return sorted(ids)

def is_admin(user_id: int) -> bool:
    try:
        uid = int(user_id)
    except Exception:
        return False
    return uid in set(get_admin_ids())

def admin_denied_text(requester_id: int) -> str:
    admins = get_admin_ids()
    admins_text = ", ".join(map(str, admins)) if admins else "NONE CONFIGURED"
    return (
        "❌ Admin Access Required\n\n"
        f"Your ID: {requester_id}\n"
        f"Admin IDs: {admins_text}\n\n"
        "⚙️ Setup Instructions:\n"
        "1) Buka Secrets tab di Replit\n"
        "2) Tambahkan salah satu:\n"
        "   • ADMIN = 7255533151            (satu ID)\n"
        "   • ADMIN = 7255533151, 123456789 (multi ID, pisah koma)\n"
        "   • ADMINS / ADMIN_IDS juga boleh\n"
        "   • Legacy: ADMIN1, ADMIN2, ...\n"
        "3) Restart bot untuk apply changes\n"
    )
