from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.test import TestCase, override_settings
from django.urls import reverse


class FaviconTests(TestCase):
    def test_home_includes_favicon_variants(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, staticfiles_storage.url("favicons/favicon.ico"))
        self.assertContains(response, staticfiles_storage.url("favicons/favicon-16x16.png"))
        self.assertContains(response, staticfiles_storage.url("favicons/favicon-32x32.png"))
        self.assertContains(response, 'rel="apple-touch-icon"')
        self.assertContains(response, staticfiles_storage.url("favicons/apple-touch-icon.png"))
        self.assertContains(response, reverse("webmanifest"))

    def test_russian_home_includes_favicons(self):
        response = self.client.get("/ru/")
        self.assertContains(response, staticfiles_storage.url("favicons/favicon-32x32.png"))
        self.assertContains(response, staticfiles_storage.url("favicons/apple-touch-icon.png"))

    def test_500_template_includes_favicons(self):
        path = settings.BASE_DIR / "templates" / "core" / "500.html"
        self.assertIn('components/favicons.html', path.read_text())

    @override_settings(DEBUG=False)
    def test_404_includes_favicons(self):
        response = self.client.get("/uk/no-such-page-xyz/")
        self.assertContains(
            response,
            staticfiles_storage.url("favicons/favicon-32x32.png"),
            status_code=404,
        )
        self.assertContains(
            response,
            staticfiles_storage.url("favicons/apple-touch-icon.png"),
            status_code=404,
        )

    def test_root_favicon_redirects_to_ico(self):
        response = self.client.get(reverse("favicon"))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], staticfiles_storage.url("favicons/favicon.ico"))

    def test_favicon_and_manifest_accept_head(self):
        favicon = self.client.head(reverse("favicon"))
        self.assertEqual(favicon.status_code, 301)
        manifest = self.client.head(reverse("webmanifest"))
        self.assertEqual(manifest.status_code, 200)
        self.assertIn("application/manifest+json", manifest["Content-Type"])

    def test_webmanifest_lists_android_icons(self):
        response = self.client.get(reverse("webmanifest"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/manifest+json", response["Content-Type"])
        srcs = {icon["src"] for icon in response.json()["icons"]}
        self.assertIn(staticfiles_storage.url("favicons/android-chrome-192x192.png"), srcs)
        self.assertIn(staticfiles_storage.url("favicons/android-chrome-512x512.png"), srcs)

    def test_unfold_defines_favicon_variants(self):
        rels = [item["rel"] for item in settings.UNFOLD["SITE_FAVICONS"]]
        self.assertIn("icon", rels)
        self.assertIn("apple-touch-icon", rels)
        href = settings.UNFOLD["SITE_FAVICONS"][0]["href"]
        self.assertEqual(href(None), staticfiles_storage.url("favicons/favicon.ico"))
