import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shipping", "0002_delivery_methods_pickup_taxi"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shippingsettings",
            name="np_api_key",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Порожнє поле — ключ з .env (NOVAPOSHTA_API_KEY). "
                    "Після збереження ключа запустіть sync_novaposhta. "
                    "«Примусово тестові дані» ігнорує і адмінку, і .env."
                ),
                max_length=255,
                verbose_name="API-ключ Нової Пошти",
            ),
        ),
        migrations.CreateModel(
            name="NPCity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Створено")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Оновлено")),
                ("ref", models.CharField(max_length=64, unique=True, verbose_name="Ref")),
                ("name", models.CharField(db_index=True, max_length=255, verbose_name="Назва")),
                ("area", models.CharField(blank=True, max_length=255, verbose_name="Область")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Активне")),
            ],
            options={
                "verbose_name": "Місто Нової Пошти",
                "verbose_name_plural": "Міста Нової Пошти",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="NPWarehouse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Створено")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Оновлено")),
                ("ref", models.CharField(max_length=64, unique=True, verbose_name="Ref")),
                ("number", models.CharField(blank=True, max_length=16, verbose_name="Номер")),
                ("description", models.CharField(max_length=512, verbose_name="Назва")),
                ("category", models.CharField(blank=True, db_index=True, max_length=32, verbose_name="Категорія")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Активне")),
                (
                    "city",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="warehouses",
                        to="shipping.npcity",
                        verbose_name="Місто",
                    ),
                ),
            ],
            options={
                "verbose_name": "Відділення Нової Пошти",
                "verbose_name_plural": "Відділення Нової Пошти",
                "ordering": ["number", "description"],
            },
        ),
    ]
