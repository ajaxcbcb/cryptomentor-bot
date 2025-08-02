
import os
import time

def force_deployment_mode():
    """Force the bot into real-time deployment mode"""
    
    # Create deployment indicators
    try:
        # Create deployment flag file
        with open('/tmp/repl_deployment_flag', 'w') as f:
            f.write(f"forced_deployment_mode_{int(time.time())}")
        print("✅ Created deployment flag file")
        
        # Set environment variables for this session
        os.environ['REPLIT_DEPLOYMENT'] = '1'
        os.environ['FORCE_REALTIME'] = '1'
        print("✅ Set deployment environment variables")
        
        # Verify deployment detection
        deployment_checks = {
            'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
            'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
            'deployment_flag_file': os.path.exists('/tmp/repl_deployment_flag'),
            'replit_slug': bool(os.getenv('REPL_SLUG')),
            'replit_owner': bool(os.getenv('REPL_OWNER')),
            'force_realtime': os.getenv('FORCE_REALTIME') == '1'
        }
        
        print("\n🔍 Deployment Detection Status:")
        for check, result in deployment_checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}: {result}")
        
        is_deployment = any(deployment_checks.values())
        print(f"\n📊 Overall Status: {'✅ DEPLOYMENT MODE ACTIVE' if is_deployment else '❌ STILL IN DEV MODE'}")
        
        if is_deployment:
            print("\n🚀 Bot will now use REAL-TIME mode for all API calls!")
            print("💡 Restart the bot to apply changes")
        else:
            print("\n❌ Failed to activate deployment mode")
            
        return is_deployment
        
    except Exception as e:
        print(f"❌ Error forcing deployment mode: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Forcing Real-Time Deployment Mode...")
    force_deployment_mode()
