import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from apps.chat.models import ChatMessage, ChatSession, MessageAuthor
from apps.chat.notifications import notify_new_message

MAX_LENGTH = 2000
AUTO_REPLY = _(
    "Дякуємо! Повідомлення отримано. Менеджер відповість у робочі години."
)


def _get_session(request, create: bool = True) -> ChatSession | None:
    if not request.session.session_key:
        if not create:
            return None
        request.session.create()
    key = request.session.session_key
    user = request.user if request.user.is_authenticated else None

    session = ChatSession.objects.filter(session_key=key, is_closed=False).first()
    if session is None and user:
        session = ChatSession.objects.filter(user=user, is_closed=False).order_by("-updated_at").first()
    if session is None and create:
        session = ChatSession.objects.create(
            session_key=key,
            user=user,
            name=user.display_name if user else "",
            phone=getattr(user, "phone", "") or "",
        )
    if session and user and session.user_id is None:
        session.user = user
        session.save(update_fields=["user", "updated_at"])
    return session


def _serialize(message: ChatMessage) -> dict:
    return {
        "id": message.id,
        "author": message.author,
        "text": message.text,
        "time": date_format(timezone.localtime(message.created_at), "H:i"),
    }


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


@require_GET
def history(request):
    session = _get_session(request, create=False)
    if session is None:
        return JsonResponse({"messages": []})
    messages = session.messages.order_by("created_at")[:200]
    return JsonResponse({"messages": [_serialize(m) for m in messages]})


@require_POST
def send(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = request.POST

    text = (payload.get("text") or "").strip()[:MAX_LENGTH]
    if not text:
        if _is_htmx(request):
            return HttpResponse("", status=400)
        return JsonResponse({"error": "empty"}, status=400)

    session = _get_session(request)
    name = (payload.get("name") or "").strip()[:120]
    phone = (payload.get("phone") or "").strip()[:32]
    updates = []
    if name and not session.name:
        session.name = name
        updates.append("name")
    if phone and not session.phone:
        session.phone = phone
        updates.append("phone")
    if updates:
        session.save(update_fields=[*updates, "updated_at"])

    message = ChatMessage.objects.create(session=session, author=MessageAuthor.CUSTOMER, text=text)
    notify_new_message(message)

    if _is_htmx(request):
        now = timezone.localtime()
        return render(
            request,
            "chat/_message_sent.html",
            {
                "message": message,
                "message_time": date_format(now, "H:i"),
                "auto_reply": AUTO_REPLY,
                "reply_time": date_format(now, "H:i"),
            },
        )

    return JsonResponse({"message": _serialize(message)})
