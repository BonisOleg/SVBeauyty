from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_productreview"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="ingredients_uk",
            new_name="composition_uk",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="ingredients_ru",
            new_name="composition_ru",
        ),
        migrations.AlterField(
            model_name="product",
            name="composition_uk",
            field=models.TextField(
                blank=True,
                help_text="Текст складу на сторінці товару (вкладка «Склад»).",
                verbose_name="Склад (укр)",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="composition_ru",
            field=models.TextField(
                blank=True,
                verbose_name="Склад (рос)",
            ),
        ),
    ]
