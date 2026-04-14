#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Entry Point
Simple entry point for Railway deployment
"""

if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    from dotenv import load_dotenv

    # Load env before importing bot modules.
    # 1) Bismillah/.env (if present)
    load_dotenv()
    # 2) repo-root .env (production VPS layout: /root/cryptomentor-bot/.env)
    repo_root = Path(__file__).resolve().parent.parent
    root_env = repo_root / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env, override=False)
    # 3) website-backend/.env for shared auth config (JWT_SECRET, FRONTEND_URL)
    #    Keep override=False so repo-root env remains highest priority.
    web_env = repo_root / "website-backend" / ".env"
    if web_env.exists():
        load_dotenv(dotenv_path=web_env, override=False)

    import bot

    print("🚀 Starting CryptoMentor AI Bot...")

    # Cek curl_cffi availability
    try:
        from curl_cffi import requests as _cffi
        print(f"✅ curl_cffi available — Cloudflare bypass aktif")
    except ImportError:
        print("⚠️ curl_cffi NOT available — akan fallback ke requests biasa (kemungkinan 403)")

    # Create bot instance
    telegram_bot = bot.TelegramBot()

    # Run bot
    asyncio.run(telegram_bot.run_bot())
