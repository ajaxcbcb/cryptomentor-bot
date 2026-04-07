"""
Example: Multiple Concurrent Positions with Risk Management
Demonstrates how to manage risk across multiple open positions
"""

import sys
sys.path.insert(0, 'Bismillah')

from app.risk_calculator import calculate_position_size


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title):
    print(f"\n{'─' * 80}")
    print(f"{title}")
    print(f"{'─' * 80}")


# ============================================================================
# SCENARIO: Multiple Concurrent Positions
# ============================================================================

print_header("MULTIPLE CONCURRENT POSITIONS - RISK MANAGEMENT")

print("""
Pertanyaan: "Berarti ini maximal hanya bisa 1 posisi saja di saat yang bersamaan ya?"

Jawaban: TIDAK! Modul ini mendukung MULTIPLE POSITIONS secara bersamaan.

Konsep Kunci:
1. Risk PER TRADE tetap konsisten (misal 2% per trade)
2. Total risk exposure = jumlah semua posisi terbuka
3. Max concurrent positions dikontrol oleh engine (default: 4 posisi)
4. Setiap posisi dihitung independen dengan risk yang sama
""")

# ============================================================================
# Example 1: 4 Concurrent Positions
# ============================================================================

print_section("EXAMPLE 1: 4 Concurrent Positions (Max Allowed)")

balance = 1000.0
risk_per_trade = 2.0  # 2% per trade
max_concurrent = 4

print(f"\n📊 Account Setup:")
print(f"   Balance: ${balance:,.2f}")
print(f"   Risk per Trade: {risk_per_trade}%")
print(f"   Max Concurrent Positions: {max_concurrent}")

positions = [
    {"symbol": "BTC", "entry": 66500.0, "sl": 65500.0, "side": "LONG"},
    {"symbol": "ETH", "entry": 3200.0, "sl": 3100.0, "side": "LONG"},
    {"symbol": "SOL", "entry": 150.0, "sl": 145.0, "side": "LONG"},
    {"symbol": "BNB", "entry": 580.0, "sl": 570.0, "side": "LONG"},
]

print(f"\n{'Symbol':<8} {'Entry':<12} {'Stop Loss':<12} {'Risk $':<12} {'Position Size':<20}")
print("─" * 75)

total_risk = 0.0
for pos in positions:
    calc = calculate_position_size(
        last_balance=balance,
        risk_percentage=risk_per_trade,
        entry_price=pos["entry"],
        stop_loss_price=pos["sl"]
    )
    
    if calc["status"] == "success":
        risk_amt = calc["risk_amount"]
        pos_size = calc["position_size"]
        total_risk += risk_amt
        
        print(f"{pos['symbol']:<8} ${pos['entry']:<11,.2f} ${pos['sl']:<11,.2f} "
              f"${risk_amt:<11.2f} {pos_size:.8f}")

print(f"\n💰 Risk Summary:")
print(f"   Risk per Position: ${balance * risk_per_trade / 100:.2f} ({risk_per_trade}%)")
print(f"   Total Positions: {len(positions)}")
print(f"   Total Risk Exposure: ${total_risk:.2f} ({(total_risk/balance)*100:.1f}%)")
print(f"   Max Possible Loss: ${total_risk:.2f} (if ALL 4 positions hit SL)")

# ============================================================================
# Example 2: Progressive Position Opening
# ============================================================================

print_section("EXAMPLE 2: Progressive Position Opening")

print("""
Skenario: Bot membuka posisi satu per satu seiring sinyal muncul.
Balance tetap sama, tapi risk exposure bertambah seiring posisi terbuka.
""")

balance = 1000.0
risk_pct = 2.0

print(f"\n{'Stage':<20} {'Open Positions':<18} {'Total Risk $':<15} {'Total Risk %':<15}")
print("─" * 70)

stages = [
    ("No positions", 0),
    ("1st position (BTC)", 1),
    ("2nd position (ETH)", 2),
    ("3rd position (SOL)", 3),
    ("4th position (BNB)", 4),
]

for stage_name, num_positions in stages:
    total_risk = num_positions * (balance * risk_pct / 100)
    total_risk_pct = (total_risk / balance) * 100
    
    print(f"{stage_name:<20} {num_positions:<18} ${total_risk:<14.2f} {total_risk_pct:<14.1f}%")

print(f"\n💡 Insight:")
print(f"   - Setiap posisi: 2% risk")
print(f"   - 4 posisi bersamaan: 8% total risk exposure")
print(f"   - Jika semua SL hit: Loss 8% dari capital")
print(f"   - Jika semua TP hit (1:2): Profit 16% dari capital")

# ============================================================================
# Example 3: Dynamic Balance Adjustment
# ============================================================================

print_section("EXAMPLE 3: Dynamic Balance Adjustment")

print("""
Skenario: Balance berubah seiring profit/loss, tapi risk % tetap konsisten.
Ini menunjukkan bagaimana position size menyesuaikan dengan balance.
""")

risk_pct = 2.0
entry = 66500.0
sl = 65500.0

print(f"\n{'Balance':<15} {'Risk Amount':<15} {'Position Size':<20} {'Total Risk (4 pos)':<20}")
print("─" * 75)

balances = [500, 1000, 2000, 5000, 10000]

for bal in balances:
    calc = calculate_position_size(bal, risk_pct, entry, sl)
    if calc["status"] == "success":
        risk_amt = calc["risk_amount"]
        pos_size = calc["position_size"]
        total_risk_4pos = risk_amt * 4
        
        print(f"${bal:<14,.2f} ${risk_amt:<14.2f} {pos_size:.8f} BTC{'':<5} "
              f"${total_risk_4pos:<19.2f}")

print(f"\n💡 Insight:")
print(f"   - Risk % tetap: {risk_pct}%")
print(f"   - Position size menyesuaikan dengan balance")
print(f"   - Total risk 4 posisi selalu 8% dari balance")

# ============================================================================
# Example 4: Mixed Win/Loss Scenario
# ============================================================================

print_section("EXAMPLE 4: Mixed Win/Loss with Multiple Positions")

print("""
Skenario Real: 4 posisi terbuka, hasil berbeda-beda.
Menunjukkan bagaimana multiple positions mempengaruhi P&L.
""")

balance = 1000.0
risk_pct = 2.0

positions_outcome = [
    {"symbol": "BTC", "outcome": "WIN", "rr": 2},   # TP hit
    {"symbol": "ETH", "outcome": "WIN", "rr": 2},   # TP hit
    {"symbol": "SOL", "outcome": "LOSS", "rr": -1}, # SL hit
    {"symbol": "BNB", "outcome": "WIN", "rr": 2},   # TP hit
]

print(f"\n{'Symbol':<8} {'Risk $':<12} {'Outcome':<12} {'P&L $':<12}")
print("─" * 50)

total_pnl = 0.0
risk_per_pos = balance * risk_pct / 100

for pos in positions_outcome:
    if pos["outcome"] == "WIN":
        pnl = risk_per_pos * pos["rr"]
        outcome_str = f"TP HIT (1:{pos['rr']})"
    else:
        pnl = risk_per_pos * pos["rr"]
        outcome_str = "SL HIT"
    
    total_pnl += pnl
    
    print(f"{pos['symbol']:<8} ${risk_per_pos:<11.2f} {outcome_str:<12} "
          f"{pnl:+.2f}")

new_balance = balance + total_pnl

print(f"\n📊 Summary:")
print(f"   Starting Balance: ${balance:.2f}")
print(f"   Total P&L: ${total_pnl:+.2f}")
print(f"   New Balance: ${new_balance:.2f}")
print(f"   Return: {(total_pnl/balance)*100:+.1f}%")
print(f"   Win Rate: 75% (3 wins, 1 loss)")

# ============================================================================
# Example 5: Risk Allocation Strategy
# ============================================================================

print_section("EXAMPLE 5: Risk Allocation Strategies")

print("""
Berbagai strategi alokasi risk untuk multiple positions:
""")

balance = 1000.0

strategies = [
    {
        "name": "Conservative (1% per trade, max 4 pos)",
        "risk_per_trade": 1.0,
        "max_positions": 4,
        "total_risk": 4.0
    },
    {
        "name": "Standard (2% per trade, max 4 pos)",
        "risk_per_trade": 2.0,
        "max_positions": 4,
        "total_risk": 8.0
    },
    {
        "name": "Aggressive (2% per trade, max 6 pos)",
        "risk_per_trade": 2.0,
        "max_positions": 6,
        "total_risk": 12.0
    },
    {
        "name": "Very Aggressive (3% per trade, max 4 pos)",
        "risk_per_trade": 3.0,
        "max_positions": 4,
        "total_risk": 12.0
    },
]

print(f"\n{'Strategy':<45} {'Risk/Trade':<12} {'Max Pos':<10} {'Total Risk':<12}")
print("─" * 85)

for strat in strategies:
    print(f"{strat['name']:<45} {strat['risk_per_trade']}%{'':<10} "
          f"{strat['max_positions']:<10} {strat['total_risk']}%")

print(f"\n💡 Rekomendasi:")
print(f"   - Pemula: 1% per trade, max 3-4 posisi (3-4% total risk)")
print(f"   - Intermediate: 2% per trade, max 4 posisi (8% total risk)")
print(f"   - Advanced: 2-3% per trade, max 4-6 posisi (8-18% total risk)")

# ============================================================================
# Summary
# ============================================================================

print_header("KESIMPULAN")

print("""
✅ MULTIPLE POSITIONS FULLY SUPPORTED!

1. Risk Per Trade Konsisten
   - Setiap posisi dihitung independen
   - Risk % tetap sama untuk semua posisi
   - Position size menyesuaikan dengan SL distance

2. Total Risk Exposure
   - Total risk = risk_per_trade × jumlah_posisi_terbuka
   - Contoh: 2% × 4 posisi = 8% total exposure
   - Max concurrent positions dikontrol oleh engine

3. Flexible & Scalable
   - Bisa 1 posisi, 2 posisi, atau 4 posisi bersamaan
   - Balance adjustment otomatis
   - Works dengan account size apapun

4. Risk Control
   - Daily loss limit: 5% (circuit breaker)
   - Max concurrent: 4 posisi (configurable)
   - Per trade risk: 1-3% (user setting)

5. Real-World Application
   - Bot scan 10 pairs: BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, MATIC
   - Buka posisi saat sinyal muncul (max 4 bersamaan)
   - Setiap posisi: risk konsisten 2%
   - Total exposure: max 8% (4 × 2%)

Modul ini DIRANCANG untuk multiple concurrent positions! 🚀
""")
