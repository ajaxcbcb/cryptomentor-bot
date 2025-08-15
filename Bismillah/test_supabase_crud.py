
#!/usr/bin/env python3
"""
Test script for Supabase CRUD operations
"""

import os
from datetime import datetime, timedelta
from supabase_client import add_user, get_user, update_user, delete_user, grant_premium

def test_supabase_crud():
    """Test all CRUD operations"""
    print("🧪 Testing Supabase CRUD Operations")
    print("=" * 50)
    
    test_user_id = 999999999  # Test user ID
    
    # Test 1: Add user
    print("1️⃣ Testing add_user...")
    result = add_user(
        user_id=test_user_id,
        username="test_user",
        first_name="Test",
        last_name="User",
        is_premium=False
    )
    print(f"Result: {result}")
    
    # Test 2: Get user
    print("\n2️⃣ Testing get_user...")
    result = get_user(test_user_id)
    print(f"Result: {result}")
    
    # Test 3: Update user
    print("\n3️⃣ Testing update_user...")
    result = update_user(test_user_id, {
        "first_name": "Updated Test",
        "credits": 200
    })
    print(f"Result: {result}")
    
    # Test 4: Grant premium
    print("\n4️⃣ Testing grant_premium...")
    expiry_date = (datetime.now() + timedelta(days=30)).isoformat()
    result = grant_premium(test_user_id, expiry_date)
    print(f"Result: {result}")
    
    # Test 5: Get updated user
    print("\n5️⃣ Testing get_user after updates...")
    result = get_user(test_user_id)
    print(f"Result: {result}")
    
    # Test 6: Delete user (cleanup)
    print("\n6️⃣ Testing delete_user (cleanup)...")
    result = delete_user(test_user_id)
    print(f"Result: {result}")
    
    print("\n✅ CRUD testing completed!")

if __name__ == "__main__":
    test_supabase_crud()
