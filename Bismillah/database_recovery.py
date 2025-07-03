
#!/usr/bin/env python3
"""
Database Recovery and Backup System for CryptoMentor AI
Ensures user data persistence and recovery capabilities
"""

import sqlite3
import json
import os
from datetime import datetime
from database import Database

class DatabaseRecovery:
    def __init__(self, db_path="cryptomentor.db"):
        self.db_path = db_path
        self.backup_dir = "database_backups"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_full_backup(self):
        """Create complete database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.backup_dir}/backup_{timestamp}.db"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            print(f"✅ Full database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def export_users_json(self):
        """Export all users to JSON for backup"""
        try:
            db = Database()
            
            # Get all users
            db.cursor.execute("""
                SELECT telegram_id, first_name, last_name, username, language_code, 
                       is_premium, credits, subscription_end, created_at
                FROM users WHERE telegram_id IS NOT NULL
            """)
            
            users = []
            for row in db.cursor.fetchall():
                user_data = {
                    'telegram_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'username': row[3],
                    'language_code': row[4],
                    'is_premium': row[5],
                    'credits': row[6],
                    'subscription_end': row[7],
                    'created_at': row[8]
                }
                users.append(user_data)
            
            # Save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"{self.backup_dir}/users_backup_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'backup_date': timestamp,
                    'total_users': len(users),
                    'users': users
                }, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Users exported to JSON: {json_file}")
            print(f"📊 Total users backed up: {len(users)}")
            
            db.close()
            return json_file
            
        except Exception as e:
            print(f"❌ JSON export failed: {e}")
            return None
    
    def restore_users_from_json(self, json_file):
        """Restore users from JSON backup"""
        try:
            if not os.path.exists(json_file):
                print(f"❌ Backup file not found: {json_file}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            db = Database()
            restored_count = 0
            skipped_count = 0
            
            for user_data in backup_data['users']:
                telegram_id = user_data['telegram_id']
                
                # Check if user already exists
                existing = db.get_user(telegram_id)
                if existing:
                    skipped_count += 1
                    continue
                
                # Restore user
                success = db.cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (telegram_id, first_name, last_name, username, language_code, 
                     is_premium, credits, subscription_end, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['telegram_id'],
                    user_data['first_name'],
                    user_data['last_name'], 
                    user_data['username'],
                    user_data['language_code'],
                    user_data['is_premium'],
                    user_data['credits'],
                    user_data['subscription_end'],
                    user_data['created_at']
                ))
                
                restored_count += 1
                
                # Log restoration
                db.log_user_activity(telegram_id, "user_restored_from_backup", f"Restored from JSON backup: {json_file}")
            
            db.conn.commit()
            db.close()
            
            print(f"✅ User restoration completed!")
            print(f"📊 Restored: {restored_count} users")
            print(f"⏭️ Skipped (already exist): {skipped_count} users")
            
            return True
            
        except Exception as e:
            print(f"❌ Restoration failed: {e}")
            return False
    
    def check_and_repair_database(self):
        """Check database integrity and repair if needed"""
        try:
            db = Database()
            
            print("🔍 Running database health check...")
            health_ok = db.database_health_check()
            
            if not health_ok:
                print("⚠️ Database issues detected, attempting repair...")
                
                # Recreate tables if needed
                db.create_tables()
                
                # Fix common issues
                fixed_credits = db.fix_user_credits()
                print(f"✅ Fixed credits for {fixed_credits} users")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ Database repair failed: {e}")
            return False

def main():
    """Main function for database recovery operations"""
    print("🔧 CryptoMentor AI - Database Recovery System")
    print("=" * 50)
    
    recovery = DatabaseRecovery()
    
    print("1. Creating full database backup...")
    backup_file = recovery.create_full_backup()
    
    print("\n2. Exporting users to JSON...")
    json_backup = recovery.export_users_json()
    
    print("\n3. Running database health check...")
    recovery.check_and_repair_database()
    
    print("\n✅ Recovery system check completed!")
    print(f"💾 Database backup: {backup_file}")
    print(f"📄 JSON backup: {json_backup}")

if __name__ == "__main__":
    main()
