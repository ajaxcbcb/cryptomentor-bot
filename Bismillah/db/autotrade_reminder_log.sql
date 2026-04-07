-- Tabel untuk tracking reminder autotrade yang sudah dikirim
CREATE TABLE IF NOT EXISTS autotrade_reminder_log (
    id           BIGSERIAL PRIMARY KEY,
    telegram_id  BIGINT NOT NULL,
    sent_date    DATE NOT NULL,          -- tanggal terakhir reminder dikirim
    count        INT NOT NULL DEFAULT 1, -- total berapa kali sudah dikirim
    updated_at   TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_reminder_user UNIQUE (telegram_id)
);

-- Index untuk query cepat per tanggal
CREATE INDEX IF NOT EXISTS idx_reminder_log_date ON autotrade_reminder_log (sent_date);
