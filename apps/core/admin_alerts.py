"""Лічильники нових замовлень / заявок / непрочитаних повідомлень для адмінки."""

from __future__ import annotations

from django.db.models import Count, Max, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from apps.accounts.models import CosmetologistRequest, RequestStatus
from apps.chat.models import ChatMessage, ChatSession, MessageAuthor
from apps.commerce.models import Order, OrderStatus

ALERT_LIMIT = 5


def count_new_orders() -> int:
    return Order.objects.filter(status=OrderStatus.NEW).count()


def count_new_requests() -> int:
    return CosmetologistRequest.objects.filter(status=RequestStatus.NEW).count()


def count_unread_messages() -> int:
    return ChatMessage.objects.filter(
        author=MessageAuthor.CUSTOMER,
        is_read=False,
        is_deleted=False,
    ).count()


def get_alert_counts() -> dict[str, int]:
    orders = count_new_orders()
    requests = count_new_requests()
    messages = count_unread_messages()
    return {
        "orders": orders,
        "requests": requests,
        "messages": messages,
        "total": orders + requests + messages,
    }


def badge_orders(request) -> int:  # noqa: ARG001 — Unfold badge API
    return count_new_orders()


def badge_requests(request) -> int:  # noqa: ARG001
    return count_new_requests()


def badge_messages(request) -> int:  # noqa: ARG001
    return count_unread_messages()


def _fmt_dt(value) -> str:
    if not value:
        return ""
    return date_format(timezone.localtime(value), "d.m.Y H:i")


def _orders_feed(limit: int = ALERT_LIMIT) -> list[dict]:
    qs = Order.objects.filter(status=OrderStatus.NEW).order_by("-created_at")[:limit]
    items = []
    for order in qs:
        items.append(
            {
                "id": order.pk,
                "title": f"№{order.number}",
                "meta": f"{order.first_name} {order.last_name}".strip() or order.phone,
                "time": _fmt_dt(order.created_at),
                "url": reverse("admin:commerce_order_change", args=[order.pk]),
            }
        )
    return items


def _requests_feed(limit: int = ALERT_LIMIT) -> list[dict]:
    qs = CosmetologistRequest.objects.filter(status=RequestStatus.NEW).order_by("-created_at")[
        :limit
    ]
    items = []
    for req in qs:
        items.append(
            {
                "id": req.pk,
                "title": req.full_name,
                "meta": req.phone,
                "time": _fmt_dt(req.created_at),
                "url": reverse("admin:accounts_cosmetologistrequest_change", args=[req.pk]),
            }
        )
    return items


def _messages_feed(limit: int = ALERT_LIMIT) -> list[dict]:
    unread_q = Q(
        messages__author=MessageAuthor.CUSTOMER,
        messages__is_read=False,
        messages__is_deleted=False,
    )
    qs = (
        ChatSession.objects.filter(unread_q)
        .annotate(
            unread=Count(
                "messages",
                filter=Q(
                    messages__author=MessageAuthor.CUSTOMER,
                    messages__is_read=False,
                    messages__is_deleted=False,
                ),
            ),
            last_unread_at=Max(
                "messages__created_at",
                filter=Q(
                    messages__author=MessageAuthor.CUSTOMER,
                    messages__is_read=False,
                    messages__is_deleted=False,
                ),
            ),
        )
        .filter(unread__gt=0)
        .order_by("-last_unread_at")[:limit]
    )
    items = []
    for session in qs:
        label = session.name or session.phone or f"#{session.pk}"
        items.append(
            {
                "id": session.pk,
                "title": label,
                "meta": f"{session.unread} непрочит.",
                "time": _fmt_dt(session.last_unread_at),
                "url": reverse("admin:chat_chatsession_change", args=[session.pk]),
            }
        )
    return items


def get_alerts_payload() -> dict:
    counts = get_alert_counts()
    return {
        **counts,
        "links": {
            "orders": reverse("admin:commerce_order_changelist") + "?status__exact=new",
            "requests": reverse("admin:accounts_cosmetologistrequest_changelist")
            + "?status__exact=new",
            "messages": reverse("admin:chat_chatsession_changelist"),
        },
        "feed": {
            "orders": _orders_feed(),
            "requests": _requests_feed(),
            "messages": _messages_feed(),
        },
    }
