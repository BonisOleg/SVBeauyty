from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Зберігає поточні GET-параметри й підмінює лише передані."""
    request = context.get("request")
    params = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    return f"?{params.urlencode()}" if params else ""


@register.simple_tag(takes_context=True)
def switch_language_url(context, language_code):
    request = context.get("request")
    if not request:
        return "/"
    path = request.path
    parts = path.split("/", 2)
    rest = parts[2] if len(parts) > 2 else ""
    url = f"/{language_code}/{rest}"
    if request.GET:
        url = f"{url}?{urlencode(request.GET, doseq=True)}"
    return url


@register.simple_tag(takes_context=True)
def language_absolute_url(context, language_code):
    """Абсолютний URL без query — для hreflang / canonical."""
    request = context.get("request")
    if not request:
        return f"/{language_code}/"
    path = request.path
    parts = path.split("/", 2)
    rest = parts[2] if len(parts) > 2 else ""
    path_lang = f"/{language_code}/{rest}"
    return request.build_absolute_uri(path_lang)


@register.filter
def field_type(field):
    return field.field.widget.__class__.__name__.lower()
