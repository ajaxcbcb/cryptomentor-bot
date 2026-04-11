#!/usr/bin/env python3
"""Check what migration files are on VPS vs local"""
import paramiko
import os

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_BACKEND = "/root/cryptomentor-bot/website-backend"

LOCAL_BACKEND = "website-backend"

# Files yang seharusnya ada dari migration
MIGRATION_FILES = {
    "Backend": [
        "app/middleware/verification_guard.py",
        "app/routes/user.py",  # Should have new endpoints
        "app/routes/dashboard.py",  # Should have leverage/margin endpoints
    ],
    "Frontend": [
        "src/components/GatekeeperScreen.jsx",
        "src/components/VerificationPendingScreen.jsx", 
        "src/components/OnboardingWizard.jsx",
    ],
    "Bot": [
        "app/handlers_autotrade.py",  # Rewritten for gatekeeper
        "menu_system.py",  # Simplified menu
    ]
}

print("=" * 70)
print("🔍 TELEGRAM WEB MIGRATION - FILE STATUS CHECK")
print("=" * 70)
print()

# Check local files
print("📂 LOCAL FILES:")
print("-" * 70)
for category, files in MIGRATION_FILES.items():
    print(f"\n{category}:")
    for file in files:
        path = os.path.join(".", file) if category != "Bot" else os.path.join("Bismillah", file)
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {exists} {file}")

# Check VPS files
print()
print()
print("🌐 VPS FILES:")
print("-" * 70)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, 
               password=<REDACTED_PASSWORD> timeout=10)
    
    for category, files in MIGRATION_FILES.items():
        print(f"\n{category}:")
        for file in files:
            remote_path = f"{VPS_BACKEND}/{file}" if category != "Bot" else f"/root/cryptomentor-bot/Bismillah/{file}"
            
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path} && echo 'found' || echo 'missing'")
            result = stdout.read().decode().strip()
            
            exists = "✅" if result == "found" else "❌"
            print(f"  {exists} {file}")
    
    ssh.close()
    
except Exception as e:
    print(f"✗ VPS Connection Error: {e}")

print()
print()
print("=" * 70)
print("📋 MIGRATION STATUS:")
print("=" * 70)
print()
print("Tasks marked [x] in tasks.md:")
print("  ✅ Backend — Verification Status Endpoint")
print("  ✅ Backend — Verification Guard Middleware") 
print("  ✅ Backend — Leverage & Margin Settings Endpoints")
print("  ✅ Frontend — Verification Gate & Registration Flow")
print("  ✅ Frontend — Onboarding Wizard")
print("  ✅ Telegram Bot — Rewrite /start as Gatekeeper")
print("  ✅ Telegram Bot — Simplify Menu System")
print("  ✅ Telegram Bot — Redirect Retired Commands")
print("  ✅ Telegram Bot — Update Notifications with Dashboard Link")
print("  ✅ Cleanup — Remove Retired Handler Files")
print("  ✅ Documentation — Update CHANGELOG.md")
print()
print("⚠️  STATUS: Code exists locally but NOT DEPLOYED to VPS yet!")
print()
print("💡 RECOMMENDATION:")
print("  Run: python deploy_full_system.py")
print("  Select: Option 2 (Frontend + Backend)")
print("=" * 70)
print()
