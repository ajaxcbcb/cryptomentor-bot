-- Migration: tambah kolom margin_mode dan bitunix_uid ke autotrade_sessions
-- Jalankan di Supabase SQL Editor

ALTER TABLE public.autotrade_sessions
  ADD COLUMN IF NOT EXISTS margin_mode text NOT NULL DEFAULT 'cross';

ALTER TABLE public.autotrade_sessions
  ADD COLUMN IF NOT EXISTS bitunix_uid text;
