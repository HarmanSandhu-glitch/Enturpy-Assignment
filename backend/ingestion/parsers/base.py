"""Base parser interface for all marketplace parsers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class NormalizedProduct:
    """Canonical product representation after parsing."""
    external_id: str          # UUID or unique ID from the source
    source_name: str          # 'grailed' | 'fashionphile' | '1stdibs'
    title: str
    brand: str
    model: str
    price: Decimal
    currency: str
    url: str
    category: str
    condition: Optional[str]
    image_url: Optional[str]


class BaseParser(ABC):
    """Abstract marketplace parser."""

    source_name: str  # Must be set by each subclass

    @abstractmethod
    def parse(self, raw: dict) -> NormalizedProduct:
        """Parse raw marketplace JSON into a NormalizedProduct."""
        ...

    def _safe_decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal("0")
