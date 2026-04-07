-- Tabel untuk sistem Community Partners
CREATE TABLE IF NOT EXISTS community_partners (
    id                    BIGSERIAL PRIMARY KEY,
    telegram_id           BIGINT NOT NULL UNIQUE,
    community_name        TEXT NOT NULL,
    community_code        TEXT NOT NULL UNIQUE,
    bitunix_uid           TEXT,              -- UID Bitunix ketua komunitas (untuk admin verifikasi)
    bitunix_referral_code TEXT,              -- kode referral Bitunix milik komunitas
    bitunix_referral_url  TEXT,              -- link referral Bitunix milik komunitas
    status                TEXT NOT NULL DEFAULT 'pending',
    member_count          INT DEFAULT 0,
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_community_code ON community_partners (community_code);
CREATE INDEX IF NOT EXISTS idx_community_leader ON community_partners (telegram_id);

ALTER TABLE autotrade_sessions ADD COLUMN IF NOT EXISTS community_code TEXT;

-- Tambah kolom ke tabel yang sudah ada
ALTER TABLE community_partners ADD COLUMN IF NOT EXISTS bitunix_uid TEXT;
ALTER TABLE community_partners ADD COLUMN IF NOT EXISTS bitunix_referral_code TEXT;
ALTER TABLE community_partners ADD COLUMN IF NOT EXISTS bitunix_referral_url TEXT;
