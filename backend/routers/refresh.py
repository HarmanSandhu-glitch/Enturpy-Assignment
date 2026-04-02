"""Refresh router — triggers async data ingestion."""
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends

from backend.auth.api_key import require_api_key
from backend.ingestion.fetcher import load_from_files
from backend.notifications.queue import push_event
from backend.schemas import RefreshOut

router = APIRouter(prefix="/api/refresh", tags=["refresh"])

_refresh_lock = asyncio.Lock()


async def _run_refresh() -> dict:
    async with _refresh_lock:
        events = await load_from_files()
        for event in events:
            await push_event(event)
        return {"products_processed": -1, "price_changes": len(events)}


@router.post("", response_model=RefreshOut)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    _: str = Depends(require_api_key),
):
    """Trigger a non-blocking data refresh. Returns immediately."""
    background_tasks.add_task(_async_refresh_task)
    return RefreshOut(status="refresh_started", products_processed=0, price_changes=0)


async def _async_refresh_task():
    result = await _run_refresh()
    return result


@router.post("/sync", response_model=RefreshOut)
async def trigger_refresh_sync(
    _: str = Depends(require_api_key),
):
    """Trigger a synchronous data refresh — waits for completion and returns counts."""
    result = await _run_refresh()
    return RefreshOut(
        status="ok",
        products_processed=result["price_changes"],
        price_changes=result["price_changes"],
    )
