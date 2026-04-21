from pydantic import BaseModel
from typing import Optional


class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
    referred_by: Optional[str] = None


class UserProfile(BaseModel):
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    credits: int
    is_premium: bool
    premium_until: Optional[str]
    is_lifetime: bool = False
    is_admin: bool = False
