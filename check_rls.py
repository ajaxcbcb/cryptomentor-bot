import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

from supabase import create_client

url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_KEY')
anon_key = os.getenv('SUPABASE_ANON_KEY')

print(f"Service key role: {service_key.split('.')[1][:20] if service_key else 'none'}...")
print(f"Anon key role: {anon_key.split('.')[1][:20] if anon_key else 'none'}...")

# Test with service key
s_service = create_client(url, service_key)
r1 = s_service.table('user_api_keys').select('telegram_id').execute()
print(f"\nWith SERVICE key: {len(r1.data or [])} rows")

# Test with anon key
s_anon = create_client(url, anon_key)
r2 = s_anon.table('user_api_keys').select('telegram_id').execute()
print(f"With ANON key: {len(r2.data or [])} rows")
