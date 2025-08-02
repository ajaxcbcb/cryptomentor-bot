#!/usr/bin/env python3
"""Check current users in CryptoMentor AI database"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)


def check_current_users():
    """Check current users in the database"""
    print("👥 CryptoMentor AI - Current Users Check")
    print("=" * 50)

    try:
        # Initialize database
        db = Database()
        print("✅ Database connection established")

        # Get basic stats
        stats = db.get_bot_statistics()

        print(f"\n📊 User Statistics:")
        print(f"👥 Total Users: {stats['total_users']}")
        print(f"⭐ Premium Users: {stats['premium_users']}")
        print(f"🆓 Free Users: {stats['total_users'] - stats['premium_users']}")
        print(f"📈 Active Today: {stats['active_today']}")
        print(f"💰 Total Credits: {stats['total_credits']:,}")
        print(f"📊 Average Credits: {stats['avg_credits']:.1f}")

        # Show recent users
        print(f"\n👤 Recent Users (Last 10):")
        db.cursor.execute("""
            SELECT telegram_id, first_name, username, is_premium, credits, created_at
            FROM users 
            WHERE telegram_id IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 10
        """)

        recent_users = db.cursor.fetchall()

        if recent_users:
            for user in recent_users:
                telegram_id, first_name, username, is_premium, credits, created_at = user
                status = "⭐ Premium" if is_premium else f"🆓 Free ({credits} credits)"
                username_display = f"@{username}" if username else "No username"
                date_created = created_at[:10] if created_at else "Unknown"

                print(f"• {first_name} ({username_display}) - {status} - {date_created}")
        else:
            print("❌ No users found")

        # Check for data issues
        print("\n🔍 Data Quality Check:")

        # Users with 0 credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits = 0")
        zero_credits = db.cursor.fetchone()[0]

        # Users with NULL telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL")
        null_ids = db.cursor.fetchone()[0]

        print(f"⚠️ Users with 0 credits: {zero_credits}")
        print(f"❌ Users with NULL telegram_id: {null_ids}")

        if zero_credits > 0:
            print("💡 Tip: Consider running credit distribution for 0-credit users")

        if null_ids > 0:
            print("🔧 Warning: Found users with NULL telegram_id - database needs cleanup")

        db.close()
        print("\n✅ Database check completed!")

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_current_users()