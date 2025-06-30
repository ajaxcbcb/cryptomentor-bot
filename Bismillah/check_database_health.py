#!/usr/bin/env python3
"""Database health checker for CryptoMentor AI Bot"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    print("Make sure database.py exists in the same directory")
    sys.exit(1)

def check_database_health():
    """Comprehensive database health check"""
    print("🔍 CryptoMentor AI - Database Health Check")
    print("=" * 50)

    try:
        # Initialize database connection
        print("📂 Connecting to database...")
        db = Database()
        print("✅ Database connection successful")

        # Check database structure
        print("\n🏗️ Database Structure:")
        try:
            # Check if users table exists and get structure
            db.cursor.execute("PRAGMA table_info(users)")
            users_columns = db.cursor.fetchall()

            if users_columns:
                print("✅ Users table exists")
                print("📋 Columns:", [col[1] for col in users_columns])
            else:
                print("❌ Users table missing!")
                return

            # Check if user_activity table exists
            db.cursor.execute("PRAGMA table_info(user_activity)")
            activity_columns = db.cursor.fetchall()

            if activity_columns:
                print("✅ User activity table exists")
            else:
                print("⚠️ User activity table missing")

            # Check if portfolio table exists
            db.cursor.execute("PRAGMA table_info(portfolio)")
            portfolio_columns = db.cursor.fetchall()

            if portfolio_columns:
                print("✅ Portfolio table exists")
            else:
                print("⚠️ Portfolio table missing")

        except Exception as e:
            print(f"❌ Database structure error: {e}")

        # Check data integrity
        print("\n🔍 Data Integrity Check:")
        try:
            # Count total users
            db.cursor.execute("SELECT COUNT(*) FROM users")
            total_users = db.cursor.fetchone()[0]
            print(f"👥 Total users: {total_users}")

            # Check for users with NULL telegram_id
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE user_id IS NULL OR user_id = ''")
            null_telegram_id = db.cursor.fetchone()[0]

            # Check for users with NULL credits
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits IS NULL")
            null_credits = db.cursor.fetchone()[0]

            # Check for users with negative credits
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
            negative_credits = db.cursor.fetchone()[0]

            # Check for users with zero credits
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits = 0")
            zero_credits = db.cursor.fetchone()[0]

            # Check premium users
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            premium_users = db.cursor.fetchone()[0]

            # Check expired premium users
            db.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE is_premium = 1 
                AND subscription_end IS NOT NULL 
                AND datetime(subscription_end) < datetime('now')
            """)
            expired_premium = db.cursor.fetchone()[0]

            print(f"🆔 Users with NULL ID: {null_telegram_id}")
            print(f"💳 Users with NULL credits: {null_credits}")
            print(f"❌ Users with negative credits: {negative_credits}")
            print(f"🔒 Users with zero credits: {zero_credits}")
            print(f"⭐ Premium users: {premium_users}")
            print(f"⏰ Expired premium: {expired_premium}")

            # Data quality assessment
            quality_issues = null_telegram_id + null_credits + negative_credits + expired_premium

            if quality_issues == 0:
                print("✅ Data integrity: Excellent")
            elif quality_issues < total_users * 0.05:  # Less than 5% issues
                print("🟡 Data integrity: Good (minor issues)")
            else:
                print("🔴 Data integrity: Poor (significant issues)")

        except Exception as e:
            print(f"❌ Database operations error: {e}")

        # Memory usage check
        print("\n💾 Database Performance:")
        try:
            db.cursor.execute("PRAGMA page_count")
            page_count = db.cursor.fetchone()[0]

            db.cursor.execute("PRAGMA page_size")
            page_size = db.cursor.fetchone()[0]

            total_size = page_count * page_size
            print(f"📊 Database size: {total_size:,} bytes ({page_count:,} pages)")

            # Check for unused space
            db.cursor.execute("PRAGMA freelist_count")
            free_pages = db.cursor.fetchone()[0]
            if free_pages > page_count * 0.1:  # More than 10% free space
                print(f"⚠️ High fragmentation: {free_pages} free pages")
                print("💡 Consider running VACUUM to optimize")
            else:
                print("✅ Database fragmentation: Normal")

        except Exception as e:
            print(f"❌ Error checking performance: {e}")

        # Recommendations
        print("\n💡 Recommendations:")

        if null_telegram_id > 0:
            print("• Fix users with NULL telegram_id")

        if null_credits > 0:
            print("• Fix users with NULL credits")

        if zero_credits > total_users * 0.8:  # More than 80% users have 0 credits
            print("• Consider credit distribution campaign")

        if expired_premium > 0:
            print("• Update expired premium users")

        if quality_issues == 0:
            print("• Database is healthy! 🎉")

        # Close database connection
        db.conn.close()
        print("\n✅ Database health check completed")

    except Exception as e:
        print(f"❌ Critical database error: {e}")
        print("🔧 Database may need repair or recreation")

def fix_common_issues():
    """Fix common database issues"""
    print("\n🔧 Auto-fixing common issues...")

    try:
        db = Database()

        # Fix NULL credits
        db.cursor.execute("UPDATE users SET credits = 10 WHERE credits IS NULL")
        null_credits_fixed = db.cursor.rowcount

        # Fix users with negative credits
        db.cursor.execute("UPDATE users SET credits = 0 WHERE credits < 0")
        negative_credits_fixed = db.cursor.rowcount

        # Fix expired premium users
        db.cursor.execute("""
            UPDATE users SET is_premium = 0 
            WHERE is_premium = 1 
            AND subscription_end IS NOT NULL 
            AND datetime(subscription_end) < datetime('now')
        """)
        expired_premium_fixed = db.cursor.rowcount

        db.conn.commit()

        print(f"✅ Fixed NULL credits: {null_credits_fixed} users")
        print(f"✅ Fixed negative credits: {negative_credits_fixed} users") 
        print(f"✅ Fixed expired premium: {expired_premium_fixed} users")

        db.conn.close()

    except Exception as e:
        print(f"❌ Error during auto-fix: {e}")

if __name__ == "__main__":
    check_database_health()

    # Ask if user wants to fix issues
    print("\n" + "="*50)
    fix_issues = input("🔧 Run auto-fix for common issues? (y/n): ").lower().strip()

    if fix_issues == 'y':
        fix_common_issues()
        print("\n🔄 Re-running health check after fixes...")
        check_database_health()
    else:
        print("👋 Health check completed. Run again anytime!")