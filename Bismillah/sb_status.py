
#!/usr/bin/env python3
"""
CLI tester untuk koneksi Supabase
Jalankan: python sb_status.py
"""

from supabase_conn import health

def main():
    print("🔍 Testing Supabase connection...")
    ok, detail = health()
    
    if ok:
        print(f"✅ Supabase: {detail}")
    else:
        print(f"❌ Supabase: {detail}")
        
        # Troubleshooting hints
        if "SUPABASE_URL belum diset" in detail:
            print("💡 Set SUPABASE_URL in Replit Secrets")
        elif "tidak valid" in detail:
            print("💡 Use project URL: https://<ref>.supabase.co (not dashboard URL)")
        elif "SUPABASE_SERVICE_KEY belum diset" in detail:
            print("💡 Set SUPABASE_SERVICE_KEY (service_role key) in Replit Secrets")
        elif "table_status=404" in detail:
            print("💡 Create 'users' table in Supabase SQL Editor")
        elif "401" in detail or "403" in detail:
            print("💡 Check if you're using service_role key (not anon key)")

if __name__ == "__main__":
    main()
