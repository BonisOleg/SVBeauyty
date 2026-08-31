from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe


@require_safe
@cache_control(max_age=86400)
def favicon_redirect(request):
    return redirect(static("favicons/favicon.ico"), permanent=True)


@require_safe
@cache_control(max_age=86400)
def site_webmanifest(request):
    return JsonResponse(
        {
            "name": "SVbeauty",
            "short_name": "SVbeauty",
            "icons": [
                {
                    "src": static("favicons/android-chrome-192x192.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": static("favicons/android-chrome-512x512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                },
            ],
            "theme_color": "#1A1A1A",
            "background_color": "#ffffff",
            "display": "browser",
        },
        content_type="application/manifest+json",
    )


@cache_control(max_age=86400)
def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /cabinet/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /chat/",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
