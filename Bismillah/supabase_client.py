
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Validate that required environment variables are present
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables. Please add them to Replit Secrets.")

# Create global supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("✅ Supabase client initialized successfully")
