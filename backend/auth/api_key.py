"""API Key authentication dependency."""
import hashlib
import logging
from fastapi import Header, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.api_key import ApiKey

logger = logging.getLogger(__name__)


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> str:
    """FastAPI dependency: validates X-API-Key header and increments usage count."""
    key_hash = _hash_key(x_api_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key_row = result.scalar_one_or_none()

    if api_key_row is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Increment usage counter
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key_row.id)
        .values(request_count=ApiKey.request_count + 1)
    )
    await db.commit()
    return x_api_key


async def seed_api_keys(db: AsyncSession) -> None:
    """Idempotently seed dev API keys from config on startup."""
    for raw_key in settings.dev_api_keys:
        key_hash = _hash_key(raw_key)
        result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        if result.scalar_one_or_none() is None:
            db.add(ApiKey(key_hash=key_hash, label=f"dev-{raw_key[:8]}"))
    await db.commit()
