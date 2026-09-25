from django.core.management.base import BaseCommand, CommandError

from apps.shipping.novaposhta import NovaPoshtaError
from apps.shipping.sync import sync_directory


class Command(BaseCommand):
    help = "Завантажує міста і відділення Нової Пошти в локальну базу."

    def handle(self, *args, **options):
        try:
            result = sync_directory()
        except NovaPoshtaError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Міст: {result['cities']}. Відділень: {result['warehouses']}."
            )
        )
