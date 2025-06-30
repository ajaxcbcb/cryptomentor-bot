
#!/usr/bin/env python3
from database import Database
import os

def test_premium_functionality():
    """Test premium functionality"""
    print("🧪 Testing Premium Functionality...")
    print("=" * 50)
    
    try:
        # Initialize database
        db = Database()
        
        # Test user ID (you can change this)
        test_user_id = 123456789
        
        print(f"📝 Testing with User ID: {test_user_id}")
        
        # 1. Check if user exists
        print("\n1️⃣ Checking if user exists...")
        user = db.get_user(test_user_id)
        
        if not user:
            print("❌ User not found! Creating test user...")
            success = db.create_user(
                telegram_id=test_user_id,
                username="testuser",
                first_name="Test User",
                language_code='id'
            )
            if success:
                print("✅ Test user created")
            else:
                print("❌ Failed to create test user")
                return
        else:
            print(f"✅ User found: {user['first_name']} (@{user['username']})")
        
        # 2. Check current premium status
        print("\n2️⃣ Checking current premium status...")
        is_premium = db.is_user_premium(test_user_id)
        credits = db.get_user_credits(test_user_id)
        print(f"Premium Status: {'✅ Premium' if is_premium else '❌ Free'}")
        print(f"Credits: {credits}")
        
        # 3. Test grant premium
        print("\n3️⃣ Testing grant premium...")
        success = db.grant_premium(test_user_id, 30)
        if success:
            print("✅ Premium granted successfully")
        else:
            print("❌ Failed to grant premium")
            return
        
        # 4. Verify premium status
        print("\n4️⃣ Verifying premium status...")
        is_premium_after = db.is_user_premium(test_user_id)
        print(f"Premium Status After: {'✅ Premium' if is_premium_after else '❌ Still Free'}")
        
        # 5. Test permanent premium
        print("\n5️⃣ Testing permanent premium...")
        success = db.grant_permanent_premium(test_user_id)
        if success:
            print("✅ Permanent premium granted")
        else:
            print("❌ Failed to grant permanent premium")
        
        # 6. Test credit addition
        print("\n6️⃣ Testing credit addition...")
        old_credits = db.get_user_credits(test_user_id)
        success = db.add_credits(test_user_id, 50)
        new_credits = db.get_user_credits(test_user_id)
        
        if success:
            print(f"✅ Credits added: {old_credits} → {new_credits}")
        else:
            print("❌ Failed to add credits")
        
        # 7. Test revoke premium
        print("\n7️⃣ Testing revoke premium...")
        success = db.revoke_premium(test_user_id)
        if success:
            print("✅ Premium revoked")
            is_premium_revoked = db.is_user_premium(test_user_id)
            print(f"Status after revoke: {'❌ Still Premium' if is_premium_revoked else '✅ Successfully revoked'}")
        else:
            print("❌ Failed to revoke premium")
        
        print("\n" + "=" * 50)
        print("✅ Premium functionality test completed!")
        
        # Admin ID check
        admin_id = os.getenv('ADMIN_USER_ID', '0')
        print(f"\n🔧 Current Admin ID from env: {admin_id}")
        print(f"💡 Make sure to set your Telegram User ID as ADMIN_USER_ID in Secrets")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_premium_functionality()
