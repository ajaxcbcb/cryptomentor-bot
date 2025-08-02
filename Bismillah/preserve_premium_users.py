#!/usr/bin/env python3
"""
Premium User Preservation Script
Ensures premium and lifetime users persist through deployments
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError as e:
    print(f"❌ Cannot import Database: {e}")
    sys.exit(1)

def preserve_premium_users():
    """Preserve all premium users before deployment"""
    try:
        print("🔒 Premium User Preservation System")
        print("=" * 50)

        db = Database()

        # Get all premium users
        db.cursor.execute("""
            SELECT telegram_id, first_name, username, is_premium, subscription_end, created_at
            FROM users WHERE is_premium = 1
        """)

        premium_users = db.cursor.fetchall()

        if not premium_users:
            print("ℹ️ No premium users found to preserve")
            return True

        # Create preservation backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"premium_users_backup_{timestamp}.json"

        preservation_data = {
            'backup_timestamp': timestamp,
            'total_premium_users': len(premium_users),
            'premium_users': []
        }

        for user in premium_users:
            user_data = {
                'telegram_id': user[0],
                'first_name': user[1],
                'username': user[2],
                'is_premium': user[3],
                'subscription_end': user[4],
                'created_at': user[5],
                'preserved_at': timestamp
            }
            preservation_data['premium_users'].append(user_data)

        # Save to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(preservation_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Preserved {len(premium_users)} premium users")
        print(f"💾 Backup saved: {backup_file}")

        # Log preservation
        for user in premium_users:
            db.log_user_activity(user[0], "premium_preserved", f"Premium status preserved before deployment at {timestamp}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Premium preservation failed: {e}")
        return False

def restore_premium_users(backup_file=None):
    """Restore premium users from backup"""
    try:
        if not backup_file:
            # Find latest backup
            backup_files = [f for f in os.listdir('.') if f.startswith('premium_users_backup_') and f.endswith('.json')]
            if not backup_files:
                print("❌ No premium backup files found")
                return False
            backup_file = sorted(backup_files)[-1]

        print(f"🔄 Restoring premium users from {backup_file}")

        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        db = Database()
        restored_count = 0

        for user_data in backup_data['premium_users']:
            telegram_id = user_data['telegram_id']

            # Restore premium status
            db.cursor.execute("""
                UPDATE users SET is_premium = ?, subscription_end = ?
                WHERE telegram_id = ?
            """, (user_data['is_premium'], user_data['subscription_end'], telegram_id))

            if db.cursor.rowcount > 0:
                restored_count += 1
                db.log_user_activity(telegram_id, "premium_restored", f"Premium status restored from backup {backup_file}")

        db.conn.commit()
        db.close()

        print(f"✅ Restored premium status for {restored_count} users")
        return True

    except Exception as e:
        print(f"❌ Premium restoration failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_premium_users()
    else:
        preserve_premium_users()