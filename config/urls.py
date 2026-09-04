from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path

from apps.seo.sitemaps import SITEMAPS
from apps.seo.views import favicon_redirect, robots_txt, site_webmanifest

urlpatterns = [
    path("healthz/", lambda request: HttpResponse("ok"), name="healthz"),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("favicon.ico", favicon_redirect, name="favicon"),
    path("site.webmanifest", site_webmanifest, name="webmanifest"),
    path("chat/", include("apps.chat.urls")),
    path("shipping/", include("apps.shipping.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("apps.core.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.commerce.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.content.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"
