"""1stdibs marketplace parser."""
from backend.ingestion.parsers.base import BaseParser, NormalizedProduct


class FirstDibsParser(BaseParser):
    source_name = "1stdibs"

    def parse(self, raw: dict) -> NormalizedProduct:
        metadata = raw.get("metadata", {})
        model = raw.get("model", "")

        # Prefer the explicit USD price from all_prices; fallback to top-level price
        all_prices = metadata.get("all_prices", {})
        price_usd = all_prices.get("USD") or raw.get("price", 0)
        price = self._safe_decimal(price_usd)

        # Condition from metadata fields
        condition = (
            metadata.get("condition_display")
            or metadata.get("condition")
            or metadata.get("item_condition")
        )

        # Extract category from product URL path
        # e.g. /fashion/accessories/belts/... → "Belts"
        url: str = raw.get("product_url", "")
        category = "Other"
        if url:
            parts = [p for p in url.split("/") if p]
            # typically: ['fashion', 'accessories', 'belts', 'product-slug', 'id-...']
            if len(parts) >= 3:
                category = parts[2].replace("-", " ").title()

        # Image from first main_images entry
        image_url = raw.get("image_url") or (
            raw.get("main_images", [{}])[0].get("url") if raw.get("main_images") else None
        )

        return NormalizedProduct(
            external_id=raw.get("product_id", raw.get("session_id", "")),
            source_name=self.source_name,
            title=model or raw.get("brand", ""),
            brand=raw.get("brand", ""),
            model=model,
            price=price,
            currency="USD",
            url=url,
            category=category,
            condition=condition,
            image_url=image_url,
        )
