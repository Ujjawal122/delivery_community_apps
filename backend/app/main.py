from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import redis_client
import app.core.handlers as handlers
from app.core.logging import get_logger, setup_logging
from app.core.responses import ApiResponse, ok
from app.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.post import router as post_router
from app.routers.community import router as community_router
from app.routers.location import router as location_router
from app.routers.hazard import router as hazard_router
from app.routers.gate import router as gate_router

logger = get_logger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Delivery Community API starting")

    # Connect Redis Cloud
    await redis_client.connect()

    yield

    # Graceful shutdown
    await redis_client.close()
    logger.info("Delivery Community API stopped")


# ── App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Delivery Community API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

handlers.register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(post_router)
app.include_router(community_router)
app.include_router(location_router)
app.include_router(hazard_router)
app.include_router(gate_router)


# ── Health ─────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], response_model=ApiResponse)
async def root():
    return ok({"version": "1.0.0"}, "Delivery Community API is running")


@app.get("/db-test", tags=["Health"], response_model=ApiResponse)
async def test_database(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return ok({"result": result.scalar()}, "Database connected")


@app.get("/redis-test", tags=["Health"], response_model=ApiResponse)
async def test_redis(redis: Redis = Depends(get_redis)):
    """Verify Redis Cloud connection."""
    pong = await redis.ping()
    info = await redis.info("server")
    return ok(
        {
            "ping": pong,
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
        },
        "Redis Cloud connected",
    )


# ── Test routes ────────────────────────────────────────────────────

@app.get("/test/protected", tags=["Auth Tests"], response_model=ApiResponse)
async def test_protected_route(current_user: User = Depends(get_current_user)):
    """🔐 Protected — requires valid Bearer access token."""
    return ok(
        {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_verified": current_user.is_verified,
        },
        "Authenticated",
    )


@app.get("/test/public", tags=["Auth Tests"], response_model=ApiResponse)
async def test_public_route():
    """🌍 Public — no token required."""
    return ok(None, "Public route. No authentication needed.")
 