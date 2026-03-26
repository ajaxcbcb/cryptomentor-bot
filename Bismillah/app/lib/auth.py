
import os
import json

# Dynamic admins file path
DYNAMIC_ADMINS_FILE = "data/dynamic_admins.json"

# Admin hierarchy levels
ADMIN_HIERARCHY = {
    1: "ADMIN1",  # Highest level
    2: "ADMIN2",  # Mid level
    3: "ADMIN3"   # Lower level
}

def _get_admin_id_from_secret(level):
    """Get admin ID from secret by level (1, 2, or 3)"""
    secret_name = f"ADMIN{level}"
    admin_secret = os.getenv(secret_name, "").strip()
    if admin_secret and admin_secret.isdigit():
        return int(admin_secret)
    return None

def get_admin_level(user_id):
    """Get admin level of user (1, 2, 3, or None if not admin)"""
    try:
        uid = int(user_id)
        # Check hierarchy: ADMIN1, ADMIN2, ADMIN3
        for level in [1, 2, 3]:
            admin_id = _get_admin_id_from_secret(level)
            if admin_id and uid == admin_id:
                return level
        return None
    except Exception:
        return None

def get_super_admin():
    """Get ADMIN1 (highest level admin)"""
    return _get_admin_id_from_secret(1)

def is_super_admin(user_id):
    """Check if user is ADMIN1 (highest level)"""
    return get_admin_level(user_id) == 1

def is_admin_level_at_least(user_id, required_level):
    """Check if user has admin level >= required_level (lower number = higher privilege)"""
    user_level = get_admin_level(user_id)
    if user_level is None:
        return False
    return user_level <= required_level

def _load_dynamic_admins():
    """Load dynamic admins from JSON file"""
    try:
        if os.path.exists(DYNAMIC_ADMINS_FILE):
            with open(DYNAMIC_ADMINS_FILE, 'r') as f:
                data = json.load(f)
                return set(int(aid) for aid in data.get('admin_ids', []) if str(aid).isdigit())
        return set()
    except Exception as e:
        print(f"Error loading dynamic admins: {e}")
        return set()

def _save_dynamic_admins(admin_ids):
    """Save dynamic admins to JSON file"""
    try:
        os.makedirs(os.path.dirname(DYNAMIC_ADMINS_FILE), exist_ok=True)
        with open(DYNAMIC_ADMINS_FILE, 'w') as f:
            json.dump({'admin_ids': list(admin_ids)}, f)
        return True
    except Exception as e:
        print(f"Error saving dynamic admins: {e}")
        return False

def _resolve_admin_ids():
    """
    Resolve admin IDs from environment variables and dynamic list.
    Priority: ADMIN (super admin) + ADMIN1/ADMIN2 + dynamic admins + legacy fallback
    """
    ids = set()

    # 1. Super admin from ADMIN secret
    super_admin = get_super_admin()
    if super_admin:
        ids.add(super_admin)
        print(f"✅ ADMIN (Super Admin) loaded: {super_admin}")

    # 2. Primary admin variables (ADMIN1 and ADMIN2)
    admin1 = os.getenv("ADMIN1", "").strip()
    admin2 = os.getenv("ADMIN2", "").strip()

    # Add ADMIN1 if valid
    if admin1 and admin1.isdigit():
        ids.add(int(admin1))
        print(f"✅ ADMIN1 loaded: {admin1}")
    
    # Add ADMIN2 if valid (SUPER ADMIN ACCESS)
    if admin2 and admin2.isdigit():
        ids.add(int(admin2))
        print(f"✅ ADMIN2 loaded: {admin2}")

    # 3. Legacy fallback variables
    legacy_admin = os.getenv("ADMIN_USER_ID", "").strip()
    legacy_admin2 = os.getenv("ADMIN2_USER_ID", "").strip()
    
    if legacy_admin and legacy_admin.isdigit():
        ids.add(int(legacy_admin))
        print(f"✅ Legacy ADMIN_USER_ID loaded: {legacy_admin}")
    
    if legacy_admin2 and legacy_admin2.isdigit():
        ids.add(int(legacy_admin2))
        print(f"✅ Legacy ADMIN2_USER_ID loaded: {legacy_admin2}")

    # 4. Dynamic admins added by super admin
    dynamic_admins = _load_dynamic_admins()
    if dynamic_admins:
        ids.update(dynamic_admins)
        print(f"✅ Dynamic admins loaded: {list(dynamic_admins)}")

    # 5. Support for ADMIN3-ADMIN9 for future expansion
    for i in range(3, 10):
        admin_var = os.getenv(f"ADMIN{i}", "").strip()
        if admin_var and admin_var.isdigit():
            ids.add(int(admin_var))
            print(f"✅ ADMIN{i} loaded: {admin_var}")

    print(f"🎯 Total resolved admin IDs: {sorted(list(ids))}")
    return ids

# Initialize admin IDs
ADMIN_IDS = _resolve_admin_ids()

def get_admin_ids():
    """Get all admin IDs"""
    return list(ADMIN_IDS)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def is_super_admin(user_id: int) -> bool:
    """Check if user is super admin"""
    super_admin = get_super_admin()
    return super_admin and user_id == super_admin

def add_admin(new_admin_id: int, requester_id: int) -> bool:
    """Add new admin (super admin only)"""
    if not is_super_admin(requester_id):
        return False
    
    try:
        dynamic_admins = _load_dynamic_admins()
        dynamic_admins.add(new_admin_id)
        
        if _save_dynamic_admins(dynamic_admins):
            # Refresh global admin IDs
            global ADMIN_IDS
            ADMIN_IDS = _resolve_admin_ids()
            return True
        return False
    except Exception as e:
        print(f"Error adding admin: {e}")
        return False

def can_remove_admin(requester_id: int, target_admin_id: int) -> bool:
    """Check if requester can remove target_admin based on hierarchy"""
    requester_level = get_admin_level(requester_id)
    target_level = get_admin_level(target_admin_id)
    
    # Static admins (ADMIN1, ADMIN2, ADMIN3) can only be removed by higher levels
    if requester_level is None:
        return False  # Not an admin
    
    if target_level is None:
        return True  # Can remove non-static admins
    
    # Can only remove if requester has lower level number (higher privilege)
    # ADMIN1 (1) > ADMIN2 (2) > ADMIN3 (3)
    return requester_level < target_level

def remove_admin(admin_id: int, requester_id: int) -> bool:
    """Remove admin with hierarchy checking"""
    if not can_remove_admin(requester_id, admin_id):
        return False
    
    try:
        dynamic_admins = _load_dynamic_admins()
        dynamic_admins.discard(admin_id)
        
        if _save_dynamic_admins(dynamic_admins):
            global ADMIN_IDS
            ADMIN_IDS = _resolve_admin_ids()
            return True
        return False
    except Exception as e:
        print(f"Error removing admin: {e}")
        return False

def get_admin_hierarchy():
    """Get admin hierarchy info with new system"""
    admin1 = _get_admin_id_from_secret(1)
    admin2 = _get_admin_id_from_secret(2)
    admin3 = _get_admin_id_from_secret(3)
    dynamic_admins = _load_dynamic_admins()
    
    return {
        'admin1': {'id': admin1, 'level': 1, 'name': 'ADMIN1', 'can_remove': ['ADMIN2', 'ADMIN3']},
        'admin2': {'id': admin2, 'level': 2, 'name': 'ADMIN2', 'can_remove': ['ADMIN3']},
        'admin3': {'id': admin3, 'level': 3, 'name': 'ADMIN3', 'can_remove': []},
        'dynamic_admins': list(dynamic_admins),
        'total_admins': len(_resolve_admin_ids()),
        'hierarchy': '✅ ADMIN1 > ADMIN2 > ADMIN3'
    }

def refresh_admin_ids():
    """Refresh admin IDs from environment and dynamic file"""
    global ADMIN_IDS
    ADMIN_IDS = _resolve_admin_ids()
    return ADMIN_IDS
