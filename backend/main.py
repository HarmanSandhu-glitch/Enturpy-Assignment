"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db, AsyncSessionFactory
from backend.auth.api_key import seed_api_keys
from backend.notifications.worker import start_worker, stop_worker
from backend.routers import products, analytics, refresh, webhooks
from backend.schemas import HealthOut

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    async with AsyncSessionFactory() as session:
        await seed_api_keys(session)
    logger.info("Starting notification worker...")
    start_worker()
    logger.info("Application ready.")
    yield
    # Shutdown
    stop_worker()
    logger.info("Application shutdown.")


app = FastAPI(
    title="Entrupy Price Monitor",
    description="Product price monitoring across Grailed, Fashionphile, and 1stdibs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(refresh.router)
app.include_router(webhooks.router)


@app.get("/api/health", response_model=HealthOut, tags=["health"])
async def health():
    return HealthOut(status="ok")
