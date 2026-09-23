from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import ClientType, User
from apps.catalog.models import Brand, Category, Product, Variant, WishlistItem
from apps.seo.sitemaps import ProductSitemap


class ProOnlyProductTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="Cure Skin", slug="cure-skin")
        category = Category.objects.create(name_uk="Сироватки", slug="syrovatky")
        self.public = Product.objects.create(
            brand=brand,
            category=category,
            name_uk="Публічна сироватка",
            slug="public-serum",
            is_active=True,
            is_hit=True,
        )
        self.secret = Product.objects.create(
            brand=brand,
            category=category,
            name_uk="Професійний пілінг",
            slug="pro-peel",
            is_active=True,
            is_hit=True,
            pro_only=True,
        )
        self.variant = Variant.objects.create(
            product=self.secret,
            sku="PRO-1",
            volume="30 мл",
            purchase_price_uah=Decimal("100.00"),
            stock_qty=4,
        )
        self.regular = User.objects.create_user("client@test.local", "Pass12345!")
        self.pending = User.objects.create_user(
            "pending@test.local",
            "Pass12345!",
            client_type=ClientType.PENDING,
        )
        self.pro = User.objects.create_user(
            "cosmo@test.local",
            "Pass12345!",
            client_type=ClientType.COSMETOLOGIST,
        )

    def test_guest_regular_and_pending_do_not_see_pro_product(self):
        catalog_url = reverse("catalog:catalog")
        product_url = reverse("catalog:product", kwargs={"slug": self.secret.slug})
        home_url = reverse("core:home")
        for user in (None, self.regular, self.pending):
            if user:
                self.client.force_login(user)
            else:
                self.client.logout()
            catalog = self.client.get(catalog_url)
            self.assertNotContains(catalog, self.secret.name_uk)
            self.assertContains(catalog, self.public.name_uk)
            self.assertEqual(self.client.get(product_url).status_code, 404)
            home = self.client.get(home_url)
            self.assertNotContains(home, self.secret.name_uk)

    def test_cosmetologist_sees_pro_product(self):
        self.client.force_login(self.pro)
        catalog = self.client.get(reverse("catalog:catalog"))
        self.assertContains(catalog, self.secret.name_uk)
        page = self.client.get(reverse("catalog:product", kwargs={"slug": self.secret.slug}))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, self.secret.name_uk)

    def test_search_hides_pro_product_from_guest(self):
        response = self.client.get(reverse("catalog:search"), {"q": "пілінг"})
        self.assertNotContains(response, self.secret.name_uk)
        suggest = self.client.get(reverse("catalog:search_suggest"), {"q": "пілінг"})
        self.assertEqual(suggest.json()["results"], [])

    def test_guest_cannot_add_pro_product_to_cart(self):
        response = self.client.post(
            reverse("commerce:cart_add"),
            {"variant_id": self.variant.id, "quantity": 1},
        )
        self.assertEqual(response.status_code, 404)

    def test_pro_product_is_absent_from_sitemap(self):
        slugs = [item.slug for item in ProductSitemap().items()]
        self.assertIn(self.public.slug, slugs)
        self.assertNotIn(self.secret.slug, slugs)

    def test_wishlist_hides_pro_product_from_regular(self):
        WishlistItem.objects.create(user=self.regular, product=self.secret)
        WishlistItem.objects.create(user=self.pro, product=self.secret)
        self.client.force_login(self.regular)
        page = self.client.get(reverse("accounts:wishlist"))
        self.assertNotContains(page, self.secret.name_uk)
        self.client.force_login(self.pro)
        page = self.client.get(reverse("accounts:wishlist"))
        self.assertContains(page, self.secret.name_uk)
