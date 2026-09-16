from django.db import migrations

_LEGACY_ACCENT = {"#1a1a1a", "#111111", "#000000", "#000"}


def restore_brand_accent(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    for row in SiteSettings.objects.all().iterator():
        accent = (row.accent_color or "").strip().lower()
        if accent not in _LEGACY_ACCENT:
            continue
        row.accent_color = "#20847C"
        hover = (row.accent_hover_color or "").strip().lower()
        if hover in _LEGACY_ACCENT or not hover:
            row.accent_hover_color = "#186F68"
        row.save(update_fields=["accent_color", "accent_hover_color"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0013_banner_button_sale_default"),
    ]

    operations = [
        migrations.RunPython(restore_brand_accent, migrations.RunPython.noop),
    ]
