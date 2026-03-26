"""
Skills Repository
Mengelola skill premium yang dibeli user secara per-item.
Skill bersifat permanen (expires_at = NULL) kecuali ditentukan lain.

Akses gratis diberikan kepada:
- Admin (env: ADMIN1, ADMIN2, ADMIN_IDS, ADMIN_USER_ID, ADMIN2_USER_ID)
- User premium aktif (is_premium = true dan belum expired / is_lifetime = true)
"""
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.supabase_repo import _client

# ─────────────────────────────────────────────
#  Katalog skill — tambah skill baru di sini
# ─────────────────────────────────────────────
SKILL_CATALOG: Dict[str, Dict] = {
    "dual_tp_rr3": {
        "name":        "Dual TP + Breakeven SL",
        "emoji":       "🎯",
        "description": (
            "Upgrade strategi autotrade ke R:R 1:3 dengan 2 Take Profit:\n"
            "• TP1 di R:R 1:2 → ambil 75% posisi\n"
            "• TP2 di R:R 1:3 → sisa 25% posisi\n"
            "• Setelah TP1 hit → SL otomatis geser ke entry (breakeven)\n"
            "• Tidak ada risiko rugi setelah TP1 tercapai"
        ),
        "price_credits": 500,
        "category":    "autotrade",
        "permanent":   True,
    },
    # Placeholder untuk skill masa depan:
    # "trailing_sl": {
    #     "name": "Trailing Stop Loss",
    #     "emoji": "📉",
    #     "description": "SL mengikuti harga secara otomatis untuk lock profit lebih banyak.",
    #     "price_credits": 300,
    #     "category": "autotrade",
    #     "permanent": True,
    # },
    # "multi_pair_scan": {
    #     "name": "Multi-Pair Scanner (10 pairs)",
    #     "emoji": "🔍",
    #     "description": "Perluas scan dari 4 pair menjadi 10 pair sekaligus.",
    #     "price_credits": 400,
    #     "category": "autotrade",
    #     "permanent": True,
    # },
}


def _resolve_admin_ids():
    """Kumpulkan semua admin ID dari env vars."""
    ids = set()
    for key in ["ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"]:
        val = (os.getenv(key) or "").strip().strip('"').strip("'")
        if val.isdigit():
            ids.add(int(val))
    for val in (os.getenv("ADMIN_IDS") or "").split(","):
        val = val.strip()
        if val.isdigit():
            ids.add(int(val))
    return ids


def _is_privileged(telegram_id: int) -> bool:
    """
    Return True jika user adalah admin ATAU premium aktif.
    User privileged mendapat semua skill secara gratis dan otomatis.
    """
    # Admin check
    if telegram_id in _resolve_admin_ids():
        return True

    # Premium check via Supabase v_users view
    try:
        s = _client()
        res = s.table("v_users").select("premium_active") \
               .eq("telegram_id", int(telegram_id)).limit(1).execute()
        if res.data and res.data[0].get("premium_active"):
            return True
    except Exception as e:
        print(f"[skills_repo] _is_privileged check error: {e}")

    return False


def get_user_skills(telegram_id: int) -> List[str]:
    """
    Return list skill_id yang aktif untuk user.
    Admin dan premium mendapat semua skill dari katalog secara otomatis.
    """
    if _is_privileged(telegram_id):
        return list(SKILL_CATALOG.keys())

    try:
        s = _client()
        res = s.table("user_skills").select("skill_id, expires_at") \
               .eq("telegram_id", int(telegram_id)).execute()
        now = datetime.now(timezone.utc)
        active = []
        for row in (res.data or []):
            exp = row.get("expires_at")
            if exp is None or datetime.fromisoformat(exp.replace("Z", "+00:00")) > now:
                active.append(row["skill_id"])
        return active
    except Exception as e:
        print(f"[skills_repo] get_user_skills error: {e}")
        return []


def has_skill(telegram_id: int, skill_id: str) -> bool:
    """Cek apakah user memiliki skill tertentu (termasuk auto-grant untuk privileged)."""
    return skill_id in get_user_skills(telegram_id)


def purchase_skill(telegram_id: int, skill_id: str) -> Dict:
    """
    Beli skill dengan credits.
    Return: {"success": bool, "message": str}
    """
    if skill_id not in SKILL_CATALOG:
        return {"success": False, "message": "Skill tidak ditemukan."}

    if has_skill(telegram_id, skill_id):
        return {"success": False, "message": "Kamu sudah memiliki skill ini."}

    skill = SKILL_CATALOG[skill_id]
    price = skill["price_credits"]

    try:
        s = _client()

        # Cek dan potong credits
        user_res = s.table("users").select("credits").eq("telegram_id", int(telegram_id)).limit(1).execute()
        if not user_res.data:
            return {"success": False, "message": "User tidak ditemukan."}

        current_credits = user_res.data[0].get("credits", 0)
        if current_credits < price:
            return {
                "success": False,
                "message": f"Credits tidak cukup. Kamu punya {current_credits}, butuh {price}."
            }

        # Deduct credits
        s.table("users").update({"credits": current_credits - price}) \
         .eq("telegram_id", int(telegram_id)).execute()

        # Insert skill
        s.table("user_skills").insert({
            "telegram_id":   int(telegram_id),
            "skill_id":      skill_id,
            "price_credits": price,
            "expires_at":    None,  # permanent
        }).execute()

        return {"success": True, "message": f"Skill '{skill['name']}' berhasil diaktifkan!"}

    except Exception as e:
        print(f"[skills_repo] purchase_skill error: {e}")
        return {"success": False, "message": f"Error: {str(e)[:80]}"}
