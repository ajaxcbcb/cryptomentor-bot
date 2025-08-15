
-- Setup users table for CryptoMentor AI
-- Run this in Supabase SQL Editor if table doesn't exist

create table if not exists users (
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

-- Enable RLS (Row Level Security)
alter table users enable row level security;

-- Create policy for service role (allows all operations)
create policy "Service role can do anything" on users
  for all using (auth.role() = 'service_role');

-- Create policy for authenticated users (can only see their own data)
create policy "Users can view own data" on users
  for select using (auth.uid()::text = telegram_id::text);

-- Create indexes for better performance
create index if not exists idx_users_telegram_id on users(telegram_id);
create index if not exists idx_users_is_premium on users(is_premium);
create index if not exists idx_users_referred_by on users(referred_by);

-- Create updated_at trigger
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language 'plpgsql';

create trigger update_users_updated_at before update on users
  for each row execute procedure update_updated_at_column();
