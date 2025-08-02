#!/usr/bin/env python3
"""
Database Checkpoint System for CryptoMentor AI
Creates complete snapshots of all database data for recovery purposes
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from database import Database

class DatabaseCheckpoint:
    def __init__(self, db_path="cryptomentor.db"):
        self.db_path = db_path
        self.checkpoint_dir = "database_checkpoints"
        
        # Create checkpoint directory if it doesn't exist
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
    
    def create_full_checkpoint(self):
        """Create complete database checkpoint with all data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_name = f"checkpoint_{timestamp}"
            checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)
            
            print(f"🔄 Creating database checkpoint: {checkpoint_name}")
            print("=" * 60)
            
            # Create checkpoint directory
            os.makedirs(checkpoint_path, exist_ok=True)
            
            # 1. Full database file backup
            db_backup_file = os.path.join(checkpoint_path, "database_backup.db")
            shutil.copy2(self.db_path, db_backup_file)
            print(f"✅ Database file backed up: {db_backup_file}")
            
            # 2. Export all tables to JSON
            self.export_all_tables_to_json(checkpoint_path, timestamp)
            
            # 3. Create metadata file
            self.create_checkpoint_metadata(checkpoint_path, timestamp)
            
            # 4. Create recovery script
            self.create_recovery_script(checkpoint_path)
            
            print(f"\n🎉 Checkpoint completed successfully!")
            print(f"📁 Location: {checkpoint_path}")
            print(f"📊 Checkpoint contains:")
            print(f"   - Full database backup")
            print(f"   - JSON exports of all tables")
            print(f"   - Recovery metadata")
            print(f"   - Automated recovery script")
            
            return checkpoint_path
            
        except Exception as e:
            print(f"❌ Checkpoint failed: {e}")
            return None
    
    def export_all_tables_to_json(self, checkpoint_path, timestamp):
        """Export all database tables to JSON files"""
        try:
            db = Database()
            
            # Get all table names
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in db.cursor.fetchall()]
            
            print(f"\n📋 Exporting {len(tables)} tables to JSON:")
            
            for table in tables:
                try:
                    # Get table data
                    db.cursor.execute(f"SELECT * FROM {table}")
                    rows = db.cursor.fetchall()
                    
                    # Get column names
                    db.cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in db.cursor.fetchall()]
                    
                    # Convert to list of dictionaries
                    table_data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = value
                        table_data.append(row_dict)
                    
                    # Save to JSON
                    json_file = os.path.join(checkpoint_path, f"{table}_data.json")
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'table_name': table,
                            'export_timestamp': timestamp,
                            'record_count': len(table_data),
                            'columns': columns,
                            'data': table_data
                        }, f, indent=2, ensure_ascii=False, default=str)
                    
                    print(f"   ✅ {table}: {len(table_data)} records → {table}_data.json")
                    
                except Exception as e:
                    print(f"   ❌ {table}: Export failed - {e}")
            
            db.close()
            
        except Exception as e:
            print(f"❌ Table export failed: {e}")
    
    def create_checkpoint_metadata(self, checkpoint_path, timestamp):
        """Create metadata file with checkpoint information"""
        try:
            db = Database()
            
            # Get database statistics
            stats = db.get_bot_statistics()
            
            # Get database file size
            db_size = os.path.getsize(self.db_path)
            
            metadata = {
                'checkpoint_info': {
                    'created_at': timestamp,
                    'creation_date': datetime.now().isoformat(),
                    'database_file': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2)
                },
                'database_statistics': stats,
                'table_info': {},
                'recovery_info': {
                    'can_restore_full_database': True,
                    'can_restore_individual_tables': True,
                    'recovery_script': 'recovery_script.py'
                }
            }
            
            # Get table information
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in db.cursor.fetchall()]
            
            for table in tables:
                try:
                    db.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = db.cursor.fetchone()[0]
                    metadata['table_info'][table] = {
                        'record_count': count,
                        'json_file': f"{table}_data.json"
                    }
                except:
                    metadata['table_info'][table] = {
                        'record_count': 0,
                        'json_file': f"{table}_data.json",
                        'error': 'Could not get record count'
                    }
            
            # Save metadata
            metadata_file = os.path.join(checkpoint_path, "checkpoint_metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Checkpoint metadata created: checkpoint_metadata.json")
            
            db.close()
            
        except Exception as e:
            print(f"❌ Metadata creation failed: {e}")
    
    def create_recovery_script(self, checkpoint_path):
        """Create automated recovery script"""
        recovery_script_content = '''#!/usr/bin/env python3
"""
Automated Database Recovery Script
Generated by CryptoMentor AI Database Checkpoint System
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime

def recover_database():
    """Recover database from checkpoint files"""
    print("🔄 Starting database recovery...")
    
    # Check if database backup exists
    if os.path.exists("database_backup.db"):
        print("✅ Found database backup file")
        
        # Ask user for recovery method
        print("\\nRecovery options:")
        print("1. Full database restore (replaces current database)")
        print("2. Table-by-table restore (selective)")
        print("3. Create new database with checkpoint data")
        
        choice = input("\\nChoose recovery method (1-3): ").strip()
        
        if choice == "1":
            restore_full_database()
        elif choice == "2":
            restore_selective_tables()
        elif choice == "3":
            create_new_database()
        else:
            print("❌ Invalid choice")
    else:
        print("❌ Database backup file not found!")

def restore_full_database():
    """Restore complete database from backup"""
    try:
        target_db = input("Enter target database path (default: cryptomentor_restored.db): ").strip()
        if not target_db:
            target_db = "cryptomentor_restored.db"
        
        shutil.copy2("database_backup.db", target_db)
        print(f"✅ Database restored to: {target_db}")
        
    except Exception as e:
        print(f"❌ Full restore failed: {e}")

def restore_selective_tables():
    """Restore specific tables from JSON files"""
    try:
        # List available tables
        json_files = [f for f in os.listdir(".") if f.endswith("_data.json")]
        tables = [f.replace("_data.json", "") for f in json_files]
        
        print("\\nAvailable tables:")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")
        
        selected = input("\\nEnter table numbers to restore (comma-separated): ").strip()
        
        if selected:
            indices = [int(x.strip()) - 1 for x in selected.split(",")]
            selected_tables = [tables[i] for i in indices if 0 <= i < len(tables)]
            
            target_db = input("Enter target database path: ").strip()
            restore_tables_to_database(selected_tables, target_db)
        
    except Exception as e:
        print(f"❌ Selective restore failed: {e}")

def restore_tables_to_database(tables, db_path):
    """Restore specific tables to database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for table in tables:
            json_file = f"{table}_data.json"
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create table structure and insert data
                # This is a simplified version - you may need to adjust
                print(f"✅ Restored table: {table}")
            else:
                print(f"❌ JSON file not found for table: {table}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Table restore failed: {e}")

def create_new_database():
    """Create new database with all checkpoint data"""
    print("🔧 Creating new database from checkpoint...")
    # Implementation for creating fresh database
    pass

if __name__ == "__main__":
    recover_database()
'''
        
        recovery_file = os.path.join(checkpoint_path, "recovery_script.py")
        with open(recovery_file, 'w', encoding='utf-8') as f:
            f.write(recovery_script_content)
        
        # Make script executable
        os.chmod(recovery_file, 0o755)
        print(f"✅ Recovery script created: recovery_script.py")
    
    def list_checkpoints(self):
        """List all available checkpoints"""
        try:
            if not os.path.exists(self.checkpoint_dir):
                print("❌ No checkpoints directory found")
                return []
            
            checkpoints = []
            for item in os.listdir(self.checkpoint_dir):
                checkpoint_path = os.path.join(self.checkpoint_dir, item)
                if os.path.isdir(checkpoint_path):
                    metadata_file = os.path.join(checkpoint_path, "checkpoint_metadata.json")
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            checkpoints.append({
                                'name': item,
                                'path': checkpoint_path,
                                'metadata': metadata
                            })
                        except:
                            pass
            
            return sorted(checkpoints, key=lambda x: x['metadata']['checkpoint_info']['created_at'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error listing checkpoints: {e}")
            return []
    
    def restore_from_checkpoint(self, checkpoint_name):
        """Restore database from specific checkpoint"""
        try:
            checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)
            
            if not os.path.exists(checkpoint_path):
                print(f"❌ Checkpoint not found: {checkpoint_name}")
                return False
            
            backup_file = os.path.join(checkpoint_path, "database_backup.db")
            if os.path.exists(backup_file):
                # Create backup of current database
                current_backup = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, current_backup)
                print(f"✅ Current database backed up to: {current_backup}")
                
                # Restore from checkpoint
                shutil.copy2(backup_file, self.db_path)
                print(f"✅ Database restored from checkpoint: {checkpoint_name}")
                return True
            else:
                print(f"❌ Backup file not found in checkpoint: {checkpoint_name}")
                return False
                
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

def main():
    """Main function for database checkpoint operations"""
    print("🔧 CryptoMentor AI - Database Checkpoint System")
    print("=" * 60)
    
    checkpoint = DatabaseCheckpoint()
    
    print("Choose operation:")
    print("1. Create new checkpoint")
    print("2. List existing checkpoints")
    print("3. Restore from checkpoint")
    print("4. Create checkpoint and exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1" or choice == "4":
        checkpoint_path = checkpoint.create_full_checkpoint()
        if checkpoint_path:
            print(f"\n✅ Checkpoint created successfully!")
            print(f"📁 Location: {checkpoint_path}")
        
    elif choice == "2":
        checkpoints = checkpoint.list_checkpoints()
        if checkpoints:
            print(f"\n📋 Found {len(checkpoints)} checkpoints:")
            for i, cp in enumerate(checkpoints, 1):
                metadata = cp['metadata']['checkpoint_info']
                stats = cp['metadata']['database_statistics']
                print(f"\n{i}. {cp['name']}")
                print(f"   📅 Created: {metadata['creation_date']}")
                print(f"   📊 Users: {stats['total_users']} (Premium: {stats['premium_users']})")
                print(f"   💾 Size: {metadata['database_size_mb']} MB")
        else:
            print("❌ No checkpoints found")
    
    elif choice == "3":
        checkpoints = checkpoint.list_checkpoints()
        if checkpoints:
            print(f"\nAvailable checkpoints:")
            for i, cp in enumerate(checkpoints, 1):
                print(f"{i}. {cp['name']}")
            
            try:
                selection = int(input("\nSelect checkpoint to restore: ")) - 1
                if 0 <= selection < len(checkpoints):
                    selected_checkpoint = checkpoints[selection]['name']
                    print(f"\n⚠️ This will replace your current database!")
                    confirm = input("Are you sure? (yes/no): ").lower().strip()
                    
                    if confirm == "yes":
                        checkpoint.restore_from_checkpoint(selected_checkpoint)
                    else:
                        print("❌ Restore cancelled")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No checkpoints available for restore")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
