-- Migration: user_skills
-- Menyimpan skill premium yang dibeli user per-item
-- Idempotent — aman dijalankan ulang

create table if not exists public.user_skills (
  id           bigserial primary key,
  telegram_id  bigint not null references public.users(telegram_id) on delete cascade,
  skill_id     text not null,          -- e.g. 'dual_tp_rr3', 'trailing_sl', dst.
  purchased_at timestamptz not null default now(),
  expires_at   timestamptz,            -- NULL = selamanya
  price_credits integer not null default 0,
  unique(telegram_id, skill_id)
);

create index if not exists idx_user_skills_tg on public.user_skills(telegram_id);

alter table public.user_skills enable row level security;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'user_skills' and policyname = 'user_skills_service_only'
  ) then
    execute 'create policy user_skills_service_only on public.user_skills for all using (true) with check (true)';
  end if;
end $$;
