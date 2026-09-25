from django.db import migrations

OLD_UK = "Професійна косметика для домашнього та салонного догляду."
OLD_RU = "Профессиональная косметика для домашнего и салонного ухода."
NEW_UK = (
    "Інтернет-магазин професійної косметики Cure Skin і Great Care: "
    "пілінги, сироватки, креми та SPF. Доставка Новою Поштою по Україні."
)
NEW_RU = (
    "Интернет-магазин профессиональной косметики Cure Skin и Great Care: "
    "пилинги, сыворотки, кремы и SPF. Доставка Новой Почтой по Украине."
)


def lengthen(apps, schema_editor):
    Settings = apps.get_model("content", "SiteSettings")
    row = Settings.objects.filter(pk=1).first()
    if row is None:
        return
    fields = []
    if (row.meta_description_uk or "") == OLD_UK:
        row.meta_description_uk = NEW_UK
        fields.append("meta_description_uk")
    if (row.meta_description_ru or "") in ("", OLD_RU):
        row.meta_description_ru = NEW_RU
        fields.append("meta_description_ru")
    if fields:
        row.save(update_fields=fields)


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0014_restore_brand_accent_from_bw"),
    ]

    operations = [
        migrations.RunPython(lengthen, migrations.RunPython.noop),
    ]
