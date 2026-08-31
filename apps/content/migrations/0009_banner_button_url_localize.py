import re

from django.db import migrations, models

_LANG_PREFIX = re.compile(r"^/(uk|ru)(?=/|$)", re.IGNORECASE)


def strip_lang_prefixes(apps, schema_editor):
    Banner = apps.get_model("content", "Banner")
    for banner in Banner.objects.exclude(button_url="").iterator():
        url = (banner.button_url or "").strip()
        if not url or url.lower().startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        cleaned = _LANG_PREFIX.sub("", url, count=1)
        if cleaned and not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        if cleaned != banner.button_url:
            banner.button_url = cleaned or "/"
            banner.save(update_fields=["button_url"])


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0008_pro_cta_image_colors"),
    ]

    operations = [
        migrations.RunPython(strip_lang_prefixes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="banner",
            name="button_url",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Шлях без мови, напр. /catalog/syrovatky/. "
                    "Префікс /uk/ або /ru/ підставиться автоматично. "
                    "Зовнішні посилання (https://...) — без змін."
                ),
                max_length=255,
                verbose_name="Посилання кнопки",
            ),
        ),
    ]
