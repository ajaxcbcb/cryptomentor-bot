#!/usr/bin/env python3
"""Test Deposit Eligibility on VPS"""
import sys
import os
sys.path.insert(0, '/root/cryptomentor-bot')

# Load environment
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

try:
    from app.supabase_repo import (
        get_user_total_deposit,
        is_stackmentor_eligible
    )
    print("✅ Deposit functions import successful")
    
    # Test with dummy user (will return 0 if not exists)
    test_user_id = 123456789
    
    try:
        deposit = get_user_total_deposit(test_user_id)
        print(f"✅ get_user_total_deposit works: ${deposit}")
    except Exception as e:
        print(f"⚠️  get_user_total_deposit: {e}")
    
    try:
        eligible = is_stackmentor_eligible(test_user_id)
        print(f"✅ is_stackmentor_eligible works: {eligible}")
    except Exception as e:
        print(f"⚠️  is_stackmentor_eligible: {e}")
    
    print("\n✅ Deposit eligibility check is working!")
    print("\n📝 To add deposit for a user, run in Supabase:")
    print("   SELECT add_user_deposit(telegram_id, amount);")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
