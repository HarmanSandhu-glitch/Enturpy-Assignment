"""Products router — list, filter, and detail endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.api_key import require_api_key
from backend.database import get_db
from backend.models.product import Product
from backend.models.source import Source
from backend.models.category import Category
from backend.schemas import ProductOut, ProductDetailOut, PaginatedProducts

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=PaginatedProducts)
async def list_products(
    source: str | None = Query(None, description="Filter by source name"),
    category: str | None = Query(None, description="Filter by category name"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    brand: str | None = Query(None, description="Filter by brand (case-insensitive)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    stmt = (
        select(Product)
        .join(Product.source)
        .outerjoin(Product.category)
        .options(selectinload(Product.source), selectinload(Product.category))
    )
    if source:
        stmt = stmt.where(Source.name == source)
    if category:
        stmt = stmt.where(Category.name == category)
    if min_price is not None:
        stmt = stmt.where(Product.current_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.current_price <= max_price)
    if brand:
        stmt = stmt.where(Product.brand.ilike(f"%{brand}%"))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginate
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Product.last_seen_at.desc())
    result = await db.execute(stmt)
    products = result.scalars().all()

    items = []
    for p in products:
        out = ProductOut.model_validate(p)
        out.source_name = p.source.name if p.source else None
        out.category_name = p.category.name if p.category else None
        items.append(out)

    return PaginatedProducts(total=total, page=page, size=size, items=items)


@router.get("/{product_id}", response_model=ProductDetailOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
):
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.source),
            selectinload(Product.category),
            selectinload(Product.price_history),
        )
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    out = ProductDetailOut.model_validate(product)
    out.source_name = product.source.name if product.source else None
    out.category_name = product.category.name if product.category else None
    out.price_history = sorted(product.price_history, key=lambda h: h.recorded_at, reverse=True)
    return out
