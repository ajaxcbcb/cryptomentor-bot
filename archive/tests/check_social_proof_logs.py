#!/usr/bin/env python3
"""
Script untuk cek social proof broadcast logs dan trade history
Untuk verifikasi apakah notifikasi profit sudah tersampaikan ke user
"""

import os
import sys
from datetime import datetime, timedelta

# Load .env file
from pathlib import Path
env_path = Path(__file__).parent / 'Bismillah' / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def check_social_proof_activity():
    """Cek aktivitas social proof broadcast dari database"""
    try:
        from app.supabase_repo import _client
        
        print("=" * 70)
        print("🔍 SOCIAL PROOF BROADCAST VERIFICATION")
        print("=" * 70)
        print()
        
        s = _client()
        
        # 1. Cek trade history yang closed dengan profit >= $5
        print("📊 TRADE HISTORY - Profit Trades (≥$5 USDT)")
        print("-" * 70)
        
        # Get trades from last 7 days
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        trades_res = s.table("autotrade_trades").select(
            "id, telegram_id, symbol, side, pnl_usdt, closed_at, status, leverage"
        ).eq("status", "closed_tp").gte("pnl_usdt", 5.0).gte(
            "closed_at", week_ago
        ).order("closed_at", desc=True).limit(20).execute()
        
        profit_trades = trades_res.data or []
        
        if not profit_trades:
            print("❌ No profit trades ≥$5 found in last 7 days")
            print()
        else:
            print(f"✅ Found {len(profit_trades)} profit trades ≥$5 USDT:\n")
            
            for i, trade in enumerate(profit_trades, 1):
                tid = trade.get("telegram_id")
                symbol = trade.get("symbol", "?")
                side = trade.get("side", "?")
                pnl = trade.get("pnl_usdt", 0)
                closed = trade.get("closed_at", "")
                leverage = trade.get("leverage", 1)
                
                # Get user info
                try:
                    user_res = s.table("users").select("first_name").eq("telegram_id", tid).limit(1).execute()
                    fname = user_res.data[0].get("first_name", "Unknown") if user_res.data else "Unknown"
                except:
                    fname = "Unknown"
                
                print(f"{i}. User: {fname} (ID: {tid})")
                print(f"   Trade: {symbol} {side} {leverage}x")
                print(f"   Profit: ${pnl:.2f} USDT")
                print(f"   Closed: {closed}")
                print()
        
        # 2. Cek berapa user yang BELUM daftar autotrade (target broadcast)
        print("👥 TARGET AUDIENCE - Non-Autotrade Users")
        print("-" * 70)
        
        # Total users
        total_res = s.table("users").select("telegram_id", count="exact").execute()
        total_users = total_res.count or 0
        
        # Users with autotrade
        at_res = s.table("autotrade_sessions").select("telegram_id", count="exact").execute()
        at_users = at_res.count or 0
        
        target_users = total_users - at_users
        
        print(f"📊 Total Users: {total_users}")
        print(f"🤖 Autotrade Users: {at_users}")
        print(f"🎯 Target Broadcast: {target_users} users")
        print()
        
        # 3. Sample target users (first 10)
        print("📋 Sample Target Users (first 10):")
        print("-" * 70)
        
        all_users_res = s.table("users").select("telegram_id, first_name").limit(1000).execute()
        all_uids = {row["telegram_id"]: row.get("first_name", "Unknown") for row in (all_users_res.data or [])}
        
        at_uids_res = s.table("autotrade_sessions").select("telegram_id").execute()
        at_uids = {row["telegram_id"] for row in (at_uids_res.data or [])}
        
        target_sample = [(uid, name) for uid, name in all_uids.items() if uid not in at_uids][:10]
        
        if target_sample:
            for i, (uid, name) in enumerate(target_sample, 1):
                print(f"{i}. {name} (ID: {uid})")
        else:
            print("❌ No target users found")
        
        print()
        
        # 4. Summary
        print("=" * 70)
        print("📝 SUMMARY")
        print("=" * 70)
        
        if profit_trades and target_users > 0:
            print(f"✅ System Ready: {len(profit_trades)} profit trades found")
            print(f"✅ Target Audience: {target_users} users will receive broadcasts")
            print()
            print("🔔 When next profit ≥$5 occurs:")
            print(f"   → Broadcast will be sent to {target_users} non-autotrade users")
            print(f"   → Username will be masked for privacy")
            print(f"   → Cooldown: 4 hours per user")
        elif not profit_trades:
            print("⏳ Waiting for profit trades ≥$5 USDT")
            print(f"   Target audience ready: {target_users} users")
        else:
            print("⚠️ No target users (all users already using autotrade)")
        
        print()
        
        # 5. Check recent autotrade sessions for activity
        print("🤖 RECENT AUTOTRADE ACTIVITY")
        print("-" * 70)
        
        active_sessions = s.table("autotrade_sessions").select(
            "telegram_id, status, exchange_id, updated_at"
        ).eq("status", "active").order("updated_at", desc=True).limit(10).execute()
        
        if active_sessions.data:
            print(f"✅ {len(active_sessions.data)} active autotrade sessions:\n")
            for i, sess in enumerate(active_sessions.data, 1):
                tid = sess.get("telegram_id")
                exchange = sess.get("exchange_id", "?")
                updated = sess.get("updated_at", "")
                
                try:
                    user_res = s.table("users").select("first_name").eq("telegram_id", tid).limit(1).execute()
                    fname = user_res.data[0].get("first_name", "Unknown") if user_res.data else "Unknown"
                except:
                    fname = "Unknown"
                
                print(f"{i}. {fname} (ID: {tid}) - {exchange}")
                print(f"   Last update: {updated}")
        else:
            print("❌ No active autotrade sessions")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_social_proof_activity()
