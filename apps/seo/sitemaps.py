from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.content.models import Page


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    i18n = True

    def items(self):
        return ["core:home", "catalog:catalog"]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    i18n = True

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    i18n = True
    limit = 2000

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4
    i18n = True

    def items(self):
        return Page.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
    "pages": PageSitemap,
}
