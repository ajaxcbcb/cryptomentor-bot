
#!/usr/bin/env python3
"""
System Health Monitor for CryptoMentor AI
Consolidates all health check and verification functionality
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from database import Database
from crypto_api import CryptoAPI

load_dotenv()

class SystemHealth:
    def __init__(self):
        self.db = Database()
        self.crypto_api = CryptoAPI()

    def check_environment(self):
        """Check deployment environment"""
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.path.exists('/tmp/repl_deployment_flag')
        )
        return is_deployment

    def check_api_keys(self):
        """Check all API keys"""
        keys = {
            'telegram': bool(os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')),
            'coinapi': bool(os.getenv('COINAPI_KEY')),
            'coingecko': bool(os.getenv('COINGECKO_API_KEY')),
            'cryptonews': bool(os.getenv('CRYPTONEWS_API_KEY'))
        }
        return keys

    def check_database_health(self):
        """Check database health"""
        try:
            stats = self.db.get_bot_statistics()
            
            # Check for data issues
            self.db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL")
            null_ids = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
            negative_credits = self.db.cursor.fetchone()[0]
            
            return {
                'total_users': stats['total_users'],
                'premium_users': stats['premium_users'],
                'data_issues': null_ids + negative_credits,
                'healthy': null_ids == 0 and negative_credits == 0
            }
        except Exception as e:
            return {'error': str(e), 'healthy': False}

    def check_api_connectivity(self):
        """Check API connectivity"""
        apis = {}
        
        # Binance
        try:
            response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
            apis['binance'] = response.status_code == 200
        except:
            apis['binance'] = False
        
        # CoinGecko
        try:
            response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
            apis['coingecko'] = response.status_code == 200
        except:
            apis['coingecko'] = False
        
        # CryptoNews (if key exists)
        cryptonews_key = os.getenv('CRYPTONEWS_API_KEY')
        if cryptonews_key:
            try:
                response = requests.get(
                    "https://cryptonews-api.com/api/v1/category",
                    params={'section': 'general', 'items': 1, 'token': cryptonews_key},
                    timeout=10
                )
                apis['cryptonews'] = response.status_code == 200
            except:
                apis['cryptonews'] = False
        else:
            apis['cryptonews'] = None
        
        return apis

    def generate_health_report(self):
        """Generate comprehensive health report"""
        print("🏥 CryptoMentor AI - System Health Report")
        print("=" * 50)
        print(f"⏰ Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Environment
        is_deployment = self.check_environment()
        print(f"🌍 Environment: {'🚀 DEPLOYMENT' if is_deployment else '🔧 DEVELOPMENT'}")
        
        # API Keys
        keys = self.check_api_keys()
        print(f"\n🔐 API Keys:")
        for key, status in keys.items():
            print(f"  • {key.upper()}: {'✅ SET' if status else '❌ MISSING'}")
        
        # Database
        db_health = self.check_database_health()
        print(f"\n🗄️ Database:")
        if 'error' not in db_health:
            print(f"  • Users: {db_health['total_users']} (Premium: {db_health['premium_users']})")
            print(f"  • Health: {'✅ GOOD' if db_health['healthy'] else '⚠️ ISSUES'}")
            if db_health['data_issues'] > 0:
                print(f"  • Issues: {db_health['data_issues']} records need fixing")
        else:
            print(f"  • Error: {db_health['error']}")
        
        # API Connectivity
        apis = self.check_api_connectivity()
        print(f"\n🌐 API Connectivity:")
        for api, status in apis.items():
            if status is None:
                print(f"  • {api.upper()}: ⚠️ NOT CONFIGURED")
            else:
                print(f"  • {api.upper()}: {'✅ ONLINE' if status else '❌ OFFLINE'}")
        
        # Overall Status
        working_keys = sum(keys.values())
        working_apis = sum(1 for v in apis.values() if v is True)
        
        if working_keys >= 2 and working_apis >= 1 and db_health.get('healthy', False):
            status = "🟢 EXCELLENT"
        elif working_keys >= 1 and working_apis >= 1:
            status = "🟡 GOOD"
        else:
            status = "🔴 NEEDS ATTENTION"
        
        print(f"\n🎯 Overall Status: {status}")
        
        return {
            'environment': is_deployment,
            'keys': keys,
            'database': db_health,
            'apis': apis,
            'overall_healthy': working_keys >= 2 and working_apis >= 1
        }

def main():
    """Main health check function"""
    health = SystemHealth()
    report = health.generate_health_report()
    return report['overall_healthy']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
