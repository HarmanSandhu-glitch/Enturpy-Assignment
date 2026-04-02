"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, HttpUrl
from decimal import Decimal
from datetime import datetime
from typing import Optional


# --- Price History ---

class PriceHistoryOut(BaseModel):
    id: int
    price: Decimal
    currency: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


# --- Products ---

class ProductOut(BaseModel):
    id: int
    external_id: str
    title: str
    brand: str
    model: str
    condition: Optional[str]
    url: str
    image_url: Optional[str]
    current_price: Decimal
    currency: str
    last_seen_at: datetime
    source_name: Optional[str] = None
    category_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductDetailOut(ProductOut):
    price_history: list[PriceHistoryOut] = []


# --- Analytics ---

class SourceStat(BaseModel):
    source: str
    total_products: int
    avg_price: float
    min_price: float
    max_price: float


class CategoryStat(BaseModel):
    category: str
    total_products: int
    avg_price: float


class AnalyticsOut(BaseModel):
    total_products: int
    by_source: list[SourceStat]
    by_category: list[CategoryStat]
    last_refreshed_at: Optional[datetime]


# --- Refresh ---

class RefreshOut(BaseModel):
    status: str
    products_processed: int
    price_changes: int


# --- Webhooks ---

class WebhookCreate(BaseModel):
    callback_url: str
    secret: Optional[str] = None


class WebhookOut(BaseModel):
    id: int
    callback_url: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Pagination ---

class PaginatedProducts(BaseModel):
    total: int
    page: int
    size: int
    items: list[ProductOut]


# --- Health ---

class HealthOut(BaseModel):
    status: str
