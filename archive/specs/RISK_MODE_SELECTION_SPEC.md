# Risk Mode Selection - Specification

**Date:** April 2, 2026  
**Feature:** Dual Mode Risk Management (Recommended vs Manual)

---

## Overview

Memberikan user pilihan di awal registration dan settings:
1. **Mode Rekomendasi (Risk-Based)** - System hitung otomatis dari balance
2. **Mode Manual (Legacy)** - User set margin & leverage sendiri

---

## User Flow

### Registration Flow:

```
Start /autotrade
    ↓
Select Exchange (Bitunix/Binance/etc)
    ↓
Enter API Key & Secret
    ↓
[NEW] Choose Risk Management Mode:
    ├─ 🎯 Rekomendasi (Risk Per Trade) ← RECOMMENDED
    │   ↓
    │   Select Risk %: 1% / 2% / 3% / 5%
    │   ↓
    │   Select Leverage: 5x / 10x / 20x / 50x
    │   ↓
    │   [System auto-calculate margin from balance]
    │   ↓
    │   Confirm & Start
    │
    └─ ⚙️ Manual (Set Margin & Leverage)
        ↓
        Enter Margin (e.g., $10)
        ↓
        Select Leverage: 5x / 10x / 20x / 50x
        ↓
        Confirm & Start
```

### Settings Flow:

```
/autotrade → Settings
    ↓
Current Mode: [Rekomendasi / Manual]
    ↓
Options:
    ├─ Change Risk % (if Rekomendasi mode)
    ├─ Change Leverage (both modes)
    ├─ Change Margin (if Manual mode)
    └─ Switch Mode (Rekomendasi ↔ Manual)
```

---

## Database Changes

### Add Column: `risk_mode`

```sql
ALTER TABLE autotrade_sessions 
ADD COLUMN risk_mode VARCHAR(20) DEFAULT 'risk_based';

-- Values: 'risk_based' or 'manual'
```

### Migration:

```sql
-- Set existing users to 'manual' mode (backward compatible)
UPDATE autotrade_sessions 
SET risk_mode = 'manual' 
WHERE risk_mode IS NULL;

-- New users default to 'risk_based' (recommended)
ALTER TABLE autotrade_sessions 
ALTER COLUMN risk_mode SET DEFAULT 'risk_based';
```

---

## UI Messages

### Mode Selection:

```
🎯 <b>Pilih Mode Risk Management</b>

Pilih cara mengatur posisi trading Anda:

🌟 <b>Rekomendasi (Risk Per Trade)</b>
✅ System hitung otomatis dari balance
✅ Safe compounding
✅ Account protection
✅ Cocok untuk pemula & pro trader

⚙️ <b>Manual (Set Margin & Leverage)</b>
✅ Kontrol penuh atas margin
✅ Fixed position size
✅ Cocok untuk advanced trader

Pilih mode:
```

### Rekomendasi Mode - Risk Selection:

```
🎯 <b>Pilih Risk Per Trade</b>

Berapa % dari balance yang mau Anda risikokan per trade?

💰 Balance Anda: $100.00

🛡️ <b>1%</b> - Sangat Konservatif
   Risk: $1.00 per trade
   Bisa survive 100+ losing trades

⚖️ <b>2%</b> - Moderate (REKOMENDASI)
   Risk: $2.00 per trade
   Bisa survive 50+ losing trades

⚡ <b>3%</b> - Agresif
   Risk: $3.00 per trade
   Bisa survive 33+ losing trades

🔥 <b>5%</b> - Sangat Agresif
   Risk: $5.00 per trade
   Bisa survive 20+ losing trades

Pilih risk %:
```

### Rekomendasi Mode - Leverage Selection:

```
⚡ <b>Pilih Leverage</b>

Mode: Rekomendasi (Risk 2%)
Balance: $100.00

Leverage menentukan potensi profit & loss:

📊 <b>5x</b> - Konservatif
   Margin per trade: ~$4-10
   
📊 <b>10x</b> - Moderate (REKOMENDASI)
   Margin per trade: ~$2-5
   
📊 <b>20x</b> - Agresif
   Margin per trade: ~$1-2.5
   
📊 <b>50x</b> - Sangat Agresif
   Margin per trade: ~$0.4-1

⚠️ Leverage tinggi = profit besar tapi risk juga besar

Pilih leverage:
```

### Manual Mode - Margin Input:

```
⚙️ <b>Set Margin Per Trade</b>

Mode: Manual

Berapa USDT yang mau Anda gunakan per trade?

Contoh:
• $5 - Untuk balance $50-100
• $10 - Untuk balance $100-200
• $20 - Untuk balance $200-500

⚠️ Jangan gunakan lebih dari 10% balance Anda

Balance Anda: $100.00
Rekomendasi: $5-10

Masukkan margin (USDT):
```

### Confirmation - Rekomendasi Mode:

```
✅ <b>Konfirmasi Setup AutoTrade</b>

Mode: 🎯 Rekomendasi (Risk Per Trade)

📊 <b>Settings:</b>
• Exchange: Bitunix
• Risk per trade: 2%
• Leverage: 10x
• Balance: $100.00

💡 <b>Cara Kerja:</b>
• System otomatis hitung margin dari balance
• Position size adjust otomatis per trade
• Safe compounding saat balance naik

📈 <b>Contoh Trade:</b>
Entry: $50,000
SL: $49,000 (2% away)
→ Risk: $2.00 (2% dari $100)
→ Position: $100
→ Margin: $10 (dengan 10x leverage)
→ Qty: 0.002 BTC

Jika SL hit: Loss $2 (2% dari balance) ✅
Jika TP hit: Profit varies by R:R

Lanjutkan?
```

### Confirmation - Manual Mode:

```
✅ <b>Konfirmasi Setup AutoTrade</b>

Mode: ⚙️ Manual (Fixed Margin)

📊 <b>Settings:</b>
• Exchange: Bitunix
• Margin per trade: $10
• Leverage: 10x
• Balance: $100.00

💡 <b>Cara Kerja:</b>
• Setiap trade pakai $10 margin
• Position size: $100 ($10 × 10x)
• Fixed, tidak berubah saat balance naik

📈 <b>Contoh Trade:</b>
Entry: $50,000
→ Position: $100 (fixed)
→ Margin: $10 (fixed)
→ Qty: 0.002 BTC

⚠️ Tidak ada compounding otomatis
⚠️ Harus adjust margin manual saat balance naik

Lanjutkan?
```

---

## Settings Dashboard

### Current Settings Display:

**Rekomendasi Mode:**
```
⚙️ <b>AutoTrade Settings</b>

Mode: 🎯 Rekomendasi (Risk Per Trade)
Status: ✅ Running

📊 <b>Risk Management:</b>
• Risk per trade: 2%
• Leverage: 10x
• Balance: $150.00
• Risk amount: $3.00 per trade

💡 Position size dihitung otomatis per trade

<button>Change Risk %</button>
<button>Change Leverage</button>
<button>Switch to Manual Mode</button>
```

**Manual Mode:**
```
⚙️ <b>AutoTrade Settings</b>

Mode: ⚙️ Manual (Fixed Margin)
Status: ✅ Running

📊 <b>Risk Management:</b>
• Margin per trade: $10
• Leverage: 10x
• Balance: $150.00
• Position size: $100 (fixed)

💡 Margin tidak berubah saat balance naik

<button>Change Margin</button>
<button>Change Leverage</button>
<button>Switch to Rekomendasi Mode</button>
```

---

## Implementation Plan

### Phase 1: Database
1. Add `risk_mode` column
2. Migration script
3. Update repository functions

### Phase 2: Registration Flow
1. Add mode selection step
2. Branch flow based on mode
3. Update confirmation message

### Phase 3: Settings Flow
1. Display current mode
2. Mode-specific options
3. Switch mode functionality

### Phase 4: Engine Integration
1. Check `risk_mode` in engine
2. Use appropriate calculation
3. Logging for both modes

---

## Benefits

### For Users:
✅ Clear choice between simple (recommended) vs advanced (manual)
✅ Recommended mode guides beginners
✅ Manual mode for advanced users who want control
✅ Can switch modes anytime

### For System:
✅ Backward compatible (existing users = manual mode)
✅ New users default to better mode (risk-based)
✅ Clear separation of logic
✅ Easy to maintain

---

## Next Steps

1. Create database migration
2. Update `supabase_repo.py` with mode functions
3. Update `handlers_autotrade.py` registration flow
4. Update settings dashboard
5. Test both modes
6. Deploy

---

**Ready to implement!** 🚀
