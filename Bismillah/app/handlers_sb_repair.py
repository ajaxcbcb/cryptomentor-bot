
from telegram import Update
from telegram.ext import ContextTypes
from app.lib.guards import admin_guard
from app.safe_send import safe_reply

REPAIR_SQL = """-- RUN di Supabase SQL Editor
create extension if not exists "uuid-ossp";

create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  telegram_id bigint unique,
  is_premium boolean not null default false,
  premium_until timestamptz,
  credits integer not null default 0,
  banned boolean not null default false,
  updated_at timestamptz default now()
);

create unique index if not exists users_telegram_id_idx on public.users(telegram_id);

alter table public.users enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies where tablename='users' and policyname='allow_service_role_all') then
    create policy allow_service_role_all on public.users
      for all
      to service_role
      using (true)
      with check (true);
  end if;
end$$;
"""

@admin_guard
async def cmd_sb_repair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update.effective_message, "🛠️ **Supabase RLS/Schema Repair SQL:**\n\n```sql\n" + REPAIR_SQL + "\n```\n\n**Instructions:**\n1. Copy SQL above\n2. Open Supabase SQL Editor\n3. Paste & RUN (once only)\n4. Test with /sb_status")
