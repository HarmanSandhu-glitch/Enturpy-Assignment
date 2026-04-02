"""Webhook subscription and delivery tracking models."""
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from backend.database import Base


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    callback_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    deliveries: Mapped[List["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan"
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_subscriptions.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="price_change")
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subscription: Mapped["WebhookSubscription"] = relationship(
        "WebhookSubscription", back_populates="deliveries"
    )
    product: Mapped["Product"] = relationship("Product", back_populates="webhook_deliveries")  # type: ignore[name-defined]
