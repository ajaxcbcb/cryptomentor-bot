
-- CryptoMentor AI Database Schema for Supabase
-- Run this in Supabase SQL Editor if Python script fails

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    language_code TEXT DEFAULT 'id',
    is_premium BOOLEAN DEFAULT FALSE,
    credits INTEGER DEFAULT 100,
    subscription_end TIMESTAMPTZ,
    referred_by BIGINT,
    referral_code TEXT,
    premium_referral_code TEXT,
    premium_earnings INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    plan TEXT,
    status TEXT,
    start_date TIMESTAMPTZ DEFAULT NOW(),
    end_date TIMESTAMPTZ,
    granted_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id)
);

-- Portfolio table
CREATE TABLE IF NOT EXISTS public.portfolio (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    amount DECIMAL NOT NULL,
    avg_buy_price DECIMAL NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id)
);

-- User activity table
CREATE TABLE IF NOT EXISTS public.user_activity (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id)
);

-- Premium referrals table
CREATE TABLE IF NOT EXISTS public.premium_referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    subscription_type TEXT,
    subscription_amount INTEGER,
    earnings INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    FOREIGN KEY (referrer_id) REFERENCES public.users(telegram_id),
    FOREIGN KEY (referred_id) REFERENCES public.users(telegram_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON public.users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON public.users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_premium_referral_code ON public.users(premium_referral_code);
CREATE INDEX IF NOT EXISTS idx_users_is_premium ON public.users(is_premium);

CREATE INDEX IF NOT EXISTS idx_subscriptions_telegram_id ON public.subscriptions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_telegram_id ON public.portfolio(telegram_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON public.user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON public.user_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_premium_referrals_referrer ON public.premium_referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_premium_referrals_referred ON public.users(referred_id);

-- Enable Row Level Security (RLS) if needed
-- ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.portfolio ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.user_activity ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.premium_referrals ENABLE ROW LEVEL SECURITY;

-- Insert test data (optional)
-- INSERT INTO public.users (telegram_id, first_name, username, is_premium) 
-- VALUES (1234500009, 'Admin', 'admin', TRUE)
-- ON CONFLICT (telegram_id) DO NOTHING;
