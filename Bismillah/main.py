#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Entry Point
Simple entry point for Railway deployment
"""

if __name__ == "__main__":
    import bot
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

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
