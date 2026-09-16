"""Авто-WebP після збереження ImageField каталогу (див. apps.core.utils.images)."""
from __future__ import annotations

import logging

from django.db.models.signals import post_save

from apps.core.utils.images import (
    convert_imagefield_to_webp,
    get_webp_specs_for_model,
    image_needs_webp_processing,
    iter_webp_targets,
)

logger = logging.getLogger(__name__)


def convert_images_on_save(sender, instance, **kwargs) -> None:
    if getattr(instance, "_webp_converting", False):
        return

    specs = get_webp_specs_for_model(sender)
    if not specs:
        return

    update_fields = kwargs.get("update_fields")
    converted: list[str] = []

    for field_name, max_side in specs:
        if update_fields is not None and field_name not in update_fields:
            continue
        field_file = getattr(instance, field_name, None)
        if not image_needs_webp_processing(field_file, max_side):
            continue
        try:
            if convert_imagefield_to_webp(instance, field_name, max_side=max_side):
                converted.append(field_name)
        except Exception:
            logger.exception(
                "WebP convert failed: %s.%s pk=%s",
                sender._meta.label,
                field_name,
                getattr(instance, "pk", None),
            )

    if not converted:
        return

    instance._webp_converting = True
    try:
        instance.save(update_fields=converted)
    finally:
        instance._webp_converting = False


def connect_webp_signals() -> None:
    for model, _field_name, _max_side in iter_webp_targets():
        post_save.connect(
            convert_images_on_save,
            sender=model,
            dispatch_uid=f"svbeauty_webp_{model._meta.label}",
        )
