import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('/root/cryptomentor-bot/website-backend/.env')
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

tg_id = 8263889133
code = 'navicrypto'

uv = s.table('user_verifications').select('*').eq('telegram_id', tg_id).limit(1).execute()
print('user_verifications_before=', uv.data)

cp = s.table('community_partners').select('*').eq('community_code', code).limit(1).execute()
print('community_partner=', cp.data)
