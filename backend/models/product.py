"""Product model — current state of a product listing."""
from typing import Optional, List
from sqlalchemy import String, Numeric, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from decimal import Decimal

from backend.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_product_source_external"),
        Index("ix_products_source_category_price", "source_id", "category_id", "current_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    brand: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    condition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    source: Mapped["Source"] = relationship("Source", back_populates="products")  # type: ignore[name-defined]
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")  # type: ignore[name-defined]
    price_history: Mapped[List["PriceHistory"]] = relationship(  # type: ignore[name-defined]
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )
    webhook_deliveries: Mapped[List["WebhookDelivery"]] = relationship(  # type: ignore[name-defined]
        "WebhookDelivery", back_populates="product", cascade="all, delete-orphan"
    )
