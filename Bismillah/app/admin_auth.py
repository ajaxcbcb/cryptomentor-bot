
# app/admin_auth.py
import os

def get_admin_ids():
    """Get admin IDs from environment variables"""
    admin_ids = set()
    
    # Primary admin secrets
    admin1 = os.getenv("ADMIN1", "").strip()
    admin2 = os.getenv("ADMIN2", "").strip()
    
    if admin1 and admin1.isdigit():
        admin_ids.add(int(admin1))
        
    if admin2 and admin2.isdigit():
        admin_ids.add(int(admin2))
    
    # Get ADMIN_IDS if available
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        for aid in admin_ids_str.split(","):
            aid = aid.strip()
            if aid.isdigit():
                admin_ids.add(int(aid))
    
    # Fallback to individual ADMIN3-ADMIN9
    for i in range(3, 10):
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
