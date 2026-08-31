import re

from django import template
from django.utils.html import escape, linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

_HTML_RE = re.compile(r"</?[a-zA-Z][^>]*>")


@register.filter(name="richtext", is_safe=True)
def richtext(value):
    """HTML з WYSIWYG — як є; звичайний текст — з переносами рядків."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if _HTML_RE.search(text):
        return mark_safe(text)
    # django.utils.html.linebreaks завжди повертає SafeString
    return mark_safe(linebreaks(escape(text)))
