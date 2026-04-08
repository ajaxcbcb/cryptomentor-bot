from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_URL, DEBUG
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router
from app.routes.dashboard import router as dashboard_router
from app.routes.bitunix import router as bitunix_router
from app.routes.signals import router as signals_router
from app.routes.performance import router as performance_router
from app.routes.engine import router as engine_router
from app.routes.leaderboard import router as leaderboard_router

app = FastAPI(
    title="CryptoMentor Website API",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,  # Sembunyikan docs di production
    redoc_url=None,
)

# CORS - izinkan frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "https://cryptomentor.id", "https://www.cryptomentor.id"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(bitunix_router)
app.include_router(signals_router)
app.include_router(performance_router)
app.include_router(engine_router)
app.include_router(leaderboard_router)


@app.get("/")
async def health():
    return {"status": "ok", "service": "cryptomentor-website-api"}
