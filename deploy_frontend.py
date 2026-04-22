#!/usr/bin/env python3
"""
Deploy frontend CryptoMentor ke VPS
Fitur:
- Build frontend otomatis
- Deploy semua file dari dist/
- Reload nginx service
- Verify deployment

Requirement: pip install paramiko
"""
import os
import sys
import subprocess
from pathlib import Path
import paramiko
from glob import glob

# ===== KONFIGURASI =====
VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PORT = 22
VPS_DEST_DIR = "/root/cryptomentor-bot/website-frontend/dist"  # Sesuai nginx config
FRONTEND_DIR = "website-frontend"
DIST_DIR = f"{FRONTEND_DIR}/dist"

# Build config
BUILD_COMMAND = ["npm", "run", "build"]
USE_NPM = True  # atau gunakan yarn

def build_frontend():
    """Build frontend menggunakan npm/yarn"""
    print("\n📦 Building frontend...")
    print(f"  Command: {' '.join(BUILD_COMMAND)}")
    
    try:
        result = subprocess.run(BUILD_COMMAND, cwd=FRONTEND_DIR, check=True)
        print("✓ Build berhasil!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build gagal: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ {BUILD_COMMAND[0]} tidak ditemukan. Install npm terlebih dahulu!")
        return False

def get_dist_files():
    """Gather semua file dari dist/ untuk di-deploy"""
    files_to_deploy = []
    
    if not os.path.exists(DIST_DIR):
        print(f"✗ Directory {DIST_DIR} tidak ditemukan!")
        return None
    
    # Walk through dist directory
    for root, dirs, files in os.walk(DIST_DIR):
        for file in files:
            local_path = os.path.join(root, file)
            # Relative path from dist
            rel_path = os.path.relpath(local_path, DIST_DIR)
            remote_path = f"{VPS_DEST_DIR}/{rel_path}".replace("\\", "/")
            files_to_deploy.append((local_path, remote_path))
    
    return files_to_deploy

def deploy_with_ssh(password=None, key_path=None):
    """Deploy menggunakan SSH dengan SFTP"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect dengan key atau password
        if key_path and os.path.exists(key_path):
            print(f"  Connecting dengan SSH key: {key_path}")
            ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, 
                       key_filename=key_path, timeout=10)
        elif password:
            print(f"  Connecting dengan password...")
            ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, 
                       password=password, timeout=10)
        else:
            print("✗ Tidak ada SSH key atau password")
            return False
        
        sftp = ssh.open_sftp()
        print(f"✓ Terhubung ke {VPS_HOST}@{VPS_USER}")
        
        # Get files to deploy
        files_to_deploy = get_dist_files()
        if not files_to_deploy:
            return False
        
        print(f"\n📁 Deploy {len(files_to_deploy)} files...")
        
        # Deploy files
        for local_file, remote_file in files_to_deploy:
            remote_dir = os.path.dirname(remote_file)
            
            # Create remote directory
            try:
                sftp.stat(remote_dir)
            except IOError:
                try:
                    ssh.exec_command(f"mkdir -p {remote_dir}")
                except:
                    pass
            
            # Upload file
            try:
                sftp.put(local_file, remote_file)
                file_size = os.path.getsize(local_file)
                print(f"  ✓ {os.path.basename(local_file)} ({file_size} bytes)")
            except Exception as e:
                print(f"  ✗ {os.path.basename(local_file)}: {e}")
        
        # Reload nginx
        print(f"\n🔄 Reloading nginx...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx")
        exit_code = stdout.channel.recv_exit_status()
        if exit_code == 0:
            print("✓ Nginx reloaded!")
        else:
            error = stderr.read().decode()
            print(f"⚠ Nginx reload: {error}")
        
        # Verify deployment
        print(f"\n✅ Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {VPS_DEST_DIR}/")
        result = stdout.read().decode()
        if "index.html" in result:
            print("✓ index.html found on server!")
        else:
            print("⚠ index.html tidak ditemukan!")
        
        sftp.close()
        ssh.close()
        print("\n✓ Deploy selesai!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DEPLOY FRONTEND CRYPTOMENTOR")
    print("=" * 60)
    
    # Check working directory
    if not os.path.exists(FRONTEND_DIR):
        print(f"\n✗ Folder {FRONTEND_DIR} tidak ditemukan!")
        print("✗ Pastikan menjalankan script dari root direktori project")
        sys.exit(1)
    
    # Check paramiko
    try:
        import paramiko
    except ImportError:
        print("\n✗ Paramiko belum diinstall!")
        print("  Install: pip install paramiko")
        sys.exit(1)
    
    # Step 1: Build frontend (skip if npm not found but dist exists)
    dist_exists = os.path.exists(DIST_DIR)
    
    if not dist_exists or input(f"\nDist folder exists. Rebuild? (y/n): ").lower() == 'y':
        if not build_frontend():
            if not dist_exists:
                print("\n✗ Build frontend gagal dan dist/ tidak ada, batalkan deploy")
                sys.exit(1)
            else:
                print("\n⚠ Build gagal tapi dist/ sudah ada, lanjut deploy...")
    
    if not dist_exists:
        print("\n✗ Dist folder tidak ditemukan setelah build!")
        sys.exit(1)
    
    # Step 2: Check dist files
    files = get_dist_files()
    if not files:
        print("\n✗ Tidak ada file di dist/")
        sys.exit(1)
    
    print(f"\n📊 Siap deploy {len(files)} files")
    
    # Step 3: Get authentication method
    print("\n🔐 Pilih metode autentikasi:")
    
    key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(key_path):
        print(f"  1. SSH Key ({key_path})")
        auth_method = input("  Gunakan SSH key? (y/n): ").lower()
        if auth_method == 'y':
            deploy_with_ssh(key_path=key_path)
            sys.exit(0)
    
    # Fallback ke password
    password = os.getenv("VPS_PASSWORD")
    if not password:
        password = input("\n  Masukkan VPS password: ")
    
    # Step 4: Deploy
    if deploy_with_ssh(password=password):
        print("\n✅ DEPLOY BERHASIL!")
        print(f"   Frontend deployed ke: {VPS_DEST_DIR}")
    else:
        print("\n❌ DEPLOY GAGAL!")
        sys.exit(1)
