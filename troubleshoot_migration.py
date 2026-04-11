#!/usr/bin/env python3
"""Troubleshoot why migration changes not visible"""
import paramiko
import requests
import json

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)

print()
print("=" * 80)
print("🔍 TROUBLESHOOTING: Why Migration Changes Not Visible")
print("=" * 80)
print()

# 1. Check if bot is running with new code
print("1️⃣  CHECKING BOT SERVICE")
print("-" * 50)

stdin, stdout, stderr = ssh.exec_command("ps aux | grep python | grep bot.py")
bot_processes = stdout.read().decode()

if "bot.py" in bot_processes:
    print("✅ Bot process found:")
    for line in bot_processes.split('\n'):
        if 'bot.py' in line:
            print(f"   {line.strip()}")
else:
    print("❌ Bot process NOT found!")
    print("   Bot mungkin tidak running atau crash")

print()

# 2. Check bot service status
print("2️⃣  CHECKING BOT SERVICE STATUS")
print("-" * 50)

stdin, stdout, stderr = ssh.exec_command("sudo systemctl status cryptomentor-bot 2>&1 | head -10")
bot_status = stdout.read().decode()

if "Active: active" in bot_status:
    print("✅ Bot service is ACTIVE")
else:
    print("❌ Bot service is NOT ACTIVE")
    print("   Status:", bot_status.strip())

print()

# 3. Check if bot code is updated
print("3️⃣  CHECKING BOT CODE VERSION")
print("-" * 50)

stdin, stdout, stderr = ssh.exec_command("grep -n 'WEB_DASHBOARD_URL' /root/cryptomentor-bot/Bismillah/app/handlers_autotrade.py")
web_url_check = stdout.read().decode()

if web_url_check:
    print("✅ Bot code has WEB_DASHBOARD_URL (migration code)")
    print("   Line:", web_url_check.strip())
else:
    print("❌ Bot code missing WEB_DASHBOARD_URL")
    print("   Bot masih menggunakan code lama!")

print()

# 4. Check frontend cache
print("4️⃣  CHECKING FRONTEND CACHE")
print("-" * 50)

# Check if GatekeeperScreen exists in deployed code
stdin, stdout, stderr = ssh.exec_command("grep -q 'GatekeeperScreen' /root/cryptomentor-bot/website-frontend/dist/assets/*.js")
gatekeeper_check = stdout.channel.recv_exit_status()

if gatekeeper_check == 0:
    print("✅ GatekeeperScreen found in deployed JS")
else:
    print("❌ GatekeeperScreen NOT found in deployed JS")
    print("   Frontend belum di-build dengan migration code!")

print()

# 5. Check backend middleware
print("5️⃣  CHECKING BACKEND MIDDLEWARE")
print("-" * 50)

stdin, stdout, stderr = ssh.exec_command("grep -q 'verification_guard' /root/cryptomentor-bot/website-backend/main.py")
middleware_check = stdout.channel.recv_exit_status()

if middleware_check == 0:
    print("✅ Verification guard middleware registered in main.py")
else:
    print("❌ Verification guard middleware NOT registered!")
    print("   Backend belum di-update dengan migration code!")

print()

# 6. Check nginx cache
print("6️⃣  CHECKING NGINX CACHE")
print("-" * 50)

stdin, stdout, stderr = ssh.exec_command("sudo nginx -T 2>&1 | grep -A5 -B5 'Cache-Control'")
nginx_cache = stdout.read().decode()

if 'no-cache' in nginx_cache:
    print("✅ Nginx has no-cache headers for index.html")
else:
    print("⚠️  Nginx cache headers might be caching old content")

print()

# 7. Test API endpoints
print("7️⃣  TESTING API ENDPOINTS")
print("-" * 50)

try:
    # Test health endpoint
    response = requests.get("https://api.cryptomentor.id/", timeout=5)
    print(f"✅ API health: {response.status_code}")

    # Test verification endpoint (should return 401 without auth)
    response = requests.get("https://api.cryptomentor.id/user/verification-status", timeout=5)
    if response.status_code == 401:
        print("✅ Verification endpoint: 401 (requires auth)")
    elif response.status_code == 404:
        print("❌ Verification endpoint: 404 (not found)")
    else:
        print(f"⚠️  Verification endpoint: {response.status_code}")

except Exception as e:
    print(f"❌ API test failed: {e}")

print()

# 8. Check database schema
print("8️⃣  CHECKING DATABASE SCHEMA")
print("-" * 50)

# Check if autotrade_sessions table exists (we can't directly query Supabase from here)
print("⚠️  Cannot check Supabase schema directly")
print("   Pastikan autotrade_sessions table sudah ada dengan kolom:")
print("   - telegram_id, exchange, uid, status, community_code, leverage, margin_mode")

print()

# 9. Recommendations
print("9️⃣  RECOMMENDATIONS")
print("-" * 50)

issues_found = []

# Check if bot needs restart
if "Active: active" not in bot_status:
    issues_found.append("Bot service tidak aktif - perlu start")

if not web_url_check:
    issues_found.append("Bot code belum di-update - perlu restart bot")

if gatekeeper_check != 0:
    issues_found.append("Frontend belum di-build dengan migration code")

if middleware_check != 0:
    issues_found.append("Backend middleware belum terdaftar")

if not issues_found:
    print("✅ No obvious issues found")
    print("   Mungkin masalah cache browser atau database schema")
    print()
    print("   SOLUSI:")
    print("   1. Hard refresh browser: Ctrl+Shift+R")
    print("   2. Clear browser cache")
    print("   3. Check Supabase autotrade_sessions table")
    print("   4. Test dengan user baru (incognito mode)")
else:
    print("❌ Issues found:")
    for i, issue in enumerate(issues_found, 1):
        print(f"   {i}. {issue}")

print()

print("=" * 80)
print("🔧 QUICK FIXES")
print("=" * 80)
print()

if "Active: active" not in bot_status:
    print("🔄 Start bot service:")
    print("   ssh root@147.93.156.165")
    print("   sudo systemctl start cryptomentor-bot")
    print()

if not web_url_check:
    print("🔄 Restart bot service:")
    print("   ssh root@147.93.156.165")
    print("   sudo systemctl restart cryptomentor-bot")
    print()

if gatekeeper_check != 0:
    print("🔄 Rebuild frontend:")
    print("   cd website-frontend")
    print("   npm run build")
    print("   python deploy_now.py")
    print()

if middleware_check != 0:
    print("🔄 Check backend deployment:")
    print("   python deploy_now_auto.py")
    print()

print("🧹 Clear browser cache:")
print("   Chrome: Ctrl+Shift+Del → Clear browsing data")
print("   Firefox: Ctrl+Shift+Del → Clear recent history")
print("   Or use incognito/private mode")
print()

ssh.close()
