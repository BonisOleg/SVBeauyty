from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.chat.files import rules_text, save_attachments
from apps.chat.models import ChatMessage, ChatSession, MessageAuthor
from apps.chat.views import _attachment_public
from apps.core.admin_list_markers import unread_badge

MAX_REPLY_LENGTH = 2000
POLL_LIMIT = 200
DELETED_LABEL = _("Повідомлення видалено")
PREVIEW_LEN = 72


class UnreadMessagesFilter(admin.SimpleListFilter):
    title = _("Непрочитані")
    parameter_name = "unread"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Є нові")),
            ("no", _("Без нових")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(unread_ann__gt=0)
        if value == "no":
            return queryset.filter(unread_ann=0)
        return queryset


def _serialize_message(message: ChatMessage, *, viewer) -> dict:
    can_delete = bool(
        viewer
        and viewer.is_authenticated
        and message.author == MessageAuthor.MANAGER
        and not message.is_deleted
        and message.created_by_id == viewer.pk
    )
    files = []
    if not message.is_deleted:
        files = [_attachment_public(item) for item in message.attachments.all()]
    return {
        "id": message.id,
        "author": message.author,
        "author_label": message.get_author_display(),
        "text": str(DELETED_LABEL) if message.is_deleted else message.text,
        "time": date_format(timezone.localtime(message.created_at), "d.m.Y H:i"),
        "is_read": message.is_read,
        "is_deleted": message.is_deleted,
        "can_delete": can_delete,
        "attachments": files,
    }


def _unquote_object_id(object_id):
    from django.contrib.admin.utils import unquote

    return unquote(object_id)


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    change_form_template = "admin/chat/chatsession/change_form.html"
    list_display = [
        "session_title",
        "phone",
        "user",
        "unread_badge",
        "last_message_preview",
        "is_closed",
        "updated_at",
    ]
    list_filter = [UnreadMessagesFilter, "is_closed", "updated_at"]
    search_fields = ["name", "phone", "user__email", "messages__text"]
    readonly_fields = ["session_key", "user", "created_at", "updated_at"]
    fields = ["name", "phone", "user", "session_key", "is_closed", "created_at", "updated_at"]

    class Media:
        css = {"all": ("css/admin/chat.css",)}
        js = ("js/file-preview.js", "js/admin/chat-reply.js")

    def get_ordering(self, request):
        return ("-unread_ann", "-updated_at")

    def get_queryset(self, request):
        qs = self.model._default_manager.get_queryset()
        unread_q = Q(
            messages__author=MessageAuthor.CUSTOMER,
            messages__is_read=False,
            messages__is_deleted=False,
        )
        last_text = (
            ChatMessage.objects.filter(session_id=OuterRef("pk"), is_deleted=False)
            .order_by("-created_at")
            .values("text")[:1]
        )
        return qs.annotate(
            unread_ann=Count("messages", filter=unread_q, distinct=True),
            last_text_ann=Subquery(last_text),
        )

    @admin.display(description=_("Діалог"), ordering="name")
    def session_title(self, obj):
        title = str(obj)
        css = "admin-list-title"
        html = format_html('<span class="{}">{}</span>', css, title)
        if getattr(obj, "unread_ann", 0):
            return format_html('<span data-admin-new="1">{}</span>', html)
        return html

    @admin.display(description=_("Непрочитані"), ordering="unread_ann")
    def unread_badge(self, obj):
        return unread_badge(int(getattr(obj, "unread_ann", 0) or 0))

    @admin.display(description=_("Останнє повідомлення"))
    def last_message_preview(self, obj):
        raw = getattr(obj, "last_text_ann", None)
        if raw is None:
            return "—"
        text = raw.strip() or str(_("Вкладення"))
        if len(text) > PREVIEW_LEN:
            text = text[: PREVIEW_LEN - 1] + "…"
        unread = int(getattr(obj, "unread_ann", 0) or 0)
        css = "admin-list-preview admin-list-preview--unread" if unread else "admin-list-preview"
        return format_html('<span class="{}">{}</span>', css, text)

    def get_urls(self):
        opts = self.model._meta
        info = (opts.app_label, opts.model_name)
        custom = [
            path(
                "<path:object_id>/messages/",
                self.admin_site.admin_view(self.messages_view),
                name="%s_%s_messages" % info,
            ),
            path(
                "<path:object_id>/reply/",
                self.admin_site.admin_view(self.reply_view),
                name="%s_%s_reply" % info,
            ),
            path(
                "<path:object_id>/messages/<int:message_id>/delete/",
                self.admin_site.admin_view(self.delete_message_view),
                name="%s_%s_delete_message" % info,
            ),
        ]
        return custom + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, _unquote_object_id(object_id))
        extra_context = extra_context or {}
        if obj is not None:
            obj.messages.filter(author=MessageAuthor.CUSTOMER, is_read=False).update(is_read=True)
            extra_context.update(
                {
                    "chat_thread_enabled": True,
                    "chat_messages_url": reverse(
                        "admin:chat_chatsession_messages", args=[obj.pk]
                    ),
                    "chat_reply_url": reverse("admin:chat_chatsession_reply", args=[obj.pk]),
                    "chat_delete_url_template": reverse(
                        "admin:chat_chatsession_delete_message",
                        args=[obj.pk, 0],
                    ).replace("/0/delete/", "/{id}/delete/"),
                }
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def messages_view(self, request, object_id):
        if request.method != "GET":
            return JsonResponse({"error": "method"}, status=405)
        session = self._get_session_for_staff(request, object_id)
        qs = session.messages.prefetch_related("attachments").order_by("created_at")[:POLL_LIMIT]
        messages_list = list(qs)
        unread_ids = [
            m.pk for m in messages_list if m.author == MessageAuthor.CUSTOMER and not m.is_read
        ]
        if unread_ids:
            ChatMessage.objects.filter(pk__in=unread_ids).update(is_read=True)
        return JsonResponse(
            {"messages": [_serialize_message(m, viewer=request.user) for m in messages_list]}
        )

    def reply_view(self, request, object_id):
        if request.method != "POST":
            return JsonResponse({"error": "method"}, status=405)
        session = self._get_session_for_staff(request, object_id)
        text = (request.POST.get("text") or "").strip()[:MAX_REPLY_LENGTH]
        uploads = request.FILES.getlist("files")
        if not text and not uploads:
            return JsonResponse(
                {"error": str(_("Напишіть відповідь або додайте файл. %(rules)s") % {"rules": rules_text()})},
                status=400,
            )
        if session.is_closed:
            return JsonResponse({"error": str(_("Діалог закрито."))}, status=400)

        try:
            with transaction.atomic():
                message = ChatMessage.objects.create(
                    session=session,
                    author=MessageAuthor.MANAGER,
                    text=text,
                    is_read=True,
                    created_by=request.user,
                )
                if uploads:
                    save_attachments(message, uploads)
        except ValidationError as exc:
            return JsonResponse({"error": " ".join(exc.messages)}, status=400)
        ChatSession.objects.filter(pk=session.pk).update(updated_at=timezone.now())
        return JsonResponse({"message": _serialize_message(message, viewer=request.user)})

    def delete_message_view(self, request, object_id, message_id):
        if request.method != "POST":
            return JsonResponse({"error": "method"}, status=405)
        session = self._get_session_for_staff(request, object_id)
        message = get_object_or_404(ChatMessage, pk=message_id, session=session)
        if (
            message.author != MessageAuthor.MANAGER
            or message.created_by_id != request.user.pk
            or message.is_deleted
        ):
            return JsonResponse(
                {"error": str(_("Можна видалити лише власне повідомлення менеджера."))},
                status=403,
            )
        message.soft_delete()
        ChatSession.objects.filter(pk=session.pk).update(updated_at=timezone.now())
        return JsonResponse({"message": _serialize_message(message, viewer=request.user)})

    def _get_session_for_staff(self, request, object_id) -> ChatSession:
        session = get_object_or_404(ChatSession, pk=_unquote_object_id(object_id))
        if not self.has_change_permission(request, session):
            raise PermissionDenied
        return session
