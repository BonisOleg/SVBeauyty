from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0005_site_settings_accent_bw"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="tiktok",
            field=models.CharField(
                blank=True,
                help_text="URL профілю",
                max_length=255,
                verbose_name="TikTok",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="instagram",
            field=models.CharField(
                blank=True,
                help_text="URL профілю",
                max_length=255,
                verbose_name="Instagram",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="telegram",
            field=models.CharField(
                blank=True,
                help_text="URL, напр. https://t.me/...",
                max_length=255,
                verbose_name="Telegram",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="viber",
            field=models.CharField(
                blank=True,
                help_text="URL або номер телефону",
                max_length=255,
                verbose_name="Viber",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="whatsapp",
            field=models.CharField(
                blank=True,
                help_text="URL або номер телефону",
                max_length=255,
                verbose_name="WhatsApp",
            ),
        ),
    ]
