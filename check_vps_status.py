#!/usr/bin/env python3
"""
Check VPS status dan bandingkan dengan local files
Untuk lihat apa yang belum di-update
"""
import os
import hashlib
from datetime import datetime

from vps_ssh_utils import connect_ssh, load_vps_config

# VPS Config
VPS_HOST, VPS_USER, VPS_PORT = load_vps_config()

# Paths
FRONTEND_LOCAL = "website-frontend/dist"
FRONTEND_REMOTE = "/root/cryptomentor-bot/website-frontend/dist"

def get_local_files(directory):
    """Get all files locally dengan hash"""
    files = {}
    if not os.path.exists(directory):
        print(f"✗ Local directory tidak ditemukan: {directory}")
        return files
    
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, directory)
            
            # Get file hash
            try:
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                files[rel_path] = {
                    'hash': file_hash,
                    'size': size,
                    'mtime': mtime,
                    'path': filepath
                }
            except:
                pass
    
    return files

def check_vps():
    """Check VPS files"""
    try:
        ssh = connect_ssh(host=VPS_HOST, user=VPS_USER, port=VPS_PORT)
        
        sftp = ssh.open_sftp()
        
        print(f"✓ Connected to {VPS_HOST}@{VPS_USER}")
        print()
        
        # Check remote directory
        try:
            sftp.stat(FRONTEND_REMOTE)
            print(f"✓ Remote directory exists: {FRONTEND_REMOTE}")
        except IOError:
            print(f"✗ Remote directory NOT found: {FRONTEND_REMOTE}")
            return None
        
        # List files
        remote_files = {}
        
        def walk_sftp(path, prefix=""):
            try:
                for item in sftp.listdir_attr(path):
                    if item.filename.startswith('.'):
                        continue
                    
                    full_path = f"{path}/{item.filename}"
                    rel_path = f"{prefix}/{item.filename}".lstrip('/')
                    
                    if item.filename == '.' or item.filename == '..':
                        continue
                    
                    if os.path.isdir(item):  # Directory
                        walk_sftp(full_path, rel_path)
                    else:  # File
                        remote_files[rel_path] = {
                            'size': item.st_size,
                            'mtime': item.st_mtime,
                            'path': full_path
                        }
            except Exception as e:
                print(f"✗ Error walking {path}: {e}")
        
        walk_sftp(FRONTEND_REMOTE)
        sftp.close()
        ssh.close()
        
        return remote_files
        
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return None

def compare_files(local_files, remote_files):
    """Compare local vs remote files"""
    print()
    print("=" * 70)
    print("📊 FILE COMPARISON REPORT")
    print("=" * 70)
    print()
    
    status = {
        'missing_remote': [],
        'outdated': [],
        'same': [],
        'only_remote': [],
        'different_size': []
    }
    
    # Check local files
    for local_file, local_info in local_files.items():
        if local_file not in remote_files:
            status['missing_remote'].append(local_file)
        else:
            remote_info = remote_files[local_file]
            
            if local_info['size'] != remote_info['size']:
                status['different_size'].append({
                    'file': local_file,
                    'local': local_info['size'],
                    'remote': remote_info['size']
                })
            elif local_info['mtime'] > remote_info['mtime']:
                status['outdated'].append({
                    'file': local_file,
                    'local_mtime': datetime.fromtimestamp(local_info['mtime']),
                    'remote_mtime': datetime.fromtimestamp(remote_info['mtime'])
                })
            else:
                status['same'].append(local_file)
    
    # Check remote only files
    for remote_file in remote_files.keys():
        if remote_file not in local_files:
            status['only_remote'].append(remote_file)
    
    # Report: Missing on remote
    if status['missing_remote']:
        print("🔴 FILES MISSING ON REMOTE (Need to upload):")
        print("-" * 70)
        for i, file in enumerate(status['missing_remote'], 1):
            size = local_files[file]['size']
            print(f"  {i}. {file} ({size} bytes)")
        print()
    
    # Report: Different size
    if status['different_size']:
        print("🟠 FILES WITH DIFFERENT SIZE:")
        print("-" * 70)
        for i, item in enumerate(status['different_size'], 1):
            print(f"  {i}. {item['file']}")
            print(f"     Local:  {item['local']} bytes")
            print(f"     Remote: {item['remote']} bytes")
        print()
    
    # Report: Outdated
    if status['outdated']:
        print("🟡 FILES OUTDATED ON REMOTE (local is newer):")
        print("-" * 70)
        for i, item in enumerate(status['outdated'], 1):
            print(f"  {i}. {item['file']}")
            print(f"     Local:  {item['local_mtime']}")
            print(f"     Remote: {item['remote_mtime']}")
        print()
    
    # Report: Only on remote
    if status['only_remote']:
        print("🔵 FILES ONLY ON REMOTE (Old files):")
        print("-" * 70)
        for i, file in enumerate(status['only_remote'], 1):
            print(f"  {i}. {file} ({remote_files[file]['size']} bytes)")
        print()
    
    # Report: Up to date
    if status['same']:
        print(f"✅ UP-TO-DATE FILES: {len(status['same'])}")
    
    print()
    print("=" * 70)
    print("📈 SUMMARY:")
    print("=" * 70)
    print(f"  Total local files:           {len(local_files)}")
    print(f"  Total remote files:          {len(remote_files)}")
    print(f"  ✅ Up-to-date:               {len(status['same'])}")
    print(f"  🟡 Outdated (need update):   {len(status['outdated'])}")
    print(f"  🔴 Missing on remote:         {len(status['missing_remote'])}")
    print(f"  🟠 Different size:            {len(status['different_size'])}")
    print(f"  🔵 Only on remote (old):      {len(status['only_remote'])}")
    print()
    
    need_update = len(status['missing_remote']) + len(status['outdated']) + len(status['different_size'])
    if need_update == 0:
        print("✅ ALL FILES ARE UP-TO-DATE!")
    else:
        print(f"⚠️  NEED TO UPDATE: {need_update} files")
    
    print()
    return status

def main():
    print()
    print("=" * 70)
    print("🔍 VPS FILE STATUS CHECK")
    print("=" * 70)
    print(f"  VPS: {VPS_HOST}@{VPS_USER}")
    print(f"  Frontend Remote: {FRONTEND_REMOTE}")
    print(f"  Frontend Local: {FRONTEND_LOCAL}")
    print()
    
    # Get local files
    print("📂 Scanning local files...")
    local_files = get_local_files(FRONTEND_LOCAL)
    print(f"✓ Found {len(local_files)} local files")
    print()
    
    # Check VPS
    print("🌐 Checking VPS...")
    remote_files = check_vps()
    
    if remote_files is None:
        print("✗ Failed to check VPS")
        return False
    
    print(f"✓ Found {len(remote_files)} remote files")
    print()
    
    # Compare
    status = compare_files(local_files, remote_files)
    
    # Auto-deploy recommendation
    need_update = len(status['missing_remote']) + len(status['outdated']) + len(status['different_size'])
    if need_update > 0:
        print()
        print("=" * 70)
        print("💡 RECOMMENDATION:")
        print("=" * 70)
        print(f"  Run: python deploy_frontend.py")
        print("  This will upload all {0} missing/outdated files".format(need_update))
        print()
    
    return True

if __name__ == "__main__":
    main()
