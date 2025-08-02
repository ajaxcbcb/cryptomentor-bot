
#!/usr/bin/env python3
import os
from database import Database
from dotenv import load_dotenv

def test_grant_premium():
    """Test grant premium functionality"""
    print("🧪 Testing Grant Premium Command...")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check admin ID
    admin_id = os.getenv('ADMIN_USER_ID', '0')
    print(f"🔧 Current Admin ID from env: {admin_id}")
    
    if admin_id == '0' or not admin_id:
        print("❌ ADMIN_USER_ID not set in environment!")
        print("💡 Please set your Telegram User ID as ADMIN_USER_ID in Secrets")
        return
    
    try:
        admin_id = int(admin_id)
        print(f"✅ Admin ID validated: {admin_id}")
    except ValueError:
        print("❌ ADMIN_USER_ID is not a valid number!")
        return
    
    try:
        # Initialize database
        db = Database()
        
        # Test user ID (you can change this)
        test_user_id = 123456789
        
        print(f"\n📝 Testing grant premium with User ID: {test_user_id}")
        
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
        
        # 3. Test grant premium (30 days)
        print("\n3️⃣ Testing grant premium (30 days)...")
        success = db.grant_premium(test_user_id, 30)
        if success:
            print("✅ Premium (30 days) granted successfully")
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
            
            # Verify permanent premium
            is_permanent = db.is_user_premium(test_user_id)
            print(f"Permanent Premium Status: {'✅ Active' if is_permanent else '❌ Failed'}")
        else:
            print("❌ Failed to grant permanent premium")
        
        # 6. Test revoke premium
        print("\n6️⃣ Testing revoke premium...")
        success = db.revoke_premium(test_user_id)
        if success:
            print("✅ Premium revoked")
            is_premium_revoked = db.is_user_premium(test_user_id)
            print(f"Status after revoke: {'❌ Still Premium' if is_premium_revoked else '✅ Successfully revoked'}")
        else:
            print("❌ Failed to revoke premium")
        
        print("\n" + "=" * 50)
        print("✅ Grant premium functionality test completed!")
        print(f"\n💡 How to use the command:")
        print(f"• `/grant_premium {test_user_id} 30` - Grant 30 days premium")
        print(f"• `/grant_premium {test_user_id} 0` - Grant permanent premium")
        print(f"• `/revoke_premium {test_user_id}` - Revoke premium")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grant_premium()
