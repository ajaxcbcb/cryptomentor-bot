#!/usr/bin/env python3
"""Restart backend service on VPS"""
import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "rMM2m63P"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASSWORD, timeout=10)

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
