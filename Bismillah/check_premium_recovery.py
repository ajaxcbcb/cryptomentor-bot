
#!/usr/bin/env python3
"""Check and recover premium users after system updates"""

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


def check_premium_users_status():
    """Check current premium users status"""
    print("🔍 Checking Premium Users Status...")
    print("=" * 50)

    try:
        db = Database()
        
        # Create backup first
        backup_timestamp = db.create_automatic_backup()
        if backup_timestamp:
            print(f"✅ Backup created: {backup_timestamp}")
        
        # Verify data integrity
        integrity = db.verify_user_data_integrity()
        print(f"📊 Data Integrity Check:")
        print(f"   Premium Users: {integrity.get('premium_users', 0)}")
        print(f"   Lifetime Users: {integrity.get('lifetime_users', 0)}")
        print(f"   Corrupt Entries: {integrity.get('corrupt_entries', 0)}")
        
        # Check for backup tables
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'users_backup%'")
        backup_tables = db.cursor.fetchall()
        
        if backup_tables:
            print(f"\n📦 Found {len(backup_tables)} backup tables:")
            for table in backup_tables:
                table_name = table[0]
                db.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE is_premium = 1")
                premium_in_backup = db.cursor.fetchone()[0]
                print(f"   {table_name}: {premium_in_backup} premium users")
                
                # Option to restore from most recent backup
                if 'users_backup_' in table_name and premium_in_backup > integrity.get('premium_users', 0):
                    print(f"⚠️ Backup {table_name} has MORE premium users than current table!")
                    
                    restore = input(f"Restore premium users from {table_name}? (y/n): ").lower().strip()
                    if restore == 'y':
                        try:
                            # Restore premium status from backup
                            db.cursor.execute(f"""
                                UPDATE users 
                                SET is_premium = b.is_premium, 
                                    subscription_end = b.subscription_end,
                                    premium_referral_code = b.premium_referral_code,
                                    premium_earnings = b.premium_earnings
                                FROM {table_name} b
                                WHERE users.telegram_id = b.telegram_id
                                AND b.is_premium = 1
                            """)
                            
                            restored = db.cursor.rowcount
                            db.conn.commit()
                            print(f"✅ Restored premium status for {restored} users")
                            
                        except Exception as e:
                            print(f"❌ Error restoring from backup: {e}")
        else:
            print("\n❌ No backup tables found")
            
        # Final verification
        print("\n🔄 Final Verification:")
        final_integrity = db.verify_user_data_integrity()
        print(f"   Premium Users: {final_integrity.get('premium_users', 0)}")
        print(f"   Lifetime Users: {final_integrity.get('lifetime_users', 0)}")
        
        db.close()
        print("\n✅ Premium users check completed!")
        
    except Exception as e:
        print(f"❌ Error checking premium users: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_premium_users_status()
