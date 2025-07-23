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
        print(f"👥 Total valid users: {final_users}")

        # Check remaining issues
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
        remaining_negative = db.cursor.fetchone()[0]
        print(f"➖ Remaining negative credits: {remaining_negative}")

        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits IS NULL")
        remaining_null_credits = db.cursor.fetchone()[0]
        print(f"💳 Remaining NULL credits: {remaining_null_credits}")

        if remaining_negative == 0 and remaining_null_credits == 0:
            print("✅ All database issues fixed successfully!")
        else:
            print("⚠️ Some issues may remain - consider running the fix again")

        db.close()
        print(f"\n🎉 Database fix completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    fix_database_users()
    
    print("\n" + "="*50)
    
    # Ask if user wants to create test user
    create_test = input("Create a test user to verify functionality? (y/n): ").lower().strip()
    if create_test == 'y':
        # Create test user
        try:
            db = Database()

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
            import traceback
            traceback.print_exc()

    
    print("\n🎉 Database maintenance completed!")