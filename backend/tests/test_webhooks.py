"""Tests for webhook subscription CRUD and notification delivery."""
import pytest

HEADERS = {"X-API-Key": "test-key"}


@pytest.mark.asyncio
async def test_create_webhook(client):
    resp = await client.post(
        "/api/webhooks",
        json={"callback_url": "http://example.com/hook", "secret": "mysecret"},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["callback_url"] == "http://example.com/hook"
    assert data["active"] is True


@pytest.mark.asyncio
async def test_list_webhooks(client):
    await client.post(
        "/api/webhooks",
        json={"callback_url": "http://example.com/hook2"},
        headers=HEADERS,
    )
    resp = await client.get("/api/webhooks", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_delete_webhook(client):
    create_resp = await client.post(
        "/api/webhooks",
        json={"callback_url": "http://example.com/hook-to-delete"},
        headers=HEADERS,
    )
    webhook_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/webhooks/{webhook_id}", headers=HEADERS)
    assert del_resp.status_code == 204

    # Verify it no longer appears in list
    list_resp = await client.get("/api/webhooks", headers=HEADERS)
    ids = [w["id"] for w in list_resp.json()]
    assert webhook_id not in ids


@pytest.mark.asyncio
async def test_delete_nonexistent_webhook_returns_404(client):
    resp = await client.delete("/api/webhooks/999999", headers=HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_notification_queue_receives_price_change_event():
    """Unit test: pushing to queue and retrieving the event."""
    from backend.notifications.queue import push_event, get_queue

    event = {"product_id": 1, "old_price": 100.0, "new_price": 120.0, "title": "Test"}
    await push_event(event)
    queue = get_queue()
    received = await queue.get()
    assert received["product_id"] == 1
    assert received["new_price"] == 120.0
