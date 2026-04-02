"""Webhooks router — CRUD for subscriptions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.api_key import require_api_key
from backend.database import get_db
from backend.models.webhook import WebhookSubscription
from backend.schemas import WebhookCreate, WebhookOut

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookOut, status_code=201)
async def create_webhook(
    body: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    sub = WebhookSubscription(callback_url=body.callback_url, secret=body.secret)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.active == True))  # noqa: E712
    return result.scalars().all()


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    sub.active = False
    await db.commit()
