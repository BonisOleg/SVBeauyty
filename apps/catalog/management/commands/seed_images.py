from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductImage
from apps.catalog.seed import images as generator
from apps.content.models import Banner, SiteSettings

IMAGES_PER_PRODUCT = 2


class Command(BaseCommand):
    help = "Генерує тестові зображення товарів, категорій і банерів (заглушки до реальних фото)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Перегенерувати навіть там, де зображення вже є",
        )

    def handle(self, *args, **options):
        force = options["force"]
        self.stdout.write(f"Товарів: {self._seed_products(force)}")
        self.stdout.write(f"Категорій: {self._seed_categories(force)}")
        self.stdout.write(f"Банерів: {self._seed_banners(force)}")
        self.stdout.write(self.style.SUCCESS("Тестові зображення готові"))

    def _seed_products(self, force: bool) -> int:
        count = 0
        for product in Product.objects.select_related("brand", "category").prefetch_related("variants"):
            if product.images.exists():
                if not force:
                    continue
                product.images.all().delete()

            variant = product.variants.first()
            volume = variant.volume if variant else ""
            for index in range(IMAGES_PER_PRODUCT):
                buffer = generator.product_image(
                    seed=f"{product.slug}",
                    category_slug=product.category.slug,
                    brand=product.brand.name,
                    title=product.name_uk,
                    volume=volume,
                    angle=index,
                )
                image = ProductImage(
                    product=product,
                    alt_uk=product.name_uk,
                    alt_ru=product.name_ru or product.name_uk,
                    is_main=index == 0,
                    sort_order=index,
                )
                image.image.save(f"{product.slug}-{index + 1}.jpg", ContentFile(buffer.read()), save=True)
                count += 1
        return count

    def _seed_categories(self, force: bool) -> int:
        count = 0
        for category in Category.objects.all():
            if category.image and not force:
                continue
            buffer = generator.category_image(seed=category.slug, slug=category.slug)
            category.image.save(f"{category.slug}.jpg", ContentFile(buffer.read()), save=True)
            count += 1
        return count

    def _seed_banners(self, force: bool) -> int:
        count = 0
        for banner in Banner.objects.all():
            if banner.image and not force:
                continue
            desktop = generator.banner_image(size=(1600, 620), layout="desktop")
            banner.image.save(f"banner-{banner.pk}.jpg", ContentFile(desktop.read()), save=True)

            mobile = generator.banner_image(size=(900, 900), layout="mobile")
            banner.image_mobile.save(
                f"banner-{banner.pk}-mobile.jpg", ContentFile(mobile.read()), save=True
            )
            count += 1

        settings_obj = SiteSettings.get_solo()
        if not settings_obj.logo:
            self.stdout.write("Логотип не заданий — використовується static/images/logo.png")
        return count
