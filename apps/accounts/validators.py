from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

ALLOWED_DOCUMENT_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_cosmetologist_document(uploaded_file):
    """Розмір + MIME + розширення для документа заявки косметолога."""
    if uploaded_file is None:
        return

    name = (getattr(uploaded_file, "name", "") or "").lower()
    extension = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    content_type = getattr(uploaded_file, "content_type", "") or ""

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            _("Дозволені формати: PDF, JPG, PNG, WEBP.")
        )
    if content_type and content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
        raise ValidationError(
            _("Тип файлу не підтримується. Завантажте PDF або зображення.")
        )
    if uploaded_file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError(
            _("Файл завеликий (макс. %(size)s).")
            % {"size": filesizeformat(MAX_DOCUMENT_SIZE)}
        )
