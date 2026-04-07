# Risk Selection UI Messages

**Messages yang akan ditampilkan ke user di Telegram bot**

---

## Message 1: Penjelasan Awal (Education)

```
📚 <b>Apa itu Risk Per Trade?</b>

Risk Per Trade adalah berapa persen dari modal kamu yang siap kamu "pertaruhkan" di setiap trade.

<b>Kenapa ini penting?</b>

1️⃣ <b>Melindungi Modal</b>
   Dengan risk 2%, kamu bisa tahan 50+ loss berturut-turut tanpa habis modal!

2️⃣ <b>Otomatis Compounding</b>
   Kalau profit, position size otomatis naik. Kalau loss, otomatis turun.

3️⃣ <b>Trading Lebih Tenang</b>
   Tidak stress karena tahu risk sudah terkontrol.

<b>Contoh Sederhana:</b>

Modal: $100
Risk: 2%

• Kalau LOSS → Turun $2 (sisa $98)
• Kalau WIN (RR 1:2) → Naik $4 (jadi $104)

Position size otomatis dihitung oleh bot berdasarkan:
✓ Balance kamu saat ini
✓ Risk % yang kamu pilih
✓ Jarak Stop Loss

<b>Mau lanjut pilih risk level?</b>

[📖 Baca Penjelasan Lengkap]  [✅ Ya, Pilih Risk]
```

---

## Message 2: Pilihan Risk Level

```
⚙️ <b>Pilih Risk Per Trade</b>

Balance kamu saat ini: <b>$125.50</b>

Pilih berapa persen yang siap kamu risk per trade:

┌─────────────────────────────────
│ 🛡️ <b>1% - Sangat Aman</b>
│ Risk: $1.26 per trade
│ Tahan: 100+ loss berturut-turut
│ Cocok: Pemula, modal kecil
│ Growth: Lambat tapi stabil
│ [Pilih 1%]
├─────────────────────────────────
│ ⚖️ <b>2% - Seimbang</b> ⭐ RECOMMENDED
│ Risk: $2.51 per trade
│ Tahan: 50+ loss berturut-turut
│ Cocok: Kebanyakan trader
│ Growth: Sedang & sustainable
│ [Pilih 2%]
├─────────────────────────────────
│ ⚡ <b>3% - Agresif</b>
│ Risk: $3.77 per trade
│ Tahan: 33+ loss berturut-turut
│ Cocok: Trader berpengalaman
│ Growth: Cepat
│ [Pilih 3%]
├─────────────────────────────────
│ 🔥 <b>5% - Sangat Agresif</b>
│ Risk: $6.28 per trade
│ Tahan: 20+ loss berturut-turut
│ Cocok: Pro trader only
│ Growth: Sangat cepat
│ [Pilih 5%]
└─────────────────────────────────

💡 <b>Tips:</b> Kebanyakan pro trader pakai 1-2%. Mulai dari sini dulu, nanti bisa diubah kapan saja!

[📊 Lihat Simulasi]  [❓ Tanya Admin]
```

---

## Message 3: Simulasi Perbandingan

```
📊 <b>Simulasi Risk Level</b>

Balance: $100
Timeframe: 10 trades (5 win, 5 loss)
RR Ratio: 1:2

<b>Hasil Simulasi:</b>

🛡️ <b>Risk 1%</b>
• Setelah 5 win: $110.41 (+10.4%)
• Setelah 5 loss: $95.10 (-4.9%)
• Net (5W-5L): $105.20 (+5.2%)

⚖️ <b>Risk 2%</b> ⭐
• Setelah 5 win: $121.67 (+21.7%)
• Setelah 5 loss: $90.39 (-9.6%)
• Net (5W-5L): $110.40 (+10.4%)

⚡ <b>Risk 3%</b>
• Setelah 5 win: $133.83 (+33.8%)
• Setelah 5 loss: $85.88 (-14.1%)
• Net (5W-5L): $115.60 (+15.6%)

🔥 <b>Risk 5%</b>
• Setelah 5 win: $161.05 (+61.1%)
• Setelah 5 loss: $77.38 (-22.6%)
• Net (5W-5L): $125.00 (+25.0%)

<b>Kesimpulan:</b>
• Risk lebih tinggi = Profit lebih besar, tapi loss juga lebih besar
• Risk 2% paling balance untuk long-term growth
• Risk 1% paling aman untuk pemula

[⬅️ Kembali]  [✅ Pilih Risk]
```

---

## Message 4: Konfirmasi Pilihan (Risk 2%)

```
✅ <b>Konfirmasi Risk Setting</b>

Kamu memilih: <b>2% Risk Per Trade</b>

<b>Detail:</b>
• Balance saat ini: $125.50
• Max loss per trade: $2.51 (2%)
• Survivability: 50+ consecutive losses
• Risk level: Moderate (Recommended)

<b>Apa artinya?</b>

Bot akan otomatis hitung position size untuk setiap trade agar risk kamu selalu 2% dari balance.

<b>Contoh:</b>
• Entry: $50,000
• Stop Loss: $49,000 (2% distance)
• Position size: $125.50 (2% risk / 2% SL)
• Margin (10x leverage): $12.55

Kalau SL kena → Loss $2.51 (2% dari $125.50)
Kalau TP kena (RR 1:2) → Profit $5.02

<b>Keuntungan:</b>
✓ Tidak bisa habis modal
✓ Otomatis compounding
✓ Risk terkontrol
✓ Bisa diubah kapan saja

<b>Yakin dengan pilihan ini?</b>

[✅ Ya, Lanjutkan]  [⬅️ Ubah Risk]
```

---

## Message 5: Success Confirmation

```
🎉 <b>Risk Setting Berhasil!</b>

Risk per trade kamu sekarang: <b>2%</b>

<b>Yang berubah:</b>
✓ Position size dihitung otomatis
✓ Risk selalu 2% dari balance
✓ Compounding aktif

<b>Yang TIDAK berubah:</b>
• Leverage tetap sama
• Strategy tetap sama
• Min confidence tetap sama

<b>Monitoring:</b>
Kamu bisa lihat risk info di dashboard:
• Current balance
• Risk per trade (%)
• Risk amount ($)
• Survivability

<b>Mau ubah risk?</b>
Buka Dashboard → Risk Settings

[📊 Lihat Dashboard]  [🚀 Mulai Trading]
```

---

## Message 6: Dashboard Display (Updated)

```
📊 <b>AutoTrade Dashboard</b>

<b>Status:</b> 🟢 Active
<b>Mode:</b> Swing Trading
<b>Exchange:</b> Bitunix

<b>Balance & Risk:</b>
💰 Balance: $125.50
⚖️ Risk per trade: 2% ($2.51)
🛡️ Survivability: 50+ losses

<b>Performance Today:</b>
📈 Trades: 3 (2W-1L)
💵 PnL: +$8.50 (+6.8%)
🎯 Win rate: 66.7%

<b>Open Positions:</b> 2/4
• BTCUSDT LONG @ $50,000 (+2.5%)
• ETHUSDT SHORT @ $3,000 (+1.2%)

[⚙️ Risk Settings]  [📊 Performance]  [⏸️ Pause]
```

---

## Message 7: Risk Settings Modal

```
⚙️ <b>Risk Management Settings</b>

<b>Current Settings:</b>
• Balance: $125.50
• Risk per trade: 2%
• Max loss per trade: $2.51
• Survivability: 50+ losses

<b>Ubah Risk Level:</b>

[🛡️ 1% - Sangat Aman]
[⚖️ 2% - Seimbang] ✓ Current
[⚡ 3% - Agresif]
[🔥 5% - Sangat Agresif]

<b>Custom Risk:</b>
[⌨️ Input Manual (0.5% - 10%)]

<b>Info:</b>
• Perubahan berlaku untuk trade berikutnya
• Position size dihitung ulang otomatis
• Tidak affect open positions

[📖 Pelajari Risk]  [⬅️ Kembali]
```

---

## Message 8: Custom Risk Input

```
⌨️ <b>Input Custom Risk</b>

Masukkan risk percentage yang kamu inginkan:

<b>Range:</b> 0.5% - 10%

<b>Contoh:</b>
• 1.5 → Risk 1.5%
• 2.5 → Risk 2.5%
• 4.0 → Risk 4%

<b>Rekomendasi:</b>
• Pemula: 1-2%
• Intermediate: 2-3%
• Advanced: 3-5%
• Pro: 1-2% (capital preservation)

<b>Balance kamu:</b> $125.50

Ketik angka risk (contoh: 2.5):

[⬅️ Kembali ke Pilihan]
```

---

## Message 9: Risk Changed Notification

```
✅ <b>Risk Setting Updated!</b>

<b>Perubahan:</b>
• Risk lama: 2% ($2.51)
• Risk baru: 3% ($3.77)

<b>Impact:</b>
• Position size akan lebih besar
• Potential profit lebih tinggi
• Potential loss juga lebih tinggi
• Survivability: 33+ losses

<b>Berlaku untuk:</b>
✓ Trade berikutnya
✓ Semua pair
✓ Semua mode (swing/scalping)

<b>Open positions:</b>
Tidak terpengaruh (tetap pakai risk lama)

<b>Monitoring:</b>
Pantau performance di dashboard untuk lihat impact perubahan ini.

[📊 Lihat Dashboard]  [✅ OK]
```

---

## Message 10: Warning untuk High Risk

```
⚠️ <b>Warning: High Risk!</b>

Kamu memilih risk <b>5%</b> per trade.

<b>Ini artinya:</b>
• Max loss per trade: $6.28
• Hanya tahan 20 consecutive losses
• Volatility tinggi
• Stress level tinggi

<b>Rekomendasi:</b>
Risk 5% hanya untuk:
✓ Pro trader dengan track record bagus
✓ Modal besar (>$1000)
✓ Sudah profit konsisten
✓ Paham risk management

<b>Apakah kamu yakin?</b>

Kebanyakan pro trader pakai 1-2% untuk long-term sustainability.

[⬅️ Pilih Risk Lebih Rendah]  [✅ Ya, Saya Yakin]
```

---

## Message 11: FAQ Quick Access

```
❓ <b>FAQ - Risk Per Trade</b>

<b>Q: Apakah risk bisa diubah kapan saja?</b>
A: Ya! Buka Dashboard → Risk Settings

<b>Q: Kalau modal naik, risk juga naik?</b>
A: Ya, otomatis! Ini yang disebut compounding.

<b>Q: Kalau modal turun, risk juga turun?</b>
A: Ya! Ini melindungi kamu dari habis modal.

<b>Q: Berapa risk paling bagus?</b>
A: 2% untuk kebanyakan trader. Pro trader pakai 1-2%.

<b>Q: Apakah harus pakai leverage tinggi?</b>
A: Tidak! Risk dan leverage berbeda. Bot akan hitung position size yang tepat.

<b>Masih ada pertanyaan?</b>

[💬 Tanya Admin @BillFarr]  [📖 Baca Panduan Lengkap]
```

---

## Button Labels

**Main Buttons:**
- `⚙️ Risk Settings` - Open risk settings modal
- `📖 Pelajari Risk` - Show education content
- `📊 Lihat Simulasi` - Show simulation
- `✅ Pilih Risk` - Confirm selection
- `⬅️ Kembali` - Go back
- `❓ Tanya Admin` - Contact support

**Risk Level Buttons:**
- `🛡️ 1% - Sangat Aman`
- `⚖️ 2% - Seimbang ⭐`
- `⚡ 3% - Agresif`
- `🔥 5% - Sangat Agresif`
- `⌨️ Custom Risk`

---

## Callback Data Format

```python
# Risk selection
"at_risk_settings"  # Show risk settings modal
"at_risk_edu"       # Show education
"at_risk_sim"       # Show simulation
"at_set_risk_1"     # Set risk to 1%
"at_set_risk_2"     # Set risk to 2%
"at_set_risk_3"     # Set risk to 3%
"at_set_risk_5"     # Set risk to 5%
"at_risk_custom"    # Input custom risk
"at_risk_confirm_1" # Confirm risk 1%
"at_risk_confirm_2" # Confirm risk 2%
"at_risk_confirm_3" # Confirm risk 3%
"at_risk_confirm_5" # Confirm risk 5%
```

---

## Implementation Notes

**Flow:**
1. User clicks "Risk Settings" di dashboard
2. Show education message (optional, bisa skip)
3. Show risk level selection
4. User pilih risk level
5. Show confirmation dengan detail
6. User confirm
7. Update database
8. Show success message
9. Update dashboard display

**Features:**
- ✅ Clear education content
- ✅ Visual comparison
- ✅ Real examples dengan balance user
- ✅ Warning untuk high risk
- ✅ FAQ quick access
- ✅ Easy to change anytime

---

**Messages ready untuk implementation!** 🚀
