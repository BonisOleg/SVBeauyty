from django.core.management.base import BaseCommand

from apps.catalog.models import Variant
from apps.pricing import services


class Command(BaseCommand):
    help = "Перераховує роздрібні й професійні ціни від закупівельних за поточними націнками."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Скинути ручний режим і перерахувати геть усі ціни",
        )

    def handle(self, *args, **options):
        if options["force"]:
            Variant.objects.update(price_is_manual=False, price_pro_is_manual=False)
            self.stdout.write(self.style.WARNING("Ручний режим знято з усіх варіантів"))

        count = services.recalculate_all()
        self.stdout.write(self.style.SUCCESS(f"Оновлено цін: {count}"))
