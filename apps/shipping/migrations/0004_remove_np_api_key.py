from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shipping", "0003_npcity_npwarehouse"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="shippingsettings",
            name="np_api_key",
        ),
        migrations.AlterField(
            model_name="shippingsettings",
            name="use_test_data",
            field=models.BooleanField(
                default=False,
                help_text="Увімкнено — чекаут читає тестовий довідник, ключ з .env ігнорується.",
                verbose_name="Примусово тестові дані",
            ),
        ),
    ]
