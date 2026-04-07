
#!/usr/bin/env python3
"""
Script untuk membersihkan file-file yang tidak terpakai di project CryptoMentor AI
"""

import os
import shutil
from datetime import datetime

def cleanup_unused_files():
    """Membersihkan file-file yang tidak terpakai"""
    print("🧹 Starting CryptoMentor AI Cleanup Process")
    print("=" * 50)
    
    # Files yang aman untuk dihapus
    files_to_remove = [
        # Test files
        "Bismillah/test_admin_agent.py",
        "Bismillah/test_analyze_command.py", 
        "Bismillah/test_binance_connection.py",
        "Bismillah/test_bot_response.py",
        "Bismillah/test_coinglass_provider.py",
        "Bismillah/test_fixed_apis.py",
        "Bismillah/test_new_apis.py",
        "Bismillah/test_supabase_connection.py",
        "Bismillah/test_supabase_crud.py",
        "tools/test_supabase_rpc.py",
        
        # Setup files
        "Bismillah/setup_coinapi.py",
        "Bismillah/setup_coinglass_v4.py",
        "Bismillah/setup_supabase_tables.py",
        
        # Migration/utility files
        "Bismillah/migrate_to_new_apis.py",
        "Bismillah/fix_database_users.py",
        "Bismillah/auto_backup.py",
        "Bismillah/preserve_premium_users.py",
        
        # Old provider files
        "Bismillah/coinglass_provider.py",
        "Bismillah/coinmarketcap_provider.py", 
        "Bismillah/binance_provider.py",
        
        # Database files yang redundan
        "Bismillah/database_checkpoint.py",
        "Bismillah/database_recovery.py",
        "Bismillah/supabase_client.py",
        
        # Config/check files
        "Bismillah/check_api_health.py",
        "Bismillah/check_connection_status.py",
        "Bismillah/system_health.py",
        "Bismillah/config.py",
        
        # Handler files yang tidak terintegrasi
        "Bismillah/handlers_sb.py",
        "Bismillah/menu_handler.py",
        
        # Backup files
        "Bismillah/premium_users_backup_20250802_130229.json",
        
        # Lock files
        "Bismillah/uv.lock",
        "uv.lock",
        
        # Utility files
        "kill_bot_instances.py",
        "=1.0.0",
        
        # Data provider
        "Bismillah/data_provider.py"
    ]
    
    # Directories yang bisa dihapus jika kosong setelah cleanup
    dirs_to_check = [
        "tools",
        "attached_assets"  # Folder dengan banyak file temporary
    ]
    
    removed_count = 0
    skipped_count = 0
    
    print("🗑️ Removing unused files:")
    
    # Remove files
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  ✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {file_path}: {e}")
                skipped_count += 1
        else:
            print(f"  ⏭️ Already missing: {file_path}")
    
    print(f"\n📂 Checking directories for cleanup:")
    
    # Handle attached_assets directory specially (has many temporary files)
    if os.path.exists("attached_assets"):
        try:
            files_in_assets = os.listdir("attached_assets")
            if files_in_assets:
                print(f"  📁 attached_assets contains {len(files_in_assets)} files")
                confirm = input("    Remove all files in attached_assets? (y/N): ").lower().strip()
                if confirm == 'y':
                    shutil.rmtree("attached_assets")
                    os.makedirs("attached_assets")  # Recreate empty directory
                    print(f"  ✅ Cleaned attached_assets directory")
                    removed_count += len(files_in_assets)
                else:
                    print(f"  ⏭️ Skipped attached_assets directory")
            else:
                print(f"  📁 attached_assets is already empty")
        except Exception as e:
            print(f"  ❌ Error handling attached_assets: {e}")
    
    # Remove empty directories
    for dir_path in dirs_to_check:
        if dir_path != "attached_assets" and os.path.exists(dir_path):
            try:
                if not os.listdir(dir_path):  # Directory is empty
                    os.rmdir(dir_path)
                    print(f"  ✅ Removed empty directory: {dir_path}")
                    removed_count += 1
                else:
                    print(f"  📁 Directory not empty: {dir_path}")
            except Exception as e:
                print(f"  ❌ Failed to remove directory {dir_path}: {e}")
    
    # Clean up database files if confirmed
    db_files = ["cryptomentor.db", "Bismillah/cryptomentor.db"]
    db_found = [f for f in db_files if os.path.exists(f)]
    
    if db_found:
        print(f"\n💾 Found database files: {db_found}")
        print("⚠️ These files contain user data. Only remove if fully migrated to Supabase.")
        confirm_db = input("Remove database files? (y/N): ").lower().strip()
        
        if confirm_db == 'y':
            for db_file in db_found:
                try:
                    # Create backup first
                    backup_name = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(db_file, backup_name)
                    print(f"  💾 Backup created: {backup_name}")
                    
                    os.remove(db_file)
                    print(f"  ✅ Removed: {db_file}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to remove {db_file}: {e}")
        else:
            print("  ⏭️ Skipped database files")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CLEANUP SUMMARY:")
    print(f"✅ Files removed: {removed_count}")
    print(f"❌ Files skipped: {skipped_count}")
    
    if removed_count > 0:
        print("\n🎉 Cleanup completed successfully!")
        print("💡 Your project is now cleaner and more organized.")
    else:
        print("\n✨ Project was already clean!")
    
    print("\n🔍 Core files preserved:")
    core_files = [
        "Bismillah/main.py",
        "Bismillah/bot.py", 
        "Bismillah/ai_assistant.py",
        "Bismillah/snd_zone_detector.py",
        "Bismillah/crypto_api.py",
        "Bismillah/menu_handlers.py"
    ]
    
    for core_file in core_files:
        if os.path.exists(core_file):
            print(f"  ✅ {core_file}")
        else:
            print(f"  ⚠️ {core_file} - MISSING!")

if __name__ == "__main__":
    cleanup_unused_files()
