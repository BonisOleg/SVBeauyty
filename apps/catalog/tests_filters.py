from decimal import Decimal
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.accounts.models import ClientType
from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeGroup,
    Variant,
)
from apps.catalog import selectors
from apps.pricing.models import PricingSettings

User = get_user_model()


class CatalogFiltersTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        pricing = PricingSettings.get_solo()
        pricing.retail_markup_percent = Decimal("100.00")
        pricing.pro_markup_percent = Decimal("40.00")
        pricing.rounding_step = "1.00"
        pricing.save()

        self.brand = Brand.objects.create(name="Cure Skin", slug="cure-skin")
        self.category = Category.objects.create(name_uk="Сироватки", slug="syrovatky")

        self.group_age = ProductAttributeGroup.objects.create(
            slug=ProductAttributeGroup.Slug.AGE,
            name_uk="За віком",
            sort_order=10,
        )
        self.group_skin = ProductAttributeGroup.objects.create(
            slug=ProductAttributeGroup.Slug.SKIN_TYPE,
            name_uk="За типом шкіри",
            sort_order=20,
        )
        self.attr_35 = ProductAttribute.objects.create(
            group=self.group_age, slug="35-plus", name_uk="35+", sort_order=10
        )
        self.attr_dry = ProductAttribute.objects.create(
            group=self.group_skin, slug="dry", name_uk="Суха", sort_order=10
        )
        self.attr_oily = ProductAttribute.objects.create(
            group=self.group_skin, slug="oily", name_uk="Жирна", sort_order=20
        )

        self.product_a = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Сироватка A",
            slug="serum-a",
        )
        self.product_b = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Сироватка B",
            slug="serum-b",
        )
        self.product_c = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Сироватка C",
            slug="serum-c",
        )

        self.variant_a = Variant.objects.create(
            product=self.product_a,
            sku="A-001",
            volume="30 мл",
            purchase_price_uah=Decimal("500.00"),
            stock_qty=5,
        )
        self.variant_b = Variant.objects.create(
            product=self.product_b,
            sku="B-001",
            volume="30 мл",
            purchase_price_uah=Decimal("400.00"),
            stock_qty=0,
        )
        self.variant_c = Variant.objects.create(
            product=self.product_c,
            sku="C-001",
            volume="30 мл",
            purchase_price_uah=Decimal("300.00"),
            stock_qty=3,
        )

        self.product_a.filter_attrs.set([self.attr_35, self.attr_dry])
        self.product_b.filter_attrs.set([self.attr_35, self.attr_oily])
        self.product_c.filter_attrs.set([self.attr_dry])

        self.pro = User.objects.create_user(
            "cosmo@test.local", "Pass12345!", client_type=ClientType.COSMETOLOGIST
        )


class ParseCatalogFiltersTests(CatalogFiltersTestCase):
    def test_parses_known_attr_keys_and_ignores_unknown(self):
        request = self.factory.get(
            "/catalog/",
            {
                "age": ["35-plus"],
                "skin_type": ["dry", "oily"],
                "volume": ["30ml"],
                "brand": ["cure-skin"],
                "in_stock": "1",
                "price_min": "100",
                "price_max": "900",
                "sort": "new",
            },
        )
        parsed = selectors.parse_catalog_filters(request)
        self.assertEqual(parsed["brands"], ["cure-skin"])
        self.assertTrue(parsed["in_stock"])
        self.assertEqual(parsed["sort"], "new")
        self.assertEqual(parsed["price_min"], Decimal("100"))
        self.assertEqual(parsed["price_max"], Decimal("900"))
        self.assertEqual(parsed["attr_filters"]["age"], ["35-plus"])
        self.assertEqual(parsed["attr_filters"]["skin_type"], ["dry", "oily"])
        self.assertNotIn("volume", parsed["attr_filters"])


class FilterCatalogTests(CatalogFiltersTestCase):
    def test_or_within_group_and_and_across_groups(self):
        qs = selectors.filter_catalog(
            attr_filters={"age": ["35-plus"], "skin_type": ["dry", "oily"]}
        )
        slugs = set(qs.values_list("slug", flat=True))
        self.assertEqual(slugs, {"serum-a", "serum-b"})

    def test_and_excludes_partial_match(self):
        qs = selectors.filter_catalog(attr_filters={"age": ["35-plus"], "skin_type": ["dry"]})
        self.assertEqual(list(qs.values_list("slug", flat=True)), ["serum-a"])

    def test_in_stock(self):
        qs = selectors.filter_catalog(in_stock=True)
        self.assertEqual(set(qs.values_list("slug", flat=True)), {"serum-a", "serum-c"})

    def test_price_uses_sale_for_guest(self):
        self.variant_a.sale_price_uah = Decimal("700.00")
        self.variant_a.price_is_manual = True
        self.variant_a.price_uah = Decimal("1000.00")
        self.variant_a.save()

        qs = selectors.filter_catalog(price_min=Decimal("650"), price_max=Decimal("750"))
        self.assertEqual(list(qs.values_list("slug", flat=True)), ["serum-a"])

        qs_miss = selectors.filter_catalog(price_min=Decimal("900"), price_max=Decimal("1100"))
        self.assertNotIn("serum-a", qs_miss.values_list("slug", flat=True))

    def test_price_uses_pro_for_cosmetologist(self):
        self.variant_a.refresh_from_db()
        qs = selectors.filter_catalog(
            price_min=Decimal("650"),
            price_max=Decimal("750"),
            user=self.pro,
        )
        self.assertEqual(list(qs.values_list("slug", flat=True)), ["serum-a"])


class FilterGroupsAndResetTests(CatalogFiltersTestCase):
    def test_unused_attribute_hidden_from_sidebar(self):
        unused = ProductAttribute.objects.create(
            group=self.group_age, slug="60-plus", name_uk="60+", sort_order=99
        )
        groups = selectors.filter_groups_for_catalog()
        age_block = next(b for b in groups if b["group"].slug == "age")
        slugs = {a.slug for a in age_block["attributes"]}
        self.assertIn("35-plus", slugs)
        self.assertNotIn(unused.slug, slugs)

    def test_reset_url_keeps_search_query(self):
        request = self.factory.get("/search/")
        self.assertEqual(
            selectors.catalog_filters_reset_url(request, query="ніацинамід"),
            f"/search/?{urlencode({'q': 'ніацинамід'})}",
        )
        self.assertEqual(selectors.catalog_filters_reset_url(request, query=""), "/search/")
