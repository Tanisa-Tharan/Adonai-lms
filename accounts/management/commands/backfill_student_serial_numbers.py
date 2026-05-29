from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User


class Command(BaseCommand):
    help = "Backfill serial_number for existing STUDENT users that are missing it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of students to update (0 = no limit).",
        )

    def handle(self, *args, **options):
        limit = options["limit"] or 0

        qs = User.objects.filter(role="STUDENT").filter(serial_number__isnull=True) | User.objects.filter(
            role="STUDENT", serial_number=""
        )
        qs = qs.order_by("created_at", "id")
        if limit > 0:
            qs = qs[:limit]

        updated = 0
        with transaction.atomic():
            for student in qs:
                # User.save() generates the serial when role=STUDENT and serial_number is empty.
                student.save(update_fields=["serial_number"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Backfilled serial_number for {updated} students."))

