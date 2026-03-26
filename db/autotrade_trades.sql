-- Migration: autotrade_trades
-- Menyimpan history setiap trade dari /autotrade
-- Idempotent — aman dijalankan ulang

create table if not exists public.autotrade_trades (
  id              bigserial primary key,
  telegram_id     bigint not null references public.users(telegram_id) on delete cascade,
  symbol          text not null,
  side            text not null,          -- LONG / SHORT
  entry_price     numeric(18,8),
  exit_price      numeric(18,8),
  qty             numeric(18,8),
  leverage        integer,
  tp_price        numeric(18,8),
  sl_price        numeric(18,8),
  pnl_usdt        numeric(18,8),          -- realized PnL saat close (null jika masih open)
  status          text not null default 'open',  -- open / closed_tp / closed_sl / closed_flip / closed_manual
  confidence      integer,                -- confidence % saat entry
  rr_ratio        numeric(6,2),
  trend_1h        text,                   -- 1H trend saat entry
  market_structure text,                  -- uptrend/downtrend/ranging saat entry
  rsi_15          numeric(6,2),
  atr_pct         numeric(6,4),
  entry_reasons   jsonb default '[]',     -- array alasan entry dari sinyal
  loss_reasoning  text,                   -- analisis kenapa loss (diisi saat close dengan SL)
  is_flip         boolean default false,  -- apakah ini hasil dari reversal/flip
  order_id        text,                   -- order ID dari Bitunix
  opened_at       timestamptz not null default now(),
  closed_at       timestamptz
);

create index if not exists idx_autotrade_trades_tg     on public.autotrade_trades(telegram_id);
create index if not exists idx_autotrade_trades_status on public.autotrade_trades(status);
create index if not exists idx_autotrade_trades_symbol on public.autotrade_trades(symbol, status);

alter table public.autotrade_trades enable row level security;

do $$ begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'autotrade_trades' and policyname = 'autotrade_trades_service_only'
  ) then
    execute 'create policy autotrade_trades_service_only on public.autotrade_trades for all using (true) with check (true)';
  end if;
end $$;
