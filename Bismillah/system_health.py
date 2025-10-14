
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, List

class SystemHealth:
    def __init__(self):
        self.status = {}
        
    def check_api_connectivity(self):
        """Check API connectivity - Binance only"""
        apis = {}
        
        # Binance Spot
        try:
            response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
            apis['binance_spot'] = response.status_code == 200
        except:
            apis['binance_spot'] = False
        
        # Binance Futures
        try:
            response = requests.get("https://fapi.binance.com/fapi/v1/ping", timeout=10)
            apis['binance_futures'] = response.status_code == 200
        except:
            apis['binance_futures'] = False
        
        return apis
    
    def check_database_status(self):
        """Check database connections"""
        db_status = {}
        
        # Local SQLite
        try:
            import sqlite3
            conn = sqlite3.connect('cryptomentor.db')
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            db_status['sqlite'] = True
            conn.close()
        except:
            db_status['sqlite'] = False
        
        # Supabase
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            if supabase_url and supabase_key:
                headers = {
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}'
                }
                response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
                db_status['supabase'] = response.status_code == 200
            else:
                db_status['supabase'] = None  # Not configured
        except:
            db_status['supabase'] = False
        
        return db_status
    
    def get_system_info(self):
        """Get basic system information"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'timestamp': datetime.now().isoformat()
        }
    
    def run_comprehensive_check(self):
        """Run all health checks"""
        return {
            'apis': self.check_api_connectivity(),
            'databases': self.check_database_status(),
            'system': self.get_system_info(),
            'timestamp': datetime.now().isoformat()
        }

# Global instance
system_health = SystemHealth()
