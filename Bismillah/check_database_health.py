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
    print("🏥 CryptoMentor AI - Database Health Check")
    print("=" * 50)

    try:
        # Initialize database
        db = Database()
        print("✅ Database connection established")

        # Perform comprehensive health check
        health_status = db.database_health_check()

        print("\n📊 Detailed Statistics:")
        stats = db.get_bot_statistics()

        print(f"👥 Total Users: {stats['total_users']}")
        print(f"⭐ Premium Users: {stats['premium_users']}")
        print(f"🆓 Free Users: {stats['total_users'] - stats['premium_users']}")
        print(f"📈 Active Today: {stats['active_today']}")
        print(f"💳 Total Credits: {stats['total_credits']}")
        print(f"📊 Average Credits/User: {stats['avg_credits']:.2f}")
        print(f"⚡ Commands Today: {stats['commands_today']}")
        print(f"📈 Total Analyses: {stats['analyses_count']}")

        # Data integrity checks
        print("\n🔍 Data Integrity Checks:")

        # Check for users with invalid telegram_id
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
        invalid_ids = db.cursor.fetchone()[0]
        print(f"❌ Invalid telegram_id: {invalid_ids}")

        # Check for users with negative credits
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
        negative_credits = db.cursor.fetchone()[0]
        print(f"➖ Negative credits: {negative_credits}")

        # Check for expired premium users still marked as premium
        db.cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE is_premium = 1 
            AND subscription_end IS NOT NULL 
            AND datetime(subscription_end) < datetime('now')
        """)
        expired_premium = db.cursor.fetchone()[0]
        print(f"⏰ Expired premium: {expired_premium}")

        # Check for orphaned activity records
        db.cursor.execute("""
            SELECT COUNT(*) FROM user_activity ua
            WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.telegram_id = ua.telegram_id)
        """)
        orphaned_activities = db.cursor.fetchone()[0]
        print(f"🔗 Orphaned activities: {orphaned_activities}")

        # Overall health assessment
        print("\n🎯 Overall Health Assessment:")

        issues_found = invalid_ids + negative_credits + expired_premium + orphaned_activities

        if issues_found == 0:
            print("🟢 DATABASE HEALTHY - No issues detected")
        elif issues_found <= 5:
            print("🟡 DATABASE MINOR ISSUES - Some cleanup needed")
        else:
            print("🔴 DATABASE NEEDS ATTENTION - Multiple issues found")

        if issues_found > 0:
            print("\n💡 Recommended Actions:")
            if invalid_ids > 0:
                print("• Run database user fix to clean invalid users")
            if negative_credits > 0:
                print("• Reset negative credits to 0 or positive values")
            if expired_premium > 0:
                print("• Update expired premium users status")
            if orphaned_activities > 0:
                print("• Clean orphaned activity records")

            print("\nRun: python fix_database_users.py")

        db.close()
        print(f"\n✅ Health check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return health_status

    except Exception as e:
        print(f"❌ Error during health check: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_database_health()