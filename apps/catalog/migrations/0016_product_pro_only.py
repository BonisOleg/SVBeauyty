from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0015_variant_sale_percent"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="pro_only",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=(
                    "Товар бачать тільки клієнти зі статусом «Косметолог». "
                    "Гості, звичайні покупці і заявки його не бачать."
                ),
                verbose_name="Лише для косметологів",
            ),
        ),
    ]
