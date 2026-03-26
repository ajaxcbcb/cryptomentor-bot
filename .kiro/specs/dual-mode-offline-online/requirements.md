# Requirements Document

## Introduction

Fitur dual-mode untuk bot Telegram CryptoMentor yang memisahkan dengan jelas antara mode offline (manual trading dengan Binance API) dan mode online (AI agent trading dengan Automaton). Fitur ini dirancang untuk memberikan pengalaman pengguna yang intuitif dengan transisi yang smooth antara kedua mode, serta alur deposit dan credit management yang terstruktur.

## Glossary

- **Bot**: Sistem bot Telegram CryptoMentor
- **User**: Pengguna bot Telegram
- **Admin**: Administrator yang mengelola credit dan registrasi agent
- **Offline_Mode**: Mode operasi manual trading menggunakan Binance API tanpa LLM
- **Online_Mode**: Mode operasi AI agent trading menggunakan Automaton dengan LLM
- **Automaton_Credits**: Credit yang digunakan untuk mengakses dan berinteraksi dengan AI agent
- **AI_Agent**: Instance Automaton pribadi yang isolated untuk setiap user
- **Session**: Window atau context khusus untuk interaksi dengan Automaton
- **Genesis_Prompt**: Prompt pusat yang dipasang di Automaton untuk trading otomatis
- **Manual_Trading**: Fitur trading manual seperti analisis teknikal dan sinyal futures
- **Isolated_Agent**: AI agent yang terpisah dan independen untuk setiap user

## Requirements

### Requirement 1: Mode Switching

**User Story:** Sebagai user, saya ingin dapat beralih antara mode offline dan online dengan mudah, sehingga saya dapat memilih antara manual trading atau AI agent trading sesuai kebutuhan.

#### Acceptance Criteria

1. THE Bot SHALL menyediakan command /offline untuk mengaktifkan Offline_Mode
2. THE Bot SHALL menyediakan command /online untuk mengaktifkan Online_Mode
3. WHEN User mengetik /offline, THE Bot SHALL mengaktifkan Offline_Mode dan menampilkan menu manual trading
4. WHEN User mengetik /online, THE Bot SHALL memeriksa Automaton_Credits User
5. IF User memiliki Automaton_Credits yang cukup, THEN THE Bot SHALL mengaktifkan Online_Mode dan membuat Session baru
6. IF User tidak memiliki Automaton_Credits yang cukup, THEN THE Bot SHALL menampilkan pesan informasi cara mendapatkan credits
7. THE Bot SHALL menyimpan status mode aktif User di database
8. WHEN User beralih mode, THE Bot SHALL menampilkan konfirmasi mode yang aktif dengan UI yang jelas

### Requirement 2: Offline Mode Features

**User Story:** Sebagai user di mode offline, saya ingin menggunakan fitur manual trading yang sudah ada, sehingga saya dapat melakukan analisis teknikal dan mendapatkan sinyal trading tanpa menggunakan LLM.

#### Acceptance Criteria

1. WHILE User berada di Offline_Mode, THE Bot SHALL menyediakan akses ke fitur analisis teknikal
2. WHILE User berada di Offline_Mode, THE Bot SHALL menyediakan akses ke sinyal futures
3. WHILE User berada di Offline_Mode, THE Bot SHALL menggunakan Binance API untuk data market
4. WHILE User berada di Offline_Mode, THE Bot SHALL tidak menggunakan LLM untuk processing
5. THE Bot SHALL menampilkan menu Offline_Mode dengan opsi: analisis teknikal, sinyal futures, dan kembali ke menu utama
6. WHEN User mengetik manual di Offline_Mode, THE Bot SHALL memproses request untuk sinyal trading
7. THE Bot SHALL memformat response Offline_Mode dengan style yang konsisten dan mudah dibaca

### Requirement 3: Online Mode Features

**User Story:** Sebagai user di mode online, saya ingin berinteraksi dengan AI agent Automaton pribadi saya, sehingga saya dapat mendapatkan sinyal trading otomatis atau berdiskusi tentang strategi trading.

#### Acceptance Criteria

1. WHEN User mengaktifkan Online_Mode, THE Bot SHALL membuat Session baru yang isolated untuk User
2. WHEN User mengaktifkan Online_Mode, THE Bot SHALL menginisialisasi AI_Agent pribadi User
3. WHILE User berada di Online_Mode, THE Bot SHALL meneruskan semua pesan User ke AI_Agent mereka
4. WHILE User berada di Online_Mode, THE AI_Agent SHALL menggunakan Genesis_Prompt sebagai context dasar
5. THE AI_Agent SHALL dapat memberikan sinyal trading otomatis berdasarkan request User
6. THE AI_Agent SHALL dapat melakukan percakapan natural dengan User tentang trading
7. THE Bot SHALL memastikan setiap User memiliki Isolated_Agent yang tidak tercampur dengan user lain
8. WHEN User mengirim pesan di Online_Mode, THE Bot SHALL mengurangi Automaton_Credits sesuai usage
9. THE Bot SHALL menampilkan sisa Automaton_Credits User setelah setiap interaksi

### Requirement 4: Credit Management System

**User Story:** Sebagai user, saya ingin memahami sistem credit dengan jelas, sehingga saya tahu bagaimana cara mendapatkan dan menggunakan Automaton_Credits.

#### Acceptance Criteria

1. THE Bot SHALL menyediakan command /credits untuk melihat saldo Automaton_Credits
2. WHEN User mengetik /credits, THE Bot SHALL menampilkan saldo Automaton_Credits User saat ini
3. THE Bot SHALL menampilkan informasi cara mendapatkan Automaton_Credits melalui deposit
4. THE Bot SHALL menyimpan transaksi Automaton_Credits di database dengan timestamp
5. WHEN Automaton_Credits User habis di Online_Mode, THE Bot SHALL menampilkan notifikasi dan cara top-up
6. THE Bot SHALL mencatat setiap penggunaan Automaton_Credits dengan detail aktivitas

### Requirement 5: Initial Deposit Flow

**User Story:** Sebagai user baru, saya ingin melakukan deposit awal melalui admin untuk mendapatkan Automaton_Credits, sehingga saya dapat mengakses mode online.

#### Acceptance Criteria

1. WHEN User baru ingin akses Online_Mode, THE Bot SHALL menampilkan instruksi untuk deposit melalui Admin
2. THE Bot SHALL menyediakan informasi kontak Admin untuk proses deposit
3. WHEN Admin memproses deposit awal, THE Admin SHALL dapat memberikan Automaton_Credits ke User
4. THE Bot SHALL mengirim notifikasi ke User ketika Automaton_Credits berhasil ditambahkan
5. THE Bot SHALL mencatat deposit awal di audit log dengan detail User dan jumlah credits
6. WHEN deposit awal berhasil, THE Bot SHALL secara otomatis mengarahkan User ke Online_Mode

### Requirement 6: Admin Credit Management

**User Story:** Sebagai admin, saya ingin dapat mengelola Automaton_Credits user dengan mudah, sehingga saya dapat memproses deposit awal dan registrasi agent dengan efisien.

#### Acceptance Criteria

1. THE Bot SHALL menyediakan command /admin untuk Admin mengakses menu administrasi
2. WHILE Admin berada di menu admin, THE Bot SHALL menampilkan opsi: tambah credits, lihat user, dan registrasi agent
3. WHEN Admin memilih tambah credits, THE Bot SHALL meminta User ID dan jumlah Automaton_Credits
4. WHEN Admin memasukkan User ID dan jumlah, THE Bot SHALL menambahkan Automaton_Credits ke User tersebut
5. THE Bot SHALL mengirim konfirmasi ke Admin setelah credits berhasil ditambahkan
6. THE Bot SHALL mengirim notifikasi ke User yang menerima credits
7. THE Bot SHALL mencatat semua aktivitas Admin di audit log
8. IF Admin memasukkan User ID yang tidak valid, THEN THE Bot SHALL menampilkan pesan error yang jelas

### Requirement 7: Subsequent Deposit and Withdrawal via AI

**User Story:** Sebagai user yang sudah memiliki AI agent, saya ingin dapat melakukan deposit atau withdrawal selanjutnya dengan berbicara langsung ke AI di mode online, sehingga prosesnya lebih mudah dan tidak perlu melalui admin lagi.

#### Acceptance Criteria

1. WHILE User berada di Online_Mode, THE AI_Agent SHALL dapat memproses request deposit dari User
2. WHILE User berada di Online_Mode, THE AI_Agent SHALL dapat memproses request withdrawal dari User
3. WHEN User meminta deposit di Online_Mode, THE AI_Agent SHALL memberikan instruksi deposit dan wallet address
4. WHEN User meminta withdrawal di Online_Mode, THE AI_Agent SHALL memvalidasi saldo dan memproses withdrawal
5. THE AI_Agent SHALL menggunakan conversational interface untuk proses deposit dan withdrawal
6. THE Bot SHALL mencatat semua transaksi deposit dan withdrawal yang diproses melalui AI_Agent
7. THE Bot SHALL mengirim konfirmasi ke User setelah transaksi berhasil diproses

### Requirement 8: UI/UX Mode Distinction

**User Story:** Sebagai user, saya ingin UI/UX yang jelas membedakan antara mode offline dan online, sehingga saya selalu tahu mode mana yang sedang aktif dan fitur apa yang tersedia.

#### Acceptance Criteria

1. THE Bot SHALL menampilkan indicator visual yang berbeda untuk Offline_Mode dan Online_Mode
2. WHEN User berada di Offline_Mode, THE Bot SHALL menampilkan prefix "[OFFLINE]" di setiap response
3. WHEN User berada di Online_Mode, THE Bot SHALL menampilkan prefix "[ONLINE - AI]" di setiap response
4. THE Bot SHALL menggunakan emoji atau icon yang berbeda untuk setiap mode
5. THE Bot SHALL menampilkan menu yang berbeda sesuai mode aktif
6. WHEN User beralih mode, THE Bot SHALL menampilkan welcome message yang menjelaskan fitur mode tersebut
7. THE Bot SHALL menyediakan command /status untuk melihat mode aktif dan informasi terkait

### Requirement 9: Smooth Mode Transition

**User Story:** Sebagai user, saya ingin transisi antara mode offline dan online berjalan smooth tanpa kehilangan context, sehingga pengalaman penggunaan bot terasa seamless.

#### Acceptance Criteria

1. WHEN User beralih dari Offline_Mode ke Online_Mode, THE Bot SHALL menyimpan state Offline_Mode
2. WHEN User beralih dari Online_Mode ke Offline_Mode, THE Bot SHALL menutup Session dengan graceful
3. THE Bot SHALL tidak kehilangan data User saat transisi mode
4. WHEN transisi mode terjadi, THE Bot SHALL menampilkan loading indicator
5. THE Bot SHALL menyelesaikan transisi mode dalam waktu maksimal 2 detik
6. IF terjadi error saat transisi, THEN THE Bot SHALL menampilkan pesan error dan tetap di mode sebelumnya
7. THE Bot SHALL mencatat setiap transisi mode di log untuk monitoring

### Requirement 10: Isolated AI Agent Management

**User Story:** Sebagai user, saya ingin memiliki AI agent yang benar-benar isolated dan pribadi, sehingga percakapan dan strategi trading saya tidak tercampur dengan user lain.

#### Acceptance Criteria

1. WHEN User pertama kali mengakses Online_Mode, THE Bot SHALL membuat Isolated_Agent baru untuk User
2. THE Bot SHALL menyimpan Isolated_Agent dengan identifier unik per User
3. THE Isolated_Agent SHALL menyimpan conversation history hanya untuk User pemiliknya
4. THE Bot SHALL memastikan Isolated_Agent User A tidak dapat diakses oleh User B
5. WHEN User mengakses Online_Mode, THE Bot SHALL memuat Isolated_Agent yang sesuai dengan User ID
6. THE Isolated_Agent SHALL menggunakan Genesis_Prompt yang sama untuk semua user sebagai base knowledge
7. THE Bot SHALL dapat menghapus Isolated_Agent jika User request atau tidak aktif dalam periode tertentu

### Requirement 11: Genesis Prompt Integration

**User Story:** Sebagai system, saya ingin setiap AI agent menggunakan Genesis Prompt yang konsisten, sehingga semua agent memiliki base knowledge yang sama tentang trading otomatis.

#### Acceptance Criteria

1. THE Bot SHALL memuat Genesis_Prompt dari file konfigurasi saat inisialisasi
2. WHEN Isolated_Agent dibuat, THE Bot SHALL menginject Genesis_Prompt sebagai system prompt
3. THE Genesis_Prompt SHALL berisi instruksi untuk trading otomatis dan signal generation
4. THE Bot SHALL dapat mengupdate Genesis_Prompt tanpa perlu restart untuk agent baru
5. THE Isolated_Agent SHALL menggunakan Genesis_Prompt sebagai context dasar untuk semua response
6. WHERE Admin mengupdate Genesis_Prompt, THE Bot SHALL menerapkan update ke agent baru yang dibuat setelahnya

### Requirement 12: Error Handling and Fallback

**User Story:** Sebagai user, saya ingin bot tetap berfungsi dengan baik meskipun terjadi error, sehingga pengalaman saya tidak terganggu.

#### Acceptance Criteria

1. IF Automaton service tidak tersedia, THEN THE Bot SHALL menampilkan pesan error dan menyarankan menggunakan Offline_Mode
2. IF AI_Agent gagal merespon, THEN THE Bot SHALL retry maksimal 3 kali dengan exponential backoff
3. IF retry gagal, THEN THE Bot SHALL menampilkan pesan error yang informatif dan tidak mengurangi Automaton_Credits
4. WHEN error terjadi di Online_Mode, THE Bot SHALL mencatat error di log dengan detail lengkap
5. THE Bot SHALL mengirim notifikasi ke Admin jika terjadi error critical
6. IF database tidak tersedia, THEN THE Bot SHALL menggunakan cache lokal untuk operasi read-only
7. THE Bot SHALL menampilkan status system health di command /status untuk debugging

### Requirement 13: Automaton API Credit Validation

**User Story:** Sebagai admin, saya ingin sistem memvalidasi koneksi dan saldo Automaton API sebelum memberikan credits ke user, sehingga credits yang diberikan sesuai dengan credits yang tersedia di dashboard Automaton saya.

#### Acceptance Criteria

1. WHEN Admin akan memberikan Automaton_Credits, THE Bot SHALL memvalidasi koneksi ke Automaton API terlebih dahulu
2. IF Automaton API tidak tersambung, THEN THE Bot SHALL menampilkan pesan error dan membatalkan pemberian credits
3. WHEN koneksi Automaton API berhasil, THE Bot SHALL mengecek saldo Automaton_Credits Admin di dashboard Automaton
4. THE Bot SHALL menampilkan saldo Automaton_Credits Admin di menu admin
5. WHEN Admin memasukkan jumlah credits untuk diberikan, THE Bot SHALL memvalidasi bahwa jumlah tersebut tidak melebihi saldo Admin
6. IF jumlah credits melebihi saldo Admin, THEN THE Bot SHALL menampilkan pesan error dengan informasi saldo tersedia
7. IF Automaton API timeout saat pengecekan, THEN THE Bot SHALL menampilkan pesan error timeout dan menyarankan retry
8. THE Bot SHALL mencatat setiap pengecekan Automaton API di audit log dengan timestamp dan status
9. THE Bot SHALL mencatat saldo Admin sebelum dan sesudah pemberian credits untuk audit trail
10. WHEN pemberian credits berhasil, THE Bot SHALL mengurangi saldo Admin di Automaton API sesuai jumlah yang diberikan

