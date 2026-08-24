import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Category, Product, Variant
from apps.catalog.seed import content as content_seed
from apps.catalog.seed.taxonomy import BRANDS, CATEGORIES
from apps.content.models import Banner, Page, SiteSettings
from apps.loyalty.models import LoyaltySettings
from apps.pricing import services as pricing_services
from apps.pricing.models import PricingSettings
from apps.shipping.models import ShippingSettings

PRODUCTS_JSON = Path(__file__).resolve().parents[2] / "seed" / "products.json"
DEFAULT_STOCK = 12


class Command(BaseCommand):
    help = "Наповнює базу стартовим контентом і тестовим каталогом з прайсу клієнта."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Видалити наявні товари перед сівбою")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Variant.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING("Каталог очищено"))

        self._seed_settings()
        brands = self._seed_brands()
        categories = self._seed_categories()
        self._seed_products(brands, categories)
        self._seed_content()
        pricing_services.recalculate_all()

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {Product.objects.count()} товарів, {Variant.objects.count()} варіантів, "
                f"{Category.objects.count()} категорій"
            )
        )

    def _seed_brands(self) -> dict:
        result = {}
        for data in BRANDS:
            key = data.pop("key") if "key" in data else data["slug"]
            brand, _ = Brand.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "sort_order": data["sort_order"],
                    "description_uk": data["description_uk"],
                    "description_ru": data["description_ru"],
                },
            )
            result[key] = brand
        return result

    def _seed_categories(self) -> dict:
        result = {}
        for data in CATEGORIES:
            category, _ = Category.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name_uk": data["name_uk"],
                    "name_ru": data["name_ru"],
                    "sort_order": data["sort_order"],
                    "description_uk": data["description_uk"],
                    "description_ru": data["description_ru"],
                    "seo_title_uk": f"{data['name_uk']} — купити в Україні | SVbeauty",
                    "seo_description_uk": data["description_uk"],
                },
            )
            result[data["slug"]] = category
        return result

    def _seed_products(self, brands: dict, categories: dict) -> None:
        with PRODUCTS_JSON.open(encoding="utf-8") as fh:
            items = json.load(fh)

        for order, item in enumerate(items, start=1):
            description = item.get("description_uk", "")
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "brand": brands[item["brand"]],
                    "category": categories[item["category"]],
                    "name_uk": item["name_uk"],
                    "name_ru": item["name_ru"],
                    "description_uk": description,
                    "short_description_uk": description[:290],
                    "is_hit": item["is_hit"],
                    "is_new": item["is_new"],
                    "sort_order": order,
                    "seo_title_uk": f"{item['name_uk']} — SVbeauty",
                    "seo_description_uk": description[:290],
                },
            )
            for index, variant in enumerate(item["variants"], start=1):
                Variant.objects.update_or_create(
                    sku=variant["sku"],
                    defaults={
                        "product": product,
                        "volume": variant["volume"],
                        "purchase_price_uah": Decimal(str(variant["price"])),
                        "stock_qty": DEFAULT_STOCK,
                        "sort_order": index,
                    },
                )

    def _seed_settings(self) -> None:
        self._update_singleton(SiteSettings, content_seed.SITE_SETTINGS)
        self._update_singleton(PricingSettings, content_seed.PRICING_SETTINGS)
        self._update_singleton(LoyaltySettings, content_seed.LOYALTY_SETTINGS)
        ShippingSettings.get_solo()

    @staticmethod
    def _update_singleton(model, values: dict) -> None:
        obj = model.get_solo()
        for field, value in values.items():
            setattr(obj, field, value)
        obj.save()

    def _seed_content(self) -> None:
        for data in content_seed.PAGES:
            Page.objects.update_or_create(slug=data["slug"], defaults=data)
        Banner.objects.update_or_create(
            title_uk=content_seed.BANNER["title_uk"], defaults=content_seed.BANNER
        )
