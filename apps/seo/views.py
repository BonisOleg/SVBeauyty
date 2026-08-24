from django.http import HttpResponse
from django.views.decorators.cache import cache_control


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
