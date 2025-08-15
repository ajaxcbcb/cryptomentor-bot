
-- CryptoMentorAI - Setup users table in Supabase
-- Run this in Supabase SQL Editor

-- 1. Enable uuid extension if not exists
create extension if not exists "uuid-ossp";

-- 2. Create users table with all required columns
create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  telegram_id bigint unique not null,
  first_name text,
  last_name text,
  username text,
  language_code text default 'id',
  is_premium boolean not null default false,
  premium_until timestamptz,
  credits integer not null default 100,
  banned boolean not null default false,
  referred_by bigint,
  referral_code text,
  premium_referral_code text,
  premium_earnings integer default 0,
  restart_required boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 3. Enable Row Level Security
alter table public.users enable row level security;

-- 4. Create policy for service role (allows all operations)
create policy "Service role can do anything" on public.users
  for all using (auth.role() = 'service_role');

-- 5. Create policy for authenticated users (can only see their own data)
create policy "Users can view own data" on public.users
  for select using (auth.uid()::text = telegram_id::text);

-- 6. Create indexes for better performance
create unique index if not exists users_telegram_id_idx 
  on public.users(telegram_id);

create index if not exists users_is_premium_idx 
  on public.users(is_premium);

create index if not exists users_referred_by_idx 
  on public.users(referred_by);

create index if not exists users_created_at_idx 
  on public.users(created_at);

-- 7. Create updated_at trigger
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language 'plpgsql';

create trigger update_users_updated_at 
  before update on public.users
  for each row execute procedure update_updated_at_column();

-- 8. Verify table creation
select 'Table users created successfully' as status;
