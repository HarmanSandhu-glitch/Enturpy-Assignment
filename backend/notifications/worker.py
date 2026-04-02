"""Webhook delivery worker — consumes price change events and dispatches webhooks."""
import asyncio
import json
import logging
from datetime import datetime, timezone

import aiohttp
from sqlalchemy import select

from backend.config import settings
from backend.database import AsyncSessionFactory
from backend.models.webhook import WebhookSubscription, WebhookDelivery
from backend.notifications.queue import get_queue

logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None


async def _dispatch(session, subscription: WebhookSubscription, event: dict) -> None:
    """Attempt to deliver a webhook with retries. Persists all attempts to DB."""
    payload_str = json.dumps(event)
    delivery = WebhookDelivery(
        subscription_id=subscription.id,
        product_id=event["product_id"],
        event_type="price_change",
        payload=payload_str,
        status="pending",
    )
    session.add(delivery)
    await session.flush()

    for attempt in range(settings.webhook_max_retries):
        try:
            async with aiohttp.ClientSession() as client:
                headers = {"Content-Type": "application/json"}
                if subscription.secret:
                    headers["X-Webhook-Secret"] = subscription.secret
                async with client.post(
                    subscription.callback_url,
                    data=payload_str,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    resp.raise_for_status()
            delivery.status = "delivered"
            delivery.attempts = attempt + 1
            delivery.last_attempt_at = datetime.now(timezone.utc)
            logger.info(f"Webhook delivered to {subscription.callback_url} (attempt {attempt + 1})")
            return
        except Exception as exc:
            delivery.attempts = attempt + 1
            delivery.last_attempt_at = datetime.now(timezone.utc)
            logger.warning(f"Webhook attempt {attempt + 1} failed for {subscription.callback_url}: {exc}")
            if attempt < settings.webhook_max_retries - 1:
                await asyncio.sleep(settings.webhook_retry_backoff_base ** attempt)

    delivery.status = "failed"
    logger.error(f"Webhook permanently failed after {settings.webhook_max_retries} attempts: {subscription.callback_url}")


async def _worker_loop() -> None:
    """Background loop that drains the event queue and dispatches webhooks."""
    queue = get_queue()
    logger.info("Notification worker started.")
    while True:
        event: dict = await queue.get()
        try:
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(WebhookSubscription).where(WebhookSubscription.active == True)  # noqa: E712
                    )
                    subscriptions = result.scalars().all()
                    for sub in subscriptions:
                        await _dispatch(session, sub, event)
        except Exception as exc:
            logger.exception(f"Worker error processing event: {exc}")
        finally:
            queue.task_done()


def start_worker() -> asyncio.Task:
    """Start the background notification worker. Call once on app startup."""
    global _worker_task
    _worker_task = asyncio.create_task(_worker_loop())
    return _worker_task


def stop_worker() -> None:
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        _worker_task = None
