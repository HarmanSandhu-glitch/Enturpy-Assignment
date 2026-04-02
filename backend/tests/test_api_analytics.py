"""Tests for analytics endpoint."""
import pytest

HEADERS = {"X-API-Key": "test-key"}


@pytest.mark.asyncio
async def test_analytics_returns_source_totals(seeded_client):
    resp = await seeded_client.get("/api/analytics", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_products" in data
    assert "by_source" in data
    assert "by_category" in data
    assert data["total_products"] >= 0


@pytest.mark.asyncio
async def test_analytics_source_names_are_known(seeded_client):
    resp = await seeded_client.get("/api/analytics", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    known_sources = {"grailed", "fashionphile", "1stdibs"}
    for entry in data["by_source"]:
        assert entry["source"] in known_sources
        assert entry["total_products"] >= 0
        assert entry["avg_price"] >= 0
