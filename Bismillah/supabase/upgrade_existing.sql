
-- Upgrade existing users table with new columns
alter table users add column if not exists is_lifetime boolean default false not null;
alter table users add column if not exists premium_until timestamptz;
alter table users add column if not exists credits integer default 0 not null;
alter table users add column if not exists referral_code text;
alter table users add column if not exists referred_by text references users(id) on delete set null;

-- Create unique index for referral codes
create unique index if not exists idx_users_refcode_unique on users(referral_code);

-- Create referral_events table if not exists
create table if not exists referral_events (
  id uuid primary key default gen_random_uuid(),
  referred_user_id text not null references users(id) on delete cascade,
  referrer_user_id text not null references users(id) on delete cascade,
  source text default 'start' not null,
  created_at timestamptz default now()
);

-- Indexes
create index if not exists idx_users_referred_by on users(referred_by);
create index if not exists idx_ref_events_referrer on referral_events(referrer_user_id);
