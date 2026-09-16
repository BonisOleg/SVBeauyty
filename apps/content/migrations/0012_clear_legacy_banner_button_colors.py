from django.db import migrations

_LEGACY_BTN = {"#111111", "#000000", "#000"}
_LEGACY_BTN_TEXT = {"#ffffff", "#fff"}


def clear_legacy_black_buttons(apps, schema_editor):
    Banner = apps.get_model("content", "Banner")
    for banner in Banner.objects.all().iterator():
        updates = []
        btn = (banner.button_color or "").strip().lower()
        if btn in _LEGACY_BTN:
            banner.button_color = ""
            updates.append("button_color")
        txt = (banner.button_text_color or "").strip().lower()
        # Після очищення чорної кнопки білий текст теж скидаємо на бренд-дефолт
        if txt in _LEGACY_BTN_TEXT and (
            "button_color" in updates or not (banner.button_color or "").strip()
        ):
            banner.button_text_color = ""
            updates.append("button_text_color")
        if updates:
            banner.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_banner_button_brand_default"),
    ]

    operations = [
        migrations.RunPython(clear_legacy_black_buttons, migrations.RunPython.noop),
    ]
