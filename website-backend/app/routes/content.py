from __future__ import annotations

from fastapi import APIRouter
from app.db.supabase import _client

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/testimonials")
async def list_public_testimonials():
    try:
        res = (
            _client()
            .table("testimonials")
            .select("id,name,role,avatar_url,message,rating,display_order")
            .eq("is_visible", True)
            .order("display_order", desc=False)
            .order("created_at", desc=True)
            .limit(12)
            .execute()
        )
        return {"testimonials": res.data or []}
    except Exception:
        return {"testimonials": []}
