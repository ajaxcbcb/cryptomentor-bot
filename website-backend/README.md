# Website Backend - CryptoMentor

Backend API untuk website CryptoMentor. Login menggunakan Telegram Login Widget.

## Tech Stack
- FastAPI (Python)
- Telegram Login Widget (auth)
- Supabase (shared dengan Bismillah bot)
- JWT (session)

## Setup

```bash
cd website-backend
pip install -r requirements.txt
cp .env.example .env
# isi .env lalu jalankan:
uvicorn main:app --reload --port 8000
```

## Struktur
```
website-backend/
├── main.py              # Entry point + CORS
├── config.py            # Env vars
├── requirements.txt
├── .env.example
└── app/
    ├── auth/
    │   ├── telegram.py  # Verifikasi hash Telegram
    │   └── jwt.py       # Create & decode JWT
    ├── routes/
    │   ├── auth.py      # POST /auth/telegram, POST /auth/logout
    │   └── user.py      # GET /user/me, GET /user/dashboard
    ├── models/
    │   └── user.py      # Pydantic schemas
    └── db/
        └── supabase.py  # Query ke Supabase (tabel users)
```

## Endpoints

| Method | Path | Keterangan |
|--------|------|------------|
| GET | `/` | Health check |
| POST | `/auth/telegram` | Login via Telegram Widget |
| POST | `/auth/logout` | Logout (hapus token di frontend) |
| GET | `/user/me` | Profil lengkap user |
| GET | `/user/dashboard` | Data ringkasan dashboard |

## Telegram Login Setup (wajib sebelum deploy)
1. Buka BotFather → `/setdomain` → pilih bot → masukkan domain website
2. Frontend pasang widget Telegram Login (teman kamu yang handle)
3. Setelah user klik widget, frontend kirim semua field ke `POST /auth/telegram`
4. Backend verifikasi HMAC hash, buat JWT, return ke frontend
