#!/usr/bin/env python3
"""
Deploy frontend CryptoMentor ke VPS - SIMPLIFIED VERSION
Auto skip prompt, gunakan password langsung
"""
import os
import sys
import subprocess
from pathlib import Path

from vps_ssh_utils import connect_ssh, load_vps_config

# ===== KONFIGURASI =====
VPS_HOST, VPS_USER, VPS_PORT = load_vps_config()
VPS_DEST_DIR = "/root/cryptomentor-bot/website-frontend/dist"

FRONTEND_DIR = "website-frontend"
DIST_DIR = f"{FRONTEND_DIR}/dist"

def deploy_files():
    """Deploy files ke VPS"""
    try:
        print(f"🔐 Connecting to {VPS_HOST}...")
        ssh = connect_ssh(host=VPS_HOST, user=VPS_USER, port=VPS_PORT)
        
        sftp = ssh.open_sftp()
        print(f"✅ Connected!")
        print()
        
        # Get all files from dist
        print(f"📁 Scanning {DIST_DIR}...")
        files_to_deploy = []
        
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, DIST_DIR)
                remote_path = f"{VPS_DEST_DIR}/{rel_path}".replace("\\", "/")
                files_to_deploy.append((local_path, remote_path))
        
        print(f"✓ Found {len(files_to_deploy)} files")
        print()
        
        # Create remote directory
        print(f"📂 Creating {VPS_DEST_DIR}...")
        try:
            ssh.exec_command(f"mkdir -p {VPS_DEST_DIR}")
            print("✓ Directory ready")
        except:
            pass
        
        print()
        print("📤 Uploading files...")
        print("-" * 60)
        
        # Deploy each file
        for i, (local_path, remote_path) in enumerate(files_to_deploy, 1):
            remote_dir = os.path.dirname(remote_path)
            filename = os.path.basename(local_path)
            size = os.path.getsize(local_path)
            
            # Create remote subdirectory
            try:
                sftp.stat(remote_dir)
            except IOError:
                ssh.exec_command(f"mkdir -p {remote_dir}")
            
            # Upload
            sftp.put(local_path, remote_path)
            print(f"  {i}. ✅ {filename:40s} ({size:>10,} bytes)")
        
        print("-" * 60)
        print()
        
        # Reload nginx
        print("🔄 Reloading nginx...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx")
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("✅ Nginx reloaded!")
        else:
            error = stderr.read().decode()
            print(f"⚠️  Warning: {error}")
        
        print()
        
        # Verify
        print("✅ Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {VPS_DEST_DIR}/ | grep -E '(index|assets)'")
        result = stdout.read().decode()
        if result:
            print(result)
        
        sftp.close()
        ssh.close()
        
        print()
        print("=" * 60)
        print("✨ DEPLOYMENT BERHASIL!")
        print("=" * 60)
        print("  Website: https://cryptomentor.id")
        print("  API: https://cryptomentor.id/api")
        print()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("🚀 DEPLOY FRONTEND - CRYPTOMENTOR")
    print("=" * 60)
    print()
    
    # Check dist
    if not os.path.exists(DIST_DIR):
        print(f"❌ {DIST_DIR} tidak ditemukan!")
        sys.exit(1)
    
    # Check paramiko
    try:
        import paramiko
    except ImportError:
        print("❌ Paramiko not installed!")
        print("   pip install paramiko")
        sys.exit(1)
    
    # Deploy
    if deploy_files():
        sys.exit(0)
    else:
        sys.exit(1)
