#!/usr/bin/env python3
"""
Deploy full CryptoMentor system to VPS
Includes:
- Frontend (React/Vite)
- Backend (FastAPI)
- Bot services
- License server

Requirement: pip install paramiko
"""
import os
import sys
import subprocess
from pathlib import Path
import paramiko
from datetime import datetime

# ===== KONFIGURASI =====
VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PORT = 22
VPS_BASE_DIR = "/root/cryptomentor-bot"

COMPONENTS = {
    "frontend": {
        "local_dir": "website-frontend/dist",
        "remote_dir": f"{VPS_BASE_DIR}/website-frontend/dist",
        "build_cmd": ["npm", "run", "build"],
        "build_dir": "website-frontend",
        "required": True,
        "reload_service": True,
    },
    "backend": {
        "local_dir": "website-backend",
        "remote_dir": f"{VPS_BASE_DIR}/website-backend",
        "sync_only": True,
        "required": False,
        "reload_service": "cryptomentor-web",
    },
    "bot": {
        "local_dir": "Bismillah",
        "remote_dir": f"{VPS_BASE_DIR}/Bismillah",
        "sync_only": True,
        "required": False,
        "reload_service": None,
    },
}

class DeploymentManager:
    def __init__(self, password=None, key_path=None):
        self.password = password
        self.key_path = key_path
        self.ssh = None
        self.sftp = None
        self.deployment_log = []
        
    def connect(self):
        """Connect ke VPS via SSH"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path and os.path.exists(self.key_path):
                print(f"  🔑 Using SSH key: {self.key_path}")
                self.ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER,
                               key_filename=self.key_path, timeout=10)
            elif self.password:
                print(f"  🔐 Using password auth")
                self.ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER,
                               password=self.password, timeout=10)
            else:
                print("  ✗ No SSH key or password")
                return False
            
            self.sftp = self.ssh.open_sftp()
            print(f"✓ Connected to {VPS_HOST}@{VPS_USER}")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect dari VPS"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
    
    def build_component(self, component_name):
        """Build component jika perlu"""
        component = COMPONENTS[component_name]
        
        if "build_cmd" not in component:
            return True
        
        print(f"\n📦 Building {component_name}...")
        
        try:
            build_dir = component.get("build_dir", ".")
            result = subprocess.run(component["build_cmd"], cwd=build_dir, check=True)
            print(f"✓ {component_name} built successfully")
            return True
        except Exception as e:
            print(f"✗ Build failed: {e}")
            return False
    
    def deploy_component(self, component_name):
        """Deploy component ke VPS"""
        component = COMPONENTS[component_name]
        local_dir = component["local_dir"]
        remote_dir = component["remote_dir"]
        
        print(f"\n📁 Deploying {component_name}...")
        print(f"  Local: {local_dir}")
        print(f"  Remote: {remote_dir}")
        
        if not os.path.exists(local_dir):
            print(f"✗ Local directory not found: {local_dir}")
            return False
        
        try:
            # Create remote directory
            try:
                self.sftp.stat(remote_dir)
            except IOError:
                self.ssh.exec_command(f"mkdir -p {remote_dir}")
            
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
                        self.sftp.stat(remote_subdir)
                    except IOError:
                        self.ssh.exec_command(f"mkdir -p {remote_subdir}")
                    
                    # Upload file
                    try:
                        self.sftp.put(local_path, remote_path)
                        file_count += 1
                    except Exception as e:
                        print(f"  ⚠ Skipped {file}: {e}")
            
            print(f"✓ Deployed {file_count} files ({component_name})")
            return True
            
        except Exception as e:
            print(f"✗ Deploy failed: {e}")
            return False
    
    def restart_service(self, service_name):
        """Restart systemd service di VPS"""
        if not service_name:
            return True
        
        print(f"\n🔄 Restarting service: {service_name}...")
        
        try:
            stdin, stdout, stderr = self.ssh.exec_command(
                f"sudo systemctl restart {service_name}"
            )
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                print(f"✓ Service {service_name} restarted")
                return True
            else:
                error = stderr.read().decode()
                print(f"⚠ Restart failed: {error}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def reload_nginx(self):
        """Reload nginx"""
        print(f"\n🌐 Reloading nginx...")
        
        try:
            stdin, stdout, stderr = self.ssh.exec_command("sudo systemctl reload nginx")
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                print(f"✓ Nginx reloaded")
                return True
            else:
                error = stderr.read().decode()
                print(f"⚠ Nginx reload: {error}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def verify_deployment(self):
        """Verify deployment"""
        print(f"\n✅ Verifying deployment...")
        
        for component_name, component in COMPONENTS.items():
            remote_dir = component["remote_dir"]
            
            try:
                stdin, stdout, stderr = self.ssh.exec_command(f"ls -la {remote_dir}/ | head -5")
                result = stdout.read().decode()
                
                if result:
                    print(f"✓ {component_name}: {remote_dir} ✓")
                else:
                    print(f"⚠ {component_name}: directory empty")
            except:
                print(f"⚠ {component_name}: cannot verify")
    
    def create_deployment_report(self):
        """Create deployment report"""
        report = f"""
=== DEPLOYMENT REPORT ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
VPS: {VPS_HOST}@{VPS_USER}
Base Dir: {VPS_BASE_DIR}

Components Deployed:
"""
        for component_name in COMPONENTS.keys():
            component = COMPONENTS[component_name]
            report += f"\n- {component_name}: {component['remote_dir']}"
        
        report += f"""

Next Steps:
1. Verify website: https://cryptomentor.id
2. Check API: https://cryptomentor.id/api/health
3. Review logs if needed
4. Notify users of update

=== END REPORT ===
"""
        
        # Save report
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_file}")

def main():
    print("=" * 60)
    print("🚀 CRYPTOMENTOR FULL SYSTEM DEPLOYMENT")
    print("=" * 60)
    print()
    
    # Check working directory
    if not os.path.exists("website-frontend"):
        print("✗ Not in project root directory!")
        sys.exit(1)
    
    # Check paramiko
    try:
        import paramiko
    except ImportError:
        print("✗ Paramiko not installed!")
        print("  Install: pip install paramiko")
        sys.exit(1)
    
    # Get components to deploy
    print("📋 Select components to deploy:")
    print("  1. Frontend only")
    print("  2. Frontend + Backend")
    print("  3. All (Frontend + Backend + Bot)")
    print("  4. Custom")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        components_to_deploy = ["frontend"]
    elif choice == "2":
        components_to_deploy = ["frontend", "backend"]
    elif choice == "3":
        components_to_deploy = ["frontend", "backend", "bot"]
    else:
        components_to_deploy = []
        for name in COMPONENTS.keys():
            resp = input(f"Deploy {name}? (y/n): ").lower()
            if resp == 'y':
                components_to_deploy.append(name)
    
    if not components_to_deploy:
        print("✗ No components selected")
        sys.exit(1)
    
    print(f"\n✅ Selected: {', '.join(components_to_deploy)}")
    
    # Build components
    print("\n" + "=" * 60)
    print("🔨 BUILDING COMPONENTS")
    print("=" * 60)
    
    for component_name in components_to_deploy:
        component = COMPONENTS[component_name]
        if "build_cmd" in component:
            if not DeploymentManager().build_component(component_name):
                print(f"\n✗ Build failed for {component_name}")
                sys.exit(1)
    
    # Get authentication
    print("\n" + "=" * 60)
    print("🔐 VPS AUTHENTICATION")
    print("=" * 60)
    
    key_path = os.path.expanduser("~/.ssh/id_rsa")
    password = os.getenv("VPS_PASSWORD")
    
    if os.path.exists(key_path):
        print(f"\n🔑 SSH key found: {key_path}")
        use_key = input("Use SSH key? (y/n): ").lower()
        if use_key != 'y':
            password = input("Enter VPS password: ")
    else:
        password = input("\nEnter VPS password: ")
    
    # Deploy
    print("\n" + "=" * 60)
    print("📤 DEPLOYING TO VPS")
    print("=" * 60)
    
    deployer = DeploymentManager(password=password, key_path=key_path if os.path.exists(key_path) else None)
    
    if not deployer.connect():
        sys.exit(1)
    
    try:
        for component_name in components_to_deploy:
            if not deployer.deploy_component(component_name):
                print(f"\n✗ Deploy failed for {component_name}")
                sys.exit(1)
        
        # Reload nginx
        deployer.reload_nginx()
        
        # Verify
        deployer.verify_deployment()
        
        # Report
        deployer.create_deployment_report()
        
        print("\n" + "=" * 60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("=" * 60)
        print("\n🌐 Check: https://cryptomentor.id")
        print()
        
    finally:
        deployer.disconnect()

if __name__ == "__main__":
    main()
