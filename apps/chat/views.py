import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.http import content_disposition_header
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from apps.chat.business_hours import is_within_business_hours
from apps.chat.files import rules_text, save_attachments
from apps.chat.models import ChatAttachment, ChatMessage, ChatSession, MessageAuthor
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


def _attachment_public(attachment: ChatAttachment) -> dict:
    return {
        "name": attachment.original_name,
        "kind": attachment.kind,
        "url": reverse("chat:file", args=[attachment.public_id]),
    }


def _serialize(message: ChatMessage) -> dict:
    deleted = bool(message.is_deleted)
    files = []
    if not deleted:
        files = [_attachment_public(item) for item in message.attachments.all()]
    return {
        "id": message.id,
        "author": message.author,
        "text": str(_("Повідомлення видалено")) if deleted else message.text,
        "is_deleted": deleted,
        "time": date_format(timezone.localtime(message.created_at), "H:i"),
        "attachments": files,
    }


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


@require_GET
def history(request):
    session = _get_session(request, create=False)
    needs_contacts = _guest_needs_contacts(request, session)
    if session is None:
        response = JsonResponse({"messages": [], "needs_contacts": needs_contacts})
    else:
        messages = session.messages.prefetch_related("attachments").order_by("created_at")[:200]
        response = JsonResponse(
            {
                "messages": [_serialize(m) for m in messages],
                "needs_contacts": needs_contacts,
            }
        )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


def _guest_needs_contacts(request, session: ChatSession | None) -> bool:
    if request.user.is_authenticated:
        return False
    if session is None:
        return True
    return not (bool(session.name and session.name.strip()) and bool(session.phone and session.phone.strip()))


def _maybe_auto_reply(session: ChatSession, customer_message: ChatMessage) -> ChatMessage | None:
    """Автовідповідь: лише на перше повідомлення клієнта і лише поза графіком."""
    prior_customer = (
        session.messages.filter(author=MessageAuthor.CUSTOMER)
        .exclude(pk=customer_message.pk)
        .exists()
    )
    if prior_customer:
        return None
    if is_within_business_hours():
        return None
    return ChatMessage.objects.create(
        session=session,
        author=MessageAuthor.MANAGER,
        text=str(AUTO_REPLY),
        is_read=True,
    )


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
    uploads = request.FILES.getlist("files")
    if not text and not uploads:
        error = _("Напишіть повідомлення або додайте файл. %(rules)s") % {"rules": rules_text()}
        if _is_htmx(request):
            return HttpResponse(str(error), status=400)
        return JsonResponse({"error": "empty", "detail": str(error)}, status=400)

    session = _get_session(request)
    name = (payload.get("name") or "").strip()[:120]
    phone = (payload.get("phone") or "").strip()[:32]

    if _guest_needs_contacts(request, session):
        if not name or not phone:
            error = _("Вкажіть імʼя та телефон перед першим повідомленням.")
            if _is_htmx(request):
                return HttpResponse(str(error), status=400)
            return JsonResponse({"error": "contacts_required", "detail": str(error)}, status=400)
        session.name = name
        session.phone = phone
        session.save(update_fields=["name", "phone", "updated_at"])
    else:
        updates = []
        if name and not session.name:
            session.name = name
            updates.append("name")
        if phone and not session.phone:
            session.phone = phone
            updates.append("phone")
        if updates:
            session.save(update_fields=[*updates, "updated_at"])

    try:
        with transaction.atomic():
            message = ChatMessage.objects.create(
                session=session, author=MessageAuthor.CUSTOMER, text=text
            )
            if uploads:
                save_attachments(message, uploads)
    except ValidationError as exc:
        error = " ".join(exc.messages)
        if _is_htmx(request):
            return HttpResponse(error, status=400)
        return JsonResponse({"error": "file", "detail": error}, status=400)
    notify_new_message(message)
    reply = _maybe_auto_reply(session, message)

    if _is_htmx(request):
        now = timezone.localtime()
        return render(
            request,
            "chat/_message_sent.html",
            {
                "message": message,
                "message_time": date_format(now, "H:i"),
                "reply_message": reply,
                "reply_time": date_format(timezone.localtime(reply.created_at), "H:i") if reply else "",
            },
        )

    payload_out = {"message": _serialize(message), "needs_contacts": False}
    if reply:
        payload_out["auto_reply"] = _serialize(reply)
    return JsonResponse(payload_out)


def _can_read_attachment(request, attachment: ChatAttachment) -> bool:
    session = attachment.message.session
    user = request.user
    if user.is_authenticated and user.is_staff:
        return True
    if user.is_authenticated and session.user_id == user.pk:
        return True
    key = request.session.session_key
    return bool(key and session.session_key == key)


@require_GET
def attachment_file(request, public_id):
    attachment = (
        ChatAttachment.objects.select_related("message__session")
        .filter(public_id=public_id, message__is_deleted=False)
        .first()
    )
    if attachment is None or not attachment.file or not _can_read_attachment(request, attachment):
        raise Http404
    content_type = "image/webp" if attachment.kind == "image" else "application/pdf"
    as_attachment = request.GET.get("download") == "1"
    response = FileResponse(attachment.file.open("rb"), content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(as_attachment, attachment.original_name)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
