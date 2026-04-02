"""Fashionphile marketplace parser."""
from backend.ingestion.parsers.base import BaseParser, NormalizedProduct


class FashionphileParser(BaseParser):
    source_name = "fashionphile"

    def parse(self, raw: dict) -> NormalizedProduct:
        metadata = raw.get("metadata", {})
        model = raw.get("model", "")

        # Category from metadata.garment_type or function_id
        raw_category = metadata.get("garment_type") or raw.get("function_id", "")
        category = raw_category.replace("_authentication", "").replace("_", " ").title() if raw_category else "Other"

        return NormalizedProduct(
            external_id=raw.get("product_id", metadata.get("sku", metadata.get("item_number", ""))),
            source_name=self.source_name,
            title=model or raw.get("brand", ""),
            brand=raw.get("brand", ""),
            model=model,
            price=self._safe_decimal(raw.get("price", 0)),
            currency=raw.get("currency", "USD"),
            url=raw.get("product_url", ""),
            category=category,
            condition=raw.get("condition"),
            image_url=raw.get("image_url"),
        )
