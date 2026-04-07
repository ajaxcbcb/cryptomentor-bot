#!/usr/bin/env python3
"""Check trading_mode in database on VPS"""

import sqlite3

conn = sqlite3.connect('/root/cryptomentor-bot/Bismillah/autotrade_users.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT telegram_id, trading_mode, risk_mode, is_active 
    FROM autotrade_sessions 
    ORDER BY is_active DESC, telegram_id
''')

rows = cursor.fetchall()

print("\n=== AUTOTRADE SESSIONS ===\n")
print(f"{'User ID':<15} {'Trading Mode':<15} {'Risk Mode':<15} {'Active':<10}")
print("-" * 60)

active_count = 0
scalping_count = 0

for row in rows:
    user_id, trading_mode, risk_mode, is_active = row
    active_str = "YES" if is_active else "NO"
    print(f"{user_id:<15} {trading_mode or 'NULL':<15} {risk_mode or 'NULL':<15} {active_str:<10}")
    
    if is_active:
        active_count += 1
        if trading_mode == "scalping":
            scalping_count += 1

print("-" * 60)
print(f"\nTotal active sessions: {active_count}")
print(f"Scalping mode sessions: {scalping_count}")
print(f"Non-scalping sessions: {active_count - scalping_count}")

conn.close()
