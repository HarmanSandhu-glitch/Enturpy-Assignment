"""Tests for product API endpoints."""
import pytest


HEADERS = {"X-API-Key": "test-key"}


@pytest.mark.asyncio
async def test_list_products_returns_data(seeded_client):
    resp = await seeded_client.post("/api/refresh/sync", headers=HEADERS)
    assert resp.status_code == 200

    resp = await seeded_client.get("/api/products", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0


@pytest.mark.asyncio
async def test_filter_by_source(seeded_client):
    resp = await seeded_client.get("/api/products?source=grailed", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["source_name"] == "grailed"


@pytest.mark.asyncio
async def test_filter_by_price_range(seeded_client):
    resp = await seeded_client.get("/api/products?min_price=100&max_price=500", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert 100 <= float(item["current_price"]) <= 500


@pytest.mark.asyncio
async def test_product_detail_returns_price_history(seeded_client):
    # Get first product ID
    resp = await seeded_client.get("/api/products?size=1", headers=HEADERS)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0

    product_id = items[0]["id"]
    resp = await seeded_client.get(f"/api/products/{product_id}", headers=HEADERS)
    assert resp.status_code == 200
    detail = resp.json()
    assert "price_history" in detail
    assert len(detail["price_history"]) >= 1


@pytest.mark.asyncio
async def test_product_not_found_returns_404(seeded_client):
    resp = await seeded_client.get("/api/products/999999", headers=HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_price_range_returns_422(seeded_client):
    resp = await seeded_client.get("/api/products?min_price=-10", headers=HEADERS)
    assert resp.status_code == 422
