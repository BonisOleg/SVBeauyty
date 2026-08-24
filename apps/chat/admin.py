from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.chat.models import ChatMessage, ChatSession, MessageAuthor


class ChatMessageInline(TabularInline):
    model = ChatMessage
    extra = 1
    fields = ["author", "text", "is_read", "created_at"]
    readonly_fields = ["created_at"]

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields["author"].initial = MessageAuthor.MANAGER
        return formset


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    list_display = ["__str__", "phone", "user", "unread_count", "is_closed", "updated_at"]
    list_filter = ["is_closed", "updated_at"]
    search_fields = ["name", "phone", "user__email", "messages__text"]
    inlines = [ChatMessageInline]
    readonly_fields = ["session_key", "user", "created_at", "updated_at"]

    @admin.display(description="Непрочитані")
    def unread_count(self, obj):
        return obj.unread_count

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is ChatMessage:
            form.instance.messages.filter(author=MessageAuthor.CUSTOMER, is_read=False).update(is_read=True)
