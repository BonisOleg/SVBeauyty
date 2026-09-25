import shutil
from pathlib import Path

import apps.accounts.storage
import apps.accounts.validators
from django.conf import settings
from django.db import migrations, models


def move_documents_to_private(apps, schema_editor):
    Request = apps.get_model("accounts", "CosmetologistRequest")
    private_root = Path(settings.PRIVATE_MEDIA_ROOT)
    media_root = Path(settings.MEDIA_ROOT)
    private_root.mkdir(parents=True, exist_ok=True)
    for row in Request.objects.exclude(document=""):
        relative = Path(row.document.name)
        source = media_root / relative
        target = private_root / relative
        if not source.is_file():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_cosmetologist_document_validators"),
    ]

    operations = [
        migrations.RunPython(move_documents_to_private, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cosmetologistrequest",
            name="document",
            field=models.FileField(
                blank=True,
                help_text="PDF або зображення до 5 МБ. Файл не публічний.",
                storage=apps.accounts.storage.private_document_storage,
                upload_to=apps.accounts.storage.document_upload_to,
                validators=[apps.accounts.validators.validate_cosmetologist_document],
                verbose_name="Документ",
            ),
        ),
    ]
