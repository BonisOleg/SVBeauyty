from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_chat_storage():
    root = settings.PRIVATE_MEDIA_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return FileSystemStorage(location=root, base_url=None)


def chat_upload_to(instance, filename):
    ext = "webp" if instance.kind == "image" else "pdf"
    return f"chat/{instance.public_id}.{ext}"
