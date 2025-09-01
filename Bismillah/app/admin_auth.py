
# app/admin_auth.py
import os

def get_admin_ids():
    """Get admin IDs from environment variables"""
    admin_ids = set()
    
    # Get ADMIN_IDS if available
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        for aid in admin_ids_str.split(","):
            aid = aid.strip()
            if aid.isdigit():
                admin_ids.add(int(aid))
    
    # Fallback to individual ADMIN1, ADMIN2, etc.
    for i in range(1, 10):
        admin_id = os.getenv(f"ADMIN{i}")
        if admin_id and admin_id.strip().isdigit():
            admin_ids.add(int(admin_id.strip()))
    
    # Legacy fallback
    legacy_admin = os.getenv("ADMIN_USER_ID")
    if legacy_admin and legacy_admin.strip().isdigit():
        admin_ids.add(int(legacy_admin.strip()))
        
    return admin_ids

ADMIN_IDS = get_admin_ids()

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def denied(uid: int) -> str:
    return f"❌ Admin only. Your ID: {uid}"
