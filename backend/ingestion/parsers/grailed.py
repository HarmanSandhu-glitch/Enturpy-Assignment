"""Grailed marketplace parser."""
from backend.ingestion.parsers.base import BaseParser, NormalizedProduct


class GrailedParser(BaseParser):
    source_name = "grailed"

    def parse(self, raw: dict) -> NormalizedProduct:
        metadata = raw.get("metadata", {})
        model = raw.get("model", "")

        # Grailed doesn't provide an explicit currency — all prices are USD
        price = self._safe_decimal(raw.get("price", 0))

        # Derive category from function_id (e.g. "apparel_authentication" → "apparel")
        function_id: str = raw.get("function_id", "")
        category = function_id.replace("_authentication", "").replace("_", " ").title() if function_id else "Other"

        condition = None
        if metadata.get("is_sold"):
            condition = "Sold"
        elif metadata.get("condition"):
            condition = metadata["condition"]

        return NormalizedProduct(
            external_id=raw.get("product_id", raw.get("session_id", "")),
            source_name=self.source_name,
            title=model or raw.get("brand", ""),
            brand=raw.get("brand", ""),
            model=model,
            price=price,
            currency="USD",
            url=raw.get("product_url", ""),
            category=category,
            condition=condition,
            image_url=raw.get("image_url"),
        )
