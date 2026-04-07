# Dokumen Requirements: Sideways Micro-Scalping

## Pendahuluan

Fitur ini memperluas kemampuan Scalping Engine (`scalping_engine.py`) agar tetap dapat melakukan trading ketika market sedang dalam kondisi sideways/ranging — bukan skip seperti perilaku saat ini.

Saat ini, `autosignal_async.py` hanya menghasilkan sinyal berkualitas tinggi ketika 15M trend berstatus `STRONG`. Ketika market ranging (`NEUTRAL`, `WEAK`), sinyal yang dihasilkan menggunakan logika yang lebih longgar tanpa validasi Support/Resistance yang solid, sehingga berisiko menghasilkan trade sembarangan.

Fitur Sideways Micro-Scalping menambahkan lapisan analisis khusus untuk kondisi ranging: deteksi range S/R yang jelas, konfirmasi bounce signal, dan RSI divergence — layaknya analisis pro trader. Hold time maksimal 2 menit (bukan 30 menit seperti trending mode) dengan SL ketat di luar range dan R:R minimal 1:1.

Fitur ini **hanya aktif di mode Scalping (5M)**. Mode Swing (15M) tidak terpengaruh sama sekali.

---

## Glosarium

- **Scalping_Engine**: Modul `scalping_engine.py` yang menjalankan trading frekuensi tinggi pada timeframe 5M
- **Sideways_Detector**: Komponen baru yang mendeteksi kondisi market sideways/ranging berdasarkan ATR relatif dan EMA spread
- **Range_Analyzer**: Komponen baru yang mengidentifikasi batas atas (resistance) dan batas bawah (support) dari range harga
- **Bounce_Detector**: Komponen baru yang mendeteksi sinyal pantulan harga dari level S/R
- **RSI_Divergence_Detector**: Komponen baru yang mendeteksi divergensi antara pergerakan harga dan RSI
- **Micro_Scalp_Signal**: Objek sinyal khusus untuk trading di kondisi sideways, berbeda dari `ScalpingSignal` trending
- **Range_Support**: Level harga terendah yang valid dalam range sideways (minimal 2 kali diuji)
- **Range_Resistance**: Level harga tertinggi yang valid dalam range sideways (minimal 2 kali diuji)
- **Bounce_Signal**: Konfirmasi bahwa harga sedang memantul dari level S/R (bukan menembus)
- **RSI_Divergence**: Kondisi di mana arah harga dan arah RSI berlawanan, mengindikasikan potensi reversal
- **Max_Hold_Sideways**: Batas waktu maksimal posisi sideways terbuka, ditetapkan 2 menit (120 detik)
- **ATR_Relative**: Persentase ATR terhadap harga saat ini, digunakan untuk mengukur volatilitas relatif
- **Range_Width**: Jarak antara Range_Resistance dan Range_Support dalam persentase harga
- **Signal_Generator**: Modul `autosignal_async.py` yang menghasilkan sinyal trading
- **Circuit_Breaker**: Sistem risk management yang menghentikan trading setelah mencapai batas kerugian harian
- **Cooldown_Tracker**: Sistem pelacak waktu jeda antar trade pada simbol yang sama

---

## Requirements

### Requirement 1: Deteksi Kondisi Market Sideways

**User Story:** Sebagai trader, saya ingin engine scalping dapat mendeteksi secara akurat kapan market sedang sideways/ranging, agar analisis yang digunakan sesuai dengan kondisi market yang sebenarnya.

#### Acceptance Criteria

1. WHEN `Scalping_Engine` memproses sinyal untuk suatu simbol, THE `Sideways_Detector` SHALL menentukan apakah kondisi market adalah trending atau sideways
2. THE `Sideways_Detector` SHALL mengklasifikasikan market sebagai sideways WHEN ATR_Relative pada timeframe 5M berada di bawah 0.3% dari harga saat ini
3. THE `Sideways_Detector` SHALL mengklasifikasikan market sebagai sideways WHEN spread antara EMA21 dan EMA50 pada timeframe 15M berada di bawah 0.2% dari harga saat ini
4. THE `Sideways_Detector` SHALL mengklasifikasikan market sebagai sideways WHEN harga bergerak dalam kisaran kurang dari 1.5% selama 20 candle terakhir pada timeframe 5M
5. IF salah satu dari tiga kondisi di atas terpenuhi, THEN THE `Sideways_Detector` SHALL mengembalikan status `SIDEWAYS`
6. IF tidak ada kondisi sideways yang terpenuhi, THEN THE `Sideways_Detector` SHALL mengembalikan status `TRENDING` dan `Scalping_Engine` SHALL menggunakan logika sinyal trending yang sudah ada
7. THE `Sideways_Detector` SHALL mencatat hasil klasifikasi beserta nilai ATR_Relative, EMA_Spread, dan Range_Width ke dalam log untuk setiap simbol yang diproses

---

### Requirement 2: Identifikasi Range Support dan Resistance

**User Story:** Sebagai trader, saya ingin engine dapat mengidentifikasi level support dan resistance yang valid dalam range sideways, agar trade hanya dilakukan di level harga yang memiliki konfirmasi historis yang kuat.

#### Acceptance Criteria

1. WHEN `Sideways_Detector` mengembalikan status `SIDEWAYS`, THE `Range_Analyzer` SHALL mengidentifikasi Range_Support dan Range_Resistance dari 30 candle terakhir pada timeframe 5M
2. THE `Range_Analyzer` SHALL menetapkan Range_Resistance sebagai level harga yang telah diuji (touched atau rejected) minimal 2 kali dalam 30 candle terakhir
3. THE `Range_Analyzer` SHALL menetapkan Range_Support sebagai level harga yang telah diuji (touched atau rejected) minimal 2 kali dalam 30 candle terakhir
4. THE `Range_Analyzer` SHALL menggunakan toleransi 0.15% untuk mengelompokkan level harga yang berdekatan sebagai satu level S/R yang sama
5. IF `Range_Analyzer` tidak dapat menemukan Range_Support atau Range_Resistance yang valid, THEN THE `Scalping_Engine` SHALL skip simbol tersebut dan tidak menghasilkan sinyal sideways
6. THE `Range_Analyzer` SHALL menghitung Range_Width sebagai persentase jarak antara Range_Resistance dan Range_Support terhadap harga saat ini
7. IF Range_Width kurang dari 0.5%, THEN THE `Scalping_Engine` SHALL skip simbol tersebut karena range terlalu sempit untuk menghasilkan R:R yang layak
8. IF Range_Width lebih dari 3.0%, THEN THE `Scalping_Engine` SHALL skip simbol tersebut karena range terlalu lebar dan tidak terklasifikasi sebagai sideways yang valid

---

### Requirement 3: Deteksi Bounce Signal dari Level S/R

**User Story:** Sebagai trader, saya ingin engine hanya masuk trade ketika ada konfirmasi bounce yang jelas dari level S/R, bukan saat harga sedang dalam perjalanan menuju S/R, agar entry price lebih optimal dan risiko breakout diminimalkan.

#### Acceptance Criteria

1. WHEN `Range_Analyzer` berhasil mengidentifikasi Range_Support dan Range_Resistance, THE `Bounce_Detector` SHALL mengevaluasi apakah harga saat ini sedang memantul dari salah satu level tersebut
2. THE `Bounce_Detector` SHALL mengkonfirmasi bounce dari Range_Support WHEN harga saat ini berada dalam jarak 0.2% dari Range_Support DAN candle 5M terakhir menunjukkan lower wick yang lebih panjang dari body candle
3. THE `Bounce_Detector` SHALL mengkonfirmasi bounce dari Range_Resistance WHEN harga saat ini berada dalam jarak 0.2% dari Range_Resistance DAN candle 5M terakhir menunjukkan upper wick yang lebih panjang dari body candle
4. WHEN bounce dari Range_Support terkonfirmasi, THE `Bounce_Detector` SHALL menghasilkan sinyal arah LONG
5. WHEN bounce dari Range_Resistance terkonfirmasi, THE `Bounce_Detector` SHALL menghasilkan sinyal arah SHORT
6. IF tidak ada bounce yang terkonfirmasi dari kedua level, THEN THE `Scalping_Engine` SHALL skip simbol tersebut pada siklus scan ini
7. THE `Bounce_Detector` SHALL menambahkan alasan bounce ke dalam daftar `reasons` pada `Micro_Scalp_Signal` yang dihasilkan

---

### Requirement 4: Validasi RSI Divergence

**User Story:** Sebagai trader, saya ingin engine memvalidasi sinyal bounce dengan RSI divergence, agar hanya trade dengan probabilitas reversal yang lebih tinggi yang dieksekusi.

#### Acceptance Criteria

1. WHEN `Bounce_Detector` mengkonfirmasi bounce signal, THE `RSI_Divergence_Detector` SHALL mengevaluasi keberadaan RSI divergence pada timeframe 5M
2. THE `RSI_Divergence_Detector` SHALL mendeteksi bullish divergence WHEN harga membentuk lower low baru TETAPI RSI membentuk higher low dalam 10 candle terakhir pada timeframe 5M
3. THE `RSI_Divergence_Detector` SHALL mendeteksi bearish divergence WHEN harga membentuk higher high baru TETAPI RSI membentuk lower high dalam 10 candle terakhir pada timeframe 5M
4. WHEN bullish divergence terdeteksi pada sinyal LONG, THE `RSI_Divergence_Detector` SHALL menambahkan 10 poin ke confidence score `Micro_Scalp_Signal`
5. WHEN bearish divergence terdeteksi pada sinyal SHORT, THE `RSI_Divergence_Detector` SHALL menambahkan 10 poin ke confidence score `Micro_Scalp_Signal`
6. IF tidak ada RSI divergence yang terdeteksi, THE `Scalping_Engine` SHALL tetap memproses sinyal dengan confidence score dasar tanpa penambahan poin divergence
7. THE `RSI_Divergence_Detector` SHALL mencatat hasil evaluasi divergence (detected/not detected) ke dalam `reasons` pada `Micro_Scalp_Signal`

---

### Requirement 5: Kalkulasi TP dan SL untuk Sideways Trade

**User Story:** Sebagai trader, saya ingin TP dan SL dihitung berdasarkan batas range yang teridentifikasi, agar setiap trade memiliki target yang logis dan SL yang ketat di luar range.

#### Acceptance Criteria

1. WHEN `Micro_Scalp_Signal` dengan arah LONG dihasilkan dari bounce di Range_Support, THE `Scalping_Engine` SHALL menetapkan TP di 70% jarak menuju Range_Resistance dari entry price
2. WHEN `Micro_Scalp_Signal` dengan arah SHORT dihasilkan dari bounce di Range_Resistance, THE `Scalping_Engine` SHALL menetapkan TP di 70% jarak menuju Range_Support dari entry price
3. WHEN `Micro_Scalp_Signal` dengan arah LONG dihasilkan, THE `Scalping_Engine` SHALL menetapkan SL di bawah Range_Support sebesar 0.15% dari Range_Support
4. WHEN `Micro_Scalp_Signal` dengan arah SHORT dihasilkan, THE `Scalping_Engine` SHALL menetapkan SL di atas Range_Resistance sebesar 0.15% dari Range_Resistance
5. THE `Scalping_Engine` SHALL menghitung R:R ratio dari setiap `Micro_Scalp_Signal` sebelum validasi
6. IF R:R ratio kurang dari 1.0, THEN THE `Scalping_Engine` SHALL menolak sinyal tersebut dan tidak mengeksekusi trade
7. THE `Scalping_Engine` SHALL mencatat nilai TP, SL, dan R:R ratio ke dalam log untuk setiap `Micro_Scalp_Signal` yang dievaluasi

---

### Requirement 6: Validasi Confidence Score Sideways Signal

**User Story:** Sebagai trader, saya ingin hanya sinyal sideways dengan confidence yang cukup tinggi yang dieksekusi, agar kualitas trade tetap terjaga meskipun kondisi market tidak trending.

#### Acceptance Criteria

1. THE `Scalping_Engine` SHALL menetapkan confidence score dasar sebesar 70 untuk setiap `Micro_Scalp_Signal` yang melewati validasi Range_Analyzer dan Bounce_Detector
2. WHEN RSI divergence terdeteksi, THE `RSI_Divergence_Detector` SHALL menambahkan 10 poin ke confidence score (total maksimal dari divergence: 10 poin)
3. WHEN volume pada candle bounce melebihi 1.5x rata-rata volume 20 candle terakhir, THE `Scalping_Engine` SHALL menambahkan 5 poin ke confidence score
4. WHEN Range_Width berada antara 1.0% dan 2.0% (range ideal), THE `Scalping_Engine` SHALL menambahkan 5 poin ke confidence score
5. THE `Scalping_Engine` SHALL membatasi confidence score maksimal pada 95
6. IF confidence score akhir kurang dari 75, THEN THE `Scalping_Engine` SHALL menolak sinyal dan tidak mengeksekusi trade
7. THE `Scalping_Engine` SHALL mencatat breakdown confidence score (base + divergence bonus + volume bonus + range bonus) ke dalam log

---

### Requirement 7: Batas Waktu Hold Maksimal 2 Menit

**User Story:** Sebagai trader, saya ingin posisi sideways otomatis ditutup setelah 2 menit, agar tidak ada posisi sideways yang tertahan terlalu lama dan mengekspos balance ke risiko yang tidak perlu.

#### Acceptance Criteria

1. WHEN `Scalping_Engine` membuka posisi dari `Micro_Scalp_Signal`, THE `Scalping_Engine` SHALL mencatat timestamp pembukaan posisi
2. WHILE posisi sideways terbuka, THE `Scalping_Engine` SHALL memonitor elapsed time pada setiap siklus scan (setiap 15 detik)
3. WHEN elapsed time posisi sideways melebihi 120 detik (2 menit), THE `Scalping_Engine` SHALL menutup posisi tersebut dengan market order
4. WHEN posisi ditutup karena Max_Hold_Sideways, THE `Scalping_Engine` SHALL mencatat `close_reason` sebagai `"sideways_max_hold_exceeded"` di database
5. WHEN posisi ditutup karena Max_Hold_Sideways, THE `Scalping_Engine` SHALL menghitung dan mencatat PnL final
6. WHEN posisi ditutup karena Max_Hold_Sideways, THE `Scalping_Engine` SHALL mengirimkan notifikasi ke user dengan informasi simbol, entry price, exit price, hold time, dan PnL
7. THE `Scalping_Engine` SHALL memproses Max_Hold_Sideways secara terpisah dari Max_Hold_Time trending (30 menit) agar tidak saling mengganggu

---

### Requirement 8: Isolasi dari Mode Swing

**User Story:** Sebagai trader, saya ingin fitur sideways micro-scalping hanya aktif di mode Scalping, agar mode Swing tidak terpengaruh dan tetap berjalan dengan logika aslinya.

#### Acceptance Criteria

1. THE `Sideways_Detector` SHALL hanya diaktifkan WHEN `trading_mode` user di database bernilai `"scalping"`
2. WHILE user menggunakan mode Swing (15M), THE `Scalping_Engine` SHALL tidak menjalankan `Sideways_Detector`, `Range_Analyzer`, `Bounce_Detector`, maupun `RSI_Divergence_Detector`
3. THE `Scalping_Engine` SHALL tidak mengubah logika atau parameter apapun pada Swing Mode sebagai dampak dari implementasi fitur ini
4. WHEN user beralih dari mode Scalping ke mode Swing, THE `Scalping_Engine` SHALL menutup semua posisi sideways yang masih terbuka sebelum engine Swing dimulai
5. THE `Scalping_Engine` SHALL menandai semua trade yang berasal dari sideways micro-scalping dengan `trade_subtype = "sideways_scalp"` di database untuk membedakannya dari trade trending scalping

---

### Requirement 9: Integrasi dengan Scalping Engine yang Ada

**User Story:** Sebagai developer, saya ingin logika sideways micro-scalping terintegrasi dengan mulus ke dalam `ScalpingEngine` yang sudah ada, agar tidak ada duplikasi kode dan sistem tetap maintainable.

#### Acceptance Criteria

1. THE `Scalping_Engine` SHALL memanggil `Sideways_Detector` di dalam method `generate_scalping_signal()` setelah mendapatkan data klines, sebelum mengembalikan sinyal
2. WHEN `Sideways_Detector` mengembalikan status `TRENDING`, THE `Scalping_Engine` SHALL melanjutkan ke logika sinyal trending yang sudah ada tanpa perubahan
3. WHEN `Sideways_Detector` mengembalikan status `SIDEWAYS`, THE `Scalping_Engine` SHALL memanggil `Range_Analyzer`, `Bounce_Detector`, dan `RSI_Divergence_Detector` secara berurutan
4. THE `Scalping_Engine` SHALL menggunakan `ScalpingConfig` yang sudah ada untuk parameter seperti `min_confidence`, `max_concurrent_positions`, dan `cooldown_seconds`
5. THE `Scalping_Engine` SHALL menerapkan `Circuit_Breaker` yang sama untuk trade sideways maupun trending
6. THE `Scalping_Engine` SHALL menerapkan `Cooldown_Tracker` yang sama untuk trade sideways maupun trending pada simbol yang sama
7. THE `Scalping_Engine` SHALL menerapkan filter waktu trading optimal (`is_optimal_trading_time`) yang sama untuk trade sideways

---

### Requirement 10: Notifikasi Trade Sideways

**User Story:** Sebagai trader, saya ingin menerima notifikasi yang jelas ketika engine membuka atau menutup posisi sideways, agar saya dapat membedakan trade sideways dari trade trending.

#### Acceptance Criteria

1. WHEN posisi sideways dibuka, THE `Scalping_Engine` SHALL mengirimkan notifikasi Telegram dengan label `"⚡ SIDEWAYS SCALP"` yang berbeda dari label trending `"⚡ SCALP"`
2. THE notifikasi pembukaan posisi sideways SHALL mencantumkan: simbol, arah (LONG/SHORT), entry price, TP, SL, R:R ratio, confidence score, Range_Support, Range_Resistance, dan max hold time (2 menit)
3. WHEN posisi sideways ditutup karena TP hit, THE `Scalping_Engine` SHALL mengirimkan notifikasi dengan label `"✅ SIDEWAYS TP Hit"` beserta PnL
4. WHEN posisi sideways ditutup karena SL hit, THE `Scalping_Engine` SHALL mengirimkan notifikasi dengan label `"🛑 SIDEWAYS SL Hit"` beserta PnL
5. WHEN posisi sideways ditutup karena Max_Hold_Sideways, THE `Scalping_Engine` SHALL mengirimkan notifikasi dengan label `"⏰ SIDEWAYS Closed (2min)"` beserta PnL final
6. THE `Scalping_Engine` SHALL menyertakan alasan-alasan sinyal (`reasons`) dalam notifikasi pembukaan posisi sideways

---

### Requirement 11: Penyimpanan Data Trade Sideways di Database

**User Story:** Sebagai developer, saya ingin trade sideways tersimpan dengan metadata yang lengkap di database, agar performa strategi sideways dapat dianalisis secara terpisah dari strategi trending.

#### Acceptance Criteria

1. WHEN posisi sideways dibuka, THE `Scalping_Engine` SHALL menyimpan record ke tabel `autotrade_trades` dengan `trade_type = "scalping"` dan `trade_subtype = "sideways_scalp"`
2. THE record trade sideways SHALL menyimpan field: `range_support`, `range_resistance`, `range_width_pct`, `bounce_confirmed`, `rsi_divergence_detected`, `max_hold_time = 120`
3. WHEN posisi sideways ditutup, THE `Scalping_Engine` SHALL memperbarui record dengan `close_price`, `pnl_usdt`, `close_reason`, dan `closed_at`
4. THE `Scalping_Engine` SHALL menyimpan `confidence` score final pada saat trade dibuka
5. IF penyimpanan ke database gagal, THEN THE `Scalping_Engine` SHALL mencatat error ke log dan melanjutkan operasi tanpa menghentikan engine

---

### Requirement 12: Penanganan Error pada Sideways Analysis

**User Story:** Sebagai developer, saya ingin error pada analisis sideways ditangani dengan graceful, agar kegagalan analisis sideways tidak menghentikan engine scalping secara keseluruhan.

#### Acceptance Criteria

1. IF `Sideways_Detector` mengalami exception, THEN THE `Scalping_Engine` SHALL mencatat error ke log, skip simbol tersebut, dan melanjutkan ke simbol berikutnya
2. IF `Range_Analyzer` mengalami exception, THEN THE `Scalping_Engine` SHALL mencatat error ke log dan mengembalikan `None` (tidak ada sinyal)
3. IF `Bounce_Detector` mengalami exception, THEN THE `Scalping_Engine` SHALL mencatat error ke log dan mengembalikan `None`
4. IF `RSI_Divergence_Detector` mengalami exception, THEN THE `Scalping_Engine` SHALL mencatat error ke log dan melanjutkan tanpa bonus divergence (tidak menolak sinyal)
5. THE `Scalping_Engine` SHALL tidak mengizinkan error pada komponen sideways untuk menyebabkan crash pada main trading loop
6. WHEN terjadi 3 error berturut-turut pada analisis sideways untuk simbol yang sama dalam satu siklus scan, THE `Scalping_Engine` SHALL memasukkan simbol tersebut ke dalam cooldown selama 5 menit
