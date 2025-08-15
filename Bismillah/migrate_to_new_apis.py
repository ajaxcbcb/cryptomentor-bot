
#!/usr/bin/env python3
"""
Migration helper script to update from old API structure to new modular structure
"""

import os
import shutil
import logging
from datetime import datetime

def backup_old_files():
    """Backup old API files"""
    backup_dir = f"backup_old_apis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    files_to_backup = [
        'setup_coinapi.py',
        'setup_coinglass_v4.py'
    ]
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Backed up {file}")
    
    print(f"📦 Old files backed up to: {backup_dir}")

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = [
        'COINGLASS_API_KEY',
        'CMC_API_KEY',
        'COINMARKETCAP_API_KEY'  # Alternative name
    ]
    
    print("\n🔍 Checking environment variables...")
    
    coinglass_key = os.getenv('COINGLASS_API_KEY')
    cmc_key = os.getenv('CMC_API_KEY') or os.getenv('COINMARKETCAP_API_KEY')
    
    if coinglass_key:
        print(f"✅ COINGLASS_API_KEY: Configured ({coinglass_key[:8]}...)")
    else:
        print("❌ COINGLASS_API_KEY: Not found")
    
    if cmc_key:
        print(f"✅ CMC_API_KEY: Configured ({cmc_key[:8]}...)")
    else:
        print("❌ CMC_API_KEY: Not found")
    
    if not coinglass_key or not cmc_key:
        print("\n⚠️ Missing API keys! Please add them to Replit Secrets:")
        if not coinglass_key:
            print("  - Add COINGLASS_API_KEY")
        if not cmc_key:
            print("  - Add CMC_API_KEY (or COINMARKETCAP_API_KEY)")
        return False
    
    return True

def test_new_apis():
    """Test the new API structure"""
    print("\n🧪 Testing new API structure...")
    
    try:
        from data_provider import data_provider
        from crypto_api import crypto_api
        
        # Quick API test
        test_result = data_provider.test_all_apis()
        
        print(f"📊 API Test Results:")
        print(f"  Overall Status: {test_result.get('overall_status', 'unknown').upper()}")
        print(f"  Working APIs: {test_result.get('working_apis', 0)}/{test_result.get('total_apis', 0)}")
        
        for api_name, api_result in test_result.get('apis', {}).items():
            status = api_result.get('status', 'unknown')
            status_emoji = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
            print(f"  {status_emoji} {api_name.title()}: {status}")
        
        return test_result.get('overall_status') not in ['poor', 'error']
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 CryptoMentor API Migration Script")
    print("="*50)
    
    # Step 1: Backup old files
    backup_old_files()
    
    # Step 2: Check environment variables
    if not check_environment_variables():
        print("\n❌ Migration aborted due to missing API keys")
        return False
    
    # Step 3: Test new APIs
    if not test_new_apis():
        print("\n❌ Migration completed but API tests failed")
        print("Please check your API keys and network connection")
        return False
    
    # Step 4: Success
    print("\n✅ Migration completed successfully!")
    print("\n📋 Next steps:")
    print("  1. Run 'python test_new_apis.py' for comprehensive testing")
    print("  2. Update your bot code to use the new crypto_api module")
    print("  3. Remove old API files if everything works correctly")
    print("\n🎉 Your CryptoMentor bot is now using the new modular API structure!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
