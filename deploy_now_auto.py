#!/usr/bin/env python3
"""
Auto deploy Frontend + Backend (with migration code) to VPS
No interactive prompts
"""
import os
import sys
import subprocess
import paramiko
from datetime import datetime

# ===== KONFIGURASI =====
VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PORT = 22
VPS_BASE_DIR = "/root/cryptomentor-bot"

def deploy_to_vps():
    """Deploy Frontend + Backend to VPS"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print()
        print("🔐 Connecting to VPS...")
        ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, 
                   password=<REDACTED_PASSWORD> timeout=10)
        
        sftp = ssh.open_sftp()
        print("✅ Connected!")
        print()
        
        components = {
            "frontend": {
                "local": "website-frontend/dist",
                "remote": f"{VPS_BASE_DIR}/website-frontend/dist",
                "reload": "nginx",
            },
            "backend": {
                "local": "website-backend",
                "remote": f"{VPS_BASE_DIR}/website-backend",
                "reload": "cryptomentor-web",
            },
        }
        
        for comp_name, comp_config in components.items():
            print(f"📤 Deploying {comp_name}...")
            print(f"  Local: {comp_config['local']}")
            print(f"  Remote: {comp_config['remote']}")
            print()
            
            local_dir = comp_config['local']
            remote_dir = comp_config['remote']
            
            if not os.path.exists(local_dir):
                print(f"  ⚠️  {local_dir} not found, skipping")
                continue
            
            # Create remote directory
            try:
                ssh.exec_command(f"mkdir -p {remote_dir}")
            except:
                pass
            
            # Deploy files
            file_count = 0
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    rel_path = os.path.relpath(local_path, local_dir)
                    remote_path = f"{remote_dir}/{rel_path}".replace("\\", "/")
                    
                    # Create remote subdirectory
                    remote_subdir = os.path.dirname(remote_path)
                    try:
                        sftp.stat(remote_subdir)
                    except IOError:
                        ssh.exec_command(f"mkdir -p {remote_subdir}")
                    
                    # Upload
                    try:
                        sftp.put(local_path, remote_path)
                        file_count += 1
                    except Exception as e:
                        print(f"    ⚠️  {file}: {e}")
            
            print(f"  ✅ Uploaded {file_count} files")
            print()
            
            # Reload service
            if comp_config.get('reload'):
                service = comp_config['reload']
                print(f"  🔄 Restarting {service}...")
                stdin, stdout, stderr = ssh.exec_command(f"sudo systemctl reload {service}")
                exit_code = stdout.channel.recv_exit_status()
                if exit_code == 0:
                    print(f"  ✅ {service} reloaded!")
                else:
                    error = stderr.read().decode()
                    print(f"  ⚠️  {service}: {error}")
            print()
        
        # Final verification
        print("=" * 60)
        print("✅ VERIFYING MIGRATION DEPLOYMENT...")
        print("=" * 60)
        print()
        
        # Check middleware
        stdin, stdout, stderr = ssh.exec_command(
            f"test -f {VPS_BASE_DIR}/website-backend/app/middleware/verification_guard.py && echo 'OK' || echo 'MISSING'"
        )
        middleware_check = stdout.read().decode().strip()
        print(f"Middleware (verification_guard.py): {middleware_check}")
        
        # Check backend routes
        stdin, stdout, stderr = ssh.exec_command(
            f"grep -q 'submit-uid' {VPS_BASE_DIR}/website-backend/app/routes/user.py && echo 'OK' || echo 'MISSING'"
        )
        routes_check = stdout.read().decode().strip()
        print(f"Routes (user endpoints): {routes_check}")
        
        # Check frontend
        stdin, stdout, stderr = ssh.exec_command(
            f"test -f {VPS_BASE_DIR}/website-frontend/dist/index.html && echo 'OK' || echo 'MISSING'"
        )
        frontend_check = stdout.read().decode().strip()
        print(f"Frontend (index.html): {frontend_check}")
        
        sftp.close()
        ssh.close()
        
        print()
        print("=" * 60)
        print("✨ DEPLOYMENT COMPLETE!")
        print("=" * 60)
        print()
        print("🌐 URLs:")
        print("  Frontend: https://cryptomentor.id")
        print("  API: https://cryptomentor.id/api")
        print()
        print("✅ Migration updates deployed to VPS!")
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
    print("🚀 AUTO-DEPLOY FRONTEND + BACKEND (Migration Updates)")
    print("=" * 60)
    print()
    
    # Check requirements
    try:
        import paramiko
    except ImportError:
        print("❌ Paramiko not installed!")
        sys.exit(1)
    
    if deploy_to_vps():
        sys.exit(0)
    else:
        sys.exit(1)
