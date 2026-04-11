#!/usr/bin/env python3
"""Quick verification of VPS files"""
import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_DEST = "/root/cryptomentor-bot/website-frontend/dist"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)

print("=" * 70)
print("📊 VPS FILE VERIFICATION")
print("=" * 70)
print()

# List all files
stdin, stdout, stderr = ssh.exec_command(f"find {VPS_DEST} -type f -exec ls -lh {{}} \\;")
result = stdout.read().decode()

print(f"Directory: {VPS_DEST}")
print()
print("Files on VPS:")
print("-" * 70)
print(result if result else "  (none found)")
print()

# Count files
stdin, stdout, stderr = ssh.exec_command(f"find {VPS_DEST} -type f | wc -l")
count = stdout.read().decode().strip()

print(f"Total files: {count}")
print()

# Check sizes
stdin, stdout, stderr = ssh.exec_command(f"du -sh {VPS_DEST}")
size = stdout.read().decode().strip()
print(f"Total size: {size}")
print()

# Check index.html specifically
stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_DEST}/index.html && echo 'OK' || echo 'NOT FOUND'")
check = stdout.read().decode().strip()
print(f"index.html exists: {check}")

ssh.close()

print()
print("=" * 70)
