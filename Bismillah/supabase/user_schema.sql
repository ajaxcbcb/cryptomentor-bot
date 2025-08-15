
-- Enable required extensions
create extension if not exists pgcrypto;

-- USERS: menyimpan profil + premium + referral + credits
create table if not exists users (
  id text primary key,                    -- telegram user id (string)
  username text default '' not null,
  is_admin boolean default false not null,

  -- Premium flags
  is_lifetime boolean default false not null,
  premium_until timestamptz,              -- null jika lifetime; boleh null jika non-premium
  -- Derived premium status dihitung di aplikasi: is_lifetime OR (premium_until >= now())

  -- Ekonomi
  credits integer default 0 not null,

  -- Referral
  referral_code text unique,              -- kode milik user (unik)
  referred_by text references users(id) on delete set null, -- siapa yang mereferensikan user ini (opsional)

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- LOG: menyimpan event referral (opsional, buat audit)
create table if not exists referral_events (
  id uuid primary key default gen_random_uuid(),
  referred_user_id text not null references users(id) on delete cascade,
  referrer_user_id text not null references users(id) on delete cascade,
  source text default 'start' not null,       -- mis: 'start', 'link', dsb
  created_at timestamptz default now()
);

-- Index berguna
create index if not exists idx_users_referral_code on users(referral_code);
create index if not exists idx_users_referred_by on users(referred_by);
create index if not exists idx_ref_events_referrer on referral_events(referrer_user_id);

-- Trigger untuk updated_at
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

do $$
begin
  if not exists (select 1 from pg_trigger where tgname = 'users_set_updated_at') then
    create trigger users_set_updated_at
    before update on users
    for each row execute function set_updated_at();
  end if;
end;
$$;

-- RLS (opsional - karena server pakai SERVICE KEY, aman)
alter table users enable row level security;
alter table referral_events enable row level security;

-- Policies minimal (server w/ service key override policies)
create policy if not exists "service select users" on users for select using (true);
create policy if not exists "service ins/upd/del users" on users for all using (true) with check (true);

create policy if not exists "service all referral_events" on referral_events for all using (true) with check (true);
