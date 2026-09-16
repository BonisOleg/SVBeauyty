"""Маркери «нове» для changelist адмінки."""

from django.utils.html import format_html
from django.utils.translation import gettext as _


def list_badge(text: str, *, tone: str = "new") -> str:
    return format_html(
        '<span class="admin-list-badge admin-list-badge--{}">{}</span>',
        tone,
        text,
    )


def mark_new(inner_html: str) -> str:
    """Обгортка для :has([data-admin-new]) підсвітки рядка."""
    return format_html('<span data-admin-new="1">{}</span>', inner_html)


def new_badge() -> str:
    return list_badge(_("Нове"), tone="new")


def unread_badge(count: int) -> str:
    if count <= 0:
        return "—"
    label = _("%(n)s нових") % {"n": count}
    return mark_new(list_badge(label, tone="unread"))
