-- Unified UID verification source of truth for web + telegram.
-- Run this in Supabase SQL editor using service-role/admin permissions.

create table if not exists public.user_verifications (
  telegram_id bigint primary key references public.users(telegram_id) on delete cascade,
  bitunix_uid text not null,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  submitted_via text not null default 'web' check (submitted_via in ('web', 'telegram')),
  submitted_at timestamptz not null default now(),
  reviewed_at timestamptz,
  reviewed_by_admin_id bigint,
  rejection_reason text,
  updated_at timestamptz not null default now()
);

create index if not exists idx_user_verifications_status on public.user_verifications(status);
create unique index if not exists idx_user_verifications_bitunix_uid on public.user_verifications(bitunix_uid);

create or replace function public.set_updated_at_user_verifications()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_user_verifications_updated_at on public.user_verifications;
create trigger trg_user_verifications_updated_at
before update on public.user_verifications
for each row execute function public.set_updated_at_user_verifications();

alter table public.user_verifications enable row level security;

-- User can read only own verification record.
drop policy if exists "uv_select_own" on public.user_verifications;
create policy "uv_select_own"
on public.user_verifications
for select
to authenticated
using ((auth.jwt() ->> 'sub')::bigint = telegram_id);

-- User can create own pending request.
drop policy if exists "uv_insert_own_pending" on public.user_verifications;
create policy "uv_insert_own_pending"
on public.user_verifications
for insert
to authenticated
with check (
  (auth.jwt() ->> 'sub')::bigint = telegram_id
  and status = 'pending'
);

-- User can resubmit own UID to pending state only.
drop policy if exists "uv_update_own_pending_only" on public.user_verifications;
create policy "uv_update_own_pending_only"
on public.user_verifications
for update
to authenticated
using ((auth.jwt() ->> 'sub')::bigint = telegram_id)
with check (
  (auth.jwt() ->> 'sub')::bigint = telegram_id
  and status = 'pending'
);

-- Optional: backfill from legacy autotrade_sessions if records already exist.
insert into public.user_verifications (
  telegram_id,
  bitunix_uid,
  status,
  submitted_via,
  submitted_at,
  updated_at
)
select
  s.telegram_id,
  coalesce(nullif(s.bitunix_uid, ''), s.telegram_id::text) as bitunix_uid,
  case
    when s.status in ('uid_verified', 'active') then 'approved'
    when s.status = 'uid_rejected' then 'rejected'
    when s.status = 'pending_verification' then 'pending'
    else 'pending'
  end as status,
  'telegram' as submitted_via,
  coalesce(s.updated_at, now()) as submitted_at,
  coalesce(s.updated_at, now()) as updated_at
from public.autotrade_sessions s
where s.bitunix_uid is not null
on conflict (telegram_id) do update
set
  bitunix_uid = excluded.bitunix_uid,
  status = excluded.status,
  updated_at = now();

-- Allow bitunix_uid to be NULL (admin may reject before UID is submitted)
alter table public.user_verifications alter column bitunix_uid drop not null;
