import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('/root/cryptomentor-bot/website-backend/.env')
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

tg_id = 8263889133
users = s.table('users').select('*').eq('telegram_id', tg_id).limit(1).execute()
row = (users.data or [None])[0]
print('users_row=', row)
if row:
    print('users_columns=', sorted(row.keys()))
