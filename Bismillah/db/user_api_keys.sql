-- Migration: user_api_keys + autotrade_sessions
-- Idempotent — aman dijalankan ulang
-- API Secret user disimpan terenkripsi AES-256-GCM (enkripsi di sisi app, bukan DB)

-- ── user_api_keys ──────────────────────────────────────────────────
create table if not exists public.user_api_keys (
  id             bigserial primary key,
  telegram_id    bigint unique not null references public.users(telegram_id) on delete cascade,
  exchange       text not null default 'bitunix',
  api_key        text not null,
  api_secret_enc text not null,   -- AES-256-GCM encrypted (app/lib/crypto.py)
  key_hint       text,            -- 4 char terakhir api_key untuk display
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create index if not exists idx_user_api_keys_tg on public.user_api_keys(telegram_id);

drop trigger if exists tg_user_api_keys_updated on public.user_api_keys;
create trigger tg_user_api_keys_updated
  before update on public.user_api_keys
  for each row execute procedure public.tg_touch_updated_at();

alter table public.user_api_keys enable row level security;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'user_api_keys' and policyname = 'api_keys_service_only'
  ) then
    execute 'create policy api_keys_service_only on public.user_api_keys for all using (true) with check (true)';
  end if;
end $$;

-- ── autotrade_sessions ─────────────────────────────────────────────
create table if not exists public.autotrade_sessions (
  id               bigserial primary key,
  telegram_id      bigint unique not null references public.users(telegram_id) on delete cascade,
  initial_deposit  numeric(18,8) not null default 0,
  current_balance  numeric(18,8) not null default 0,
  total_profit     numeric(18,8) not null default 0,
  status           text not null default 'inactive',
  started_at       timestamptz,
  updated_at       timestamptz not null default now()
);

create index if not exists idx_autotrade_sessions_tg on public.autotrade_sessions(telegram_id);

drop trigger if exists tg_autotrade_sessions_updated on public.autotrade_sessions;
create trigger tg_autotrade_sessions_updated
  before update on public.autotrade_sessions
  for each row execute procedure public.tg_touch_updated_at();

alter table public.autotrade_sessions enable row level security;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'autotrade_sessions' and policyname = 'autotrade_sessions_service_only'
  ) then
    execute 'create policy autotrade_sessions_service_only on public.autotrade_sessions for all using (true) with check (true)';
  end if;
end $$;
