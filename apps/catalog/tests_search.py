from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from apps.catalog import selectors
from apps.catalog.models import Brand, Category, Product, Variant


class SearchProductsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(name="Cure Skin", slug="cure-skin")
        cls.other_brand = Brand.objects.create(name="Great Care", slug="great-care")
        cls.category = Category.objects.create(
            name_uk="Сироватки", name_ru="Сыворотки", slug="syrovatky"
        )
        cls.peels = Category.objects.create(
            name_uk="Пілінги", name_ru="Пилинги", slug="pilinh"
        )
        cls.product = Product.objects.create(
            brand=cls.brand,
            category=cls.category,
            name_uk="Сироватка з ніацинамідом",
            name_ru="Сыворотка с ниацинамидом",
            short_description_uk="Для пор і сяйва",
            slug="syrovatka-niacynamid",
            is_active=True,
        )
        Variant.objects.create(
            product=cls.product,
            sku="SV-NIAC-30",
            volume="30 мл",
            purchase_price_uah=Decimal("100.00"),
            stock_qty=5,
        )
        cls.other = Product.objects.create(
            brand=cls.other_brand,
            category=cls.peels,
            name_uk="Ензимний пілінг",
            slug="enzymnyi-pilinh",
            is_active=True,
        )
        Variant.objects.create(
            product=cls.other,
            sku="SV-PEEL-50",
            volume="50 мл",
            purchase_price_uah=Decimal("120.00"),
            stock_qty=3,
        )

    def test_normalize_collapses_whitespace(self):
        self.assertEqual(selectors.normalize_search_query("  а  б  "), "а б")

    def test_short_query_returns_empty(self):
        self.assertEqual(selectors.search_products("н").count(), 0)
        self.assertEqual(selectors.search_products("").count(), 0)

    def test_search_by_name_uk(self):
        qs = selectors.search_products("ніацинамід")
        self.assertEqual(list(qs), [self.product])

    def test_search_by_sku(self):
        qs = selectors.search_products("SV-NIAC-30")
        self.assertEqual(list(qs), [self.product])

    def test_search_by_brand(self):
        qs = selectors.search_products("Cure Skin")
        self.assertIn(self.product, qs)

    def test_search_by_category(self):
        qs = selectors.search_products("Сироватки")
        self.assertIn(self.product, qs)

    def test_sku_ranks_above_partial_name(self):
        named = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Крем SV-NIAC-30",
            slug="krem-sv-niac",
            is_active=True,
        )
        Variant.objects.create(
            product=named,
            sku="OTHER-1",
            volume="50 мл",
            purchase_price_uah=Decimal("90.00"),
            stock_qty=1,
        )
        ranked = list(selectors.search_products("SV-NIAC-30"))
        self.assertEqual(ranked[0], self.product)

    def test_suggest_endpoint(self):
        client = Client()
        response = client.get(reverse("catalog:search_suggest"), {"q": "ніацин"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item["id"] == self.product.pk for item in data["results"]))

    def test_search_page_short_query_message(self):
        client = Client()
        response = client.get(reverse("catalog:search"), {"q": "н"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "щонайменше 2")

    def test_search_page_empty_query_message(self):
        client = Client()
        response = client.get(reverse("catalog:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Введіть запит для пошуку")
