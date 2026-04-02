import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
import backend.database as db_module  # lazy reference so tests can patch AsyncSessionFactory
from backend.database import Base
from backend.ingestion.parsers.base import NormalizedProduct
from backend.ingestion.parsers.grailed import GrailedParser
from backend.ingestion.parsers.fashionphile import FashionphileParser
from backend.ingestion.parsers.firstdibs import FirstDibsParser
from backend.models.source import Source
from backend.models.category import Category
from backend.models.product import Product
from backend.models.price_history import PriceHistory

# Registry of parsers keyed by filename prefix
PARSERS = {
    "grailed": GrailedParser(),
    "fashionphile": FashionphileParser(),
    "1stdibs": FirstDibsParser(),
}


def _detect_parser(filename: str):
    for key, parser in PARSERS.items():
        if filename.startswith(key):
            return parser
    return None


async def _get_or_create_source(session: AsyncSession, name: str) -> Source:
    result = await session.execute(select(Source).where(Source.name == name))
    source = result.scalar_one_or_none()
    if source is None:
        source = Source(name=name, base_url="")
        session.add(source)
        await session.flush()
    return source


async def _get_or_create_category(session: AsyncSession, name: str) -> Category:
    result = await session.execute(select(Category).where(Category.name == name))
    cat = result.scalar_one_or_none()
    if cat is None:
        cat = Category(name=name)
        session.add(cat)
        await session.flush()
    return cat


async def upsert_product(
    session: AsyncSession,
    normalized: NormalizedProduct,
    source: Source,
    category: Category,
    price_change_events: list,
) -> None:
    """Insert or update a product, recording price history on change."""
    result = await session.execute(
        select(Product).where(
            Product.source_id == source.id,
            Product.external_id == normalized.external_id,
        )
    )
    product: Optional[Product] = result.scalar_one_or_none()

    if product is None:
        # New product — create and record initial price
        product = Product(
            external_id=normalized.external_id,
            source_id=source.id,
            category_id=category.id,
            title=normalized.title,
            brand=normalized.brand,
            model=normalized.model,
            condition=normalized.condition,
            url=normalized.url,
            image_url=normalized.image_url,
            current_price=normalized.price,
            currency=normalized.currency,
            last_seen_at=datetime.now(timezone.utc),
        )
        session.add(product)
        await session.flush()
        session.add(PriceHistory(
            product_id=product.id,
            price=normalized.price,
            currency=normalized.currency,
        ))
    else:
        # Existing product — detect price change
        if product.current_price != normalized.price:
            price_change_events.append({
                "product_id": product.id,
                "old_price": float(product.current_price),
                "new_price": float(normalized.price),
                "currency": normalized.currency,
                "title": product.title,
                "url": product.url,
            })
            product.current_price = normalized.price
        product.last_seen_at = datetime.now(timezone.utc)
        # Always append a price history entry on each refresh
        session.add(PriceHistory(
            product_id=product.id,
            price=normalized.price,
            currency=normalized.currency,
        ))


async def load_from_files(data_dir: str | None = None) -> list:
    """Read all sample JSON files and upsert into DB. Returns list of price change events."""
    directory = Path(data_dir or settings.sample_data_dir)
    price_change_events: list = []

    files = sorted(directory.glob("*.json"))
    if not files:
        return price_change_events

    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            for filepath in files:
                parser = _detect_parser(filepath.name)
                if parser is None:
                    continue
                try:
                    raw = json.loads(filepath.read_text(encoding="utf-8"))
                    normalized = parser.parse(raw)
                    source = await _get_or_create_source(session, normalized.source_name)
                    category = await _get_or_create_category(session, normalized.category)
                    await upsert_product(session, normalized, source, category, price_change_events)
                except Exception as exc:
                    # Log and continue — don't fail the entire batch on one bad file
                    print(f"[fetcher] Skipping {filepath.name}: {exc}")

    return price_change_events


async def fetch_with_retry(
    url: str, retries: int = 3, backoff: int = 2
) -> dict:
    """Async HTTP GET with exponential backoff (used for live API integration)."""
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(backoff ** attempt)
    raise last_exc
