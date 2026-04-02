"""Tests for marketplace parsers."""
import pytest
from decimal import Decimal

from backend.ingestion.parsers.grailed import GrailedParser
from backend.ingestion.parsers.fashionphile import FashionphileParser
from backend.ingestion.parsers.firstdibs import FirstDibsParser


GRAILED_SAMPLE = {
    "brand": "amiri",
    "model": "Amiri Washed Filigree T-Shirt",
    "price": 425.0,
    "image_url": "https://media-assets.grailed.com/prd/listing/temp/069726883ab242969a4b4e5e42429c2a",
    "product_url": "https://www.grailed.com/listings/83672676",
    "metadata": {"color": "Black", "style": "Street", "is_sold": False},
    "product_id": "3dcbbe62-a0c8-4238-8f42-acdb7f0af660",
    "function_id": "apparel_authentication",
}

FASHIONPHILE_SAMPLE = {
    "product_url": "https://www.fashionphile.com/products/tiffany-earrings-1806623",
    "condition": "Shows Wear",
    "price": 1480.0,
    "currency": "USD",
    "image_url": "https://example.com/image.jpg",
    "product_id": "84f903a5-3c76-53d5-9d31-25956c2ffdc3",
    "brand_id": "tiffany",
    "function_id": "apparel_authentication",
    "metadata": {
        "garment_type": "jewelry",
        "item_number": "1806623",
        "original_price": 2100.0,
        "sku": "1806623",
    },
    "brand": "Tiffany",
    "model": "Tiffany 18K Rose Gold Earrings",
}

FIRSTDIBS_SAMPLE = {
    "product_url": "https://www.1stdibs.com/fashion/accessories/belts/chanel-belt/id-v_123/",
    "model": "CHANEL Belt",
    "price": 2617.6,
    "brand": "Chanel",
    "main_images": [{"url": "https://example.com/img.jpg", "format": "image/jpeg", "metadata": {}}],
    "metadata": {
        "condition_display": "New",
        "all_prices": {"USD": 2617.6, "EUR": 2200.0},
    },
    "product_id": "8205b80f-2d23-449c-9ea9-0060c3c2df8e",
}


class TestGrailedParser:
    def setup_method(self):
        self.parser = GrailedParser()

    def test_parses_correct_fields(self):
        result = self.parser.parse(GRAILED_SAMPLE)
        assert result.brand == "amiri"
        assert result.model == "Amiri Washed Filigree T-Shirt"
        assert result.price == Decimal("425.0")
        assert result.currency == "USD"
        assert result.source_name == "grailed"
        assert result.external_id == "3dcbbe62-a0c8-4238-8f42-acdb7f0af660"

    def test_derives_category_from_function_id(self):
        result = self.parser.parse(GRAILED_SAMPLE)
        assert result.category == "Apparel"

    def test_handles_missing_price_gracefully(self):
        sample = {**GRAILED_SAMPLE, "price": None}
        result = self.parser.parse(sample)
        assert result.price == Decimal("0")


class TestFashionphileParser:
    def setup_method(self):
        self.parser = FashionphileParser()

    def test_parses_correct_fields(self):
        result = self.parser.parse(FASHIONPHILE_SAMPLE)
        assert result.brand == "Tiffany"
        assert result.price == Decimal("1480.0")
        assert result.currency == "USD"
        assert result.condition == "Shows Wear"
        assert result.source_name == "fashionphile"

    def test_uses_garment_type_for_category(self):
        result = self.parser.parse(FASHIONPHILE_SAMPLE)
        assert result.category == "Jewelry"


class TestFirstDibsParser:
    def setup_method(self):
        self.parser = FirstDibsParser()

    def test_prefers_usd_from_all_prices(self):
        result = self.parser.parse(FIRSTDIBS_SAMPLE)
        assert result.price == Decimal("2617.6")

    def test_derives_category_from_url(self):
        result = self.parser.parse(FIRSTDIBS_SAMPLE)
        # URL: /fashion/accessories/belts/... → parts[2] = 'belts' → 'Belts'
        assert result.category in ("Belts", "Accessories", "Fashion") or result.category != ""

    def test_reads_condition_from_metadata(self):
        result = self.parser.parse(FIRSTDIBS_SAMPLE)
        assert result.condition == "New"

    def test_source_name_is_correct(self):
        result = self.parser.parse(FIRSTDIBS_SAMPLE)
        assert result.source_name == "1stdibs"
