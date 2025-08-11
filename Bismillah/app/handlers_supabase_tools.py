
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import health, upsert_user_tid, sb_list_users

REPAIR_SQL = """-- RUN IN SUPABASE SQL EDITOR (sekali saja)
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
      using (true) with check (true);
  end if;
end$$;
"""

@admin_guard
async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, info = health()
    
    # Additional stats
    try:
        users = sb_list_users({}, limit=5)
        premium_users = sb_list_users({"is_premium": "eq.true"}, limit=1000)
        stats = f"\n👥 Total users sample: {len(users)}\n💎 Premium users: {len(premium_users)}"
    except Exception as e:
        stats = f"\n❌ Stats error: {e}"
    
    await safe_reply(update.effective_message, f"🗄️ Supabase: {'✅ OK' if ok else '❌ FAIL'}\n{info}{stats}")

@admin_guard
async def cmd_sb_diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Test upsert
        test_tid = 999999999
        result = upsert_user_tid(test_tid, test_probe=True, credits=100)
        
        # Test read
        read_back = sb_list_users({"telegram_id": f"eq.{test_tid}"}, limit=1)
        
        await safe_reply(update.effective_message, 
                        f"🔍 Upsert test OK (service key & policy aman)\n"
                        f"Write result: {result}\n"
                        f"Read back: {read_back}")
    except Exception as e:
        await safe_reply(update.effective_message, f"🔍 Upsert test FAIL: {e}")

@admin_guard
async def cmd_sb_repair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update.effective_message, "🛠️ Jalankan SQL ini di Supabase SQL Editor:\n```\n"+REPAIR_SQL+"\n```", parse_mode='Markdown')

@admin_guard
async def cmd_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /ban <userid>")

    tid = int(context.args[0])
    try:
        upsert_user_tid(tid, banned=True)
        await safe_reply(msg, f"✅ User {tid} banned")
    except Exception as e:
        await safe_reply(msg, f"❌ Error banning user: {e}")

@admin_guard
async def cmd_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /unban <userid>")

    tid = int(context.args[0])
    try:
        upsert_user_tid(tid, banned=False)
        await safe_reply(msg, f"✅ User {tid} unbanned")
    except Exception as e:
        await safe_reply(msg, f"❌ Error unbanning user: {e}")
