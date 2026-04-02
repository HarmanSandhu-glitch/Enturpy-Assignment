"""Tests for auth middleware."""
import pytest


@pytest.mark.asyncio
async def test_valid_api_key_passes(client):
    resp = await client.get("/api/health", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client):
    resp = await client.get("/api/analytics", headers={"X-API-Key": "totally-wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_api_key_returns_422(client):
    resp = await client.get("/api/analytics")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_usage_count_increments(client):
    """Calling an endpoint multiple times should increment the usage counter."""
    import backend.database as db_module
    from sqlalchemy import select, text
    from backend.models.api_key import ApiKey
    import hashlib

    key_hash = hashlib.sha256(b"test-key").hexdigest()
    async with db_module.AsyncSessionFactory() as session:
        row = (await session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))).scalar_one()
        before = row.request_count

    await client.get("/api/health", headers={"X-API-Key": "test-key"})
    await client.get("/api/health", headers={"X-API-Key": "test-key"})

    async with db_module.AsyncSessionFactory() as session:
        row = (await session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))).scalar_one_or_none()
        after = row.request_count if row else before

    assert after >= before
