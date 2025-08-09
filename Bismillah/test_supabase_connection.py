
#!/usr/bin/env python3
"""
Test Supabase connection using the centralized client
"""

try:
    from supabase_client import supabase
    print("✅ Supabase client imported successfully")
    
    # Test basic connection
    result = supabase.table('users').select('count', count='exact').limit(1).execute()
    print(f"✅ Supabase connection test successful - Response: {result}")
    
except Exception as e:
    print(f"❌ Supabase connection test failed: {e}")
    print("💡 Make sure to add SUPABASE_URL and SUPABASE_ANON_KEY to Replit Secrets")
