-- Migration: support multi-exchange per user
-- Jalankan di Supabase SQL Editor

-- 1. Ubah unique constraint user_api_keys dari telegram_id saja
--    menjadi (telegram_id, exchange) agar 1 user bisa punya key di banyak exchange
ALTER TABLE public.user_api_keys
  DROP CONSTRAINT IF EXISTS user_api_keys_telegram_id_key;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'user_api_keys_tg_exchange_key'
  ) THEN
    ALTER TABLE public.user_api_keys
      ADD CONSTRAINT user_api_keys_tg_exchange_key UNIQUE (telegram_id, exchange);
  END IF;
END $$;

-- 2. Tambah kolom exchange ke autotrade_sessions
ALTER TABLE public.autotrade_sessions
  ADD COLUMN IF NOT EXISTS exchange text NOT NULL DEFAULT 'bitunix';

-- 3. Tambah kolom exchange_uid (generik, menggantikan bitunix_uid yang hardcoded)
ALTER TABLE public.autotrade_sessions
  ADD COLUMN IF NOT EXISTS exchange_uid text;

-- 4. Migrate data lama
UPDATE public.autotrade_sessions
  SET exchange_uid = bitunix_uid
  WHERE bitunix_uid IS NOT NULL AND exchange_uid IS NULL;
