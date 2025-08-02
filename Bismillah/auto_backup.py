
#!/usr/bin/env python3
"""
Auto Backup System for CryptoMentor AI
Runs periodic backups to ensure data safety
"""

import schedule
import time
import os
from datetime import datetime
from database_recovery import DatabaseRecovery

def run_scheduled_backup():
    """Run scheduled backup process"""
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running scheduled backup...")
    
    recovery = DatabaseRecovery()
    
    # Create database backup
    backup_file = recovery.create_full_backup()
    
    # Export users to JSON
    json_backup = recovery.export_users_json()
    
    # Clean old backups (keep last 7 days)
    cleanup_old_backups()
    
    print(f"✅ Scheduled backup completed!")

def cleanup_old_backups(days_to_keep=7):
    """Clean up old backup files"""
    try:
        backup_dir = "database_backups"
        if not os.path.exists(backup_dir):
            return
        
        import time
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        cleaned_count = 0
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
        
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old backup files")
            
    except Exception as e:
        print(f"⚠️ Backup cleanup warning: {e}")

def start_backup_scheduler():
    """Start the backup scheduler"""
    print("🕐 Starting CryptoMentor AI Auto Backup System...")
    
    # Schedule backups every 6 hours
    schedule.every(6).hours.do(run_scheduled_backup)
    
    # Schedule daily backup at 3 AM
    schedule.every().day.at("03:00").do(run_scheduled_backup)
    
    print("✅ Backup scheduler started!")
    print("📅 Backups will run every 6 hours and daily at 3 AM")
    
    # Run initial backup
    run_scheduled_backup()
    
    # Keep scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    start_backup_scheduler()
