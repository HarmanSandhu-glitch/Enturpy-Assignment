"""Global asyncio queue for price change events."""
import asyncio
from typing import Any

_queue: asyncio.Queue = asyncio.Queue()


def get_queue() -> asyncio.Queue:
    return _queue


async def push_event(event: dict[str, Any]) -> None:
    await _queue.put(event)
