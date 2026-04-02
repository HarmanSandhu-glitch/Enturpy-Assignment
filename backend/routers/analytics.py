"""Analytics router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.api_key import require_api_key
from backend.database import get_db
from backend.models.product import Product
from backend.models.source import Source
from backend.models.category import Category
from backend.models.price_history import PriceHistory
from backend.schemas import AnalyticsOut, SourceStat, CategoryStat

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsOut)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    # Total products
    total = (await db.execute(select(func.count()).select_from(Product))).scalar_one()

    # Per-source stats
    source_rows = await db.execute(
        select(
            Source.name,
            func.count(Product.id).label("total"),
            func.avg(Product.current_price).label("avg_price"),
            func.min(Product.current_price).label("min_price"),
            func.max(Product.current_price).label("max_price"),
        )
        .join(Product, Product.source_id == Source.id)
        .group_by(Source.name)
    )
    by_source = [
        SourceStat(
            source=row.name,
            total_products=row.total,
            avg_price=round(float(row.avg_price or 0), 2),
            min_price=float(row.min_price or 0),
            max_price=float(row.max_price or 0),
        )
        for row in source_rows
    ]

    # Per-category stats
    category_rows = await db.execute(
        select(
            Category.name,
            func.count(Product.id).label("total"),
            func.avg(Product.current_price).label("avg_price"),
        )
        .join(Product, Product.category_id == Category.id)
        .group_by(Category.name)
    )
    by_category = [
        CategoryStat(
            category=row.name,
            total_products=row.total,
            avg_price=round(float(row.avg_price or 0), 2),
        )
        for row in category_rows
    ]

    # Last refresh = most recent price_history entry
    last_refreshed = (
        await db.execute(select(func.max(PriceHistory.recorded_at)))
    ).scalar_one_or_none()

    return AnalyticsOut(
        total_products=total,
        by_source=by_source,
        by_category=by_category,
        last_refreshed_at=last_refreshed,
    )
