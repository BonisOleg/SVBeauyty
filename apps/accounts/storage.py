import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage

_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def private_document_storage():
    root = settings.PRIVATE_MEDIA_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return FileSystemStorage(location=root, base_url=None)


def document_upload_to(instance, filename):
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        ext = ""
    return f"cosmetologist/{uuid.uuid4().hex}{ext}"
