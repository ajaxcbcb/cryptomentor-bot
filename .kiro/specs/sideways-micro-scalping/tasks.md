# Rencana Implementasi: Sideways Micro-Scalping

## Overview

Implementasi pipeline analisis sideways yang terintegrasi ke dalam `ScalpingEngine` yang sudah ada. Pipeline terdiri dari empat komponen baru (`SidewaysDetector`, `RangeAnalyzer`, `BounceDetector`, `RSIDivergenceDetector`) yang dipanggil secara berurutan di dalam `generate_scalping_signal()`. Logika trending yang sudah ada tidak diubah.

## Tasks

- [x] 1. Database migration — tambah field sideways scalping
  - Buat file `db/add_sideways_scalping_fields.sql` sesuai schema di design document
  - Tambahkan kolom: `trade_type`, `trade_subtype`, `timeframe`, `tp_strategy`, `max_hold_time`, `close_reason`, `close_price`, `quantity`, `range_support`, `range_resistance`, `range_width_pct`, `bounce_confirmed`, `rsi_divergence_detected`
  - Tambahkan index `idx_autotrade_trades_subtype` pada kolom `trade_subtype`
  - _Requirements: 11.1, 11.2, 11.3_

- [x] 2. Data models — MicroScalpSignal dan modifikasi ScalpingPosition
  - [x] 2.1 Tambahkan dataclass `MicroScalpSignal` ke `Bismillah/app/trading_mode.py`
    - Field: `symbol`, `side`, `entry_price`, `tp_price`, `sl_price`, `rr_ratio`, `range_support`, `range_resistance`, `range_width_pct`, `confidence`, `bounce_confirmed`, `rsi_divergence_detected`, `volume_ratio`, `reasons`, `is_sideways = True`, `max_hold_time = 120`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 7.1_
  - [x] 2.2 Tambahkan field `is_sideways: bool = False` ke dataclass `ScalpingPosition` yang sudah ada di `Bismillah/app/trading_mode.py`
    - Tambahkan juga field `opened_at: float` jika belum ada (untuk max hold timer)
    - _Requirements: 7.1, 7.7, 14_

- [x] 3. Implementasi `SidewaysDetector`
  - [x] 3.1 Buat file `Bismillah/app/sideways_detector.py` dengan class `SidewaysDetector` dan dataclass `SidewaysResult`
    - Implementasikan method `detect(candles_5m, candles_15m, price) -> SidewaysResult`
    - Hitung `atr_relative_pct`: ATR 14-period dari candle 5M dibagi harga × 100
    - Hitung `ema_spread_pct`: |EMA21 - EMA50| dari candle 15M dibagi harga × 100
    - Hitung `range_width_pct`: (max_high - min_low) dari 20 candle 5M terakhir dibagi harga × 100
    - Klasifikasi SIDEWAYS jika salah satu: `atr_relative_pct < 0.3` OR `ema_spread_pct < 0.2` OR `range_width_pct < 1.5`
    - Log hasil klasifikasi beserta ketiga nilai metrik
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [ ]* 3.2 Tulis property test untuk `SidewaysDetector` — Property 1: Klasifikasi Sideways Berdasarkan Threshold
    - **Property 1: Klasifikasi Sideways Berdasarkan Threshold**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    - Gunakan `@given` dengan `atr_relative` di bawah 0.3 → assert `is_sideways == True`
  - [ ]* 3.3 Tulis property test untuk `SidewaysDetector` — Property 2: Klasifikasi Trending Ketika Semua Threshold Terlampaui
    - **Property 2: Klasifikasi Trending Ketika Semua Threshold Terlampaui**
    - **Validates: Requirements 1.6**
    - Gunakan `@given` dengan semua metrik di atas threshold → assert `is_sideways == False`
  - [ ]* 3.4 Tulis unit tests untuk `SidewaysDetector` di `Bismillah/tests/test_sideways_detector.py`
    - Test contoh spesifik: candle dengan ATR = 0.25% → SIDEWAYS
    - Test edge case: candle doji (body = 0), candle identik
    - Test error handling: candle list kosong, candle kurang dari minimum

- [x] 4. Implementasi `RangeAnalyzer`
  - [x] 4.1 Buat file `Bismillah/app/range_analyzer.py` dengan class `RangeAnalyzer` dan dataclass `RangeResult`
    - Implementasikan method `analyze(candles_5m, price) -> Optional[RangeResult]`
    - Identifikasi swing high: `high[i] > high[i-1]` dan `high[i] > high[i+1]`
    - Identifikasi swing low: `low[i] < low[i-1]` dan `low[i] < low[i+1]`
    - Cluster level yang berjarak < 0.15% menjadi satu level (rata-rata harga dalam cluster)
    - Hitung jumlah touches per cluster (high/low dalam toleransi 0.15%)
    - Pilih cluster dengan `touches >= 2` sebagai level valid
    - Resistance = cluster valid tertinggi di atas harga; Support = cluster valid terendah di bawah harga
    - Validasi `range_width_pct`: return `None` jika < 0.5% atau > 3.0%
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  - [ ]* 4.2 Tulis property test untuk `RangeAnalyzer` — Property 3: Clustering Level S/R dengan Toleransi 0.15%
    - **Property 3: Clustering Level S/R dengan Toleransi 0.15%**
    - **Validates: Requirements 2.4**
    - Dua level yang berjarak < 0.15% harus dicluster menjadi satu level
  - [ ]* 4.3 Tulis property test untuk `RangeAnalyzer` — Property 4: Validasi Range Width
    - **Property 4: Validasi Range Width**
    - **Validates: Requirements 2.7, 2.8**
    - `@given` dengan `width_pct < 0.5` atau `width_pct > 3.0` → assert return `None`
  - [ ]* 4.4 Tulis unit tests untuk `RangeAnalyzer` di `Bismillah/tests/test_range_analyzer.py`
    - Test identifikasi swing high/low yang benar
    - Test clustering level berdekatan
    - Test validasi minimum touches
    - Test edge case: tidak ada swing point, semua candle flat

- [x] 5. Implementasi `BounceDetector`
  - [x] 5.1 Buat file `Bismillah/app/bounce_detector.py` dengan class `BounceDetector` dan dataclass `BounceResult`
    - Implementasikan method `detect(last_candle, support, resistance, price) -> Optional[BounceResult]`
    - Hitung `body = abs(close - open)`, `upper_wick = high - max(open, close)`, `lower_wick = min(open, close) - low`
    - Bounce LONG: `|price - support| / support < 0.002` AND `lower_wick > body`
    - Bounce SHORT: `|price - resistance| / resistance < 0.002` AND `upper_wick > body`
    - Return `None` jika tidak ada bounce yang terkonfirmasi
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  - [ ]* 5.2 Tulis property test untuk `BounceDetector` — Property 5: Konfirmasi Bounce Berdasarkan Wick Analysis
    - **Property 5: Konfirmasi Bounce Berdasarkan Wick Analysis**
    - **Validates: Requirements 3.2, 3.3**
    - Bounce LONG iff dalam 0.2% dari support AND lower_wick > body
    - Bounce SHORT iff dalam 0.2% dari resistance AND upper_wick > body
  - [ ]* 5.3 Tulis unit tests untuk `BounceDetector` di `Bismillah/tests/test_bounce_detector.py`
    - Test candle doji (body = 0): tidak ada bounce
    - Test harga tepat di support vs 0.3% dari support
    - Test wick sama panjang dengan body: tidak ada bounce

- [x] 6. Implementasi `RSIDivergenceDetector`
  - [x] 6.1 Buat file `Bismillah/app/rsi_divergence_detector.py` dengan class `RSIDivergenceDetector` dan dataclass `DivergenceResult`
    - Implementasikan method `detect(candles_5m, direction) -> DivergenceResult`
    - Hitung RSI 14-period untuk setiap candle dalam lookback window 10 candle
    - Bullish divergence: `price_now < price_10_ago` AND `rsi_now > rsi_10_ago`
    - Bearish divergence: `price_now > price_10_ago` AND `rsi_now < rsi_10_ago`
    - `confidence_bonus = 10` jika divergence terdeteksi, `0` jika tidak
    - Minimal 24 candle diperlukan (14 untuk RSI + 10 lookback)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - [ ]* 6.2 Tulis property test untuk `RSIDivergenceDetector` — Property 6: Deteksi RSI Divergence
    - **Property 6: Deteksi RSI Divergence**
    - **Validates: Requirements 4.2, 4.3**
    - Bullish divergence iff lower low price AND higher low RSI
    - Bearish divergence iff higher high price AND lower high RSI
  - [ ]* 6.3 Tulis property test untuk `RSIDivergenceDetector` — Property 7: Bonus Confidence dari Divergence
    - **Property 7: Bonus Confidence dari Divergence**
    - **Validates: Requirements 4.4, 4.5, 6.2**
    - Jika `rsi_divergence_detected = True` maka confidence lebih tinggi tepat 10 poin
  - [ ]* 6.4 Tulis unit tests untuk `RSIDivergenceDetector` di `Bismillah/tests/test_rsi_divergence_detector.py`
    - Test dengan data divergence yang diketahui
    - Test candle tidak cukup (< 24): return `detected = False`
    - Test kondisi no-divergence: harga dan RSI bergerak searah

- [x] 7. Checkpoint — Pastikan semua komponen analisis berfungsi
  - Pastikan semua tests pass, tanyakan ke user jika ada pertanyaan.

- [x] 8. Integrasi pipeline sideways ke `ScalpingEngine`
  - [x] 8.1 Modifikasi `generate_scalping_signal()` di `Bismillah/app/scalping_engine.py`
    - Tambahkan import untuk keempat komponen baru
    - Setelah fetch klines, panggil `SidewaysDetector().detect(candles_5m, candles_15m, price)`
    - Jika `is_sideways = True`: panggil `_generate_sideways_signal()` (method baru)
    - Jika `is_sideways = False`: lanjutkan ke logika trending yang sudah ada (tidak berubah)
    - Tambahkan `sideways_error_counter: Dict[str, int] = {}` ke `__init__`
    - _Requirements: 9.1, 9.2, 9.3, 8.1, 8.2, 12.1_
  - [x] 8.2 Implementasikan method `_generate_sideways_signal()` di `ScalpingEngine`
    - Validasi minimum candle: 30 candle 5M, 50 candle 15M, field `open/high/low/close/volume` ada
    - Panggil `RangeAnalyzer().analyze()` → return `None` jika gagal
    - Panggil `BounceDetector().detect()` → return `None` jika tidak ada bounce
    - Panggil `RSIDivergenceDetector().detect()` → lanjut tanpa bonus jika exception
    - Hitung confidence: base 70 + divergence bonus + volume bonus (>1.5x avg = +5) + range bonus (1.0-2.0% = +5), cap di 95
    - Hitung TP: LONG = `entry + 0.70 * (resistance - entry)`, SHORT = `entry - 0.70 * (entry - support)`
    - Hitung SL: LONG = `support * (1 - 0.0015)`, SHORT = `resistance * (1 + 0.0015)`
    - Hitung RR ratio, return `None` jika RR < 1.0 atau confidence < 75
    - Bungkus setiap komponen dalam try-except; increment `sideways_error_counter`; cooldown 5 menit jika counter >= 3
    - Return `MicroScalpSignal`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 9.4, 9.5, 9.6, 9.7, 12.2, 12.3, 12.4, 12.5, 12.6_
  - [ ]* 8.3 Tulis property test untuk kalkulasi TP — Property 8: Kalkulasi TP Sideways
    - **Property 8: Kalkulasi TP Sideways**
    - **Validates: Requirements 5.1, 5.2**
    - LONG: `tp == entry + 0.70 * (resistance - entry)`; SHORT: `tp == entry - 0.70 * (entry - support)`
  - [ ]* 8.4 Tulis property test untuk kalkulasi SL — Property 9: Kalkulasi SL Sideways
    - **Property 9: Kalkulasi SL Sideways**
    - **Validates: Requirements 5.3, 5.4**
    - LONG: `sl == support * (1 - 0.0015)`; SHORT: `sl == resistance * (1 + 0.0015)`
  - [ ]* 8.5 Tulis property test untuk penolakan sinyal RR < 1.0 — Property 10: Penolakan Sinyal dengan R:R < 1.0
    - **Property 10: Penolakan Sinyal dengan R:R < 1.0**
    - **Validates: Requirements 5.6**
    - Sinyal dengan `rr_ratio < 1.0` harus return `None`
  - [ ]* 8.6 Tulis property test untuk confidence cap — Property 11: Confidence Score Tidak Melebihi 95
    - **Property 11: Confidence Score Tidak Melebihi 95**
    - **Validates: Requirements 6.5**
    - Semua kombinasi bonus → `confidence <= 95`
  - [ ]* 8.7 Tulis property test untuk penolakan confidence < 75 — Property 12: Penolakan Sinyal dengan Confidence < 75
    - **Property 12: Penolakan Sinyal dengan Confidence < 75**
    - **Validates: Requirements 6.6**
    - Sinyal dengan `confidence < 75` harus return `None`

- [x] 9. Implementasi max hold timer 2 menit
  - [x] 9.1 Modifikasi `monitor_positions()` di `Bismillah/app/scalping_engine.py`
    - Tambahkan pengecekan `getattr(position, 'is_sideways', False)` di awal loop per posisi
    - Jika sideways: hitung `elapsed = time.time() - position.opened_at`; jika `elapsed > 120` panggil `_close_sideways_max_hold()`
    - Jika tidak sideways: gunakan logika max hold trending 30 menit yang sudah ada (tidak berubah)
    - _Requirements: 7.1, 7.2, 7.3, 7.7_
  - [x] 9.2 Implementasikan method `_close_sideways_max_hold()` di `ScalpingEngine`
    - Tutup posisi dengan market order
    - Hitung PnL final
    - Update database: `close_reason = "sideways_max_hold_exceeded"`, `close_price`, `closed_at`, `pnl_usdt`
    - Kirim notifikasi dengan label `"⏰ SIDEWAYS Closed (2min)"`
    - Hapus posisi dari `self.positions`
    - _Requirements: 7.3, 7.4, 7.5, 7.6_
  - [ ]* 9.3 Tulis property test untuk max hold timer — Property 13: Max Hold Timer Sideways
    - **Property 13: Max Hold Timer Sideways**
    - **Validates: Requirements 7.3, 7.4**
    - Posisi sideways dengan elapsed > 120 detik harus ditutup dengan `close_reason = "sideways_max_hold_exceeded"`
  - [ ]* 9.4 Tulis property test untuk isolasi timer — Property 14: Isolasi Timer Sideways dari Trending
    - **Property 14: Isolasi Timer Sideways dari Trending**
    - **Validates: Requirements 7.7**
    - Timer 120 detik tidak mempengaruhi posisi trending (`is_sideways = False`)

- [x] 10. Implementasi notifikasi trade sideways
  - [x] 10.1 Implementasikan method `_notify_sideways_opened()` di `ScalpingEngine`
    - Label: `"⚡ SIDEWAYS SCALP"`
    - Cantumkan: simbol, arah, entry, TP, SL, R:R, confidence, range_support, range_resistance, max hold time (2 menit), reasons
    - _Requirements: 10.1, 10.2, 10.6_
  - [x] 10.2 Implementasikan method `_notify_sideways_closed()` di `ScalpingEngine`
    - TP hit: label `"✅ SIDEWAYS TP Hit"` + PnL
    - SL hit: label `"🛑 SIDEWAYS SL Hit"` + PnL
    - Max hold: label `"⏰ SIDEWAYS Closed (2min)"` + PnL final
    - _Requirements: 10.3, 10.4, 10.5_
  - [x] 10.3 Modifikasi `place_scalping_order()` untuk menangani `MicroScalpSignal`
    - Deteksi tipe sinyal: jika `isinstance(signal, MicroScalpSignal)` gunakan notifikasi sideways
    - Set `position.is_sideways = True` saat membuat `ScalpingPosition`
    - Simpan field sideways ke database saat insert: `trade_subtype`, `range_support`, `range_resistance`, `range_width_pct`, `bounce_confirmed`, `rsi_divergence_detected`, `max_hold_time`
    - _Requirements: 8.5, 10.1, 11.1, 11.2, 11.4, 11.5_

- [x] 11. Checkpoint — Pastikan integrasi engine berfungsi
  - Pastikan semua tests pass, tanyakan ke user jika ada pertanyaan.

- [x] 12. Isolasi mode — pastikan sideways tidak aktif di Swing Mode
  - [x] 12.1 Tambahkan guard di `generate_scalping_signal()` untuk cek `trading_mode`
    - Jika mode bukan `"scalping"`, skip pemanggilan `SidewaysDetector` sepenuhnya
    - _Requirements: 8.1, 8.2, 8.3_
  - [x] 12.2 Modifikasi `TradingModeManager.switch_mode()` di `Bismillah/app/trading_mode_manager.py`
    - Sebelum stop engine, tutup semua posisi sideways yang masih terbuka jika switch dari scalping ke swing
    - _Requirements: 8.4_
  - [ ]* 12.3 Tulis property test untuk isolasi mode — Property 16: Isolasi Mode
    - **Property 16: Isolasi Mode — Sideways Hanya Aktif di Mode Scalping**
    - **Validates: Requirements 8.1, 8.2**
    - Dengan `trading_mode = "swing"`, tidak ada komponen sideways yang dipanggil

- [x] 13. Penyimpanan metadata trade sideways ke database
  - [x] 13.1 Modifikasi `_save_position_to_db()` di `ScalpingEngine` untuk menyimpan field sideways
    - Jika `position.is_sideways = True`: tambahkan field `trade_subtype = "sideways_scalp"`, `trade_type = "scalping"`, `timeframe = "5m"`, `max_hold_time = 120`, `range_support`, `range_resistance`, `range_width_pct`, `bounce_confirmed = True`, `rsi_divergence_detected`
    - Bungkus dalam try-except: log error, lanjutkan tanpa menghentikan engine
    - _Requirements: 11.1, 11.2, 11.4, 11.5_
  - [x] 13.2 Modifikasi method close position untuk update field sideways saat tutup
    - Update `close_price`, `pnl_usdt`, `close_reason`, `closed_at` saat posisi sideways ditutup
    - _Requirements: 11.3_
  - [ ]* 13.3 Tulis property test untuk metadata trade — Property 15: Metadata Trade Sideways Lengkap
    - **Property 15: Metadata Trade Sideways Lengkap**
    - **Validates: Requirements 8.5, 11.1, 11.2**
    - Record sideways harus memiliki `trade_subtype = "sideways_scalp"` dan semua field wajib terisi

- [ ] 14. Tulis integration tests di `Bismillah/tests/test_sideways_integration.py`
  - [ ]* 14.1 Test end-to-end: `generate_scalping_signal()` memanggil pipeline sideways saat market sideways
    - Mock `SidewaysDetector` return `is_sideways = True`
    - Verifikasi `RangeAnalyzer`, `BounceDetector`, `RSIDivergenceDetector` dipanggil berurutan
    - _Requirements: 9.1, 9.3_
  - [ ]* 14.2 Test end-to-end: `generate_scalping_signal()` skip pipeline sideways saat market trending
    - Mock `SidewaysDetector` return `is_sideways = False`
    - Verifikasi komponen sideways tidak dipanggil
    - _Requirements: 9.2_
  - [ ]* 14.3 Test graceful degradation: exception di `RangeAnalyzer` return `None` tanpa crash
    - _Requirements: 12.2, 12.5_
  - [ ]* 14.4 Test graceful degradation: exception di `RSIDivergenceDetector` lanjut tanpa bonus confidence
    - _Requirements: 12.4_
  - [ ]* 14.5 Test error counter: 3 error berturut-turut pada simbol yang sama → cooldown 5 menit
    - _Requirements: 12.6_

- [x] 15. Final checkpoint — Pastikan semua tests pass
  - Pastikan semua tests pass, tanyakan ke user jika ada pertanyaan.

## Catatan

- Task bertanda `*` bersifat opsional dan dapat dilewati untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk traceability
- Urutan implementasi mengikuti dependency: data models → komponen analisis → integrasi engine → notifikasi → database
- Property tests menggunakan library `hypothesis` dengan minimal 100 iterasi (`@settings(max_examples=100)`)
- Logika trending yang sudah ada di `scalping_engine.py` tidak boleh diubah sama sekali
