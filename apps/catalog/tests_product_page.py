import json
import re
from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from apps.accounts.models import ClientType, User
from apps.catalog.models import Brand, Category, Product, ProductReview, Variant

_LD_JSON_RE = re.compile(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
    re.DOTALL,
)


class ProductPageTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="Cure Skin", slug="cure-skin")
        category = Category.objects.create(name_uk="Сироватки", slug="syrovatky")
        self.product = Product.objects.create(
            brand=brand,
            category=category,
            name_uk="Публічна сироватка",
            name_ru="Публичная сыворотка",
            slug="public-serum",
            is_active=True,
        )
        Variant.objects.create(
            product=self.product,
            sku="SERUM-30",
            volume="30 мл",
            purchase_price_uah=Decimal("100.00"),
            stock_qty=4,
        )
        self.brand = brand
        self.category = category
        self.pro = User.objects.create_user(
            "cosmo@test.local",
            "Pass12345!",
            client_type=ClientType.COSMETOLOGIST,
        )

    def _product_url(self, slug, language):
        with override(language):
            return reverse("catalog:product", kwargs={"slug": slug})

    def _product_json_ld(self, response):
        html = response.content.decode()
        for raw in _LD_JSON_RE.findall(html):
            data = json.loads(raw)
            if data.get("@type") == "Product":
                return data
        self.fail("JSON-LD Product не знайдено")

    def test_product_page_guest_uk_and_ru_ok_json_ld_url_strips_query(self):
        for language in ("uk", "ru"):
            path = self._product_url(self.product.slug, language)
            response = self.client.get(path, {"utm_source": "test"})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '"@type": "Product"')
            request = response.wsgi_request
            self.assertIn("utm_source=test", request.get_full_path())
            payload = self._product_json_ld(response)
            expected = f"{request.scheme}://{request.get_host()}{request.path}"
            self.assertEqual(payload["offers"]["url"], expected)
            self.assertNotIn("?", payload["offers"]["url"])

    def test_product_page_without_variants_ok(self):
        product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Без обʼєму",
            slug="no-variants",
            is_active=True,
        )
        response = self.client.get(self._product_url(product.slug, "uk"))
        self.assertEqual(response.status_code, 200)

    @override_settings(REVIEWS_ENABLED=True)
    def test_product_page_cosmetologist_with_reviews_enabled_ok(self):
        ProductReview.objects.create(
            product=self.product,
            user=self.pro,
            author_name="Олена",
            rating=5,
            text="Гарний засіб",
            is_published=True,
        )
        self.client.force_login(self.pro)
        response = self.client.get(self._product_url(self.product.slug, "uk"))
        self.assertEqual(response.status_code, 200)

    def test_all_project_templates_compile(self):
        from django.template.loader import get_template

        root = settings.BASE_DIR / "templates"
        paths = sorted(path for path in root.rglob("*.html") if path.is_file())
        self.assertTrue(paths)
        for path in paths:
            get_template(path.relative_to(root).as_posix())

    def test_inactive_and_missing_product_return_404(self):
        inactive = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name_uk="Прихований",
            slug="inactive-serum",
            is_active=False,
        )
        hidden = self.client.get(self._product_url(inactive.slug, "uk"))
        self.assertEqual(hidden.status_code, 404)
        missing = self.client.get(self._product_url("missing-product-slug", "uk"))
        self.assertEqual(missing.status_code, 404)
