
import os

# Rate limiting configuration
USE_RATE_LIMIT = os.getenv("USE_RATE_LIMIT", "true").lower() in ("1", "true", "yes")
RATE_LIMIT_QPS = float(os.getenv("RATE_LIMIT_QPS", "1.5"))  # ~1–2 req/detik per user
BURST_TOKENS = int(os.getenv("BURST_TOKENS", "3"))          # burst kecil

# Auto signals configuration
AUTO_SIGNALS_ENABLED = os.getenv("AUTO_SIGNALS_ENABLED", "false").lower() in ("1", "true", "yes")

# API configuration
COINAPI_ENABLED = os.getenv("COINAPI_ENABLED", "true").lower() in ("1", "true", "yes")
BINANCE_ENABLED = os.getenv("BINANCE_ENABLED", "true").lower() in ("1", "true", "yes")
CMC_ENABLED = os.getenv("CMC_ENABLED", "true").lower() in ("1", "true", "yes")
