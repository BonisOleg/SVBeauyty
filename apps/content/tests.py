from django.test import TestCase
from django.utils import translation
from django.utils.safestring import SafeData

from apps.content.models import Banner, Page, SiteSettings
from apps.content.templatetags.content_tags import richtext
from apps.core.utils import localize_path


class SiteSettingsCopyTests(TestCase):
    def setUp(self):
        self.settings_obj = SiteSettings.get_solo()
        self.settings_obj.slogan_uk = "Слоган УК"
        self.settings_obj.slogan_ru = "Слоган РУ"
        self.settings_obj.meta_description_uk = "Meta УК"
        self.settings_obj.meta_description_ru = "Meta РУ"
        self.settings_obj.pro_cta_title_uk = "Косметолог УК"
        self.settings_obj.pro_cta_title_ru = "Косметолог РУ"
        self.settings_obj.usp1_title_uk = "USP1 УК"
        self.settings_obj.usp1_title_ru = "USP1 РУ"
        self.settings_obj.save()

    def test_localized_properties_switch_language(self):
        with translation.override("uk"):
            self.assertEqual(self.settings_obj.slogan, "Слоган УК")
            self.assertEqual(self.settings_obj.meta_description, "Meta УК")
            self.assertEqual(self.settings_obj.pro_cta_title, "Косметолог УК")
            self.assertEqual(self.settings_obj.usp_items()[0]["title"], "USP1 УК")
        with translation.override("ru"):
            self.assertEqual(self.settings_obj.slogan, "Слоган РУ")
            self.assertEqual(self.settings_obj.meta_description, "Meta РУ")
            self.assertEqual(self.settings_obj.pro_cta_title, "Косметолог РУ")
            self.assertEqual(self.settings_obj.usp_items()[0]["title"], "USP1 РУ")

    def test_home_and_footer_render_admin_copy(self):
        response = self.client.get("/uk/")
        self.assertContains(response, "Слоган УК")
        self.assertContains(response, "Meta УК")
        self.assertContains(response, "Косметолог УК")
        self.assertContains(response, "USP1 УК")

        response_ru = self.client.get("/ru/")
        self.assertContains(response_ru, "Слоган РУ")
        self.assertContains(response_ru, "Meta РУ")
        self.assertContains(response_ru, "Косметолог РУ")
        self.assertContains(response_ru, "USP1 РУ")


class RichtextFilterTests(TestCase):
    def test_plain_text_becomes_safe_paragraphs(self):
        out = richtext("Рядок один\n\nРядок два")
        self.assertIsInstance(out, SafeData)
        self.assertIn("<p>", out)
        self.assertNotIn("&lt;p&gt;", out)

    def test_html_passthrough_is_safe(self):
        out = richtext("<p><strong>Жирний</strong> текст</p>")
        self.assertIsInstance(out, SafeData)
        self.assertIn("<strong>Жирний</strong>", out)

    def test_cms_page_renders_html_not_escaped_tags(self):
        Page.objects.create(
            title_uk="Тест",
            title_ru="Тест",
            slug="test-rich",
            body_uk="<p>Абзац з <strong>жирним</strong></p>",
            body_ru="<p>Абзац</p>",
            is_active=True,
            sort_order=99,
        )
        response = self.client.get("/uk/page/test-rich/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>жирним</strong>", html=False)
        self.assertNotContains(response, "&lt;p&gt;")
        self.assertNotContains(response, "&lt;strong&gt;")


class BannerButtonUrlTests(TestCase):
    def test_localize_path_adds_and_rewrites_prefix(self):
        self.assertEqual(localize_path("/catalog/syrovatky/", "uk"), "/uk/catalog/syrovatky/")
        self.assertEqual(localize_path("/catalog/syrovatky/", "ru"), "/ru/catalog/syrovatky/")
        self.assertEqual(localize_path("/uk/catalog/syrovatky/", "ru"), "/ru/catalog/syrovatky/")
        self.assertEqual(localize_path("/ru/catalog/", "uk"), "/uk/catalog/")
        self.assertEqual(localize_path("https://example.com/x", "ru"), "https://example.com/x")

    def test_banner_href_follows_active_language(self):
        banner = Banner.objects.create(
            title_uk="Банер",
            title_ru="Баннер",
            button_text_uk="Дивитись",
            button_text_ru="Смотреть",
            button_url="/catalog/syrovatky/",
            is_active=True,
            sort_order=1,
        )
        with translation.override("uk"):
            self.assertEqual(banner.button_href, "/uk/catalog/syrovatky/")
        with translation.override("ru"):
            self.assertEqual(banner.button_href, "/ru/catalog/syrovatky/")

    def test_legacy_uk_prefix_in_db_still_rewrites_on_ru(self):
        banner = Banner.objects.create(
            title_uk="Банер",
            button_url="/uk/catalog/syrovatky/",
            is_active=True,
            sort_order=2,
        )
        with translation.override("ru"):
            self.assertEqual(banner.button_href, "/ru/catalog/syrovatky/")
