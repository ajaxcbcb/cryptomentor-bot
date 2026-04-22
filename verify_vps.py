#!/usr/bin/env python3
"""Quick verification of VPS files"""
from vps_ssh_utils import connect_ssh, load_vps_config

VPS_HOST, VPS_USER, VPS_PORT = load_vps_config()
VPS_DEST = "/root/cryptomentor-bot/website-frontend/dist"

ssh = connect_ssh(host=VPS_HOST, user=VPS_USER, port=VPS_PORT)

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
