"""Tests for deduplication and price change detection."""
import pytest
from decimal import Decimal
from sqlalchemy import select

import backend.database as db_module
from backend.ingestion.fetcher import upsert_product, _get_or_create_source, _get_or_create_category
from backend.ingestion.parsers.base import NormalizedProduct
from backend.models.product import Product
from backend.models.price_history import PriceHistory


def make_product(price: float, external_id: str = "test-dedupe-001") -> NormalizedProduct:
    return NormalizedProduct(
        external_id=external_id,
        source_name="grailed",
        title="Test Product",
        brand="TestBrand",
        model="Test Model",
        price=Decimal(str(price)),
        currency="USD",
        url="https://grailed.com/test",
        category="Apparel",
        condition=None,
        image_url=None,
    )


@pytest.mark.asyncio
async def test_same_product_upserted_creates_one_row(test_engine):
    events = []
    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            source = await _get_or_create_source(session, "grailed")
            category = await _get_or_create_category(session, "Apparel")
            product = make_product(100.0, "dedupe-uuid-1")
            await upsert_product(session, product, source, category, events)
            await upsert_product(session, product, source, category, events)

    async with db_module.AsyncSessionFactory() as session:
        result = await session.execute(
            select(Product).where(Product.external_id == "dedupe-uuid-1")
        )
        rows = result.scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_price_change_detected(test_engine):
    events = []
    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            source = await _get_or_create_source(session, "grailed")
            category = await _get_or_create_category(session, "Apparel")
            await upsert_product(session, make_product(200.0, "price-change-uuid"), source, category, events)

    events2 = []
    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            source = await _get_or_create_source(session, "grailed")
            category = await _get_or_create_category(session, "Apparel")
            await upsert_product(session, make_product(250.0, "price-change-uuid"), source, category, events2)

    assert len(events2) == 1
    assert events2[0]["old_price"] == 200.0
    assert events2[0]["new_price"] == 250.0


@pytest.mark.asyncio
async def test_no_price_change_no_event(test_engine):
    events = []
    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            source = await _get_or_create_source(session, "grailed")
            category = await _get_or_create_category(session, "Apparel")
            await upsert_product(session, make_product(300.0, "no-change-uuid"), source, category, events)

    events2 = []
    async with db_module.AsyncSessionFactory() as session:
        async with session.begin():
            source = await _get_or_create_source(session, "grailed")
            category = await _get_or_create_category(session, "Apparel")
            await upsert_product(session, make_product(300.0, "no-change-uuid"), source, category, events2)

    assert len(events2) == 0
