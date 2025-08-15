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
            db.cursor.execute("UPDATE users SET credits = 100 WHERE credits IS NULL")
            fixed_null_credits = db.cursor.rowcount
            db.conn.commit()
            print(f"✅ Fixed {fixed_null_credits} users with NULL credits")

        # Fix negative credits
        if negative_credits > 0:
            db.cursor.execute("UPDATE users SET credits = 10 WHERE credits < 0")
            fixed_negative_credits = db.cursor.rowcount
            db.conn.commit()
            print(f"✅ Fixed {fixed_negative_credits} users with negative credits")

        # Delete users with NULL telegram_id
        if null_telegram_id > 0:
            db.cursor.execute("DELETE FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
            deleted_null_users = db.cursor.rowcount
            db.conn.commit()
            print(f"✅ Deleted {deleted_null_users} users with NULL telegram_id")

        print("\n✅ Database fixes completed!")

        # Show final status
        db.cursor.execute("SELECT COUNT(*) FROM users")
        final_total = db.cursor.fetchone()[0]

        db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = db.cursor.fetchone()[0]

        db.cursor.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
        total_credits = db.cursor.fetchone()[0]

        print(f"📊 Final total users: {final_total}")
        print(f"👥 Valid users: {final_total}")
        print(f"⭐ Premium users: {premium_users}")
        print(f"💰 Total credits: {total_credits}")

        print("\n✅ Database user issues fixed successfully!")

        # Close database connection
        db.close()

    except Exception as e:
        print(f"❌ Error fixing database: {e}")
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