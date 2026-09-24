"""Вкладення чату: JPEG/PNG/WebP/PDF, до 3 файлів по 5 МБ, картинки → WebP."""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _
from PIL import Image, ImageOps

MAX_FILES = 3
MAX_BYTES = 5 * 1024 * 1024
MAX_SIDE = 1600
WEBP_QUALITY = 85
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PDF_EXT = {".pdf"}


def rules_text() -> str:
    return _(
        "До 3 файлів: JPEG, PNG, WebP або PDF, кожен до 5 МБ. "
        "Зображення зберігаються у WebP."
    )


def _ext(name: str) -> str:
    return os.path.splitext(name or "")[1].lower()


def _safe_stem(name: str) -> str:
    stem = Path(name or "").name
    stem = Path(stem).stem.strip().replace("\x00", "") or "file"
    return stem[:120]


def save_attachments(message, uploaded_list) -> None:
    from apps.chat.models import ChatAttachment

    for name, kind, content in prepare_uploads(uploaded_list):
        attachment = ChatAttachment(
            message=message,
            original_name=name,
            kind=kind,
            size=content.size,
        )
        attachment.file.save(name, content, save=False)
        attachment.save()


def prepare_uploads(uploaded_list) -> list[tuple[str, str, ContentFile]]:
    files = [item for item in uploaded_list if item]
    if len(files) > MAX_FILES:
        raise ValidationError(rules_text())

    prepared = []
    for uploaded in files:
        size = getattr(uploaded, "size", None)
        if size is not None and size > MAX_BYTES:
            raise ValidationError(
                _("Файл завеликий (макс. %(size)s). %(rules)s")
                % {"size": filesizeformat(MAX_BYTES), "rules": rules_text()}
            )
        ext = _ext(getattr(uploaded, "name", ""))
        if ext in IMAGE_EXT:
            prepared.append(_prepare_image(uploaded))
        elif ext in PDF_EXT:
            prepared.append(_prepare_pdf(uploaded))
        else:
            raise ValidationError(rules_text())
    return prepared


def _prepare_image(uploaded) -> tuple[str, str, ContentFile]:
    pos = uploaded.tell() if hasattr(uploaded, "tell") else None
    try:
        img = Image.open(uploaded)
        img.verify()
    except Exception as exc:
        raise ValidationError(_("Файл не є коректним зображенням. %(rules)s") % {"rules": rules_text()}) from exc
    finally:
        if pos is not None and hasattr(uploaded, "seek"):
            uploaded.seek(pos)

    try:
        with Image.open(uploaded) as src:
            img = ImageOps.exif_transpose(src)
            if getattr(img, "n_frames", 1) > 1:
                img.seek(0)
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            img = img.convert("RGBA" if has_alpha else "RGB")
            if max(img.size) > MAX_SIDE:
                img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
    except Exception as exc:
        raise ValidationError(_("Файл не є коректним зображенням. %(rules)s") % {"rules": rules_text()}) from exc

    name = f"{_safe_stem(uploaded.name)}.webp"
    return name, "image", ContentFile(buf.getvalue(), name=name)


def _prepare_pdf(uploaded) -> tuple[str, str, ContentFile]:
    pos = uploaded.tell() if hasattr(uploaded, "tell") else None
    try:
        head = uploaded.read(5)
    finally:
        if pos is not None and hasattr(uploaded, "seek"):
            uploaded.seek(0)
        elif hasattr(uploaded, "seek"):
            uploaded.seek(0)
    if head != b"%PDF-":
        raise ValidationError(_("Файл не є PDF. %(rules)s") % {"rules": rules_text()})
    raw = uploaded.read()
    if len(raw) > MAX_BYTES:
        raise ValidationError(
            _("Файл завеликий (макс. %(size)s). %(rules)s")
            % {"size": filesizeformat(MAX_BYTES), "rules": rules_text()}
        )
    name = f"{_safe_stem(uploaded.name)}.pdf"
    return name, "pdf", ContentFile(raw, name=name)
