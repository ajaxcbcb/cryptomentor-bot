import time
from fastapi import APIRouter, HTTPException
from app.auth.telegram import verify_telegram_auth
from app.auth.jwt import create_token
from app.db.supabase import upsert_web_login
from app.models.user import TelegramAuthData

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_AUTH_AGE_SECONDS = 86400  # 24 jam


@router.post("/telegram")
async def telegram_login(data: TelegramAuthData):
    """
    Endpoint dipanggil frontend setelah user klik Telegram Login Widget.
    Frontend kirim semua field dari Telegram ke sini.
    """
    payload = data.model_dump()

    # 1. Verifikasi hash dari Telegram
    if not verify_telegram_auth(payload):
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    # 2. Cek auth_date tidak terlalu lama
    if time.time() - data.auth_date > MAX_AUTH_AGE_SECONDS:
        raise HTTPException(status_code=401, detail="Auth data expired")

    # 3. Upsert user ke Supabase
    user = upsert_web_login(
        tg_id=data.id,
        username=data.username or "",
        first_name=data.first_name,
        last_name=data.last_name,
    )

    # 4. Buat JWT
    token = create_token(
        telegram_id=data.id,
        extra={"username": data.username, "first_name": data.first_name},
    )

    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/logout")
async def logout():
    # JWT stateless, logout cukup hapus token di frontend
    return {"message": "Logged out"}
