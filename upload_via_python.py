#!/usr/bin/env python3
"""
Upload verification file ke VPS menggunakan Python
"""

import paramiko
import sys
import os

def upload_file():
    """Upload file via SFTP"""
    
    # Configuration
    hostname = "147.93.156.165"
    port = 22
    username = "root"
    remote_path = "/var/www/cryptomentor/google25bce93832cdac80.html"
    local_file = "google25bce93832cdac80.html"
    
    print("=" * 50)
    print("📤 Uploading verification file to VPS")
    print("=" * 50)
    print()
    
    # Check if local file exists
    if not os.path.exists(local_file):
        print(f"❌ Local file not found: {local_file}")
        return False
    
    print(f"📁 Local file: {local_file}")
    print(f"🌐 VPS: {hostname}")
    print(f"📍 Remote path: {remote_path}")
    print()
    
    try:
        # Create SSH client
        print("🔌 Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try to connect (will prompt for password if needed)
        ssh.connect(
            hostname=hostname,
            port=port,
            username=username,
            timeout=30,
            look_for_keys=True,
            allow_agent=True
        )
        
        print("✅ Connected!")
        print()
        
        # Upload file via SFTP
        print("📤 Uploading file...")
        sftp = ssh.open_sftp()
        sftp.put(local_file, remote_path)
        sftp.close()
        
        print("✅ File uploaded!")
        print()
        
        # Set permissions
        print("🔧 Setting permissions...")
        stdin, stdout, stderr = ssh.exec_command(
            f"chmod 644 {remote_path} && chown www-data:www-data {remote_path}"
        )
        stdout.channel.recv_exit_status()  # Wait for command to complete
        
        print("✅ Permissions set!")
        print()
        
        # Verify file exists
        print("🔍 Verifying file...")
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_path}")
        content = stdout.read().decode('utf-8')
        
        if "google-site-verification" in content:
            print("✅ File verified on server!")
            print(f"   Content: {content}")
        else:
            print("⚠️  File uploaded but content might be incorrect")
        
        ssh.close()
        
        print()
        print("=" * 50)
        print("✅ SUCCESS!")
        print("=" * 50)
        print()
        print("🔗 Test URL: https://cryptomentor.id/google25bce93832cdac80.html")
        print()
        print("📝 Next steps:")
        print("   1. Open the URL above in browser")
        print("   2. Go back to Google Search Console")
        print("   3. Click 'VERIFIKASI' button")
        print()
        
        return True
        
    except paramiko.AuthenticationException:
        print("❌ Authentication failed!")
        print("   Please check your SSH credentials")
        return False
        
    except paramiko.SSHException as e:
        print(f"❌ SSH error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = upload_file()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
