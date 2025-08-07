
#!/usr/bin/env python3
"""
Utility functions for CryptoMentor AI
Common functions used across the application
"""

import os
import time
import json
from datetime import datetime

def mask_api_key(key):
    """Mask API key for security display"""
    if not key or len(key) < 8:
        return "❌ NOT SET"
    return f"✅ SET ({key[:8]}...{key[-4:]})"

def is_deployment_mode():
    """Check if running in deployment mode"""
    return (
        os.getenv('REPLIT_DEPLOYMENT') == '1' or 
        os.getenv('REPL_DEPLOYMENT') == '1' or
        os.path.exists('/tmp/repl_deployment_flag')
    )

def safe_float_parse(value, default=0.0):
    """Safely parse float with default fallback"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_parse(value, default=0):
    """Safely parse int with default fallback"""
    try:
        if value is None:
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def load_json_file(file_path, default=None):
    """Safely load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def save_json_file(file_path, data):
    """Safely save JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False

def format_number(number, decimals=2):
    """Format number with proper separators"""
    try:
        if isinstance(number, (int, float)):
            return f"{number:,.{decimals}f}"
        return str(number)
    except:
        return "0.00"

def get_file_size(file_path):
    """Get file size in human readable format"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except:
        return "Unknown"

def create_directory(directory):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating directory {directory}: {e}")
        return False

def cleanup_old_files(directory, max_age_days=7):
    """Clean up old files in directory"""
    try:
        if not os.path.exists(directory):
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        cleaned = 0
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    cleaned += 1
        
        return cleaned
    except Exception as e:
        print(f"❌ Error cleaning up files: {e}")
        return 0
