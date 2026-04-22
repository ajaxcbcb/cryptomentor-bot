import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
ADMIN_IDS  = [
    int(x.strip()) for x in [
        os.getenv("ADMIN1", ""),
        os.getenv("ADMIN2", ""),
        os.getenv("ADMIN3", ""),
    ] if x.strip()
]

# ── Supabase ──────────────────────────────────────────
SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ── AI ────────────────────────────────────────────────
DEEPSEEK_API_KEY  = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://openrouter.ai/api/v1")
AI_MODEL          = os.getenv("AI_MODEL", "google/gemini-flash-1.5")

# ── Crypto Data Providers (TERPISAH dari pusat) ───────
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY", "")
HELIUS_API_KEY        = os.getenv("HELIUS_API_KEY", "")
COINGECKO_API_KEY     = os.getenv("COINGECKO_API_KEY", "")
CRYPTONEWS_API_KEY    = os.getenv("CRYPTONEWS_API_KEY", "")

# ── Bitunix ───────────────────────────────────────────
BITUNIX_BASE_URL = os.getenv("BITUNIX_BASE_URL", "https://fapi.bitunix.com")
BITUNIX_WS_URL   = os.getenv("BITUNIX_WS_URL", "wss://fapi.bitunix.com/private")

# ── License (WL#1 credentials untuk License Guard) ───
WL_ID          = os.getenv("WL_ID", "")
WL_SECRET_KEY  = os.getenv("WL_SECRET_KEY", "")
LICENSE_API_URL = os.getenv("LICENSE_API_URL", "")

# ── Bot Settings ──────────────────────────────────────
WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "100"))
BOT_NAME        = os.getenv("BOT_NAME", "CryptoMentor AI")
BOT_TAGLINE     = os.getenv("BOT_TAGLINE", "Your AI Crypto Trading Assistant")
