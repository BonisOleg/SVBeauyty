from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category
from apps.content.models import Page
from apps.core.views import HOME_CATEGORIES_LIMIT

CREDIT_URL = "https://www.prometeylabs.com/internet-shop-v2/"


class FooterDeveloperLinkTests(TestCase):
    def test_home_has_nofollow_credit_link(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, "nofollow")
        self.assertContains(response, "footer__credit-link")
        self.assertContains(response, "footer__credit-prometey")
        self.assertContains(response, "footer__credit-labs")
        self.assertContains(response, "Prometey")
        self.assertContains(response, "Labs")

    def test_localized_home_keeps_credit_link(self):
        for path in ("/uk/", "/ru/"):
            response = self.client.get(path)
            self.assertContains(response, CREDIT_URL)
            self.assertContains(response, 'rel="nofollow noopener noreferrer"')

    def test_inner_pages_show_credit_without_link(self):
        Page.objects.create(
            slug="pro-nas",
            title_uk="Про нас",
            title_ru="О нас",
            is_active=True,
        )
        for url in (reverse("content:page", args=["pro-nas"]), reverse("catalog:catalog")):
            response = self.client.get(url)
            self.assertContains(response, "Prometey")
            self.assertContains(response, "Labs")
            self.assertNotContains(response, CREDIT_URL)
            self.assertNotContains(response, "footer__credit-link")


class HomeCategoriesLimitTests(TestCase):
    def test_home_shows_at_most_eight_categories(self):
        for index in range(HOME_CATEGORIES_LIMIT + 3):
            Category.objects.create(
                name_uk=f"Кат {index}",
                slug=f"kat-{index}",
                is_active=True,
                sort_order=index,
            )
        response = self.client.get(reverse("core:home"))
        self.assertEqual(len(response.context["categories"]), HOME_CATEGORIES_LIMIT)
