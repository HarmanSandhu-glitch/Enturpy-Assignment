"""Shared pytest fixtures."""
import os
import asyncio
import pytest
import pytest_asyncio

# Set env vars BEFORE any backend imports
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["DEV_API_KEYS"] = '["test-key"]'
os.environ["SAMPLE_DATA_DIR"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sample_products",
)

from httpx import AsyncClient, ASGITransport  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession  # noqa: E402

from backend.database import Base  # noqa: E402
import backend.database as db_module  # noqa: E402
from backend.main import app  # noqa: E402
from backend.auth.api_key import seed_api_keys  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)

    # Patch module-level engine + session factory BEFORE creating tables
    db_module.engine = engine
    db_module.AsyncSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Now create tables using the patched engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client(test_engine):
    """HTTP client with seeded API keys."""
    async with db_module.AsyncSessionFactory() as session:
        await seed_api_keys(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def seeded_client(test_engine):
    """HTTP client with seeded API keys (same pool, data loaded by test_list_products_returns_data)."""
    async with db_module.AsyncSessionFactory() as session:
        await seed_api_keys(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


HEADERS = {"X-API-Key": "test-key"}
BAD_HEADERS = {"X-API-Key": "wrong-key"}
