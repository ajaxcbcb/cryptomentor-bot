
#!/usr/bin/env python3
"""Fix database user issues for CryptoMentor AI Bot"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)

def fix_database_users():
    """Fix common database user issues"""
    print("🔧 Starting database user fixes...")
    
    try:
        db = Database()
        
        # Fix 1: Update NULL telegram_ids
        print("🔍 Checking for NULL telegram_ids...")
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL")
        null_count = db.cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"⚠️ Found {null_count} users with NULL telegram_id")
            # Delete users with NULL telegram_id as they're invalid
            db.cursor.execute("DELETE FROM users WHERE telegram_id IS NULL")
            db.conn.commit()
            print(f"✅ Removed {null_count} invalid users")
        
        # Fix 2: Fix negative credits
        print("🔍 Checking for negative credits...")
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
        negative_count = db.cursor.fetchone()[0]
        
        if negative_count > 0:
            print(f"⚠️ Found {negative_count} users with negative credits")
            db.cursor.execute("UPDATE users SET credits = 10 WHERE credits < 0")
            db.conn.commit()
            print(f"✅ Fixed {negative_count} users with negative credits")
        
        # Fix 3: Ensure all users have proper is_premium status
        print("🔍 Checking premium status...")
        db.cursor.execute("UPDATE users SET is_premium = 0 WHERE is_premium IS NULL")
        db.conn.commit()
        
        print("✅ Database fixes completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database_users()1)

def fix_database_users():
    """Fix common database user issues"""
    print("🔧 CryptoMentor AI - Database User Fix")
    print("=" * 50)
    
    try:
        # Initialize database
        db = Database()
        print("✅ Database connection established")
        
        # Check current status
        print("\n📊 Current Database Status:")
        
        # Total users
        db.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = db.cursor.fetchone()[0]
        print(f"👥 Total users: {total_users}")
        
        # Users with NULL telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
        null_telegram_id = db.cursor.fetchone()[0]
        print(f"❌ NULL telegram_id: {null_telegram_id}")
        
        # Users with NULL credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits IS NULL")
        null_credits = db.cursor.fetchone()[0]
        print(f"💳 NULL credits: {null_credits}")
        
        # Users with negative credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
        negative_credits = db.cursor.fetchone()[0]
        print(f"➖ Negative credits: {negative_credits}")
        
        # Start fixing issues
        print("\n🔧 Fixing Issues:")
        
        # Fix NULL credits
        if null_credits > 0:
            db.cursor.execute("UPDATE users SET credits = 10 WHERE credits IS NULL")
            fixed_null_credits = db.cursor.rowcount
            print(f"✅ Fixed NULL credits: {fixed_null_credits} users given 10 credits")
        
        # Fix negative credits
        if negative_credits > 0:
            db.cursor.execute("UPDATE users SET credits = 0 WHERE credits < 0")
            fixed_negative_credits = db.cursor.rowcount
            print(f"✅ Fixed negative credits: {fixed_negative_credits} users set to 0 credits")
        
        # Remove users with NULL telegram_id (invalid entries)
        if null_telegram_id > 0:
            db.cursor.execute("DELETE FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
            removed_invalid = db.cursor.rowcount
            print(f"🗑️ Removed invalid users: {removed_invalid} users")
        
        # Fix expired premium users
        db.cursor.execute("""
            UPDATE users SET is_premium = 0 
            WHERE is_premium = 1 
            AND subscription_end IS NOT NULL 
            AND datetime(subscription_end) < datetime('now')
        """)
        expired_premium_fixed = db.cursor.rowcount
        if expired_premium_fixed > 0:
            print(f"⏰ Fixed expired premium: {expired_premium_fixed} users")
        
        # Commit all changes
        db.conn.commit()
        
        # Final status check
        print("\n📊 Final Database Status:")
        
        # Recount after fixes
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
        final_users = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
        total_credits = db.cursor.fetchone()[0]
        
        print(f"👥 Valid users: {final_users}")
        print(f"⭐ Premium users: {premium_users}")
        print(f"💰 Total credits: {total_credits}")
        
        print("\n✅ Database user issues fixed successfully!")
        
        # Close database connection
        db.close()
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database_users()
        import traceback
        traceback.print_exc()

def create_test_user():
    """Create a test user to verify database functionality"""
    print("\n🧪 Creating test user...")
    
    try:
        db = Database()
        
        # Create test user
        test_telegram_id = 123456789
        success = db.create_user(
            telegram_id=test_telegram_id,
            username="test_user",
            first_name="Test",
            last_name="User",
            language_code="id"
        )
        
        if success:
            print(f"✅ Test user created: {test_telegram_id}")
            
            # Verify user was created
            user = db.get_user(test_telegram_id)
            if user:
                print(f"✅ User verification successful:")
                print(f"   - Name: {user['first_name']}")
                print(f"   - Credits: {user['credits']}")
                print(f"   - Premium: {user['is_premium']}")
            else:
                print("❌ User verification failed")
        else:
            print("❌ Failed to create test user")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

if __name__ == "__main__":
    fix_database_users()
    
    print("\n" + "="*50)
    
    # Ask if user wants to create test user
    create_test = input("Create a test user to verify functionality? (y/n): ").lower().strip()
    if create_test == 'y':
        create_test_user()
    
    print("\n🎉 Database maintenance completed!")
