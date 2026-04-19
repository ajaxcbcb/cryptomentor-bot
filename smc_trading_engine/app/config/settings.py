from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    bitunix_base_url: str = os.getenv("BITUNIX_BASE_URL", "https://api.bitunix.com")
    bitunix_api_key: str = os.getenv("BITUNIX_API_KEY", "")
    bitunix_api_secret: str = os.getenv("BITUNIX_API_SECRET", "")
    bitunix_passphrase: str = os.getenv("BITUNIX_PASSPHRASE", "")

    default_leverage: int = int(os.getenv("DEFAULT_LEVERAGE", "20"))
    pair_cooldown_minutes: int = int(os.getenv("PAIR_COOLDOWN_MINUTES", "30"))
    min_confidence_score: float = float(os.getenv("MIN_CONFIDENCE_SCORE", "0.70"))
    db_url: str = os.getenv("DB_URL", "sqlite:///./smc_engine.db")
    redis_url: str = os.getenv("REDIS_URL", "")
    telegram_admin_ids: str = os.getenv("TELEGRAM_ADMIN_IDS", "")
    telegram_auth_enabled: bool = os.getenv("TELEGRAM_AUTH_ENABLED", "false").lower() == "true"

    scan_interval_seconds: int = int(os.getenv("SCAN_INTERVAL_SECONDS", "20"))
    default_timeframes: tuple[str, ...] = tuple(
        tf.strip() for tf in os.getenv("DEFAULT_TIMEFRAMES", "1m,5m,15m,1h").split(",") if tf.strip()
    )

    shadow_mode: bool = os.getenv("SMC_SHADOW_MODE", "true").lower() == "true"
    execution_enabled: bool = os.getenv("SMC_EXECUTION_ENABLED", "false").lower() == "true"


settings = Settings()
