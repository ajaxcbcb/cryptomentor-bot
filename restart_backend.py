#!/usr/bin/env python3
"""Restart backend service on VPS"""
from vps_ssh_utils import connect_ssh, load_vps_config

VPS_HOST, VPS_USER, VPS_PORT = load_vps_config()

ssh = connect_ssh(host=VPS_HOST, user=VPS_USER, port=VPS_PORT)

print("🔄 Restarting FastAPI backend service...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptomentor-web")
exit_code = stdout.channel.recv_exit_status()

if exit_code == 0:
    print("✅ Backend service restarted successfully!")
else:
    error = stderr.read().decode()
    print(f"⚠️  Error: {error}")
    
    # Try alternative
    print()
    print("Trying alternative method (if service file not found)...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
    procs = stdout.read().decode()
    print(f"Current processes: {procs if procs else '(none)'}")

print()
print("Checking service status...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl status cryptomentor-web 2>&1 | head -5")
status = stdout.read().decode()
print(status)

ssh.close()
