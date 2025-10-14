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
        fixes_applied = 0

        # Fix NULL telegram_id (remove these invalid records)
        if null_telegram_id > 0:
            db.cursor.execute("DELETE FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
            print(f"✅ Removed {null_telegram_id} users with invalid telegram_id")
            fixes_applied += 1

        # Fix NULL credits (set to default 0)
        if null_credits > 0:
            db.cursor.execute("UPDATE users SET credits = 0 WHERE credits IS NULL")
            print(f"✅ Fixed {null_credits} users with NULL credits")
            fixes_applied += 1

        # Fix negative credits (set to 0)
        if negative_credits > 0:
            db.cursor.execute("UPDATE users SET credits = 0 WHERE credits < 0")
            print(f"✅ Fixed {negative_credits} users with negative credits")
            fixes_applied += 1

        # Commit changes
        if fixes_applied > 0:
            db.conn.commit()
            print(f"\n✅ Applied {fixes_applied} fixes successfully")
        else:
            print("\n✅ No fixes needed - database is healthy")

        # Final status
        print("\n📊 Final Database Status:")
        db.cursor.execute("SELECT COUNT(*) FROM users")
        final_users = db.cursor.fetchone()[0]
        print(f"👥 Total users: {final_users}")

        db.close()
        print("\n🎉 Database fix completed successfully!")

    except Exception as e:
        print(f"❌ Error during database fix: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_database_users()