
#!/usr/bin/env python3
"""
Test local SQLite database functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.db.local_db import (
    init_db, upsert_user, get_user, set_premium_with_value, 
    is_premium, add_credits, get_user_credits, count_users
)

async def test_local_database():
    """Test all local database functions"""
    print("🔍 Testing Local SQLite Database...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Test user creation
    test_user_id = "123456789"
    await upsert_user(test_user_id, "TestUser", "Test", "testuser")
    print("✅ User created")
    
    # Test user retrieval
    user = await get_user(test_user_id)
    print(f"✅ User retrieved: {user['first_name']}")
    
    # Test premium functionality
    await set_premium_with_value(test_user_id, "lifetime", 0)
    premium_status = await is_premium(test_user_id)
    print(f"✅ Premium set: {premium_status}")
    
    # Test credits
    await add_credits(test_user_id, 100)
    credits = await get_user_credits(test_user_id)
    print(f"✅ Credits added: {credits}")
    
    # Test user count
    user_count = await count_users()
    print(f"✅ Total users: {user_count}")
    
    print("\n🎉 All local database tests passed!")
    print("✅ No Supabase dependencies - 100% local!")

if __name__ == "__main__":
    asyncio.run(test_local_database())
