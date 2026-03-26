-- ============================================================
-- Whitelabel License Billing — Database Schema
-- Central Supabase (Pusat)
-- ============================================================

-- Enum types
CREATE TYPE wl_status AS ENUM ('active', 'grace_period', 'suspended', 'inactive');
CREATE TYPE billing_status AS ENUM ('success', 'failed');

-- ============================================================
-- Tabel utama lisensi
-- ============================================================
CREATE TABLE wl_licenses (
    wl_id             UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    balance_usdt      DECIMAL(18, 6)  NOT NULL DEFAULT 0 CHECK (balance_usdt >= 0),
    expires_at        TIMESTAMPTZ     NOT NULL,
    status            wl_status       NOT NULL DEFAULT 'inactive',
    monthly_fee       DECIMAL(10, 2)  NOT NULL DEFAULT 100,
    deposit_address   VARCHAR(42)     NOT NULL,
    deposit_index     INTEGER         NOT NULL UNIQUE,
    secret_key        UUID            NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    admin_telegram_id BIGINT          NOT NULL,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Riwayat deposit (idempotency via tx_hash UNIQUE)
-- ============================================================
CREATE TABLE wl_deposits (
    id           BIGSERIAL       PRIMARY KEY,
    wl_id        UUID            NOT NULL REFERENCES wl_licenses(wl_id),
    tx_hash      VARCHAR(66)     NOT NULL UNIQUE,
    amount_usdt  DECIMAL(18, 6)  NOT NULL,
    block_number BIGINT          NOT NULL,
    confirmed_at TIMESTAMPTZ     NOT NULL,
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Riwayat billing
-- ============================================================
CREATE TABLE wl_billing_history (
    id               BIGSERIAL       PRIMARY KEY,
    wl_id            UUID            NOT NULL REFERENCES wl_licenses(wl_id),
    amount_usdt      DECIMAL(10, 2)  NOT NULL,
    billing_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    status           billing_status  NOT NULL,
    balance_before   DECIMAL(18, 6)  NOT NULL,
    balance_after    DECIMAL(18, 6)  NOT NULL,
    expires_at_before TIMESTAMPTZ,
    expires_at_after  TIMESTAMPTZ,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX idx_wl_deposits_wl_id      ON wl_deposits(wl_id);
CREATE INDEX idx_wl_billing_wl_id       ON wl_billing_history(wl_id);
CREATE INDEX idx_wl_licenses_status     ON wl_licenses(status);
CREATE INDEX idx_wl_licenses_expires_at ON wl_licenses(expires_at);

-- ============================================================
-- Row Level Security — hanya service_role yang bisa write
-- ============================================================
ALTER TABLE wl_licenses        ENABLE ROW LEVEL SECURITY;
ALTER TABLE wl_deposits        ENABLE ROW LEVEL SECURITY;
ALTER TABLE wl_billing_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_only_write" ON wl_licenses
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_only_write" ON wl_deposits
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_only_write" ON wl_billing_history
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- Supabase RPC: process_billing (atomic billing per WL)
-- ============================================================
CREATE OR REPLACE FUNCTION process_billing(p_wl_id UUID)
RETURNS JSON LANGUAGE plpgsql AS $$
DECLARE
    lic        wl_licenses%ROWTYPE;
    bal_before DECIMAL;
    bal_after  DECIMAL;
    exp_before TIMESTAMPTZ;
    exp_after  TIMESTAMPTZ;
    new_status wl_status;
    result     JSON;
BEGIN
    -- Lock row untuk atomic update
    SELECT * INTO lic FROM wl_licenses WHERE wl_id = p_wl_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'WL not found: %', p_wl_id;
    END IF;

    bal_before := lic.balance_usdt;
    exp_before := lic.expires_at;

    IF lic.balance_usdt >= lic.monthly_fee THEN
        -- Billing sukses: kurangi balance, perpanjang 30 hari
        bal_after  := lic.balance_usdt - lic.monthly_fee;
        exp_after  := lic.expires_at + INTERVAL '30 days';
        new_status := 'active';

        UPDATE wl_licenses
        SET balance_usdt = bal_after,
            expires_at   = exp_after,
            status       = new_status
        WHERE wl_id = p_wl_id;

        INSERT INTO wl_billing_history
            (wl_id, amount_usdt, status, balance_before, balance_after,
             expires_at_before, expires_at_after)
        VALUES
            (p_wl_id, lic.monthly_fee, 'success', bal_before, bal_after,
             exp_before, exp_after);
    ELSE
        -- Balance tidak cukup: set grace_period, balance tidak berubah
        bal_after  := bal_before;
        exp_after  := exp_before;
        new_status := 'grace_period';

        -- Hanya update status jika belum grace_period (idempotent)
        UPDATE wl_licenses
        SET status = new_status
        WHERE wl_id = p_wl_id AND status != 'grace_period';

        INSERT INTO wl_billing_history
            (wl_id, amount_usdt, status, balance_before, balance_after,
             expires_at_before, expires_at_after)
        VALUES
            (p_wl_id, lic.monthly_fee, 'failed', bal_before, bal_after,
             exp_before, exp_after);
    END IF;

    result := json_build_object(
        'success',        new_status = 'active',
        'balance_before', bal_before,
        'balance_after',  bal_after,
        'new_status',     new_status,
        'expires_at',     exp_after
    );
    RETURN result;
END;
$$;

-- ============================================================
-- Supabase RPC: increment_balance (atomic balance update)
-- Digunakan oleh credit_balance untuk menghindari race condition.
-- ============================================================
CREATE OR REPLACE FUNCTION increment_balance(p_wl_id UUID, p_amount DECIMAL)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE wl_licenses
    SET balance_usdt = balance_usdt + p_amount
    WHERE wl_id = p_wl_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'WL not found: %', p_wl_id;
    END IF;
END;
$$;
