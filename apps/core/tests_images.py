"""Тести WebP-конвертації та валідації ImageField каталогу."""
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.catalog.models import Brand, Category, Product, ProductImage
from apps.core.utils.images import validate_image


def _make_png(width: int = 100, height: int = 80, color=(200, 100, 50)) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return SimpleUploadedFile("test-photo.png", buf.getvalue(), content_type="image/png")


class ValidateImageTests(TestCase):
    def test_rejects_bad_extension(self):
        f = SimpleUploadedFile("shell.php", b"<?php", content_type="application/x-php")
        with self.assertRaises(ValidationError):
            validate_image(f)

    def test_accepts_png(self):
        validate_image(_make_png())


class WebpConvertOnSaveTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name_uk="Test Cat", slug="test-cat")
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            name_uk="Test Product",
            slug="test-product",
            category=self.category,
            brand=self.brand,
        )

    def test_product_image_becomes_webp(self):
        img = ProductImage.objects.create(
            product=self.product,
            image=_make_png(400, 300),
            is_main=True,
        )
        img.refresh_from_db()
        self.assertTrue(img.image.name.lower().endswith(".webp"))
        with Image.open(img.image.path) as opened:
            self.assertEqual(opened.format, "WEBP")
            self.assertEqual(opened.size, (400, 300))

    def test_category_image_becomes_webp(self):
        self.category.image = _make_png(320, 240)
        self.category.save()
        self.category.refresh_from_db()
        self.assertTrue(self.category.image.name.lower().endswith(".webp"))
        with Image.open(self.category.image.path) as opened:
            self.assertEqual(opened.format, "WEBP")

    def test_oversized_resized(self):
        img = ProductImage.objects.create(
            product=self.product,
            image=_make_png(2000, 1500),
        )
        img.refresh_from_db()
        with Image.open(img.image.path) as opened:
            self.assertEqual(opened.format, "WEBP")
            self.assertLessEqual(max(opened.size), 1200)
