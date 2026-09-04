from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection


class Command(BaseCommand):
    help = "Reset PostgreSQL PK sequences after loaddata with explicit PKs."

    def handle(self, *args, **options):
        sql = connection.ops.sequence_reset_sql(no_style(), apps.get_models())
        if not sql:
            self.stdout.write("No sequences to reset")
            return
        with connection.cursor() as cursor:
            for stmt in sql:
                cursor.execute(stmt)
        self.stdout.write(self.style.SUCCESS(f"Reset {len(sql)} sequences"))
